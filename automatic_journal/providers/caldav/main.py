import csv
import datetime
import itertools
import json
import logging
import os
import re
import subprocess
import sys
from functools import partial, reduce
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple

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


def read_events_data_from_cache(cache_dir: Path) -> Iterator[str]:
    if cache_dir.is_dir():
        logger.info(f'Reading cache {cache_dir}')
        for cache_file in os.scandir(cache_dir):
            if cache_file.is_file():
                yield Path(cache_file.path).read_text()


def write_events_to_cache(events: Iterator[caldav.Event], cache_dir: Path):
    logger.info(f'Writing cache {cache_dir}')
    cache_dir.mkdir(parents=True, exist_ok=True)
    for event in events:
        _, event_id = event.url.rsplit('/', maxsplit=1)
        cache_file = cache_dir / event_id
        if cache_file.exists():
            raise Exception(f'Cache file {cache_file} already exists')
        cache_file.write_text(event.data)


def download_events(config: dict) -> List[str]:
    url = config['url']
    username = config['username']
    password = config['password']
    cache_dir = Path(config['cache_dir'])
    events_data = list(read_events_data_from_cache(cache_dir))
    if events_data:
        return events_data
    logger.info('Connecting to %s', url)
    client = caldav.DAVClient(
        url,
        username=username,
        password=password
    )
    logger.info('Reading principal')
    principal = client.principal()
    events = itertools.chain(
        calendar.events()
        for calendar in principal.calendars()
    )
    write_events_to_cache(events, cache_dir)
    return [event.data for event in events]


TDateTimeAndText = Tuple[datetime.datetime, str]


def parse_ics(events_data: Iterable[str]) -> Iterator[TDateTimeAndText]:
    for i, event_data in enumerate(events_data):
        try:
            calendar = ics.Calendar(event_data)
        except (ValueError, ics.parse.ParseError):
            logger.error('Failed to parse event %s', event_data)
            continue
        for event in calendar.events:
            yield (event.begin.datetime, event.name)


def format_csv(dt_and_text: Iterable[TDateTimeAndText],
               provider: str,
               subprovider: str) -> Iterator[Tuple[str, str, str, str]]:
    for dt, text in dt_and_text:
        clean_text = re.sub(r'\s+', ' ', text).strip()
        yield (
            dt.isoformat(),
            provider,
            subprovider,
            clean_text
        )


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)
    return wrapped


def main(config_path: str, csv_path: str):
    config = load_config(config_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        chain(
            download_events,
            parse_ics,
            partial(format_csv, provider='caldav', subprovider=config['url']),
            writer.writerows
        )(config)
