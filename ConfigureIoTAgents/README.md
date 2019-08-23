## Info
This tool is a part of [FIWARE](https://fiware.org) OPS infrastructure.
It creates services and devices(from a template) for perfomance test

## How to run
```console
$ docker run -d \
             -v $(pwd)/config.json:/opt/config.json \ 
             fiware/tools:configureiotagents \
             --start 1 \
             --end 100 \
             --mask '0000' \
             --limit 20
```

## How to configure
+ Sample config file is located [here](./config.example.json).
