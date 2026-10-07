# Source-tool CLI smoke (#9991)

`tests/test_source_ingest_entrypoints.py` computes the tracked CLI import
closure of `scripts.rag.source_query` and `scripts.wiki.slovnyk_me`, including
deferred imports and regular package initializers. Each CLI has two probes in
a fresh interpreter, from the repository root with inherited `PYTHONPATH`
removed:

- Module: import its dotted name without executing legacy main logic.
- File: replace cwd on `sys.path` with the script's directory, remove any
  repository-root entries, and execute `runpy.run_path(..., run_name="__main__")`
  with `--help`. The script's own main-block import setup runs. Successful
  `SystemExit(0)` from argparse help is accepted; other exits fail.

The file probe uses `__main__` because pytest's existing Cursor tripwire owns
`sitecustomize` and prepends it before child startup. A second temporary
`sitecustomize` would silently lose the offline guard. The wrapper installs
the audit hook directly while preserving the script import path. Direct file
and module `--help` launches also verify both urgent ingest entrypoints.

Each probe receives a fresh private temporary directory outside the checkout
through `TMPDIR`, `TEMP`, and `TMP`. The parent removes it on success, failure,
or timeout. This permits the standard library's temp-directory validation and
`filelock`'s temporary filesystem check to finish before testing the remaining
imports.

The audit hook blocks network, subprocesses (except local `git rev-parse`),
and filesystem writes or writable SQLite connections outside that directory.
Containment checks resolve symlinks and parent traversal; rename and link
operations must keep both paths inside it. Linux directory descriptors are
resolved through `/proc/self/fd` so private temporary-directory cleanup works;
unresolvable descriptors fail closed. Writable opens require absolute paths
because their audit event omits `dir_fd`. CLIs that ignore `--help`
remain classified failures rather than executing unrestricted main logic.
Each probe has a 15-second timeout. Guard-blocked rows are coverage limitations:
imports or main logic after the blocked operation remain unverified.
The round-c failure classes are preserved; write-blocked diagnostics retain
`IMPORT_SMOKE_BLOCKED_WRITE` and use the existing `other_import_failure` class,
alongside non-import startup failures.

`scripts/audit/bio_lit_cross_reference.py` parses arguments before running its
audit. Its `--help` exits without reading plans or writing the gap report;
invocation without arguments retains the existing audit and exit codes.

The baseline stores only repository-relative path, form, and failure class.
The observed set must equal its remaining rows: a new failure fails, and a
repaired CLI fails until its stale row is removed. Both urgent ingest CLIs
must remain clean and cannot be baselined. The inventory uses exact equality
on count, probe count, and a SHA-256 of sorted CLI paths, so growth, shrinkage,
and same-size substitutions all require review.

The round-e re-baseline retains 412 CLIs / 824 probes. Of the 30 probes that
previously stopped at temp-directory validation, 28 now pass; file launches of
`scripts/lexicon/runner/ulif_forms.py` and `scripts/tools/consultation_cli.py`
now reach their actual `ModuleNotFoundError` (`No module named 'scripts'`). The
bio audit's file probe also passes. Remaining failure counts are:

| Class | Round d | Round e | Delta |
| --- | ---: | ---: | ---: |
| `module_not_found` | 110 | 112 | +2 |
| `import_error` | 23 | 23 | 0 |
| `other_import_failure` | 52 | 21 | -31 |
| `environment_blocked_subprocess` | 7 | 7 | 0 |
| `environment_blocked_network` | 3 | 3 | 0 |
| `timeout` | 0 | 0 | 0 |
| Total | 195 | 166 | -29 |

The remaining failures, swallowed guard exceptions, and writes inside compiled
libraries that bypass Python audit hooks remain residual scope for the #9991
driver. A successful probe does not establish that no guard exception was caught
by the CLI, or that a compiled library performed no writes.

After reviewing an inventory change, run the exact refresh command printed
by the freshness failure. It uses the test interpreter, including the shared
interpreter in dispatch worktrees. In an ordinary checkout the command is:

```bash
.venv/bin/python tests/test_source_ingest_entrypoints.py --refresh-denominator
```

This option updates only the inventory snapshot; it never adds or removes
failure rows. Verify changed rows individually and run the smoke afterward:

```bash
.venv/bin/python -m pytest tests/test_source_ingest_entrypoints.py -n 2 -q
```

Use the task-prescribed shared interpreter instead of a worktree-local venv
in dispatch worktrees. Scratch mutation checks belong in the task's managed
scratch directory, never in the tracked checkout. The smoke remains in the
required CI Gate tier, with repository-wide selection and batches of three
CLIs (six bounded probes) per test.
