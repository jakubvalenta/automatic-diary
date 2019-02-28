import datetime
import logging
import re
from typing import Iterator

from automatic_journal.common import Item

logger = logging.getLogger(__name__)


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = config['path']
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
