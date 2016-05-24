#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys

def main(sip_uuid,transfer_path):
    print sip_uuid
    print transfer_path

if __name__ == '__main__':
    print(sys.argv)
    sip_uuid = sys.argv[1]
    transfer_path = sys.argv[2]
    main(sip_uuid,transfer_path)
