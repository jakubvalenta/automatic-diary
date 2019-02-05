import csv
import datetime
import json
import logging
import re
import sys
from dataclasses import dataclass
from functools import partial, reduce
from typing import Iterable, Iterator, Tuple

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_date_time(dt_str: str) -> datetime.datetime:
    m = re.search(
        r'(?P<month>\S+) (?P<day>\d{1,2}), (?P<year>\d{4}) at '
        r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})(?P<am_or_pm>am|pm) '
        r'UTC(?P<tz>[+-]\d{2})$',
        dt_str,
    )
    if not m:
        raise Exception(f'Failed to parse date {dt_str}')
    dt_str_full_numbers = (
        '{month} {day:>02} {year} {hour:>02}:{minute}{am_or_pm} {tz:<05}'
    ).format(**m.groupdict())
    dt = datetime.datetime.strptime(dt_str_full_numbers, '%B %d %Y %I:%M%p %z')
    return dt


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        paths = config['facebook']['paths']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {'paths': paths}


@dataclass
class Status:
    dt: datetime.datetime
    text: str

    @property
    def clean_text(self):
        return re.sub(r'\s+', ' ', self.text).strip()


def _parse_wall_page(soup: BeautifulSoup) -> Iterator[Status]:
    for p in soup.find_all('p'):
        comment_el = p.find(class_='comment')
        if not comment_el:
            continue
        text = comment_el.string
        dt_str = p.find(class_='meta').string
        dt = parse_date_time(dt_str)
        logger.info('Found status from %s: %s', dt, text)
        yield Status(dt=dt, text=text)


parsers = {'wall.htm': _parse_wall_page}


def parse_all_pages(config: dict) -> Iterator[Tuple[Status, str]]:
    for path in config['paths']:
        for path_end, parser in parsers.items():
            if path.endswith(path_end):
                with open(path) as f:
                    html = f.read()
                soup = BeautifulSoup(html, 'html.parser')
                for status in parser(soup):
                    yield status, path
                return
        raise Exception(f'No parser found for path {path}')


def format_csv(
    statuses_and_paths: Iterable[Tuple[Status, str]], provider: str
) -> Iterator[Tuple[str, str, str, str]]:
    for status, path in statuses_and_paths:
        yield (status.dt.isoformat(), provider, path, status.clean_text)


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)

    return wrapped


def main(config_path: str, csv_path: str):
    config = load_config(config_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        chain(
            parse_all_pages,
            partial(format_csv, provider='facebook'),
            writer.writerows,
        )(config)
