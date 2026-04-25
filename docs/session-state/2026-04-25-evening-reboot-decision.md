# Session Handoff — 2026-04-25 evening (curriculum reboot decided)

> **Project pivoted from V6 patch loop to structural reboot.** EPIC #1577 +
> Phase 0 (#1578) + Phase 1 (#1579) opened. 13 V6-loop issues closed. 62
> open issues triaged with labels. Salvage manifest committed as draft.
> Phase 0 (North Star + Lesson Contract) is the next concrete work.

## Decision summary

After 5 months on V6, Krisztian decided to reboot. The convergence loop never
converged on a1/1; every fix surfaced a new failure class. **The reboot
PRESERVES validated infrastructure (plans, corpus, dictionaries, wikis,
site, decisions journal, contract framework) and REPLACES only the rotten
architectural layers (writer prompts, reviewer prompts, activities prompt,
convergence loop, QG semantics).**

Three-agent consensus achieved (Claude + Codex + Gemini, two discussion
rounds, both [AGREE] at round 1):
- Round 1: `architecture` channel, thread `0b748a12cadc...`
- Round 2 corrections: `architecture` channel, thread `d36b068bcdee...`
- Round 3 salvage manifest open questions: `architecture` channel, thread (pending — running at handoff time)

## What's on main

`823f511052` — `docs: salvage manifest for curriculum reboot — Phase 1 draft (#1577)`

Earlier in session: Unit 7 (#1574), Unit 8 (#1576), Unit 9 (#1575) all
merged from the now-abandoned V6 fix loop. Those PRs technically closed
real prompt bugs and stay in main as the V6 final state — they don't
hurt the reboot, they just don't define it either.

## Open issues count

- **64 open** (62 + Phase 0 + Phase 1 sub-issues). Recap:
  - 19 `reboot-blocker`
  - 36 `mvp-deferred`
  - 6 `backlog`
  - 3 unlabeled (#1577 EPIC, #1578 Phase 0, #1579 Phase 1)

## Worktree state

```
main checkout (a1/1 manual patches preserved, intact)
.worktrees/codex-interactive (user's session, do not touch)
```

NO dispatch worktrees pending. Earlier session worktrees all cleaned up.

## Phase plan from EPIC #1577

| Phase | What | Issue # | Bound |
|---|---|---|---|
| 0 | North Star + Lesson Contract (3-agent draft) | #1578 | 2d |
| 1 | Salvage inventory + 62-issue triage | #1579 | 3d (in progress — manifest committed) |
| 2 | Config audit | (open after Phase 0) | 2d |
| 3 | Lesson schema (1:1 with Starlight components) | (open after Phase 0) | 3d |
| 4 | A1/20 `my-morning` exemplar build | (open after Phase 3) | 2w |
| 5 | A1/20 ships → fan-out to A1/4–A1/55 | (open after Phase 4) | 2-3w |
| 6 | A2/30 `work-and-food` exemplar → fan-out | (open after Phase 5) | 3-4w |
| 7 | B1/20 `pluralia-tantum` exemplar → fan-out | (open after Phase 6) | 3-4w |
| 8 | A1/1, A1/2, A1/3 (literacy bootstrap, last) | (open after Phase 7) | 1-2w |

Don't pre-open Phases 2–8 until prerequisites are clear. Per Codex's
"freeze contracts per slice" rule.

## Critical invariants from the consensus (carry into every phase)

1. **Plans are sacred.** No phase redesigns plans; phases design the lesson contract that consumes them.
2. **Immersion is plan-driven.** Each module's plan specifies its target. Lesson contract = STRUCTURE. Plan = CONTENT + RATIO.
3. **Reviewer must receive `{IMMERSION_RULE}` injection** for ALL 9 dim reviewers (currently only Naturalness has it explicitly). Audit + fix in Phase 8.
4. **NO autonomous patching loops.** Reviewer flags → Python auto-fix if format → fail fast → scoped regen of one section OR human review. No infinite repair.
5. **Python QG and LLM QG do NOT overlap.** Python: forbidden words, structure, vocab coverage, citations. LLM: pedagogical flow, naturalness, decolonization, tone.
6. **Freeze contracts per slice.** Don't scale to 218 modules until ONE exemplar passes the new pipeline end-to-end.
7. **Three-agent consultation rule.** Architecture decisions = all 3. Implementation = primary + 1 peer. Mechanical = primary alone.

## Lesson page structure (confirmed today)

A published lesson has 4 tabs in this order:

1. **Урок** (Theory) — narrative prose, RuleBox, callouts, DialogueBox, ReadingActivity, inline activities embedded between sections
2. **Словник** (Vocabulary) — FlashcardDeck, VocabCard, PhraseTable
3. **Вправи** (Workbook) — most activity components: Quiz, FillIn, MatchUp, OddOneOut, Order, GroupSort, ErrorCorrection, Anagram, Cloze, Translate, Unjumble, etc. (Tab 3 label corrected from "Зошит" to "Вправи" per `docs/lesson-contract.md` §7 P1; canonical Ukrainian label matches running code at `scripts/generate_mdx/core.py:356`. Classify and Select removed from the list — both are deprecated per `docs/best-practices/activity-pedagogy.md` §2.)
4. **Ресурси** (Resources) — SourceBox, citations, external links, YouTubeVideo references

55 Starlight components total. The Lesson Contract (Phase 0) enumerates which components live in which tab and the data shape each consumes.

## Sacred-name policy (security)

User's two private contacts (the teachers): names stay in `memory/MEMORY.md`,
NOT in any committed file. Fresh sessions inherit MY memory (so I know who
they are without naming them in chat). Phase 1 sub-task includes scrubbing
personal references across `curriculum/`, `wiki/`, `docs/` — distinguish
PERSONAL references from generic dialogue uses (the names are also common
Ukrainian first names; characters can still be called that).

Public creators (Anna Ohoiko, textbook authors) — fine to reference.

## Outstanding consultation (running at handoff)

Salvage manifest open questions in §3 — 3-agent consultation dispatched at
~21:40 UTC, background task `b3kdqtay0`. Result lands in
`.mcp/servers/message-broker/messages.db` channel `architecture`. Apply
agent-consensus changes to `docs/salvage-manifest.md` once it returns.

The four questions:
- Q1: Are #1196, #1195, #1197 actually `reboot-blocker` not `mvp-deferred`?
- Q2: Are #1051, #705 actually `backlog` not `reboot-blocker`?
- Q3: Existing curriculum modules — `source-only` (kept as reference) vs `discard` (will be regenerated)?
- Q4: Personal-name audit — Phase 1 (now) or later?

## Cold-start sequence for next session

1. Read this file (you're here)
2. `gh issue view 1577` (the EPIC)
3. `gh issue view 1578 1579` (Phase 0, Phase 1 sub-issues)
4. Read `docs/salvage-manifest.md` for full triage
5. Check `architecture` channel for outstanding agent threads:
   ```
   ab channel tail architecture --thread d36b068bcdee  # round-2 consensus
   ab channel tail architecture --thread (whatever b3kdqtay0 produced)  # round-3 manifest sign-off
   ```
6. Apply any consensus changes to manifest, commit
7. Begin Phase 0 — North Star draft (with Codex + Gemini)

## Phase 1 EXECUTED — closed at session end

After the handoff above was first written, the session continued through
Phase 1 work (per user direction "you will work all night and organize"):

### Q1+Q2 label corrections
- #1197 (Pre-launch infrastructure) moved from `mvp-deferred` → `reboot-blocker` (Codex's call)
- #705 (Vocab progression audit A1→C2) moved from `reboot-blocker` → `backlog` (Codex's call)

### Q3 — bulk legacy discard
- ~7,800 files removed from `curriculum/l2-uk-en/{a1,a2,b1,b2,c1,c2}/` and `starlight/src/content/docs/{level}/`
- a1/1 manual patches quarantined to `testbed/reference/a1/1/` (gitignore exception added: `!/testbed/reference/`)
- Orphan top-level `activities/` dir (29 files, V6-era) removed
- `curriculum/l2-uk-en/stuck-modules.yaml` (V6 tracking) removed

### Q4 — personal-name scrub
- 13 wiki LOCKED review files: "(Teacher X / Teacher Y)" → "(native-speaker reviewer)"
- 8 design docs / ADRs / scripts: line-by-line scrub
- 3 pre-reboot session-state files DELETED (V6 history, no forward value, most exposure)
- `tests/test_human_eval_tracker.py`: fixture rename ReviewerA/ReviewerB
- 4 newly-found refs scrubbed (.gitignore comment, miyklas-resources, agent-channels context, etc.)
- Public Ukrainian creators preserved (Anna Ohoiko, textbook authors, academic publishers)
- Generic dialogue uses of common Ukrainian first names preserved

### Final state
- 8 commits on main this session: salvage manifest draft → handoff doc → personal-name audit → personal-name scrub → testbed quarantine → bulk discard → manifest FINAL → dispatch briefs preserved
- Phase 1 sub-issue #1579 CLOSED with completion comment
- Final issue label distribution: 20 reboot-blocker / 35 mvp-deferred / 7 backlog / 3 EPIC-level

### Working tree state at handoff time
- ~870 files still dirty: mostly Gemini's wiki cron (new wiki figures + modified wiki articles), corpus_audit reports, current.md, finding-normalizer-growth.yaml, plus a backup of sources.db. None of these block Phase 0; the wiki cron's new figures are part of corpus salvage.
- The user's previous-session orchestration-final*.md handoffs are untouched (not in my scope).

### Phase 0 starts here
The user starts Phase 0 by commissioning the North Star + Lesson Contract draft.
Three-agent collaboration: Claude drafts, Codex + Gemini review, all three sign off.

## Anti-checklist (next session)

1. **NO solo Claude decisions on architecture.** Always consult Codex + Gemini via `ab discuss` or `ab post`.
2. **NO redesign of plans.** They're State Standard 2024 grounded.
3. **NO autonomous patching loops** in the new pipeline design.
4. **NO overlap between Python QG and LLM QG.**
5. **NO writing the user's two private teacher names anywhere committed.**
6. **NO cutting corners on math/verification.** Pull data, show work, then conclude. xhigh effort means xhigh effort.
7. **NO assuming silence = consent.** When in doubt, ask one focused question; do not menu.
8. **NO opening Phases 2–8 sub-issues yet.** Wait for Phase 0/1 to inform their scope.
