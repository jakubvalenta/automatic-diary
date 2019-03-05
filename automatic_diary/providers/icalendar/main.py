import datetime
import logging
import quopri
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

import ics
import ics.parse

from automatic_diary.model import Item

logger = logging.getLogger(__name__)
provider = Path(__file__).parent.name


def quopri_decode(s: Optional[str]) -> str:
    if not s:
        return ''
    try:
        return quopri.decodestring(s.encode()).decode()
    except ValueError:
        return s
    return s


@dataclass
class Event:
    _name: Optional[str]
    _location: Optional[str]
    begin: datetime.datetime
    all_day: bool

    @classmethod
    def from_ics_event(cls, event: ics.Event):
        # TODO: multiple days
        return cls(
            _name=event.name,
            _location=event.location,
            begin=event.begin.datetime,
            all_day=event.all_day,
        )

    @property
    def name(self) -> str:
        name = quopri_decode(self._name)
        location = quopri_decode(self._location)
        if location:
            return f'{name} ({location})'
        return name


def _clean_ics_text(lines: Iterable[str]) -> Iterator[str]:
    current_line = ''
    for line in lines:
        if line.startswith('='):
            current_line += line
            continue
        else:
            yield current_line
            current_line = line
    if current_line:
        yield current_line


def parse_calendar(lines: Iterable[str]) -> Iterator[Event]:
    calendar = ics.Calendar(_clean_ics_text(lines))
    for event in calendar.events:
        yield Event.from_ics_event(event)


def _read_calendar(path: Path) -> Iterator[Event]:
    logger.info('Reading calendar %s', path)
    with path.open() as f:
        yield from parse_calendar(f)


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    paths = config['paths']
    unique_events: List[Event] = []
    for path_str in paths:
        path = Path(path_str)
        subprovider = path.name
        for event in _read_calendar(path):
            if event not in unique_events:
                yield Item.normalized(
                    datetime_=event.begin,
                    text=event.name,
                    provider=provider,
                    subprovider=subprovider,
                    all_day=event.all_day,
                )
                unique_events.append(event)
