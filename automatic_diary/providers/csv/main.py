import csv
import datetime
import logging
from pathlib import Path
from typing import Iterator

import pystache

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = Path(config['path'])
    subprovider = path.name
    logger.info('Reading CSV file %s', path)
    renderer = pystache.Renderer(escape=lambda u: u)
    date_source_tmpl = pystache.parse(config['date_source'])
    text_source_tmpl = pystache.parse(config['text_source'])
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = renderer.render(text_source_tmpl, row)
            datetime_ = datetime.datetime.strptime(
                renderer.render(date_source_tmpl, row), config['date_format']
            )
            yield Item.normalized(
                datetime_=datetime_,
                text=text,
                provider=provider,
                subprovider=subprovider,
                all_day=True,
            )
