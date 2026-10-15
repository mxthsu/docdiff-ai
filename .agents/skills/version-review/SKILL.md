---
name: version-review
description: Build auditable before/after document comparisons without overclaiming semantic accuracy.
---

# Evidence-first document version review

Load this skill when editing passage splitting, alignment, change classification,
before/after visualizations or downloadable version reports.

1. Preserve verbatim before/after passages, source names and line references.
2. Differentiate deterministic exact matches, heading matches and lexical heuristics.
3. Never call lexical similarity a semantic-equivalence score or legal risk.
4. Resolve repeated clauses one-to-one; do not silently drop removals/additions.
5. Verify reorders, duplicates, ambiguity, changed numbers, headings and blank files.
6. Ensure the default demo uses only synthetic documents and no external provider.
7. Limit potentially expensive alignment work and reject oversized input explicitly.
8. Keep version review independent from the existing field extraction and LLM APIs.
9. For UI changes, test the interactive sample flow, not only module import.
10. Update user-facing docs and exports when the comparison contract changes.
