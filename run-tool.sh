#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

run_tool() {
    local tool_name="$1"
    local tool_dir="${SCRIPT_DIR}/tools/${tool_name}"
    if [ ! -d "$tool_dir" ]; then
        echo "Tool directory not found: $tool_dir" >&2
        return 1
    fi

    echo "=== Running tool: ${tool_name} ==="
    cd "$tool_dir"

    if command -v uv &>/dev/null && [ -f "pyproject.toml" ]; then
        uv run python3 server.py
    elif [ -f ".venv/bin/activate" ]; then
        source ".venv/bin/activate"
        python3 server.py
    else
        echo "Warning: no virtualenv found at $tool_dir/.venv and uv not available" >&2
        python3 server.py
    fi
    cd "$SCRIPT_DIR"
}

TOOL_NAME="${1:-}"
if [ -z "$TOOL_NAME" ]; then
    for tool_dir in "${SCRIPT_DIR}"/tools/*/; do
        tool_name="$(basename "$tool_dir")"
        [[ "$tool_name" == _* ]] && continue
        [ -f "${tool_dir}server.py" ] || continue
        run_tool "$tool_name"
    done
else
    run_tool "$TOOL_NAME"
fi
