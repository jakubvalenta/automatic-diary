import csv
import datetime
import json
import logging
import quopri
import re
import sys
from dataclasses import dataclass
from functools import partial, reduce
from typing import Iterable, Iterator, Tuple, Union

import ics
import ics.parse

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path) as f:
        config = json.load(f)
    try:
        paths = config['icalendar']['paths']
    except (KeyError, TypeError):
        logger.error('Invalid config')
        sys.exit(1)
    return {'paths': paths}


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
    def clean_text(self):
        return re.sub(r'\s+', ' ', self.name).strip()

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


TEventAndPath = Tuple[Event, str]


def read_all_calendars(config: dict) -> Iterator[Tuple[Event, str]]:
    unique_events = []
    for path in config['paths']:
        for event in read_calendar(path):
            if event not in unique_events:
                yield event, path
                unique_events.append(event)


def format_csv(
    events_and_paths: Iterable[Tuple[Event, str]], provider: str
) -> Iterator[Tuple[str, str, str, str]]:
    for event, path in events_and_paths:
        yield (event.one_date.isoformat(), provider, path, event.clean_text)


def chain(*funcs):
    def wrapped(initializer):
        return reduce(lambda x, y: y(x), funcs, initializer)

    return wrapped


def main(config_path: str, csv_path: str):
    config = load_config(config_path)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        chain(
            read_all_calendars,
            partial(format_csv, provider='calendar'),
            writer.writerows,
        )(config)
