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
- src/docdiff_ai/core.py — deterministic extraction, normalization, comparison
- src/docdiff_ai/ai.py — optional and explicitly unverified LLM summary
- src/docdiff_ai/cli.py — CLI
- app/streamlit_app.py — optional interface
- tests/ — synthetic input fixtures and regression tests

## Engineering rules

- Public functions must be typed; support Python 3.11+.
- Keep work scoped; do not change unrelated modules or the public schema silently.
- Every extracted value must retain literal source evidence.
- Treat contradictory and missing information explicitly, never guess.
- Validate file size, extension and user-controlled input.
- Never invoke external models from offline paths.
- Never commit secrets or personal customer documents.
- Add focused tests for meaningful changes and fixes.
- Update examples and README when user-visible behavior changes.
- Avoid unnecessary frameworks, agents or long-running CI jobs.

## Validation before completion

Run: python -m ruff check .
Run: python -m ruff format --check .
Run: python -m unittest discover -s tests -v
Run: python .github/scripts/check_skills.py

State skipped tests, failed checks and unverified assumptions explicitly.
Do not approve or merge PRs without permission.
