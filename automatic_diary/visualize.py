import argparse
import csv
import datetime
import json
import logging
import re
import sys
from calendar import Calendar
from collections import defaultdict
from pathlib import Path
from pprint import pprint as pp
from statistics import quantiles
from typing import Iterable, Sequence, TypeAlias

from dateutil.rrule import DAILY, rrule
from jinja2 import Environment, PackageLoader, Template, select_autoescape
from more_itertools import chunked

from automatic_diary.model import Item

logger = logging.getLogger(__name__)

# Example:
# {
#     2023: {
#         11: {
#             1: [Item, Item],
#             5: [Item]
#         }
#     }
# }
ItemsByYearMonthDay: TypeAlias = dict[int, dict[int, dict[int, list[Item]]]]

# Example:
# {
#     2023: [
#         [
#             datetime.date(2022, 12, 26),
#             datetime.date(2022, 12, 27),
#             datetime.date(2022, 12, 28),
#             datetime.date(2022, 12, 29),
#             datetime.date(2022, 12, 30),
#             datetime.date(2022, 12, 31),
#             datetime.date(2023, 1, 1)
#         ],
#         [
#             datetime.date(2023, 1, 2),
#             datetime.date(2023, 1, 3),
#             datetime.date(2023, 1, 4),
#             datetime.date(2023, 1, 5),
#             datetime.date(2023, 1, 6),
#             datetime.date(2023, 1, 7),
#             datetime.date(2023, 1, 8)
#         ],
#         ...
#     ]
# }
DatesByYearWeek: TypeAlias = dict[int, list[list[datetime.date]]]

# Example:
# {
#     2023: [
#         {"git": 13, "csv: 10"}, # first week
#         {"git": 1, "csv: 90"}, # second week
#         ...
#     ]
# }
ProviderStats: TypeAlias = dict[int, list[dict[str, int]]]


def read_items(
    rows: Iterable[list[str]], tags_dict: dict[str, str] | None = None
) -> ItemsByYearMonthDay:
    """Read passed CSV rows into a dict.

    Example return value:

    {
        2023: {
            11: {
                1: [Item, Item],
                5: [Item]
            }
        }
    }
    """
    items_by_year_month_day: ItemsByYearMonthDay = {}
    for formatted_datetime, provider, subprovider, text in rows:
        datetime_ = datetime.datetime.fromisoformat(formatted_datetime)
        tags = []
        if tags_dict:
            for pattern, tag in tags_dict.items():
                if re.search(pattern, text):
                    tags.append(tag)
        item = Item.normalized(
            datetime_=datetime_,
            text=text,
            provider=provider,
            subprovider=subprovider,
            tags=tags,
        )
        date = item.date
        if date.year not in items_by_year_month_day:
            items_by_year_month_day[date.year] = {}
        if date.month not in items_by_year_month_day[date.year]:
            items_by_year_month_day[date.year][date.month] = {}
        if date.day not in items_by_year_month_day[date.year][date.month]:
            items_by_year_month_day[date.year][date.month][date.day] = []
        items_by_year_month_day[date.year][date.month][date.day].append(item)
    return items_by_year_month_day


def gen_dates(items_by_year_month_day: ItemsByYearMonthDay) -> DatesByYearWeek:
    """Generate a calendar structure for passed items.

    Example return value:

    {
        2023: [
            [
                datetime.date(2022, 12, 26),
                datetime.date(2022, 12, 27),
                datetime.date(2022, 12, 28),
                datetime.date(2022, 12, 29),
                datetime.date(2022, 12, 30),
                datetime.date(2022, 12, 31),
                datetime.date(2023, 1, 1)
            ],
            [
                datetime.date(2023, 1, 2),
                datetime.date(2023, 1, 3),
                datetime.date(2023, 1, 4),
                datetime.date(2023, 1, 5),
                datetime.date(2023, 1, 6),
                datetime.date(2023, 1, 7),
                datetime.date(2023, 1, 8)
            ],
            ...
        ]
    }
    """
    calendar = Calendar()
    return {
        year: [
            [datetime_.date() for datetime_ in week]
            for week in chunked(
                rrule(
                    DAILY,
                    dtstart=calendar.monthdatescalendar(year, 1)[0][0],
                    until=calendar.monthdatescalendar(year, 12)[-1][-1],
                ),
                7,
            )
        ]
        for year in items_by_year_month_day
    }


