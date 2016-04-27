#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys
from shutil import ignore_patterns

def main(transfer_path):
    source = os.path.join(transfer_path)
    destination = os.path.join(transfer_path, 'objects')

    print('move data from' + source + ' to ' + destination)
    src_files = os.listdir(transfer_path)

    # copy folders
    shutil.copytree(source, destination, symlinks=False, ignore=ignore_patterns('objects', 'submissionDocumentation', 'processingMCP.xml'))

    # copy files
    for file_name in src_files:
        full_file_name = os.path.join(transfer_path, file_name)
        if (os.path.isfile(full_file_name)):
            print('moving ' + full_file_name)
            shutil.move(full_file_name, os.path.join(destination,full_file_name))

    print('move submission documentation into the /metadata/submissionDocumentation')
    source = os.path.join(transfer_path + 'submissionDocumentation')
    destination = os.path.join(transfer_path, 'metadata/')
    shutil.move(source, destination)

    print('reset all file permissions')
    for root, dirs, files in os.walk(transfer_path):
        shutil.chown(root, 'archivematica', 'archivematica')
        for d in dirs:
            shutil.chown(os.path.join(root, d), 'archivematica', 'archivematica')
        for f in files:
            shutil.chown(os.path.join(root, f), 'archivematica', 'archivematica')

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
