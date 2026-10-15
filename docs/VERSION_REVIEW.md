# Document version review

DocDiff AI compares two versions of a document and creates an inspectable
textual change report. It intentionally does **not** claim to infer contract
risk or full semantic equivalence.

## MVP

- Segments Markdown headings, numbered clauses and blank-line-delimited paragraphs.
- Preserves the original passage text and source line ranges.
- Aligns exact text first, then uniquely named headings, then high-confidence
  lexical matches.
- Labels passages **modified, added, removed or unchanged**.
- Flags numeric changes in modified passages for human attention.
- Produces JSON and Markdown reports; local comparison uses no LLM or API key.
- Accepts Docling-converted PDF/DOCX/PPTX, with converted-Markdown line
  references rather than invented PDF page numbers.

## Quick start

~~~bash
docdiff examples/agreement_before.md examples/agreement_after.md --review-versions
docdiff examples/agreement_before.md examples/agreement_after.md --review-versions --format json
streamlit run app/streamlit_app.py
~~~

In the Streamlit interface version review opens with the synthetic sample pair;
no credentials, document upload or paid API are required to view it.
A restricted public entrypoint (`app/demo_app.py`) disables uploads and LLMs.
Deployment instructions are in [DEPLOYMENT.md](DEPLOYMENT.md).

## Why this is not a semantic diff yet

Alignment uses normalized text, identical section headings, and lexical similarity
(`difflib.SequenceMatcher`) — **not an embedding model, NLI, or an LLM**.
A section with the same heading can carry totally different meaning.
A rewritten clause with completely different words can appear as an addition
and removal. Numeric flags mean only that numeric tokens changed, not that
legal or financial risk was detected.

The report keeps both verbatim texts so the reader can verify each observation.
An optional, experimental, quote-verified per-pair interpretation is provided
for modified passages only; it requires consent and does not change the offline
report. See [SEMANTIC_REVIEW.md](SEMANTIC_REVIEW.md).
A future evaluated semantic **alignment** for unmatched clauses must
explain uncertainty and cite each side independently. It must never silently
override textual evidence.

## Safety, limits and privacy

- Two input documents are required for version review.
- Maximum of 150,000 converted-text characters and 200 passages per document.
- Huge/empty inputs fail explicitly; the app does not silently truncate.
- Passage alignment is best-effort, not legal advice or an approval workflow.
- Local version review makes no external API calls.
- Uploaded files are not persisted by the Streamlit UI; Docling temporary files
  are cleaned up after conversion.
- Public hosting is not enabled; deployment requires an independent security
  review covering upload scanning, denial of service, limits and rate controls.

## Related work

Docling is used only to parse the source formats. Other open-source projects
already offer semantic/redline review of contracts. This is an independent
evidence-first version review workflow for broad business documents, with
optional AI features isolated and measurable, rather than an attempt to replace
Docling's document-conversion engine.
