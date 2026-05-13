---
name: fix-lintian
description: Fix lintian issues in Ubuntu packages. Use when the user wants to run lintian on a package, fix lintian errors or warnings, or improve package quality per Debian/Ubuntu policy. Especially useful for Rust packages.
---

# Fix Lintian Issues

## When to Use

- User asks to fix lintian issues in a package
- User asks about package policy compliance
- User wants to clean up lintian errors/warnings before upload

## Workflow

1. **Download source**: Use `get_source_package` MCP tool or `scripts/download-source-pkg`
2. **Run lintian**: Use `run_lintian` MCP tool or `scripts/run-lintian` on the `.changes` file
3. **Categorize**: Sort issues by severity — errors first, then warnings, then info
4. **Fix each issue**: See the reference tables below
5. **Re-verify**: Run lintian again to confirm fixes

## Common Lintian Fixes for Rust Packages

| Tag | Fix |
|---|---|
| `debian-watch-file-is-missing` | Add `debian/watch` pointing to crates.io API |
| `package-uses-old-packaging-format` | Upgrade to debhelper compat 13+ or dh-sequence |
| `copyright-file-out-of-date` | Regenerate `debian/copyright` from Cargo.lock crate list |
| `description-synopsis-starts-with-article` | Remove leading "A" or "An" from synopsis |
| `extra-license-file` | Remove duplicate LICENSE files from binary packages |
| `rust-module-not-compiled-with-debhelper` | Use `dh-cargo` for proper Rust packaging |
| `arch-dependent-file-in-usr-share` | Move arch-specific files to `usr/lib` |
| `binary-without-manpage` | Generate manpage from `--help` output |
| `hardening-no-relro` | Enable hardening flags in `debian/rules` |
| `missing-build-dependency` | Add missing B-D entries |

## When to Override vs. Fix

**Fix** the issue when:
- The tag points to a genuine problem
- The fix is straightforward
- It improves package quality

**Override** when:
- The tag is a false positive (document why)
- The upstream design requires the flagged behavior
- The fix would break functionality

Override file locations:
- Binary: `debian/<package>.lintian-overrides` or `/usr/share/lintian/overrides/<package>`
- Source: `debian/source/lintian-overrides`

Override format:
```
<package> [arch-list]: <tag-name> [context]
# Comment explaining why this override exists
```

## Tag Reference

Full tag explanations: `https://lintian.debian.org/tags/<tag-name>.html`

## Important Notes

- Always prioritize **errors** (E:) over **warnings** (W:) over **info** (I:)
- When you fix a lintian issue, commit the fix separately with a message like "fix-lintian: <tag-name>"
- If lintian is not available in the environment, instruct the user to run it locally and paste the JSON output
