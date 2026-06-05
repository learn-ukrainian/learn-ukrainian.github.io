# Session Handoff — 2026-05-05 (bakeoff execution + prompt foundations)

> **Predecessor:** `2026-05-05-bakeoff-prep-and-licensing.md`
> **Mode:** Substantive Claude orchestration session — first real bakeoff execution attempts, surfaced multiple pipeline + integration regressions, six PRs landed, three open issues parked, one critical dispatch (B) NOT YET FIRED for next session.

---

## TL;DR — what shipped

Six PRs merged tonight, in order:

1. **PR #1704** — `feat(bakeoff): V7 codex-tools writer + review-only + telemetry-out + harness (#1703)` — full bakeoff infrastructure
2. **PR #1706** — `fix(prompts): escape literal {X} in linear-write.md + add render-guard test (#1705)` — `{X}` token bug + CI render-guard
3. **PR #1711** — `fix(gemini): pass prompts via cli flag (#1709 #1710)` — Gemini stdin-pipe → `-p` flag + API-first auth flip
4. **PR #1714** — `fix(agent-runtime): reject tools-suffixed registry names (#1712)` — python_qg invocation name fix
5. **PR #1716** — `fix(bakeoff): silent no-op diagnostics + citation whitespace + Codex fence prompt` — five python_qg gate-fix patches
6. **PR #1717** — `feat(mcp): slovnyk.me ingester + search_slovnyk_me + search_heritage tools (#1715)` — slovnyk.me MCP tools with conservative legal posture, heritage-defense merger

Main now at `567ee66094`.

---

## Bakeoff state

The A1/20 three-writer bakeoff was attempted **THREE times tonight**. All three failed to produce a complete report.

