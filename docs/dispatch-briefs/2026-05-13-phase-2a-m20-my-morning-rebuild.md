---
date: 2026-05-13
target: USER-RUN (V7 builds are USER-RUN ONLY per CLAUDE.md)
phase: 2a — m20 knee-transition validation pilot
module: a1/my-morning (m20)
prerequisites:
  - PR #1939 (learner-state V7 wiring) merged — DONE
  - PR #1943 (ULP-derived band derivation + recycle cadence + plan.targets) merged — DONE
  - PR #1950 (Phase 4 calibration + USE_ULP_IMMERSION_DERIVATION=True) merged — DONE
  - PR #1952 (--worktree flag) merged — DONE
  - PR #1953 (Card 1: writer isolation + curriculum-writer agent + infra_context_contamination gate) merged — pending
---

# Phase 2a — Rebuild `a1/my-morning` (m20) with full student-aware pipeline

## Why this module

`a1/my-morning` is module 20 in the A1 track. It sits at cumulative_vocab=573 — **the exact knee transition into the `a1-m15-24` band** (15-24% UK advisory) per the Phase 4 ULP calibration (`audit/ulp-calibration-2026-05-13/REPORT.html`). That makes it the hardest single-module test of:

1. **ULP-derived band selection** at a transition boundary — does `compute_immersion_band()` correctly land in `a1-m15-24` given the cumulative vocab signal?
2. **Learner-state injection** — by m20, the writer prompt should receive ~573 cumulative lemmas + ~19 modules of grammar history. That's substantial scaffolding load.
3. **Writer isolation (Card 1)** — the writer must NOT read orchestrator-context files (no handoffs, no MEMORY.md, no Bash polling). New `curriculum-writer` agent + `infra_context_contamination` gate enforces this.
4. **Recycle cadence** — by m20, lemmas should be revisiting per the calibrated cadence. The new `recycle_cadence` audit gate should NOT fire (WARN at A1).

Plus: we have a direct **before/after** signal. The previous-session build of `a1/my-morning` (lost to a dropped stash this session) hit `GOAL_PREDICATE=SATISFIED` on a 5-predicate visual contract:

```
PREDICATE_REPORT for starlight/src/content/docs/a1/my-morning.mdx:
  P1_ASSEMBLE_MDX=PASS
  P2_DIALOGUEBOX_count=2 (need >= 1)
  P3_FLASHCARD_OR_VOCABCARD_count=2 (need >= 1)
  P4_ACTIVITY_COMPONENT_count=17 (need >= 4)
  P5_BY_UNKNOWN_count=0 (need = 0)
  P5_NAMED_AUTHORS_count=5 (need >= 1)
GOAL_PREDICATE=SATISFIED
```

The new build must also satisfy these 5 predicates. If it does AND the new audit gates (`unknown_vocabulary`, `infra_context_contamination`, `recycle_cadence`) stay quiet, that proves the student-aware pipeline doesn't regress the visual contract.

