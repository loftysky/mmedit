from __future__ import print_function 

import errno
import os
import re

from sgfs import SGFS


REDUCTIONS = (
    (r'/xdroot/', '/'),
    (r'/clip/', '/'),
    (r'/dcim/\d+\w*/', '/'),
    (r'/dcim/', '/'),
)


def relink(elements, dst_root, use_symlinks=True, reduce_paths=True, prefer_checksum=True, dry_run=False, verbose=False):
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

        dir_, file_name = os.path.split(rel_path)

        base_name, ext = os.path.splitext(file_name)
        new_dirs = os.path.join(dst_root, dir_)
        
        try: 
            os.makedirs(new_dirs)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # "x" is for checksum, and "u" for UUID; wanted to uses non-hex letters.
        if prefer_checksum and element['sg_checksum']:
            # Checksums are assumed to look like "md5:xxx" or "sha256:xxx".
            dst_name = '%s_X%s%s' % (base_name, element['sg_checksum'].split(':')[-1][:8].upper(), ext)
        else:
            dst_name = '%s_U%s%s' % (base_name, element['sg_uuid'][:8].upper(), ext)

        dst_path = os.path.join(new_dirs, dst_name)

        src_path = element['sg_path']

        if verbose:
            print('%s -> %s' % (dst_path, src_path))

        if not dry_run:
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

    parser.add_argument('-u', '--prefer-uuid', action='store_true')
    parser.add_argument('-s', '--symlink', action='store_true')
    parser.add_argument('-H', '--hardlink', action='store_true')

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--dry-run', action='store_true')

    parser.add_argument('element_set')
    parser.add_argument('root')
    args = parser.parse_args()

    if not args.dry_run and ((args.symlink and args.hardlink) or not (args.symlink or args.hardlink)):
        print("Please pick one of --hardlink or --symlink.")
        exit(1)

    sgfs = SGFS()

    element_set = sgfs.parse_user_input(args.element_set, ['CustomEntity27'])
    if not element_set:
        print("Could not parse element set:", args.element_set)

    elements = sgfs.session.find('Element', [
        ('sg_element_set', 'is', element_set),
    ], ['sg_path', 'sg_relative_path', 'sg_uuid'])

    relink(elements, args.root,
        use_symlinks=args.symlink,
        prefer_checksum=not args.prefer_uuid,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )



if __name__ == '__main__':
    main()

