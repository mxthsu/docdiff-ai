# DocDiff AI

**Compare business documents. Find discrepancies. Inspect the evidence.**

DocDiff AI is an open-source tool for comparing proposals and structured business documents.
Instead of an unexplained verdict, it links every extracted value to the original text used
in the comparison.

**Status:** early alpha (v0.1). This release focuses on a narrow, reproducible workflow:
comparing labeled totals, deadlines, warranties and payment terms. It is not a general
contract analysis or legal decision system.

> **Em português:** compare propostas comerciais, encontre informações divergentes e
> confira os trechos que justificam cada resultado.

## What works today

- Compare 2–10 TXT or Markdown documents locally without an API key.
- Extract labeled totals, delivery deadlines, warranties and payment terms.
- Detect differences, missing fields and contradictions inside a document.
- Export evidence-linked reports as Markdown or JSON.
- Convert PDF with selectable text and DOCX/PPTX through lightweight, optional Docling adapters.
- Optionally generate an LLM summary using an OpenAI-compatible API.
- Optionally use a Streamlit interface with document upload.

## Quick start

Python 3.11+ is required.

~~~bash
python -m pip install -e .
docdiff examples/proposal_a.md examples/proposal_b.md
docdiff examples/proposal_a.md examples/proposal_b.md --format json
~~~

For PDF and Office files:

~~~bash
python -m pip install -e ".[documents]"
~~~

For the visual interface:

~~~bash
python -m pip install -e ".[ui]"
streamlit run app/streamlit_app.py
~~~

### Optional LLM summary

Core comparison runs offline. To request a narrative summary, explicitly configure
an OpenAI-compatible provider:

~~~powershell
$env:DOCDIFF_API_KEY="your-key"
$env:DOCDIFF_MODEL="your-model"
$env:DOCDIFF_BASE_URL="https://api.openai.com/v1"
docdiff examples/proposal_a.md examples/proposal_b.md --ai-summary
~~~

**Privacy:** this option sends the structured findings and evidence excerpts to
the configured provider, not the full original files. Use only with permitted
data. AI summaries are unverified and require human review.

## Expected sample result

| Field | Status |
|---|---|
| Total amount | Different |
| Delivery deadline | Different |
| Warranty | Match |
| Payment terms | Different |

Each field contains the exact values and source excerpts.

## Architecture

1. Read files locally (or convert through optional Docling).
2. Extract values from supported labeled lines.
3. Normalize values and compare across documents.
4. Present differences with inspectable excerpts and converted-text line numbers.
5. Optionally summarize those evidence-backed results with an LLM.

See [document formats and integration tests](docs/DOCUMENTS.md),
[architecture](docs/ARCHITECTURE.md), [roadmap](.plans/active/v0.1.md),
and [contributing](CONTRIBUTING.md).

## Current limitations

- The deterministic engine supports four labeled fields only.
- Arbitrary clauses and complex tables are not generally understood yet.
- PDF files use Docling's native, model-free text extraction: scanned/image-only PDFs require OCR, which is not included yet.
- For converted PDF/Office files, line references point to converted Markdown text, **not physical PDF pages**.
- This is not a hosted production service or a replacement for human document review.
- AI summaries are not automatically fact-checked.
- OCR and conversion quality depend on the optional Docling setup.

## Development

~~~bash
python -m pip install -e '.[dev]'
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -s tests -v
python .github/scripts/check_skills.py
~~~

Instructions for coding agents live in [AGENTS.md](AGENTS.md). Canonical skills and
task routes live in [.agents/skills](.agents/skills). This structure draws inspiration
from Docling's contributor workflow; DocDiff AI is an independent project.

MIT licensed. Contributions and issues are welcome.
