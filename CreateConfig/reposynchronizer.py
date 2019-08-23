#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from gspread import authorize
from json import dumps
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']
out = 'reposynchronizer.json'


def clean(column):
    column = list(filter(None, column))
    column.pop(0)
    return column


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--id', dest="id", required=True, help='ID of google doc', action="store")
    args = parser.parse_args()

    print("Started")

    result = dict()
    result['repositories'] = list()

    credentials = ServiceAccountCredentials.from_json_keyfile_name('auth.json', scope)
    gc = authorize(credentials)

    wks = gc.open_by_key(args.id).worksheet('Release-Mirror-Catalog')

    target = clean(wks.col_values(1))
    source = clean(wks.col_values(2))

    for el in range(0, len(target)):
        data = dict()

        data['target'] = target[el]
        data['source'] = source[el]

        result['repositories'].append(data)

    result['repositories'] = sorted(result['repositories'], key=lambda k: k['target'])

    f = open(out, 'w')
    f.write(dumps(result, indent=2))

    print("Done")
