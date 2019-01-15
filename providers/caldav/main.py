#!/usr/bin/env python3

import json
import logging
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Any, Callable

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
        cache_file = config['caldav']['cache_file']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    completed_process = lookup_secret(password_key, password_val)
    password = completed_process.stdout
    return {
        'url': url,
        'username': username,
        'password': password,
        'cache_file': cache_file,
    }


def with_cache(func: Callable, cache_file: str) -> Any:
    path = Path(cache_file)
    if path.is_file():
        logger.info('Reading cache')
        return path.read_text()
    data = func()
    logger.info('Writing cache')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data)
    return data


def read_ical(data: str) -> str:
    pass


def download_data(url: str, username: str, password: str) -> str:
    data = []
    logger.info('Connecting to %s', url)
    client = caldav.DAVClient(
        url,
        username=username,
        password=password
    )
    logger.info('Reading principal')
    principal = client.principal()
    for calendar in principal.calendars():
        for event in calendar.events():
            data.append(event.data)
    return '\n'.join(data)


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format='%(message)s')
    config = load_config(sys.argv[1])
    data = with_cache(
        partial(
            download_data,
            config['url'],
            config['username'],
            config['password']
        ),
        config['cache_file']
    )
    read_ical(data)
