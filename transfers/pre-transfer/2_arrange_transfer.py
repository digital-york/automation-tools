#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys
import pwd
import grp

def main(transfer_path):
    src_files = os.listdir(transfer_path)

    print('Create folders')

    # TODO check there isn't already a folder called objects, if there is rename it; ditto logs; ditto metadata
    ids = transfer_path.split('/')
    os.mkdir(ids[len(ids) - 2])
    os.mkdir("objects")
    shutil.move("objects",transfer_path)
    shutil.move(ids[len(ids) - 2], os.path.join(transfer_path, 'objects'))
    os.mkdir("metadata")
    shutil.move("metadata",transfer_path)
    os.mkdir("submissionDocumentation") #temporary - will always be there in transfer
    shutil.move("submissionDocumentation",os.path.join(transfer_path,'metadata'))
    dest_s = os.path.join(transfer_path, os.path.join('metadata','submissionDocumentation'))

    print('Arrange files and folders')

    for name in src_files:
        full_name = os.path.join(transfer_path, name)
        try:
            if name != 'submissionDocumentation' and name != 'metadata' and name != 'processingMCP.xml' and name != 'metadata.json':
                dest = os.path.join(transfer_path, os.path.join('objects',os.path.join(ids[len(ids) - 2],name)))
                print(dest)
                shutil.move(full_name, dest)
            elif name == 'metadata.json':
                shutil.move(full_name, dest_s)
            elif name == 'submissionDocumentation':
                shutil.move(full_name, dest_s)

        except AttributeError as e:
            print(e)
        except OSError as e:
            print(e)

    os.mkdir('logs')
    shutil.move('logs', transfer_path)

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
