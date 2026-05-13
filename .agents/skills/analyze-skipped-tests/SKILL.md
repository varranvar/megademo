---
name: analyze-skipped-tests
description: Analyze skipped or failing autopkgtest results for Ubuntu packages. Use when the user wants to understand why tests are skipped, investigate test failures, or improve test reliability.
---

# Analyze Skipped Autopkgtests

## When to Use

- User asks why autopkgtests are skipped for a package
- User wants to investigate test failures
- User wants to improve test reliability

## Workflow

1. **Fetch results**: `get_autopkgtest_results` MCP tool to get current results
2. **Identify issues**: Focus on `skipped`, `failed`, and `flaky` statuses
3. **Categorize skip reasons**: See the categories below
4. **Propose fixes**: Target the most impactful issues first
5. **Instruct user**: For actions requiring Launchpad write access

## Skip/Failure Categories

### Infrastructure Issues
| Reason | Fix |
|---|---|
| `needs-root` not available | Request `isolation-machine` or `needs-root` restriction |
| `isolation-machine` unavailable | Request machine with isolation support |
| Testbed setup timeout | Optimize test setup; reduce dependencies |
| Worker OOM | Reduce memory usage or request larger instance |

### Dependency Issues
| Reason | Fix |
|---|---|
| Missing build dependency | Add to `Depends:` in `debian/tests/control` |
| Version mismatch | Pin dependency version or update test |
| Circular dependency | Restructure test to avoid cycle |

### Test Code Issues
| Reason | Fix |
|---|---|
| Flaky test | Add `flaky` restriction or improve test reliability |
| Hardcoded paths | Use `$AUTOPKGTEST_TMP` or `$HOME` for temp files |
| Race condition | Add proper synchronization or serialization |
| Missing cleanup | Add cleanup in trap handler |

### Rust-Specific Issues
| Reason | Fix |
|---|---|
| `allow-stderr` missing | Add restriction to `debian/tests/control` |
| Network access required | Mock network calls or use `needs-internet` hint |
| Cargo cache issues | Clean `CARGO_HOME` before test |
| ThreadSanitizer false positives | Add `TSAN_OPTIONS="suppressions=..."` |

## Interpreting Autopkgtest Status

| Status | Meaning |
|---|---|
| `pass` | All tests passed |
| `fail` | One or more tests failed |
| `skipped` | Test was not run (see reason) |
| `tmpfail` | Temporary infrastructure failure (retry) |
| `flaky` | Inconsistent results across runs |

## Important Notes

- `tmpfail` results should be retried — they indicate infrastructure problems, not code problems
- For SRU (Stable Release Update) migrations, autopkgtest results directly affect whether a package migrates from `-proposed` to the release pocket
- The agent cannot trigger re-runs. Instruct the user: `ssh adt@autopkgtest.ubuntu.com -- <release> <package> <arch>`
- When proposing test fixes, always include a diff of `debian/tests/control` and any test scripts
