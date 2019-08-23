#!/usr/bin/python3

import json as jsn
import requests
import os
import sys
import re
import argparse
from prettytable import PrettyTable
from prettytable import MSWORD_FRIENDLY


def check_validity(orion):
    link = orion + '/version'
    reply = requests.get(link)
    if reply.status_code == 200:
        return True
    else:
        return False


if __name__ == '__main__':

    url = ''
    out = []
    done = []
    item = {}
    headers = {}
    count = {'config': 0,
             'added': 0,
             'deleted': 0,
             'found': 0,
             'ignored': 0,
             'disabled': 0,
             'errors': 0}

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_path', help='path to config file',  action='store')
    parser.add_argument('--prod', dest='prod', help='subscribe prod environment',  action='store_true')
    args = parser.parse_args()
    config_path = args.config_path
    prod = args.prod

    if not os.path.isfile(config_path):
        print('Config file not found')
        config_file = None
        sys.exit(1)

    try:
        with open(config_path) as f:
            cfg = jsn.load(f)
    except ValueError:
        print('Unsupported config type')
        sys.exit(1)

    print('Checking config')
    config = dict()
    try:
        services = cfg['services']
        prefix = cfg['prefix']
        config = list()
        for el in cfg['list']:
            tmp = dict()

            if not el['source'].startswith('http'):
                tmp['source'] = 'http://' + el['source']
            else:
                tmp['source'] = el['source']

            if not el['target'].startswith('http'):
                tmp['target'] = 'http://' + el['target']
            else:
                tmp['target'] = el['target']

            tmp['description'] = el['description']
            tmp['template'] = el['template']

            if 'fw_id' in el:
                tmp['fw_id'] = el['fw_id']
            else:
                tmp['fw_id'] = ''
            if 'state' in el:
                tmp['state'] = el['state']
            if 'test' in el:
                tmp['test'] = el['test']
            if 'service' in el:
                tmp['service'] = el['service']
            if 'path' in el:
                tmp['path'] = el['path']
            if 'token' in el:
                tmp['path'] = el['token']

            config.append(tmp)
    except KeyError:
        print('Config error')
        sys.exit(1)

    print('Started')
    for el in config:
        count['config'] += 1
        headers.clear()

        print('Working with', el['source'])
        if check_validity(el['source']):
            url = el['source']+'/v2/subscriptions'

            if 'token'in el:
                headers['X-Auth-Token'] = el['token']

            # Clean block. We don't store subscriptions, so simply remove everything belongs to prefix, e.g. 'FW--'
            if not el['source'] in done:
                done.append(el['source'])

                for service in services:
                    headers['Fiware-Service'] = service
                    resp = requests.get(url + '?limit=200', headers=headers).json()
                    for sub in resp:
                        count['found'] += 1
                        ignore = False
                        item.clear()
                        if 'description' in sub:
                            if re.search(prefix, sub['description']):
                                requests.delete(url+'/'+sub['id'], headers=headers)
                                item = {'type': 'deleted',
                                        'source': el['source'],
                                        'target': sub['notification']['http']['url'],
                                        'service': service,
                                        'path': '',
                                        'description': sub['description'],
                                        'id': sub['id'],
                                        'fw_id': '',
                                        'comment': ''}
                                out.append(dict(item))
                                count['deleted'] += 1
                            else:
                                ignore = True
                                item['description'] = sub['description']
                        else:
                            ignore = True
                            item['description'] = ''

                        if ignore:
                            item['type'] = 'ignored'
                            item['source'] = el['source']
                            if 'http' in sub['notification']:
                                item['target'] = sub['notification']['http']['url']
                            if 'httpCustom' in sub['notification']:
                                item['target'] = sub['notification']['httpCustom']['url']
                            item['service'] = service
                            item['path'] = ''
                            item['id'] = sub['id']
                            item['fw_id'] = ''

                            out.append(dict(item))
                            count['ignored'] += 1

            # Check if valid for test
            check = True
            if 'test' in el:
                if el['test'] == 'false':
                    if not prod:
                        check = False

            # Check if enabled
            state = True
            if 'state' in el:
                if el['state'] == 'disabled':
                    state = False

            if not check or not state:
                count['disabled'] += 1
            else:
                # Add subscription
                if 'template' in el:
                    file = os.path.split(os.path.abspath(__file__))[0] + '/templates/' + el['template']+'.json'
                else:
                    file = os.path.split(os.path.abspath(__file__))[0] + '/templates/default.json'

                template = jsn.load(open(file))
                template['notification']['http']['url'] = el['target']+template['notification']['http']['url']
                template['description'] = el['description']

                data = jsn.dumps(template)

                headers['Content-Type'] = 'application/json'

                if 'service' in el:
                    headers['Fiware-Service'] = el['service']
                else:
                    el['service'] = ''
                    if 'Fiware-Service' in headers:
                        del headers['Fiware-Service']

                if 'path' in el:
                    headers['Fiware-ServicePath'] = el['path']
                else:
                    el['path'] = ''
                    if 'Fiware-ServicePath' in headers:
                        del headers['Fiware-ServicePath']

                resp = requests.post(url, headers=headers, data=data)

                if resp.status_code == 201:
                    item = {'type': 'added',
                            'source': el['source'],
                            'target': template['notification']['http']['url'],
                            'service': el['service'],
                            'path': el['path'],
                            'description': template['description'],
                            'id': re.sub('/v2/subscriptions/', '', resp.headers['Location']),
                            'fw_id': el['fw_id']}
                    out.append(dict(item))
                    count['added'] += 1
                else:
                    sys.exit(1)
        else:
            count['errors'] += 1
            item = {'type': 'error',
                    'source': el['source'],
                    'target': el['target'],
                    'service': '',
                    'path': '',
                    'description': '',
                    'id': '',
                    'fw_id': el['fw_id']}
            out.append(dict(item))
    # Show results in table format
    print('TOTAL:')
    print('config:  ', count['config'])
    print('disabled: ', count['disabled'])
    print('------------')
    print('found:   ', count['found'])
    print('ignored: ', count['ignored'])
    print('deleted: ', count['deleted'])
    print('added :  ', count['added'])
    print('errors :  ', count['errors'])

    table = PrettyTable(['type', 'source', 'target', 'service', 'path', 'description', 'id', 'fw_id'])

    for el in out:
        table.add_row([el['type'],
                       el['source'],
                       el['target'],
                       el['service'],
                       el['path'],
                       el['description'],
                       el['id'],
                       el['fw_id']])

    table.border = False
    table.set_style(MSWORD_FRIENDLY)
    table.align = 'l'
    table.sortby = 'type'
    print(table)
