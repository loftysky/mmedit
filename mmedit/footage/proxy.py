from __future__ import print_function 

import os
import re
import subprocess

from .utils import makedirs, reduce_path, clean_path, add_render_arguments, iter_render_work, guess_type



def submit(element, dst_path, **_):
    src_path = element['sg_path']
    if guess_type(src_path) == 'footage':
        print('mmedit-proxy encode', src_path, dst_path)

def encode(src, dst):
    return subprocess.call(['ffmpeg',
        '-y', # Overwrite.
        '-i', src,
        '-c:v', 'prores_ks',
        '-profile:v', '0', # Proxy.
        '-qscale:v', '9', # 0 is best, 32 is worst.
        '-vendor', 'ap10', # Mimick QuickTime.
        '-pix_fmt', 'yuv422p10le',
        '-s', '1920x1080',
        dst
    ])     


def main():

    import argparse

    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='_command')

    submit_parser = commands.add_parser('submit')
    add_render_arguments(submit_parser)

    encode_parser = commands.add_parser('encode')
    encode_parser.add_argument('src')
    encode_parser.add_argument('dst')

    args = parser.parse_args()

    if args._command == 'submit':
        exit(main_submit(args) or 0)
    else:
        exit(main_encode(args) or 0)


def main_submit(args):
    for element, path in iter_render_work(**args.__dict__):
        submit(element, path, **args.__dict__)


def main_encode(args):
    encode(args.src, args.dst)



if __name__ == '__main__':
    main()
