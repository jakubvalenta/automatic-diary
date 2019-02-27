import csv
import datetime
import logging
import sys
from typing import Iterator

import pystache

from automatic_journal.common import Item

logger = logging.getLogger(__name__)


def load_config(config_json: dict) -> dict:
    try:
        path = config_json['csv']['path']
        date_source = config_json['csv']['date_source']
        date_format = config_json['csv']['date_format']
        text_source = config_json['csv']['text_source']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {
        'path': path,
        'date_source': date_source,
        'date_format': date_format,
        'text_source': text_source,
    }


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
            yield Item(dt=dt, text=text, subprovider=config['path'])


def main(config_json: dict, *args, **kwargs) -> Iterator[Item]:
    config = load_config(config_json)
    return read_csv(config)
