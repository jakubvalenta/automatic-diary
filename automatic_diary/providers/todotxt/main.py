import datetime
import logging
import re
from pathlib import Path
from typing import Iterator

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name

regex_line = re.compile(
    r'^x (?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})' r'( \([A-F]\))? \d{4}-\d{2}-\d{2} (?P<text>.+)\s*$'
)
regex_threshold = re.compile(r' t:\d{4}-\d{2}-\d{2}')
regex_due = re.compile(r' (due|DUE):\d{4}-\d{2}-\d{2}')


def _clean_text(s: str) -> str:
    s = regex_threshold.sub('', s)
    s = regex_due.sub('', s)
    return s


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = Path(config['path'])
    subprovider = path.name
    logger.info('Reading todo.txt file %s', path)
    with path.open() as f:
        for line in f:
            m = regex_line.match(line)
            if not m:
                continue
            datetime_ = datetime.datetime(int(m.group('y')), int(m.group('m')), int(m.group('d')))
            text = _clean_text(m.group('text'))
            yield Item.normalized(
                datetime_=datetime_,
                text=text,
                provider=provider,
                subprovider=subprovider,
                all_day=True,
            )
