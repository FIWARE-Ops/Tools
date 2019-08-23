#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json as jsn
import requests
import os
import sys
import argparse


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

    data = jsn.dumps(data)
    url = 'https://api.github.com/repos/' + target + '/hooks' + '?access_token=' + token
    resp = requests.post(url, data=data, headers={'Content-Type': 'application/json'})
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

    data = jsn.dumps(data)
    url = 'https://api.github.com/repos/' + source + '/hooks' + '?access_token=' + token
    resp = requests.post(url, data=data, headers={'Content-Type': 'application/json'})
    if resp.status_code == 201:
        return True
    else:
        return False


def change_description(source, target):
        data = dict()
        data['name'] = target.split('/')[1]
        data['description'] = description + source
        data = jsn.dumps(data)

        url = 'https://api.github.com/repos/' + repo['target'] + '?access_token=' + token
        resp = requests.patch(url, data=data, headers={'Content-Type': 'application/json'})
        if resp.status_code == 200:
            return True
        else:
            return False


if __name__ == '__main__':

    if 'TOKEN' in os.environ:
        token = os.environ['TOKEN']
    else:
        print('TOKEN not found')
        token = None
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--mirror', dest='config_mirror', required=True,  action="store")
    parser.add_argument('--transformer', dest='config_transformer', required=True,  action="store")

    args = parser.parse_args()
    config_mirror = args.config_mirror
    config_transformer = args.config_transformer

    description = "This is a mirror repo. Please fork from https://github.com/"
    url_mirror = 'https://webhook.fiware.org/close-pull-request'
    url_transformer = 'https://webhook.fiware.org/transform'

    if not os.path.isfile(config_mirror):
        print('Config for mirror webhook not found')
        config_mirror = None
        sys.exit(1)

    if not os.path.isfile(config_transformer):
        print('Config for transformer webhook not found')
        config_transformer = None
        sys.exit(1)

    try:
        with open(config_mirror) as f:
            cfg_mirror = jsn.load(f)
    except ValueError:
        print('Unsupported config type')
        sys.exit(1)

    try:
        with open(config_transformer) as f:
            cfg_transformer = jsn.load(f)
    except ValueError:
        print('Unsupported config type')
        sys.exit(1)

    # mirror
    print('Working on mirror webhook')
    for repo in cfg_mirror['repositories']:
        hook = False
        hook_url = 'https://api.github.com/repos/' + repo['target'] + '/hooks?access_token=' + token

        response = requests.get(hook_url)
        if response.status_code == 200:
            for element in jsn.loads(response.text):
                if 'config' in element:
                    if 'url' in element['config']:
                        if element['config']['url'] == 'https://webhook.fiware.org/close-pull-request':
                            hook = True

            if not hook:
                print("repo:", repo['target'])
                if create_cpr(repo['target']):
                    print('hook: added')
                else:
                    print('hook: ERROR')
                    sys.exit(1)

        else:
            print("repo:", repo['target'], " not found")
            sys.exit(1)

    # mirror
    print('Working on description')
    for repo in cfg_mirror['repositories']:
        desc_url = 'https://api.github.com/repos/' + repo['target']
        response = requests.get(desc_url)
        if response.status_code == 200:
            if jsn.loads(response.text)['description'] != description + repo['source']:
                if not change_description(repo['source'], repo['target']):
                    print('desc: failed')
                    sys.exit(1)

    # transformer
    print('Working on transformer webhook')
    for repo in cfg_transformer['repositories']:
        hook = False
        hook_url = 'https://api.github.com/repos/' + repo['source'] + '/hooks?access_token=' + token

        response = requests.get(hook_url)
        if response.status_code == 200:
            for element in jsn.loads(response.text):
                if 'config' in element:
                    if 'url' in element['config']:
                        if element['config']['url'] == url_transformer:
                            hook = True

            if not hook:
                if create_transformer(repo['source']):
                    print('hook: added')
                else:
                    print('hook: ERROR')
                    sys.exit(1)

        else:
            print("repo", repo['source'], " not found")
            sys.exit(1)
