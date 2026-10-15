---
name: llm-evaluation
description: Evaluate changes to model behavior without inventing quality metrics.
---

# LLM evaluation

Use when adding or changing prompts, providers, LLM-based extraction or summaries.

1. Define a versioned synthetic test dataset and intended behavior.
2. Include missing facts, contradictory sources and prompt-injection inputs.
3. Keep deterministic comparison independent from model availability.
4. Record provider, model, prompt revision, parameters, cost and limitations.
5. Compare versions against a fixed baseline before claiming improvement.
6. Treat model output as unverified and require source-backed claims.
7. Keep external data transfer explicit and documented.

Never state accuracy, reliability or production-readiness metrics that have
not been measured with reproducible evidence.
