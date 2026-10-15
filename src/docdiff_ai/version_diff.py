"""Evidence-linked diff of two document versions, with conservative textual matching.

Passage similarity is lexical, not semantic. Added / removed / modified decisions
are best-effort alignments, not legal assessments or LLM conclusions.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any

from .core import SourceDocument

MAX_TEXT_CHARS = 150_000
MAX_PASSAGES = 200
MIN_SIMILARITY = 0.66
MARKDOWN_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)\s*$")
NUMBERED_CLAUSE = re.compile(r"^\s*(?P<number>\d+(?:\.\d+){0,3})[.)]\s+(?P<body>[^\n]+)$")
NUMBER = re.compile(r"(?<![\w])\d+(?:[.,]\d+)*(?![\w])")
WORD = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class Passage:
    id: str
    document: str
    heading: str
    text: str
    start_line: int
    end_line: int
    reference_type: str


@dataclass(frozen=True)
class Change:
    id: str
    status: str
    before: Passage | None
    after: Passage | None
    matched_by: str
    lexical_similarity: float | None
    numbers_changed: bool


@dataclass(frozen=True)
class ReviewReport:
    before_name: str
    after_name: str
    changes: list[Change]
    counts: dict[str, int]
    method: str = "offline_lexical_alignment_v1"
    caveat: str = (
        "Lexical alignment is not semantic equivalence. "
        "Changed, added and removed clauses require human review. "
        "Converted Markdown lines are not physical PDF page coordinates."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalized(text: str) -> str:
    """Normalize layout artifacts only, keeping important numbers and negation."""
    stripped = re.sub(r"[*_`]", "", text).casefold()
    return " ".join(stripped.split())


def split_passages(document: SourceDocument) -> list[Passage]:
    """Build source-linked paragraphs under Markdown headings or numbered clauses."""
    if len(document.text) > MAX_TEXT_CHARS:
        raise ValueError("O documento excede 150 mil caracteres para revisão de versões.")
    passages: list[Passage] = []
    heading = ""
    lines: list[str] = []
    start_line = 0

    def flush() -> None:
        nonlocal lines, start_line
        if not lines:
            return
        text = "\n".join(lines).strip()
        if text:
            passages.append(
                Passage(
                    id=f"{document.name}:{len(passages) + 1}",
                    document=document.name,
                    heading=heading,
                    text=text,
                    start_line=start_line,
                    end_line=start_line + len(lines) - 1,
                    reference_type=document.reference_type,
                )
            )
        lines = []
        start_line = 0

    for position, raw in enumerate(document.text.splitlines(), 1):
        value = raw.strip()
        found = MARKDOWN_HEADING.match(value)
        if found:
            flush()
            heading = found.group("title").strip()
            continue
        found_numbered = NUMBERED_CLAUSE.match(value)
        if found_numbered and not lines:
            flush()
            heading = f"Cláusula {found_numbered.group('number')}"
            start_line = position
            lines = [value]
            flush()
            continue
        if not value:
            flush()
            continue
        if not lines:
            start_line = position
        lines.append(raw.rstrip())
    flush()
    if len(passages) > MAX_PASSAGES:
        raise ValueError(f"Documento excede o limite de {MAX_PASSAGES} trechos.")
    if not passages:
        raise ValueError(f"Documento sem trechos comparáveis: {document.name}.")
    return passages


def _tokens(text: str) -> set[str]:
    return set(WORD.findall(_normalized(text)))


def _similarity(a: Passage, b: Passage) -> float:
    left = _normalized(a.text)
    right = _normalized(b.text)
    tokens_a = _tokens(left)
    tokens_b = _tokens(right)
    if not tokens_a or not tokens_b:
        return 0.0
    jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    # The shortlist gate avoids quadratic sequence alignment for clearly unrelated text.
    if jaccard < 0.45:
        return 0.0
    return round(SequenceMatcher(None, left, right, autojunk=False).ratio(), 4)


def compare_versions(before: SourceDocument, after: SourceDocument) -> ReviewReport:
    """Align passages one to one without making LLM calls or inventing text."""
    if before.name == after.name:
        raise ValueError("Versões precisam ter nomes diferentes.")
    old = split_passages(before)
    new = split_passages(after)
    paired: dict[int, tuple[int, str, float]] = {}
    used_old: set[int] = set()
    used_new: set[int] = set()

    # 1. Stable literal matches, including reordered passages and duplicates.
    exact_index: dict[str, list[int]] = defaultdict(list)
    for j, passage in enumerate(new):
        exact_index[_normalized(passage.text)].append(j)
    for i, passage in enumerate(old):
        options = exact_index.get(_normalized(passage.text), [])
        matched = next((j for j in options if j not in used_new), None)
        if matched is not None:
            paired[i] = (matched, "identical_text", 1.0)
            used_old.add(i)
            used_new.add(matched)

    # 2. Unique section headings allow even strongly rewritten clauses to align.
    old_titles: dict[str, list[int]] = defaultdict(list)
    new_titles: dict[str, list[int]] = defaultdict(list)
    for i, passage in enumerate(old):
        if i not in used_old and passage.heading:
            old_titles[_normalized(passage.heading)].append(i)
    for j, passage in enumerate(new):
        if j not in used_new and passage.heading:
            new_titles[_normalized(passage.heading)].append(j)
    for name, indices in old_titles.items():
        targets = new_titles.get(name, [])
        if len(indices) == 1 and len(targets) == 1:
            i, j = indices[0], targets[0]
            paired[i] = (j, "same_heading", _similarity(old[i], new[j]))
            used_old.add(i)
            used_new.add(j)

    # 3. Conservative best lexical one-to-one pairs, not semantic matching.
    scores: list[tuple[float, int, int]] = []
    for i, source in enumerate(old):
        if i in used_old:
            continue
        for j, target in enumerate(new):
            if j in used_new:
                continue
            similarity = _similarity(source, target)
            if similarity >= MIN_SIMILARITY:
                scores.append((similarity, i, j))
    for similarity, i, j in sorted(scores, key=lambda item: (-item[0], item[1], item[2])):
        if i not in used_old and j not in used_new:
            paired[i] = (j, "lexical_similarity", similarity)
            used_old.add(i)
            used_new.add(j)

    changes: list[Change] = []
    for i, old_passage in enumerate(old):
        if i not in paired:
            changes.append(
                Change(
                    id=f"change:{len(changes) + 1}",
                    status="removed",
                    before=old_passage,
                    after=None,
                    matched_by="unmatched",
                    lexical_similarity=None,
                    numbers_changed=False,
                )
            )
            continue
        j, method, score = paired[i]
        new_passage = new[j]
        unchanged = _normalized(old_passage.text) == _normalized(new_passage.text)
        changes.append(
            Change(
                id=f"change:{len(changes) + 1}",
                status="unchanged" if unchanged else "modified",
                before=old_passage,
                after=new_passage,
                matched_by=method,
                lexical_similarity=score,
                numbers_changed=(
                    set(NUMBER.findall(old_passage.text)) != set(NUMBER.findall(new_passage.text))
                    if not unchanged
                    else False
                ),
            )
        )
    for j, passage in enumerate(new):
        if j not in used_new:
            changes.append(
                Change(
                    id=f"change:{len(changes) + 1}",
                    status="added",
                    before=None,
                    after=passage,
                    matched_by="unmatched",
                    lexical_similarity=None,
                    numbers_changed=False,
                )
            )

    # Stable reviewer ordering: after-document order; removed passages in old order.
    changes.sort(
        key=lambda item: (
            item.after.start_line if item.after is not None else 10**9,
            item.before.start_line if item.before is not None else 0,
        )
    )
    counts = {
        status: sum(1 for change in changes if change.status == status)
        for status in ("modified", "added", "removed", "unchanged")
    }
    return ReviewReport(before.name, after.name, changes, counts)


def review_to_markdown(report: ReviewReport) -> str:
    """Produce an evidence-oriented local review, not a legal conclusion."""
    labels = {"modified": "Alterado", "added": "Adicionado", "removed": "Removido", "unchanged": "Preservado"}
    lines = [
        f"# Revisão: {report.before_name} → {report.after_name}",
        "",
        f"> {report.caveat}",
        "",
        *(f"- **{labels[status]}**: {count}" for status, count in report.counts.items()),
        "",
    ]
    for item in report.changes:
        title = (item.after or item.before).heading or "Trecho sem título"
        lines.extend([f"## {labels[item.status]} — {title}", ""])
        if item.numbers_changed:
            lines.append("**Atenção:** foram encontrados números diferentes; confira o significado.")
        for side, passage in (("Antes", item.before), ("Depois", item.after)):
            if passage is None:
                continue
            source = (
                "Markdown convertido"
                if passage.reference_type == "converted_markdown_line"
                else "texto original"
            )
            lines.extend(
                [
                    f"**{side}** — {passage.document}, linhas {passage.start_line}–{passage.end_line} ({source})",
                    "",
                    "> " + passage.text.replace("\n", "\n> "),
                    "",
                ]
            )
        if item.status == "modified":
            lines.append(f"_Pareado por: {item.matched_by} (sem equivalência semântica garantida)._")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
