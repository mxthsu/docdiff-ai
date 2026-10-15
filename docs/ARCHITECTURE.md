# Architecture

DocDiff AI uses deterministic evidence extraction before optional AI summarization.

~~~text
file / upload
    |
documents.py -> SourceDocument(name, text)
    |
core.py -> Evidence(document, line, excerpt, raw, normalized)
    |
ComparisonReport(status by field)
    |                      |
CLI / Streamlit ------> Markdown / JSON
                           |
                      (explicit opt-in)
                           |
                          ai.py
                           |
                      external LLM summary
~~~

## Design constraints

- Ingestion validates extensions and a 10 MB limit per document.
- Markdown and TXT are read as UTF-8; optional Docling handles PDF and Office.
- Rule-based field extraction includes literal text evidence.
- Statuses distinguish match, different, missing and internally ambiguous.
- LLM summaries do not alter the comparison outcome.
- A converted Markdown line does not establish a physical PDF page number.
- Files uploaded via the UI are only stored in temporary locations during conversion.

## Relationship to Docling

Docling is an optional document conversion dependency, not the product itself.
DocDiff AI focuses on review workflows and evidence-linked comparisons.

## Possible extensions

Typed extraction protocol, multilingual rule packs, evaluated LLM-based extraction,
provenance validation, document highlights and deployable demo environments.
