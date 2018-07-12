#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json as jsn
import requests
import os
import sys
import argparse
from prettytable import PrettyTable
from prettytable import MSWORD_FRIENDLY

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
        out = []
        print('General')
        for repo in config['repositories']:
            url = 'https://api.github.com/repos/' + repo + '?access_token=' + token
            response = requests.get(url)
            if response.status_code == 200:
                data = jsn.loads(response.text)
                item = {'repo': repo,
                        'description': data['description'],
                        'has_issues': data['has_issues'],
                        'has_wiki': data['has_wiki'],
                        'has_pages': data['has_pages'],
                        'has_projects': data['has_projects'],
                        'has_downloads': data['has_downloads']}
                out.append(dict(item))
            else:
                sys.exit(1)
        table = PrettyTable(['repo', 'description', 'has_issues', 'has_wiki', 'has_pages', 'has_projects', 'has_downloads'])
        for el in out:
            table.add_row([el['repo'],
                           el['description'],
                           el['has_issues'],
                           el['has_wiki'],
                           el['has_pages'],
                           el['has_projects'],
                           el['has_downloads']])

        table.border = False
        table.set_style(MSWORD_FRIENDLY)
        table.align = 'l'
        table.sortby = 'repo'
        print(table)
        print('\n')

    if hooks:
        out = []
        print('WebHooks')
        for repo in config['repositories']:
            i = 1
            status = False
            while not status:
                url = 'https://api.github.com/repos/' + repo + '/hooks' + '?page=' + str(i) + '&access_token=' + token
                response = requests.get(url)
                if response.status_code == 200:
                    data = jsn.loads(response.text)
                    for element in data:
                        item = {'repo': repo,
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
                            item['events'] = element['events']
                        out.append(dict(item))
                    if 'next' not in response:
                        status = True
                    else:
                        i = i + 1
                else:
                    print('Something is wrong, check config')
                    sys.exit(1)
        table = PrettyTable(['repo', 'active', 'url', 'type', 'ssl', 'events'])
        for el in out:
            table.add_row([el['repo'],
                           el['active'],
                           el['url'],
                           el['type'],
                           el['ssl'],
                           el['events']])

        table.border = False
        table.set_style(MSWORD_FRIENDLY)
        table.align = 'l'
        table.sortby = 'events'
        print(table)
        print('\n')

    print('Finished')
