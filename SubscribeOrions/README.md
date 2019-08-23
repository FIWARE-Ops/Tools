## Info
This tool is a part of [FIWARE](https://fiware.org) OPS infrastructure.
It creates subscriptions in the array of [Orions](https://fiware-orion.readthedocs.io/en/latest/) from different templates.

## How to run
Create an array of subscriptions in the orions and prepare output
```console
$ python3 run.py --config ${PATH_TO_CONFIG} --xls .
```

## How to configure
+ Templates should be at the same level as python script. 
+ Sample template is located [here](./templates/default.json.example) 
