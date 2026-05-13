---
name: fix-copyright
description: Find and fix outdated or inaccurate debian/copyright files in Ubuntu packages. Use when the user wants to verify copyright accuracy, update license information, or fix DEP-5 compliance issues, especially for Rust packages with many vendored dependencies.
---

# Fix debian/copyright

## When to Use

- `debian/copyright` is outdated or inaccurate
- Lintian reports `copyright-file-out-of-date`
- New upstream version added/removed files
- User wants to audit license compliance
- Rust package with many crate dependencies

## Workflow

1. **Fetch current copyright**: `get_copyright_file` MCP tool
2. **Download source**: `get_source_package` to get the source tree
3. **Scan source files**: `scripts/analyze-copyright <source-dir>`
4. **Compare**: Identify mismatches between actual licenses and `debian/copyright`
5. **Fix**: Update `debian/copyright` in DEP-5 format
6. **Verify**: Run lintian to check for remaining issues

## DEP-5 Format (Machine-Readable debian/copyright)

```
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: serde
Source: https://crates.io/crates/serde

Files: *
Copyright: 2017 David Tolnay <dtolnay@gmail.com>
License: MIT OR Apache-2.0

Files: src/impls.rs
Copyright: 2017 David Tolnay <dtolnay@gmail.com>
           2019 Serde Contributors
License: MIT OR Apache-2.0

License: MIT
 [MIT license text]

License: Apache-2.0
 [Apache-2.0 license text]
```

## Common Issues in Rust Packages

| Issue | Fix |
|---|---|
| Missing entries for new crate files | Add `Files:` stanza for new files |
| Stale year ranges (e.g., `2017-2023`) | Update to include current year if files were modified |
| Wrong license (MIT vs Apache-2.0) | Check actual `LICENSE-*` files in upstream crate |
| Missing `Upstream-Name` or `Source` | Add from `Cargo.toml` `name` and `repository` fields |
| Vendored dependencies not listed | Add entries for each vendored crate with correct license |
| `Files-Excluded` not matching repack | Update to match `debian/copyright` `Files-Excluded` |

## Using analyze-copyright

```bash
scripts/analyze-copyright /tmp/rustc/rustc-1.75.0
```

Output (JSON):
```json
{
  "source_dir": "/tmp/rustc/rustc-1.75.0",
  "files_scanned": 1500,
  "licenses_found": {
    "MIT": 800,
    "Apache-2.0": 700,
    "BSD-3-Clause": 50
  },
  "copyright_holders": {
    "David Tolnay": 500,
    "The Rust Project Developers": 400
  },
  "mismatches": [
    {
      "file": "src/new_feature.rs",
      "declared_license": null,
      "actual_license": "MIT",
      "actual_copyright": "2024 Jane Doe",
      "suggestion": "Add Files: src/new_feature.rs stanza"
    }
  ],
  "orphaned_entries": [
    {
      "files_pattern": "src/removed_module.rs",
      "suggestion": "Remove: file no longer exists in source"
    }
  ]
}
```

## Important Notes

- Always preserve existing copyright holders — never remove someone
- For Rust packages, dual-licensing (MIT OR Apache-2.0) is the norm
- `debian/copyright` must cover every file in the source tarball
- Use `Files-Excluded` in `debian/copyright` to document files removed during repacking
- When in doubt about a license, check the upstream `Cargo.toml` `license` field
