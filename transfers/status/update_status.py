#!/usr/bin/env python

from __future__ import print_function
import sys
import requests
import time
import json


def main(status, uuid, transfer_path, url, params):
    # call my update url
    # add these to config

    print("I have been called!!!")
    print(transfer_path)
    print(uuid)
    print(status)

    if status == 'NOT APPROVED':
        hydra_params = {"aip": {
            "status": status,
            "api-key": params['api_key'],
        }
        }
    else:
        print('here')
        # type and name - not needed, can we assume type is SIP?

        aip_object = transfer_path.split('/')[1]
        hydra_url = 'http://10.0.2.2:3000/api/v1/aip/' + aip_object
        aip_location = ''
        sip_uuid = ''

        count = 0
        while _status_checker(status, count) == 'go':
            print(count)
            if count > 0:
                time.sleep(30)
            status,sip_uuid = get_transfer_details(uuid, url, params)
            count += 1
        count = 0
        print(sip_uuid)
        if status == 'COMPLETE':
            print(count)
            status = ''
            while _status_checker(status, count) == 'go':
                if count > 0:
                    time.sleep(30)
                status = get_sip_details(sip_uuid, url, params)
                count += 1
            count = 0
            print(status)
            if status == 'COMPLETE':
                print(count)
                status = ''
                while _status_checker(status, count) == 'go':
                    if count > 0:
                        time.sleep(1)
                    status, aip_location = get_aip_details(sip_uuid, url)
                    count += 1

        if status == 'FAIL':
        # send email???
            print('fail')

        hydra_params = {"aip": {
            "aip_uuid": sip_uuid,
            "status": status,
            "aip_location": aip_location,
            "api-key": params['api_key']
        }
        }
    update = _call_url_json(hydra_url, hydra_params, 'put')
    if update == None:
        print('none')
    else:
        print(update)

# do something on failure

def get_transfer_details(uuid, url, params):
    get_url = url + '/api/transfer/status/' + uuid + '/'
    aip = _call_url_json(get_url, params, 'get')
    print('printing aip')
    print(aip)
    status = aip['status']
    try:
        sip_uuid = aip['sip_uuid']
    except KeyError:
        sip_uuid = ''
    return (status, sip_uuid)

def get_sip_details(sip_uuid, url, params):
    print(sip_uuid)
    get_url = url + '/api/ingest/status/' + sip_uuid + '/'
    aip = _call_url_json(get_url, params, 'get')
    print('printing aip 2')
    print(aip)
    status = aip['status']
    return status

def get_aip_details(uuid, url):
    # extract aip info
    # results-uuid, status, current_path, size
    get_url = url + ':8000/api/v2/search/package/'
    params = {'uuid': uuid}
    aip = _call_url_json(get_url, params, 'get')
    print('printing aip 3')
    print(aip)
    status = aip['results'][0]['status']
    aip_location = aip['results'][0]['current_path']
    return (status, aip_location)


def _status_checker(status, count):
    if status == "COMPLETE" or status == 'UPLOADED':
        return 'stop'
    elif count > 1:
        return 'stop'
    else:
        return 'go'


def _call_url_json(url, params, method):
    """
    Helper to GET a URL where the expected response is 200 with JSON.

    :param str url: URL to call
    :param dict params: Params to pass to requests.get
    :returns: Dict of the returned JSON or None
    """
    # LOGGER.debug('URL: %s; params: %s;', url, params)
    if method == 'get':
        response = requests.get(url, params=params)
    elif method == 'put':
        response = requests.put(url, data=json.dumps(params))
    # LOGGER.debug('Response: %s', response)
    if not response.ok:
        # LOGGER.warning('Request to %s returned %s %s', url, response.status_code, response.reason)
        # LOGGER.debug('Response: %s', response.text)
        return None
    try:
        return response.json()
    except ValueError:  # JSON could not be decoded
        print('ERROR')
        # LOGGER.warning('Could not parse JSON from response: %s', response.text)
        return None


if __name__ == '__main__':
    status = sys.argv[1]
    url = sys.argv[2]
    params = {'username': sys.argv[3], 'api_key': sys.argv[4]}
    transfer_path = sys.argv[5]
    uuid = sys.argv[6]
    # why does it take so long to run this?

main(status, uuid, transfer_path, url, params)
