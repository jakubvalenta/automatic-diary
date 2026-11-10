import io
import sys
import unicodedata
from contextlib import redirect_stderr
from unittest import TestCase
from unittest.mock import patch

from automatic_diary import cli as cli_module
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

    def test_missing_config_file_is_usage_error(self):
        # A missing config file should be a usage error (exit 2),
        # not an unhandled FileNotFoundError traceback.
        err = io.StringIO()
        argv = ["automatic-diary", "missing.json", "out.csv"]
        with redirect_stderr(err), patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit) as ctx:
                cli_module.main()
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("missing.json", err.getvalue())
