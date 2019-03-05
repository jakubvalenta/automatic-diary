from unittest import TestCase
from unittest.mock import patch

from automatic_diary.cli import obfuscate


class TestCLI(TestCase):
    @patch('automatic_diary.cli._obfuscate_uppercase', return_value='X')
    @patch('automatic_diary.cli._obfuscate_lowercase', return_value='y')
    def test_parse_date_time(self, url, expected):
        result = obfuscate('Ve škole domluveno tisknutí v 10 s Mirkem, ale.')
        expected = 'Xy šyyyy yyyyyyyyy yyyyyyyí y 10 y Xyyyyy, yyy.'
        self.assertEqual(result, expected)
