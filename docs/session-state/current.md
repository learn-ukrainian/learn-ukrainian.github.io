# Session handoff — 2026-04-14 evening close

Context at 75% of 1M window. Handing off before compaction.

## State on main (HEAD: `d8eb7f3d3`)

Recent commits this session:
- `d8eb7f3d3` feat(claude): PostToolUse context-monitor hook with 75/85/95% handoff tiers
- `e1806f9c2` feat(v6): plateau-aware heal loop + auto-plan-patch, plus insert_after fix (#1252 #1253 #1254 #1255)
- `357f6bb2b` fix(audit): improve ACTIVITY_ORDER violation message formatting (#1252)
- `fb3d44258` fix(contract): match bare activity types against descriptive writer IDs (#1251)

## Closed this session

- **#1251** ACTIVITY_ORDER validator bug (bare types vs descriptive IDs) — shipped + tested
- **#1252** plateau-aware heal loop + auto-plan-patch + insert_after parser — shipped monolithically by Codex after I mistakenly dispatched it as one big task (lesson: split Codex tasks ≤10 min going forward)
- **#1253 / #1254 / #1255** sub-issues — closed as superseded by #1252 commit (filed AFTER Codex had actually already finished)

## Running background tasks

None. All cleared.

## Gemini adversarial review findings for commit e1806f9c2 (`review-1252` task — DONE)

Full report at `batch_state/tasks/review-1252.result`. Must-fix before user runs real-module validation:

**[CRITICAL] plan_patch.py — missing protected-field guard**
- `apply_plan_patch_response` applies any `path` the LLM hallucinates. The prompt says "don't touch slug/level/word_target/version" but nothing enforces it. Hallucinated `path: word_target, value: 100` would silently rewrite a plan's foundational constraint.
- Fix: explicit blocklist of paths (`slug`, `level`, `word_target`, `version`, `track`, `num`) OR allowlist of permitted fields (`content_outline`, `dialogue_situations`, `activity_hints`, `vocabulary_hints`) before `_set_path`.

**[MAJOR] plan_patch.py — non-atomic write to plan.yaml**
- `plan_path.write_text(yaml.safe_dump(...))` is not atomic. Kill mid-write → zero-byte or truncated plan.yaml → next build explodes.
- Fix: reuse `_write_v6_state_atomic` pattern (tempfile + `os.replace`) from `v6_build.py`.

**[MAJOR] plan_patch.py — prompt injection via f-string interpolation**
- `build_plan_patch_prompt` f-strings in `plan_text` and `complaints` without control-tag stripping or literal block wrapping. Plan or reviewer text containing `===PLAN_PATCH_START===` or control syntax would hijack Gemini's parser.
- Fix: import `_format_prompt_literal_block` and `_strip_prompt_control_tags` from `v6_build.py` and wrap untrusted artifacts.

**[MAJOR] test_plan_patch.py — lenient mocks, missing validation paths**
- Lambda `(True, raw_response)` tests only happy + noop paths. No test for rejected-payload flow (missing keys, protected-field edits, malformed diff).
- Fix: add tests where Gemini returns: a diff editing word_target (should reject), a response missing required top-level keys (should reject), raw non-YAML garbage (should reject).

**[MINOR] plan_patch.py — .bak collision** — second patch overwrites original baseline. Fix: timestamp or version suffix.

**[MINOR] insert_after applier — punctuation spacing** — if payload starts with punctuation (e.g., `, і це важливо`), the auto-prepended space inserts rogue whitespace before the comma.

## Next session — what to do

1. **Dispatch Codex on the 3 Gemini findings (scoped ≤10 min each this time):**
   - Sub-task 1: plan_patch.py protected-field blocklist + rejection tests
   - Sub-task 2: plan_patch.py atomic write (reuse `_write_v6_state_atomic`)
   - Sub-task 3: plan_patch.py prompt-injection hardening via literal-block wrapping
   
   File 3 GH issues first (#1256 / #1257 / #1258 suggested), dispatch each independently. Do NOT re-do the monolithic mistake.

2. **After those ship, the user runs real-module validation** on 5 failing A1 modules:
   ```bash
   for N in <5 a1 numbers>; do
     .venv/bin/python scripts/build/v6_build.py a1 $N --resume \
       --writer gemini-tools --reviewer codex-tools
   done
   ```
   Target: ≥3/5 auto-ship at ≥9.0 with zero `needs_human_review` flags.

3. **Minors** (`#1259` bucket): `.bak` versioned suffix + insert_after punctuation-aware spacing. Low priority.

## Known-good infrastructure (don't re-invent)

- Contract-first write path (#1247) — shipped, validated via M18
- Plateau + auto-plan-patch (#1252) — shipped but NEEDS the 3 findings fixed before real-module run
- insert_after parser — shipped with 6 regression tests
- ACTIVITY_ORDER validator (#1251) — shipped with matcher + position-by-position error messages
- PostToolUse context-monitor hook (`d8eb7f3d3`) — ACTIVE; fires at 75/85/95% of 1M window

## Critical rules to re-learn on restart

- **Codex dispatches ≤10 min each.** MEMORY rule, I violated it once this session already (#1252 as monolith).
- **Adversarial review after every non-trivial commit.** I skipped it on `e1806f9c2`; user had to prompt me. Don't repeat.
- **Gemini is a coding agent too** — not just Codex. Use both in parallel when files don't conflict.
- Claude weekly budget was at ~90% when this session ended. Monday reset. Minimize Claude turns; prefer Gemini/Codex dispatch.

## Uncommitted on disk (user's earlier weather rebuild, pre-existing)

Same as previous handoff — `curriculum/l2-uk-en/a1/weather.md`, several `*-review-r2/r3.md`, orchestration dispatch metas. Not this session's work. User decides commit/stash/revert.
