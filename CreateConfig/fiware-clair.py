#!/usr/bin/python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from gspread import authorize
from json import dumps
from oauth2client.service_account import ServiceAccountCredentials


scope = ['https://spreadsheets.google.com/feeds']
out = 'fiware-clair.json'
ws = 'Catalogue'


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--id', dest="id", required=True, help='ID of google doc', action="store")
    args = parser.parse_args()

    print("Started")

    result = dict()
    result['enablers'] = list()

    credentials = ServiceAccountCredentials.from_json_keyfile_name('auth.json', scope)
    gc = authorize(credentials)

    wks = gc.open_by_key(args.id).worksheet(ws)
    images = wks.col_values(4)
    names = wks.col_values(2)

    for el in range(1, len(images)):
        if names[el] != '':
            item = dict()
            item['name'] = names[el]
            item['image'] = images[el]
            result['enablers'].append(item)

    f = open(out, 'w')
    f.write(dumps(result, indent=4))

    print("Done")
