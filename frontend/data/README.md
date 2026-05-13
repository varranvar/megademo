# Analysis Data Directory

This directory is the **only** location tools are permitted to write their output.

## Convention

Each tool has its own subdirectory:

```
data/
  bug-triage/
    manifest.json
    hello-2024-01-01.json
    ...
  vulnerability-analysis/
    manifest.json
    ...
```

### manifest.json
Each tool subdirectory should contain a `manifest.json` listing the analysis files it has produced:

```json
[
  "hello-2024-01-01.json",
  "world-2024-01-02.json"
]
```

The frontend uses these manifests to discover available runs.
