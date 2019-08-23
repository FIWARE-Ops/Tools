#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from json import load, loads, dumps
from os import environ, path
from requests import get, post, patch, delete

url_description = 'https://api.github.com/repos/{}?access_token={}'
url_webhooks = 'https://api.github.com/repos/{}/hooks?access_token={}'
url_release = 'https://api.github.com/repos/{}/releases?page={}&token={}'
url_webhook = {'mirror': 'https://webhook.fiware.org/close-pull-request',
               'transformer': 'https://webhook.fiware.org/transform'}
headers = {'Content-Type': 'application/json'}
description = "This is a mirror repo. Please fork from https://github.com/{}"


def create_webhook(target, webhook):
    data = {'name': 'web',
            'active': True,
            'events': list(),
            'config': {'insecure_ssl': 0,
                       'content_type': 'json'}
            }
    if webhook == 'mirror':
        data['config']['url'] = url_webhook['mirror']
        data['events'].append('pull_request')
    else:
        data['config']['url'] = url_webhook['transformer']
        data['events'].append('push')

    data = dumps(data)
    url = url_webhooks.format(target, token)
    resp = post(url, data=data, headers=headers)
    if resp.status_code == 201:
        return True
    else:
        return False


def change_parameters(source, target):
    data = {'name': target.split('/')[1],
            'description': description.format(source),
            'has_issues': False,
            'has_projects': False,
            'has_wiki': False}

    data = dumps(data)

    resp = patch(url_description.format(repo['target'], token), data=data, headers=headers)
    if resp.status_code == 200:
        return True

    return False


def delete_releases(target):
    i = 0
    releases = list()
    while True:
        resp = get(url_release.format(target, str(i), token))
        if resp.status_code == 200:
            data = loads(resp.text)
            for el in data:
                releases.append(el)
            if 'next' not in resp:
                break
            i += 1
    if len(releases) > 0:
        for item in releases:
            resp = delete(item['url'] + '?access_token=' + token)
            if resp.status_code == 204:
                print('Release deletion succeeded, ', item['url'])
            else:
                print('Release deletion failed, ', item['url'])

    return True


def delete_webhooks(target):
    resp = get(url_webhooks.format(target, token))
    if resp.status_code == 200:
        for item in loads(resp.text):
            if 'config' in item:
                if 'url' in item['config']:
                    if 'webhook.fiware.org' in item['config']['url']:
                        resp = delete(item['url'] + '?access_token=' + token)
                        if resp.status_code == 204:
                            print('Webhook deletion succeeded, ', item['url'], item['config']['url'])
                        else:
                            print('Webhook deletion failed, ', item['url'])
    return True


if __name__ == '__main__':

    if 'TOKEN' in environ:
        token = environ['TOKEN']
    else:
        print('TOKEN not found')
        token = None
        exit(1)

    parser = ArgumentParser()
    parser.add_argument('--transformer', required=True, action='store')
    parser.add_argument('--mirror', required=True, action='store')
    parser.add_argument('--description', action='store_true')
    parser.add_argument('--webhooks', action='store_true')
    parser.add_argument('--delete_releases', action='store_true')
    parser.add_argument('--delete_webhooks', action='store_true')
    args = parser.parse_args()

    if not path.isfile(args.mirror):
        print('Config for mirror webhook not found')
        exit(1)

    if not path.isfile(args.transformer):
        print('Config for transformer webhook not found')
        exit(1)

    config = dict()
    try:
        with open(args.mirror) as f:
            config['mirror'] = load(f)
    except ValueError:
        print('Unsupported config type')
        exit(1)

    try:
        with open(args.transformer) as f:
            config['transformer'] = load(f)
    except ValueError:
        print('Unsupported config type')
        exit(1)

    if args.delete_releases:
        print('Deleting releases')
        for repo in config['mirror']['repositories']:
            if not delete_releases(repo['target']):
                print('releases: failed')
                exit(1)

    if args.delete_webhooks:
        print('Deleting webhooks')
        for repo in config['mirror']['repositories']:
            if not delete_webhooks(repo['target']):
                print('webhooks: failed')
                exit(1)

    if args.description:
        print('Changing parameters')
        for repo in config['mirror']['repositories']:
            if not change_parameters(repo['source'], repo['target']):
                print('desc: failed')
                exit(1)

    if not args.webhooks:
        exit(0)

    for webhook_type in ['mirror', 'transformer']:
        print('Working on', webhook_type, 'webhook')
        for repo in config[webhook_type]['repositories']:
            hook = False
            if webhook_type == 'mirror':
                repo = repo['target']
            else:
                repo = repo['source']
            response = get(url_webhooks.format(repo, token))
            if response.status_code == 200:
                for element in loads(response.text):
                    if 'config' in element:
                        if 'url' in element['config']:
                            if element['config']['url'] == url_webhook[webhook_type]:
                                hook = True
                                print('hook: exists')

                if not hook:
                    print("repo:", repo)
                    if create_webhook(repo, webhook_type):
                        print('hook: added')
                    else:
                        print('hook: ERROR')
                        exit(1)

            else:
                print("repo:", repo['target'], " not found")
                exit(1)
