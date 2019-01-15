#!/usr/bin/env python3

import json
import logging
import subprocess
import sys

import caldav

logger = logging.getLogger(__name__)


def lookup_secret(key: str, val: str) -> str:
    return subprocess.run(
        [
            'secret-tool',
            'lookup',
            key,
            val,
        ],
        stdout=subprocess.PIPE,
        check=True,
        universal_newlines=True  # Don't use arg 'text' for Python 3.6 compat.
    )


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        url = config['caldav']['url']
        username = config['caldav']['username']
        password_key = config['caldav']['password_key']
        password_val = config['caldav']['password_val']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    completed_process = lookup_secret(password_key, password_val)
    password = completed_process.stdout
    return {
        'url': url,
        'username': username,
        'password': password,
    }


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


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format='%(message)s')
    config = load_config(sys.argv[1])
    sys.exit(0)
    main(
        config['url'],
        config['username'],
        config['password'],
    )