def deciles(data: Sequence[float]) -> list[float]:
    return quantiles(
        data if len(data) >= 2 else list(data) + [0], n=10, method="inclusive"
    )


def quantile_rank(score: float, cut_points: list[float]) -> int:
    for quantile, cut_point in enumerate(cut_points, start=1):
        if score < cut_point:
            return quantile
    return len(cut_points) + 1


def calc_provider_stats(
    dates_by_year_week: DatesByYearWeek,
    items_by_year_month_day: ItemsByYearMonthDay,
) -> ProviderStats:
    """Calculate provider stats.

    Return a value that describes how small or large the number of items was for each provider each
    week.

    First the function calculates how many items there were for each provider each week. Example:

    - 1st week of November 2023: 150 "git" items, 70 "csv" items.
    - 2nd week of November 2023: 145 "git" items, 30 "csv" items.
    - 3rd week of November 2023: 120 "git" items, 10 "csv" items.
    - 4th week of November 2023: 100 "git" items, 90 "csv" items.

    Then it calculates deciles for each provider:

    - "git": quantile([150, 145, 120, 100], n=10, method="inclusive")
    - "csv": quantile([70, 30, 10, 90], n=10, method="inclusive")

    Finally it calculates in which decile each provider was each week:

    - 1st week of November 2023: "git" 10th decile, "csv" 7th decile.
    - 2nd week of November 2023: "git" 7th decile, "csv" 4th decile.
    - 3rd week of November 2023: "git" 4th decile, "csv" 1st decile.
    - 4th week of November 2023: "git" 1st decile, "csv" 10th decile.

    And returns it like this:

    {
        2023: [
            {"git": 10, "csv": 7},
            {"git": 7, "csv": 7},
            {"git": 4, "csv": 1},
            {"git": 1, "csv": 10},
        ]
    }
    """
    # Dictionary in format:
    # {
    #     2023: [
    #         {"git": 150, "csv": 70},
    #         {"git": 145, "csv": 30},
    #         {"git": 120, "csv": 10},
    #         {"git": 100, "csv": 90},
    #         ...
    #     ]
    # }
    item_count_by_year_week_provider: dict[int, list[dict[str, int]]] = defaultdict(
        list
    )

    # Dictionary in format:
    # {
    #     "git": [150, 145, 120, 110],
    #     "csv": [70, 30, 10, 90],
    # }
    item_counts_by_provider: dict[str, list[int]] = defaultdict(list)

    for year, weeks in dates_by_year_week.items():
        for week in weeks:
            week_item_count_by_provider: dict[str, int] = defaultdict(int)
            for date in week:
                try:
                    items = items_by_year_month_day[date.year][date.month][date.day]
                except KeyError:
                    continue
                for item in items:
                    week_item_count_by_provider[item.provider] += 1
            for provider, item_count in week_item_count_by_provider.items():
                item_counts_by_provider[provider].append(item_count)
            item_count_by_year_week_provider[year].append(week_item_count_by_provider)

    # Dictionary in format:
    # {
    #     "git": [106.0, 112.0, 118.0, 125.0, 132.5, 140.0, 145.5, 147.0, 148.5],
    #     "csv": [16.0, 22.0, 28.0, 38.0, 50.0, 62.0, 72.0, 78.0, 84.0],
    # }
    deciles_by_provider: dict[str, list[float]] = {
        provider: deciles(item_counts)
        for provider, item_counts in item_counts_by_provider.items()
    }

    # Dictionary in format:
    # {
    #     2023: [
    #         {"git": 10, "csv": 7}, # first week
    #         {"git": 7, "csv": 7}, # second week
    #         {"git": 4, "csv": 1}, # third week
    #         {"git": 1, "csv": 10}, # fourth week
    #     ]
    # }
    return {
        year: [
            {
                provider: quantile_rank(item_count, deciles_by_provider[provider])
                for provider, item_count in item_count_by_provider.items()
            }
            for item_count_by_provider in weeks
        ]
        for year, weeks in item_count_by_year_week_provider.items()
    }


