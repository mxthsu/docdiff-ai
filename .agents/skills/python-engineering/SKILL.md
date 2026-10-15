---
name: python-engineering
description: Standards for maintainable Python changes in DocDiff AI.
---

# Python engineering

Use this skill when changing Python code. Check the minimum supported Python
version in pyproject.toml. Prefer typed functions, explicit contracts,
pathlib for filesystem access, narrow exception handling and standard library
solutions where appropriate. Separate comparison logic from CLI and UI.

Add targeted regression tests for owned behavior. Do not add self-validating
tests or mock-heavy tests that cannot detect real regressions.
