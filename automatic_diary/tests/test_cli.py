import unicodedata
from unittest import TestCase

from automatic_diary.cli import obfuscate


class TestCLI(TestCase):
    def test_obfuscate(self):
        source = "Ve škole, 10"
        result = obfuscate(source)
        self.assertNotEqual(source, result)
        self.assertEqual(len(source), len(result))
        for source_char, result_char in zip(source, result):
            self.assertEqual(
                unicodedata.category(source_char),
                unicodedata.category(result_char),
            )
