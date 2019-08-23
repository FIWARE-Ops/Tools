#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json as jsn
import requests
import os
import sys
import argparse
import xlsxwriter


if __name__ == '__main__':

    if 'TOKEN' in os.environ:
        token = os.environ['TOKEN']
    else:
        print('TOKEN not found')
        token = None
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_path', help='path to config file',  action="store")
    parser.add_argument('--general', dest='general', help='get general info',  action="store_true")
    parser.add_argument('--hooks', dest='hooks', help='get webhooks info',  action="store_true")
    args = parser.parse_args()
    config_path = args.config_path
    general = args.general
    hooks = args.hooks

    gen_items = ['repo', 'description', 'has_issues', 'has_wiki', 'has_pages', 'has_projects', 'has_downloads']
    hook_items = ['repo', 'active', 'url', 'type', 'ssl', 'events']

    if not general:
        if not hooks:
            print('At lease one option should be defined')
            sys.exit(1)

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

    if 'repositories' not in config:
        print('Repositories not defined')
        sys.exit(1)
    elif len(config['repositories']) == 0:
        print('Repositories list is empty')
        sys.exit(1)

    if general:
        gen = []
        print('Collecting general info')
        for repo in config['repositories']:
            url = 'https://api.github.com/repos/' + repo['target'] + '?access_token=' + token
            response = requests.get(url)
            if response.status_code == 200:
                data = jsn.loads(response.text)
                item = {'repo': repo['target'],
                        'description': data['description'],
                        'has_issues': data['has_issues'],
                        'has_wiki': data['has_wiki'],
                        'has_pages': data['has_pages'],
                        'has_projects': data['has_projects'],
                        'has_downloads': data['has_downloads']}
                gen.append(dict(item))
            else:
                print('Something is wrong, check config')
                sys.exit(1)

    if hooks:
        hook = []
        print('Collecting WebHooks info')
        for repo in config['repositories']:
            i = 1
            status = False
            while not status:
                url = 'https://api.github.com/repos/' + repo['target'] + '/hooks' + '?page=' + str(i) + '&access_token=' + token
                response = requests.get(url)
                if response.status_code == 200:
                    data = jsn.loads(response.text)
                    for element in data:
                        item = {'repo': repo['target'],
                                'active': '',
                                'url': '',
                                'type': '',
                                'ssl': '',
                                'events': ''}
                        if 'active' in element:
                            item['active'] = element['active']
                        if 'config' in element:
                            if 'url' in element['config']:
                                item['url'] = element['config']['url']
                            if 'content_type' in element['config']:
                                item['type'] = element['config']['content_type']
                            if 'insecure_ssl' in element['config']:
                                item['ssl'] = element['config']['insecure_ssl']
                        if 'events' in element:
                            item['events'] = jsn.dumps(element['events'])
                        hook.append(dict(item))
                    if 'next' not in response:
                        status = True
                    else:
                        i = i + 1
                else:
                    print('Something is wrong, check config')
                    sys.exit(1)

    workbook = xlsxwriter.Workbook('info.xlsx')

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

    if general:
        print('Fill in general')
        ws_gen = workbook.add_worksheet()
        max_size = dict()

        col = 0
        for item in gen_items:
            ws_gen.write(0, col, item, format_title)
            col += 1
            max_size[item] = len(item)

        row = 1
        for el in range(0, len(gen)):
            col = 0
            for item in gen_items:
                length = len(str(gen[el][item]))
                if max_size[item] < length:
                    max_size[item] = length
                ws_gen.write(row, col, gen[el][item], format_cell)
                col += 1
            row += 1

        col = 0
        for item in gen_items:
            ws_gen.set_column(col, col, max_size[item])
            col += 1

    if hooks:
        print('Fill in hooks')
        ws_hook = workbook.add_worksheet()
        max_size = dict()

        col = 0
        for item in hook_items:
            ws_hook.write(0, col, item, format_title)
            col += 1
            max_size[item] = len(item)

        row = 1
        for el in range(0, len(hook)):
            col = 0
            for item in hook_items:
                length = len(str(hook[el][item]))
                if max_size[item] < length:
                    max_size[item] = length
                ws_hook.write(row, col, hook[el][item], format_cell)
                col += 1
            row += 1

        col = 0
        for item in hook_items:
            ws_hook.set_column(col, col, max_size[item])
            col += 1

    workbook.close()
    print('Finished')
