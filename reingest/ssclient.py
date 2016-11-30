#!/usr/bin/env python

import json
import logging
import optparse
import pprint
import re
import requests
import sys
import time

# Change the following to ``True`` to see full requests being sent.
if False:
    try:
        import http.client as http_client
    except ImportError:
        # Python 2
        import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


class SSClient:

    def __init__(self,
                 ss_url,
                 ss_user_name,
                 ss_api_key,
                 am_url,
                 am_user_name,
                 am_api_key,
                 output_mode):
        self.ss_url = ss_url
        self.ss_user_name = ss_user_name
        self.ss_api_key = ss_api_key
        self.am_url = am_url
        self.am_user_name = am_user_name
        self.am_api_key = am_api_key
        self.output_mode = output_mode

    def search_package(self, params):
        params = '&'.join(['{}={}'.format(k, v) for k, v in params.items()])
        url = '{}/api/v2/search/package/?{}'.format(
            self.ss_url, params)
        r = requests.get(url)
        return r.json()

    def stdout(self, stuff):
        if self.output_mode == 'json':
            print(json.dumps(stuff))
        else:
            pprint.pprint(stuff)

    def get_all_aips(self):
        return self.get_all_packages('AIP')

    def get_all_dips(self):
        return self.get_all_packages('DIP')

    def get_all_packages(self, ptype='AIP', packages=None, next=None):
        """Get all packages (AIPs or DIPs) in the Storage Service, following
        the pagination trail if necessary.
        """
        if not packages:
            packages = []
        if next:
            r = requests.get(next).json()
        else:
            r = self.search_package({'package_type': ptype})
        packages = packages + r['results']
        if r['next']:
            packages = self.get_all_packages(ptype, packages, r['next'])
        return packages

    def aip2dips(self, aip_uuid):
        """Get all DIPS created from AIP with UUID ``aip_uuid``."""
        dips = self.get_all_dips()
        return [d for d in dips if
                d['current_path'].endswith(aip_uuid)]

    def get_all_aips_and_their_dips(self):
        """Get all AIP UUIDs and map them to their DIP UUIDs, if any."""
        aips = self.get_all_aips()
        dips = self.get_all_dips()
        return dict([(a['uuid'],
                      [d['uuid'] for d in dips if
                       d['current_path'].endswith(a['uuid'])])
                     for a in aips])

    def download_dip(self, dip_uuid):
        """Download the DIP with UUID ``dip_uuid``."""
        url = '{}/api/v2/file/{}/download/'.format(self.ss_url, dip_uuid)
        r = requests.get(
            url,
            params={'username': self.ss_user_name,
                    'api_key': self.ss_api_key},
            stream=True)
        print(r.status_code)
        if r.status_code == 200:
            local_filename = re.findall('filename="(.+)"',
                                        r.headers['content-disposition'])[0]
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(local_filename)
            return local_filename
        else:
            print('Unable to download DIP {}'.format(dip_uuid))

    def reingest_aip(self, aip_uuid):
        """Request that the Storage Service reingest the AIP with UUID
        ``aip_uuid``. Example usage::

            $ ./ssclient.py reingest 198e7890-f19e-4b41-a172-953380e543e5 \
                 --ss-key=fdbdf0f21196c6e1f9884452172e330ad41d8cae \
                 --am-key=1b6aac9388733df195d4f63a8c6eb53dc1cffa31
        """
        url = '{}/api/v2/file/{}/reingest/'.format(self.ss_url, aip_uuid)
        pipeline = self.aip_uuid2pipeline_uuid(aip_uuid)
        # At present, the Storage Service will not make use of a
        # 'processing_config' argument in a reingest_request.
        payload = {
            'pipeline': pipeline,
            'reingest_type': 'objects',
        }
        auth_header = {'Authorization': 'ApiKey {}:{}'.format(
                       self.ss_user_name, self.ss_api_key)}
        r = requests.post(url, json=payload, headers=auth_header)
        try:
            assert r.status_code == 202
            print('Reingest of AIP {} initiated.'.format(aip_uuid))
        except AssertionError:
            print('ERROR: something went wrong when attempting to reingest AIP'
                  ' {}.'.format(aip_uuid))
        self.approve_reingest(aip_uuid)

    approve_reingest_retry_count = 5

    def approve_reingest(self, reingest_uuid):
        if self.am_url and self.am_api_key and self.am_user_name:
            for i in range(self.approve_reingest_retry_count):
                result = self._approve_reingest(reingest_uuid)
                if result:
                    print('Approved re-ingest!')
                    break
            else:
                print('Failed to approve re-ingest; please do it manually via'
                      ' the dashboard interface.')
        else:
            print('Archivematica API not information provided, cannot approve'
                  ' reingest.')

    def _approve_reingest(self, reingest_uuid):
        """Approve re-ingest with UUID ``reingest_uuid``.

        :returns: UUID of the approved ingest or None.
        """
        time.sleep(5)
        # List available ingests
        get_url = '{}/api/ingest/waiting'.format(self.am_url)
        params = {'username': self.am_user_name, 'api_key': self.am_api_key}
        waiting_transfers = requests.get(get_url, params).json()
        if waiting_transfers is None:
            print('No waiting transfer ')
            return None
        elif waiting_transfers.get('error'):
            print(waiting_transfers.get('message', 'No error message provided'))
            return None
        for a in waiting_transfers['results']:
            print("Found waiting transfer: %s", a['sip_directory'])
            if a['sip_uuid'] == reingest_uuid:
                url = '{}/api/ingest/reingest/approve'.format(self.am_url)
                payload = {
                    'username': self.am_user_name,
                    'api_key': self.am_api_key,
                    'name': a['sip_directory'],
                    'uuid': reingest_uuid
                }
                r = requests.post(url, data=payload)
                if r.status_code != 200:
                    return None
                return a['sip_uuid']
            else:
                print("%s is not what we are looking for", a['sip_directory'])
        else:
            return None

    def aip_uuid2pipeline_uuid(self, aip_uuid):
        """Return the origin pipeline UUID of the AIP with UUID
        ``aip_uuid``.
        """
        r = self.search_package({'package_type': 'AIP', 'uuid': aip_uuid})
        if r.get('count', 0) == 1:
            return r['results'][0]['origin_pipeline']
        return None


