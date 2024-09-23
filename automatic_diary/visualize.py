import argparse
import csv
import datetime
import logging
import re
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

from jinja2 import Environment, PackageLoader, select_autoescape

from automatic_diary.model import Item

logger = logging.getLogger(__name__)

today = datetime.date.today()


@dataclass
class Day:
    date: datetime.date
    today: bool
    even: bool
    items: list[Item] = field(default_factory=list)

    @classmethod
    def from_date(cls, date: datetime.date, *args, **kwargs) -> "Day":
        today_ = date == today
        even = bool(date.month % 2)
        return cls(date, today_, even, *args, **kwargs)


class Week(list):
    pass


def _create_days_around(date: datetime.date, start: int, stop: int) -> Iterator[Day]:
    for i in range(start, stop):
        empty_date = date + datetime.timedelta(days=i)
        logger.info("Empty day %s", empty_date)
        yield Day.from_date(empty_date)


def _read_items(csv_path: str) -> Iterator[Item]:
    with open(csv_path) as f:
        reader = csv.reader(f)
        for row in reader:
            yield Item.from_tuple(row)


def _group_items_in_days(items: Iterable[Item]) -> Iterator[Day]:
    current_date = None
    current_items = []
    for item in items:
        date: datetime.date = item.date
        if not current_date:
            yield from _create_days_around(date, start=-date.weekday(), stop=0)
            current_date = date
        elif date != current_date:
            yield Day.from_date(current_date, current_items)
            yield from _create_days_around(current_date, start=1, stop=(date - current_date).days)
            logger.info("New day %s", date)
            current_date = date
            current_items = []
        current_items.append(item)
    if current_date:
        yield Day.from_date(current_date, current_items)


def _calc_perc(part: float, whole: float) -> int:
    return round(min(part / whole, 1) * 100)


def _calc_stats(weeks: Iterable[Week]) -> list[dict[str, int]]:
    provider_counts_by_week: list[dict[str, int]] = []
    provider_counts: dict[str, list[int]] = defaultdict(list)
    for week in weeks:
        week_provider_counts: dict[str, int] = defaultdict(int)
        for day in week:
            for item in day.items:
                week_provider_counts[item.provider] += 1
        for provider, counts in week_provider_counts.items():
            provider_counts[provider].append(counts)
        provider_counts_by_week.append(week_provider_counts)
    provider_means: dict[str, float] = {
        provider: statistics.mean(counts) for provider, counts in provider_counts.items()
    }
    stats = [
        {
            provider: _calc_perc(counts, provider_means[provider])
            for provider, counts in week_provider_counts.items()
        }
        for week_provider_counts in provider_counts_by_week
    ]
    return stats


def _group_days_in_weeks(days: Iterable[Day]) -> Iterator[Week]:
    days = list(days)
    n_days = len(days)
    week = Week()
    for i, day in enumerate(days):
        week.append(day)
        if i % 7 == 6 or i == n_days - 1:
            yield week
            week = Week()


def _matches_regex(s: str, regex: str) -> bool:
    if not regex:
        return False
    return re.search(regex, s) is not None


def _render_template(package: list[str], output_html_path: str, highlight: str, **context):
    environment = Environment(
        autoescape=select_autoescape(["html"]),
        loader=PackageLoader(*package[:-1]),
    )
    environment.tests["highlighted"] = lambda s: _matches_regex(s, highlight)
    template = environment.get_template(package[-1])
    stream = template.stream(**context)
    with Path(output_html_path).open("w") as f:
        f.writelines(stream)


def _visualize(csv_path: str, output_html_path: str, highlight: str):
    items = _read_items(csv_path)
    days = _group_items_in_days(items)
    weeks = list(_group_days_in_weeks(days))
    stats = _calc_stats(weeks)
    _render_template(
        ["automatic_diary", "templates", "template.html"],
        output_html_path,
        highlight,
        weeks=weeks,
        stats=stats,
    )


def main():
    parser = argparse.ArgumentParser(description="Visualize Automatic Diary CSV")
    parser.add_argument("csv_path", help="Input CSV file path")
    parser.add_argument("output_html_path", help="Output HTML file path")
    parser.add_argument("-i", "--highlight", help="Highlight items matching regex")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debugging output")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
    _visualize(args.csv_path, args.output_html_path, args.highlight)


if __name__ == "__main__":
    main()
