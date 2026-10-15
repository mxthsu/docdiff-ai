import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_llm_extraction_mode_with_stub_never_calls_network(self):
        from docdiff_ai.verified_extraction import VerifiedLLMExtractor

        def make_stub():
            return VerifiedLLMExtractor(lambda _payload: json.dumps({"candidates": []}))

        stdout = io.StringIO()
        with patch("docdiff_ai.cli.VerifiedLLMExtractor", make_stub), contextlib.redirect_stdout(stdout):
            code = main(EXAMPLES + ["--extraction", "llm", "--format", "json"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["extraction"]["mode"], "llm")
        self.assertEqual(payload["fields"][0]["status"], "missing")
        self.assertEqual(payload["extraction"]["rejected_candidate_count"], 0)

    def test_review_versions_cli_reports_changes_in_json(self):
        files = [
            str(ROOT / "examples" / "agreement_before.md"),
            str(ROOT / "examples" / "agreement_after.md"),
        ]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(files + ["--review-versions", "--format", "json"])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["counts"]["modified"], 2)
        self.assertEqual(report["counts"]["added"], 1)
        self.assertEqual(report["counts"]["removed"], 1)
        self.assertIn("offline_lexical_alignment", report["method"])

    def test_review_rejects_ambiguous_options_and_wrong_party_size(self):
        files = [
            str(ROOT / "examples" / "agreement_before.md"),
            str(ROOT / "examples" / "agreement_after.md"),
        ]
        for args in (
            files[:1] + ["--review-versions"],
            files + ["--review-versions", "--ai-summary"],
            files + ["--review-versions", "--extraction", "llm"],
        ):
            error = io.StringIO()
            with self.subTest(args=args), contextlib.redirect_stderr(error):
                self.assertEqual(main(args), 2)
            self.assertIn("Erro", error.getvalue())

    def test_missing_file_fails(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = main(["missing.md", *EXAMPLES])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
