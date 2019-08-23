## Info:
This tool is a part of [FIWARE](https://fiware.org) OPS infrastructure.
It scrapes information about Docker images from the Docker Hub repository and represents it in an excel-compatible form.

It collects:
+ pull count
+ last update
+ source repository
+ if it is an automated build
+ star count
+ list of tags and their last update

## How to run
```console
$ python3 run.py --owner ${OWNER}
```
