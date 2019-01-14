#!/usr/bin/env python3

import logging
import os
import sys

import caldav

logger = logging.getLogger(__name__)


def main(url: str, username: str, password: str) -> str:
    logger.info('  Connecting to %s', url)
    client = caldav.DAVClient(
        url,
        username=username,
        password=password
    )
    logger.info('  Reading principal')
    principal = client.principal()
    for calendar in principal.calendars():
        for event in calendar.events():
            ical_text = event.data
            logger.info(ical_text)


def check_environ_vars() -> bool:
    okay = True
    if 'CALDAV_URL' not in os.environ:
        logger.error('Plase set the environment variable CALDAV_URL.')
        logger.error('Example: CALDAV_URL=""')
        okay = False
    if 'CALDAV_USERNAME' not in os.environ:
        logger.error('Plase set the environment variable CALDAV_USERNAME.')
        logger.error('Example: CALDAV_USERNAME="jakub"')
        okay = False
    if 'CALDAV_PASSWORD' not in os.environ:
        logger.error('Plase set the environment variable CALDAV_PASSWORD.')
        logger.error('Example: CALDAV_PASSWORD=$(secret-tool lookup key val)')
        okay = False
    return okay


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format='%(message)s')
    if not check_environ_vars():
        sys.exit(1)
    main(
        os.environ['CALDAV_URL'],
        os.environ['CALDAV_USERNAME'],
        os.environ['CALDAV_PASSWORD'],
    )
