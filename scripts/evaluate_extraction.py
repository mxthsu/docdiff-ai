"""Small reproducible evaluator for local rules or explicitly enabled LLM calls.

Does not claim model quality unless an actual model is executed. Cases are
synthetic and metrics are exact normalized-value field matches, not semantics.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from docdiff_ai.core import FIELDS, SourceDocument, extract_evidence
from docdiff_ai.verified_extraction import PROMPT_VERSION, extract_with_llm

DATASET = Path(__file__).resolve().parents[1] / "evaluation" / "dataset_v1.json"


def evaluate_dataset(dataset: dict[str, Any], *, mode: str = "rules") -> dict[str, Any]:
    if mode not in {"rules", "llm"}:
        raise ValueError("mode deve ser 'rules' ou 'llm'")
    tp = fp = fn = 0
    rejected = 0
    cases = []
    start = time.perf_counter()
    for item in dataset["cases"]:
        source = SourceDocument(f"{item['id']}.txt", item["text"])
        if mode == "rules":
            evidence = extract_evidence(source)
        else:
            result = extract_with_llm(source)
            evidence = result.evidence
            rejected += len(result.rejected)
        passed = True
        for field in FIELDS:
            expected = set(item["expected"][field])
            actual = {hit.normalized for hit in evidence[field]}
            tp += len(expected & actual)
            fp += len(actual - expected)
            fn += len(expected - actual)
            passed &= expected == actual
        cases.append({"id": item["id"], "exact_match": passed})
    duration = round(time.perf_counter() - start, 3)
    return {
        "dataset_version": dataset["version"],
        "prompt_version": PROMPT_VERSION if mode == "llm" else None,
        "mode": mode,
        "model": os.getenv("DOCDIFF_MODEL") if mode == "llm" else None,
        "case_count": len(cases),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(tp / (tp + fp), 4) if tp + fp else None,
        "recall": round(tp / (tp + fn), 4) if tp + fn else None,
        "exact_case_matches": sum(case["exact_match"] for case in cases),
        "rejected_llm_candidates": rejected if mode == "llm" else None,
        "elapsed_wall_seconds": duration,
        "cost_usd": None,
        "cost_note": "Provider pricing and token billing were not independently measured.",
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate field-level extraction on synthetic fixtures.")
    parser.add_argument("--mode", choices=["rules", "llm"], default="rules")
    parser.add_argument("--allow-external", action="store_true", help="Explicit permission to call an LLM.")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "llm" and not args.allow_external:
        parser.error("--mode llm requires --allow-external (sends document text to provider).")
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    report = evaluate_dataset(dataset, mode=args.mode)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Evaluation saved: {args.output}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
