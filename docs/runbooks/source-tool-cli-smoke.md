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
must remain clean and cannot be baselined. The inventory saves sorted CLI paths,
their count, probe count, and SHA-256. Freshness validates the saved snapshot and
requires every saved path to remain in the discovered inventory. A removal or
substitution fails even when additions leave the total count unchanged or larger.
Reviewed removals require the explicit refresh command below.

Newly discovered CLIs automatically receive both probes and do not require a
snapshot edit. Passing additions are accepted; a failing addition is a new
failure row and fails the ratchet. Two PRs adding different CLIs can therefore
share the same saved inventory and both pass on their combined merge tree.

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

After merging #10058's shared-configuration import fix, round g removes ten
repaired file-form `import_error` rows under `scripts/audit/`:
`apply_source_inventory_promotion.py`, `freeze_benchmark.py`,
`generate_activity_quality_queue.py`, `paronym_residual_audit.py`,
`probe_uk_writing_score.py`, `qg_bakeoff.py`, `qg_corpus_report.py`,
`qg_seat_decision.py`, `qg_tier2_canary_check.py`, and
`relation_residual_audit.py`. The remaining baseline is 156 rows:
112 `module_not_found`, 13 `import_error`, 21 `other_import_failure`,
7 `environment_blocked_subprocess`, and 3 `environment_blocked_network`.
The saved inventory stays at 412 CLIs / 824 probes; the merged tree discovers
413 CLIs / 826 probes, and the additional CLI is probed automatically.

The initial round-g run reports `1 failures` in each batch beginning with
`generate_activity_quality_queue.py` and `paronym_residual_audit.py`. These
are batch totals for neighboring file probes, not new failures of the repaired
CLIs. `generate_daily_pool.py` fails at its `scripts.audit.daily_cefr` import,
and `plan_source_inventory_promotion.py` fails at its
`scripts.audit.generate_source_inventory_review_candidates` import; both
raise `ModuleNotFoundError: No module named 'scripts'`. Their existing
`module_not_found` rows and entrypoint sources are unchanged from the
previously approved head. No failure rows are added or reclassified.

The remaining failures, swallowed guard exceptions, and writes inside compiled
libraries that bypass Python audit hooks remain residual scope for the #9991
driver. A successful probe does not establish that no guard exception was caught
by the CLI, or that a compiled library performed no writes.

After reviewing an inventory removal, run the exact refresh command printed
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
scratch directory, never in the tracked checkout. Round g verifies the existing
`qg_seat_decision.py` batch passes in an unmodified scratch copy, then inserts
`raise ImportError("REGRESSION_SENTINEL_9991_G")` after that entrypoint's future
import. The same test fails with exactly two new `import_error` rows, one for
each invocation form, and no stale rows. This mutation requires no change to
the ratchet or baseline. The smoke remains in the
required CI Gate tier, with repository-wide selection and batches of three
CLIs (six bounded probes) per test.
