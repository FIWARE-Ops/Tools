## Docker info
[![Docker badge](https://img.shields.io/docker/pulls/fiware/tool.subscribeorions.svg)](https://hub.docker.com/r/fiware/tool.subscribeorions/)

## This tools
It allows to create subscriptions in the array of [Orions](https://fiware-orion.readthedocs.io/en/latest/) from different templates.

## How to run
Create an array of subscriptions in the test environment
```console
$ sunscribe.py --config ${PATH_TO_CONFIG}
```
Create an array of subscriptions in the production environment

```console
$ sunscribe.py --config ${PATH_TO_CONFIG} --prod
```

## How to configure
+ Templates should be at the same level as python script. 
+ Sample template is located [here](./templates/default.json) 
