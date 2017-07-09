#!/usr/bin/env python
"""
Automate Status Updates

Helper script to automate getting status info from Archivematica.
"""

from __future__ import print_function, unicode_literals
import argparse
import ast
import base64
import logging
import logging.config  # Has to be imported separately
import os
import requests
from six.moves import configparser
import subprocess
import sys
import time
import json
import shutil

# from . import models
import models
import amclient

try:
    from os import fsencode, fsdecode
except ImportError:
    # Cribbed & modified from Python3's OS module to support Python2
    def fsencode(filename):
        encoding = sys.getfilesystemencoding()
        if isinstance(filename, str):
            return filename
        elif isinstance(filename, unicode):
            return filename.encode(encoding)
        else:
            raise TypeError("expect bytes or str, not %s" % type(filename).__name__)


    def fsdecode(filename):
        encoding = sys.getfilesystemencoding()
        if isinstance(filename, unicode):
            return filename
        elif isinstance(filename, str):
            return filename.decode(encoding)
        else:
            raise TypeError("expect bytes or str, not %s" % type(filename).__name__)

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(THIS_DIR)

# should I create a different logger?
LOGGER = logging.getLogger('transfer')

CONFIG_FILE = None


def get_setting(setting, default=None):
    config = configparser.SafeConfigParser()
    try:
        config.read(CONFIG_FILE)
        return config.get('transfers', setting)
    except Exception:
        return default


def setup(config_file):
    global CONFIG_FILE
    CONFIG_FILE = config_file
    models.init(get_setting('databasefile', os.path.join(THIS_DIR, 'transfers.db')))

    # Configure logging
    default_logfile = os.path.join(THIS_DIR, 'automate-transfer.log')
    CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(levelname)-8s  %(asctime)s  %(filename)s:%(lineno)-4s %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': get_setting('logfile', default_logfile),
                'backupCount': 2,
                'maxBytes': 10 * 1024,
            },
        },
        'loggers': {
            'transfer': {
                'level': 'INFO',  # One of INFO, DEBUG, WARNING, ERROR, CRITICAL
                'handlers': ['console', 'file'],
            },
        },
    }
    logging.config.dictConfig(CONFIG)


def _call_url_json(url, params, method):
    """
    Helper to GET a URL where the expected response is 200 with JSON.

    :param str url: URL to call
    :param dict params: Params to pass to requests.get
    :returns: Dict of the returned JSON or None
    """
    LOGGER.debug('URL: %s; params: %s;', url, params)
    if method == 'get':
        response = requests.get(url, params=params, verify=False)
    elif method == 'put':
        response = requests.put(url, data=json.dumps(params), verify=False)
    elif method == 'post':
        response = requests.post(url, data=json.dumps(params), verify=False)
    LOGGER.debug('Response: %s', response)
    if not response.ok:
        LOGGER.warning('Request to %s returned %s %s', url, response.status_code, response.reason)
        LOGGER.debug('Response: %s', response.text)
        return None
    try:
        return response.json()
    except ValueError:  # JSON could not be decoded
        if response.status_code != 204:   # don't bother logging warning if 'No Content' response
            LOGGER.warning('Could not parse JSON from response: %s', response.text)
        return None


def get_status(am_url, am_user, am_api_key, unit_uuid, unit_type, session):
    """
    Get status of the SIP or Transfer with unit_uuid.

    :param str unit_uuid: UUID of the unit to query for.
    :param str unit_type: 'ingest' or 'transfer'
    :returns: Dict with status of the unit from Archivematica or None.
    """

    unit_info = None

    # Get status
    url = am_url + '/api/' + unit_type + '/status/' + unit_uuid + '/'
    params = {'username': am_user, 'api_key': am_api_key}
    try:
        unit_info = _call_url_json(url, params, 'get')
    except ValueError as e:  # JSON could not be decoded
        LOGGER.error(e.message)
        return None

    # If Transfer is complete, get the SIP's status
    if unit_info and unit_type == 'transfer' and unit_info['status'] == 'COMPLETE' and unit_info[
        'sip_uuid'] != 'BACKLOG':
        LOGGER.info('%s is a complete transfer, fetching SIP %s status.', unit_uuid, unit_info['sip_uuid'])
        try:
        # Update DB to refer to this one
            db_unit = session.query(models.Unit).filter_by(unit_type=unit_type, uuid=unit_uuid).one()
            db_unit.unit_type = 'ingest'
            db_unit.uuid = unit_info['sip_uuid']
            # Get SIP status
            url = am_url + '/api/ingest/status/' + unit_info['sip_uuid'] + '/'
            unit_info = _call_url_json(url, params, 'get')
        except ValueError as e:  # JSON could not be decoded
            LOGGER.error(e.message)
        return unit_info
    if unit_info == None:
        LOGGER.warning("nothing returned from archivematica API, unit_info is empty")
        return
    else:
        return unit_info


