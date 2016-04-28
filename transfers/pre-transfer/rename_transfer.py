#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys
import pwd
import grp
from shutil import ignore_patterns

def main(transfer_path):
    obj = transfer_path
    log = transfer_path
    md = transfer_path
    print('TRANSFER PATH ' + transfer_path)
    src_files = os.listdir(transfer_path)

    # copy files and folders
    for name in src_files:
        full_name = os.path.join(transfer_path, name)
        try:
            if name != 'objects':
                if name != 'submissionDocumentation':
                    if name != 'processingMCP.xml':
                        dest = os.path.join(transfer_path, os.path.join('objects',name))
                        try:
                            shutil.move(full_name, dest)
                        except AttributeError as e:
                            print(e)
                        except OSError as e:
                            print(e)
                elif name == 'submissionDocumentation':
                    dest = os.path.join(transfer_path, os.path.join('metadata', name))
                try:
                    shutil.move(full_name, dest)
                except AttributeError as e:
                    print(e)
                except OSError as e:
                    print(e)
        except OSError as e:
            print(e)

    uid = pwd.getpwnam("archivematica").pw_uid
    gid = grp.getgrnam("archivematica").gr_gid

    print('reset all file permissions')
    os.chown(os.path.join(obj, 'objects'), uid,gid)
    os.chown(os.path.join(transfer_path, 'metadata'), uid,gid)
    os.chown(os.path.join(transfer_path, 'metadata/submissionDocumentation'), uid, gid)
    os.chown(os.path.join(log, 'logs'), uid,gid)
    os.chown(os.path.join(transfer_path, 'processingMCP.xml'), uid,gid)

    for root, dirs, files in os.walk(transfer_path):
        for d in dirs:
            print(d)
            #shutil.chown(os.path.join(transfer_path, d), uid,gid)
        for f in files:
            print(f)
            #shutil.chown(os.path.join(transfer_path, f), uid,gid)

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
