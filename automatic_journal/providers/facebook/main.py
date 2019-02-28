import datetime
import logging
import re
from dataclasses import dataclass
from typing import Iterator

import dateparser
from bs4 import BeautifulSoup

from automatic_journal.common import Item

logger = logging.getLogger(__name__)


def parse_date_time(s: str) -> datetime.datetime:
    s = re.sub(r'\s(at|um)\s', ' ', s)
    s = re.sub(r'UTC([+-]\d{2})', r'\g<1>00', s)  # "UTC+01" > "+0100"
    s = re.sub(r'\b(\d{1}[ :])', r'0\g<1>', s)  # "1:37" > "01:37"
    dt = dateparser.parse(s)
    logger.info('Parsed date string %s as %s', s, dt)
    return dt


@dataclass
class Status:
    dt: datetime.datetime
    text: str


filter_regex = re.compile(
    '|'.join(
        [
            r'hat an .+ teilgenommen\.',
            r'hat .+ abonniert\.',
            r'hat eine private Veranstaltung erstellt\.',
        ]
    )
)


def parse_timeline_page(soup: BeautifulSoup) -> Iterator[Status]:
    for p in soup.find_all('p'):
        comment_el = p.find(class_='comment')
        if not comment_el:
            continue
        text = comment_el.string
        if not text or filter_regex.search(str(p.contents[1])):
            logger.warn('Not a status, skipping: "%s"', text)
            continue
        dt_str = p.find(class_='meta').string
        dt = parse_date_time(dt_str)
        logger.info('Found status from %s: %s', dt, text)
        yield Status(dt=dt, text=text)


def read_html(path: str) -> BeautifulSoup:
    with open(path) as f:
        html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
    return soup


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = config['path']
    logger.info('Reading Facebook archive %s', path)
    soup = read_html(path)
    for status in parse_timeline_page(soup):
        yield Item(dt=status.dt, text=status.text, subprovider=path)
