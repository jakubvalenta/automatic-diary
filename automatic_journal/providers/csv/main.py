import csv
import datetime
import json
import logging
import sys
from dataclasses import dataclass
from functools import partial, reduce
from typing import Iterable, Iterator, Tuple

import pystache

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        path = config['csv']['path']
        date_source = config['csv']['date_source']
        date_format = config['csv']['date_format']
        text_source = config['csv']['text_source']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {
        'path': path,
        'date_source': date_source,
        'date_format': date_format,
        'text_source': text_source,
    }


@dataclass
class Item:
    dt: datetime.datetime
    text: str


def read_csv(config: dict) -> Iterator[Item]:
    logger.info('Reading CSV file %s', config['path'])
    renderer = pystache.Renderer(escape=lambda u: u)
    date_source_tmpl = pystache.parse(config['date_source'])
    text_source_tmpl = pystache.parse(config['text_source'])
    with open(config['path']) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt_str = renderer.render(date_source_tmpl, row)
            text = renderer.render(text_source_tmpl, row)
            dt = datetime.datetime.strptime(dt_str, config['date_format'])
            yield Item(dt=dt, text=text)


def format_csv(
    items: Iterable[Item], provider: str, subprovider: str
) -> Iterator[Tuple[str, str, str, str]]:
    for item in items:
        yield (item.dt.isoformat(), provider, subprovider, item.text)


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)

    return wrapped


def main(config_path: str, csv_path: str):
    config = load_config(config_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        chain(
            read_csv,
            partial(format_csv, provider='csv', subprovider=config['path']),
            writer.writerows,
        )(config)
