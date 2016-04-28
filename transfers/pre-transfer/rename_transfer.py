#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys
from shutil import ignore_patterns

def main(transfer_path):
    os.mkdir(os.path.join(transfer_path, 'objects'))
    os.mkdir(os.path.join(transfer_path, 'logs'))
    src_files = os.listdir(transfer_path)

    # copy files and folders
    for name in src_files:
        full_name = os.path.join(transfer_path, name)
        try:
            if name != 'objects':
                if name != 'submissionDocumentation':
                    if name != 'processingMCP.xml':
                        print(full_name)
                        print(name)
                        dest = os.path.join(transfer_path, os.path.join('objects/',name))
                        print(dest)
                        try:
                            shutil.move(full_name, dest)
                        except AttributeError as e:
                            print(e)
                        except OSError as e:
                            print(e)
        except OSError as e:
            print(e)

    print('move submission documentation into the /metadata/submissionDocumentation')
    source = os.path.join(transfer_path,'submissionDocumentation')
    destination = os.path.join(transfer_path, 'metadata/')
    shutil.move(source, destination)

    print('reset all file permissions')
    shutil.chown(os.path.join(transfer_path, 'objects'), 'archivematica', 'archivematica')
    shutil.chown(os.path.join(transfer_path, 'metadata'), 'archivematica', 'archivematica')
    shutil.chown(os.path.join(transfer_path, 'logs'), 'archivematica', 'archivematica')
    shutil.chown(os.path.join(transfer_path, 'processingMCP.xml'), 'archivematica', 'archivematica')
    for root, dirs, files in os.walk(transfer_path):
        for d in dirs:
            print(d)
            #shutil.chown(os.path.join(transfer_path, d), 'archivematica', 'archivematica')
        for f in files:
            print(f)
            #shutil.chown(os.path.join(transfer_path, f), 'archivematica', 'archivematica')

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
