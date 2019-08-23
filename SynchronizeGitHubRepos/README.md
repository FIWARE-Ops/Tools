## Info
This tool is a part of [FIWARE](https://fiware.org) OPS infrastructure.
It synchronizes 2 GitHub repositories:
+ Commits
+ Branches
+ Tags
+ Releases

## How to run
```console
$ python3 run.py --config <PATH_TO_CONFIG> --commits --releases
```

## How to configure
+ You should provide a valid token for GitHub with an environment variable TOKEN.
+ Sample config is located [here](./config-example.json).
