from __future__ import print_function 

import errno
import os

from sgfs import SGFS


def relink(elements, dst_root, use_symlinks=True, dry_run=False, verbose=False):
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
    sg.fetch(elements, ['sg_path', 'sg_relative_path', 'sg_uuid'])

    for element in elements:

        dir_, file_name = os.path.split(element['sg_relative_path'])

        base_name, ext = os.path.splitext(file_name)
        new_dirs = os.path.join(dst_root, dir_)
        
        try: 
            os.makedirs(new_dirs)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        dst_name = base_name + "_" + element['sg_uuid'][:8 ] + ext
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

    parser.add_argument('-s', '--symlink', action='store_true')
    parser.add_argument('-H', '--hardlink', action='store_true')

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-n', '--dry-run', action='store_true')

    parser.add_argument('element_set')
    parser.add_argument('root')
    args = parser.parse_args()

    if (args.symlink and args.hardlink) or not (args.symlink or args.hardlink):
        print("Please pick one of --hardlink or --symlink.")
        exit(1)

    sgfs = SGFS()

    element_set = sgfs.parse_user_input(args.element_set, ['CustomEntity27'])
    if not element_set:
        print("Could not parse element set:", args.element_set)

    elements = sgfs.session.find('Element', [
        ('sg_element_set', 'is', element_set),
    ], ['sg_path', 'sg_relative_path', 'sg_uuid'])

    relink(elements, args.root, use_symlinks=args.symlink, dry_run=args.dry_run, verbose=args.verbose)



if __name__ == '__main__':
    main()

