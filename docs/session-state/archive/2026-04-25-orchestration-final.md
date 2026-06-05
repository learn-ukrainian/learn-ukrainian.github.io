# Session Handoff — 2026-04-25 orchestration final

> **All 17 EPIC #1550 items addressed in code. 7 PRs merged.** Unit 6
> verification (the actual a1/1 build) blocked by an environmental
> mismatch in dispatched Codex workers — `shutil.which("claude")`
> resolves to a binary < 2.1.116 inside the sandbox even though your
> local shell has 2.1.119. **You can run the verification locally;
> your shell sees the right binary.**

## What landed (all merged to main)

| PR | Unit | Subject |
|---|---|---|
| inline `534d28ff1b` | API hotfix | uvicorn AccessFormatter — direct to main |
| #1554 | API hardening v2 | Codex regression test + sweep + docs (`tests/api/test_logging_config.py`, `docs/MONITOR-API.md`) |
| #1551 | Unit 2 writer | 5 prompt rules: `<phonetic-notation>`, `<no-meta-language>`, `<speaker-labels>`, `<dialogue-not-lecture>`, `<no-stress-marks>` |
| #1552 | Unit 1 reviewer | Stress pre-strip + `{learner_level}`, `{module_index}`, `{module_total}` injection per dim. `<pedagogical-stage>` (Dialogue M1-M3). `<factual-scope>` (Factual). |
| #1556 | Unit 3 activities | INLINE_MIN/MAX dynamic from markers, plan vocab + 33 letters (a1/1), letter_module flag, pre-validate gate, type-list invariants. Required fix-up commit `a21033d068` for non-dict activities crash. |
| #1557 | Unit 5 exercise_quality | order → set-membership; verified `nf_9b2ce3f5744c855b` no longer raised |
| inline `73c1db2c06` | plan completion | `letter_module: true` added to a1/2 + a1/3 plans (Codex did only a1/1) |
| #1558 | Unit 4 audit/pipeline | 575/-88 across 11 files. Two-layer config map. *_MAX → soft WARN. letter_module exception in audit gates. min floors raised. Cross-layer alignment. 242-line invariant test suite. |

**Main is at `5844a70928`.**

## Items checked off EPIC #1550 (17/17)

