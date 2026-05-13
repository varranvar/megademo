---
name: sanitizer-builds
description: Build packages with sanitizers (ASan, UBSan, TSan) to find memory errors, undefined behavior, and data races. Use when the user wants to find and fix memory safety issues, especially in C/C++ and Rust packages.
---

# Sanitizer Builds

## When to Use

- User wants to find memory safety issues in a package
- User asks about address sanitizer, undefined behavior, or thread sanitizer results
- User wants to harden a package against memory errors

## Sanitizer Overview

| Sanitizer | Flag | Finds | Compatible With |
|---|---|---|---|
| ASan (Address) | `-fsanitize=address` | Buffer overflows, use-after-free, double-free, leaks | UBSan |
| UBSan (Undefined Behavior) | `-fsanitize=undefined` | Signed overflow, null deref, alignment, shift | ASan, TSan |
| TSan (Thread) | `-fsanitize=thread` | Data races, deadlocks | UBSan only |
| MSan (Memory) | `-fsanitize=memory` | Reads of uninitialized memory | None (standalone) |

**Important**: ASan and MSan are mutually exclusive. ASan and TSan are mutually exclusive.

## Workflow

1. **Download source**: `get_source_package` or `scripts/download-source-pkg`
2. **Build with sanitizer**: `scripts/run-sanitizer-build <package> <series> <sanitizer>`
3. **Parse output**: Sanitizer errors appear in build/test output
4. **Fix issues**: Apply targeted source fixes
5. **Re-verify**: Re-run sanitizer build to confirm

## Interpreting Sanitizer Output

### ASan Example
```
==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x...
    #0 0x... in function_name file.c:42
    #1 0x... in caller file.c:100
```
→ Fix: Check buffer bounds at `file.c:42`, ensure proper allocation size

### UBSan Example
```
runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
```
→ Fix: Use wider type (`int64_t`) or check for overflow before operation

### TSan Example
```
==================
WARNING: ThreadSanitizer: data race (pid=12345)
  Write of size 4 at 0x... by thread T2:
    #0 function_a file.c:50
  Previous read of size 4 at 0x... by thread T1:
    #0 function_b file.c:80
```
→ Fix: Add mutex/atomic to protect the shared variable

## Rust-Specific Notes

- Rust packages already get significant protection from the borrow checker
- Sanitizers are still useful for:
  - `unsafe` blocks
  - FFI / C interop
  - Logic errors that the borrow checker doesn't catch
- For Rust, use: `RUSTFLAGS="-Zsanitizer=address"` (nightly) or CFLAGS for native deps
- Many Rust packages use C libraries via `*-sys` crates — these benefit most from ASan

## Container Setup

```bash
scripts/container-setup noble
scripts/run-sanitizer-build rustc noble asan
scripts/run-sanitizer-build rustc noble ubsan
```

## Important Notes

- Sanitizer builds are significantly slower and use more memory
- ASan adds ~2x memory overhead; TSan adds ~10x
- False positives are rare but possible — verify each finding
- Some packages may need `--sanitize=undefined` split from `--sanitize=address` due to interactions
