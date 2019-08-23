FROM alpine
MAINTAINER Dmitrii Demin <mail@demin.co>

RUN apk update \
&&  apk add --update --no-cache py3-requests py3-pip \
&&  pip3 install --upgrade pip \
&&  pip3 install --upgrade xlsxwriter \
&&  apk del py3-pip

ADD run.py /opt/
ADD config-example.json /opt/config.json
ADD templates /opt/templates

WORKDIR /opt/

ENTRYPOINT ["python3", "-u", "/opt/run.py", "--config", "/opt/config.json"]
