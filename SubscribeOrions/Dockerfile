FROM python:3.7.2-alpine

LABEL maintainer="mail@demin.co"

WORKDIR /opt/

COPY . /opt/

RUN pip3 install -r requirements.txt

ENTRYPOINT ["/usr/bin/env", "python3", "-u", "/opt/run.py", "--config", "/opt/config.json"]
