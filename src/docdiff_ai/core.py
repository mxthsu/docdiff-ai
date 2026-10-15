"""Deterministic comparison engine with inspectable source evidence."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

FIELDS = ("total_price", "delivery_days", "warranty_months", "payment_days")
LABELS = {
    "total_price": "Valor total",
    "delivery_days": "Prazo de entrega",
    "warranty_months": "Garantia",
    "payment_days": "Prazo de pagamento",
}
PATTERNS = {
    "total_price": re.compile(
        r"^\s*(?:valor total|pre[cç]o total|total(?: price| amount)?|total da proposta|amount due)"
        r"\s*[:=\-]\s*(?P<value>(?:R\$|US\$|USD|BRL|EUR|€|\$)\s*[\d.,]+)",
        re.IGNORECASE,
    ),
    "delivery_days": re.compile(
        r"^\s*(?:prazo de entrega|entrega|delivery(?: time| period)?)"
        r"\s*[:=\-]\s*(?P<value>\d+)\s*(?:dias|days)\b",
        re.IGNORECASE,
    ),
    "warranty_months": re.compile(
        r"^\s*(?:garantia|warranty)\s*[:=\-]\s*(?P<value>\d+)\s*(?:meses|months)\b",
        re.IGNORECASE,
    ),
    "payment_days": re.compile(
        r"^\s*(?:prazo de pagamento|payment terms|payment period)"
        r"\s*[:=\-]\s*(?:net\s*)?(?P<value>\d+)\s*(?:dias|days)?\b",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True)
class SourceDocument:
    name: str
    text: str


@dataclass(frozen=True)
class Evidence:
    document: str
    line: int
    excerpt: str
    raw: str
    normalized: str


@dataclass(frozen=True)
class FieldComparison:
    field: str
    label: str
    status: str
    evidence: dict[str, list[Evidence]]


@dataclass(frozen=True)
class ComparisonReport:
    documents: list[str]
    fields: list[FieldComparison]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_price(raw: str) -> str:
    value = raw.strip().replace(" ", "")
    prefix = re.match(r"^(R\$|US\$|USD|BRL|EUR|€|\$)", value, re.IGNORECASE)
    if prefix is None:
        raise ValueError("Moeda ausente.")
    symbol = prefix.group(1).upper()
    currency = {"R$": "BRL", "BRL": "BRL", "US$": "USD", "$": "USD", "USD": "USD", "€": "EUR", "EUR": "EUR"}[symbol]
    amount = value[len(prefix.group(1)):]
    if "," in amount and "." in amount:
        decimal_separator = "," if amount.rfind(",") > amount.rfind(".") else "."
    elif "," in amount:
        decimal_separator = "," if len(amount.rsplit(",", 1)[-1]) != 3 else ""
    elif "." in amount:
        decimal_separator = "." if len(amount.rsplit(".", 1)[-1]) != 3 else ""
    else:
        decimal_separator = ""
    if decimal_separator:
        thousands = "." if decimal_separator == "," else ","
        amount = amount.replace(thousands, "").replace(decimal_separator, ".")
    else:
        amount = amount.replace(",", "").replace(".", "")
    try:
        parsed = Decimal(amount).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError("Valor monetário inválido.") from exc
    return f"{currency}:{parsed}"


def _normalize(field: str, raw: str) -> str:
    if field == "total_price":
        return _normalize_price(raw)
    return str(int(raw))


def extract_evidence(document: SourceDocument, fields: tuple[str, ...] = FIELDS) -> dict[str, list[Evidence]]:
    """Return only values supported by literal text excerpts."""
    unknown = set(fields) - set(FIELDS)
    if unknown:
        raise ValueError(f"Campos desconhecidos: {', '.join(sorted(unknown))}")
    matches: dict[str, list[Evidence]] = {field: [] for field in fields}
    for line_number, line in enumerate(document.text.splitlines(), start=1):
        for field in fields:
            matched = PATTERNS[field].match(line)
            if matched is not None:
                raw = matched.group("value").strip()
                matches[field].append(
                    Evidence(document.name, line_number, line.strip(), raw, _normalize(field, raw))
                )
    return matches


def compare(documents: list[SourceDocument], fields: tuple[str, ...] = FIELDS) -> ComparisonReport:
    """Compare two or more documents without making unsupported inferences."""
    if not 2 <= len(documents) <= 10:
        raise ValueError("Forneça entre 2 e 10 documentos.")
    names = [document.name for document in documents]
    if len(set(names)) != len(names):
        raise ValueError("Os nomes dos documentos precisam ser diferentes.")
    evidence = {document.name: extract_evidence(document, fields) for document in documents}
    comparisons: list[FieldComparison] = []
    for field in fields:
        occurrences = {name: evidence[name][field] for name in names}
        distinct_by_document = [{entry.normalized for entry in occurrences[name]} for name in names]
        if any(len(values) > 1 for values in distinct_by_document):
            status = "ambiguous"
        elif any(not values for values in distinct_by_document):
            status = "missing"
        elif len(set.union(*distinct_by_document)) == 1:
            status = "match"
        else:
            status = "different"
        comparisons.append(FieldComparison(field, LABELS[field], status, occurrences))
    return ComparisonReport(names, comparisons)


STATUS_LABELS = {
    "match": "Concordam",
    "different": "Divergentes",
    "missing": "Dados ausentes",
    "ambiguous": "Ambíguos no documento",
}


def report_to_markdown(report: ComparisonReport) -> str:
    lines = ["# Comparação de documentos", "", "Resultados extraídos de evidências textuais. Não equivalem a uma auditoria definitiva.", ""]
    for field in report.fields:
        lines += [f"## {field.label} — {STATUS_LABELS[field.status]}", ""]
        for name in report.documents:
            hits = field.evidence[name]
            if not hits:
                lines.append(f"- **{name}**: não encontrado")
            else:
                for hit in hits:
                    lines.append(
                        f"- **{name}**, linha {hit.line}: {hit.raw} "
                        f"(normalizado: {hit.normalized}) — \u201c{hit.excerpt}\u201d"
                    )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
