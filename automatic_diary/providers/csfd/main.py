import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

import requests
from bs4 import BeautifulSoup

from automatic_diary.common import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0',  # noqa: E501
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa: E501
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Referer': 'https://www.csfd.cz/',
}


@dataclass
class Film:
    title: str
    date: datetime.date


def _download_ratings_page(
    profile_url: str, cache_dir: Path, no_cache: bool, page_no: int = 1
) -> str:
    cache_file = cache_dir / f'{page_no:d}.html'
    if not no_cache and cache_file.is_file():
        logger.info(f'Reading cache {cache_file}')
        return cache_file.read_text()
    page_url = f'{profile_url}hodnoceni/strana-{page_no}/'
    logger.info(f'Downloading {page_url}')
    r = requests.get(page_url, headers=HEADERS)
    html = r.text
    logger.info(f'Writing cache {cache_file}')
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(html)
    return html


def download_all_ratings_pages(
    profile_url: str, cache_dir: Path, no_cache: bool
) -> Iterator[BeautifulSoup]:
    html = _download_ratings_page(profile_url, cache_dir, no_cache)
    soup = BeautifulSoup(html, 'html.parser')
    page_links = soup.select('.profile-content .paginator a')
    page_num_links = [node for node in page_links if not node.get('class')]
    last_page_num_link = page_num_links[-1]
    last_page_num = int(last_page_num_link.string)
    logger.info('Found %d pages', last_page_num)
    yield soup
    for page_no in range(2, last_page_num + 1):
        html = _download_ratings_page(
            profile_url, cache_dir, no_cache, page_no
        )
        soup = BeautifulSoup(html, 'html.parser')
        yield soup


def _parse_ratings_page(soup: BeautifulSoup) -> Iterator[Film]:
    for tr in soup.select('.profile-content .ui-table-list tbody tr'):
        title = tr.find(class_='film').string
        date = datetime.datetime.strptime(
            tr.find_all('td')[-1].string, '%d.%m.%Y'
        ).date()
        logger.info('Found film %s rated on %s', title, date)
        yield Film(title=title, date=date)


def parse_ratings_pages(
    soups: Iterable[BeautifulSoup], subprovider: str
) -> Iterator[Item]:
    for soup in soups:
        for film in _parse_ratings_page(soup):
            yield Item(
                dt=film.date,
                text=film.title,
                provider=provider,
                subprovider=subprovider,
            )


def parse_username(url: str) -> Optional[str]:
    m = re.search(r'\/\d+-(\S+)\/$', url)
    if m:
        return m.group(1)
    return None


def main(config: dict, no_cache: bool, *args, **kwargs) -> Iterator[Item]:
    profile_url = config['profile_url']
    cache_dir = Path(config['cache_dir'])
    username = parse_username(profile_url)
    pages = download_all_ratings_pages(profile_url, cache_dir, no_cache)
    return parse_ratings_pages(pages, subprovider=username)
