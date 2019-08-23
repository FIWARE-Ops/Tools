#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from json import loads
from requests import get
from xlsxwriter import Workbook


repo_items = ['name', 'star_count', 'is_automated', 'source_repo', 'last_updated', 'pull_count']
build_items = ['repo', 'name', 'last_updated']
url_template = 'https://hub.docker.com/v2/repositories/'


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--owner', dest="owner", default='fiware', help='owner (default: fiware)', action="store")
    args = parser.parse_args()

    repos = list()
    tags = list()

    url_template = url_template + args.owner + '/'

    print('collecting main data')
    url = url_template
    while True:
        reply = get(url)

        if reply.status_code == 200:
            resp = loads(reply.text)
            for el in range(0, len(resp['results'])):
                block = dict()
                for item in repo_items:
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

    print('collecting source_repo data')
    for el in range(0, len(repos)):
        if repos[el]['is_automated']:
            url = url_template + repos[el]['name'] + '/autobuild'
            reply = get(url)
            if reply.status_code == 200:
                resp = loads(reply.text)
                repos[el]['source_repo'] = resp['source_url'].strip()
            else:
                exit(1)
        else:
            repos[el]['source_repo'] = ''

    print('collecting tags data')
    for el in range(0, len(repos)):
        url = url_template + repos[el]['name'] + '/tags'
        reply = get(url)
        if reply.status_code == 200:
            resp = loads(reply.text)
            for tag in resp['results']:
                block = dict()
                block['repo'] = repos[el]['name']
                for item in build_items:
                    if item != 'repo':
                        if tag[item] is not None:
                            block[item] = tag[item].strip()
                        else:
                            block[item] = ''
                tags.append(block)
        else:
            exit(1)

    print('preparing xlsx')
    workbook = Workbook('info.xlsx')
    worksheet1 = workbook.add_worksheet()
    worksheet2 = workbook.add_worksheet()

    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bold': True})

    col = 0
    for item in repo_items:
        worksheet1.write(0, col, item, cell_format)
        col += 1

    col = 0
    for item in build_items:
        worksheet2.write(0, col, item, cell_format)
        col += 1

    cell_format = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'border': 1})

    print('fill in repos')
    row = 1
    for el in range(0, len(repos)):
        col = 0
        for item in repo_items:
            worksheet1.write(row, col, repos[el][item], cell_format)
            col += 1
        row += 1

    print('fill in tags')
    row = 1
    for el in range(0, len(tags)):
        col = 0
        for item in build_items:
            worksheet2.write(row, col, tags[el][item], cell_format)
            col += 1
        row += 1

    current = 2
    start = 2
    item = tags[0]['repo']
    for el in range(1, len(tags)):
        if tags[el]['repo'] != item:
            if current - start >= 1:
                merge_range = 'A' + str(start) + ':A' + str(current)
                worksheet2.merge_range(merge_range, item, cell_format)
            start = current + 1
            item = tags[el]['repo']
        current += 1

    print('autoscale cells')
    max_size = dict()
    for item in repo_items:
        max_size[item] = 0

    for el in range(0, len(repos)):
        for item in repo_items:
            length = len(str(repos[el][item]))
            if max_size[item] < length:
                max_size[item] = length

    for item in repo_items:
        length = len(item)
        if max_size[item] < length:
            max_size[item] = length

    col = 0
    for item in repo_items:
        worksheet1.set_column(col, col, max_size[item])
        col += 1

    max_size = dict()
    for item in build_items:
        max_size[item] = 0

    for el in range(0, len(tags)):
        for item in build_items:
            length = len(str(tags[el][item]))
            if max_size[item] < length:
                max_size[item] = length

    col = 0
    for item in build_items:
        worksheet2.set_column(col, col, max_size[item])
        col += 1

    workbook.close()
