import contextlib
import io
import json
import unittest
from pathlib import Path

from docdiff_ai.cli import main

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [str(ROOT / "examples" / "proposal_a.md"), str(ROOT / "examples" / "proposal_b.md")]


class CLITests(unittest.TestCase):
    def test_markdown_report(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(EXAMPLES)
        self.assertEqual(exit_code, 0)
        self.assertIn("Divergentes", stdout.getvalue())
        self.assertIn("Concordam", stdout.getvalue())

    def test_json_report(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = main(EXAMPLES + ["--format", "json"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["fields"][0]["status"], "different")

    def test_missing_file_fails(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = main(["missing.md", *EXAMPLES])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
