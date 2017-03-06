#!/usr/bin/env python
from __future__ import print_function 
import argparse
import re
import os
import hashlib
import uuid

from sgfs import SGFS
from sgpublish import Publisher


VALID_EXT = set(('.mp4', '.avi', '.mts', '.mov'))


def create_element_set(set_data, element_data, sgfs):
    '''Creates an ElementSet with a set of Elements on Shotgun.

    TODO:
    - Create a stub $ElementSet, blank path and name = "__creating__"
    - Create all of the Elements (with `create_element`).
    - Finalize the Element.

    '''
    sg = sgfs.session
    element_set = sg.create('$ElementSet',{ 
        'sg_path': '',
        'code': '__creating__',
        'project': set_data['project'],
    })

    for item in element_data: 
        create_element(element_set, item, sg)


    sg.update('$ElementSet', element_set['id'], set_data)


def create_element(set_, data, sg):
    '''Creates a single Element on Shotgun.

    sg.
    TODO (later):
    - Create a thumbnail/filmstrip (ffmpeg is okay for now, PyAV later).
    - Create a proxy on the farm (ffmpeg is okay).
    - Publish with sgpublish.
    - Create a Version (likely with sgpublish Version tools).
    '''
    '''
    sgfs = SGFS()
    sg = sgfs.session
    entity = sg.create('entity', data)
    '''
    data = data.copy()
    data['sg_element_set'] = set_
    data['project'] = set_["project"]
    sg.create('Element', data)

    
def is_footage(path):
    name, ext = os.path.splitext(os.path.basename(path))           
    if ext.lower() in VALID_EXT and not name.startswith('.'):
        return True

def main():
    '''

    TODO:
    - Walk the directory structure, looking for things that look like footage
      (with a handy is_footage or similar function).
    - Create a big list of files that we want to create Elements for, e.g.:
        element_data = [{'path': '/path/to/footage.mov'}, ...]
    - Maaaaybe look on Shotgun for these already existing. It is possible that
      will want to re-ingest something when we update our understanding of it.
    - Ask the user if the stuff we are skipping is okay, and what we have
      found is okay.
    - Pass element_data to create_element_set.

    '''
    sgfs = SGFS()
    approvedFootageList = []
    unapprovedFootageList = []
    data = {}


    parser = argparse.ArgumentParser()
    parser.add_argument('--name')
    parser.add_argument('-y', '--yes',
        help='Forcing this to work')
    parser.add_argument('-n', '--dry-run', action='store_true',
        help='Dont do anything.')
    parser.add_argument('fdirectory')
    parser.add_argument('-P', '--project', help="Path to project/url/id")
    args = parser.parse_args()


    if args.project:
        project = sgfs.parse_user_input(args.project, ["Project"])
        if not project:
            print("This is not a project")
            exit(1)
    else: 
        projects = sgfs.entities_from_path(args.fdirectory, ["Project"])
        if not projects: 
            print("Couldn't find project.")
            exit(2)
        project = projects[0]

    print("Importing the following...")

    for root, dirs, files in os.walk(args.fdirectory, topdown=True):
        for name in files:
            path = os.path.join(root, name)
            rel_path = os.path.relpath(path, args.fdirectory)
            filename, _ = os.path.splitext(name)            
            if is_footage(path):
                print (rel_path)
                approvedFootageList.append({
                    'code': filename,
                    'sg_uuid': str(uuid.uuid4()),
                    'sg_type': "footage",
                    'sg_path': path,
                    'sg_relative_path': rel_path,
                })


    if not args.yes:
        answer = raw_input("Do you want to import this footage? [Y or n?] ")
        if not answer.strip().lower() == "y":
            exit()
    create_element_set({
        'code': args.name or os.path.basename(args.fdirectory),
        'sg_path': args.fdirectory,
        'project': project,
    }, approvedFootageList, sgfs)



if __name__ == '__main__':
    main()

