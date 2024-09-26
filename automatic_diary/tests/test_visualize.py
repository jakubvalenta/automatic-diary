import datetime

from automatic_diary.model import Item, default_tz
from automatic_diary.visualize import calc_provider_stats, gen_dates, read_items


def test_read_items():
    assert read_items(
        [
            ["2024-09-24T23:11:53.589437", "git", "my-project", "Initial commit"],
            ["2024-09-24T23:12:03.861082", "git", "my-project", "Add more files"],
        ]
    ) == {
        2024: {
            9: {
                24: [
                    Item(
                        datetime.datetime.fromisoformat(
                            "2024-09-24T23:11:53.589437"
                        ).replace(tzinfo=default_tz),
                        "Initial commit",
                        "git",
                        "my-project",
                    ),
                    Item(
                        datetime.datetime.fromisoformat(
                            "2024-09-24T23:12:03.861082"
                        ).replace(tzinfo=default_tz),
                        "Add more files",
                        "git",
                        "my-project",
                    ),
                ]
            }
        }
    }


def test_gen_dates():
    res = gen_dates({2023: {11: {1: []}}, 2024: {9: {24: []}}})
    assert set(res.keys()) == {2023, 2024}
    assert res[2024][0] == [
        datetime.date(2024, 1, 1),
        datetime.date(2024, 1, 2),
        datetime.date(2024, 1, 3),
        datetime.date(2024, 1, 4),
        datetime.date(2024, 1, 5),
        datetime.date(2024, 1, 6),
        datetime.date(2024, 1, 7),
    ]
    assert res[2024][4] == [
        datetime.date(2024, 1, 29),
        datetime.date(2024, 1, 30),
        datetime.date(2024, 1, 31),
        datetime.date(2024, 2, 1),
        datetime.date(2024, 2, 2),
        datetime.date(2024, 2, 3),
        datetime.date(2024, 2, 4),
    ]
    assert res[2024][-1] == [
        datetime.date(2024, 12, 30),
        datetime.date(2024, 12, 31),
        datetime.date(2025, 1, 1),
        datetime.date(2025, 1, 2),
        datetime.date(2025, 1, 3),
        datetime.date(2025, 1, 4),
        datetime.date(2025, 1, 5),
    ]


def test_calc_provider_stats():
    items_by_year_month_day = read_items(
        [
            ["2024-08-10T00:16:45.098644", "csv", "", "First line"],
            ["2024-09-24T23:11:53.589437", "git", "my-project", "Initial commit"],
            ["2024-09-24T23:12:03.861082", "git", "my-project", "Add more files"],
            ["2024-09-25T00:16:47.879263", "csv", "", "Second line"],
            ["2024-09-25T00:17:07.080366", "csv", "", "Third line"],
        ]
    )
    dates_by_year_month_week = gen_dates(items_by_year_month_day)
    assert calc_provider_stats(dates_by_year_month_week, items_by_year_month_day) == {
        2024: [
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {"csv": 1},
            {},
            {},
            {},
            {},
            {},
            {},
            {"git": 10, "csv": 10},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ]
    }
