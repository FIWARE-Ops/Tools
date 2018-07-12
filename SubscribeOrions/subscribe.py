#!/usr/bin/python3

import json as jsn
import requests
import os
import sys
import re
import argparse
from prettytable import PrettyTable
from prettytable import MSWORD_FRIENDLY


if __name__ == "__main__":

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
             'disabled': 0}

    parser = argparse.ArgumentParser()
    parser.add_argument('--token', dest='token', help='token',  action="store")
    parser.add_argument('--config', dest='config_path', help='path to config file',  action="store")
    parser.add_argument('--prod', dest='prod', help='subscribe prod environment',  action="store_true")
    args = parser.parse_args()
    token = args.token
    config_path = args.config_path
    prod = args.prod

    if not os.path.isfile(config_path):
        print('Config file not found')
        config_file = None
        sys.exit(1)

    try:
        with open(config_path) as f:
            config = jsn.load(f)
    except ValueError:
        print('Unsupported config type')
        sys.exit(1)

    print('Checking config')

    if 'services' not in config:
        print('Services list not defined')
        sys.exit(1)
    elif len(config['services']) == 0:
        print('Services list is empty')
        sys.exit(1)

    if 'prefix' not in config:
        print('Prefix not defined')
        sys.exit(1)

    if 'list' not in config:
        print('List not defined')
        sys.exit(1)
    elif len(config['list']) == 0:
        print('List list is empty')
        sys.exit(1)

    services = config['services']
    prefix = config['prefix']

    for el in config['list']:
        count['config'] += 1
        headers.clear()

        if not el['source'].startswith('http'):
            el['source'] = 'http://' + el['source']

        if not el['target'].startswith('http'):
            el['target'] = 'http://' + el['target']

        url = el['source']+'/v2/subscriptions'

        if 'token'in el:
            if token:
                headers['X-Auth-Token'] = token
            else:
                print('Token found in config, but not present in parameters')
                exit(1)

        # Clean block. We don't store subscriptions, so simply remove everything belongs to FW, e.g. 'FW--'
        if not el['source'] in done:
            done.append(el['source'])
            for service in services:
                headers['Fiware-Service'] = service
                resp = requests.get(url, headers=headers).json()
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
                                    'fw_id': "",
                                    'comment': ""}
                            out.append(dict(item))
                            count['deleted'] += 1
                        else:
                            ignore = True
                            item['description'] = sub['description']
                    else:
                        ignore = True
                        item['description'] = ""

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
                        item['fw_id'] = ""

                        out.append(dict(item))
                        count['ignored'] += 1

        # Check if prod only
        if 'test' not in el:
            check = True
        elif el['test'] == 'true':
            check = True
        elif el['test'] == 'false' and prod in os.environ:
            check = True
        else:
            check = False

        # Check if enabled
        if 'state' in el:
            if el['state'] == 'enabled':
                state = True
            else:
                state = False
        else:
            state = True

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

    # Show results in table format
    print("TOTAL:")
    print("config:  ", count['config'])
    print("disabled: ", count['disabled'])
    print("------------")
    print("found:   ", count['found'])
    print("ignored: ", count['ignored'])
    print("deleted: ", count['deleted'])
    print("added :  ", count['added'])

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
