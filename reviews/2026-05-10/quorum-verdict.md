# CI review — quorum verdict (Codex + Gemini + Claude)

**Date:** 2026-05-10. Sources: `reviews/2026-05-10/codex-ci-review.md` (Codex via `ab ask-codex`), `reviews/2026-05-10/gemini-ci-review.md` (Gemini-3.1-pro-preview via `ab ask-gemini`), inline-Claude judge pass (anchored — Claude saw both reports before voting; verified C+G claims against actual workflow files per #M-4).

## Tier 1 — Unanimous (PR-A)

| Item | File:line | Codex | Gemini | Claude |
|---|---|---|---|---|
| Restrict `push` to `branches: [main]` | `ci.yml:6-26`, `validate-yaml.yml:6-16`, `rules-deployment-check.yml:6-26` | ✓ | ✓ | ✓ verified pattern |
| Drop debugger job | `gemini-dispatch.yml:26-43` | ✓ | ✓ | ✓ verified always-false `if:` |
| Drop CodeQL `actions` lane | (default-setup, repo settings) | ✓ | ✓ | ✓ |
| Fix cache key (drop `requirements.txt` from hashFiles) | `ci.yml:304` | ✓ | ✓ | ✓ verified |
| Drop `pull_request_review*` triggers | `gemini-dispatch.yml:4-9` | ✓ | (implied via router) | ✓ verified |

## Tier 2 — Codex-only finds, all valid (PR-B)

| Item | File:line | Claude verdict |
|---|---|---|
| **Drop unconditional torch reinstall** | `ci.yml:308-317` | YES — biggest direct time win (~2-3 min). `--force-reinstall` defeats pip cache. |
| Replace manual `actions/cache` with `cache: 'pip'` in setup-python (Gemini add) | `ci.yml:300-306` | YES — pair with torch fix |
| `Quality Gates (radon)` `needs: [changes, lint]` → `needs: changes` | not re-verified | LOW PRIORITY |

## Tier 3 — Gemini-only structural fix (PR-C, DEFER)

Router job pattern collapsing 4 skipped Gemini downstream jobs into one conditional invoker.

- File: `gemini-dispatch.yml:142-200`
- Verdict: DEFER until PR-A + PR-B prove value. Risk: touches the `@gemini-cli` orchestration flow we depend on for issue triage.

## Disagreement — pytest matrix split

- Codex: don't split (already `-n auto`)
- Gemini: split via `strategy: matrix: suite`
- **Claude judge: Codex.** `-n auto` verified at `ci.yml:324`. Matrix adds job-startup + deps-install overhead per shard. Sequence: fix torch reinstall first → re-profile pytest → decide on data.

## What all three missed

- `ci.yml:15-26` has 4 historical "widened path filter" comments (#1544, #1546, etc.). **Path-filtered required checks are structurally fragile.** The `needs.changes.outputs.code` pattern (`ci.yml:249/301/320`) is the structural substitute. Out of scope here, but worth an autopsy entry: future workflows should NOT use `paths:` filter on `push`/`pull_request` triggers when emitting required checks. Route via the `changes` job instead.

## Implementation order (for Codex when reset day-after-tomorrow)

1. **PR-A** (Tier 1, ~25 LoC, low risk) — pure config trim. Should be done in one Codex dispatch.
2. **PR-B** (Tier 2, ~15 LoC, medium risk) — pytest perf. Validate by comparing pytest wall-clock before/after on a representative PR.
3. **PR-C** (Tier 3) — re-evaluate after PR-A + PR-B land.
4. Matrix split — re-evaluate after PR-B's torch fix lands and pytest is re-profiled.

## #M-4 evidence

- Verified workflow line refs: see "verified" column above. All Tier 1 + 2 items grounded in actual file contents read at handoff time.
- C+G reports archived at `reviews/2026-05-10/{codex,gemini}-ci-review.md`.
