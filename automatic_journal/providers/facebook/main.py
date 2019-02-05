import csv
import datetime
import json
import logging
import re
import sys
from dataclasses import dataclass
from functools import partial, reduce
from typing import Iterable, Iterator, Tuple

import dateparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_date_time(s: str) -> datetime.datetime:
    s = re.sub(r'\s\S{2}\s', ' ', s)  # remove "at", "um"...
    s = re.sub(r'UTC([+-]\d{2})', r'\g<1>00', s)  # "UTC+01" > "+0100"
    s = re.sub(r'\b(\d{1}[ :])', r'0\g<1>', s)  # "1:37" > "01:37"
    dt = dateparser.parse(s)
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


def _parse_timeline_page(soup: BeautifulSoup) -> Iterator[Status]:
    for p in soup.find_all('p'):
        comment_el = p.find(class_='comment')
        if not comment_el:
            continue
        text = comment_el.string
        if not text or re.search(
            r'hat an .+ teilgenommen|hat .+ abonniert\.$', str(p.contents[1])
        ):
            logger.warn('Not a status, skipping: "%s"', text)
            continue
        dt_str = p.find(class_='meta').string
        dt = parse_date_time(dt_str)
        logger.info('Found status from %s: %s', dt, text)
        yield Status(dt=dt, text=text)


def parse_all_archives(config: dict) -> Iterator[Tuple[Status, str]]:
    for path in config['paths']:
        logger.info('Reading Facebook archive %s', path)
        with open(path) as f:
            html = f.read()
            soup = BeautifulSoup(html, 'html.parser')
            for status in _parse_timeline_page(soup):
                yield status, path


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
            parse_all_archives,
            partial(format_csv, provider='facebook'),
            writer.writerows,
        )(config)
