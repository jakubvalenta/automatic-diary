import datetime
import logging
import quopri
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Union

import ics
import ics.parse

from automatic_journal.common import Item

logger = logging.getLogger(__name__)


@dataclass
class Event:
    _name: str
    begin: datetime.datetime
    all_day: bool

    @classmethod
    def from_ics_event(cls, event: ics.Event):
        # TODO: multiple days
        return cls(
            _name=event.name, begin=event.begin.datetime, all_day=event.all_day
        )

    @property
    def name(self):
        try:
            return quopri.decodestring(self._name).decode()
        except ValueError:
            return self._name

    @property
    def one_date(self) -> Union[datetime.datetime, datetime.date]:
        if self.all_day:
            return self.begin.date()
        return self.begin


def clean_ics_text(lines: Iterable[str]) -> Iterator[str]:
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
    calendar = ics.Calendar(clean_ics_text(lines))
    for event in calendar.events:
        yield Event.from_ics_event(event)


def read_calendar(path: str) -> Iterator[Event]:
    logger.info('Reading calendar %s', path)
    with open(path) as f:
        yield from parse_calendar(f)


def main(config: dict, *args, **kwargs) -> Iterator[Item]:
    paths = config['paths']
    unique_events: List[Event] = []
    for path in paths:
        for event in read_calendar(path):
            if event not in unique_events:
                yield Item(
                    dt=event.one_date, text=event.name, subprovider=path
                )
                unique_events.append(event)
