# Integrating a New Tool

## 1. Copy the Template
```bash
cp -r tools/_template tools/my-new-tool
```

## 2. Implement the MCP Server
Edit `tools/my-new-tool/server.py`:
- Rename the FastMCP instance.
- Replace the placeholder `example_tool` with your actual analysis tools.
- Keep the server read-only.

## 3. Add Dependencies
Edit `tools/my-new-tool/pyproject.toml` and add any required packages.

## 4. Create a Virtualenv
```bash
cd tools/my-new-tool
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 5. Register in Root MCP Config
Add an entry to the root `.opencode.json`:
```json
"my-new-tool": {
  "type": "stdio",
  "command": "./run-tool.sh",
  "args": ["my-new-tool"]
}
```

## 6. Add Skill Metadata
Edit `tools/my-new-tool/skill.yaml` to describe your tool's purpose, parameters, and example prompts.

## 7. Add Frontend Renderer (Required)
Create `frontend/src/components/MyNewTool.svelte` to visualise your tool's JSON output.
Register it in `frontend/src/App.svelte` so it is used when your tool's data is selected.

## 8. Document in AGENTS.md
Add your tool to the "Tool Registry" section so agents know it exists.

## 9. Build & Test
```bash
cd frontend
npm run build
```
Verify the frontend compiles and that your tool's data directory appears correctly.
