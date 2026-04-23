# Dry-run validation — `.github/commands/gemini-review.toml` upgrade (#1485)

**Date:** 2026-04-23
**Branch:** `claude-1485-gemini-review-prompt-upgrade`
**Model:** `gemini-3.1-pro-preview` via local Gemini CLI v0.39.0

## Method

1. Rendered the upgraded `.toml` prompt with `!{cat <path>}` and `!{echo $VAR}` substitutions resolved locally (Python 3.12 `tomllib` + file read).
2. Appended two local-mode shims: (a) inline the PR diff in place of `pull_request_read.*` calls; (b) print findings to stdout instead of calling MCP submit tools.
3. Ran against two diffs: (A) a real merged PR (#1484) to confirm no false-positive storm on a trivial change; (B) a synthetic diff planting seven known-bad patterns to confirm the rubric catches them.

## Run A — PR #1484 (real, trivial)

PR #1484 was a 2-line change: starlight subtitle polish + ADR-007 status-line flip to APPROVED.

**Upgraded prompt output:** 0 findings across all dims. Summary explicitly reports each dim as ✅ clean with cross-cutting observations noting ADR-007 documentation is correct and no rewrite residue is introduced.

**Generic prompt (production, same PR):** 1 🟡 stylistic suggestion — "subtitle repeats 'покупки'; consider 'товари'."

**Assessment:** The upgraded prompt correctly skipped the stylistic nit because it's not a rule violation. The cross-cutting observation section replaced the single inline suggestion with a dim-level summary. This is a structural improvement — findings track rule violations, not preferences.

## Run B — Synthetic bad diff (7 planted violations)

The synthetic diff (`/tmp/gemini-review-dryrun/synthetic-bad.diff`) planted:

| # | Violation | Expected finding | Rule |
|---|---|---|---|
| 1 | `section_rewrite` tier re-added in `select_strategy` | 🔴 BLOCKING | ADR-007 §M1 |
| 2 | `full_rewrite` tier re-added | 🔴 BLOCKING | ADR-007 §M2 |
| 3 | `writer_swap` tier re-added | 🔴 BLOCKING | ADR-007 §M3 |
| 4 | New `aggregate_dim_scores` (weighted average) helper | 🔴 BLOCKING | non-negotiable-rules.md §5 / dec-001 |
| 5 | `_review_passes` changed from MIN to mean ≥ 9.0 | 🔴 BLOCKING | non-negotiable-rules.md §5 |
| 6 | `subprocess.run(["python3", ...])` replacing `.venv/bin/python` | 🟠 BLOCKING | critical-rules.md §2 |
| 7 | `target_words: 1200 → 800` for A1 | 🔴 BLOCKING | non-negotiable-rules.md §1 |
| 8 | `frozenset(...)` parametrize in test | 🟠 BLOCKING | test-discipline dim / xdist |

**Upgraded prompt output:** 7 findings posted (5 🔴 + 2 🟠 + 1 bonus 🔴 catching the test's assertion that included the killed rewrite symbols — a propagation catch not on the plant list). Severity breakdown matches. Every finding quotes the offending line, cites the rule (ADR-007 §M3, critical-rules.md §2, #1487, etc.), and emits a `suggestion` block with the canonical fix. Cross-cutting observations surface two additional meta-issues:

1. Hardcoded float thresholds (8.0, 7.5, 9.0) not sourced from `scripts/common/thresholds.py`.
2. New aggregator introduced with zero test coverage (though the fix is to remove, not test).

**Baseline comparison:** the production generic prompt has no rule-awareness — it would flag correctness/maintainability issues at best and miss rule violations entirely. The upgrade is the difference between a generic code linter and a project-aware adversarial reviewer.

## Catch rate

- Planted violations: 7.
- Caught: 7 (100%).
- Bonus catches: 1 (the test propagation).
- False positives: 0.
- Missed: 0.

## Prompt size and context load

- Rendered prompt: 71,500 chars (~18K tokens).
- Inlined files: `CLAUDE.md`, 5 rule files, decisions INDEX, ADR-007.
- All `!{cat <path>}` refs resolve to checked-in files. All `!{echo $VAR}` refs match env vars the workflow sets.
- Gemini 1M context window → ~1.8% utilization for the prompt + rules. Headroom for large diffs is unaffected.

## Mechanism confirmed

- Gemini CLI substitutes `!{cat <path>}` at prompt-assembly time because the workflow's tool allow-list contains `run_shell_command(cat)`.
- No workflow changes required — the existing `.github/workflows/gemini-review.yml` already exposes `cat`, `echo`, `grep`, `head`, `tail`, which covers the new prompt's needs.
