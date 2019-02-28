import csv
import datetime
import logging
from typing import Iterator

import pystache

from automatic_journal.common import Item

logger = logging.getLogger(__name__)


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
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
