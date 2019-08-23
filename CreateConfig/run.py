#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from gspread import authorize
from json import dumps
from oauth2client.service_account import ServiceAccountCredentials
from copy import deepcopy

prefix_github = 'https://github.com/'
prefix_mirror = 'FIWARE-GEs/'
scope = ['https://spreadsheets.google.com/feeds']
ws_c = 'Catalog'
ws_g = 'GitHub'
ws_d = 'Docker'
c_output = 'enablers_clair.json'
r_output = 'reposynchronizer.json'
p_output = 'prcloser.json'
a_output = 'apispectransformer.json'
tm_output = 'metrics_endpoints.json'
te_output = 'enablers_tsc.json'

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
             'API',
             'Transform']

tsc_dashboard_template = {
    'enabler': '',
    'catalogue': '',
    'academy': '',
    'readthedocs': '',
    'helpdesk': '',
    'coverall': '',
    'github': list(),
    'docker': list()
}

tsc_enablers_template = {
    'name': '',
    'status': '',
    'chapter': '',
    'type': '',
    'owner': ''
}


# Returns GE row from the main sheet, needed to verify the status, if deprecated
def get_id(f_array, f_index, f_entry):
    for row in range(1, len(f_array)):
        if f_array[row][f_index] == f_entry:
            return row

    return None


# Fills in empty cells
def normalize(f_array, f_index):
    for row in range(1, len(f_array)):
        if f_array[row][f_index] == '':
            f_array[row][f_index] = f_array[row - 1][f_index]

    return f_array


# Returns column id by name
def return_index(f_index, f_array):
    if f_index in f_array[0]:
        return f_array[0].index(f_index)

    return None


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--id', required=True, help='ID of google doc', action="store")
    parser.add_argument('-c', help='FIWARE Clair', action="store_true")
    parser.add_argument('-r', help='Repository Synchronizer', action="store_true")
    parser.add_argument('-p', help='Pull Request Closer', action="store_true")
    parser.add_argument('-a', help='API Specifications Transformer', action="store_true")
    parser.add_argument('-tm', help='FIWARE TSC Dashboard - metrics', action="store_true")
    parser.add_argument('-te', help='FIWARE TSC Dashboard - enablers', action="store_true")

    args = parser.parse_args()

    result = dict()
    index_c = dict()
    index_g = dict()
    index_d = dict()
    f = None

    print("Started")

    # Download the content (sheets -> raw values)
    credentials = ServiceAccountCredentials.from_json_keyfile_name('auth.json', scope)
    gc = authorize(credentials)
    ws_c = gc.open_by_key(args.id).worksheet(ws_c)
    values_c = ws_c.get_all_values()
    ws_g = gc.open_by_key(args.id).worksheet(ws_g)
    values_g = ws_g.get_all_values()
    ws_d = gc.open_by_key(args.id).worksheet(ws_d)
    values_d = ws_d.get_all_values()

    # Find indexes of columns (sheet can be reorganized in different ways) and fill in empty cells
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

    # FIWARE Clair
    if args.c:
        result['enablers'] = list()

        for el in range(1, len(values_d)):
            if values_d[el][index_d['Docker Image']] not in ['-', '?']:
                # check status
                el_c = get_id(values_c, index_c['GE Tech Name'], values_d[el][index_d['GE Tech Name']])
                if values_c[el_c][index_c['Status']] in ['deprecated']:
                    continue

                # fill in entity
                item = {'name': values_c[el_c][index_c['GE Tech Name']],
                        'image': values_d[el][index_d['Docker Image']]}

                if values_d[el][index_d['Entry Tech Name']] != '-':
                    item['name'] += '.' + values_d[el][index_d['Entry Tech Name']]

                result['enablers'].append(item)

        result['enablers'] = sorted(result['enablers'], key=lambda k: k['name'])
        f = open(c_output, 'w')

    # Repository Synchronizer
    if args.r:
        result['repositories'] = list()

        for el in range(1, len(values_g)):
            if values_g[el][index_g['Repository']] not in ['-', '?']:
                # check status
                el_c = get_id(values_c, index_c['GE Tech Name'], values_g[el][index_g['GE Tech Name']])
                if values_c[el_c][index_c['Status']] in ['deprecated']:
                    continue

                # fill in entity
                item = {'source': values_g[el][index_g['Repository']],
                        'target': prefix_mirror + values_g[el][index_g['GE Tech Name']]}

                if values_g[el][index_g['Entry Tech Name']] != '-':
                    item['target'] += '.' + values_g[el][index_g['Entry Tech Name']]

                result['repositories'].append(item)

        result['repositories'] = sorted(result['repositories'], key=lambda k: k['target'])
        f = open(r_output, 'w')

    # Pull Request Closer
    if args.p:
        result['repositories'] = list()

        for el in range(1, len(values_g)):
            if values_g[el][index_g['Repository']] not in ['-', '?']:
                # check status
                el_c = get_id(values_c, index_c['GE Tech Name'], values_g[el][index_g['GE Tech Name']])
                if values_c[el_c][index_c['Status']] in ['deprecated']:
                    continue

                # fill in entity
                item = prefix_mirror + values_g[el][index_g['GE Tech Name']]
                if values_g[el][index_g['Entry Tech Name']] != '-':
                    item += '.' + values_g[el][index_g['Entry Tech Name']]
                result['repositories'].append(item)

        result['repositories'] = sorted(result['repositories'])
        f = open(p_output, 'w')

    # API Specifications Transformer
    if args.a:
        result = {'repositories': list(),
                  'format': 'swagger20',
                  'branches': ['master', 'gh-pages']}

        for el in range(1, len(values_g)):
            if values_g[el][index_g['API']] not in ['-', '?']:
                # check status
                el_c = get_id(values_c, index_c['GE Tech Name'], values_g[el][index_g['GE Tech Name']])
                if values_c[el_c][index_c['Status']] in ['deprecated']:
                    continue

                # fill in entity
                item = {'target': 'Fiware/specifications',
                        'source': 'FIWARE-GEs/' + values_g[el][index_c['GE Tech Name']],
                        'files': list()}
                if values_g[el][index_g['Entry Tech Name']] != '-':
                    item['source'] += '.' + values_g[el][index_c['Entry Tech Name']]

                file = {'source': values_g[el][index_g['API']],
                        'target': 'OpenAPI/' + values_g[el][index_g['GE Tech Name']] + '/openapi.json',
                        'transform': True}

                if values_g[el][index_g['Transform']] == 'FALSE':
                    file['transform'] = False

                item['files'].append(file)

                result['repositories'].append(item)

        f = open(a_output, 'w')

    # FIWARE TSC Dashboard - metrics
    if args.tm:
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

            for el_g in range(1, len(values_g)):
                if values_g[el_g][index_g['GE Tech Name']] == values_c[el][index_c['GE Tech Name']]:
                    if values_g[el_g][index_g['Repository']] not in ['?', '-']:
                        item['github'].append(values_g[el_g][index_g['Repository']])

            for el_d in range(1, len(values_d)):
                if values_d[el_d][index_d['GE Tech Name']] == values_c[el][index_c['GE Tech Name']]:
                    if values_d[el_d][index_d['Docker Image']]not in ['?', '-']:
                        item['docker'].append(values_d[el_d][index_d['Docker Image']])

            result.append(item)

        result = sorted(result, key=lambda k: k['enabler'])
        f = open(tm_output, 'w')

    # FIWARE TSC Dashboard - enablers
    if args.te:
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
        f = open(te_output, 'w')

    f.write(dumps(result, indent=4, ensure_ascii=False) + '\n')
    print("Finished")
