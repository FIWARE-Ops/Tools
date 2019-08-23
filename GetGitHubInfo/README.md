## Info
This tool is a part of [FIWARE](https://fiware.org) OPS infrastructure.
It greps information from the GitHub repositories and represents it in an excel-compatible form.

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
$ python3 run.py --config <PATH_TO_CONFIG> --general --hooks
```

## How to configure
+ You should provide a valid token for GitHub with an environment variable TOKEN.
+ Sample config is located [here](./config.example.json).
