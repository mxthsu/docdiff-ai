# Architecture

DocDiff AI has two complementary, explicitly separated workflows:

1. **Version review (offline):** two documents, evidence-linked paragraphs,
   change categories and a side-by-side reviewer interface.
2. **Field comparison:** two to ten documents, structured values normalized by
   deterministic rules or extracted by a separately enabled LLM path.

~~~text
Local TXT/Markdown OR optional Docling PDF/DOCX/PPTX conversion
                         |
             SourceDocument(name, text, reference_type)
                         |
            +------------+-------------+
            |                          |
      version_diff.py                core.py
      segment paragraphs            field extraction
      align by exact/heading        normalize values
      lexical similarity            evidence / status
            |                          |
       ReviewReport           ComparisonReport
            |                          |
       CLI / Streamlit              CLI / Streamlit
       Markdown / JSON              Markdown / JSON
                                       |
                                (explicit opt-in only)
                                       |
                               verified_extraction.py
                               OpenAI-compatible LLM
                                       |
                                local quote validation
~~~

The independent `ai.py` module can optionally summarize field results;
it cannot override the normalized field-comparison statuses.

## Core contracts

- Version evidence includes `document`, `heading`, `text`,
  `start_line`, `end_line` and `reference_type`.
- Optional `semantic_review.py` takes only a selected paired change, requires two independently verified original quotes, and never overwrites the offline review.
- The version-review pairing order is exact-text matches, unique headings,
  then conservative **lexical** matches. This is **not semantic analysis**.
- Field extraction preserves `document`, `line`, literal `excerpt`, `raw`,
  `normalized` and `reference_type`. LLM suggestions must be verified.
- Ingestion validates extension and a 10 MB input limit.
- Text formats are UTF-8; optional Docling-slim handles PDF with selectable
  text and DOCX/PPTX without local ML models.
- `text_line` references original TXT/MD lines. `converted_markdown_line`
  references Docling's exported Markdown, **not** physical PDF coordinates.
- Version review bounds text to 150k characters and 200 passages per document.
- Default review and default field comparison do **not** send data to providers.
- The public demo uses a separate `app/demo_app.py` entry point that forcibly disables uploads and LLM actions. The full app must not be hosted publicly without additional security review.
- Model-assisted field extraction must be enabled explicitly, is constrained
  by response/size limits and still requires human interpretation.

## Contribution and quality

The engineering process follows `AGENTS.md`, canonical skills under
`.agents/skills`, `skill-router.json`, a route validator and PR-only quick
quality gates. Expensive Docling integration tests are opt-in via manual CI.

## Relationship to Docling

Docling focuses on content conversion and document representations; DocDiff AI
implements the version review workflow that follows conversion. Related
open-source semantic/redline comparison projects already exist; DocDiff AI
does not claim novelty or complete semantic comparison. It prioritizes an
auditable local-first baseline and useful nontechnical review experience.

## Future work

Evaluated semantic change explanations with bilateral quote verification,
source-page coordinates, more robust clause alignment, optional deployment
with upload security review, and public demo access.
