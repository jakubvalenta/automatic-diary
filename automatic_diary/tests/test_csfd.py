from unittest import TestCase

from ddt import data, ddt, unpack

from automatic_diary.providers.csfd.main import parse_username


@ddt
class TestCSFD(TestCase):
    @data(
        ('https://www.csfd.cz/uzivatel/1234-foobar/', 'foobar'),
        ('https://www.csfd.cz/uzivatel/1234-123-foo-bar/', '123-foo-bar'),
    )
    @unpack
    def test_parse_date_time(self, url, expected):
        result = parse_username(url)
        self.assertEqual(result, expected)
