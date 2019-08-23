import gspread
import json
import argparse

from oauth2client.service_account import ServiceAccountCredentials


def expand(column):
    column = list(filter(None, column))
    column.pop(0)
    return column


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--id', dest="id", required=True, help='ID of google doc', action="store")
    parser.add_argument('--format', dest="format", default='swagger20', help='API format, swagger by default',
                        action="store")
    parser.add_argument('branches', type=str, metavar='N', nargs='*', help='branches, master by default')

    args = parser.parse_args()

    print("Started")

    result = dict()
    result['format'] = args.format
    result['repositories'] = list()
    result['branches'] = list()

    if not args.branches:
        result['branches'].append('master')
    else:
        for el in args.branches:
            result['branches'].append(el)

    scope = ['https://spreadsheets.google.com/feeds']
    items = ['source', 'source_files', 'target', 'target_files', 'transform']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('auth.json', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open_by_key(args.id).worksheet('Specifications')

    data = dict()
    i = 1
    max_length = 0
    for item in items:
        data[item] = wks.col_values(i)
        data[item].pop(0)
        if len(data[item]) > max_length:
            max_length = len(data[item])
        i += 1

    for item in items:
        if len(data[item]) < max_length:
            for i in range(0, max_length - len(data[item])):
                data[item].append('')

    item = dict()
    for i in range(0, len(data[list(data.keys())[0]])):
        if data['source_files'][i] == '':
            data['source_files'][i] = data['source_files'][i-1]
        if data['target'][i] == '':
            data['target'][i] = data['target'][i-1]
        if data['transform'][i] == '':
            data['transform'][i] = data['transform'][i-1]
        else:
            if data['transform'][i] == 'FALSE':
                data['transform'][i] = False
            elif data['transform'][i] == 'TRUE':
                data['transform'][i] = True

        if data['source'][i] != '':
            if i > 0:
                result['repositories'].append(item)
            item = dict()
            item['source'] = data['source'][i]
            item['target'] = data['target'][i]
            item['files'] = list()
        else:
            status = False

        file = dict()
        if data['source_files'][i] != '':
            file['source'] = data['source_files'][i]
        else:
            file['source'] = data['source_files'][i-1]
        file['target'] = data['target_files'][i]
        file['transform'] = data['transform'][i]
        item['files'].append(file)

    result['repositories'].append(item)

    result['repositories'] = sorted(result['repositories'], key=lambda k: k['source'])

    f = open("apispectransformer.json", "w")
    f.write(json.dumps(result, indent=2))

    print("Done")