## Invocation

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/build/v7_build.py a1 my-morning --worktree
```

The `--worktree` flag (shipped in PR #1952) creates `.worktrees/builds/a1-my-morning-{YYYYMMDD-HHMMSS}/` and a `build/a1/my-morning-{YYYYMMDD-HHMMSS}` branch. Build runs entirely inside the worktree — main project tree stays clean. The build prints a final `BUILD_*` summary with next-step commands.

Expected duration: ~30-45 min (writer phase ~10-15min, reviewer phase ~10-15min, audit + assemble + tests ~5min).

## Telemetry to watch via Monitor tool

Per CLAUDE.md "Build Monitoring" guidance, run the build with the Monitor tool tail-following the JSONL event stream:

```
Monitor(
    command=".venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree 2>&1 | grep --line-buffered '^{\"event\"'",
    description="V7 build events for a1/my-morning (Phase 2a m20 rebuild)",
    persistent=True,
    timeout_ms=3600000
)
```

Events to expect (lifecycle): `phase_done` (after each phase), `review_score`, `module_done`. Writer telemetry: `writer_tool_call`, `writer_end_gate`, `mcp_config_resolved`, `phase_writer_summary`. Reviewer: `reviewer_dim_evidence`, `reviewer_audit_call`, `phase_review_summary`. Audit: any `*_gate` events.

## Acceptance predicates (in order of importance)

### Tier 1 — Writer isolation works (Card 1 verification)

- [ ] **`infra_context_contamination` gate quiet** — writer made ZERO non-`mcp__sources__*` tool calls. Check `writer_tool_calls.json` in the worktree's `curriculum/l2-uk-en/a1/my-morning/` after the build. Every tool name should start with `mcp__sources__`.
- [ ] **`MCP_TOOLS_NEVER_INVOKED` gate quiet** — writer made ≥1 `mcp__sources__*` call (proves it's actually working, not just no-op).
- [ ] **No reads of denylisted paths** — `writer_tool_calls.json` has no `Read` entries pointing at `docs/session-state/**`, `docs/decisions/**`, `memory/MEMORY.md`, etc.

### Tier 2 — Student-aware pipeline works

- [ ] **Writer prompt contained `{LEARNER_STATE}` substitution** with cumulative_vocab ~573 + ~19 modules of grammar history.
- [ ] **`unknown_vocabulary` gate quiet** — module didn't use UK words outside the learner's cumulative vocab + this module's declared new words.
- [ ] **Selected immersion band = `a1-m15-24`** — `phase_writer_summary` event should reference this band. Advisory pct min/max should be 15-24.
- [ ] **`recycle_cadence` gate quiet** at A1 (WARN severity per the calibration; should not fire on a well-formed module).

### Tier 3 — Visual contract (parity with previous build)

- [ ] `P1_ASSEMBLE_MDX=PASS` — assembler ran successfully on the regenerated source artifacts.
- [ ] `P2_DIALOGUEBOX_count >= 1` — assembled MDX renders DialogueBox component.
- [ ] `P3_FLASHCARD_OR_VOCABCARD_count >= 1` — vocab renders as Flashcard/VocabCard.
- [ ] `P4_ACTIVITY_COMPONENT_count >= 4` — Tab 3 has activity components.
- [ ] `P5_BY_UNKNOWN_count == 0` AND `P5_NAMED_AUTHORS_count >= 1` — Tab 4 has proper textbook attribution.

Use this command to check the visual contract after the build:

```bash
WORKTREE=$(ls -td .worktrees/builds/a1-my-morning-* | head -1)
cd "$WORKTREE"
.venv/bin/python -c "
import re
path = 'starlight/src/content/docs/a1/my-morning.mdx'
with open(path) as f: t = f.read()
p2 = len(re.findall(r'<DialogueBox', t))
p3 = len(re.findall(r'<(?:FlashcardDeck|VocabCard)', t))
p4 = len(re.findall(r'<(?:Match|FillBlank|TrueFalse|MultipleChoice|Order|CountSyllables|DivideWords|HighlightMorphemes|LetterGrid|OddOneOut|PickSyllables|Observe|Unjumble)', t))
p5_bad = t.count('by Unknown')
p5_good = len(re.findall(r'author:\\s*[\"\\']([^\"\\']+)', t))
print(f'P2_DIALOGUEBOX_count={p2}')
print(f'P3_FLASHCARD_OR_VOCABCARD_count={p3}')
print(f'P4_ACTIVITY_COMPONENT_count={p4}')
print(f'P5_BY_UNKNOWN_count={p5_bad}')
print(f'P5_NAMED_AUTHORS_count={p5_good}')
"
```

## If it halts on a gate

| Halt cause | What it means | Next step |
|---|---|---|
| `infra_context_contamination` | Card 1's gate fired — writer made a non-sources call. **This SHOULD NOT happen on the new `curriculum-writer` agent.** If it does, Card 1 has a bug. | Read `writer_tool_calls.json`, identify the offending call, file a Card 1 follow-up. Do NOT proceed to Phase 2b. |
| `MCP_TOOLS_NEVER_INVOKED` | Writer made zero source lookups. Possibly the `curriculum-writer` agent's prompt is too restrictive, or it short-circuited. | Read the writer's stdout. Check whether the writer prompt loaded learner-state correctly. |
| `unknown_vocabulary` HARD at m04+ (m20 is m04+) | Writer introduced UK words outside the learner's cumulative vocab + this module's declared new words. Real content failure. | Per Decision Card § Phase 4 "If smoke fails on a content-class gate: Card 2 territory; do not improvise; surface gate name + failure to user." |
| `recycle_cadence` WARN | Module didn't surface enough earlier lemmas. WARN means non-blocking — note it but continue. | If WARN fires consistently, may need to adjust the calibrated cadence in `scripts/config.py`. Card 2 follow-up. |
| Visual contract predicate fails | MDX assembler regression. Recently fixed in #1930 — should be solid. | Read the assembled MDX, identify the missing component, check the V7 source yamls in the worktree for shape. |

## On success

1. **Inspect the regenerated MDX** in the worktree at `starlight/src/content/docs/a1/my-morning.mdx`. Compare manually to the live deployed version if you have one running locally.
2. **Decide commit-or-discard.** This is the "first true student-aware A1 module" per the Decision Card line 78. Worth committing as the canonical A1 pilot.
   - To commit: from inside the worktree, `git add curriculum/l2-uk-en/a1/my-morning/{activities,module,resources,vocabulary,vocabulary_hints}.yaml starlight/src/content/docs/a1/my-morning.mdx`, conventional commit, push, open PR.
   - To discard: `git worktree remove $WORKTREE && git branch -D build/a1/my-morning-{stamp}`.
3. **Advance to Phase 2b** — m1-m7 warm-up batch per `docs/dispatch-briefs/2026-05-13-phase-2b-m1-m7-warmup-batch.md`.

## Why m20 first (not m1-m7)

m20 is the **hardest case** — knee transition + full learner-state load. If it works, m1-m7 (smaller cumulative vocab, simpler band landing) is downstream confidence. If it fails, we catch the issue before burning 7 builds on lower-leverage modules. This ordering was a deliberate user call (2026-05-13).
