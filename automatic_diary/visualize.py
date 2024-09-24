import argparse
import csv
import datetime
import logging
import re
import sys
from calendar import Calendar
from collections import defaultdict
from pathlib import Path
from statistics import quantiles
from typing import Iterable, Sequence, TypeAlias

from jinja2 import Environment, PackageLoader, Template, select_autoescape

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
#     2023: {
#         1: [
#            [0, 0, 0, 0, 0, 0, 1],
#            [2, 3, 4, 5, 6, 7, 8],
#            ...
#         },
#         ...
#     }
# }
DatesByYearMonthWeek: TypeAlias = dict[int, dict[int, list[list[datetime.date]]]]

# Example:
# {
#     2023: {
#         11: [
#             {"git": 13, "csv: 10"}, # first week
#             {"git": 1, "csv: 90"}, # second week
#             ...
#         ],
#         ...
#     }
# }
ProviderStats: TypeAlias = dict[int, dict[int, list[dict[str, int]]]]


def read_items(rows: Iterable[list[str]]) -> ItemsByYearMonthDay:
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
    res: ItemsByYearMonthDay = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for row in rows:
        item = Item.from_tuple(row)
        res[item.date.year][item.date.month][item.date.day].append(item)
    return res


def gen_dates(items_by_year_month_day: ItemsByYearMonthDay) -> DatesByYearMonthWeek:
    """Generate a calendar structure for passed items.

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
    calendar = Calendar()
    return {
        year: {
            month: calendar.monthdatescalendar(year, month) for month in range(1, 13)
        }
        for year in items_by_year_month_day.keys()
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
    dates_by_year_month_week: DatesByYearMonthWeek,
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
        2023: {
            11: [
                {"git": 10, "csv": 7},
                {"git": 7, "csv": 7},
                {"git": 4, "csv": 1},
                {"git": 1, "csv": 10},
            ]
        }
    }
    """
    # Dictionary in format:
    # {
    #     2023: {
    #         11: [
    #             {"git": 150, "csv": 70},
    #             {"git": 145, "csv": 30},
    #             {"git": 120, "csv": 10},
    #             {"git": 100, "csv": 90},
    #             ...
    #         ]
    #     }
    # }
    item_count_by_year_month_week_provider: dict[
        int, dict[int, list[dict[str, int]]]
    ] = defaultdict(lambda: defaultdict(list))

    # Dictionary in format:
    # {
    #     "git": [150, 145, 120, 110],
    #     "csv": [70, 30, 10, 90],
    # }
    item_counts_by_provider: dict[str, list[int]] = defaultdict(list)

    for year, months in dates_by_year_month_week.items():
        for month, weeks in months.items():
            for week in weeks:
                week_item_count_by_provider: dict[str, int] = defaultdict(int)
                for date in week:
                    items = items_by_year_month_day[year][month][date.day]
                    for item in items:
                        week_item_count_by_provider[item.provider] += 1
                for provider, item_count in week_item_count_by_provider.items():
                    item_counts_by_provider[provider].append(item_count)
                item_count_by_year_month_week_provider[year][month].append(
                    week_item_count_by_provider
                )

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
    #     2023: {
    #         11: [
    #             {"git": 10, "csv": 7},
    #             {"git": 7, "csv": 7},
    #             {"git": 4, "csv": 1},
    #             {"git": 1, "csv": 10},
    #         ]
    #     }
    # }
    return {
        year: {
            month: [
                {
                    provider: quantile_rank(item_count, deciles_by_provider[provider])
                    for provider, item_count in item_count_by_provider.items()
                }
                for item_count_by_provider in weeks
            ]
            for month, weeks in months.items()
        }
        for year, months in item_count_by_year_month_week_provider.items()
    }


def _is_regex(s: str, regex: str) -> bool:
    if not regex:
        return False
    return re.search(regex, s) is not None


def _render_template(
    template: Template,
    path: Path,
    *,
    dates_by_year_month_week: DatesByYearMonthWeek,
    items_by_year_month_day: ItemsByYearMonthDay,
    provider_stats: ProviderStats,
    today: datetime.date,
    year: int,
) -> None:
    stream = template.stream(
        {
            "dates_by_month_week": dates_by_year_month_week[year],
            "items_by_month_day": items_by_year_month_day[year],
            "provider_stats": provider_stats[year],
            "today": today,
            "year": year,
        }
    )
    with path.open("w") as f:
        f.writelines(stream)


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize Automatic Diary CSV")
    parser.add_argument("csv_path", help="Input CSV file path")
    parser.add_argument("output_path", help="Output file or directory path")
    parser.add_argument(
        "-a",
        "--all-years",
        action="store_true",
        help="Visualize all years, write them in the directory OUTPUT_PATH; "
        "by default only the last year is visualized and written to the file OUTPUT_PATH",
    )
    parser.add_argument("-i", "--highlight", help="Highlight items matching regex")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debugging output"
    )
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    items_by_year_month_day: ItemsByYearMonthDay = {}
    with open(args.csv_path) as f:
        reader = csv.reader(f)
        items_by_year_month_day = read_items(reader)
    dates_by_year_month_week: DatesByYearMonthWeek = gen_dates(items_by_year_month_day)
    provider_stats = calc_provider_stats(
        dates_by_year_month_week, items_by_year_month_day
    )
    today = datetime.date.today()

    environment = Environment(
        autoescape=select_autoescape(["html"]),
        loader=PackageLoader("automatic_diary", "templates"),
    )
    environment.tests["regex"] = _is_regex
    template = environment.get_template("template.html")

    if args.all_years:
        output_dir_path = Path(args.output_path)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        for year in items_by_year_month_day:
            _render_template(
                template,
                (output_dir_path / f"{year}.html"),
                dates_by_year_month_week=dates_by_year_month_week,
                items_by_year_month_day=items_by_year_month_day,
                provider_stats=provider_stats,
                today=today,
                year=year,
            )
    else:
        output_file_path = Path(args.output_path)
        year = sorted(list(items_by_year_month_day.keys()))[-1]
        _render_template(
            template,
            output_file_path,
            dates_by_year_month_week=dates_by_year_month_week,
            items_by_year_month_day=items_by_year_month_day,
            provider_stats=provider_stats,
            today=today,
            year=year,
        )


if __name__ == "__main__":
    main()
