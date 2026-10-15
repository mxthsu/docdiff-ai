"""Command-line interface for comparing local documents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ai import AIReviewError, summarize_with_llm
from .core import FIELDS, compare, report_to_markdown
from .documents import DocumentReadError, from_path
from .verified_extraction import PROMPT_VERSION, ExtractionError, VerifiedLLMExtractor
from .version_diff import compare_versions, review_to_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docdiff", description="Compare documentos comerciais com evidências verificáveis."
    )
    parser.add_argument("documents", nargs="+", type=Path, help="Arquivos para comparação (2 a 10).")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument(
        "--review-versions",
        action="store_true",
        help="Compara trechos de duas versões, offline, com evidência por linha.",
    )
    parser.add_argument(
        "--extraction",
        choices=["rules", "llm"],
        default="rules",
        help="rules: offline; llm: envia o texto completo extraído ao provedor configurado.",
    )
    parser.add_argument("--fields", nargs="+", choices=FIELDS, default=list(FIELDS))
    parser.add_argument("--output", type=Path, help="Salve o relatório no caminho indicado.")
    parser.add_argument(
        "--ai-summary", action="store_true", help="Envia evidências a um LLM externo (opt-in)."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.review_versions:
            if len(args.documents) != 2:
                raise ValueError("Revisão de versões exige exatamente dois documentos.")
            if args.extraction != "rules" or args.ai_summary:
                raise ValueError(
                    "Revisão de versões é offline e não usa as opções --extraction/--ai-summary."
                )
            before, after = (from_path(path) for path in args.documents)
            review = compare_versions(before, after)
            output = (
                json.dumps(review.to_dict(), ensure_ascii=False, indent=2) + "\n"
                if args.format == "json"
                else review_to_markdown(review)
            )
            if args.output:
                args.output.write_text(output, encoding="utf-8")
                print(f"Relatório salvo em: {args.output}")
            else:
                print(output, end="")
            return 0
        documents = [from_path(path) for path in args.documents]
        extractor = VerifiedLLMExtractor() if args.extraction == "llm" else None
        fields = tuple(dict.fromkeys(args.fields))
        report = compare(documents, fields, extractor=extractor) if extractor else compare(documents, fields)
        output = (
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"
            if args.format == "json"
            else report_to_markdown(report)
        )
        if extractor:
            if args.format == "json":
                details = json.loads(output)
                details["extraction"] = {
                    "mode": "llm",
                    "prompt_version": PROMPT_VERSION,
                    "rejected_candidate_count": len(extractor.rejected),
                    "rejected_reasons": [item.reason for item in extractor.rejected],
                    "note": "Citação textual validada; interpretação semântica requer revisão humana.",
                }
                output = json.dumps(details, ensure_ascii=False, indent=2) + "\n"
            else:
                output += (
                    "\n_Extração por LLM: evidências verificadas no texto; "
                    f"{len(extractor.rejected)} candidatos rejeitados. "
                    "Interpretação semântica exige revisão humana._\n"
                )
        if args.ai_summary:
            summary = summarize_with_llm(report)
            if args.format == "json":
                data = json.loads(output)
                data["ai_summary_unverified"] = summary
                output = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            else:
                output += "\n## Resumo por IA (revisão humana necessária)\n\n" + summary + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
            print(f"Relatório salvo em: {args.output}")
        else:
            print(output, end="")
        return 0
    except (DocumentReadError, ValueError, AIReviewError, ExtractionError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
