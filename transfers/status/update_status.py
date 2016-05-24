#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys

def main(transfer_path,sip_uuid):

    print(sip_uuid)
    # split at '/'
    # call localhost:3000/deposit/[1]
    # post aip_id, sip_uuid
    print(transfer_path)
    # call archivematica api to get aip_uuid
    # call archivematica api to get status

    print('http://192.168.168.192/api/transfer/status/' + sip_uuid + '/?username=geekscruff&api_key=66f63aa9f4d9c005e8920c588267f126c0d53bff')
    #

if __name__ == '__main__':
    transfer_path = sys.argv[1]
    sip_uuid = sys.argv[2]
    main(sip_uuid,transfer_path)
