import argparse
import csv
import datetime
import logging
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

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


class Stat:
    count: int = 0
    val: int = 0


class Week(list):
    stats: Dict[str, Stat]

    def __init__(self):
        self.stats = defaultdict(Stat)

    def append(self, day: Day):
        super().append(day)
        for item in day.items:
            self.stats[item.provider].count += 1


class Year(list):
    def __init__(self, days: Iterable[Day]):
        self._add_days(days)
        self._calc_stats()

    def _add_days(self, days: Iterable[Day]):
        week = Week()
        for i, day in enumerate(days):
            if i % 7 == 0:
                self.append(week)
                week = Week()
            week.append(day)
        self.append(week)

    def _calc_stats(self):
        for provider in ('csfd',):
            counts = [
                week.stats[provider].count
                for week in self
                if week.stats[provider].count
            ]
            mean = statistics.mean(counts)
            for week in self:
                week.stats[provider].val = round(
                    min(week.stats[provider].count / mean, 1) * 100
                )


env = Environment(loader=PackageLoader('automatic_diary', 'templates'))
template = env.get_template('template.html')


def visualize(csv_path, output_html_path):
    days = read_days(csv_path)
    year = Year(days)
    stream = template.stream(year=year)
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
