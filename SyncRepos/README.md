![FIWARE Banner](https://nexus.lab.fiware.org/repository/raw/public/images/fiware-logo1.png)

# Synchronize Repositories

## Overview
This project is part of [FIWARE](https://fiware.org) OPS infrastructure.
It synchronize GitHub repositories:
+ Commits
+ Branches
+ Tags
+ Releases

## How to run
```console
$ python3 sync.py --config <PATH_TO_CONFIG> --commits --releases
```

## How to configure
+ You should provide a valid token for GitHub with an environment variable TOKEN.
+ Sample config is located [here](https://raw.githubusercontent.com/Fiware/devops.Tools/master/SyncRepos/config-example.json).
