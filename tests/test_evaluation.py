import json
import unittest
from pathlib import Path

from scripts.evaluate_extraction import evaluate_dataset

DATASET = Path(__file__).resolve().parents[1] / "evaluation" / "dataset_v1.json"


class EvaluationTests(unittest.TestCase):
    def test_baseline_metrics_are_calculated_not_hardcoded(self):
        dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        result = evaluate_dataset(dataset)
        self.assertEqual(result["mode"], "rules")
        self.assertEqual(result["case_count"], len(dataset["cases"]))
        self.assertEqual(result["true_positives"] + result["false_negatives"], 4 + 4 + 4 + 0 + 0 + 2 + 3)
        self.assertGreater(result["false_negatives"], 0)
        self.assertIsNone(result["cost_usd"])
        self.assertIsNone(result["model"])

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_dataset({"cases": []}, mode="unknown")


if __name__ == "__main__":
    unittest.main()
