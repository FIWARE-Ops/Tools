![FIWARE Banner](https://nexus.lab.fiware.org/content/images/fiware-logo1.png)

# Subscribe Orions
[![Docker badge](https://img.shields.io/docker/pulls/fiware/tool.subscribeorions.svg)](https://hub.docker.com/r/fiware/tool.subscribeorions/)

## Overview
This project is part of [FIWARE](https://fiware.org) OPS infrastructure.
It allows to create subscriptions in the array of [Orions](https://fiware-orion.readthedocs.io/en/latest/) from different templates.

## How to use
Subscribe test environment
```console
$ sunscribe.py --config ${PATH_TO_CONFIG}
```
Subscribe production environment
```console
$ sunscribe.py --config ${PATH_TO_CONFIG} --prod
```
Templates should be at the same level as python script.
