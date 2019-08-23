#!/usr/bin/python3

import json as jsn
import requests
import os
import sys
import re
import argparse
import xlsxwriter

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

    items = ['type', 'source', 'target', 'service', 'path', 'description', 'mark', 'id']

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_path', help='path to config file',  action='store')
    parser.add_argument('--xls', dest='xls', help='save output to excel file (folder)', action='store')
    args = parser.parse_args()
    config_path = args.config_path
    xls = args.xls

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

            if 'description' in el:
                tmp['description'] = el['description']
            else:
                tmp['description'] = 'subscription'

            tmp['mark'] = prefix + str(el['mark'])

            if 'path' in el:
                tmp['path'] = el['path']

            if 'service' in el:
                tmp['service'] = el['service']

            if not el['source'].startswith('http'):
                tmp['source'] = 'http://' + el['source']
            else:
                tmp['source'] = el['source']

            if 'state' in el:
                if el['state']:
                    tmp['sate'] = True

            if not el['target'].startswith('http'):
                tmp['target'] = 'http://' + el['target']
            else:
                tmp['target'] = el['target']

            tmp['template'] = el['template']

            if 'token' in el:
                tmp['token'] = el['token']

            config.append(tmp)
    except KeyError:
        print('Config error')
        sys.exit(1)

    print('Started')
    item = dict()
    for el in config:
        count['config'] += 1
        headers.clear()

        print('Working with', el['source'])
        if check_validity(el['source']):
            url = el['source']+'/v2/subscriptions'

            if 'token'in el:
                headers['X-Auth-Token'] = el['token']

            # Clean block. We don't store subscriptions, so simply remove everything that has mark
            if not el['source'] in done:
                done.append(el['source'])

                for service in services:
                    headers['Fiware-Service'] = service
                    resp = requests.get(url + '?limit=200', headers=headers).json()
                    for sub in resp:
                        count['found'] += 1
                        ignore = True
                        item.clear()
                        if 'notification' in sub:
                            if 'httpCustom' in sub['notification']:
                                if 'headers' in sub['notification']['httpCustom']:
                                    if 'mark' in sub['notification']['httpCustom']['headers']:
                                        if re.search(prefix, sub['notification']['httpCustom']['headers']['mark']):
                                            requests.delete(url + '/'+sub['id'], headers=headers)
                                            if 'description' in sub:
                                                item['description'] = sub['description']
                                            item['id'] = sub['id']
                                            item['mark'] = sub['notification']['httpCustom']['headers']['mark']
                                            item['path'] = ''
                                            item['service'] = service
                                            item['source'] = el['source']
                                            item['target'] = sub['notification']['httpCustom']['url']
                                            item['type'] = 'deleted'
                                            out.append(dict(item))
                                            count['deleted'] += 1
                                            ignore = False

                        if ignore:
                            if 'description' in sub:
                                item['description'] = sub['description']
                            else:
                                item['description'] = ''
                            item['id'] = sub['id']
                            item['mark'] = ''
                            item['path'] = ''
                            item['service'] = service
                            item['source'] = el['source']
                            if 'http' in sub['notification']:
                                item['target'] = sub['notification']['http']['url']
                            if 'httpCustom' in sub['notification']:
                                item['target'] = sub['notification']['httpCustom']['url']
                            item['type'] = 'ignored'
                            out.append(dict(item))
                            count['ignored'] += 1

            # Check if enabled
            state = True
            if 'state' in el:
                if el['state'] == 'disabled':
                    state = False

            if not state:
                count['disabled'] += 1
            else:
                # Add subscription
                file = os.path.split(os.path.abspath(__file__))[0] + '/templates/' + el['template']+'.json'

                template = jsn.load(open(file))
                template['notification']['httpCustom']['url'] = el['target'] + template['notification']['httpCustom']['url']
                template['notification']['httpCustom']['headers'] = {'mark': el['mark']}
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
                    item = {'description': template['description'],
                            'id': re.sub('/v2/subscriptions/', '', resp.headers['Location']),
                            'mark': el['mark'],
                            'path': el['path'],
                            'service': el['service'],
                            'source': el['source'],
                            'target': template['notification']['httpCustom']['url'],
                            'type': 'added'}

                    out.append(dict(item))
                    count['added'] += 1
                else:
                    sys.exit(1)
        else:
            count['errors'] += 1
            item = {'description': '',
                    'id': '',
                    'mark': el['mark'],
                    'path': '',
                    'service': '',
                    'source': el['source'],
                    'target': el['target'],
                    'type': 'error'}
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

    if xls:
        workbook = xlsxwriter.Workbook(xls + '/info.xlsx')

        format_title = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bold': True})

        format_cell = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'bold': False})

        ws_hook = workbook.add_worksheet()
        max_size = dict()

        col = 0
        for item in items:
            ws_hook.write(0, col, item, format_title)
            col += 1
            max_size[item] = len(item)

        row = 1
        for el in out:
            col = 0
            for item in items:
                length = len(str(el[item]))
                if max_size[item] < length:
                    max_size[item] = length
                ws_hook.write(row, col, el[item], format_cell)
                col += 1
            row += 1

        col = 0
        for item in items:
            ws_hook.set_column(col, col, max_size[item])
            col += 1

        workbook.close()
