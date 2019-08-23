#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import ClientSession, client_exceptions
from argparse import ArgumentParser, ArgumentTypeError
from asyncio import run
from yajl import loads, dumps
from copy import deepcopy
from os.path import isfile
from sys import stdout
import logging


log_levels = ['ERROR', 'INFO', 'DEBUG']
logger = None
logger_req = None
http_ok = [200, 201]


def log_level_to_int(log_level_string):
    if log_level_string not in log_levels:
        message = 'invalid choice: {0} (choose from {1})'.format(log_level_string, log_levels)
        raise ArgumentTypeError(message)

    return getattr(logging, log_level_string, logging.ERROR)


async def configure(start, end, limit, mask, config):

    headers = {
        'Content-Type': 'application/json',
        'fiware-service': config['header_service'],
        'fiware-servicepath': config['header_service_path']
    }

    len_mask = len(mask)

    logger.info('Posting services')
    url = 'http://' + config['host'] + ':' + config['port'] + '/iot/services'
    data = dict()
    data['services'] = list()
    data['services'].append(deepcopy(config['service']))

    async with ClientSession() as session:
        try:
            async with session.post(url, data=dumps(data), headers=headers) as response:
                status = response.status
        except client_exceptions.ClientConnectorError:
            logger.error('service creation failed')
            return False

        if status not in http_ok:
            logger.error('service creation failed')
            return False

    logger.info('Preparing devices')
    url = 'http://' + config['host'] + ':' + config['port'] + '/iot/devices'
    data = list()
    for item in range(start, end):
        device = deepcopy(config['device'])
        device['device_id'] = device['device_id'] + str(item).rjust(len_mask, '0')
        data.append(device)

    # splitting list to list of lists to fit into limits
    block = 0
    items = 0
    data_divided = dict()
    data_divided[0] = list()
    while True:
        if len(data) > 0:
            if items < limit:
                data_divided[block].append(data.pop())
                items += 1
            else:
                items = 0
                block += 1
                data_divided[block] = list()
        else:
            break

    logger.info('Posting devices')
    for item in data_divided:
        data = dict()
        data['devices'] = deepcopy(data_divided[item])

        async with ClientSession() as session:
            try:
                async with session.post(url, data=dumps(data), headers=headers) as response:
                    status = response.status
            except client_exceptions.ClientConnectorError:
                logger.error('service creation failed')
                return False
            if status not in http_ok:
                logger.error('device creation failed')
                return False

    return True


def setup_logger():
    local_logger = logging.getLogger('root')
    local_logger.setLevel(log_level_to_int(args.log_level))

    handler = logging.StreamHandler(stdout)
    handler.setLevel(log_level_to_int(args.log_level))
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%dT%H:%M:%SZ')
    handler.setFormatter(formatter)
    local_logger.addHandler(handler)

    local_logger_req = logging.getLogger('requests')
    local_logger_req.setLevel(logging.WARNING)

    return local_logger, local_logger_req


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--start', help='first item', default='1', action='store')
    parser.add_argument('--end', help='last item', default='3000', action='store')
    parser.add_argument('--mask', help='mask to fill in', default='0000', action='store')
    parser.add_argument('--config', help='path to config file', default='./config.json',
                        action='store')
    parser.add_argument('--limit', help='limit amount entities per 1 block', default=50,
                        action='store')
    parser.add_argument('--log-level',
                        default='INFO',
                        help='Set the logging output level. {0}'.format(log_levels),
                        nargs='?')
    args = parser.parse_args()

    logger, logger_req = setup_logger()

    if not isfile(args.config):
        logger.error('Config file not found')
        exit(1)
    try:
        with open(args.config) as f:
            cfg = loads(f.read())
    except ValueError:
        logger.error('Unsupported type of config file')
        exit(1)

    logger.info('Started')
    res = run(configure(int(args.start), int(args.end), int(args.limit), args.mask, cfg))
    if not res:
        exit(1)
    logger.info('Ended')
