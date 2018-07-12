#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json as jsn
import requests
import os
import sys
import argparse
import time


def compare_releases(source, target):
    result = False
    if source['tag_name'] == target['tag_name']:
            if source['name'] == target['name']:
                if source['body'] == target['body']:
                    if source['draft'] == target['draft']:
                        if source['prerelease'] == target['prerelease']:
                            result = True
    return result


def add_release(release, target):
    url_release = gh + target + '/releases?' + token
    body = dict()
    body['tag_name'] = release['tag_name']
    #body['target_commitish'] = release['target_commitish']
    body['name'] = release['name']
    body['body'] = release['body']
    body['draft'] = release['draft']
    body['prerelease'] = release['prerelease']
    body_json = jsn.dumps(body)
    result = requests.post(url_release, data=body_json, headers={'Content-Type': 'application/json'})
    if result.status_code == 201:
        print('Release added successfully, source_id: ', release['id'], ' target_id: ', jsn.loads(result.text)['id'])
    else:
        print('Release added with errors, source_id: ', release['id'])
    return


def delete_release(release, target):
    url_release = gh + target + '/releases/' + str(release['id']) + '?' + token
    result = requests.delete(url_release)
    if result.status_code == 204:
        print('Release deleted successfully, target_id: ', release['id'])
    else:
        print('Release deleted with errors, target_id: ', release['id'])


if __name__ == '__main__':

    if 'TOKEN' in os.environ:
        token = os.environ['TOKEN']
    else:
        print('TOKEN not found')
        token = None
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', dest='config_path', help='path to config file',  action="store")
    parser.add_argument('--commits', dest='commits', help='sync commits/branches/tags/objects',  action="store_true")
    parser.add_argument('--releases', dest='releases', help='sync releases notes',  action="store_true")
    args = parser.parse_args()
    config_path = args.config_path
    commits = args.commits
    releases = args.releases

    if not commits:
        if not releases:
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

    gh = 'https://api.github.com/repos/'
    token = 'access_token=' + token
    webhook = 'https://webhook.fiware.org/mirror/sync?repo='

    print('Starting')
    for repo in config['repositories']:
        print('Repo: ', repo['target'])

        if commits:
            sync = False
            branches_src = list()
            branches_trg = list()

            url = gh + repo['source'] + '/branches?' + token
            response = requests.get(url)
            if response.status_code == 200:
                data = jsn.loads(response.text)
                for el in data:
                    item = {'branch': el['name'], 'commit': el['commit']['sha']}
                    branches_src.append(item)

            url = gh + repo['target'] + '/branches?' + token
            response = requests.get(url)
            if response.status_code == 200:
                data = jsn.loads(response.text)
                for el in data:
                    item = {'branch': el['name'], 'commit': el['commit']['sha']}
                    branches_trg.append(item)

            if len(branches_src) != len(branches_trg):
                sync = True
            else:
                for el_src in branches_src:
                    status = False
                    for el_trg in branches_trg:
                        if el_src['branch'] == el_trg['branch']:
                            if el_src['commit'] == el_trg['commit']:
                                status = True
                                break
                    if not status:
                        sync = True
            if sync:
                url = webhook + repo['target']
                requests.post(url)
                print('Commits synced')

        if releases:
            releases_src = []
            releases_trg = []
            releases_add = []

            # get list of releases from source
            status = True
            i = 1
            while status:
                url = gh + repo['source'] + '/releases?page=' + str(i) + '&' + token
                response = requests.get(url)
                if response.status_code == 200:
                    data = jsn.loads(response.text)
                    for el in data:
                        releases_src.append(el)
                    if 'next' not in response:
                        status = False
                    else:
                        i = i + 1

            # get list of releases from target
            status = True
            i = 1
            while status:
                url = gh + repo['target'] + '/releases?page=' + str(i) + '&' + token
                response = requests.get(url)
                if response.status_code == 200:
                    data = jsn.loads(response.text)
                    for el in data:
                        releases_trg.append(el)
                    if 'next' not in response:
                        status = False
                    else:
                        i = i + 1

            # prepare list of releases to be deleted from target and added from source
            for release_src in releases_src:
                status = True
                for release_trg in releases_trg:
                    if compare_releases(release_src, release_trg):
                        releases_trg.remove(release_trg)
                        status = False
                if status:
                    releases_add.append(release_src)

            # delete releases
            for release_trg in releases_trg:
                delete_release(release_trg, repo['target'])

            # add releases
            for release_src in releases_add:
                add_release(release_src, repo['target'])
