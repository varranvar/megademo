# Ubuntu Archive AI Hygiene

AI-powered strategies for improving the quality and health of packages in the
Ubuntu Archive — starting with the Rust toolchain and Rust libraries.

This project gives AI agents (and the humans working alongside them) the tools
to query the archive, find problems, and fix them: lintian violations, build
warnings, memory safety issues, missing tests, poor coverage, and inaccurate
copyright files.

## Architecture

Three pillars that work together:

| Pillar | Purpose | Location |
|--------|---------|----------|
| **MCP Server** | Real-time data access to Launchpad, archive indices, autopkgtest | `mcp/ubuntu-archive/` |
| **Skills** | Domain knowledge and step-by-step workflows for each hygiene strategy | `.agents/skills/` |
| **Helper Scripts** | Local operations: builds, analysis, generation | `scripts/` |

```
project/
├── .agents/skills/          AI agent skills
│   ├── archive-search/      Natural-language archive queries
│   ├── fix-lintian/         Fix lintian errors/warnings
│   ├── fix-build-warnings/  Eliminate compiler warnings
│   ├── sanitizer-builds/    ASan/UBSan/TSan builds
│   ├── coverage-analysis/   Measure and improve test coverage
│   ├── write-autopkgtests/  Generate autopkgtest templates
│   ├── analyze-skipped-tests/  Investigate skipped/failing tests
│   ├── fix-copyright/       Audit and fix debian/copyright
│   └── skill-creator/       Meta-skill for creating new skills
├── mcp/ubuntu-archive/      MCP server
│   ├── server.py            14 MCP tools
│   ├── pyproject.toml       uv-managed dependencies
│   └── tests/               Integration tests against live Launchpad
├── scripts/                 Shell helper scripts
│   ├── download-source-pkg  Download and extract source packages
│   ├── run-lintian          Lintian with JSON output
│   ├── container-setup      Create Podman build containers
│   ├── run-build            Build packages in containers
│   ├── run-sanitizer-build  Build with ASan/UBSan/TSan
│   ├── analyze-coverage     Coverage measurement and reports
│   ├── generate-autopkgtest Generate autopkgtest templates
│   └── analyze-copyright    Compare source licenses with debian/copyright
└── AGENTS.md                Agent configuration and MCP setup
```

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Podman](https://podman.io/) (for containerized builds)
- Bash

### Set up the MCP server

```bash
cd mcp/ubuntu-archive
uv sync
```

This creates a virtual environment and installs all dependencies including
`launchpadlib`, `mcp`, `httpx`, and `cachetools`.

### Run the tests

```bash
cd mcp/ubuntu-archive
uv run python tests/test_server.py
```

Tests run against the live Launchpad API (read-only, anonymous access). They
verify series resolution, package version lookups, search, build status, and
bug queries.

### Start the MCP server

```bash
cd mcp/ubuntu-archive
uv run ubuntu-archive-mcp
```

### Configure your AI tool

For **opencode**, add to `.config/opencode/config.json`:

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

For other MCP-compatible tools (Claude Desktop, etc.), use the same `command`
and `args` with the appropriate configuration format.

## MCP Server Tools

The `ubuntu-archive` MCP server provides 14 read-only tools backed by
Launchpad (via `launchpadlib`), archive.ubuntu.com indices, changelogs.ubuntu.com,
and autopkgtest.ubuntu.com:

| Tool | Description | Data Source |
|------|-------------|-------------|
| `get_series_info` | List all Ubuntu series (name, version, status) | Launchpad |
| `get_package_version` | Latest published version of a source package | Launchpad |
| `search_packages` | Search by name or description (supports wildcards) | Archive indices |
| `get_package_details` | Full metadata: deps, maintainer, section | Archive indices |
| `get_changelog` | Fetch Debian changelog | changelogs.ubuntu.com |
| `get_build_status` | Build status across architectures | Launchpad |
| `get_build_log` | Fetch a specific build log | Launchpad |
| `get_autopkgtest_results` | Query autopkgtest results | autopkgtest.ubuntu.com |
| `get_reverse_dependencies` | Packages that depend on a given package | Archive indices |
| `get_bug_list` | Search Launchpad bugs for a package | Launchpad |
| `run_lintian` | Run lintian locally, return structured JSON | Local CLI |
| `get_source_package` | Download and extract source package | `apt-get source` |
| `get_copyright_file` | Fetch debian/copyright | changelogs.ubuntu.com |
| `get_package_files` | List files installed by a binary package | Archive indices |

### Series aliases

Both codenames and version numbers are accepted:

| Version | Codename |
|---------|----------|
| 24.04 | noble |
| 22.04 | jammy |
| 20.04 | focal |
| 26.04 | resolute |
| 25.04 | plucky |

Call `get_series_info()` for the full list.

### Rust package conventions

| Type | Naming | Example |
|------|--------|---------|
| Library source package | `rust-<crate>` | `rust-serde`, `rust-tokio` |
| Binary library package | `librust-<crate>-dev` | `librust-serde-dev` |
| Toolchain | — | `rustc`, `cargo`, `clippy`, `rustfmt` |

## Skills

Skills are structured instruction sets that teach AI agents how to perform
specific hygiene tasks. Each lives in `.agents/skills/<name>/SKILL.md`.

| Skill | When to Use | Workflow Summary |
|-------|-------------|-----------------|
| `archive-search` | Query package info from the archive | Parse NL query → select MCP tool → call → synthesize answer |
| `fix-lintian` | Fix lintian errors/warnings | Download source → run lintian → categorize by severity → fix each issue → re-verify |
| `fix-build-warnings` | Eliminate compiler/build warnings | Fetch build log → parse warnings → categorize by type → fix source → rebuild |
| `sanitizer-builds` | Find memory/UB/race issues | Download source → build with ASan/UBSan/TSan → parse output → fix source → re-verify |
| `coverage-analysis` | Measure and improve test coverage | Download source → build with coverage → run tests → identify gaps → write tests → re-verify |
| `write-autopkgtests` | Add autopkgtests where none exist | Check existing results → inspect package → detect type → generate tests → validate |
| `analyze-skipped-tests` | Investigate skipped/failing tests | Fetch results → identify skipped/failed → categorize reason → propose fix |
| `fix-copyright` | Audit and fix debian/copyright | Fetch current file → scan source → compare → fix mismatches → verify with lintian |

### Using skills with an AI agent

If your agent supports skills (opencode, Claude Code, etc.), they trigger
automatically based on user intent. You can also invoke them explicitly:

```
Use the fix-lintian skill to clean up rustc for noble.
```

### Creating new skills

Use the `skill-creator` skill:

```
Use the skill-creator skill to draft a new skill for tracking upstream versions.
```

New skills go in `.agents/skills/<name>/SKILL.md`. See `AGENTS.md` for the
full directory convention.

## Helper Scripts

All scripts are in `scripts/` and should be run with bash.

### download-source-pkg

Download and extract a source package from the archive.

```bash
scripts/download-source-pkg <package> [series] [dest-dir]
# Example:
scripts/download-source-pkg cargo noble /tmp/cargo
```

### run-lintian

Run lintian on a `.changes` or `.deb` file with structured JSON output.

```bash
scripts/run-lintian <changes-or-deb-file> [severity]
# severity: error, warning (default), info, pedantic
# Example:
scripts/run-lintian /tmp/cargo/cargo_*.changes warning
```

### container-setup

Create a Podman build container for a given Ubuntu series. Installs
build-essential, devscripts, dh-cargo, sbuild, lintian, and autopkgtest.

```bash
scripts/container-setup <series> [image-name]
# Example:
scripts/container-setup noble
```

### run-build

Build a package inside a Podman container.

```bash
scripts/run-build <package> <series> <source-dir> [image-name]
# Example:
scripts/run-build cargo noble /tmp/cargo
```

Build logs are saved to `/tmp/build-logs/<package>/build.log`.

### run-sanitizer-build

Build with Address Sanitizer, Undefined Behavior Sanitizer, or Thread Sanitizer.

```bash
scripts/run-sanitizer-build <package> <series> <sanitizer>
# sanitizer: asan, ubsan, tsan
# Example:
scripts/run-sanitizer-build rustc noble asan
```

Logs are saved to `/tmp/sanitizer-logs/<package>/<sanitizer>/sanitizer-build.log`.

### analyze-coverage

Build with coverage instrumentation, run tests, and generate a report. Detects
Rust projects (uses `cargo-llvm-cov`) and C/C++ projects (uses `gcov`/`lcov`)
automatically.

```bash
scripts/analyze-coverage <source-dir> [output-format]
# output-format: json (default), html
# Example:
scripts/analyze-coverage /tmp/rustc/rustc-1.75.0
```

### generate-autopkgtest

Generate autopkgtest templates based on package type (Rust, Python, C, daemon).
Creates `debian/tests/control` and test scripts.

```bash
scripts/generate-autopkgtest <package> <series> <source-dir>
# Example:
scripts/generate-autopkgtest cargo noble /tmp/cargo
```

### analyze-copyright

Scan source files for license headers and compare against `debian/copyright`.

```bash
scripts/analyze-copyright <source-dir>
# Example:
scripts/analyze-copyright /tmp/rustc/rustc-1.75.0
```

## Package Scope

Initially scoped to **Rust packages**:

- **Rust toolchain**: `rustc`, `cargo`, `clippy`, `rustfmt`
- **Rust libraries**: `librust-*-dev`, `rust-*`

The MCP server works for any Ubuntu package. Skills and scripts are tested
against Rust packages first and will expand to other ecosystems over time.

## Build Environment

All builds run in **Podman** containers for isolation and reproducibility.

1. Create a build image: `scripts/container-setup noble`
2. Build inside it: `scripts/run-build cargo noble /tmp/cargo`

The container image is based on `ubuntu:<series>` and includes the full
packaging toolchain: `build-essential`, `devscripts`, `debhelper`, `dh-cargo`,
`sbuild`, `lintian`, `autopkgtest`, and `podman` (for nested containers if
needed).

## Read-Only Access

The MCP server uses **anonymous, read-only** Launchpad access. It cannot:

- File bugs
- Propose merges
- Upload packages
- Modify any Launchpad resource

When a user wants to take action, the agent provides the exact Launchpad URL
and step-by-step instructions for them to do it manually.

## Development

### Running tests

```bash
cd mcp/ubuntu-archive
uv run python tests/test_server.py
```

### Adding a new MCP tool

Add an `@mcp.tool()` function to `mcp/ubuntu-archive/server.py`. Follow the
existing pattern: docstring with `Args:` section, type-annotated parameters,
return a dict. The tool is auto-registered by FastMCP.

### Adding a new skill

Create `.agents/skills/<name>/SKILL.md` with YAML frontmatter (`name`,
`description`) and markdown instructions. Or use the `skill-creator` skill for
the full authoring workflow.

### Adding a new script

Add an executable bash script to `scripts/`. Follow the existing pattern:
`set -euo pipefail`, `usage()` function, documented parameters.

## License

This project is developed at Canonical for Ubuntu Archive quality improvement.
