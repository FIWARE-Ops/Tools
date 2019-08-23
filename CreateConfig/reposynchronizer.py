import gspread
import json
import argparse

from oauth2client.service_account import ServiceAccountCredentials


def clean(column):
    column = list(filter(None, column))
    column.pop(0)
    return column


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--id', dest="id", required=True, help='ID of google doc', action="store")

    args = parser.parse_args()

    id = args.id

    print("Started")

    scope = ['https://spreadsheets.google.com/feeds']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('auth.json', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open_by_key(id).sheet1

    target = clean(wks.col_values(1))
    source = clean(wks.col_values(2))

    result = dict()
    result['repositories'] = list()

    for el in range(0, len(target)):
        data = dict()

        data['target'] = target[el]
        data['source'] = source[el]

        result['repositories'].append(data)

    result['repositories'] = sorted(result['repositories'], key=lambda k: k['target'])

    f = open("reposynchronizer.json", "w")
    f.write(json.dumps(result, indent=2))

    print("Done")
