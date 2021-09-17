import datetime
from pathlib import Path
from unittest import TestCase

import dateutil.tz

from automatic_diary.providers.icalendar.main import Event, parse_calendar


class TestICalendar(TestCase):
    maxDiff = None

    def test_parse_calendar(self):
        path = Path(__file__).parent / 'test_data' / 'calendar.ics'
        with path.open() as f:
            result = list(parse_calendar(f.readlines()))
            self.assertEqual(len(result), 3)

            self.assertEqual(result[0]._name, 'Foo bar')
            self.assertIsNone(result[0]._location)
            self.assertEqual(
                result[0].begin.isoformat(), '2011-11-30T00:00:00'
            )
            self.assertTrue(result[0].all_day)

            self.assertEqual(result[1]._name, 'Vylet')
            self.assertIsNone(result[1]._location)
            self.assertEqual(
                result[1].begin.isoformat(), '2015-12-29T10:00:00+01:00'
            )
            self.assertFalse(result[1].all_day)

            self.assertEqual(result[2]._name, 'Predstaveni')
            self.assertEqual(result[2]._location, 'Divadlo, Ulice 10')
            self.assertEqual(
                result[2].begin.isoformat(), '2015-12-28T11:00:00+01:00'
            )
            self.assertFalse(result[2].all_day)
