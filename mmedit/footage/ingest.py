from __future__ import print_function 

import os
import re
import uuid

from sgfs import SGFS

from .utils import guess_type


EXCLUDE_DIRS = set('''
    __junk__
'''.strip().split())



def create_element(element_set, data, sg, verbose=False):
    '''Creates a single Element on Shotgun.

    TODO (later):
    - Create a thumbnail/filmstrip.
    - Create a mp4/webm for Shotgun.
    - Publish with sgpublish (maybe).
    - Create a Version (likely with sgpublish Version tools).

    '''

    data = data.copy()
    data['sg_element_set'] = element_set
    data['project'] = element_set["project"]

    if verbose:
        print('Creating Element:', data.get('code'))

    sg.create('Element', data)


def create_element_set(set_data, element_data, sgfs, verbose=False):
    '''Creates an ElementSet with a set of Elements on Shotgun.'''

    sg = sgfs.session

    if verbose:
        print('Creating ElementSet:', set_data.get('code'))

    # Create a placeholder; we need something to link our Element(s) against,
    # but want it to look incomplete until it is not.
    element_set = sg.create('$ElementSet', { 
        'sg_path': '',
        'code': '__creating__',
        'project': set_data['project'],
    })

    _create_elements_in_set(sg, element_set, element_data, verbose=verbose)

    sg.update('$ElementSet', element_set['id'], set_data)

    return element_set


def _create_elements_in_set(sg, element_set, element_data, verbose=False):
    for item in element_data: 
        create_element(element_set, item, sg, verbose=verbose)


def main():

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('--name',
        help="Defaults to basename of directory to ingest.")
    parser.add_argument('-P', '--project',
        help="Project (path, URL, or ID).")

    parser.add_argument('-f', '--force', action='store_true',
        help="Force creating a new ElementSet if this has already been ingested.")
    parser.add_argument('-u', '--update', action='store_true',
        help="Update this element set instead of creating a new one.")

    parser.add_argument('-y', '--yes', action='store_true',
        help="Don't ask for permission.")
    parser.add_argument('-n', '--dry-run', action='store_true',
        help="Don't actually do anything; preview in the ingest.")
    parser.add_argument('-v', '--verbose', action='store_true')

    parser.add_argument('root',
        help="Directory of footage to ingest.")

    args = parser.parse_args()

    # Normalize arguments.
    args.root = os.path.abspath(args.root)

    sgfs = SGFS()
    sg = sgfs.session

    existing_elements = set()
    element_specs = []
    data = {}

    # Get the Project; either parse the user's input, or find the enclosing
    # Project from the footage to ingest.
    if args.project:
        project = sgfs.parse_user_input(args.project, ["Project"])
        if not project:
            print("This is not a project")
            exit(1)
    else: 
        projects = sgfs.entities_from_path(args.root, ["Project"])
        if not projects: 
            print("Couldn't find project.")
            exit(2)
        project = projects[0]

    # Find an existing ElementSet.
    element_set = sg.find_one('$ElementSet', [
        ('sg_path', 'is', args.root),
    ], ['project'])
    if args.update:
        if not element_set:
            print("Could not find existing ElementSet at:", args.root)
            exit(4)
        for element in sg.find('Element', [('sg_element_set', 'is', element_set)], ['sg_relative_path']):
            existing_elements.add(element['sg_relative_path'])
    else:
        if element_set and not args.force:
            print("There is already an ElementSet here!")
            print("Update it with --update, or force creation with --force (if you are REALLY sure).")
            exit(5)

    print("Scanning for footage...")

    for dir_path, dir_names, file_names in os.walk(args.root, topdown=True):

        # Exclude some dirs (just __junk__ at this point).
        dir_names[:] = [x for x in dir_names if x.lower() not in EXCLUDE_DIRS]

        for name in file_names:
            abs_path = os.path.join(dir_path, name)
            
            type_ = guess_type(abs_path)
            if not type_:
                continue

            rel_path = os.path.relpath(abs_path, args.root)
            filename, _ = os.path.splitext(name)  

            # If we are updating, and already have this one, skip it.
            if rel_path in existing_elements:
                continue

            print('[%7s] %s' % (type_, rel_path))

            element_specs.append({
                'code': filename,
                'sg_uuid': str(uuid.uuid4()), # uuid4 is the random one.
                'sg_type': type_,
                'sg_path': abs_path,
                'sg_relative_path': rel_path,
            })

    if not element_specs:
        print("Nothing to ingest.")
        exit(0)

    # Get the user's permission to go ahead.
    if not args.yes:
        answer = raw_input("Do you want to import this footage? [Yn] ")
        if answer.strip().lower() not in ('yes', 'y', ''):
            exit(3)

    if not args.dry_run:

        if args.update:
            _create_elements_in_set(sgfs.session, element_set, element_specs, verbose=args.verbose)
        else:
            element_set = create_element_set({
                'code': args.name or os.path.basename(args.root),
                'sg_path': args.root,
                'project': project,
            }, element_specs, sgfs, verbose=args.verbose)
            print(element_set['id'])




if __name__ == '__main__':
    main()

