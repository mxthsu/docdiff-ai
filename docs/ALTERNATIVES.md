# Similar open-source tools and positioning

Checked 2026-10-15. The comparison below describes public project scope,
**not** a claim that DocDiff AI is more accurate or more popular.

| Project | Focus | Relation to DocDiff AI |
|---|---|---|
| [Docling](https://github.com/docling-project/docling) | Document conversion, layout, tables and OCR | DocDiff AI optionally uses its conversion library; Docling itself is not a document-review UI. |
| [Docling Graph](https://github.com/docling-project/docling-graph) | Structured extraction and knowledge graphs | Useful prior art for typed extraction; not something we should reimplement without a concrete need. |
| [LexLens / contract-lens](https://github.com/arsinghin/contract-lens) | Contract review, clause/risk analysis and redline comparison | Significant functional overlap with document comparison and review UI. |
| [SemanticDiff](https://github.com/PSakthivel353/SemanticDiff) | Legal semantic comparison and implications | Explicitly tackles semantic meaning changes; our current MVP does **not**. |

## Scope chosen for DocDiff AI

- **Local-first** review using no paid LLM calls by default.
- Transparent side-by-side before/after **source passages**, with extracted-text
  line references and separate headings.
- Reproducible deterministic baseline, documented limits, simple CLI and exports.
- A nontechnical sample-only public demo with no upload or model attack surface.
- A separate, opt-in structured-field extraction module with literal-source
  verification; no unsupported accuracy claims.

This is a **narrower engineering and UX direction**, not demonstrated market
differentiation. A genuine semantic model should be evaluated on real document
changes before being advertised as a strength.
