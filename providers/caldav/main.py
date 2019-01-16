#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys
from functools import partial
from pathlib import Path
from typing import Callable, Iterator

import caldav
import ics

logger = logging.getLogger(__name__)


def lookup_secret(key: str, val: str) -> str:
    completed_process = subprocess.run(
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
    return completed_process.stdout


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        url = config['caldav']['url']
        username = config['caldav']['username']
        password_key = config['caldav']['password_key']
        password_val = config['caldav']['password_val']
        cache_dir = config['caldav']['cache_dir']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    password = lookup_secret(password_key, password_val)
    return {
        'url': url,
        'username': username,
        'password': password,
        'cache_dir': cache_dir,
    }


def read_data_from_cache(cache_dir: Path) -> Iterator[str]:
    if cache_dir.is_dir():
        logger.info('Reading cache')
        for cache_file in os.scandir(cache_dir):
            if cache_file.is_file():
                yield Path(cache_file.path).read_text()


def write_events_to_cache(events: Iterator[caldav.Event], cache_dir: Path):
    logger.info('Writing cache')
    cache_dir.mkdir(parents=True, exist_ok=True)
    for event in events:
        _, event_id = event.url.rsplit('/', maxsplit=1)
        cache_file = cache_dir / event_id
        if cache_file.exists():
            raise Exception(f'Cache file {cache_file} already exists')
        cache_file.write_text(event.data)


def read_ical(data: str) -> str:
    pass


def download_events(url: str,
                    username: str,
                    password: str) -> Iterator[caldav.Event]:
    logger.info('Connecting to %s', url)
    client = caldav.DAVClient(
        url,
        username=username,
        password=password
    )
    logger.info('Reading principal')
    principal = client.principal()
    for calendar in principal.calendars():
        yield from calendar.events()


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format='%(message)s')
    _, config_path, path_out = sys.argv
    config = load_config(config_path)
    cache_dir = Path(config['cache_dir'])
    data = list(read_data_from_cache(cache_dir))
    if not data:
        events = list(download_events(
            config['url'],
            config['username'],
            config['password']
        ))
        write_events_to_cache(events, cache_dir)
        data = [event.data for event in events]
    read_ical(data)
