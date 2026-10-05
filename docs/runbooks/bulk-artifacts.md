# Bulk Artifacts and Large File Guard Runbook

## Overview
Repository policy prevents committing blobs > 5 MB (5,242,880 bytes) directly to Git. The CI guard (`scripts/ci/check_large_files.py`) enforces this in pull request and merge queue workflows.

## Remediating Guard Failures
When `check_large_files.py` fails with an unallowlisted oversized blob:
1. **Move to artifact store (Recommended)**: Use `scripts/storage/artifacts.py` to manifest and manage bulk data out of Git:
   ```bash
   .venv/bin/python -m scripts.storage.artifacts manifest build --group <group> --pre HEAD
   ```
2. **Add an allowlist entry**: If the blob is canonical source that must stay tracked, add an entry to `scripts/ci/large_files_allowlist.txt` with exact path, size in bytes, and reason.

## Allowlist Format
`scripts/ci/large_files_allowlist.txt` uses a tab-separated text format:
`<repository-relative-path>\t<size-in-bytes>\t<reason>`
- Lines starting with `#` and empty lines are comments/ignored.
- Exact repository-relative path match (no wildcards or prefixes).
- Recorded sizes represent provenance; modifications to allowlisted paths remain exempt.
- Seed or refresh from `origin/main` with `.venv/bin/python scripts/ci/check_large_files.py --seed-allowlist`.
