#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys
import pwd
import grp

def main(transfer_path):
    obj = transfer_path
    log = transfer_path
    md = transfer_path
    src_files = os.listdir(transfer_path)

    # TODO check there isn't already a folder called objects, if there is rename it; ditto logs; ditto metadata
    os.mkdir(os.path.join(obj,'objects'))

    print('Arrange files and folders')
    for name in src_files:
        full_name = os.path.join(transfer_path, name)
        try:
            if name != 'submissionDocumentation' and name != 'metadata' and name != 'processingMCP.xml' and name != 'metadata.json':
                dest = os.path.join(transfer_path, os.path.join('objects',name))
                shutil.move(full_name, dest)
            elif name == 'submissionDocumentation':
                os.mkdir(os.path.join(md, 'metadata'))
                dest_s = os.path.join(transfer_path, os.path.join('metadata', name))
                shutil.move(full_name, dest_s)
            elif name == 'metadata.json':
                dest_m = os.path.join(transfer_path, name)
                print('move metadata.json to ' + dest_m)
                shutil.move(full_name, dest_m)
                print(os.listdir(dest_m))
        except AttributeError as e:
            print(e)
        except OSError as e:
            print(e)

    os.mkdir(os.path.join(log, 'logs'))

    print('Reset all file permissions to archivematica:archivematica')

    uid = pwd.getpwnam("archivematica").pw_uid
    gid = grp.getgrnam("archivematica").gr_gid

    for root, dirs, files in os.walk(transfer_path):
        for d in dirs:
            os.chown(os.path.join(root, d), uid,gid)
        for f in files:
            os.chown(os.path.join(root, f), uid,gid)

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
