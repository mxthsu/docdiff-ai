import unittest

from docdiff_ai.core import SourceDocument, compare, extract_evidence, report_to_markdown


class ProvenanceTests(unittest.TestCase):
    def test_text_file_reference_uses_original_line(self):
        document = SourceDocument("a.md", "Warranty: 12 months")
        evidence = extract_evidence(document)["warranty_months"][0]
        self.assertEqual(evidence.reference_type, "text_line")

    def test_converted_document_reference_is_explicit(self):
        converted = SourceDocument("a.pdf", "Warranty: 12 months", "converted_markdown_line")
        baseline = SourceDocument("b.md", "Warranty: 12 months")
        result = compare([converted, baseline])
        evidence = result.fields[2].evidence["a.pdf"][0]
        self.assertEqual(evidence.reference_type, "converted_markdown_line")
        self.assertEqual(
            result.to_dict()["fields"][2]["evidence"]["a.pdf"][0]["reference_type"], "converted_markdown_line"
        )
        report = report_to_markdown(result)
        self.assertIn("linha do Markdown convertido 1", report)


if __name__ == "__main__":
    unittest.main()