def run_scripts(directory, *args):
    """
    Run all executable scripts in directory relative to this file.

    :param str directory: Directory in the same folder as this file to run scripts from.
    :param args: All other parameters will be passed to called scripts.
    :return: None
    """
    directory = os.path.join(THIS_DIR, directory)
    if not os.path.isdir(directory):
        LOGGER.warning('%s is not a directory. No scripts to run.', directory)
        return
    script_args = list(args)
    LOGGER.debug('script_args: %s', script_args)
    for script in sorted(os.listdir(directory)):
        LOGGER.debug('Script: %s', script)
        script_path = os.path.join(directory, script)
        if not os.path.isfile(script_path):
            LOGGER.info('%s is not a file, skipping', script)
            continue
        if not os.access(script_path, os.X_OK):
            LOGGER.info('%s is not executable, skipping', script)
            continue
        LOGGER.info('Running %s "%s"', script_path, '" "'.join(args))
        p = subprocess.Popen([script_path] + script_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        LOGGER.info('Return code: %s', p.returncode)
        LOGGER.info('stdout: %s', stdout)
        if stderr:
            LOGGER.warning('stderr: %s', stderr)


def update_status(api_key, status, hydra_url, h_id, aip_uuid='', location=''):
    hydra_params = {"package":
        {
        "aip_uuid": aip_uuid,
        "status": status,
        "current_path": location,
        "api-key": api_key
        }
        }
    try:
        update = _call_url_json(hydra_url + '/api/v1/aip/' + h_id, hydra_params, 'put')
        if update == None:
            LOGGER.error('ERROR: the hydra object could not be updated. Params were: ' + str(hydra_params))
            raise
        else:
            LOGGER.info('Updated hydra object: ' + str(update))
    except Exception as e:
        LOGGER.error(e.message)
        raise Exception('Problem updating the hydra object')

def update_dip(api_key, hydra_url, h_id, dip_uuid,current_path,resource_uri,current_location,size):
    hydra_params = {"package":
            {
            "dip_uuid": dip_uuid,
            "api-key": api_key,
            "current_path":current_path,
            "resource_uri":resource_uri,
            "current_location":current_location,
            "size":size
            }
        }
    try:
        update = _call_url_json(hydra_url + '/api/v1/dip/' + h_id, hydra_params, 'put')
        if update == None:
            LOGGER.error('ERROR: the hydra object could not be updated. Params were: ' + str(hydra_params))
            raise
        else:
            LOGGER.info('Updated hydra object: ' + str(update))
    except Exception as e:
        LOGGER.error(e.message)
        raise Exception('Problem updating the hydra object')

def waiting_dips(api_key, hydra_url):
    hydra_params = {"package":
            {
            "api-key": api_key
            }
        }
    try:
        waiting = _call_url_json(hydra_url + '/api/v1/dip/waiting', hydra_params, 'post')
        if waiting == None:
            LOGGER.info('Nothing waiting.')
            return waiting
        else:
            LOGGER.info('Waiting: %s', waiting)
            return waiting
    except Exception as e:
        LOGGER.error(e.message)
        raise Exception('Problem updating the hydra object')

def get_aip_details(uuid, ss_url, ss_user, ss_api_key):
    # extract aip info
    # results-uuid, status, current_path, size
    try:
        get_url = ss_url + '/api/v2/file/' + uuid
        params = {'username': ss_user, 'api_key': ss_api_key}
        aip = _call_url_json(get_url, params, 'get')
        status = aip['status']
        current_path = aip['current_path']
        return (status, current_path)
    except Exception as e:
        LOGGER.error(e.message)


def get_transfer_folders_list(ss_url, ss_user, ss_api_key, ts_location_uuid, path_prefix, depth):
    """
    Helper to find the first directory that doesn't have an associated transfer.

    :param ss_url: URL of the Storage Sevice to query
    :param ss_user: User on the Storage Service for authentication
    :param ss_api_key: API key for user on the Storage Service for authentication
    :param ts_location_uuid: UUID of the transfer source Location
    :param path_prefix: Relative path inside the Location to work with.
    :param depth: Depth relative to path_prefix to create a transfer from. Should be 1 or greater.
    :returns: Path relative to TS Location of the new transfer
    """
    try:
        # Get sorted list from source dir
        url = ss_url + '/api/v2/location/' + ts_location_uuid + '/browse/'
        params = {
            'username': ss_user,
            'api_key': ss_api_key,
        }
        if path_prefix:
            params['path'] = base64.b64encode(path_prefix)
        browse_info = _call_url_json(url, params, 'get')
        if browse_info is None:
            return None
        entries = browse_info['directories']
        entries = [base64.b64decode(e.encode('utf8')) for e in entries]
        LOGGER.debug('Entries: %s', entries)
        entries = [os.path.join(path_prefix, e) for e in entries]
        # If at the correct depth, check if any of these have not been made into transfers yet
        if depth <= 1:
            # Find the directories that are not already in the DB using sets
            LOGGER.debug("New transfer candidates: %s", entries)
            # Sort, take the first
            entries = sorted(list(entries))
            if not entries:
                return None
            return entries
        else:  # if depth > 1
            # Recurse on each directory
            listy = []
            for e in entries:
                LOGGER.debug('New path: %s', e)
                try:
                    l = get_transfer_folders_list(ss_url, ss_user, ss_api_key, ts_location_uuid, e, depth - 1)
                    if l is not None:
                        listy.append(l[0].split('/')[-1])  # last element will be rightmost folder
                except Exception as ex:
                    LOGGER.error(ex)
            if listy != []:
                entries = listy
        return entries

    except Exception as e:
        LOGGER.error(e.message)


def main(am_user, am_api_key, ss_user, ss_api_key, ts_uuid, ts_basepath, ts_path, depth, am_url, ss_url, hydra_url,
         config_file=None):
    setup(config_file)

    LOGGER.info("Waking up")

    session = models.Session()

    # Check for evidence that this is already running
    default_pidfile = os.path.join(THIS_DIR, 'pid.lck')
    pid_file = get_setting('pidfile', default_pidfile)
    try:
        # Open PID file only if it doesn't exist for read/write
        f = os.fdopen(os.open(pid_file, os.O_CREAT | os.O_EXCL | os.O_RDWR), 'r+')
    except:
        LOGGER.info('This script is already running. To override this behaviour and start a new run, remove %s',
                    pid_file)
        return 0
    else:
        pid = os.getpid()
        f.write(str(pid))
        f.close()

    # Get list of folders
    folders = get_transfer_folders_list(ss_url, ss_user, ss_api_key, ts_uuid, ts_path, depth)

    try:
        units = session.query(models.Unit)  # .filter_by(unit_type='PROCESSING')
        # if using this for status of DIP, need to change this, eg. for uploaded, get DIP and check status of that
        for i in units:
            f = i.path.split('/')[-1]  # last element will be rightmost folder
            if f in folders:
                LOGGER.info('DOING ' + f)
                if i.unit_type == 'transfer':
                    status_info = get_status(am_url, am_user, am_api_key, i.uuid, i.unit_type, session)
                    status = status_info['status']
                    status_info['status']
                    # update hydra
                    update_status(am_api_key, status, hydra_url, f)
                elif i.unit_type == 'ingest':
                    status_info = get_status(am_url, am_user, am_api_key, i.uuid, i.unit_type, session)
                    # update hydra
                    status = status_info['status']
                    try:
                        update_status(am_api_key, status, hydra_url, f, status_info['uuid'], status_info['path'])
                        status, current_path = get_aip_details(i.uuid, ss_url, ss_user, ss_api_key)
                        update_status(am_api_key, status, hydra_url, f, i.uuid,
                                      current_path)
                    except Exception as e:
                        LOGGER.error('ERROR: %s', e)
                        os.remove(pid_file)
                        return 0
                    if status == 'UPLOADED':
                        delete_path = os.path.join(ts_basepath, i.path)
                        LOGGER.info('Deleting: ' + delete_path)
                        shutil.rmtree(delete_path)

    except Exception as e:
        LOGGER.error('ERROR: %s', e)

    try:
        # call the hydra api for waiting dips
        dips = waiting_dips(am_api_key, hydra_url)
        # call the hydra api to update the dip
        if dips != None:
            for key, value in dips.items():
                try:
                    # get dip from aip using the amclient script
                    kwargs = {
                        'ss_user_name':ss_user,
                        'ss_url': ss_url,
                        'ss_api_key':ss_api_key,
                        'aip_uuid': value
                        }
                    # should we check that the aip is UPLOADED?
                    client = amclient.AMClient(**kwargs)
                    data = client.aip2dips()
                    LOGGER.info(data)
                    if len(data) > 0:
                        d = data[0]
                        LOGGER.info('Updating DIP: %s', d['uuid'])
                        update_dip(am_api_key, hydra_url, key, d['uuid'],
                                   d['current_path'],
                                   d['resource_uri'],
                                   d['current_location'],
                                   d['size'])
                    else:
                        LOGGER.warning('AMClient returned an empty list')
                except Exception as e:
                    LOGGER.error('ERROR: %s', e)

    except Exception as e:
        LOGGER.error('ERROR: %s', e)
        return 0

    session.commit()
    os.remove(pid_file)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-u', '--user', metavar='USERNAME', required=True,
                        help='Username of the Archivematica dashboard user to authenticate as.')
    parser.add_argument('-k', '--api-key', metavar='KEY', required=True,
                        help='API key of the Archivematica dashboard user.')
    parser.add_argument('--ss-user', metavar='USERNAME', required=True,
                        help='Username of the Storage Service user to authenticate as.')
    parser.add_argument('--ss-api-key', metavar='KEY', required=True, help='API key of the Storage Service user.')
    parser.add_argument('-t', '--transfer-source', metavar='UUID', required=True,
                        help='Transfer Source Location UUID to fetch transfers from.')
    parser.add_argument('--transfer-basepath', metavar='BASEPATH', help='Absolute path to the Transfer Source. Default: ""',
                        type=fsencode, default=b'')  # Convert to bytes from unicode str provided by command line
    parser.add_argument('--transfer-path', metavar='PATH', help='Relative path within the Transfer Source. Default: ""',
                        type=fsencode, default=b'')  # Convert to bytes from unicode str provided by command line
    parser.add_argument('--depth', '-d',
                        help='Depth to create the transfers from relative to the transfer source location and path. Default of 1 creates transfers from the children of transfer-path.',
                        type=int, default=1)
    parser.add_argument('--am-url', '-a', metavar='URL', help='Archivematica URL. Default: http://127.0.0.1',
                        default='http://127.0.0.1')
    parser.add_argument('--ss-url', '-s', metavar='URL', help='Storage Service URL. Default: http://127.0.0.1:8000',
                        default='http://127.0.0.1:8000')
    parser.add_argument('--hydra-url', metavar='URL', help='URL for Hydra app to update',
                        default=None)
    parser.add_argument('-c', '--config-file', metavar='FILE', help='Configuration file(log/db/PID files)',
                        default=None)

    # Logging
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Increase the debugging output.')
    parser.add_argument('--quiet', '-q', action='count', default=0, help='Decrease the debugging output')
    parser.add_argument('--log-level', choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'], default=None,
                        help='Set the debugging output level. This will override -q and -v')

    args = parser.parse_args()

    log_levels = {
        2: 'ERROR',
        1: 'WARNING',
        0: 'INFO',
        -1: 'DEBUG',
    }

    if args.log_level is None:
        level = args.quiet - args.verbose
        level = max(level, -1)  # No smaller than -1
        level = min(level, 2)  # No larger than 2
        log_level = log_levels[level]
    else:
        log_level = args.log_level

    sys.exit(main(
        am_user=args.user,
        am_api_key=args.api_key,
        ss_user=args.ss_user,
        ss_api_key=args.ss_api_key,
        ts_uuid=args.transfer_source,
        ts_basepath=args.transfer_basepath,
        ts_path=args.transfer_path,
        depth=args.depth,
        am_url=args.am_url,
        ss_url=args.ss_url,
        hydra_url=args.hydra_url,
        config_file=args.config_file,
    ))
