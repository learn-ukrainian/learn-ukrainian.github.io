# Test Quality Best Practices

> **Scope:** every new or changed test in this repository (Python and JS/TS). Binding
> summary: `agents_extensions/shared/rules/workflow.md` § Tests (#11226).

---

## The rule

**A new test must be able to fail for a real defect class; name that class in the test
name or docstring.**

D1–D7 are "do not write". K1–K13 are "must test". K (protected) is evaluated first and
overrides every D class. Unresolved protection means keep the test.

Protection is for demonstrated behaviour, not blanket immunity for a directory; but a
K-tagged test is never deleted by the pruning pipeline, only proposed for critical-seat
review.

## Do not write (D1–D7)

All qualifiers of a class must hold.

- **D1** asserts only what a runtime-enforced schema/validator already rejects AND another
  kept test exercises that rejection. Python annotations are not runtime enforcement;
  schema-rejection tests (e.g. `tests/api/test_fleet_board_v1.py:80-110`) stay.
- **D2** asserts only that a mock was called, where the call is not itself the contract.
  Interaction contracts stay: dispatch destination, read-only access, no network/process
  launch, exactly-once cleanup (e.g. `tests/test_mcp_sources_server.py:823-827`).
- **D3** import/smoke test duplicated by a behaviour test AND not a clean-process
  startup/packaging test (`tests/test_delegate_import_clean.py:11-28` and
  `tests/test_source_clis_entrypoint.py:44-58` stay).
- **D4** duplicate case: same semantic input partition, not merely the same code
  path/assert shape (Unicode NEL/LS/PS cases in `tests/test_cli_tail_timeouts.py:120-140`
  stay).
- **D5** speed claim (wall-clock "is fast") or fixed real sleep to force ordering.
  Bounded-liveness/stall guards and documented budgets stay until an equivalent
  replacement passes (`tests/api/test_context_cost.py:178-198`,
  `tests/api/test_fleet_board_ops.py:92-120`). Deterministic-clock tests are never
  "timer" tests.
- **D6** incidental wording/format assertions. Required CLI help sections and exit-code
  descriptions (`agents_extensions/shared/rules/cli-help-standard.md:11-26`; e.g.
  `tests/hygiene/test_retention_engine_cli_help.py:19-24`) and operational messages that
  are contracts stay.
- **D7** retired path, only with verified absence of supported callers,
  compatibility/migration/rollback use and historical readers; a governing doc alone is
  not enough.

## Must test (K1–K13, protected)

- **K1** security code (hooks, launchers, credentials, admission, sandbox, opsec scans,
  write/merge guards).
- **K2** shipping gates and audits.
- **K3** Ukrainian-language correctness (VESUM/sources, stress, morphology,
  Russian-shadow, word-card certification).
- **K4** persistence, migrations, storage topology, dataset integrity/export, lexdata.
- **K5** orchestration lifecycle and deterministic race fixes.
- **K6** external-format parsing and protocol translation.
- **K7** any identified regression test, any age.
- **K8** fixture mirrors for rules/prompt deploy checks.
- **K9** application lifecycle, resource cleanup (e.g.
  `tests/api/test_context_cost.py:149-175`), bounded liveness, resource/call-count
  budgets.
- **K10** public CLI/API/output contracts, clean-process packaging/startup,
  dependency-patch guards, platform/environment isolation.
- **K11** test manifests/registries that name test files or node ids
  (`tests/test_repo_wide_marker_invariant.py` `KNOWN_REPO_WIDE_*`,
  `scripts/ci/history-tests.txt` + `scripts/ci/split_tests.py:201-203`,
  `scripts/ci/components.json`, `scripts/ci/pytest_shards.py` serial/perf lists and
  `SELECTION_DIGEST`, workflow path lists, `scripts/hygiene/store_access_baseline.json`,
  `scripts/hygiene/lint_tmp_paths.py`): a deletion must update the manifest in the same PR
  or is refused.
- **K12** repo-wide AST/source-tree invariant scanners (`repo_wide` / `repo_invariant`
  markers).
- **K13** learner-facing frontend, e2e, accessibility, locale purity, MDX/Astro build
  contracts (`site/e2e`, `site/tests`); JS/TS deletion is out of scope until a TS rule set
  exists.

## In review

The `local-code-review` checklist (Step 5) asks every new test to name the defect class
it can fail for, and reports low-signal patterns as non-blocking review diagnostics.
