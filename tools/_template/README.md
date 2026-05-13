# Template Tool

This is a boilerplate for new analysis tools.

## Structure
- `server.py` — FastMCP server exposing tool functions.
- `pyproject.toml` — Python dependencies and entrypoint.
- `skill.yaml` — Metadata for OpenCode agent discovery.
- `.opencode.json` — Local MCP config for testing inside this folder.

## Getting Started
1. Replace `server.py` logic with your read-only analysis.
2. Update `pyproject.toml` dependencies.
3. Update `skill.yaml` with real descriptions.
4. Run `python3 -m venv .venv && source .venv/bin/activate && pip install -e .`
5. Test locally with `python3 server.py` or via the local `.opencode.json`.
