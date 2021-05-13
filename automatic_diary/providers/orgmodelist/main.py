import logging
import re
from pathlib import Path
from typing import Iterator

import dateparser
from PyOrgMode import PyOrgMode

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name

regex_item = re.compile(r'^- (?P<text>.+) [<\[](?P<date>.+)[>\]]\s$')


class OrgModeError(Exception):
    pass


def parse_orgmode_list(
    org: PyOrgMode.OrgDataStructure, subprovider: str
) -> Iterator[Item]:
    for str_or_node in org.root.content:
        if isinstance(str_or_node, PyOrgMode.OrgNode.Element):
            raise OrgModeError('Conversion to CSV doesn\'t support sections')
        if str_or_node == '\n' or str_or_node.startswith('#'):
            continue
        m = regex_item.search(str_or_node)
        if not m:
            raise OrgModeError(f'Unknow format of line "{str_or_node}"')
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


def read_org(path: Path) -> PyOrgMode.OrgDataStructure:
    org = PyOrgMode.OrgDataStructure()
    org.load_from_file(path)
    return org


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = Path(config['path'])
    subprovider = path.name
    logger.info('Reading Org-mode file %s', path)
    org = read_org(path)
    yield from parse_orgmode_list(org, subprovider)
