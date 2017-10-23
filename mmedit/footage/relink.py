from __future__ import print_function 

import errno
import os

from dirmap import DirMap

from .utils import makedirs, reduce_path, clean_path, add_render_arguments, iter_render_work



def makedirs(path):
    try: 
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


dir_map = DirMap()
dir_map.add_existing('''
    /Volumes/EditOnline/CWAF_S3/01_Raw_Source
    /Volumes/EDsource/Projects/ConfuciusWasAFoodieS3/footage/camera_originals
'''.strip().split())
dir_map.add_existing('''
    /Volumes/EditOnline/CWAF_S3/02_0ptimized_Source
    /Volumes/EDsource/Projects/ConfuciusWasAFoodieS3/footage/source
'''.strip().split())


def relink(element, dst_path, symlink, dry_run=False, update=False,
    replace=False, verbose=False, **_
):

    src_path = element['sg_path']
    src_path = dir_map(src_path)

    missing = not os.path.exists(src_path)
    if verbose or missing:
        print('%s -> %s' % (dst_path, src_path))
        if missing:
            print('    Source is missing; skipping it.')
            return

    if dry_run:
        return

    if os.path.exists(dst_path):
        if replace:
            os.unlink(dst_path)
        elif update:
            # Ignoring this file.
            return

    try:
        if symlink:
            os.symlink(src_path, dst_path)
        else:
            os.link(src_path, dst_path)
    except OSError as e:
        if errno != errno.EEXIST:
            raise

    return True


def main():

    import argparse

    parser = argparse.ArgumentParser()
    add_render_arguments(parser)
    args = parser.parse_args()

    if not args.dry_run and ((args.symlink and args.hardlink) or not (args.symlink or args.hardlink)):
        print("Please pick one of --hardlink or --symlink.")
        exit(1)

    for element, path in iter_render_work(**args.__dict__):
        relink(element, path, **args.__dict__)



if __name__ == '__main__':
    main()

