from __future__ import print_function 

import json
import os
import re
import subprocess

import psutil

from .utils import makedirs, reduce_path, clean_path, add_render_arguments, iter_render_work, guess_type



def encode(src, dst, verbose=False, dry_run=False):

    name, ext = os.path.splitext(dst)
    salt = os.urandom(2).encode('hex')
    tmp = name + '.encoding-' + salt + ext
    
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams',
        src
    ]
    if verbose:
        print('$', ' '.join(cmd))
    probe = json.loads(subprocess.check_output(cmd))
    has_video = any(s['codec_type'] == 'video' for s in probe['streams'])
    has_audio = any(s['codec_type'] == 'audio' for s in probe['streams'])

    cmd = ['ffmpeg',
        '-y', # Overwrite.
        '-i', src,
        '-vendor', 'ap10', # Mimick QuickTime.
        '-threads', str(psutil.cpu_count()), # All threads.
    ]
    if has_video:
        if ext == '.mov':
            cmd.extend((
                '-map', '0:v',
                '-c:v', 'prores_ks',
                '-profile:v', '0', # Proxy.
                '-qscale:v', '9', # 0 is best, 32 is worst.
                '-pix_fmt', 'yuv422p10le',
                '-s', '1920x1080',
            ))
        elif ext == '.mxf':
            cmd.extend((
                '-map', '0:v',
                '-c:v', 'dnxhd',
                '-pix_fmt', 'yuv422',
                '-b:v', '36Mb', # NOTE: This is only for 23.976.
                '-s', '1920x1080',
            ))
        else:
            raise ValueError('Extension not mov or mxf.', container)

    if has_audio:
        cmd.extend((
            '-map', '0:a',
            '-c:a', 'copy',
        ))
    cmd.append(tmp)

    if verbose:
        print('$', ' '.join(cmd))

    if dry_run:
        return
    
    ret = subprocess.call(cmd)
    if ret and os.path.exists(tmp):
        os.rename(tmp, name + '.failed-' + salt + ext)
    else:
        os.rename(tmp, dst)

    return ret


def main():

    import argparse

    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='_command')

    submit_parser = commands.add_parser('submit')
    submit_parser.add_argument('-f', '--format', choices=('mov', 'mxf'),
        default='mov',
        help='mov => ProRes, mxf => DNxHD')
    add_render_arguments(submit_parser)

    encode_parser = commands.add_parser('encode')
    encode_parser.add_argument('-v', '--verbose', action='store_true')
    encode_parser.add_argument('-n', '--dry-run', action='store_true')
    encode_parser.add_argument('src')
    encode_parser.add_argument('dst')

    args = parser.parse_args()

    if args._command == 'submit':
        args.types = args.types or ['footage']
        exit(main_submit(args) or 0)
    else:
        exit(main_encode(args) or 0)


def main_submit(args):

    from farmsoup.client import Client
    from farmsoup.client.models import Job

    todo = []
    for element, dst_path in iter_render_work(
        generate_path=lambda el, dst_path: os.path.splitext(dst_path)[0] + '.' + args.format,
        **args.__dict__
    ):
        src_path = element['sg_path']
        if args.verbose:
            print(dst_path, '<-', src_path)
        todo.append((src_path, dst_path))

    if args.dry_run:
        return

    new_args = ['mmedit-proxy', 'encode']

    client = Client()
    job = client.job(
        name='Proxies',
    ).setup_as_subprocess(['mmedit-proxy', 'encode'])
    template = job.tasks.pop(0)
    for src, dst in todo:
        task = template.copy()
        task.package['args'].extend((src, dst))
        task.name = dst
        job.tasks.append(task)

    if not len(job.tasks):
        print("Nothing to submit.")
        return

    client.submit(name='Proxies', jobs=[job])

def main_encode(args):
    return encode(src=args.src, dst=args.dst, verbose=args.verbose, dry_run=args.dry_run)



if __name__ == '__main__':
    main()
