import datetime
import logging
import re
from pathlib import Path
from typing import IO, Iterator, List, Optional

from more_itertools import peekable

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name

regex_heading = re.compile(r'^\* (?P<todo>TODO )?[<\[](?P<date>.+)[>\]]$')


def parse_orgmode(f: IO, subprovider: str) -> Iterator[Item]:
    current_datetime: Optional[datetime.datetime] = None
    current_paragraph: List[str] = []
    lines = peekable(f)
    for line in lines:
        line_clean = line.strip()
        if line_clean:
            m = regex_heading.match(line_clean)
            # Title line
            if m:
                if m.group('todo'):
                    current_datetime = None
                else:
                    current_datetime = datetime.datetime.strptime(
                        m.group('date'), '%Y-%m-%d %a'
                    )
            # Paragraph line but not before first heading
            elif current_datetime:
                current_paragraph.append(line_clean)
        # Empty line after paragraph or last line of file
        if not line_clean or not lines:
            if current_datetime and current_paragraph:
                yield Item.normalized(
                    datetime_=current_datetime,
                    text='\n'.join(current_paragraph),
                    provider=provider,
                    subprovider=subprovider,
                    all_day=True,
                )
                current_paragraph.clear()


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    path = Path(config['path'])
    subprovider = path.name
    logger.info('Reading Org-mode file %s', path)
    with path.open() as f:
        yield from parse_orgmode(f, subprovider)
