#!/usr/bin/python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from requests import get
from json import loads
from asyncio import Semaphore, ensure_future, gather, run
from aiohttp import ClientSession
from subprocess import run as execute

limit = 10
repos = list()
url_template = 'https://hub.docker.com/v2/repositories/{}'


async def harvest(source, src):
    tasks = list()

    sem = Semaphore(limit)

    async with ClientSession() as session:
        for repo in source:
            task = ensure_future(harvest_bounded(repo, src, sem, session))
            tasks.append(task)

        result = await gather(*tasks)

    return result


async def harvest_bounded(repo, src, sem, session):
    async with sem:
        return await harvest_one(repo, src, session)


async def harvest_one(repo, src, session):
    result = dict()
    result['name'] = repo
    result['tags'] = list()

    url_tag = url_template.format(src) + '/' + repo + '/tags/?page_size=1024'
    async with session.get(url_tag) as response:
        content = await response.read()

    content = loads(content)

    for el in content['results']:
        result['tags'].append(el['name'])

    return result


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--source', dest='source', help='source org', default='fiware', action='store')
    parser.add_argument('--target', dest='target', help='target org', default='fiwarelegacy', action='store')
    args = parser.parse_args()

    print("Started")
    print("Loading list of repos")
    request = loads(get(url_template.format(args.source) + '?page_size=1024').text)

    for item in request['results']:
        if item['namespace'] == args.source:
            repos.append(item['name'])

    print("Loading tags")
    res = run(harvest(repos, args.source))

    print("Syncing")
    for item in res:
        for item2 in item['tags']:
            pi_s = url_template.format(args.source) + '/' + item['name'] + ':' + item2
            pi_t = url_template.format(args.target) + '/' + item['name'] + ':' + item2
            print('executing:', pi_s)
            print('pulling..')
            execute(['docker', 'pull', pi_s])
            execute(['docker', 'tag', pi_s, pi_t])
            print('pushing..')
            execute(['docker', 'push', pi_t])
