#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from json import load, loads, dumps
from os import environ, path
from requests import get
from xlsxwriter import Workbook

url_template_general = 'https://api.github.com/repos/{}?access_token={}'
url_template_hooks = 'https://api.github.com/repos/{}/hooks?page={}&access_token={}'
general_items = ['repo', 'description', 'has_issues', 'has_wiki', 'has_pages', 'has_projects', 'has_downloads']
hooks_items = ['repo', 'active', 'url', 'content_type', 'insecure_ssl', 'events']

if __name__ == '__main__':

    if 'TOKEN' in environ:
        token = environ['TOKEN']
    else:
        print('TOKEN not found')
        token = None
        exit(1)

    parser = ArgumentParser()
    parser.add_argument('--config', dest='config_path', help='path to config file',  action="store")
    parser.add_argument('--general', help='get general info',  action="store_true")
    parser.add_argument('--hooks', help='get webhooks info',  action="store_true")
    args = parser.parse_args()
    config_path = args.config_path

    print("Started")

    general = None
    hooks = None
    arg_general = args.general
    arg_hooks = args.hooks

    if not arg_general:
        if not arg_hooks:
            print('At lease one option should be defined')
            exit(1)

    if not path.isfile(config_path):
        print('Config file not found')
        config_file = None
        exit(1)

    try:
        with open(config_path) as f:
            config = load(f)
    except ValueError:
        print('Unsupported config type')
        exit(1)

    print('Checking config')

    if 'repositories' not in config:
        print('Repositories not defined')
        exit(1)
    elif len(config['repositories']) == 0:
        print('Repositories list is empty')
        exit(1)

    if arg_general:
        general = list()
        print('Collecting general info')
        for repo in config['repositories']:
            response = get(url_template_general.format(repo['target'], token))
            if response.status_code == 200:
                data = loads(response.text)
                tmp = dict()
                tmp['repo'] = repo['target']
                for item in general_items:
                    if item in ['repo']:
                        continue
                    tmp[item] = data[item]
                general.append(dict(tmp))
            else:
                print('Something is wrong, check config')
                exit(1)

    if arg_hooks:
        hooks = list()
        print('Collecting webhooks info')
        for repo in config['repositories']:
            i = 1
            status = False
            while not status:
                response = get(url_template_hooks.format(repo['target'], str(i), token))
                if response.status_code == 200:
                    data = loads(response.text)
                    for element in data:
                        tmp = dict()
                        tmp['repo'] = repo['target']
                        if 'active' in element:
                            tmp['active'] = element['active']
                        if 'events' in element:
                            tmp['events'] = dumps(element['events'])
                        for item in hooks_items:
                            if item in ['repo', 'active', 'events']:
                                continue
                            tmp[item] = element['config'][item]
                        hooks.append(dict(tmp))
                    if 'next' not in response:
                        status = True
                    else:
                        i = i + 1
                else:
                    print('Something is wrong, check config')
                    exit(1)

    print('Preparing result')
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

    for ws_type in ['general', 'hooks']:
        if not eval('arg_' + ws_type):
            continue
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
            if item in ['repo', 'description', 'events']:
                multi = 1.23
            else:
                multi = 1.1
            result[ws_type].set_column(col, col, max_size[item] / multi)
            col += 1

    workbook.close()
    print("Done")
