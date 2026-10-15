# Document conversion (PDF, DOCX and PPTX)

DocDiff AI keeps conversion optional. Plain TXT/Markdown comparison works without
Docling, network access, or model credentials.

## Install

With Python 3.11+:

~~~bash
python -m pip install -e ".[documents]"
~~~

The `documents` extra uses `docling-slim[format-pdf,format-office]`. It deliberately
avoids `models-local`, Torch, downloaded layout models and OCR dependencies.
PDFs use Docling's **native** text extraction; DOCX and PPTX use Docling's
Office converters. A local model is **not** required or used by this path.

Supported:
- PDF: born-digital documents containing selectable text.
- DOCX / PPTX: document text that the Office converters can extract.
- TXT / MD: UTF-8 original text (no Docling required).

Not supported in this adapter:
- Scanned/image-only PDFs that need OCR.
- Screenshots/handwriting or AI-powered visual interpretation.
- General extraction from arbitrary tables/clauses (the field parser still
  recognizes only labeled lines).
- Accurate physical page coordinates and bounding-box citations.

## Where the evidence points

Every extracted value includes `document`, `line`, `excerpt`,
`raw`, `normalized`, and `reference_type` in JSON.

| Input | reference_type | Meaning |
|---|---|---|
| TXT / MD | `text_line` | Line in the UTF-8 input file |
| PDF / DOCX / PPTX | `converted_markdown_line` | Line in **Docling's exported Markdown** |

**A converted Markdown line is never advertised as a physical PDF page
number.** Conversion can reorder or transform source structure. The UI and
Markdown output distinguish the line types explicitly.

## Real integration tests (opt-in)

The fast unit suite runs without Docling. Run real end-to-end integration
tests separately, after installing the optional dependencies:

~~~bash
python -m pip install -e ".[documents,integration-tests]"
python -m unittest discover -s tests/integration -v
~~~

Fixtures are generated at test time with ReportLab, python-docx and python-pptx.
They contain synthetic proposal values only; no copyrighted or private
documents are committed. Coverage includes PDF, DOCX, PPTX, byte uploads,
corruption, image-only/scanned PDFs, empty DOCX, cross-format comparison and evidence provenance.

In GitHub Actions, these tests run **only on manual dispatch** with
`run_docling_integration=true`. Pull request CI runs the fast suite, Ruff
and the skill routing checks only; this avoids heavy installs on every PR.

## Reproducible profiling

~~~bash
python scripts/profile_documents.py
~~~

The profile script measures conversion wall time and process CPU time and
uses Python's `tracemalloc` for Python-managed peak allocations on synthetic
inputs. It is **not** a complete measure of native-library RSS or peak GPU RAM.
Cold-start behavior, CPU count, OS and document complexity can change times
significantly. Do not present one local profile as a throughput benchmark.

## Conversion safety

Inputs have a 10 MB per-document limit, allowed extensions, and explicit
failure on incomplete or blank conversion. Uploaded Office/PDF bytes use a
temporary file that's cleaned up when conversion returns. Converter input is
a local path, not a user-controlled remote URL. External API calls remain
opt-in in the independent LLM-summary feature.
