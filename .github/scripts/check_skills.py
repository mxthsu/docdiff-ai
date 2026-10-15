"""Validate canonical agent skill routes and front matter."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents" / "skills"
ROUTER = SKILLS / "skill-router.json"


def check_routes() -> list[str]:
    errors: list[str] = []
    try:
        routes = json.loads(ROUTER.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"Cannot load routes: {exc}"]
    if not isinstance(routes, dict) or not routes:
        return ["Routes must be a nonempty object."]
    discovered = {entry.name for entry in SKILLS.iterdir() if entry.is_dir()}
    if discovered != set(routes):
        errors.append(
            f"Routing mismatch: missing={discovered - set(routes)}; stale={set(routes) - discovered}"
        )
    for name, description in routes.items():
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            errors.append(f"Invalid skill name: {name}")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"Empty route description: {name}")
        file = SKILLS / name / "SKILL.md"
        if not file.is_file():
            errors.append(f"Missing skill file: {name}")
        else:
            sections = file.read_text(encoding="utf-8").split("---", 2)
            if len(sections) < 3 or f"name: {name}" not in sections[1]:
                errors.append(f"Invalid skill metadata: {name}")
    if not (ROOT / "AGENTS.md").is_file():
        errors.append("Missing AGENTS.md")
    return errors


if __name__ == "__main__":
    errors = check_routes()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Skill routes and instructions: OK")
