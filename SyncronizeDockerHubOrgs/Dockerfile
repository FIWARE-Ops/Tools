FROM python:3.7.2-alpine

LABEL maintainer="mail@demin.co"

WORKDIR /opt/

COPY . /opt/

RUN pip3 install -r requirements.txt \
&& apk add --upgrade --no-cache docker

ENTRYPOINT ["/usr/bin/env", "python3", "-u", "/opt/run.py"]
