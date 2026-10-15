import json
import unittest
from pathlib import Path

from scripts.evaluate_semantic import _offline_baseline, evaluate

DATASET = Path(__file__).resolve().parents[1] / "evaluation" / "semantic_pairs_v1.json"


class SemanticEvaluationTests(unittest.TestCase):
    def test_baseline_result_is_reproducible(self):
        data = json.loads(DATASET.read_text(encoding="utf-8"))
        result = evaluate(data)
        self.assertEqual(result["case_count"], 9)
        self.assertEqual(result["counts"]["attempted"], 8)
        self.assertEqual(result["counts"]["skipped_unchanged"], 1)
        self.assertEqual(result["counts"]["exact_pair_correct"], 6)
        self.assertEqual(result["exact_pair_accuracy_on_attempted"], 0.75)
        self.assertEqual(result["mode"], "baseline")
        self.assertIsNone(result["model"])
        self.assertIsNone(result["cost_usd"])

    def test_offline_baseline_cannot_claim_paraphrase(self):
        prediction = _offline_baseline(
            "The goods will arrive promptly after dispatch.",
            "Delivery of the goods will happen soon after dispatch.",
        )
        self.assertEqual(prediction, {"interpretation": "unclear", "category": "other"})

    def test_invalid_mode_fails(self):
        with self.assertRaises(ValueError):
            evaluate({"cases": []}, mode="magic")


if __name__ == "__main__":
    unittest.main()
