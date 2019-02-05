import datetime
from unittest import TestCase

import dateutil.tz

from automatic_journal.providers.facebook.main import parse_date_time


class TestFacebook(TestCase):
    def test_parse_date_time(self):
        result = parse_date_time(
            'Wednesday, December 31, 2014 at 4:17am UTC+01'
        )
        expected = datetime.datetime(
            2014, 12, 31, 4, 17, tzinfo=dateutil.tz.gettz('Europe/Prague')
        )
        self.assertEqual(result, expected)
