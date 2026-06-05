# Session Handoff — 2026-04-25 (orchestration progress)

> **Active orchestration of EPIC #1550.** User AFK ~3h. Claude orchestrating
> 6 dispatch units across Codex + Claude. Goal: a1/1 + a1/2 + a1/3 pass
> automated builds end-to-end without manual content patches.
>
> All dispatched briefs at `/tmp/briefs/`. Source of truth for the unit
> plan: EPIC #1550 + handoff `2026-04-25-a1-1-fix-comprehensive-handoff.md`.

## Cold-start sequence for next session

1. Read this file.
2. `gh issue view 1550` — 17-item EPIC checklist.
3. `gh pr list --state open` — see what's mid-review.
4. `.venv/bin/python scripts/delegate.py list --status running` — what's in flight.
5. Check `/tmp/briefs/` for any unit briefs not yet dispatched.

## Trace finding (this session) — config layer audit

Three layers govern activity behavior, two are config, one is prompt:

| Layer | File | Purpose |
|---|---|---|
| Audit | `scripts/audit/config.py` `LEVEL_CONFIG` | Audit gates — A1 has min_activities=0/min_types_unique=0 (non-binding) |
| Pipeline | `scripts/pipeline/config_tables.py` `get_activity_config` | Drives prompt placeholders — A1 has INLINE_MIN=4/INLINE_MAX=6 hardcoded |
| Prompt | `scripts/build/phases/v6-activities.md` | 352 lines, fully placeholder-driven |

**Key finding:** the EPIC's "lines 520-630" complaints about `v6-activities.md`
hardcoded conflicts are **stale** — that file is only 352 lines and fully
placeholder-driven. Real conflict is between the two config layers. Updated
Unit 3 brief to reflect actual state. Unit 4 brief expanded to address BOTH
config layers, not just audit.

**Plan reference schema gap (NEW):** plans use `{title, notes}` for references
— no structured `{kind, path, query}` for RAG retrieval. Logged as candidate
Unit 7, deferred behind Unit 4.

## Dispatched + landed this session

| Item | Agent | PR | Status |
|---|---|---|---|
| API hotfix (uvicorn AccessFormatter) | Claude (inline) | direct to main `534d28ff1b` | ✅ |
| API hardening v2 (Codex sweep + tests + docs) | Codex | #1554 | ✅ merged |
| Unit 1 — reviewer hardening (stress strip + level context per dim) | Claude | #1552 | ✅ merged |
| Unit 2 — writer prompt 5 rules | Codex | #1551 | ✅ merged |
| Unit 3 — activity prompt + plan vocab (33 letters) + letter_module flag (a1/1) | Codex | #1556 | ✅ merged (after fix-up `a21033d068` for non-dict activities crash) |
| Unit 5 — exercise_quality contract (order → set-membership) | Codex | #1557 | ✅ merged |
| letter_module flag follow-up (a1/2 + a1/3) | Claude (inline) | direct `73c1db2c06` | ✅ pushed |
| Unit 4 — audit/pipeline config reconciliation + MAX→warn + letter_module audit exception | Claude xhigh | TBD | 🟡 dispatched |

## Queued / not yet dispatched

| Item | Brief at | Blocked by |
|---|---|---|
| Unit 6 Phase A — a1/1 baseline (Claude writer / Codex reviewer) | `/tmp/briefs/codex-1550-unit6-phaseA-baseline.md` | Unit 4 merge |
| Unit 6 Phase B — a1/1 experiment (gpt-5.5 writer / Claude reviewer) | `/tmp/briefs/codex-1550-unit6-phaseB-gpt55-writer.md` | Unit 4 merge |
| Unit 6 Phase C — a1/2 + a1/3 with winner | (orchestrator writes after compare) | Phase A + B done + comparison |

## Dispatch cap policy (MEMORY)

2 Claude + 2 Codex max in flight. Currently: 0 Claude + 2 Codex.

## Immediate orchestration sequence

1. Wait for API v2 + Unit 3 merges.
2. Merge each PR per #0H — squash + delete-branch + cleanup worktree.
3. Fire Unit 5 (Codex) once a slot frees.
4. Fire Unit 4 (Claude) once Unit 3 merges (Unit 4 depends on Unit 3's
   reconciliation work + the `letter_module` flag in plans).
5. Fire Unit 6 Phase A + Phase B in parallel (2 Codex slots) once Unit 4 merges.
6. Compare Phase A + B artifacts. Decide winner per rubric:
   - Both pass MIN ≥ 8 → higher MIN dim wins.
   - One passes → that one wins.
   - Tie ±0.3 → fewer convergence rounds.
   - Still tied → manual eyeball, ask user.
7. Fire Phase C with winner pair on a1/2 + a1/3.

## Anti-checklist (do NOT do)

1. ❌ Run `v6_build.py` inline — dispatched only. (User correction 2026-04-25.)
2. ❌ Manual content patches — pipeline must produce passing modules unaided.
3. ❌ Touch `wiki/` — separate agent rebuilding.
4. ❌ Touch `.worktrees/codex-interactive` — user's local work.
5. ❌ Auto-merge any PR — orchestrator merges after CI passes.
6. ❌ Default flags on builds — always `--writer X --reviewer Y` explicit.

## Decisions made this session

- API logging.json fix: `"()": "uvicorn.logging.AccessFormatter"` —
  applied as inline hotfix because TCP RST loop was blocking user UI.
  Codex follow-up (API v2) adds regression test + sweep + docs.
- a1/1, a1/2, a1/3 all get `letter_module: true` flag (Unit 3) —
  alphabet/orthography exception class. Only a1/1 gets 33-letter vocab
  expansion; a1/2 and a1/3 are consolidation, not introduction.
- Unit 6 dispatched (not inline) — user explicitly forbade inline builds.
- Unit 7 (plan reference structured schema) deferred behind Unit 4.

## Open questions surfacing

1. After Unit 1 lands, if Dialogue dim still <8.0 on a1/1, escalate to
   per-dim agent routing (Dialogue → Claude reviewer only).
2. `letter_module` flag — explicit author flag is the chosen direction
   (Unit 3 + Unit 4). Auto-detect from `vocabulary_hints` was discussed
   in handoff but rejected as too fragile.
3. After all 17 items land, do we proceed a1/4..a1/55 in batches or
   first do dim-level QA on the 3 alphabet modules?
