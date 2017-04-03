#!/usr/bin/env python

from __future__ import print_function 

import argparse
import errno
import hashlib
import os
import re
import uuid

from sgfs import SGFS
from sgpublish import Publisher


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


def create_element(element_set, data, sg):
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
    sg.create('Element', data)


def create_element_set(set_data, element_data, sgfs):
    '''Creates an ElementSet with a set of Elements on Shotgun.'''

    sg = sgfs.session

    # Create a placeholder; we need something to link our Element(s) against,
    # but want it to look incomplete until it is not.
    element_set = sg.create('$ElementSet', { 
        'sg_path': '',
        'code': '__creating__',
        'project': set_data['project'],
    })

    for item in element_data: 
        create_element(element_set, item, sg)

    sg.update('$ElementSet', element_set['id'], set_data)

    return element_set

    
def guess_type(path):
    """What type of element is this?

    Returns one of `"footage"`, `"image"`, `"audio"`, or `None`.

    """
    name, ext = os.path.splitext(os.path.basename(path))
    if name.startswith('.'):
        return
    return EXT_TO_TYPE.get(ext.lower())


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--name',
        help="Defaults to basename of directory to ingest.")
    parser.add_argument('-P', '--project',
        help="Project (path, URL, or ID).")
    parser.add_argument('-y', '--yes', action='store_true',
        help="Don't ask for permission.")
    parser.add_argument('-n', '--dry-run', action='store_true',
        help="Don't actually do anything; preview in the ingest.")
    parser.add_argument('root',
        help="Directory of footage to ingest.")
    args = parser.parse_args()

    # Normalize arguments.
    args.root = os.path.abspath(args.root)

    sgfs = SGFS()
    sg = sgfs.session

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


    print("Importing the following...")

    for dir_path, _, file_names in os.walk(args.root, topdown=True):
        for name in file_names:
            abs_path = os.path.join(dir_path, name)
            
            type_ = guess_type(abs_path)
            if not type_:
                continue

            rel_path = os.path.relpath(abs_path, args.root)
            filename, _ = os.path.splitext(name)  

            print('%7s %s' % (type_, rel_path))

            element_specs.append({
                'code': filename,
                'sg_uuid': str(uuid.uuid4()), # uuid4 is the random one.
                'sg_type': type_,
                'sg_path': abs_path,
                'sg_relative_path': rel_path,
            })

    # Get the user's permission to go ahead.
    if not args.yes:
        answer = raw_input("Do you want to import this footage? [Y or n?] ")
        if not answer.strip().lower() == "y":
            exit(3)

    if not args.dry_run:
        element_code = create_element_set({
            'code': args.name or os.path.basename(args.root),
            'sg_path': args.root,
            'project': project,
        }, element_specs, sgfs)
        element_code_id = element_code['id']




if __name__ == '__main__':
    main()

