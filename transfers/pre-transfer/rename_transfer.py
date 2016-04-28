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
    # shutil.movetree(source, destination, symlinks=False, ignore=ignore_patterns('objects', 'submissionDocumentation', 'processingMCP.xml'))

    # copy files
    for name in src_files:
        full_name = os.path.join(transfer_path, name)
        print(full_name)
        print(name)
        try:
            if name != 'objects':
                if name != 'submissionDocumentation':
                    if name != 'processingMCP.xml':
                        shutil.move(full_name, os.path.join(transfer_path, 'objects/'))
        except OSError as e:
            print(e)

    print('move submission documentation into the /metadata/submissionDocumentation')
    source = os.path.join(transfer_path,'submissionDocumentation')
    destination = os.path.join(transfer_path, 'metadata/')
    shutil.move(source, destination)

    print('reset all file permissions')
    for root, dirs, files in os.walk(transfer_path):
        for d in dirs:
            print(d)
            shutil.chown(os.path.join(transfer_path, d), 'archivematica', 'archivematica')
        for f in files:
            print(f)
            shutil.chown(os.path.join(transfer_path, f), 'archivematica', 'archivematica')

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
