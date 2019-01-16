#!/usr/bin/env python3

import csv
import datetime
import json
import logging
import sys
from functools import partial, reduce
from pathlib import Path
from typing import Iterable, Iterator, Tuple

import requests
import tzlocal
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TDateTimeAndText = Tuple[datetime.datetime, str]


HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0',
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Referer': 'https://www.csfd.cz/',
}


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        profile_url = config['csfd']['profile_url']
        cache_dir = config['csfd']['cache_dir']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {
        'profile_url': profile_url,
        'cache_dir': cache_dir
    }


def _download_ratings_page(profile_url: str,
                           cache_dir: Path,
                           page_no: int = 1) -> str:
    cache_file = cache_dir / f'{page_no:d}.html'
    if cache_file.is_file():
        logger.info(f'Reading cache {cache_file}')
        return cache_file.read_text()
    page_url = f'{profile_url}hodnoceni/strana-{page_no}/'
    logger.info(f'Downloading {page_url}')
    r = requests.get(page_url, headers=HEADERS)
    html = r.text
    logger.info(f'Writing cache {cache_file}')
    if cache_file.exists():
        raise Exception(f'Cache file {cache_file} already exists')
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html)
    return html


def download_all_ratings_pages(config: dict) -> Iterator[BeautifulSoup]:
    profile_url = config['profile_url']
    cache_dir = Path(config['cache_dir'])
    html = _download_ratings_page(profile_url, cache_dir)
    soup = BeautifulSoup(html, 'html.parser')
    page_links = soup.select('.profile-content .paginator a')
    page_num_links = [node for node in page_links if not node.get('class')]
    last_page_num_link = page_num_links[-1]
    last_page_num = int(last_page_num_link.string)
    logger.info('Found %d pages', last_page_num)
    yield soup
    for page_no in range(2, last_page_num + 1):
        html = _download_ratings_page(profile_url, cache_dir, page_no)
        soup = BeautifulSoup(html, 'html.parser')
        yield soup


def _parse_ratings_page(soup: BeautifulSoup) -> Iterator[TDateTimeAndText]:
    for tr in soup.select('.profile-content .ui-table-list tbody tr'):
        dt = datetime.datetime.strptime(
            tr.find_all('td')[-1].string,
            '%d.%m.%Y'
        )
        text = tr.find(class_='film').string
        logger.info(f'Found film {text} rated on {dt}')
        yield (dt, text)


def parse_ratings_pages(
        soups: Iterable[BeautifulSoup]) -> Iterator[TDateTimeAndText]:
    for soup in soups:
        yield from _parse_ratings_page(soup)


def format_csv(dt_and_text: Iterable[TDateTimeAndText],
               provider: str,
               subprovider: str) -> Iterator[Tuple[str, str, str, str]]:
    for dt, text in dt_and_text:
        tz = tzlocal.get_localzone()
        dt_localized = tz.localize(dt)
        yield (
            dt_localized.isoformat(),
            provider,
            subprovider,
            text
        )


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)
    return wrapped


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO,
        format='%(message)s')
    _, config_path, csv_path = sys.argv
    config = load_config(config_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        chain(
            download_all_ratings_pages,
            parse_ratings_pages,
            partial(
                format_csv,
                provider='csfd',
                subprovider=config['profile_url']
            ),
            writer.writerows
        )(config)
