import datetime
from unittest import TestCase

import dateutil.tz
from ddt import data, ddt, unpack

from automatic_diary.providers.facebook.main import parse_datetime


@ddt
class TestFacebook(TestCase):
    @data(
        (
            'Wednesday, December 31, 2014 at 4:17am UTC+01',
            datetime.datetime(
                2014, 12, 31, 4, 17, tzinfo=dateutil.tz.gettz('Europe/Prague')
            ),
        ),
        (
            'Dienstag, 30. Januar 2018 um 13:05 UTC+01',
            datetime.datetime(
                2018, 1, 30, 13, 5, tzinfo=dateutil.tz.gettz('Europe/Berlin')
            ),
        ),
    )
    @unpack
    def test_parse_datetime(self, s, expected):
        result = parse_datetime(s)
        self.assertEqual(result, expected)
