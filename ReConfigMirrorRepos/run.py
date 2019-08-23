#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from json import load, loads, dumps
from os import environ, path
from requests import get, post, patch

url_template = 'https://api.github.com/repos/'
url_mirror = 'https://webhook.fiware.org/close-pull-request'
url_transformer = 'https://webhook.fiware.org/transform'
url_close_pull_request = 'https://webhook.fiware.org/close-pull-request'
headers = {'Content-Type': 'application/json'}
description = "This is a mirror repo. Please fork from https://github.com/"


def create_cpr(target):
    data = dict()
    data['name'] = 'web'
    data['active'] = True
    data['events'] = {}
    data['events'] = list()
    data['events'].append('pull_request')
    data['config'] = {}
    data['config']['insecure_ssl'] = 0
    data['config']['content_type'] = 'json'
    data['config']['url'] = url_mirror

    data = dumps(data)
    url = url_template + target + '/hooks' + '?access_token=' + token
    resp = post(url, data=data, headers=headers)
    if resp.status_code == 201:
        return True
    else:
        return False


def create_transformer(source):
    data = dict()
    data['name'] = 'web'
    data['active'] = True
    data['events'] = {}
    data['events'] = list()
    data['events'].append('push')
    data['config'] = {}
    data['config']['insecure_ssl'] = 0
    data['config']['content_type'] = 'json'
    data['config']['url'] = url_mirror

    data = dumps(data)
    url = url_template + source + '/hooks' + '?access_token=' + token
    resp = post(url, data=data, headers=headers)
    if resp.status_code == 201:
        return True
    else:
        return False


def change_description(source, target):
        data = dict()
        data['name'] = target.split('/')[1]
        data['description'] = description + source
        data = dumps(data)

        url = url_template + repo['target'] + '?access_token=' + token
        resp = patch(url, data=data, headers=headers)
        if resp.status_code == 200:
            return True
        else:
            return False


if __name__ == '__main__':

    if 'TOKEN' in environ:
        token = environ['TOKEN']
    else:
        print('TOKEN not found')
        token = None
        exit(1)

    parser = ArgumentParser()
    parser.add_argument('--mirror', dest='config_mirror', required=True,  action="store")
    parser.add_argument('--transformer', dest='config_transformer', required=True,  action="store")
    args = parser.parse_args()

    if not path.isfile(args.config_mirror):
        print('Config for mirror webhook not found')
        config_mirror = None
        exit(1)

    if not path.isfile(args.config_transformer):
        print('Config for transformer webhook not found')
        config_transformer = None
        exit(1)

    try:
        with open(args.config_mirror) as f:
            cfg_mirror = load(f)
    except ValueError:
        print('Unsupported config type')
        exit(1)

    try:
        with open(args.config_transformer) as f:
            cfg_transformer = load(f)
    except ValueError:
        print('Unsupported config type')
        exit(1)

    print('Working on mirror webhook')
    for repo in cfg_mirror['repositories']:
        hook = False
        hook_url = url_template + repo['target'] + '/hooks?access_token=' + token

        response = get(hook_url)
        if response.status_code == 200:
            for element in loads(response.text):
                if 'config' in element:
                    if 'url' in element['config']:
                        if element['config']['url'] == url_close_pull_request:
                            hook = True

            if not hook:
                print("repo:", repo['target'])
                if create_cpr(repo['target']):
                    print('hook: added')
                else:
                    print('hook: ERROR')
                    exit(1)

        else:
            print("repo:", repo['target'], " not found")
            exit(1)

    print('Working on description')
    for repo in cfg_mirror['repositories']:
        desc_url = url_template + repo['target']
        response = get(desc_url)
        if response.status_code == 200:
            if loads(response.text)['description'] != description + repo['source']:
                if not change_description(repo['source'], repo['target']):
                    print('desc: failed')
                    exit(1)

    print('Working on transformer webhook')
    for repo in cfg_transformer['repositories']:
        hook = False
        hook_url = url_template + repo['source'] + '/hooks?access_token=' + token

        response = get(hook_url)
        if response.status_code == 200:
            for element in loads(response.text):
                if 'config' in element:
                    if 'url' in element['config']:
                        if element['config']['url'] == url_transformer:
                            hook = True

            if not hook:
                if create_transformer(repo['source']):
                    print('hook: added')
                else:
                    print('hook: ERROR')
                    exit(1)

        else:
            print("repo", repo['source'], " not found")
            exit(1)
