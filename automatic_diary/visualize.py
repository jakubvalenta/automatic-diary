import argparse
import csv
import datetime
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, List, TypeVar

from jinja2 import Environment, PackageLoader

from automatic_diary.common import Item

logger = logging.getLogger(__name__)

today = datetime.date.today()


class Day:
    date: datetime.date
    items: List[Item]
    today: bool
    even: bool

    def __init__(self, date: datetime.date):
        self.date = date
        self.items = []
        self.today = self.date == today
        self.even = bool(self.date.month % 2)


def empty_days(date: datetime.date, start: int, stop: int) -> Iterator[Day]:
    for i in range(start, stop):
        empty_date = date + datetime.timedelta(days=i)
        logger.info('Empty day %s', empty_date)
        yield Day(empty_date)


def read_days(csv_path: str) -> Iterator[Day]:
    last_day = None
    with open(csv_path) as f:
        reader = csv.reader(f)
        for row in reader:
            dt_str, provider, subprovider, text = row
            dt = datetime.datetime.fromisoformat(dt_str)
            item = Item(
                dt=dt, text=text, provider=provider, subprovider=subprovider
            )
            date = item.date
            if not last_day:
                last_day = Day(date)
                yield from empty_days(
                    last_day.date, start=-dt.weekday(), stop=0
                )
            elif date != last_day.date:
                yield last_day
                yield from empty_days(
                    last_day.date, start=1, stop=(date - last_day.date).days
                )
                logger.info('New day %s', date)
                last_day = Day(date)
            last_day.items.append(item)
        if last_day:
            yield last_day


T = TypeVar('T')


def group(items: Iterable[T], size: int) -> Iterator[List[T]]:
    current_group: List[T] = []
    for i, item in enumerate(items):
        if i % size == 0:
            yield current_group
            current_group.clear()
        current_group.append(item)
    yield current_group


env = Environment(loader=PackageLoader('automatic_diary', 'templates'))
template = env.get_template('template.html')


def visualize(csv_path, output_html_path):
    days = read_days(csv_path)
    stream = template.stream(weeks=group(days, 7))
    with Path(output_html_path).open('w') as f:
        f.writelines(stream)


def main():
    parser = argparse.ArgumentParser(
        description='Visualize Automatic Diary CSV'
    )
    parser.add_argument('csv_path', help='Input CSV file path')
    parser.add_argument('output_html_path', help='Output HTML file path')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Enable debugging output'
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(
            stream=sys.stdout, level=logging.INFO, format='%(message)s'
        )
    visualize(args.csv_path, args.output_html_path)
