#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys

def main(transfer_path):
    print('create a director called objects')
    os.mkdir(transfer_path + '/objects')
    print('move data into the objects directory')
    source = os.path.join(transfer_path + '/')
    destination = os.path.join(transfer_path, '/objects')
    shutil.copytree(source, destination, symlinks=False, ignore='objects')

    print('move submission documentation into the /metadata/submissionDocumentation')
    os.mkdir(transfer_path + '/metadata')
    os.mkdir(transfer_path + '/metadata/submissionDocumentation')
    source = os.path.join(transfer_path + '/objects/doco')
    destination = os.path.join(transfer_path, '/metadata/submissionDocumentation')
    shutil.copytree(source, destination, symlinks=False, ignore=None)

    print ('remove submission documentation from objects directory')
    shutil.rmtree((transfer_path + '/objects/doco'))

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