| Attempt | Mode | Outcome |
|---|---|---|
| 1st | `workspace-write` (no worktree) | Hung — Gemini CLI (pre-#1711) stuck in REPL waiting on stdin; 1h+ wall before SIGKILL |
| 2nd | `workspace-write` retry | Same hang pattern even after partial fix attempt |
| 3rd | `danger` + worktree (correct) | Writers ran for real this time. **Claude write ✅ 577s, Gemini write ✅ 181s, Codex write ❌ (unnamed fenced block)**. All 3 hit `python_qg` gate — Claude/Gemini failed (real content issues per Codex msg 525), Codex never produced a `module.md`. No reviews ran. `REPORT.md` generated with all-zero CoT/tool-call telemetry. |

Bakeoff artifacts at `audit/bakeoff-2026-05-05/` — useful for diagnosis, NOT a comparison report.

**Critical mistake on attempt 3:** ran from `origin/main`, NOT from PR #1696's `claude/1673-1661-cot-tier1-prompts` branch (where the new V7 CoT/Tier-1 prompts live). So the writers received the OLD prompts. The "0 CoT block emissions" finding is expected for old prompts, NOT evidence about the new prompt design.

---

## Codex consultations (msgs 525, 528)

### msg 525 — bakeoff failure diagnosis (`bakeoff-diagnostic-consult-v2`)

- **python_qg failures**: real content gaps (Claude invented fake reflexive verbs `снідаюся`/`снідаєшся`/`ідеся`; Gemini missed `plan_sections` ±10% on word-budget) + silent no-ops in correction paths (3 sites in `linear_pipeline.py`). All silent no-ops fixed via #1716.
- **Codex unnamed fence**: model output violated existing prompt rule "do not fence prose inside `module.md`". Prompt at `linear-write.md:105` strengthened via #1716.
- **#1714 did NOT tighten gates** — only changed runtime invocation name (codex-tools → codex).
- **Re-run strategy**: option (c) — fix gates first, THEN rebase #1696, THEN run writer-only first, THEN full bakeoff.

### msg 528 — V7 prompt design review (`new-prompts-review-v3`)

User-shared verbatim "Ukrainian Tutor" prompt as the reference shape. Codex returned **verbatim edits** for 4 weaknesses in PR #1696's `linear-write.md` and `linear-review-dim.md`:

- **Q4** — writer CoT mandate: `linear-write.md:11-47, 88-89` are SOFT (allows hidden thinking, then "Return only these four fenced blocks" contradicts visible-CoT). Verbatim replacement provided.
- **Q5** — reviewer per-dim evidence: schema at `linear-review-dim.md:85-89` requires only ONE `evidence` string despite asking for 3 quotes. Verbatim schema replacement provided.
- **Q6** — heritage-defense gap: `[Archaism]/[Historism]/[Dialectism]` tagging + "Proto-Slavic roots ≠ Russian" defense MISSING from both prompts. Belongs in BOTH writer and reviewer (no separate vocab/activity author phase in V7). Verbatim edits for `linear-write.md:63-67` and `linear-review-dim.md:73-78`.
- **Q7** — slovnyk.me reference: at consultation time, no MCP tool existed → use deferral wording ("future aggregator, do not claim until tool ships"). **Now obsolete** — slovnyk.me tool shipped via #1717. Dispatch B brief (see below) needs the deferral language replaced with "use `search_heritage` for heritage defense; use `search_slovnyk_me` for direct slovnyk.me lookups."

---

## NOT YET FIRED — Dispatch B (V7 prompt strengthening)

> **Brief:** `docs/dispatch-briefs/2026-05-05-1696-prompt-strengthening.md`
> **Issue:** none filed yet (will close #1696 / #1673 / #1661 when merged)
> **Status:** brief written but needs ONE EDIT before firing — replace the slovnyk.me-deferral wording (Edit 5 in the brief) with "use `mcp__sources__search_heritage` for heritage-defense + `mcp__sources__search_slovnyk_me` for direct lookups" since #1717 shipped those tools.

**Sequence:**

1. Edit Dispatch B brief Section "Edit 5 — Slovnyk.me deferral language" — replace deferral wording with current-tool wording. Reference `search_heritage` (canonical for the heritage-defense check the writer prompt's Section 2 will use) and `search_slovnyk_me` (single-source).
2. Fire Dispatch B: `delegate.py dispatch --agent codex --task-id 1696-prompt-strengthening --worktree .worktrees/dispatch/codex/1696-prompt-strengthening --base main --mode danger --effort medium --hard-timeout 3600 --prompt-file docs/dispatch-briefs/2026-05-05-1696-prompt-strengthening.md`
3. Codex rebases `claude/1673-1661-cot-tier1-prompts` onto current main (post-#1717), applies the 5 verbatim edits from msg 528, gets Claude review, opens fresh PR superseding #1696.
4. Merge that PR.
5. **Then** re-run the full bakeoff from main — this time the new prompts ARE on main, no worktree confusion.

---

## Issues parked (not blocking the bakeoff)

| # | Title | Why parked |
|---|---|---|
| #1701 | env_sanitize.py port | Defense-in-depth; agents we run are trusted today |
| #1702 | ab discuss read-only | Real bug (Gemini wrote to main earlier today via discuss) but rare; no immediate risk |
| #1707 | bakeoff_run.py resume logic uses size-only | Workaround: `rm -rf` before re-run |
| #1708 | v7_build.py per-writer subprocess timeout | Now less urgent post-#1711 (Gemini doesn't hang); still worth shipping |
| #1713 | Gemini CodeQL cleanup PR | Has 1 NEW path-injection at `image_review_server.py:233` that Gemini's fix introduced. Needs Gemini iteration. PR open, not blocked-on-review yet — needs me to send the iteration-request comment. |
| #1696 | V7 CoT/Tier-1 prompts (DRAFT) | Will be SUPERSEDED by Dispatch B's PR. Close after Dispatch B merges. |
| #1688 | XSS refactor (DRAFT) | Stale — touched same surface as Gemini's #1713; close as superseded OR rebase + re-CI + merge. User-judgment. |

---

## Process learnings (mine)

This session had a string of orchestration failures:

1. **Sandbox mode confusion** — picked `workspace-write` for bakeoff dispatches twice when every other dispatch today used `--mode danger`. Took 3 attempts to course-correct. The lesson: copy what worked, don't re-derive.
2. **Summarized verbatim prompts** — Codex consultation #1 (msg 526) abstracted the user's "Ukrainian Tutor" prompt instead of pasting it verbatim. User caught it. Re-fired as msg 527/528. Lesson: paste source material; don't paraphrase user-provided artifacts in dispatches.
3. **Ran bakeoff from main, not #1696 worktree** — the entire point of the bakeoff was to validate #1696's NEW prompts, but I sent the dispatch with `--base main`. The 0-CoT-emission finding was thus expected, not informative.
4. **Verbose explanatory responses** burned tokens — kubedojo/cursor/opencode discussions were ~500 tokens each when 50 would have done it. User explicitly called this out (~30% Claude usage by midday).
5. **`gh` not authenticated in `--mode danger` dispatches** — Codex commits + pushes work but PR creation fails. Workaround: orchestrator opens PR after dispatch returns. Worked for #1716; should formalize as the standard pattern.

Behavioral commitments for next session:
- Default to `--mode danger` for any dispatch that needs sandbox write OR the gh CLI; reserve `workspace-write` for read-only-ish work
- Paste user-shared content verbatim into Codex/Gemini consultations; never abstract
- Before firing a bakeoff, sanity-check: which BRANCH has the prompts under test
- Open PRs from the orchestrator after danger-mode dispatches return

---

## Cold-start protocol for next session

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

# 1. Bootstrap from Monitor API
curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

# 2. Verify clean main + sync
git fetch origin main && git pull --ff-only origin main && git status -s

# 3. Read THIS handoff + the chain (predecessor)
#    docs/session-state/2026-05-05-bakeoff-execution-and-prompt-foundations.md (this)
#    docs/session-state/2026-05-05-bakeoff-prep-and-licensing.md (predecessor)

# 4. Read the unfired Dispatch B brief
#    docs/dispatch-briefs/2026-05-05-1696-prompt-strengthening.md

# 5. The first action is editing Dispatch B's "Edit 5" section to replace
#    slovnyk.me deferral wording with current-tool wording. THEN fire it.
```

---

## Ranked next-session priorities

1. **Fire Dispatch B** (5-min brief edit + dispatch). Critical path to actual bakeoff result.
2. **Merge Dispatch B's PR** when CI green + Claude review clean.
3. **Re-run full bakeoff from main** (not from a worktree) once new prompts are on main. Use `--mode danger` + `--worktree .worktrees/dispatch/codex/bakeoff-rerun` + absolute `--bakeoff-dir`. Brief at `docs/dispatch-briefs/2026-05-05-bakeoff-full-execute.md` is the template (already correct).
4. **Aggregate + interpret REPORT.md** — actually evaluate which writer wins on prompt-adherence + content quality.
5. **#1713 Gemini CodeQL iteration** — comment on PR, ask Gemini to tighten the path-injection fix at line 233.
6. **#1696 / #1688 cleanup** — close superseded DRAFTs.
7. **Parked issues** when there's slack: #1708 (writer timeout), #1707 (resume terminal-event check), #1701 (env_sanitize), #1702 (ab discuss read-only).

---

## Statistics

- **PRs merged this session:** 6 (#1704, #1706, #1711, #1714, #1716, #1717)
- **Issues filed:** 8 (#1701, #1702, #1703, #1705, #1707, #1708, #1709, #1710, #1712, #1713 backlog comment, #1715 — actually counted 11 new)
- **Issues closed via merged PRs:** 5 (#1703→#1704, #1705→#1706, #1709+#1710→#1711, #1712→#1714, #1715→#1717)
- **Codex dispatches:** 6 + 2 consultations
- **Gemini dispatches:** 1 (CodeQL cleanup, partial — #1713)
- **Bakeoff attempts:** 3 (all failed but produced diagnostic data)
- **User correction interventions:** ~5 (sandbox mode, verbatim prompts, "save Claude" budget, "don't go dark" but be terse, "do the MCP tool" for slovnyk.me)
- **Wall clock:** ~10 hours start to handoff write
