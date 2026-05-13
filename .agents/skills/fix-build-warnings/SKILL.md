---
name: fix-build-warnings
description: Find and fix compiler/build warnings in Ubuntu packages. Use when the user wants to eliminate build warnings, especially from Rust packages compiled with the Ubuntu toolchain.
---

# Fix Build Warnings

## When to Use

- User asks to fix build warnings in a package
- User wants a clean build with no warnings
- User is preparing a package for upload and needs warning-free builds

## Workflow

1. **Fetch build log**: Use `get_build_log` MCP tool to get the latest build log
2. **Parse warnings**: Extract warning lines from the build log
3. **Categorize**: Group by warning type
4. **Fix**: Apply appropriate fixes for each category
5. **Verify**: Rebuild in a container and check for remaining warnings

## Warning Categories and Fixes

### C/C++ Warnings

| Pattern | Fix |
|---|---|
| `-Wimplicit-function-declaration` | Add missing `#include` or forward declaration |
| `-Wformat-security` | Use `%s` format instead of passing string directly to printf-family |
| `-Wimplicit-int` | Add explicit `int` return type |
| `-Wincompatible-pointer-types` | Fix type mismatch in function call/assignment |
| `-Wdeprecated-declarations` | Replace with the recommended alternative |
| `-Wunused-variable` | Remove or use the variable; prefix with `(void)var;` if intentionally unused |
| `-Wreturn-mismatch` | Fix return type or add proper return statement |

### Rust Warnings

| Pattern | Fix |
|---|---|
| `warning: unused import` | Remove the import or prefix with `#[allow(unused_imports)]` |
| `warning: dead_code` | Remove dead code or add `#[allow(dead_code)]` |
| `warning: unused variable` | Prefix with `_` or use `let _ = ...` |
| `warning: deprecated` | Migrate to the recommended replacement |
| `warning: unreachable pattern` | Reorder match arms |
| `warning: clippy::...` | Apply the clippy suggestion |

### General

| Pattern | Fix |
|---|---|
| `making` / `missing separator` | Fix Makefile syntax |
| `config.status: error` | Fix configure arguments or autoreconf |
| `dpkg-buildpackage: warning` | Fix debian/rules or control file issues |

## Container Build Setup

Use the `scripts/container-setup` script to create a Podman build container, then `scripts/run-build` to build:

```bash
scripts/container-setup noble
scripts/run-build rustc noble /tmp/rustc
```

## Important Notes

- For Rust packages, many warnings are in vendored dependencies. Focus on warnings in the package's own code first.
- If a warning comes from upstream code that you don't want to modify, add a patch or configure flag to suppress it.
- Always check if the package uses `-Werror` (or `-Dwarnings` for Rust) — this makes warnings fatal.
