
import argparse
import hashlib
import os

from concurrent.futures import ThreadPoolExecutor

from sgsession import Session
from sgfs import SGFS

#import farmsoup.queue


def do_one(element_id, path, name='md5'):

    hasher = getattr(hashlib, name)()
    with open(path, 'rb') as fh:
        while True:
            chunk = fh.read(8192)
            if not chunk:
                break
            hasher.update(chunk)

    sg = Session()
    element = sg.find_one('Element', [('id', 'is', element_id)], ['sg_path', 'sg_checksum'])
    assert element['sg_path'] == path
    assert not element['sg_checksum']

    print '{} {}'.format(hasher.hexdigest(), path)
    sg.update('Element', element_id, {'sg_checksum': '%s:%s' % (name, hasher.hexdigest())})


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--threads', type=int, default=8)
    args = parser.parse_args()

    sg = Session()
    work = []
    for element in sg.find('Element', [('sg_checksum', 'is', '')], ['code', 'sg_path']):
        path = element['sg_path']
        if path and os.path.exists(path):
            # print element['code'], element['sg_path']
            work.append((element['id'], element['sg_path']))

    print 'Calculating checksums for {} files...'.format(len(work))
    
    executor = ThreadPoolExecutor(args.threads)
    executor.map(do_one, *zip(*work))


if __name__ == '__main__':
    main()


