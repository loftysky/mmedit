from __future__ import print_function 

import errno
import os
import re

from dirmap import DirMap
from sgfs import SGFS


REDUCTIONS = (
    # NOTE: The order here matters.
    (r'/clip/', '/'),
    (r'/clips\d+/', '/'),
    (r'/contents/', '/'),
    (r'/dcim/\d+\w*/', '/'),
    (r'/dcim/', '/'), # Must be after other dcim line (so don't just sort this)
    (r'/xdroot/', '/'),
)


def makedirs(path):
    try: 
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


dir_map = DirMap()
dir_map.auto_add('''
    /Volumes/EditOnline/CWAF_S3/01_Raw_Source
    /Volumes/EDsource/Projects/ConfuciusWasAFoodieS3/footage/camera_originals
'''.strip().split())
dir_map.auto_add('''
    /Volumes/EditOnline/CWAF_S3/02_0ptimized_Source
    /Volumes/EDsource/Projects/ConfuciusWasAFoodieS3/footage/source
'''.strip().split())


def relink(elements, dst_root, use_symlinks=True, reduce_paths=True, prefer_checksum=True,
    dry_run=False, update=False, replace=False, verbose=False):

    """Create a heirarchy from a set of Elements that symlink to the originals."""

    dst_root = os.path.abspath(dst_root)

    # Assert that the parent already exists (which is sometimes a good
    # indicator that the user has missed).
    dst_parent = os.path.dirname(dst_root)
    if not os.path.exists(dst_parent):
        raise ValueError('Parent does not exist.', dst_parent)

    if not elements:
        return

    sg = elements[0].session
    sg.fetch(elements, ['sg_path', 'sg_relative_path', 'sg_uuid', 'sg_checksum'])

    for element in elements:

        rel_path = element['sg_relative_path']

        if reduce_paths:
            for pattern, replacement in REDUCTIONS:
                rel_path = re.sub(pattern, replacement, rel_path, flags=re.IGNORECASE)

        # Remove all special characters from the new names.
        rel_names = rel_path.split(os.path.sep)
        rel_names = [re.sub(r'[^\w,\.]+', '-', name).strip('-') for name in rel_names]
        rel_path = os.path.sep.join(rel_names)

        dir_, file_name = os.path.split(rel_path)

        base_name, ext = os.path.splitext(file_name)
        new_dirs = os.path.join(dst_root, dir_)

        # "x" is for checksum, and "u" for UUID; wanted to uses non-hex letters.
        if prefer_checksum and element['sg_checksum']:
            # Checksums are assumed to look like "md5:xxx" or "sha256:xxx".
            dst_name = '%s_X%s%s' % (base_name, element['sg_checksum'].split(':')[-1][:8].upper(), ext)
        else:
            dst_name = '%s_U%s%s' % (base_name, element['sg_uuid'][:8].upper(), ext)

        dst_path = os.path.join(new_dirs, dst_name)
        
        src_path = element['sg_path']
        src_path = dir_map.get(src_path)

        missing = not os.path.exists(src_path)
        if verbose or missing:
            print('%s -> %s' % (dst_path, src_path))
            if missing:
                print('    Source is missing; skipping it.')
                continue

        if os.path.exists(dst_path):
            if replace:
                if verbose:
                    print('    Destination already exists; replacing it.')
                if not dry_run:
                    os.unlink(dst_path)
            elif update:
                if verbose:
                    print('    Destination already exists; skipping it.')
                continue

        if not dry_run:
            makedirs(new_dirs)
            try: 
                if use_symlinks:
                    os.symlink(src_path, dst_path)
                else:
                    os.link(src_path, dst_path)
            except OSError as e:
                if errno != errno.EEXIST:
                    raise

        
     

def main():

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--prefer-uuid', action='store_true')
    parser.add_argument('-s', '--symlink', action='store_true')
    parser.add_argument('-H', '--hardlink', action='store_true')

    parser.add_argument('-a', '--all', action='store_true',
        help="Relink all element sets in the given project.")

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-u', '--update', action='store_true',
        help="Allow updating of existing directories.")
    parser.add_argument('-U', '--replace', action='store_true',
        help="Allow updating over existing files.")
    parser.add_argument('-n', '--dry-run', action='store_true')

    parser.add_argument('entity',
        help="$ElementSet or Project (if --all).")
    parser.add_argument('root',
        )
    args = parser.parse_args()

    if not args.dry_run and ((args.symlink and args.hardlink) or not (args.symlink or args.hardlink)):
        print("Please pick one of --hardlink or --symlink.")
        exit(1)

    sgfs = SGFS()

    if args.all:
        project = sgfs.parse_user_input(args.entity, ['Project'])
        if not project:
            print("Could not parse project:", args.entity)
        element_sets = sgfs.session.find('CustomEntity27', [
            ('project', 'is', project),
        ], ['code'])
        todo = [(element, os.path.join(args.root, element['code'])) for element in element_sets]

    else:
        element_set = sgfs.parse_user_input(args.entity, ['CustomEntity27'])
        if not element_set:
            print("Could not parse element set:", args.entity)
        todo = [(element_set, args.root)]

    can_continue = True
    for _, root in todo:
        if not (args.update or args.replace) and os.path.exists(root):
            print("Root already exists:", root)
            can_continue = False
    if not can_continue:
        exit(1)

    for element_set, root in todo:
        elements = sgfs.session.find('Element', [
            ('sg_element_set', 'is', element_set),
        ], ['sg_path', 'sg_relative_path', 'sg_uuid'])

        relink(elements, root,
            use_symlinks=args.symlink,
            prefer_checksum=not args.prefer_uuid,
            dry_run=args.dry_run,
            update=args.update,
            replace=args.replace,
            verbose=args.verbose,
        )



if __name__ == '__main__':
    main()

