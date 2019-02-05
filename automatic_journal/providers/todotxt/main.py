import datetime
import logging
import re
import sys
from typing import Iterator

from automatic_journal.common import Item

logger = logging.getLogger(__name__)


def load_config(config_json: dict) -> dict:
    try:
        path = config_json['todotxt']['path']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {'path': path}


def read_todotxt(path: str) -> Iterator[Item]:
    logger.info('Reading todo.txt file %s', path)
    with open(path) as f:
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
            yield Item(dt=dt, text=text, subprovider=path)


def main(config_json: dict):
    config = load_config(config_json)
    return read_todotxt(config['path'])
