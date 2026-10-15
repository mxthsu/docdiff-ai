---
name: code-review
description: Review changes at an exact commit with reproducible findings.
---

# Code review

Before reviewing, read the issue, PR description, head commit, diff and CI.
Load AGENTS.md and applicable task skills. Identify the affected public contracts.

Trace input to output and verify source citations, normalization, error handling,
privacy and backwards compatibility where relevant. For fixes, reproduce the
original bug and show a regression test when feasible.

Run focused tests and the route validator. Record exact commands and outcomes;
never report unrun checks as passed.

Classify findings as:
- Blocker: demonstrated security, data-loss or correctness defect.
- Suggestion: nonblocking improvement without a proven defect.
- Question: important missing evidence, not an asserted defect.

Include reviewed commit SHA, blockers and known limitations in your verdict.
Seek authorization before approval or merge.
