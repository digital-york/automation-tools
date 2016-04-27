#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys
from shutil import ignore_patterns

def main(transfer_path):
    print('hello')
    print(transfer_path)
    source = os.path.join(transfer_path)
    destination = os.path.join(transfer_path, 'objects')
    print('move data from' + source + ' to ' + destination)
    shutil.copy(source, destination)
    shutil.copytree(source, destination, symlinks=False, ignore=ignore_patterns('objects','doco'))

    print('move submission documentation into the /metadata/submissionDocumentation')
    os.mkdir(transfer_path + '/metadata')
    os.mkdir(transfer_path + '/metadata/submissionDocumentation')
    source = os.path.join(transfer_path + 'doco/')
    destination = os.path.join(transfer_path, 'metadata/submissionDocumentation')
    shutil.move(source, destination)
    os.rmdir(source)

    print('reset all file permissions')
    for root, dirs, files in os.walk(transfer_path):
        for d in dirs:
            os.chown(os.path.join(root, d), 'archivematica', 'archivematica')
        for f in files:
            os.chown(os.path.join(root, f), 'archivematica', 'archivematica')

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
