## Info
This tool is a part of [FIWARE](https://fiware.org) OPS infrastructure.
It scrapes information from a google spreedsheet and prepares a config for these webhooks, tools and services:
+ [RepoSynchronizer](https://github.com/FIWARE-Ops/RepoSynchronizer)
+ [PRCloser](https://github.com/FIWARE-Ops/PRCloser)
+ [APISpecTransformer](https://github.com/FIWARE-Ops/APISpecTransformer)
+ [Clair](https://github.com/flopezag/fiware-clair)
+ [TSC-Dashboard](https://github.com/flopezag/fiware-tsc-dashboard)

## How to run
```console
$ python3 reposynchronizer.py --id ${SOME_GDOC_ID} -c -r -p -a -tm -te
```

## How to configure
+ You should provide a valid auth file from Google.
+ Sample auth file is located [here](./auth.example.json).
