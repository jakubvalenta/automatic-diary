from unittest import TestCase
from unittest.mock import patch

from automatic_diary.shell import search_secret

MOCK_RUN_CMD_OUTPUT = '''
[/org/freedesktop/secrets/collection/Default_5fkeyring/217]
label = first label
secret = first secret
created = 2019-11-05 18:39:09
modified = 2019-11-05 19:07:18
schema = org.gnome.Evolution.Data.Source
attribute.e-source-uid = fc44e5053704c83d36ed7e41302a19519b38da20
attribute.eds-origin = evolution-data-server
[/org/freedesktop/secrets/collection/Default_5fkeyring/115]
label = second label
secret = second secret
created = 2018-11-14 20:36:22
modified = 2018-11-14 20:36:22
schema = org.gnome.Evolution.Data.Source
attribute.e-source-uid = 4d5f76dbe1c64d1d374920fd723be84bd254a2fb
attribute.eds-origin = evolution-data-server
'''


class TestShell(TestCase):
    @patch(
        'automatic_diary.shell.run_shell_cmd', return_value=MOCK_RUN_CMD_OUTPUT
    )
    def test_search_secret(self, mock_method):
        self.assertEqual(
            search_secret(key='foo', val='bar', label='first label'),
            'first secret',
        )
        self.assertEqual(
            search_secret(key='foo', val='bar', label='second label'),
            'second secret',
        )
        self.assertIsNone(
            search_secret(key='foo', val='bar', label='nonexistent label')
        )
