#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from gspread import authorize
from json import dumps
from oauth2client.service_account import ServiceAccountCredentials
from copy import deepcopy


columns_c = ['GE Tech Name',
             'GE Full Name',
             'Status',
             'Chapter',
             'Owner',
             'HelpDesk',
             'Academy',
             'Read the Docs',
             'Stack Overflow',
             'Q&A',
             'Academy-Legacy',
             'Catalog-Legacy',
             'Type-Legacy',
             'Coverall']

columns_d = ['GE Tech Name',
             'Entry Full Name',
             'Entry Tech Name',
             'Docker Image',
             'Repository']

columns_g = ['GE Tech Name',
             'Entry Full Name',
             'Entry Tech Name',
             'Repository',
             'API']

tsc_dashboard_template = {
    'enabler': '',
    'catalogue': '',
    'academy': '',
    'readthedocs': '',
    'helpdesk': '',
    'coverall': ''
}

tsc_enablers_template = {
    'name': '',
    'status': '',
    'chapter': '',
    'type': '',
    'owner': ''
}

index_c = dict()
index_g = dict()
index_d = dict()
prefix_mirror = 'https://github.com/FIWARE-GEs/'
prefix_github = 'https://github.com/'
scope = ['https://spreadsheets.google.com/feeds']
ws_c = 'Catalog'
ws_g = 'GitHub'
ws_d = 'Docker'


def get_id(f_array, f_index, f_entry):
    for row in range(1, len(f_array)):
        if f_array[row][f_index] == f_entry:
            return row

    return None


def normalize(f_array, f_index):
    for row in range(1, len(f_array)):
        if f_array[row][f_index] == '':
            f_array[row][f_index] = f_array[row - 1][f_index]

    return f_array


