"""Lightweight UI integration smoke check (optional Streamlit dependency).

Run: pip install -e ".[ui]"
     python scripts/smoke_ui.py

Runs entirely in Streamlit's testing harness; no browser or external API calls.
"""

from __future__ import annotations

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "streamlit_app.py"


def assert_healthy(app: AppTest, stage: str) -> None:
    if app.exception:
        messages = "; ".join(str(exc.message) for exc in app.exception)
        raise AssertionError(f"{stage}: {messages}")


def main() -> None:
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert_healthy(app, "initial render")

    expected = {"Alterado": "2", "Adicionado": "1", "Removido": "1", "Preservado": "3"}
    actual = {item.label: item.value for item in app.metric}
    if actual != expected:
        raise AssertionError(f"unexpected synthetic demo summary: {actual}")

    demo_buttons = [i for i, button in enumerate(app.button) if "Executar demonstração" in button.label]
    if len(demo_buttons) != 1:
        raise AssertionError("demo button not available")
    app.button[demo_buttons[0]].click().run()
    assert_healthy(app, "demo interaction")
    semantic_actions = [button for button in app.button if button.label == "Solicitar hipótese por IA"]
    if len(semantic_actions) != 2 or any(not button.disabled for button in semantic_actions):
        raise AssertionError("local semantic actions must require explicit consent")

    app.radio[0].set_value("Comparar campos entre documentos").run()
    assert_healthy(app, "field comparison navigation")
    if not any(button.label == "Comparar informações" for button in app.button):
        raise AssertionError("field comparison action not available")

    original = os.environ.get("DOCDIFF_DEMO_ONLY")
    try:
        os.environ["DOCDIFF_DEMO_ONLY"] = "1"
        demo = AppTest.from_file(str(APP), default_timeout=30).run()
        assert_healthy(demo, "public sample-only review")
        if any("meus documentos" in btn.label for btn in demo.button):
            raise AssertionError("upload action exposed in demo-only mode")
        if any("Solicitar hipótese por IA" == button.label for button in demo.button):
            raise AssertionError("public demo must not expose semantic model actions")
        demo.radio[0].set_value("Comparar campos entre documentos").run()
        assert_healthy(demo, "public sample-only fields")
        field_button = next(
            (i for i, button in enumerate(demo.button) if button.label == "Comparar propostas de exemplo"),
            None,
        )
        if field_button is None:
            raise AssertionError("public sample field comparison is not available")
        demo.button[field_button].click().run()
        assert_healthy(demo, "public sample field results")
        if not any("Valor total" in item.label for item in demo.get("expander")):
            raise AssertionError("sample field result missing")
    finally:
        if original is None:
            os.environ.pop("DOCDIFF_DEMO_ONLY", None)
        else:
            os.environ["DOCDIFF_DEMO_ONLY"] = original

    public_entry = AppTest.from_file(str(ROOT / "app" / "demo_app.py"), default_timeout=30).run()
    assert_healthy(public_entry, "restricted deployment entry point")
    if any("meus documentos" in button.label for button in public_entry.button):
        raise AssertionError("public entry point exposes an upload action")
    if len(public_entry.metric) != 4:
        raise AssertionError("public entry point did not render the sample review")

    print("UI smoke passed: review, field mode, safe demo and public entry point")


if __name__ == "__main__":
    main()
