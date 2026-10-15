import unittest

from docdiff_ai.core import SourceDocument, compare, extract_evidence, report_to_markdown


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.a = SourceDocument(
            "a.md", "Valor total: R$ 12.500,00\nPrazo de entrega: 30 dias\nGarantia: 12 meses"
        )
        self.b = SourceDocument(
            "b.md", "Valor total: R$ 13.000,00\nPrazo de entrega: 45 dias\nGarantia: 12 meses"
        )

    def test_grounded_differences(self):
        report = compare([self.a, self.b])
        self.assertEqual(
            [row.status for row in report.fields], ["different", "different", "match", "missing"]
        )
        hit = report.fields[0].evidence["a.md"][0]
        self.assertEqual(hit.normalized, "BRL:12500.00")
        self.assertEqual(hit.line, 1)
        self.assertIn("12.500,00", hit.excerpt)

    def test_locale_normalization(self):
        a = SourceDocument("a", "Valor total: R$ 1.250,00")
        b = SourceDocument("b", "Valor total: BRL 1250.00")
        self.assertEqual(compare([a, b]).fields[0].status, "match")

    def test_different_currencies(self):
        a = SourceDocument("a", "Valor total: R$ 100")
        b = SourceDocument("b", "Valor total: $100")
        self.assertEqual(compare([a, b]).fields[0].status, "different")

    def test_multiple_values_in_single_document(self):
        a = SourceDocument("a", "Garantia: 12 meses\nGarantia: 24 meses")
        b = SourceDocument("b", "Garantia: 12 meses")
        self.assertEqual(compare([a, b]).fields[2].status, "ambiguous")

    def test_missing_is_not_invented(self):
        a = SourceDocument("a", "A entrega será combinada.")
        b = SourceDocument("b", "Prazo de entrega: 30 dias")
        self.assertEqual(compare([a, b]).fields[1].status, "missing")
        self.assertEqual(extract_evidence(a)["delivery_days"], [])

    def test_duplicate_names_rejected(self):
        with self.assertRaises(ValueError):
            compare([self.a, self.a])

    def test_too_few_rejected(self):
        with self.assertRaises(ValueError):
            compare([self.a])

    def test_unknown_field_rejected(self):
        with self.assertRaises(ValueError):
            extract_evidence(self.a, ("other",))

    def test_markdown_has_evidence(self):
        report = report_to_markdown(compare([self.a, self.b]))
        self.assertIn("linha 1", report)
        self.assertIn("12.500,00", report)


if __name__ == "__main__":
    unittest.main()
