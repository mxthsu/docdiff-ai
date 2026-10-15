"""Public sample-only entry point. Never accepts uploaded documents or external APIs."""

import importlib
import os

# Force the safety boundary independently of cloud environment configuration.
os.environ["DOCDIFF_DEMO_ONLY"] = "1"
importlib.import_module("streamlit_app")
