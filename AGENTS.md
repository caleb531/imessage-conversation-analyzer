This project is a fully-typed Python library and CLI for analyzing local iMessage conversations on a macOS system. The CLI allows you to run a number of built-in "analyzers" for gathering metrics, while the Python API allows you to write your own custom analyzers.

All code must be compatible with the minimum supported Python version defined in `pyproject.toml`.

After making changes, run:
- `uv run ruff format .`
- `uv run ruff check .`
- `uv run ty check .` (ty is an alternative to mypy)
- `uv run pytest`
