import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from docdiff_ai.documents import DocumentReadError, from_bytes, from_path


class DocumentTests(unittest.TestCase):
    def test_local_markdown(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "proposal.md"
            path.write_text("Valor total: R$ 42", encoding="utf-8")
            self.assertIn("R$ 42", from_path(path).text)

    def test_uploaded_filename_sanitized(self):
        self.assertEqual(from_bytes("../../proposal.md", b"Some text").name, "proposal.md")

    def test_unsupported_extension(self):
        with self.assertRaises(DocumentReadError):
            from_bytes("program.exe", b"data")

    def test_size_limit(self):
        with self.assertRaises(DocumentReadError):
            from_bytes("test.md", b"a" * (10 * 1024 * 1024 + 1))

    def test_invalid_utf8(self):
        with self.assertRaises(DocumentReadError):
            from_bytes("test.md", b"\xff")

    def test_missing_input(self):
        with self.assertRaises(DocumentReadError):
            from_path(Path("this-file-is-not-here.md"))


if __name__ == "__main__":
    unittest.main()