def _is_regex(s: str, regex: str) -> bool:
    if not regex:
        return False
    return re.search(regex, s) is not None


def _has_deep(d: dict, *attrs: str) -> bool:
    for attr in attrs:
        if attr in d:
            d = d[attr]
        else:
            return False
    return True


def _render_template(
    template: Template,
    path: Path,
    *,
    css_url: str | None,
    dates_by_year_week: DatesByYearWeek,
    items_by_year_month_day: ItemsByYearMonthDay,
    provider_stats: ProviderStats,
    today: datetime.date,
    year: int,
) -> None:
    stream = template.stream(
        {
            "css_url": css_url,
            "dates_by_week": dates_by_year_week[year],
            "items_by_year_month_day": items_by_year_month_day,
            "provider_stats": provider_stats[year],
            "today": today,
            "year": year,
        }
    )
    with path.open("w") as f:
        f.writelines(stream)


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize Automatic Diary CSV")
    parser.add_argument(
        "csv_file", type=argparse.FileType("r"), help="Input CSV file path"
    )
    parser.add_argument("output_path", help="Output HTML file or directory path")
    parser.add_argument(
        "-a",
        "--all-years",
        action="store_true",
        help="Visualize all years, write them in the directory OUTPUT_PATH; "
        "by default only the last year is visualized and written to the file OUTPUT_PATH",
    )
    parser.add_argument("-c", "--css-url", help="Additional CSS URL")
    parser.add_argument(
        "-i",
        "--highlight",
        help="[DEPRECATED] Highlight items matching regex",
        # TODO Use deprecated=True once we support Python 3.13.
    )
    parser.add_argument(
        "-t",
        "--tags-file",
        type=argparse.FileType("r"),
        help='Tags JSON file path. The file format is {"<regex>": "<tag>"}. '
        'A class "tag-<tag>" will be added to each item whose text matches <regex>.',
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debugging output"
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
    if args.highlight:
        print(
            "Option -i / --highlight is deprecated. Use a tags file with content "
            '`{"<regex>": "highlight"}` and pass it using -t / --tags-file instead. '
            "Then add a custom CSS with content `.tag-highlight { /* your CSS rules */ }` "
            "and pass it using -c / --css-file.",
            file=sys.stderr,
        )
        sys.exit(1)

    items_by_year_month_day: ItemsByYearMonthDay = {}
    reader = csv.reader(args.csv_file)
    tags_dict = json.load(args.tags_file) if args.tags_file else None
    items_by_year_month_day = read_items(reader, tags_dict)
    dates_by_year_week = gen_dates(items_by_year_month_day)
    provider_stats = calc_provider_stats(dates_by_year_week, items_by_year_month_day)
    css_url = args.css_url
    today = datetime.date.today()

    environment = Environment(
        autoescape=select_autoescape(["html"]),
        loader=PackageLoader("automatic_diary", "templates"),
    )
    environment.tests["hasdeep"] = _has_deep
    environment.tests["regex"] = _is_regex
    template = environment.get_template("template.html")

    if args.all_years:
        output_dir_path = Path(args.output_path)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        for year in items_by_year_month_day:
            _render_template(
                template,
                (output_dir_path / f"{year}.html"),
                css_url=css_url,
                dates_by_year_week=dates_by_year_week,
                items_by_year_month_day=items_by_year_month_day,
                provider_stats=provider_stats,
                today=today,
                year=year,
            )
    else:
        output_file_path = Path(args.output_path)
        year = max(items_by_year_month_day.keys())
        _render_template(
            template,
            output_file_path,
            css_url=css_url,
            dates_by_year_week=dates_by_year_week,
            items_by_year_month_day=items_by_year_month_day,
            provider_stats=provider_stats,
            today=today,
            year=year,
        )


if __name__ == "__main__":
    main()