def get_parser():
    usage = ('%prog -- Archivematica Storage Service Client\n\n'
             '  %prog aips -- get all AIPS\n'
             '  %prog dips -- get all DIPS\n'
             '  %prog aip2dips UUID -- get DIP(s) from AIP UUID\n'
             '  %prog aips2dips -- get all AIPS and their DIP(s)\n'
             '  %prog downdip UUID -- download DIP with UUID')
    parser = optparse.OptionParser(usage=usage)
    def_am_url = "http://192.168.168.192"
    parser.add_option(
        "--am-url", dest="am_url", default=def_am_url,
        help="URL of Archivematica dashboard (default: {})".format(def_am_url))
    def_ss_url = "http://192.168.168.192:8000"
    parser.add_option(
        "--ss-url", dest="ss_url", default=def_ss_url,
        help="URL of Storage Service (default: {})".format(def_ss_url))
    def_user_name = 'test'
    parser.add_option(
        "--am-user", dest="am_user_name", default=def_user_name,
        help="Username of Archivematica dashboard user (default:"
             " {})".format(def_user_name))
    parser.add_option(
        "--ss-user", dest="ss_user_name", default=def_user_name,
        help="Username of Storage Service user (default:"
             " {})".format(def_user_name))
    parser.add_option(
        "--am-key", dest="am_api_key", default=None,
        help="API key of Archivematica dashboard user")
    parser.add_option(
        "--ss-key", dest="ss_api_key", default=None,
        help="API key of Storage Service user")
    parser.add_option(
        "-o", "--output", dest="output_mode", default='python',
        help="Output mode: how output to stdout should be printed: python"
             " (default) or JSON")
    return parser


def exit_ssclient(parser):
    parser.print_help()
    sys.exit(0)


if __name__ == '__main__':

    parser = get_parser()
    (options, args) = parser.parse_args()
    ss_client = SSClient(options.ss_url,
                         options.ss_user_name,
                         options.ss_api_key,
                         options.am_url,
                         options.am_user_name,
                         options.am_api_key,
                         options.output_mode)
    if len(args) < 1:
        exit_ssclient(parser)
    elif len(args) == 1 and args[0] == 'aips':
        ss_client.stdout(ss_client.get_all_aips())
    elif len(args) == 1 and args[0] == 'dips':
        ss_client.stdout(ss_client.get_all_dips())
    elif len(args) == 1 and args[0] == 'aips2dips':
        ss_client.stdout(ss_client.get_all_aips_and_their_dips())
    elif len(args) == 2 and args[0] == 'aip2dips':
        ss_client.stdout(ss_client.aip2dips(args[1]))
    elif len(args) == 2 and args[0] == 'downdip':
        ss_client.download_dip(args[1])
    elif len(args) == 2 and args[0] == 'reingest':
        ss_client.reingest_aip(args[1])
    else:
        exit_ssclient(parser)
