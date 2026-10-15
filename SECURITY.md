# Security

Please do not disclose exploitable vulnerabilities through public issues.
Until a private disclosure contact is configured, contact the maintainer
privately via GitHub before sharing proof-of-concept or sensitive data.

- Local comparison does not use remote APIs.
- The optional LLM summary transmits excerpts only with explicit user action.
- This alpha project is not hardened for untrusted public multi-tenant hosting.
- A restricted `app/demo_app.py` entry point is available for public demonstration with synthetic inputs only; the unrestricted workspace must not be deployed publicly without security review.
- The demo entry point hides uploads and all provider actions; it is not a full production security assessment.
- Do not upload confidential or regulated documents without a separate review.
- Store API keys in environment variables; never commit credentials.
