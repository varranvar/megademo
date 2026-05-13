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

## MCP Servers

### ubuntu-archive

Real-time access to the Ubuntu Archive via Launchpad and archive indices.

**Start command:**
```bash
cd /project/mcp/ubuntu-archive && uv run ubuntu-archive-mcp
```

**Configuration** (for opencode, add to `.config/opencode/config.json`):
```json
{
  "mcpServers": {
    "ubuntu-archive": {
      "command": "uv",
      "args": ["run", "ubuntu-archive-mcp"],
      "cwd": "/project/mcp/ubuntu-archive"
    }
  }
}
```

**Available tools:**

| Tool | Description |
|------|-------------|
| `get_series_info` | List all Ubuntu series (name, version, status) |
| `get_package_version` | Latest published version of a source package |
| `search_packages` | Search packages by name or description (supports wildcards) |
| `get_package_details` | Full metadata: deps, maintainer, section, description |
| `get_changelog` | Fetch Debian changelog |
| `get_build_status` | Build status across architectures |
| `get_build_log` | Fetch a specific build log |
| `get_autopkgtest_results` | Query autopkgtest results |
| `get_reverse_dependencies` | Packages that depend on a given package |
| `get_bug_list` | Search Launchpad bugs for a package |
| `run_lintian` | Run lintian and return structured JSON |
| `get_source_package` | Download and extract source package |
| `get_copyright_file` | Fetch debian/copyright |
| `get_package_files` | List files installed by a binary package |

The MCP server uses **read-only** Launchpad access. When a user wants to take action (file a bug, propose a merge), provide the Launchpad URL and instructions for them to do it manually.

## Available Skills

| Skill | When to Use |
|-------|-------------|
| `archive-search` | Query the Ubuntu Archive for package info |
| `fix-lintian` | Fix lintian errors/warnings in packages |
| `fix-build-warnings` | Eliminate build warnings |
| `sanitizer-builds` | Build with ASan/UBSan/TSan to find memory issues |
| `coverage-analysis` | Measure and improve test coverage |
| `write-autopkgtests` | Write autopkgtests for packages with none |
| `analyze-skipped-tests` | Investigate skipped/failing autopkgtests |
| `fix-copyright` | Fix outdated/inaccurate debian/copyright files |

## Helper Scripts

All scripts live in `/project/scripts/` and should be run with bash:

| Script | Purpose |
|--------|---------|
| `download-source-pkg` | Download and extract a source package |
| `run-lintian` | Run lintian with structured JSON output |
| `container-setup` | Create a Podman build container |
| `run-build` | Build a package in a container |
| `run-sanitizer-build` | Build with sanitizers (asan/ubsan/tsan) |
| `analyze-coverage` | Build with coverage and generate report |
| `generate-autopkgtest` | Generate autopkgtest templates |
| `analyze-copyright` | Compare source licenses with debian/copyright |

## Package Scope

Initially scoped to **Rust packages** — the Rust toolchain (rustc, cargo, clippy, rustfmt) and Rust libraries (librust-\*-dev, rust-\*).

## Build Environment

All builds use **Podman** containers. Use `scripts/container-setup` to create a build image, then `scripts/run-build` to build packages inside it.
