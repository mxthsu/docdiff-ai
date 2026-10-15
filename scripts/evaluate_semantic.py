"""Evaluate a cautious offline signal baseline or a deliberately opted-in LLM.

This synthetic dataset is *not* a real-world accuracy benchmark.
Model calls require --mode llm --allow-external.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from docdiff_ai.core import SourceDocument
from docdiff_ai.semantic_review import SemanticReviewError, interpret_change
from docdiff_ai.version_diff import compare_versions

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evaluation" / "semantic_pairs_v1.json"
DIGITS = re.compile(r"\d+(?:[.,]\d+)*")
NEGATION = re.compile(r"(?i)\b(?:not|never|no|without|não|jamais)\b")
EXCEPTION = re.compile(r"(?i)\b(?:except|unless|excluding|salvo|exceto)\b")
OBLIGATION = re.compile(r"(?i)\b(?:must|shall|may|should|deverá|poderá)\b")
MONEY = re.compile(r"(?i)(?:USD|EUR|BRL|R\$|\$)\s*\d+")


def _offline_baseline(before: str, after: str) -> dict[str, str]:
    # Deliberately conservative baseline, not deep semantic understanding.
    if NEGATION.findall(before) != NEGATION.findall(after):
        return {"interpretation": "possible_change", "category": "negation"}
    if EXCEPTION.findall(before) != EXCEPTION.findall(after):
        return {"interpretation": "possible_change", "category": "exception"}
    if MONEY.findall(before) != MONEY.findall(after):
        return {"interpretation": "possible_change", "category": "amount"}
    if DIGITS.findall(before) != DIGITS.findall(after):
        return {"interpretation": "possible_change", "category": "deadline"}
    if OBLIGATION.findall(before) != OBLIGATION.findall(after):
        return {"interpretation": "possible_change", "category": "obligation"}
    return {"interpretation": "unclear", "category": "other"}


def evaluate(dataset: dict[str, Any], *, mode: str = "baseline") -> dict[str, Any]:
    if mode not in {"baseline", "llm"}:
        raise ValueError("Unknown evaluation mode")
    results: list[dict[str, Any]] = []
    all_input_tokens = all_output_tokens = 0
    usage_available = True
    total_latency = 0.0
    latency_available = True
    total_cost_usd = 0.0
    cost_available = True
    counts = {"attempted": 0, "exact_pair_correct": 0, "abstained": 0, "rejected": 0, "skipped_unchanged": 0}

    for fixture in dataset["cases"]:
        before = SourceDocument(f"{fixture['id']}_before.md", "## Terms\n" + fixture["before"])
        after = SourceDocument(f"{fixture['id']}_after.md", "## Terms\n" + fixture["after"])
        comparison = compare_versions(before, after)
        changes = [change for change in comparison.changes if change.status == "modified"]
        if not changes:
            counts["skipped_unchanged"] += 1
            results.append({"id": fixture["id"], "status": "skipped_no_modified_pair"})
            continue
        change = changes[0]
        counts["attempted"] += 1
        if mode == "baseline":
            predicted = _offline_baseline(change.before.text, change.after.text)
            status = "signal_only"
        else:
            try:
                result = interpret_change(change)
                if result.assessment is not None:
                    predicted = {
                        "interpretation": result.assessment.interpretation,
                        "category": result.assessment.category,
                    }
                    status = "verified_quotes"
                else:
                    predicted = None
                    status = "abstained"
                    counts["abstained"] += 1
                if result.input_tokens is None or result.output_tokens is None:
                    usage_available = False
                else:
                    all_input_tokens += result.input_tokens
                    all_output_tokens += result.output_tokens
                if result.cost_usd is None:
                    cost_available = False
                else:
                    total_cost_usd += result.cost_usd
                if result.latency_seconds is None:
                    latency_available = False
                else:
                    total_latency += result.latency_seconds
            except SemanticReviewError:
                predicted = None
                status = "rejected"
                counts["rejected"] += 1
                usage_available = False
                latency_available = False
                cost_available = False
        correct = predicted == fixture["expected"]
        counts["exact_pair_correct"] += int(correct)
        results.append(
            {
                "id": fixture["id"],
                "status": status,
                "expected": fixture["expected"],
                "predicted": predicted,
                "exact_pair_correct": correct,
            }
        )
    attempted = counts["attempted"]
    return {
        "dataset_version": dataset["version"],
        "mode": mode,
        "model": os.getenv("DOCDIFF_MODEL") if mode == "llm" else None,
        "case_count": len(dataset["cases"]),
        "counts": counts,
        "exact_pair_accuracy_on_attempted": round(counts["exact_pair_correct"] / attempted, 4)
        if attempted
        else None,
        "input_tokens_reported": all_input_tokens if mode == "llm" and usage_available else None,
        "output_tokens_reported": all_output_tokens if mode == "llm" and usage_available else None,
        "total_latency_seconds": round(total_latency, 3) if mode == "llm" and latency_available else None,
        "cost_usd": round(total_cost_usd, 6) if mode == "llm" and cost_available else None,
        "note": (
            "Synthetic, small, labelled examples only. Literal quotes can be verified; "
            "semantic claims remain unverified. Provider billing is not inferred. USD cost is included only if explicitly returned."
        ),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline", "llm"], default="baseline")
    parser.add_argument("--allow-external", action="store_true")
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "llm" and not args.allow_external:
        parser.error("LLM evaluation requires --allow-external (sends synthetic passages).")
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    summary = evaluate(dataset, mode=args.mode)
    output = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
        print(f"Evaluation saved: {args.output}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
