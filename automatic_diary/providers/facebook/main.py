import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

import dateparser
from bs4 import BeautifulSoup

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name


@dataclass
class Status:
    datetime_: datetime.datetime
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


def parse_datetime(s: str) -> Optional[datetime.datetime]:
    s = re.sub(r'\s(at|um)\s', ' ', s)
    s = re.sub(r'UTC([+-]\d{2})', r'\g<1>00', s)  # "UTC+01" > "+0100"
    s = re.sub(r'\b(\d{1}[ :])', r'0\g<1>', s)  # "1:37" > "01:37"
    datetime_ = dateparser.parse(s)
    logger.info('Parsed date string %s as %s', s, datetime_)
    return datetime_


def _parse_timeline_page(soup: BeautifulSoup) -> Iterator[Status]:
    for p in soup.find_all('p'):
        comment_el = p.find(class_='comment')
        if not comment_el:
            continue
        text = comment_el.string
        if not text or filter_regex.search(str(p.contents[1])):
            logger.warn('Not a status, skipping: "%s"', text)
            continue
        formatted_datetime = p.find(class_='meta').string
        datetime_ = parse_datetime(formatted_datetime)
        if not datetime_:
            logger.warn('Failed to parse date "%s"', formatted_datetime)
            continue
        logger.info('Found status from %s: %s', datetime_, text)
        yield Status(datetime_=datetime_, text=text)


def _read_html(path: str) -> BeautifulSoup:
    with open(path) as f:
        html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
    return soup


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = config['path']
    username = config['username']
    logger.info('Reading Facebook archive %s', path)
    soup = _read_html(path)
    for status in _parse_timeline_page(soup):
        yield Item.normalized(
            datetime_=status.datetime_,
            text=status.text,
            provider=provider,
            subprovider=username,
        )
