#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys
import pwd
import grp

def main(transfer_path):
    # path for metadata.json
    md_json = os.path.join(transfer_path, os.path.join('metadata', os.path.join('submissionDocumentation','metadata.json')))

    # Open metadata.json
    # try this https://github.com/evidens/json2csv

    # path for metadata.csv
    md_csv = os.path.join(transfer_path, os.path.join('metadata','metadata.csv'))


    print('Reset file permissions to archivematica:archivematica')

    uid = pwd.getpwnam("archivematica").pw_uid
    gid = grp.getgrnam("archivematica").gr_gid
    os.chown(md_csv, uid,gid)


if __name__ == '__main__':
    transfer_path = sys.argv[1]
    main(transfer_path)
