FROM alpine
MAINTAINER Dmitrii Demin <mail@demin.co>

RUN apk update \
&&  apk add --update --no-cache py3-requests py3-pip \
&&  pip3 install --upgrade pip \
&&  pip3 install --upgrade prettytable \
&&  apk del py3-pip

ADD subscribe.py /opt/
ADD templates /opt/
ADD config.json /opt/

WORKDIR /opt/

CMD ["python3", "-u", "/opt/subscribe.py", "--config", "/opt/config.json"]
