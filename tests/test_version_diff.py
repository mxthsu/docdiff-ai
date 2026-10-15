import unittest

from docdiff_ai.core import SourceDocument
from docdiff_ai.version_diff import compare_versions, review_to_markdown, split_passages


class VersionReviewTests(unittest.TestCase):
    def setUp(self):
        self.old = SourceDocument(
            "before.md",
            "# Agreement\n\n## Payment\nPayment is due within 30 days.\n\n"
            "## Termination\nEither party may end the agreement with 60 days notice.\n\n"
            "## Secret\nThe business data must remain confidential.\n\n"
            "## Objective\nWe provide support services.",
        )
        self.new = SourceDocument(
            "after.md",
            "# Agreement\n\n## Payment\nPayment is due within 45 days.\n\n"
            "## Termination\nEither party may end the agreement with 90 days notice.\n\n"
            "## Data use\nOnly authorized staff may access personal data.\n\n"
            "## Objective\nWe provide support services.",
        )

    def test_modified_added_removed_and_unchanged_with_anchors(self):
        report = compare_versions(self.old, self.new)
        self.assertEqual(report.counts, {"modified": 2, "added": 1, "removed": 1, "unchanged": 1})
        payment = next(c for c in report.changes if c.after and c.after.heading == "Payment")
        self.assertEqual(payment.status, "modified")
        self.assertTrue(payment.numbers_changed)
        self.assertEqual(payment.before.start_line, 4)
        self.assertEqual(payment.after.start_line, 4)
        self.assertEqual(payment.matched_by, "same_heading")
        self.assertEqual(payment.before.text, "Payment is due within 30 days.")
        self.assertEqual(payment.after.text, "Payment is due within 45 days.")
        self.assertIn("before_name", report.to_dict())

    def test_reordered_identical_passages_are_unchanged(self):
        left = SourceDocument("old", "A simple first passage.\n\nAnother passage here.")
        right = SourceDocument("new", "Another passage here.\n\nA simple first passage.")
        report = compare_versions(left, right)
        self.assertEqual(report.counts["unchanged"], 2)
        self.assertEqual(report.counts["modified"], 0)

    def test_duplicate_repeated_passages_align_one_to_one(self):
        left = SourceDocument("old", "This text repeats here.\n\nThis text repeats here.")
        right = SourceDocument("new", "This text repeats here.")
        report = compare_versions(left, right)
        self.assertEqual(report.counts["unchanged"], 1)
        self.assertEqual(report.counts["removed"], 1)

    def test_numbered_clauses_have_line_locations(self):
        doc = SourceDocument("numbered", "1. Scope of work\n2. Payment within 30 days")
        clauses = split_passages(doc)
        self.assertEqual(len(clauses), 2)
        self.assertEqual([c.start_line for c in clauses], [1, 2])
        self.assertEqual([c.heading for c in clauses], ["Cláusula 1", "Cláusula 2"])

    def test_numbered_clause_differences_align_by_heading(self):
        left = SourceDocument("a", "1. Services are provided each weekday.")
        right = SourceDocument("b", "1. No services will be provided on weekdays.")
        report = compare_versions(left, right)
        self.assertEqual(report.counts["modified"], 1)

    def test_no_semantic_equivalence_claims_for_paraphrase(self):
        left = SourceDocument("a", "You must deliver within seven days.")
        right = SourceDocument("b", "Delivery shall occur no later than one week.")
        report = compare_versions(left, right)
        self.assertEqual(report.counts["unchanged"], 0)
        self.assertIn("not semantic equivalence", report.caveat)

    def test_converted_markdown_line_is_not_claimed_as_pdf_page(self):
        left = SourceDocument("old.pdf", "## Payment\n30 days are allowed.", "converted_markdown_line")
        right = SourceDocument("new.pdf", "## Payment\n45 days are allowed.", "converted_markdown_line")
        result = compare_versions(left, right)
        rendered = review_to_markdown(result)
        self.assertIn("Markdown convertido", rendered)
        self.assertNotIn("página do PDF", rendered)

    def test_too_long_or_empty_documents_fail_explicitly(self):
        with self.assertRaises(ValueError):
            split_passages(SourceDocument("too-long", "x" * 150_001))
        with self.assertRaises(ValueError):
            split_passages(SourceDocument("empty", "  \n  "))

    def test_same_document_name_is_rejected(self):
        with self.assertRaises(ValueError):
            compare_versions(self.old, self.old)

    def test_output_includes_both_exact_quotes(self):
        result = compare_versions(self.old, self.new)
        md = review_to_markdown(result)
        self.assertIn("Payment is due within 30 days.", md)
        self.assertIn("Payment is due within 45 days.", md)
        self.assertIn("linhas 4", md)

    def test_lexical_similarity_is_labelled_as_such(self):
        a = SourceDocument("a", "The deliverables are to be sent by email before 30 days.")
        b = SourceDocument("b", "The deliverables are to be sent by email before 45 days.")
        report = compare_versions(a, b)
        self.assertEqual(report.counts["modified"], 1)
        self.assertEqual(report.changes[0].matched_by, "lexical_similarity")


if __name__ == "__main__":
    unittest.main()
