import datetime
import tempfile
from unittest import TestCase

from PyOrgMode import PyOrgMode

from automatic_diary.model import Item
from automatic_diary.providers.orgmodelist.main import parse_orgmode_list


def create_org(content: bytes):
    with tempfile.NamedTemporaryFile() as f:
        f.write(content)
        f.flush()
        org = PyOrgMode.OrgDataStructure()
        org.load_from_file(f.name)
    return org


class TestOrgmode(TestCase):
    def test_parse_orgmode_list(self):
        org = create_org(
            b'''#+STARTUP: showall

- Lorem ipsum foo. <2019-01-17 Thu>
- bar <2019-01-18 Fri 11:30>
- spam [2021-05-13 Thu]
'''
        )
        subprovider = 'my_provider'
        result = list(parse_orgmode_list(org, subprovider))
        expected = [
            Item.normalized(
                datetime_=datetime.datetime(2019, 1, 17),
                text='Lorem ipsum foo.',
                provider='orgmodelist',
                subprovider=subprovider,
                all_day=True,
            ),
            Item.normalized(
                datetime_=datetime.datetime(2019, 1, 18, 11, 30),
                text='bar',
                provider='orgmodelist',
                subprovider=subprovider,
                all_day=False,
            ),
            Item.normalized(
                datetime_=datetime.datetime(2021, 5, 13),
                text='spam',
                provider='orgmodelist',
                subprovider=subprovider,
                all_day=True,
            ),
        ]
        self.assertListEqual(result, expected)
