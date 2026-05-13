---
name: coverage-analysis
description: Analyze test coverage for Ubuntu packages. Use when the user wants to measure how much code is covered by tests, find uncovered code paths, or improve test coverage, especially for Rust packages.
---

# Coverage Analysis

## When to Use

- User wants to measure test coverage
- User asks "how well tested is this package?"
- User wants to find uncovered code paths
- User wants to prioritize new test writing

## Workflow

1. **Download source**: `get_source_package` or `scripts/download-source-pkg`
2. **Build with coverage**: `scripts/analyze-coverage <package> <series>`
3. **Review results**: Identify uncovered files/functions/lines
4. **Write tests**: Focus on highest-impact gaps first
5. **Re-verify**: Re-run coverage analysis

## Coverage for Rust Packages

Rust has excellent built-in coverage support via `cargo-llvm-cov` or the nightly `-Zinstrument-coverage` flag.

### Setting Up

```bash
# Install cargo-llvm-cov
cargo install cargo-llvm-cov

# Run with coverage
cargo llvm-cov --summary-only

# Generate HTML report
cargo llvm-cov --html

# For a specific test
cargo llvm-cov -- <test-name>
```

### For Debian-packaged Rust

In `debian/rules`, add coverage flags:
```makefile
export CARGO_INCREMENTAL=0
export RUSTFLAGS="-Zinstrument-coverage"
export LLVM_PROFILE_FILE="default_%p_%m.profraw"
```

Then use `scripts/analyze-coverage` to process the results.

## Coverage for C/C++ Packages

```bash
# Build with coverage flags
export CFLAGS="--coverage -g -O0"
export CXXFLAGS="--coverage -g -O0"
export LDFLAGS="--coverage"

# Build and run tests
make && make check

# Generate report
lcov --capture --directory . --output-file coverage.info
lcov --remove coverage.info '/usr/*' --output-file coverage.info
genhtml coverage.info --output-directory coverage-report
```

## Interpreting Results

| Metric | Good | Needs Work |
|---|---|---|
| Line coverage | >80% | <50% |
| Branch coverage | >70% | <40% |
| Function coverage | >90% | <60% |

Focus areas for improving coverage:
1. **Error handling paths** — often untested
2. **Edge cases** — empty inputs, maximum values, Unicode
3. **Public API surface** — every public function should have at least one test
4. **Integration points** — FFI boundaries, file I/O, network

## Output Format

`scripts/analyze-coverage` outputs JSON:
```json
{
  "package": "rustc",
  "series": "noble",
  "summary": {
    "lines_total": 50000,
    "lines_covered": 35000,
    "line_percent": 70.0,
    "branches_total": 10000,
    "branches_covered": 6000,
    "branch_percent": 60.0
  },
  "uncovered_files": [
    {"file": "src/lib.rs", "lines_total": 100, "lines_covered": 30, "uncovered_lines": [10, 11, 42, 43, 44]}
  ]
}
```

## Important Notes

- Coverage does not imply correctness — high coverage with poor tests is still poor quality
- For Rust, `cargo-llvm-cov` requires nightly toolchain; the stable `cargo-tarpaulin` is an alternative
- Always exclude vendored/generated code from coverage reports
