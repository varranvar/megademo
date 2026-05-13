#!/usr/bin/env bash
set -euo pipefail

TOOL_NAME="${1:-}"
if [ -z "$TOOL_NAME" ]; then
    echo "Usage: $0 <tool-name>" >&2
    exit 1
fi

TOOL_DIR="tools/${TOOL_NAME}"
if [ ! -d "$TOOL_DIR" ]; then
    echo "Tool directory not found: $TOOL_DIR" >&2
    exit 1
fi

cd "$TOOL_DIR"

if [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
else
    echo "Warning: no virtualenv found at $TOOL_DIR/.venv" >&2
fi

exec python3 server.py
