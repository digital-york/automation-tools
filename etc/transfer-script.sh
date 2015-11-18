#!/bin/bash
# transfer script example
# /etc/archivematica/automation-tools/transfer-script.sh
cd /usr/lib/archivematica/automation-tools/transfers/
/usr/share/python/automation-tools/bin/python transfer.py --user <user>  --api-key <apikey> --transfer-source <transfer_source_uuid>
