# DocDiff AI — guidance for coding agents

Use Portuguese for collaboration and explanations. Preserve English code
identifiers and public APIs. This file is the repository-wide instruction set.

## Goal

DocDiff AI compares business documents with evidence users can inspect.
Prioritize correctness, traceability, data privacy and usability. Do not call
deterministic extraction "AI-powered" unless AI was actually used.

## Skills and task routes

Read .agents/skills/skill-router.json and load only applicable skills.
The canonical skill source is .agents/skills; do not duplicate skill content.
For reviews and re-reviews load code-review first.

## Repository structure

- src/docdiff_ai/documents.py — reading and Docling input adapter
- src/docdiff_ai/core.py — deterministic extraction, normalization, field comparison
- src/docdiff_ai/version_diff.py — offline version review, anchored passages, textual alignment
- src/docdiff_ai/ai.py — optional and explicitly unverified LLM summary
- src/docdiff_ai/cli.py — CLI
- app/streamlit_app.py — local interactive workspace
- app/demo_app.py — restricted public sample-only entry point; never expose uploads or model actions
- tests/ — synthetic input fixtures and regression tests

## Engineering rules

- Public functions must be typed; support Python 3.11+.
- Keep work scoped; do not change unrelated modules or the public schema silently.
- Every extracted value must retain literal source evidence.
- Version review must retain each before/after passage and line range; lexical matches are not semantic judgments.
- Use `version-review` for passage segmentation, alignment, or the side-by-side review UI.
- Treat contradictory and missing information explicitly, never guess.
- Converted Markdown line numbers are not PDF page numbers; always preserve `reference_type`.
- Validate file size, extension and user-controlled input.
- Never invoke external models from offline paths. LLM extraction must be explicitly selected.
- Treat model-produced evidence as untrusted until verified against exact source text; report rejected candidates.
- Never claim LLM benchmark accuracy based on mocked model completions.
- Never commit secrets or personal customer documents.
- Add focused tests for meaningful changes and fixes.
- Update examples and README when user-visible behavior changes.
- Keep a one-click demo using synthetic documents; do not require provider API keys to view it.
- In public demos use the `demo_app.py` entry point; no file uploads, credentials or external provider actions.
- Avoid unnecessary frameworks, agents or long-running CI jobs.

## Validation before completion

Run: python -m ruff check .
Run: python -m ruff format --check .
Run: python -m unittest discover -s tests -v
Run: python .github/scripts/check_skills.py

State skipped tests, failed checks and unverified assumptions explicitly.
Do not approve or merge PRs without permission.
