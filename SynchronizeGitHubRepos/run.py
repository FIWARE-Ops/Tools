#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json as jsn
import requests
import os
import sys
import argparse


api_url = 'https://api.github.com/repos/'
webhook_url = 'https://webhook.fiware.org/mirror/sync?id='


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_path', help='path to config file',  action="store")
    parser.add_argument('--releases', help='sync releases notes',  action="store_true")
    args = parser.parse_args()

    if 'TOKEN' in os.environ:
        token = os.environ['TOKEN']
    else:
        print('TOKEN not found')
        token = None
        sys.exit(1)

    if not os.path.isfile(args.config_path):
        print('Config file not found')
        config_file = None
        sys.exit(1)

    try:
        with open(args.config_path) as f:
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

    print('Starting')
    for repo in config['repositories']:
        url = webhook_url + repo['source']

        result = requests.post(url)
        if result.status_code == 200:
            print('Repository synchronization succeeded, ', repo['source'])
        else:
            print('Repository synchronization failed, ', repo['source'])

