# Contributing

DocDiff AI is in early development. Reports with reproducible input examples and
focused pull requests are welcome.

## Working on a contribution

1. Open an issue for changes to public behavior or new field support.
2. Keep changes scoped. Include a regression test whenever behavior changes.
3. Run: python -m ruff check . and python -m ruff format --check .
4. Run: python -m unittest discover -s tests -v
5. Run: python .github/scripts/check_skills.py
6. Update examples and documentation when the public behavior changes.
7. Use synthetic fixtures: never include confidential documents or credentials.

For PRs, report tests actually executed, their results and the limitations.
Commit messages follow Conventional Commits (e.g. feat: support invoice dates).
Do not claim AI accuracy or model benchmarks without reproducible evidence.
