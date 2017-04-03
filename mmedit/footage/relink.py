

def to_link(element_set, dest_path, sg, symlinks):
    '''
    takes the element set path, sets the new path to hard or symlinks dependent on link option
    '''
    try:
        os.makedirs(dest_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    '''
    try:
        change_path = os.path.join(str(dest_path), str(element_set[0]['sg_element_set.CustomEntity27.code']))
        os.makedirs(change_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    '''
    for item in element_set:
        sg_path = item['sg_path']
        dirs, filename = os.path.split(item['sg_relative_path'])
        filename, ext = os.path.splitext(filename)
        new_dirs = os.path.join(str(dest_path), str(element_set[0]['sg_element_set.CustomEntity27.code']), dirs)
        try: 
            os.makedirs(new_dirs)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        new_filename = filename + "_" + item['sg_uuid'][:8 ] + ext
        dest_filename = os.path.join(new_dirs, new_filename)
        if symlinks == False: 
            try:
                os.link(sg_path, dest_filename)
            except OSError as e:
                if errno != errno.EEXIST:
                    raise
        try: 
            os.symlink(sg_path, dest_filename)
        except OSError as e:
            if errno != errno.EEXIST:
                raise
        print('Creating symlink for file to ....', dest_filename)
     

