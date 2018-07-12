![FIWARE Banner](https://nexus.lab.fiware.org/repository/raw/public/images/fiware-logo1.png)

# Get Repository Information

## Overview
This project is part of [FIWARE](https://fiware.org) OPS infrastructure.
It grep information from GitHub repositories and represent it in excel-compatible form.
It collects:
+ General (GitHub API v3 fields)
    + description
    + has_issues
    + has_wiki
    + has_pages
    + has_projects
    + has_downloads
+ Hooks (Webhooks):
    + active
    + url
    + type
    + ssl
    + events

## How to run
```console
$ python3 get.py --config <PATH_TO_CONFIG> --general --hooks
```

## How to configure
+ You should provide a valid token for GitHub with an environment variable TOKEN.
+ Sample config is located [here](https://raw.githubusercontent.com/Fiware/devops.Tools/master/GetRepoInfo/config-example.json).
