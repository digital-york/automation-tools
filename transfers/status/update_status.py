#!/usr/bin/env python

from __future__ import print_function
import sys
import requests
import time
import json
import os

def main(status, uuid, transfer_path, url, params,state,ts_path):

    if status == 'NOT APPROVED':
        hydra_params = {"aip": {
            "status": status,
            "api-key": params['api_key'],
        }
        }
    else:
        # type and name - not needed, can we assume type is SIP?

        aip_object = transfer_path.split('/')[1]
        hydra_url = 'http://10.0.2.2:3000/api/v1/aip/' + aip_object
        aip_location = ''
        sip_uuid = uuid

        if state == 'transfer':
            count = 0
            while _status_checker(status, count) == 'go':
                if count > 0:
                    time.sleep(30)
                status,sip_uuid = get_transfer_details(uuid, url, params)
                count += 1
        elif state == 'ingest':
            status = 'COMPLETE'
        count = 0
        if status == 'COMPLETE':
            status = ''
            while _status_checker(status, count) == 'go':
                if count > 0:
                    time.sleep(30)
                status = get_sip_details(sip_uuid, url, params)
                count += 1
            count = 0
            if status == 'COMPLETE':
                print(count)
                status = ''
                while _status_checker(status, count) == 'go':
                    if count > 0:
                        time.sleep(30)
                    status, aip_location = get_aip_details(sip_uuid, url)
                    count += 1

        if status == 'UPLOADED':
            if ts_path != None:
               print('now we delete: ' + os.path.join(ts_path,transfer_path))
        elif status == 'FAIL':
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
        print('ERROR: the hydra object could not be updated. Params were: ' + str(hydra_params))
    else:
        print('Updated hydra object: ' + str(update))

# do something on failure

def get_transfer_details(uuid, url, params):
    get_url = url + '/api/transfer/status/' + uuid + '/'
    aip = _call_url_json(get_url, params, 'get')
    status = aip['status']
    try:
        sip_uuid = aip['sip_uuid']
    except KeyError:
        sip_uuid = ''
    return (status, sip_uuid)

def get_sip_details(sip_uuid, url, params):
    get_url = url + '/api/ingest/status/' + sip_uuid + '/'
    aip = _call_url_json(get_url, params, 'get')
    status = aip['status']
    return status

def get_aip_details(uuid, url):
    # extract aip info
    # results-uuid, status, current_path, size
    get_url = url + ':8000/api/v2/search/package/'
    params = {'uuid': uuid}
    aip = _call_url_json(get_url, params, 'get')
    status = aip['results'][0]['status']
    aip_location = aip['results'][0]['current_path']
    return (status, aip_location)


def _status_checker(status, count):
    if status == "COMPLETE" or status == 'UPLOADED':
        return 'stop'
    elif count > 2:
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
    #LOGGER.debug('URL: %s; params: %s;', url, params)
    if method == 'get':
        response = requests.get(url, params=params)
    elif method == 'put':
        response = requests.put(url, data=json.dumps(params))
    # LOGGER.debug('Response: %s', response)
    if not response.ok:
        print('Request to %s returned %s %s', url, response.status_code, response.reason)
        # LOGGER.warning('Request to %s returned %s %s', url, response.status_code, response.reason)
        # LOGGER.debug('Response: %s', response.text)
        return None
    try:
        return response.json()
    except ValueError:  # JSON could not be decoded
        print('Could not parse JSON from response: %s', response.text)
        # LOGGER.warning('Could not parse JSON from response: %s', response.text)
        return None

if __name__ == '__main__':
    status = sys.argv[1]
    url = sys.argv[2]
    params = {'username': sys.argv[3], 'api_key': sys.argv[4]}
    transfer_path = sys.argv[5]
    uuid = sys.argv[6]
    try:
        state = sys.argv[7]
    except IndexError:
        state = 'transfer'
    try:
        ts_path = sys.argv[8]
        print(sys.argv[8])
    except IndexError:
        ts_path = None
    main(status, uuid, transfer_path, url, params, state,ts_path)
