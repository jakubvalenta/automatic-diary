import logging
import re
from pathlib import Path
from typing import Iterator

import dateparser
import orgparse

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name

regex_item = re.compile(r'^- (?P<text>.+) [<\[](?P<date>.+)[>\]]\s*$')


class OrgModeError(Exception):
    pass


def parse_orgmode_list(org: orgparse.OrgNode, subprovider: str) -> Iterator[Item]:
    for line in org.root.body.splitlines():
        if not line or line.startswith('#'):
            continue
        m = regex_item.search(line)
        if not m:
            raise OrgModeError(f'Unknow format of line "{line}"')
        text = m.group('text')
        date_str = m.group('date')
        datetime_ = dateparser.parse(date_str)
        if not datetime_:
            logger.warn('Failed to parse date "%s"', date_str)
            continue
        all_day = not any((datetime_.hour, datetime_.minute, datetime_.second))
        yield Item.normalized(
            datetime_=datetime_,
            text=text,
            provider=provider,
            subprovider=subprovider,
            all_day=all_day,
        )


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = Path(config['path'])
    subprovider = path.name
    logger.info('Reading Org-mode file %s', path)
    org = orgparse.load(path)
    yield from parse_orgmode_list(org, subprovider)
