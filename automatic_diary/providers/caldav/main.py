import io
import itertools
import logging
import os
from pathlib import Path
from typing import Iterable, Iterator, List

import caldav

from automatic_diary.common import Item, lookup_secret
from automatic_diary.providers.icalendar.main import parse_calendar

logger = logging.getLogger(__name__)


def _read_events_data_from_cache(
    cache_dir: Path, no_cache: bool
) -> Iterator[str]:
    if no_cache:
        return
    if cache_dir.is_dir():
        logger.info(f'Reading cache {cache_dir}')
        for cache_file in os.scandir(cache_dir):
            if cache_file.is_file():
                yield Path(cache_file.path).read_text()


def _write_events_to_cache(events: List[caldav.Event], cache_dir: Path):
    logger.info(f'Writing cache {cache_dir}')
    cache_dir.mkdir(parents=True, exist_ok=True)
    for event in events:
        _, event_id = event.url.rsplit('/', maxsplit=1)
        cache_file = cache_dir / event_id
        cache_file.write_text(event.data)


def download_events(
    url: str, username: str, password: str, cache_dir: Path, no_cache: bool
) -> List[str]:
    events_data = list(_read_events_data_from_cache(cache_dir, no_cache))
    if events_data:
        return events_data
    logger.info('Connecting to %s', url)
    client = caldav.DAVClient(url, username=username, password=password)
    logger.info('Reading principal')
    principal = client.principal()
    events = list(
        itertools.chain.from_iterable(
            calendar.events() for calendar in principal.calendars()
        )
    )
    _write_events_to_cache(events, cache_dir)
    return [event.data for event in events]


def parse_events(
    events_data: Iterable[str], subprovider: str
) -> Iterator[Item]:
    for event_data in events_data:
        lines = io.StringIO(event_data)
        for event in parse_calendar(lines):
            yield Item(
                dt=event.one_date, text=event.name, subprovider=subprovider
            )


def main(config: dict, no_cache: bool, *args, **kwargs) -> Iterator[Item]:
    url = config['url']
    username = config['username']
    password = lookup_secret(config['password_key'], config['password_val'])
    cache_dir = Path(config['cache_dir'])
    events_data = download_events(url, username, password, cache_dir, no_cache)
    return parse_events(events_data, subprovider=url)
