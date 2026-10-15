# Public sample-only demo deployment

The public Streamlit demo must be safe by construction: **no upload of third-party
documents, no API keys, no user credentials, and no external model calls.**

This repository ships two application entry points:

- `app/streamlit_app.py`: full **local** workspace. Supports optional file
  uploads and explicit opt-in provider usage when installed/configured.
- `app/demo_app.py`: **public sample-only** entry point. Forces
  `DOCDIFF_DEMO_ONLY=1` before loading the interface. Allows only synthetic
  bundled examples. Upload and model actions are unavailable.

The root `requirements.txt` installs `.[ui]` only; no heavy Docling
conversion or local ML models are required by the public demo.

## Deploy with Streamlit Community Cloud

You must connect your **mxthsu** GitHub account to Streamlit Community Cloud
and authorize access to public repositories.

1. Open <https://share.streamlit.io> and authenticate with GitHub.
2. Select **New app / Deploy an app** from the public repository
   `mxthsu/docdiff-ai` (after the PR containing the app is merged).
3. Set the entry point to **`app/demo_app.py`**, **not**
   `app/streamlit_app.py`. Use Python **3.12** where the service allows a choice.
4. Deploy. The `requirements.txt` at repository root supplies Streamlit and
   the local package.
5. Verify that version comparison loads synthetic examples, field comparison
   uses synthetic examples, downloads work, and **no file upload or LLM
   controls exist**.
6. Copy the actual public URL into the GitHub repository's website field and
   README only *after* it has been verified.

**Do not commit Streamlit secrets or real documents.** The public sample
requires none. The local app can still be used privately via
`streamlit run app/streamlit_app.py`.

If a cloud provider ignores the desired entry point, disable public access
until confirmed; deploying the full workspace without input protection
would expose unnecessary file-processing capabilities.

## Checks

~~~bash
python -m pip install -e ".[ui]"
python scripts/smoke_ui.py
streamlit run app/demo_app.py
~~~

The smoke test exercises both the local workspace and the public sample-only
mode via Streamlit's testing harness, without launching a browser or contacting
an LLM.

## Future hosting review

Before enabling uploads on a public service, separately assess: document
confidentiality/retention, file content scanning, file sizes and zip bombs,
CPU/memory caps, document parsing sandbox, rate limiting, concurrency,
authentication, logging redaction, vulnerabilities and infrastructure costs.
Passing the sample-only smoke test is **not** production security certification.

Useful official documentation:
- <https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account>
- <https://docs.streamlit.io/deploy/concepts/dependencies>
- <https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization>
