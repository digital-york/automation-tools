#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys
from shutil import ignore_patterns

def main(transfer_path):
    source = os.path.join(transfer_path)
    destination = os.path.join(transfer_path, 'objects/')

    print('move data from' + source + ' to ' + destination)
    src_files = os.listdir(transfer_path)

    # copy folders
    shutil.copytree(source, destination, symlinks=False, ignore=ignore_patterns('objects', 'submissionDocumentation'))

    # copy files
    for file_name in src_files:
        full_file_name = os.path.join(transfer_path, file_name)
        if (os.path.isfile(full_file_name)):
            print('moving ' + full_file_name)
            shutil.copy(full_file_name, destination)


    print('move submission documentation into the /metadata/submissionDocumentation')
    source = os.path.join(transfer_path + 'submissionDocumentation')
    destination = os.path.join(transfer_path, 'metadata/')
    shutil.move(source, destination)

    print('reset all file permissions')
    for root, dirs, files in os.walk(transfer_path):
        for d in dirs:
            os.chown(os.path.join(root, d), 'archivematica', 'archivematica')
        for f in files:
            os.chown(os.path.join(root, f), 'archivematica', 'archivematica')

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
