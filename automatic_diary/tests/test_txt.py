import datetime
import io
from unittest import TestCase

from automatic_diary.common import Item
from automatic_diary.providers.txt.main import parse_txt


class TestTxt(TestCase):
    def test_parse_txt(self):
        f = io.StringIO(
            '''2019-01-17 Čt
    foo
    bar
        baz baz
2019-01-18 Pá
2019-01-19
    one
        two
            foo
            three
                four
                bar
            baz
        spam
    lorem
'''
        )
        subprovider = 'my_provider'
        result = list(parse_txt(f, subprovider))
        expected = [
            Item(
                dt=datetime.date(2019, 1, 17),
                text='''foo''',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 17),
                text='''bar: baz baz''',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 19),
                text='one: two: foo',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 19),
                text='one: two: three four bar',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 19),
                text='one: two: baz',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 19),
                text='one: spam',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 19),
                text='lorem',
                subprovider=subprovider,
            ),
        ]
        self.assertListEqual(result, expected)
