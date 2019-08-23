#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from json import load, dumps
from os import path
from re import search, sub
from requests import get, post, delete, exceptions
from xlsxwriter import Workbook


items = ['type', 'source', 'target', 'service', 'description', 'mark', 'id']


def check_validity(orion):
    link = orion + '/version'
    try:
        reply = get(link)
    except exceptions.ConnectionError:
        return False

    if reply.status_code == 200:
        return True

    return False


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--config', dest='config_path', help='path to config file',  action='store')
    parser.add_argument('--xls', dest='xls', help='save output to excel file (folder)', action='store')
    args = parser.parse_args()

    count = {'config': 0,
             'added': 0,
             'deleted': 0,
             'found': 0,
             'ignored': 0,
             'disabled': 0,
             'errors': 0}

    orion_failed = list()
    services = None
    config = None
    prefix = None

    if not path.isfile(args.config_path):
        print('Config file not found')
        config_file = None
        exit(1)

    try:
        with open(args.config_path) as f:
            cfg = load(f)
    except ValueError:
        print('Unsupported config type')
        exit(1)

    print('Checking config')
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
        exit(1)

    print('Started')
    item = dict()
    headers = dict()
    cleaned = list()
    out = list()

    for el in config:
        count['config'] += 1
        status = True
        headers.clear()

        print('Working with', el['source'])

        if el['source'] in orion_failed:
            status = False

        if status and not check_validity(el['source']):
            print(el['source'], "is unavailable")
            orion_failed.append(el['source'])
            status = False

        if not status:
            count['errors'] += 1
            item = {'id': 'orion unavailable',
                    'mark': el['mark'],
                    'service': el['service'],
                    'source': el['source'],
                    'target': el['target'],
                    'type': 'errored',
                    'description': el['description']}
            out.append(item)
            continue

        url = el['source']+'/v2/subscriptions'

        if 'token'in el:
            headers['X-Auth-Token'] = el['token']

        # Clean block. We don't store subscriptions, so simply remove everything that has a mark
        if not el['source'] in cleaned:
            cleaned.append(el['source'])

            for service in services:
                headers['Fiware-Service'] = service
                resp = get(url + '?limit=200', headers=headers).json()
                for el_sub in resp:
                    count['found'] += 1
                    ignore = True
                    try:
                        if search(prefix, el_sub['notification']['httpCustom']['headers']['mark']):
                            delete(url + '/'+el_sub['id'], headers=headers)
                            item = {'id': el_sub['id'],
                                    'mark':  el_sub['notification']['httpCustom']['headers']['mark'],
                                    'service': service,
                                    'source': el['source'],
                                    'target': el_sub['notification']['httpCustom']['url'],
                                    'type': 'deleted',
                                    'description': el_sub['description'] if 'description' in el_sub else ''}

                            count['deleted'] += 1
                        else:
                            raise KeyError
                    except KeyError:
                        item = {'id': el_sub['id'],
                                'mark': '',
                                'service': service,
                                'source': el['source'],
                                'type': 'ignored',
                                'description': el_sub['description'] if 'description' in el_sub else ''}
                        try:
                            item['target'] = el_sub['notification']['http']['url']
                        except KeyError:
                            try:
                                item['target'] = el_sub['notification']['httpCustom']['url']
                            except KeyError:
                                pass
                            finally:
                                item['target'] = ''

                        count['ignored'] += 1
                    if item:
                        out.append(dict(item))

        # Check if enabled
        try:
            if el['state'] == 'disabled':
                state = False
            else:
                state = True
        except KeyError:
            state = True

        if not state:
            count['disabled'] += 1
            continue

        # Add subscription
        file = path.split(path.abspath(__file__))[0] + '/templates/' + el['template']+'.json'

        template = load(open(file))
        template['notification']['httpCustom']['headers'] = {'mark': el['mark']}
        template['description'] = el['description']
        tmp_url = template['notification']['httpCustom']['url'].format(el['target'])
        template['notification']['httpCustom']['url'] = tmp_url

        data = dumps(template)

        headers['Content-Type'] = 'application/json'

        if 'service' in el:
            headers['Fiware-Service'] = el['service']
        else:
            el['service'] = ''
            if 'Fiware-Service' in headers:
                del headers['Fiware-Service']

        item = {'id': '',
                'mark': el['mark'],
                'service': el['service'],
                'source': el['source'],
                'target': template['notification']['httpCustom']['url'],
                'type': 'added',
                'description': template['description']}

        resp = post(url, headers=headers, data=data)
        if resp.status_code == 201:
            item['id'] = sub('/v2/subscriptions/', '', resp.headers['Location'])
            count['added'] += 1
        else:
            count['errors'] += 1
            item['type'] = 'error'
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

    if args.xls:
        workbook = Workbook(args.xls + '/info.xlsx')

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
