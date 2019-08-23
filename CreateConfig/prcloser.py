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

    ID = args.id

    print("Started")

    scope = ['https://spreadsheets.google.com/feeds']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('auth.json', scope)

    gc = gspread.authorize(credentials)

    result = list()

    wks = gc.open_by_key(ID).worksheet('Release-Mirror-Catalog')
    target = clean(wks.col_values(1))
    for el in range(0, len(target)):
        result.append(target[el])

    wks = gc.open_by_key(ID).worksheet('Release-Mirror-NotCatalog')
    target = clean(wks.col_values(1))
    for el in range(0, len(target)):
        result.append(target[el])
     
    result = sorted(result, key=lambda k: k)

    f = open("prcloser.json", "w")
    f.write(json.dumps(result, indent=2))

    print("Done")
