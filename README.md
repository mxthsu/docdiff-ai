# DocDiff AI

**Compare two versions of a document. See what changed. Verify the evidence.**

DocDiff AI is an open-source document review workspace for business users and
developers. Upload two document versions, review added, removed, modified and
unchanged passages, and inspect the original text for each finding.

**No account or LLM API key is needed to try the example locally.**

> Em português: compare versões de um contrato ou proposta e veja as mudanças
> lado a lado. Os trechos são apresentados com referências ao texto de origem.

**Project status: early alpha (v0.1).** This is a working local preview, not a
hosted service or automated legal review system.

## Try the review workspace

Requirements: Python 3.11+ and a clone of this repository.

~~~bash
python -m pip install -e ".[ui]"
streamlit run app/streamlit_app.py
~~~

The interface opens with a complete comparison of **two synthetic agreements**.
You can run the example again with one click, upload your own two versions, filter
changes and export a Markdown/JSON review report. The local demo makes no LLM
requests and does not require paid credentials.

A restricted **public sample-only entry point** is included:

~~~bash
streamlit run app/demo_app.py
~~~

It disables uploads and LLM actions. See
[public deployment instructions](docs/DEPLOYMENT.md). No hosted URL has been
published or verified yet.

In the local workspace, an **experimental, optional semantic review** can
suggest what a selected change means. It requires your explicit consent before
sending two excerpts to a configured model. The result must cite both original
passages and remains an unverified hypothesis. See
[semantic review and evaluation](docs/SEMANTIC_REVIEW.md).

For PDF/DOCX/PPTX input, install the optional lightweight conversion integration:

~~~bash
python -m pip install -e ".[documents,ui]"
~~~

PDF uses model-free text extraction; scanned/image-only PDFs need OCR, which
is **not** supported by this path.

## Example: before and after

| Finding | Version A | Version B |
|---|---|---|
| Payment window | 30 days | 45 days |
| Termination notice | 60 days | 90 days |
| Confidentiality section | Present | Removed |
| Personal-data access | Absent | Added |

Each change links to the exact passage and extracted-text line references,
not just a generated interpretation. These are **synthetic example values**.

## CLI and library

Version review is deterministic and works without network calls:

~~~bash
python -m pip install -e .
docdiff examples/agreement_before.md examples/agreement_after.md --review-versions
docdiff examples/agreement_before.md examples/agreement_after.md --review-versions --format json
~~~

The original multi-document **field comparison** remains available:

~~~bash
docdiff examples/proposal_a.md examples/proposal_b.md
~~~

It extracts and compares four labeled fields: total amount, delivery deadline,
warranty period and payment period. For advanced use, there is a separate
**opt-in LLM field extractor**, with literal-source verification and an evaluation
dataset. See [LLM extraction and privacy](docs/LLM_EXTRACTION.md).

### Why not just use Docling?

[Docling](https://github.com/docling-project/docling) parses and converts source
documents into structured content. DocDiff AI uses Docling as an **optional
input adapter**, then handles *version comparison, evidence preservation,
review workflow and report exports*. It is an independent application, not
a fork of Docling or a replacement for its conversion pipeline.

## Architecture in brief

~~~text
TXT / MD / PDF / DOCX / PPTX
            |
   Local text / Docling conversion
            |
            +-- version_diff.py: paragraph segmentation and lexical alignment
            |       |
            |       +-- before/after review + evidence + exports
            |       +-- semantic_review.py (optional per-pair LLM hypothesis)
            |
            +-- core.py: normalized field comparison
                    |
                    +-- rules (offline) or verified_extraction.py (opt-in LLM)
~~~

Core behavior is unit tested without remote providers. Heavy Docling conversion
is tested separately. The repository includes `AGENTS.md`, task-specific skills,
skill routing, contribution guidelines and lint/test checks on pull requests.

See [version review behavior](docs/VERSION_REVIEW.md),
[architecture](docs/ARCHITECTURE.md),
[document formats](docs/DOCUMENTS.md) and
[how to contribute](CONTRIBUTING.md) and
[existing open-source alternatives](docs/ALTERNATIVES.md) and
[semantic review evaluation](docs/SEMANTIC_REVIEW.md).

## What the tool does **not** do

- **Text similarity is not semantic equivalence.** The version review uses
  text, headings and conservative lexical matching; it can miss paraphrases,
  reorders of substantially changed clauses and cross-references.
- Numeric differences are flagged for review, **not classified as legal risk**.
- Exact quotes are evidence of textual occurrence, not proof of contractual meaning.
- Converted Markdown line numbers are **not physical PDF page citations**.
- Hosted deployment, OCR, security hardening for untrusted multi-tenant uploads,
  automated legal-risk classification and general semantic alignment of
  unpaired clauses are not implemented yet. The optional per-pair semantic
  hypothesis is not independently verified for meaning.
- LLM extraction is opt-in and sends document text to the configured provider.
  Model accuracy has **not** been established on real-world documents.

## Quality and development

~~~bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -s tests -v
python .github/scripts/check_skills.py
python scripts/evaluate_extraction.py --mode rules
python scripts/evaluate_semantic.py --mode baseline
# Optional Streamlit UI smoke check (requires .[ui]):
python scripts/smoke_ui.py
~~~

Optional real PDF/Office integration tests are documented in
[docs/DOCUMENTS.md](docs/DOCUMENTS.md).

**License:** MIT. Reports with reproducible examples and focused contributions
are welcome. No confidential documents are checked into this repository.
