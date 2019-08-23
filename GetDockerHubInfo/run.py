#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from json import loads
from requests import get
from xlsxwriter import Workbook


url_template_repos = 'https://hub.docker.com/v2/repositories/{}/'
url_template_repos2 = 'https://hub.docker.com/v2/repositories/{}/{}/autobuild'
url_template_tags = 'https://hub.docker.com/v2/repositories/{}/{}/tags'
repos_items = ['name', 'star_count', 'is_automated', 'source_repo', 'last_updated', 'pull_count']
tags_items = ['repo', 'name', 'last_updated']

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--owner', default='fiware', help='owner (default: fiware)', action="store")
    args = parser.parse_args()

    repos = list()
    tags = list()

    print('collecting main data')
    url = url_template_repos.format(args.owner)
    while True:
        reply = get(url)

        if reply.status_code == 200:
            resp = loads(reply.text)
            for el in range(0, len(resp['results'])):
                block = dict()
                for item in repos_items:
                    if item != 'source_repo':
                        if type(resp['results'][el][item]) is str:
                            block[item] = str(resp['results'][el][item]).strip()
                        else:
                            block[item] = resp['results'][el][item]
                repos.append(block)
            if resp['next'] is None:
                break
            else:
                url = resp['next']
        else:
            exit(1)

    print('collecting autobuild data')
    for el in range(0, len(repos)):
        if repos[el]['is_automated']:
            reply = get(url_template_repos2.format(args.owner, repos[el]['name']))
            if reply.status_code == 200:
                resp = loads(reply.text)
                repos[el]['source_repo'] = resp['source_url'].strip()
            else:
                exit(1)
        else:
            repos[el]['source_repo'] = ''

    print('collecting tags data')
    for el in range(0, len(repos)):
        reply = get(url_template_tags.format(args.owner, repos[el]['name']))
        if reply.status_code == 200:
            resp = loads(reply.text)
            for tag in resp['results']:
                block = dict()
                block['repo'] = repos[el]['name']
                for item in tags_items:
                    if item != 'repo':
                        if tag[item] is not None:
                            block[item] = tag[item].strip()
                        else:
                            block[item] = ''
                tags.append(block)
        else:
            exit(1)

    print('preparing result')
    workbook = Workbook('info.xlsx')
    result = dict()

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

    for ws_type in ['repos', 'tags']:
        print('Fill in', ws_type)

        result[ws_type] = workbook.add_worksheet(ws_type)
        max_size = dict()

        col = 0
        for item in eval(ws_type + '_items'):
            result[ws_type].write(0, col, item, format_title)
            col += 1
            max_size[item] = len(item)

        row = 1
        for el in range(0, len(eval(ws_type))):
            col = 0
            for item in eval(ws_type + '_items'):
                length = len(str(eval(ws_type)[el][item]))
                if max_size[item] < length:
                    max_size[item] = length
                result[ws_type].write(row, col, eval(ws_type)[el][item], format_cell)
                col += 1
            row += 1

        col = 0
        for item in eval(ws_type + '_items'):
            if item in ['repo', 'name']:
                multi = 1.23
            else:
                multi = 1.1
            result[ws_type].set_column(col, col, max_size[item] / multi)
            col += 1

    workbook.close()
    print("Done")