def return_index(f_index, f_array):
    if f_index in f_array[0]:
        return f_array[0].index(f_index)

    return None


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--id', dest="id", required=True, help='ID of google doc', action="store")
    parser.add_argument('--c', dest="clair", help='FIWARE Clair', action="store_true")
    parser.add_argument('--r', dest="reposync", help='Repository Synchronizer', action="store_true")
    parser.add_argument('--p', dest="prcloser", help='Pull Request Closer', action="store_true")
    parser.add_argument('--a', dest="api", help='API Specifications Transformer', action="store_true")
    parser.add_argument('--tm', dest="tscmetrics", help='FIWARE TSC Dashboard - metrics', action="store_true")
    parser.add_argument('--te', dest="tscenablers", help='FIWARE TSC Dashboard - enablers', action="store_true")

    args = parser.parse_args()

    result = dict()
    f = None

    print("Started")

    credentials = ServiceAccountCredentials.from_json_keyfile_name('auth.json', scope)
    gc = authorize(credentials)
    ws_c = gc.open_by_key(args.id).worksheet(ws_c)
    values_c = ws_c.get_all_values()
    ws_g = gc.open_by_key(args.id).worksheet(ws_g)
    values_g = ws_g.get_all_values()
    ws_d = gc.open_by_key(args.id).worksheet(ws_d)
    values_d = ws_d.get_all_values()

    for el in columns_c:
        index_c[el] = return_index(el, values_c)
        if index_c[el] is None:
            print('Column "' + el + '" not found in the doc')
        else:
            values_c = normalize(values_c, index_c[el])

    for el in columns_g:
        index_g[el] = return_index(el, values_g)
        if index_g[el] is None:
            print('Column "' + el + '" not found in the doc')
        else:
            values_g = normalize(values_g, index_g[el])

    for el in columns_d:
        index_d[el] = return_index(el, values_d)
        if index_d[el] is None:
            print('Column "' + el + '" not found in the doc')
        else:
            values_d = normalize(values_d, index_d[el])

    if args.clair:
        result['enablers'] = list()

        for el in range(1, len(values_d)):
            if values_d[el][index_d['Docker Image']] not in ['-', '?']:
                el_c = get_id(values_c, index_c['GE Tech Name'], values_d[el][index_d['GE Tech Name']])

                if values_c[el_c][index_c['Status']] in ['deprecated']:
                    continue

                item = dict()
                if values_d[el][index_d['Entry Tech Name']] == '-':
                    item['name'] = values_c[el_c][index_c['GE Tech Name']]
                else:
                    item['name'] = values_c[el_c][index_c['GE Tech Name']] + '.' + values_d[el][index_d['Entry Tech Name']]
                item['image'] = values_d[el][index_d['Docker Image']]
                result['enablers'].append(item)

        result['enablers'] = sorted(result['enablers'], key=lambda k: k['name'])
        f = open('enablers.json', 'w')

    if args.reposync:
        result['repositories'] = list()

        for el in range(1, len(values_g)):
            if values_g[el][index_g['Repository']] not in ['-', '?']:
                el_c = get_id(values_c, index_c['GE Tech Name'], values_g[el][index_g['GE Tech Name']])

                if values_c[el_c][index_c['Status']] in ['deprecated']:
                    continue

                item = dict()
                item['source'] = prefix_github + values_g[el][index_g['Repository']]
                item['target'] = prefix_mirror
                if values_g[el][index_g['Entry Tech Name']] == '-':
                    item['target'] = item['target'] + values_g[el][index_g['GE Tech Name']]
                else:
                    item['target'] = item['target'] + values_g[el][index_g['GE Tech Name']] + '.' + values_g[el][index_g['Entry Tech Name']]
                result['repositories'].append(item)

        result['repositories'] = sorted(result['repositories'], key=lambda k: k['target'])
        f = open('reposynchronizer.json', 'w')

    if args.prcloser:
        result['repositories'] = list()

        for el in range(1, len(values_g)):
            if values_g[el][index_g['Repository']] not in ['-', '?']:
                el_c = get_id(values_c, index_c['GE Tech Name'], values_g[el][index_g['GE Tech Name']])

                if values_c[el_c][index_c['Status']] in ['deprecated']:
                    continue

                item = prefix_mirror
                if values_g[el][index_g['Entry Tech Name']] == '-':
                    item = item + values_g[el][index_g['GE Tech Name']]
                else:
                    item = item + values_g[el][index_g['GE Tech Name']] + '.' + values_g[el][index_g['Entry Tech Name']]
                result['repositories'].append(item)

        result['repositories'] = sorted(result['repositories'])
        f = open('prcloser.json', 'w')

    if args.api:
        result['repositories'] = list()
        result['format'] = 'swagger20'
        result['branches'] = list()
        result['branches'].append('master')
        result['branches'].append('gh-pages')

        for el in range(1, len(values_g)):
            if values_g[el][index_g['API']] not in ['-', '?']:
                el_c = get_id(values_c, index_c['GE Tech Name'], values_g[el][index_g['GE Tech Name']])

                if values_c[el_c][index_c['Status']] in ['deprecated']:
                    continue

                item = dict()
                item['target'] = 'Fiware/specifications'
                item['source'] = 'FIWARE-GEs/'
                if values_g[el][index_g['Entry Tech Name']] == '-':
                    item['source'] = item['source'] + values_g[el][index_c['GE Tech Name']]
                else:
                    item['source'] = item['source'] + values_g[el][index_c['GE Tech Name']] + '.' + values_g[el][index_c['Entry Tech Name']]
                item['files'] = list()
                file = dict()
                file['source'] = values_g[el][index_g['API']]
                file['target'] = 'OpenAPI/' + values_g[el][index_g['GE Tech Name']] + '/openapi.json'
                file['transform'] = True
                item['files'].append(file)
                result['repositories'].append(item)

        f = open('apispectransformer.json', 'w')

    if args.tscmetrics:
        result = list()
        for el in range(1, len(values_c)):
            item = deepcopy(tsc_dashboard_template)

            item['enabler'] = values_c[el][index_c['GE Full Name']]

            if values_c[el][index_c['Catalog-Legacy']] not in ['-']:
                item['catalogue'] = values_c[el][index_c['Catalog-Legacy']]

            if values_c[el][index_c['Academy-Legacy']] not in ['-']:
                item['academy'] = values_c[el][index_c['Academy-Legacy']]

            if values_c[el][index_c['Read the Docs']] not in ['-']:
                item['readthedocs'] = values_c[el][index_c['Read the Docs']]

            if values_c[el][index_c['HelpDesk']] not in ['?', '-']:
                item['helpdesk'] = values_c[el][index_c['HelpDesk']]

            if values_c[el][index_c['Coverall']] not in ['?', '-']:
                item['coverall'] = values_c[el][index_c['Coverall']]

            item['github'] = list()
            for el_g in range(1, len(values_g)):
                if values_g[el_g][index_g['GE Tech Name']] == values_c[el][index_c['GE Tech Name']]:
                    if values_g[el_g][index_g['Repository']] not in ['?', '-']:
                        item['github'].append(values_g[el_g][index_g['Repository']])

            item['docker'] = list()
            for el_d in range(1, len(values_d)):
                if values_d[el_d][index_d['GE Tech Name']] == values_c[el][index_c['GE Tech Name']]:
                    if values_d[el_d][index_d['Docker Image']]not in ['?', '-']:
                        item['docker'].append(values_d[el_d][index_d['Docker Image']])

            result.append(item)

        result = sorted(result, key=lambda k: k['enabler'])
        f = open('metrics_endpoints.json', 'w')

    if args.tscenablers:
        result = list()
        for el in range(1, len(values_c)):
            item = deepcopy(tsc_enablers_template)

            item['name'] = values_c[el][index_c['GE Full Name']]
            item['status'] = values_c[el][index_c['Status']]
            if values_c[el][index_c['Chapter']] not in ['-']:
                item['chapter'] = values_c[el][index_c['Chapter']]
            if values_c[el][index_c['Type-Legacy']] not in ['-']:
                item['type'] = values_c[el][index_c['Type-Legacy']]
            item['owner'] = values_c[el][index_c['Owner']]

            result.append(item)

        result = sorted(result, key=lambda k: k['name'])
        f = open('enablers.json', 'w')

    f.write(dumps(result, indent=4, ensure_ascii=False) + '\n')
    print("Finished")
