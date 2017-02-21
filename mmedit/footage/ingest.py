

def create_element_set(set_data, element_data):
    '''Creates an ElementSet with a set of Elements on Shotgun.

    TODO:
    - Create a stub $ElementSet, blank path and name = "__creating__"
    - Create all of the Elements (with `create_element`).
    - Finalize the Element.
    '''
    pass


def create_element(set_, data):
    '''Creates a single Element on Shotgun.

    TODO (later):
    - Create a thumbnail/filmstrip (ffmpeg is okay for now, PyAV later).
    - Create a proxy on the farm (ffmpeg is okay).
    - Publish with sgpublish.
    - Create a Version (likely with sgpublish Version tools).
    '''
    pass


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
    pass