#!/usr/bin/python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from gspread import authorize
from json import dumps
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']
out = 'prcloser.json'
ws_list = ['Release-Mirror-Catalog', 'Release-Mirror-NotCatalog']


def clean(column):
    column = list(filter(None, column))
    column.pop(0)
    return column


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--id', dest="id", required=True, help='ID of google doc', action="store")
    args = parser.parse_args()

    print("Started")

    result = list()

    credentials = ServiceAccountCredentials.from_json_keyfile_name('auth.json', scope)
    gc = authorize(credentials)

    for ws in ws_list:
        wks = gc.open_by_key(args.id).worksheet(ws)
        target = clean(wks.col_values(1))

        for el in range(0, len(target)):
            result.append(target[el])
     
    result = sorted(result, key=lambda k: k)

    f = open(out, 'w')
    f.write(dumps(result, indent=2))

    print("Done")
