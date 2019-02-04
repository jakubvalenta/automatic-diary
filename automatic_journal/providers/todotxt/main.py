import csv
import datetime
import json
import logging
import re
import sys
from dataclasses import dataclass
from functools import partial, reduce
from typing import Iterable, Iterator, Tuple

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        path = config['todotxt']['path']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {'path': path}


@dataclass
class Item:
    dt: datetime.datetime
    text: str


def read_todotxt(config: dict) -> Iterator[Item]:
    logger.info('Reading todo.txt file %s', config['path'])
    with open(config['path']) as f:
        for line in f:
            m = re.match(
                (
                    r'^x (?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})'
                    r'( \([A-F]\))? \d{4}-\d{2}-\d{2} (?P<text>.+)\s*$'
                ),
                line,
            )
            if not m:
                continue
            dt = datetime.datetime(
                int(m.group('y')), int(m.group('m')), int(m.group('d'))
            )
            text = m.group('text')
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
            read_todotxt,
            partial(
                format_csv, provider='todotxt', subprovider=config['path']
            ),
            writer.writerows,
        )(config)
