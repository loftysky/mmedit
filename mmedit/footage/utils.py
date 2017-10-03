import errno
import os
import re

from sgfs import SGFS


def makedirs(path):
    try: 
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise



EXT_TO_TYPE = {

    '.mp4':  'footage',
    '.avi':  'footage',
    '.mts':  'footage',
    '.mov':  'footage',
    '.mxf':  'footage',

    '.jpg':  'image',
    '.jpeg': 'image',
    '.png':  'image',
    '.tif':  'image',
    '.tiff': 'image',

    '.wav':  'audio',
    '.aif':  'audio',
    '.aiff': 'audio',

}

def guess_type(path):
    """What type of element is this?

    Returns one of `"footage"`, `"image"`, `"audio"`, or `None`.

    """
    path = path.lower()
    try:
        return EXT_TO_TYPE[path]
    except KeyError:
        pass

    name, ext = os.path.splitext(os.path.basename(path))
    if name.startswith('.'):
        return
    return EXT_TO_TYPE.get(ext)


REDUCTIONS = (
    # NOTE: The order here matters.
    (r'/clip/', '/'),
    (r'/clips\d+/', '/'),
    (r'/contents/', '/'),
    (r'/dcim/\d+\w*/', '/'),
    (r'/dcim/', '/'), # Must be after other dcim line (so don't just sort this)
    (r'/xdroot/', '/'),
)

def reduce_path(path):
    for pattern, replacement in REDUCTIONS:
        path = re.sub(pattern, replacement, path, flags=re.IGNORECASE)
    return path


def clean_path(path):
    parts = path.split(os.path.sep)
    parts = [re.sub(r'[^\w,\.]+', '-', part).strip('-') for part in parts]
    return os.path.sep.join(parts)


def unique_name(path, element, prefer_checksum=False):

        base, ext = os.path.splitext(path)

        # "x" is for checksum, and "u" for UUID; wanted to uses non-hex letters.
        if prefer_checksum and element.fetch('sg_checksum'):
            # Checksums are assumed to look like "md5:xxx" or "sha256:xxx".
            return '%s_X%s%s' % (base, element['sg_checksum'].split(':')[-1][:8].upper(), ext)
        else:
            return '%s_U%s%s' % (base, element.fetch('sg_uuid')[:8].upper(), ext)


def add_render_arguments(parser):

    parser.add_argument('--prefer-uuid', action='store_true')
    parser.add_argument('--ignore-uuid', action='store_true')

    parser.add_argument('-s', '--symlink', action='store_true')
    parser.add_argument('-H', '--hardlink', action='store_true')

    parser.add_argument('-a', '--all', action='store_true',
        help="Relink all element sets in the given project.")

    parser.add_argument('-t', '--type', action='append', dest='types', choices=('footage', 'image', 'audio'),
        help="Only process the given type.")

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-u', '--update', action='store_true',
        help="Allow updating of existing directories.")
    parser.add_argument('-U', '--replace', action='store_true',
        help="Allow updating over existing files.")
    parser.add_argument('-n', '--dry-run', action='store_true')

    parser.add_argument('entity',
        help="$ElementSet or Project (if --all).")
    parser.add_argument('root')


def iter_render_work(entity, root, all=False, update=False, replace=False,
    sgfs=None, **kwargs
):

    sgfs = sgfs or SGFS()

    if all:
        project = sgfs.parse_user_input(entity, ['Project'])
        if not project:
            print("Could not parse project:", entity)
        element_sets = sgfs.session.find('CustomEntity27', [
            ('project', 'is', project),
        ], ['code'])
        todo = [(element, os.path.join(root, element['code'])) for element in element_sets]

    else:
        element_set = sgfs.parse_user_input(entity, ['CustomEntity27'])
        if not element_set:
            print("Could not parse element set:", entity)
        todo = [(element_set, root)]

    can_continue = True
    for _, root in todo:
        if not (update or replace) and os.path.exists(root):
            print("Root already exists:", root)
            can_continue = False
    if not can_continue:
        exit(1)

    for element_set, root in todo:
        elements = sgfs.session.find('Element', [
            ('sg_element_set', 'is', element_set),
        ], ['sg_path', 'sg_relative_path', 'sg_uuid', 'sg_checksum', 'sg_type'])
        for x in _iter_render_work(elements, root,
            update=update,
            replace=replace,
            **kwargs
        ):
            yield x


def _iter_render_work(elements, root, reduce_paths=True, prefer_uuid=False,
    ignore_uuid=False, update=False, replace=False, verbose=False,
    dry_run=False, types=None, **_
):

    root = os.path.abspath(root)

    # Assert that the parent already exists (which is sometimes a good
    # indicator that the user has missed).
    parent = os.path.dirname(root)
    if not os.path.exists(parent):
        raise ValueError('Parent does not exist.', parent)

    if not elements:
        return

    sg = elements[0].session
    sg.fetch(elements, ['sg_path', 'sg_relative_path', 'sg_uuid', 'sg_type', 'sg_checksum'])

    for element in elements:

        if types and element['sg_type'] not in types:
            continue

        if ignore_uuid and not element['sg_checksum']:
            return
        
        rel_path = element['sg_relative_path']
        if reduce_paths:
            rel_path = reduce_path(rel_path)
        rel_path = clean_path(rel_path)
        rel_path = unique_name(rel_path, element, prefer_checksum=not prefer_uuid)

        path = os.path.join(root, rel_path)
        dir_ = os.path.dirname(path)

        if not dry_run:
            makedirs(dir_)

        if not os.path.exists(path):
            yield element, path
            continue

        if replace:
            if verbose:
                print('    Destination already exists; replacing it.')
            yield element, path
        elif update:
            if verbose:
                print('    Destination already exists; skipping it.')