- [x] A1 INLINE_MIN/MAX dynamic from markers (#1556)
- [x] A2 Configs MIN-not-MAX semantics; *_MAX → soft warn (#1558)
- [x] A3 Forbidden vs Recommended type-list disjointness (#1556 + #1558 invariants)
- [x] A4 `{MIN_TYPES_UNIQUE}` floor raised from 0 to 4 for A1 (#1558)
- [x] A5 33 alphabet letters in a1/1 plan vocab (#1556)
- [x] A6 Seminar types not in non-seminar prompts (verified absent during trace; no change needed)
- [x] A7 Topic-specific patterns at lines 538-630 — N/A (file is 352 lines, stale handoff item)
- [x] A8 exercise_quality order → set-membership (#1557)
- [x] B1 Dialogue dim level-aware for A1 M1-M3 (#1552)
- [x] C1 Stress pre-strip + defensive prompt rule (#1552)
- [x] C2 Cyrillic-only phonetic notation (#1551)
- [x] C3 No drafting-leak meta-language (#1551)
- [x] C4 Speaker labels mandatory when plan names speakers (#1551)
- [x] C5 Dialogue is conversation, never grammar lecture (#1551)
- [x] D1 Strict grounding rule + pre-validation gate (#1556)
- [x] D2 100% required-vocab coverage obligation (#1556)
- [x] D3 Activity validator schema enforcement (#1556 pre-validate)

## What's still in your working tree (preserved per handoff)

The original a1/1 manual content patches that the previous handoff said
DO NOT CLOBBER are still in place:

```
M activities/sounds-letters-and-hello.yaml
M curriculum/l2-uk-en/a1/activities/sounds-letters-and-hello.yaml
D curriculum/l2-uk-en/a1/audit/sounds-letters-and-hello-audit.md
M curriculum/l2-uk-en/a1/build-stats.jsonl
M curriculum/l2-uk-en/a1/research/sounds-letters-and-hello-knowledge-packet.md
M curriculum/l2-uk-en/a1/review/sounds-letters-and-hello-review-r1.md
M curriculum/l2-uk-en/a1/review/sounds-letters-and-hello-review-r2.md
D curriculum/l2-uk-en/a1/review/sounds-letters-and-hello-review-r3.md
M curriculum/l2-uk-en/a1/review/sounds-letters-and-hello-review.md
M curriculum/l2-uk-en/a1/sounds-letters-and-hello.md
D curriculum/l2-uk-en/a1/status/sounds-letters-and-hello.json
M curriculum/l2-uk-en/a1/vocabulary/sounds-letters-and-hello.yaml
M curriculum/l2-uk-en/stuck-modules.yaml
```

These are intentional. After your forced rebuild produces canonical
output, you can `git restore curriculum/` to clear them.

## Unit 6 verification — TWO distinct failure modes uncovered

### Phase A (Claude writer / Codex reviewer): CLI gate

Two Phase A attempts (PR #1559 closed, PR #1560 closed) terminal-failed
at `step_skeleton` with:

```
RuntimeError: Claude CLI < 2.1.116 inherits known quality regressions
fixed on 2026-04-23. Upgrade with: npm install -g @anthropic-ai/claude-cli@latest
```

The gate is at `scripts/agent_runtime/adapters/claude.py:112`. It probes
the binary returned by `shutil.which("claude")` and rejects < 2.1.116.

### What's broken

In MY (this session's) shell:
- `which claude` → `/Users/krisztiankoos/.npm/_npx/97540b0888a2deac/node_modules/.bin/claude`
- `claude --version` → `2.1.119` ✅
- `/opt/homebrew/bin/claude` → 2.1.119 ✅

I deleted a stale npx cache `becf7b9e49303068` (had 2.1.89) between v1
and v2. v2 still failed the same way.

The dispatched Codex worker must be finding an older `claude` binary I
can't see from outside the sandbox. Without the ability to introspect
the worker's PATH, I can't pinpoint which binary it resolves.

### Phase B (gpt-5.5 writer / Claude reviewer): different bug — plan file vanishes

PR #1561 (closed). Phase B got MUCH further than Phase A — the gpt-5.5
writer completed chunked prose generation, failed contract compliance
on attempt 1, then PASSED on attempt 2. So the gpt-5.5 writer works.

Build then proceeded through `Step 5a: HONESTY ANNOTATE` ✅, `Step 5b:
EXERCISES (skipped)`, then `Step 5e: ACTIVITIES`. Activity YAML generated
successfully (7 inline + 7 workbook). Crash at the state save:

```
File ".../v6_build.py", line 7557, in step_activities
File ".../v6_build.py", line 1304, in _save_v6_state
File ".../v6_build.py", line 297, in _write_v6_state_atomic
File ".../v6_build.py", line 302, in _current_alignment_manifest
File ".../alignment_manifest.py", line 441, in compose_manifest
File ".../alignment_manifest.py", line 247, in _canonical_plan_hash
File "pathlib.py", read_text → io.open
FileNotFoundError: '...curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml'
```

**Root cause: bug in `scripts/build/alignment_manifest.py:_canonical_plan_hash`.**
The function reads the plan via `read_text()` with NO `.exists()` check:

```python
def _canonical_plan_hash(level: str, slug: str) -> str:
    plan_data = yaml.safe_load(_plan_path(level, slug).read_text("utf-8"))
    canonical_yaml = yaml.safe_dump(plan_data, sort_keys=True, allow_unicode=True)
    return _sha256_bytes(canonical_yaml.encode("utf-8"))
```

This is invoked indirectly on EVERY state save via `compose_manifest →
_canonical_plan_hash` (alignment_manifest.py:441). Unit 4 introduced or
heavily reworked this code path.

**The deeper question:** activity generation READ the plan successfully
moments before — so the file existed at that point. Then it disappeared
between activity-write and state-save (sub-second timeframe). Either:

1. The dispatched Codex sandbox has eventually-consistent file I/O (possible — `--mode danger` uses sandbox-exec on macOS).
2. Some intermediate code in the v6_build pipeline deletes/moves the plan (I traced `_force_reset_module` and `_clean_build_artifacts` — neither touches `plans/`).
3. Some Unit 4 code path I missed.

**Recommended fix path** (your call to dispatch Codex on this):
- Defensive: add `.exists()` check in `_canonical_plan_hash` — if missing, return `""` or skip stamping. Stops the symptom.
- Investigative: add logging at every state save (with file existence + mtime) to trace WHEN the plan disappears. Find the actual delete site.

Phase B *did* prove gpt-5.5 writes passable prose — contract compliance
passed on attempt 2. Whether the prose quality is comparable to Claude's
output is unmeasured (no MDX captured because of the crash).

### The clean fix path

**You can run Unit 6 yourself locally** because your shell has the right
CLI. Two builds, ~20 min each:

```bash
# Phase A — baseline (current default)
.venv/bin/python scripts/build/v6_build.py a1 1 --force \
    --writer claude-tools --reviewer codex-tools \
    2>&1 | tee /tmp/a1-1-phaseA-baseline.log
cp curriculum/l2-uk-en/a1/sounds-letters-and-hello.md /tmp/a1-1-baseline.md

# Phase B — gpt-5.5 writer experiment
.venv/bin/python scripts/build/v6_build.py a1 1 --force \
    --writer codex-tools --reviewer claude-tools \
    2>&1 | tee /tmp/a1-1-phaseB-experiment.log
cp curriculum/l2-uk-en/a1/sounds-letters-and-hello.md /tmp/a1-1-experiment.md

# Compare dim scores from the two status JSONs + prose excerpts.
# Decide winner by the rubric:
#   1. Both pass MIN ≥ 8 → higher MIN dim wins
#   2. Only one passes → that one wins
#   3. Neither passes → escalate (deeper problem)
#   4. MIN tie ±0.3 → fewer convergence rounds
#   5. Still tied → manual eyeball

# Phase C — winner builds a1/2 + a1/3
.venv/bin/python scripts/build/v6_build.py a1 2 --force \
    --writer {WINNER_W} --reviewer {WINNER_R} &
.venv/bin/python scripts/build/v6_build.py a1 3 --force \
    --writer {WINNER_W} --reviewer {WINNER_R} &
wait
```

### Alternative: dispatched-environment debugging

If you want to keep verification dispatched, the diagnostic step is:

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex --task-id codex-debug-claude-cli \
    --mode danger --worktree .worktrees/dispatch/codex/codex-debug-claude-cli \
    --prompt "Run inside the worktree: 'which claude', 'claude --version', \
        and 'env | grep -i path'. Report verbatim. Do nothing else."
```

That tells us what binary the dispatched Codex actually finds.

## Other open work parallel to this session

- PR #1555 — wiki retrieval overhaul step 0 (other agent's work) — leave alone
- Open issues #1481, #1480, #1451, #1435, #1398, #1377 — coding/infra, not blocking

## Anti-checklist

1. ❌ Don't manually patch a1/1 content — the pipeline must produce passing modules
2. ❌ Don't touch `wiki/` or PR #1555 — separate agent
3. ❌ Don't touch `.worktrees/codex-interactive` — your local work
4. ❌ Don't skip the explicit `--writer X --reviewer Y` flags on builds
5. ❌ Don't auto-merge any PRs

## Next session entry point

1. Read this file.
2. `gh issue view 1550` — 17/17 checked items + final orchestration status comment.
3. Run Unit 6 Phase A + Phase B locally per the script above.
4. Compare and decide winner.
5. Run Phase C (a1/2 + a1/3 with winner) when satisfied.
6. Update EPIC #1550 with winner verdict + close.
