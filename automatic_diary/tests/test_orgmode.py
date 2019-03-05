import datetime
import io
from unittest import TestCase

from automatic_diary.common import Item
from automatic_diary.providers.orgmode.main import parse_orgmode


class TestOrgmode(TestCase):
    def test_parse_orgmode(self):
        f = io.StringIO(
            '''#+STARTUP: showall

* <2019-01-17 Thu>

foo
bar


two empty lines are okay

* <2019-01-18 Fri>
missing empty line is okay

* <2019-01-19 Sat>

something

something else
- with
- a
- list
'''
        )
        subprovider = 'my_provider'
        result = list(parse_orgmode(f, subprovider))
        expected = [
            Item(
                dt=datetime.date(2019, 1, 17),
                text='''foo\nbar''',
                provider='orgmode',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 17),
                text='two empty lines are okay',
                provider='orgmode',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 18),
                text='''missing empty line is okay''',
                provider='orgmode',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 19),
                text='something',
                provider='orgmode',
                subprovider=subprovider,
            ),
            Item(
                dt=datetime.date(2019, 1, 19),
                text='something else\n- with\n- a\n- list',
                provider='orgmode',
                subprovider=subprovider,
            ),
        ]
        self.assertListEqual(result, expected)
