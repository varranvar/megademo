---
name: write-autopkgtests
description: Write autopkgtests for Ubuntu packages that lack them. Use when the user wants to add automated tests for a package, especially Rust packages with no or minimal autopkgtest coverage.
---

# Write Autopkgtests

## When to Use

- Package has no `debian/tests/control`
- User wants to add autopkgtests
- User asks "how do I test this package after install?"
- SRU process requires autopkgtests

## Workflow

1. **Check existing tests**: `get_autopkgtest_results` to see current status
2. **Download source**: `get_source_package` to inspect package
3. **Determine package type**: CLI tool, library, daemon, Python package, Rust crate
4. **Generate tests**: Use `scripts/generate-autopkgtest` or write manually
5. **Validate**: Run tests with `autopkgtest` in a container

## Autopkgtest File Structure

```
debian/tests/
├── control          # Required: test metadata
├── import           # Optional: Python import test
├── unit-test        # Optional: custom test script
└── ...
```

## debian/tests/control Format

```
Tests: import-test
Restrictions: allow-stderr
Depends: @, python3-pytest

Tests: unit-test
Restrictions: needs-root, isolation-machine
Depends: @, @builddeps@
Features: test-name-1
```

### Key Fields

| Field | Description |
|---|---|
| `Tests` | Space-separated test executable names in `debian/tests/` |
| `Depends` | `@` (binaries from this source), `@builddeps@` (build deps), or explicit packages |
| `Restrictions` | `needs-root`, `isolation-machine`, `allow-stderr`, `flaky`, `breaks-testbed`, `rw-build-tree` |
| `Features` | Optional feature flags for the test runner |

## Test Templates by Package Type

### Rust Library (`librust-*-dev`)

```
Tests: rust-import
Depends: @, rustc
Restrictions: allow-stderr
```

`debian/tests/rust-import`:
```bash
#!/bin/sh
set -e
# Try to compile a simple program linking against the library
cat > /tmp/test.rs <<'EOF'
use serde::Serialize;
#[derive(Serialize)]
struct Foo { x: i32 }
fn main() { let _ = serde_json::to_string(&Foo { x: 1 }); }
EOF
rustc --edition 2021 --crate-type bin -o /tmp/test /tmp/test.rs -L /usr/lib/rustlib/x86_64-linux-gnu/lib --extern serde=/usr/lib/rustlib/x86_64-linux-gnu/lib/libserde-*.rlib
/tmp/test
```

### Rust Binary (cargo, rustfmt, clippy)

```
Tests: smoke-test
Depends: @, rustc
Restrictions: allow-stderr
```

`debian/tests/smoke-test`:
```bash
#!/bin/sh
set -e
cargo --version
cargo --help
cargo new /tmp/hello-world
cd /tmp/hello-world
cargo build
cargo test
```

### Python Package

```
Tests: import-test
Depends: @, python3-all
Restrictions: allow-stderr

Tests: pytest
Depends: @, python3-pytest
Restrictions: allow-stderr
```

### C Library (`lib*-dev`)

```
Tests: compile-test
Depends: @, gcc, pkg-config
Restrictions: allow-stderr
```

### Daemon/Service

```
Tests: service-test
Depends: @
Restrictions: needs-root, isolation-machine
```

## Important Notes

- Always make test scripts executable (`chmod +x debian/tests/*`)
- Use `set -e` in shell scripts to fail on any error
- `allow-stderr` is almost always needed for Rust packages
- Test that the installed package works, not the build tree
- Keep tests minimal — they run on every dependency change
- For Rust, focus on `cargo test`-level integration rather than unit tests (those run during build)
