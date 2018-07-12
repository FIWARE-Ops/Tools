![FIWARE Banner](https://nexus.lab.fiware.org/repository/raw/public/images/fiware-logo1.png)

# Subscribe Orions

## Overview
This project is part of [FIWARE](https://fiware.org) OPS infrastructure.
It allows to create subscriptions in the array of Orions from different templates.

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
