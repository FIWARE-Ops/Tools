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
url_template_main = 'https://hub.docker.com/v2/repositories/{}'
url_template_repos = 'https://hub.docker.com/v2/repositories/{}/{}/tags?page_size=1024'
url_template_tags = '{}/{}:{}'


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

    url_tag = url_template_repos.format(src, repo)
    async with session.get(url_tag) as response:
        content = await response.read()

    content = loads(content)

    for el in content['results']:
        result['tags'].append(el['name'])

    return result


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--source', help='source org', default='fiware', action='store')
    parser.add_argument('--target', help='target org', default='fiwarelegacy', action='store')
    args = parser.parse_args()

    print("Started")

    print("Loading list of repos")
    request = loads(get(url_template_main.format(args.source) + '?page_size=1024').text)

    for item in request['results']:
        if item['namespace'] == args.source:
            repos.append(item['name'])

    print("Loading tags")
    tags = run(harvest(repos, args.source))

    print("Syncing")
    for repository in tags:
        for tag in repository['tags']:
            source = url_template_tags.format(args.source, repository['name'], tag)
            target = url_template_tags.format(args.target, repository['name'], tag)
            print('executing:', source)
            print('pulling..')
            execute(['docker', 'pull', source])
            execute(['docker', 'tag', source, target])
            print('pushing..')
            execute(['docker', 'push', target])
