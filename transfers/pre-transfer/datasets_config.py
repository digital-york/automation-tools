#!/usr/bin/env python

from __future__ import print_function
import os
import shutil
import sys

def main(transfer_path):
    # Update default config
    print('copying datasets processingMCP to', transfer_path)
    source = os.path.join("/var/archivematica/sharedDirectory/sharedMicroServiceTasksConfigs/processingMCPConfigs/", "datasetsProcessingMCP.xml")
    destination = os.path.join(transfer_path, 'processingMCP.xml')
    shutil.copyfile(source, destination)


if __name__ == '__main__':
    print(sys.argv)
    transfer_path = sys.argv[1]
    main(transfer_path)
