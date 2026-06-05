# Session Handoff — 2026-05-06 morning (discussion converged + gemini fix shipped + channels UX deferred)

> **Predecessors:**
> - `2026-05-06-bakeoff-result-codex-wins-decision-pending.md` (overnight bakeoff result)
> - `2026-05-06-runbook-strand-1-and-bakeoff-validation.md` (the runbook overnight)
>
> **Mode:** Morning continuation. User awake, multiple corrections + reframings.

---

## TL;DR — what landed this morning

1. **Three-agent discussion now functions** — yargs argv-bug fixed in `scripts/agent_runtime/adapters/gemini.py` (#1730 fix shipped, 12 tests pass). Gemini's prompt now goes via stdin; placeholder ` ` via `-p`. Workaround until Gemini CLI 0.40.1+ patches yargs.
2. **Discussion converged** at round 2 on architecture channel thread `25ab8dbd8b00`. **All 3 agents [AGREE] on Option A** with three substantive refinements (below).
3. **Decision Card NOT YET updated.** User instruction: don't proceed to formal lock until they say `go`. Refinements are documented here for the user to review.
4. **Channels UX work paused mid-edit** at #1731 — surgical UX improvements + multi-UI participation architecture. User wants others to review the issue first.

---

## The discussion's substantive refinements (real signal — read these)

All 3 agents converged on Option A (lock Codex), but with concrete additions:

### 1. Gemini's VESUM-gate condition (load-bearing)

> "Codex can safely serve as the module writer **if and only if** the VESUM verification gate remains a hard, non-negotiable blocker for publication. We cannot rely on prompt constraints alone to prevent Codex from hallucinating Ukrainian morphology; the deterministic VESUM check is our only reliable defense."

Backed by morphological argument: `іти` is a motion verb with no reflexive paradigm in literary Ukrainian (no `-ся` form attested in VESUM); `снідати` is transitive/intransitive but never reflexive. Codex's `йдуся` / `снідаюся` / `юся` are real morphological errors, not minor prompt-tuning issues. The contamination prior — Russian `завтракаю` surface-similarity dragging the model toward inventing a Ukrainian reflexive — is the predicted failure class.

**Implication for the lock**: VESUM gate stays HARD. No prompt-confidence override. Aligns with user's gate philosophy reframe ("quality should always be a hard gate").

### 2. Codex's rollback-criteria (Claude sharpened concretely)

Lock is **"V7 default writer under hard gates"** — not permanent.

**Concrete rollback trigger** (testable, time-bounded):

> "If the next correction-pass on `a1/my-morning` still emits any of {invented -ся forms on non-reflexive verbs, wiki-path strings inside `references[]`, immersion >35%}, escalate to a narrower 1-writer prompt-rework cycle BEFORE proceeding to A1 batch build."

### 3. Reframe the lock language

Not "Codex is the writer forever" but **"Default V7 writer until the next bakeoff signal indicates otherwise."** ADR §3 specifies writer-selection via bakeoff, which is repeatable. Decouple from the Gemini adapter fix (#1708) — fix that independently, allowing future bakeoff retest of all 3 writers.

### Codex's narrowing of Gemini's VESUM claim (round 2)

> "VESUM is necessary for the invented `-ся` forms, but it is not sufficient for the full risk profile... the guardrail should be the full hard-gate suite, with VESUM as the morphology blocker, not the sole defense."

Full hard-gate suite per the user's morning reframe: word_count (HARD min, multi-attempt), VESUM, citations_resolve, language-quality (russianisms/surzhyk/calques/paronyms), structural gates (formatting/inject/component/mdx_render). Per-section budgets + immersion stay advisory.

---

## Code shipped this morning

| Change | File | What |
|---|---|---|
| Yargs argv-bug workaround | `scripts/agent_runtime/adapters/gemini.py` | `cmd.extend(["-p", " "])`; prompt via `stdin_payload`. Bypasses Gemini CLI 0.40.1 yargs bug where prompt content containing `-p`/`--prompt` substrings caused "Not enough arguments following: p". |
| Test updates | `tests/test_agent_runtime_gemini_adapter.py` | 3 existing tests updated, 1 new regression test (`test_prompt_with_p_substrings_works_post_yargs_workaround`). 12 tests pass. |
| Channels.html date format | `playgrounds/channels.html` | Timestamps now show `YYYY-MM-DD HH:MM:SS` (used to be HH:MM:SS only). |
| Home page nav | `playgrounds/index.html` | Replaced broken comms.html link with channels.html ("Agent Channels — Slack-style multi-agent discussions"). |
| MEMORY.md rule #0J | `~/.claude/projects/.../memory/MEMORY.md` | "LOCAL REFERENCE CORPUS IS RIGHT THERE — STOP ASKING FOR MORE" — points to `docs/references/private/` (ULP 1-00 → 4-00) and `docs/references/textbooks-txt/`. |

**NOT committed yet** — these are working-tree changes. User decides whether to commit + push or roll back.

## Issues filed this morning

- **#1730** — yargs argv bug + workaround (fix shipped same morning)
- **#1731** — channels.html UX overhaul + multi-UI participation architecture (TWO parts: surgical UX fixes + ADR for multi-UI participation; user explicitly wants others to review)

## User reframings this morning (preserve verbatim, these are operative for #1725 + future writer-prompt iterations)

1. **Gate philosophy** — word_count = HARD minimum (multi-attempt correction); per-section budgets = advisory; immersion = advisory with hard edges (block <10% / >90% on A1); VESUM + citations + language-quality + structural = HARD.
2. **Anna Ohoiko = Anna Ohoiko**, not Ohiienko (corrected twice). Both June book pages I've seen (workbook page 24 + adjectives chart) are previews of her June A1 book. ULP premium PDFs (in `docs/references/private/ULP {1-4}-00 Lesson Notes.txt`) are her full A1/A2/B1/B2 curriculum. **Single author across all reference material I've seen.**
3. **#1725 reframed twice**:
   - first: "not verbatim quote, organic content not fulfilling instruction"
   - then: "use the others' style" → author-anchored per section (Karaman / Avramenko / Vashulenko style anchors)
4. **Local data IS HERE — stop asking for more**. `docs/references/private/` + `docs/references/textbooks-txt/` + `data/textbooks/` (561 MB PDFs) + MCP `search_text`. Working set is locked. Captured as MEMORY rule #0J.
5. **Two-tab pedagogy calibration**: Lesson tab follows ULP/textbook rhythm (~30-50% Ukrainian); Workbook tab follows Anna's discipline (≥80% Ukrainian, 5-level scaffold ramp).
6. **"We won't go until Gemini is fixed"** — hard gate. Now satisfied (#1730 shipped).
7. **"Be critical, push back, no yes-man"** — operative.
8. **"Multi-UI participation"** (new this morning) — Claude Desktop, Codex UI, user-as-participant. Filed as #1731 Part B (ADR-track, not tonight).

---

## Decision Card status

`docs/decisions/pending/2026-05-06-writer-selection-codex-gpt55.md` — **STILL PENDING USER SIGNOFF.**

After 3-way discussion, **all 3 agents endorse Option A** with the three refinements above. User said "we won't go until Gemini is fixed" (✅ done) and "after discussion I will give the go" — so the next message from user should be `go` / `wait` / `go but also X`.

When user says `go`, the Decision Card update should:
1. Move from `pending/` to accepted location
2. Replace "Lock Codex/GPT-5.5 as V7 writer" with **"Default V7 writer until next bakeoff signal indicates otherwise"**
3. Bake in the rollback criteria from Codex+Claude refinement
4. Bake in Gemini's VESUM-must-stay-hard condition (already in user's morning reframe but should be explicit in the card)
5. Update `claude_extensions/rules/pipeline.md` accordingly
6. Run `npm run claude:deploy`

---

## Open work after lock signoff

1. **Codex briefing in `architecture` channel** — once locked, send Codex (via `ab post architecture codex`) the explicit lock + rollback criteria + gate philosophy reframe so he has persistent context.
2. **Gate philosophy reframe Codex dispatch** — implement word_count multi-attempt, per-section advisory, immersion soft-with-hard-edges. Single Codex dispatch, ~60 min.
3. **#1725 packet enrichment Codex dispatch** — ULP excerpts + textbook chunks pre-loaded into knowledge_packet, author-anchored per section. Larger scope, ~90-120 min, can run after gate-reframe lands.
4. **Re-run bakeoff** with all the above to validate Codex meets the rollback criteria (no invented `-ся`, no wiki-path miscites, immersion <35%).
5. **#1708 Gemini adapter stability** — independently fix so future bakeoffs include all 3 writers.
6. **#1731 multi-UI participation ADR** — design before implementation.

---

## In-flight at handoff write

- Discussion converged (thread `25ab8dbd8b0044068b60ffd26c2ffbad` in architecture channel).
- Channels UX work PAUSED mid-edit at line ~144-216 of `playgrounds/channels.html` (auto-refresh design stage). Per #1731 Part A, can resume from there OR start fresh.
- Working tree is dirty with 5 changes listed above + the orphaned files from #1718 (overnight handoff said leave alone).

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

git fetch origin main && git pull --ff-only origin main && git status -s
git worktree list

# READ DECISION CARDS FIRST
ls docs/decisions/pending/

# Then the chain of handoffs
#   docs/session-state/2026-05-06-morning-discussion-converged-and-channels-ux.md (THIS)
#   docs/session-state/2026-05-06-bakeoff-result-codex-wins-decision-pending.md (overnight)
#   docs/session-state/2026-05-06-runbook-strand-1-and-bakeoff-validation.md (overnight runbook)

# Read full converged discussion
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail architecture --thread 25ab8dbd8b0044068b60ffd26c2ffbad -n 10

# Check open issues from this session
for n in 1725 1730 1731; do gh issue view $n --json state,title --jq '.title + " — " + .state'; done
```
