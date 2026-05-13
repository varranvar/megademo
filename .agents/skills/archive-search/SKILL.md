---
name: archive-search
description: Query the Ubuntu Archive for package information. Use when the user asks about package versions, availability, dependencies, build status, bugs, or changelogs in the Ubuntu Archive. Especially useful for Rust packages (rustc, cargo, librust-*).
---

# Archive Semantic Search

You have access to the `ubuntu-archive` MCP server which provides real-time data from the Ubuntu Archive via Launchpad and archive indices.

## When to Use This Skill

- User asks "what version of X is in series Y?"
- User asks if a package exists in a release
- User asks about package dependencies or reverse dependencies
- User wants to compare package versions across series
- User asks about build status or build logs
- User asks about bugs filed against a package
- User asks about changelogs or copyright files
- User asks about autopkgtest results

## Query Patterns

| User Intent | MCP Tool | Example |
|---|---|---|
| Latest version of X in series Y | `get_package_version` | `get_package_version(package="cargo", series="noble")` |
| Does package X exist? | `search_packages` | `search_packages(query="librust-*", series="noble")` |
| Package details/deps | `get_package_details` | `get_package_details(package="rustc", series="noble")` |
| Who depends on X? | `get_reverse_dependencies` | `get_reverse_dependencies(package="librust-serde-dev")` |
| Build status | `get_build_status` | `get_build_status(package="rustc", series="noble")` |
| Build log | `get_build_log` | `get_build_log(package="cargo", series="noble", arch="amd64")` |
| Bugs | `get_bug_list` | `get_bug_list(package="rustc", status="New")` |
| Changelog | `get_changelog` | `get_changelog(package="rustc")` |
| Autopkgtest results | `get_autopkgtest_results` | `get_autopkgtest_results(package="rustc", series="noble")` |
| Copyright file | `get_copyright_file` | `get_copyright_file(package="rustc")` |
| Files in package | `get_package_files` | `get_package_files(package="cargo")` |

## Series Aliases

Both names and version numbers work:
- `24.04` = `noble`, `22.04` = `jammy`, `20.04` = `focal`
- `26.04` = `resolute`, `25.04` = `plucky`
- See `get_series_info()` for the full list

## Rust Package Conventions

- Rust library source packages: `rust-<crate-name>` (e.g., `rust-serde`, `rust-tokio`)
- Binary library packages: `librust-<crate>-dev` (e.g., `librust-serde-dev`)
- Toolchain: `rustc` (compiler), `cargo` (build tool), `clippy`, `rustfmt`

## Workflow

1. Identify the user's intent from their natural language query
2. Select the appropriate MCP tool(s)
3. Call the tool with correct parameters
4. If the result is unclear or partial, make follow-up calls
5. Synthesize the results into a clear, concise answer

## Example Interactions

**User:** "What version of cargo is in noble?"
→ Call `get_package_version(package="cargo", series="noble")`
→ Respond with version, date published, and component

**User:** "What Rust libraries are available in noble?"
→ Call `search_packages(query="librust-*", series="noble", search_field="name")`
→ Summarize the results

**User:** "Are there any open bugs on rustc?"
→ Call `get_bug_list(package="rustc", status="New")`
→ Summarize bug count and top issues

## Important Notes

- The MCP server uses **read-only** Launchpad access. It cannot file bugs or make changes.
- If a user wants to take action (file a bug, propose a change), provide them with the exact Launchpad URL and instructions for doing it manually.
- For build logs, only the last 8000 characters are returned. If the user needs more, tell them to visit the `log_url` directly.
