# Package Analyser — Agent Instructions

## Project Overview
This is a Canonical hackathon project: a read-only package analysis platform composed of multiple MCP-based tools. Each tool lives in `tools/<tool-name>/` and exposes its functionality via an MCP server. The OpenCode agent running in the root directory can invoke any registered tool.

## Read-Only Policy
All tools are **read-only**. They fetch data from external services (Launchpad, GitHub, CVE databases, Debian repositories, etc.) and must only write analysis output to `frontend/data/<tool-name>/`. No tool may modify the source tree, system packages, or any external state.

## Tool Registry
Tools are registered in `.opencode.json` at the project root. The `run-tool.sh` wrapper activates each tool's local virtualenv and starts its MCP server.

Current tools:
- `bug-triage` — Finds Launchpad bug duplicates and upstream issues.

## Data Output Convention
When a tool produces analysis, it should:
1. Write JSON files to `frontend/data/<tool-name>/`.
2. Name files descriptively (e.g., `<package>-<timestamp>.json`).
3. Update `frontend/data/<tool-name>/manifest.json` with the list of produced files.

## How to Invoke a Tool
Use the MCP server name as registered in `.opencode.json`. Example:
> "Run bug-triage on bug #123456"

The agent will call the `bug-triage` MCP server with the appropriate tool and arguments.

## Adding a New Tool
See `INTEGRATION.md`.

## Skill Directory

All skills for this project live in **`.agents/skills/`** at the repository root. This is the single shared location used by everyone on the team, regardless of which AI tool or model you're using.

- **Creating a new skill**: write it to `.agents/skills/<skill-name>/SKILL.md`
- **Editing a skill**: edit it in-place under `.agents/skills/<skill-name>/`
- **Never** create skills in `/tmp`, session workspaces, or any other location

Each skill follows the structure:
```
.agents/skills/<skill-name>/
├── SKILL.md            ← required: YAML frontmatter + instructions
├── scripts/            ← optional: helper scripts
├── references/         ← optional: supporting docs
└── assets/             ← optional: templates, icons, fonts
```

For the full skill authoring workflow (drafting, testing, evaluating, iterating), invoke the **skill-creator** skill located at `.agents/skills/skill-creator/`.
