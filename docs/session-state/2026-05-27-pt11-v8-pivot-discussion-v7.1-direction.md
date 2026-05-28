---
date: 2026-05-27
session: "Part 11 of the 2026-05-27 multi-part session. After Pt 9-10's hardening arc landed (PRs #2366, #2367, #2370, #2371, plus tactical #2372), user pivoted: stop fighting the V7 writer prompt; reframe the LLM from compose-lesson to render-the-wiki-as-lesson. Codex+Gemini consulted via `ab discuss` channel `wiki-driven-writer-pivot` (2 rounds each); both converged on **V8 (new renderer phase)** with [AGREE]. User pushed back: V7.1 (edit existing `linear-write.md` + add wiki-vocab-bound gate) likely makes more sense + add B1+/seminars/activities scaling constraints. **Cursor consultation in flight** at session handoff. Two PRs merged on main (Path B tactical #2372, agy-cli ladder rung #2375). Docs PR #2374 with V8 ADR draft pending user review."
status: cursor-consultation-in-flight-v7.1-direction-tentative
main_sha: f0ae2f6b8f (post PR #2375)
main_green: yes
working_tree_dirty: see "Untracked artifacts" below
session_close: 2026-05-27 evening / 2026-05-28 early morning
---

# 2026-05-27 — Part 11: V8 pivot discussed, V7.1 tentatively chosen, cursor in flight

**Read the TL;DR first. Then the 6-step opening sequence at the bottom.**

## TL;DR

After Pt 9-10 hardening landed and Path B tactical merged (PR #2372), user fired a strategic pivot question: *"cannot we just turn the wiki into a lesson?"* and *"the LLM should USE THE WIKI to BUILD the lesson... is this possible. how should we approach it?"*

Fired multi-agent discussion on channel `wiki-driven-writer-pivot`:
- **Codex r1+r2**: V8 (new renderer phase) — framed V7.1 as "fast but likely inherits the current prompt's crowded failure surface."
- **Gemini r1+r2**: V8 (new renderer phase) — agreed with codex; ended with `[AGREE]`.
- **Cursor**: **in flight at session close** (background task `bj33si2vx`). Output goes to channel DB in the gemini worktree (see "Recovering cursor's response" below).

Wrote draft ADR: `docs/decisions/pending/2026-05-27-v8-wiki-driven-writer.md` (recommends V8).

**User pushback (in conversation, after reading ADR summary)**:
> *"i would go for v7.1 after cursor take. and keep in mind we have to be able to produce b1+ content with it as well plus seminars in full ukrainian and activities ofc"*

So the tentative direction is **V7.1** (edit `linear-write.md` + add wiki-vocab-bound gate + scale to B1+/seminars/activities), pending cursor's perspective. ADR needs rewrite to recommend V7.1 with V8 kept as escalation path.

## What landed on main during Pt 11

- **PR #2372** (Path B tactical, my-fix-after-gemini-overscoped) — MERGED `5f55b9c87224`. Bumped `WRITER_PROMPT_CEILING_BYTES` 130KB→132KB + small ceremony trims + `#R-PROSE-FLOOR-A1` rule. Pivot supersedes this design but the word_count fix is in main for any V7-architecture refire.
- **PR #2375** (codex agy-ladder rung) — MERGED `f0ae2f6b8f` (current main HEAD). New gemini fallback ladder order: **pro+api → pro+oauth → agy-cli (Antigravity, gemini-3.5-flash-high) → flash+api → flash+oauth → 2.5-pro+api → 2.5-pro+oauth**. Sidesteps Gemini OAuth/quota issues by using agy's separate Antigravity quota. Codex implemented Shape A (extended `GeminiRung` with `cli` dimension); orchestrator finished commit/push/PR after codex's silence-timeout fired at 40min; orchestrator also caught + fixed a CI failure in `dispatch.py::_gemini_attempt_runner` (was sending agy rung through gemini-cli adapter).

## PRs open at handoff

- **PR #2374** — `claude/docs-pt9-10-v8-2026-05-27`. Bundles all Pt 9-11 docs:
  - Pt 9-10 session handoffs (these document the V7 hardening arc).
  - 7 dispatch briefs from Pt 9-10.
  - `audit/2026-05-27-codex-brain-pick-m20/turn-{1,2,3}-*.md` (the "visible compliance tokens" brain-pick).
  - `audit/2026-05-27-wiki-driven-pivot-discussion/transcript.md` (codex+gemini convergence; **cursor's reply NOT yet in this file — needs append after cursor responds**).
  - `docs/decisions/pending/2026-05-27-v8-wiki-driven-writer.md` (the V8 ADR — **needs revision to V7.1 per user direction**).
  - `docs/session-state/current.md` updated to Pt 11.
  - **Status**: CI green except advisory `review / review` CANCELLED (Gemini Dispatch — investigated, likely the ~7min timeout edge or concurrency cancel; non-blocking per #M-0.5).
  - **Disposition**: held for user review. NOT autonomous-merged because the ADR inside still recommends V8; user wants V7.1 framing.

## The pivot architecture (4-layer, agreed by codex+gemini r1+r2)

| Layer | Role | Source |
|---|---|---|
| **Wiki** | Lesson spine — methodology, sequence, vocab minimum, L2 errors, decolonization stance, textbook example formats | `wiki/pedagogy/{level}/{slug}.md` |
| **Textbook RAG** | Authority/evidence; wiki cites chunks as `[S1]…[S9]` | `data/sources.db` chunks via `mcp__sources__get_chunk_context` / `verify_quote` |
| **ULP** | Pedagogical pattern (7 practices + S1→S6 progression at A1/A2) | `docs/references/private/`; summarized `docs/best-practices/ulp-presentation-pattern.md` |
| **LLM (renderer)** | Render wiki + voice-rewrite (3rd-person methodological → 2nd-person teacher) + add English glosses + emit dialogues/activities/vocab. **NO** invention of vocab/examples/citations/claims | claude-tools / codex-tools / cursor-tools / gemini-tools |

**Key convergence points (codex r2 + gemini r2)**:

1. **Layered vocab allowlist** (Codex r2 → Gemini r2 conceded):
   ```
   allowed = (wiki.vocabulary_minimum
           ∪ plan.targets.new_vocabulary
           ∪ plan.targets.vocabulary_hints
           ∪ cumulative_learner_state.taught_lemmas
           ∪ closed_class_function_words
           ∪ proper_nouns_in_wiki_examples
           ∪ bad_form_markers
           ∪ quoted_evidence_from_cited_rag_chunks)
   ```
2. **NO CEFR runtime permission** (Codex r2 pushback; Gemini conceded — *"recreates writer invention through a side door"*).
3. **NO single-token hard-fail** — band-tolerated misses; reject on **content lemmas after normalization** outside the allowlist (codex empirical citation: `scripts/audit/checks/learner_state.py:97-110`, `scripts/config.py:488,493`).
4. **Wiki gate upstream hard-reject** when wiki sections are thin (both agents).
5. **Wiki itself is LLM-generated** — must still audit for Russianisms/calques. Wiki ≠ infallible (codex r1, gemini r2 conceded).
6. **Rules that stay load-bearing** (codex r2 enumerated): `#R-CITE-HONEST`, chunk-retrieval telemetry, `#R-BAD-FORM-MARKER`, `#R-AUDIENCE-LANGUAGE-A1`, `#R-SINGLE-VOICE-A1`, `#R-NO-SCAFFOLDING-LEAKS`, `#R-CLEAN-TABLES`, dialogue count/format, prose/word floor, artifact emission contract.

## The V7.1 vs V8 question (user's redirection)

| Aspect | V7.1 (user-preferred) | V8 (codex+gemini r1/r2) |
|---|---|---|
| **Mechanism** | Edit `scripts/build/phases/linear-write.md` to delete redundant rules + strengthen wiki-rendering rule + add vocab allowlist gate | Write new `scripts/build/phases/v8-render-module.md` prompt + new pipeline route |
| **Infrastructure** | Reuses existing V7 pipeline (`scripts/build/v7_build.py`, `scripts/build/linear_pipeline.py`, wiki manifest extraction, gates, telemetry) | New `v8_build.py` route or `--writer v8-renderer` flag; rebuild plumbing |
| **Effort** | ~1-2 days (prompt trimming + 1 new gate) | ~2 weeks |
| **Risk** | Inherits any framing baggage in V7 prompt (codex r1's "crowded failure surface") | Clean slate but more surface area for bugs |
| **Recovery** | If V7.1 doesn't deliver in 2-3 m20 refires, escalate to V8 (still cheap) | Less reversible — once V8 ships, V7 is legacy |

**Material end-state is similar**: the LLM reads a prompt that says "render the wiki, don't invent" with a hard vocab allowlist gate. The differences are largely cosmetic (file name, route name).

**User direction (2026-05-28 ~00:10)**: prefer V7.1. Wait for cursor's take before locking.

## Three scaling constraints the user added

The previous codex+gemini discussion was framed mostly around A1 modules. User explicitly named these as scaling requirements:

1. **B1+ content**: body is 100% Ukrainian (no English explanations). Voice-rewrite is methodological-UK → teacher-UK register shift, not language translation. Cumulative learner state is ~3000 lemmas vs A1's ~200 — the wiki-vocab-bound gate becomes much less restrictive but still bounds *new* vocabulary introduction to the wiki minimum.

2. **Seminar tracks in full Ukrainian** (HIST, BIO, ISTORIO, LIT, OES, RUTH, plus the LIT sub-tracks like lit-essay, lit-hist-fic, lit-fantastika, etc.). Wiki is an LLM-generated research artifact citing textbook RAG + external articles + Wikipedia. The verification surface is bigger. Treating wiki as source-of-truth risks laundering hallucination upstream — but the wiki itself was generated with `mcp__sources__verify_source_attribution` and external article ingestion, so the laundering window is small.

3. **Activities** (`activities.yaml` emission): fill-in, MCQ, error-correction, contrast-pair items. Wiki names exercise formats (Вправа 1, 2, ...) but not concrete items. The LLM still composes activity items — vocab allowlist applies, but the activity-item composition needs its own constraint set within the renderer framing.

The cursor consultation explicitly asks about these. The revised V7.1 ADR must address each.

## Cursor consultation — RATE LIMITED

- **First task** `bj33si2vx`: failed silently. Root cause: bridge resolves `REPO_ROOT` from `__file__` (script path), not cwd. With absolute script path the bridge looked at main project's DB where the channel doesn't exist.
- **Re-fire task** `bac0ynhl1` with `AB_REPO_ROOT` env var pointing at gemini worktree: discussion ran but **cursor returned a rate-limit message** (`cursor/composer-2.5 rate limited`). Discussion ended with `hit max_rounds=1 without convergence. Still disagreeing: cursor`. No substantive cursor position captured.
- **Channel DB**: `.worktrees/dispatch/gemini/path-b-writer-prompt-section-floor-2026-05-27/.mcp/servers/message-broker/messages.db` (NOT main project's `.mcp/.../messages.db`).
- **Question file**: `/tmp/cursor-v7_1-vs-v8.md` (also committed at `audit/2026-05-27-wiki-driven-pivot-discussion/cursor-r1-question.md`).
- **What cursor was asked**: V7.1 vs V8 + "crowded failure surface" claim + B1+ scaling + seminar scaling + activities + cursor-specific perspective + blind spots. Max 1 round.

### Recovery: re-fire cursor when rate-limit window resets

```bash
AB_REPO_ROOT=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/gemini/path-b-writer-prompt-section-floor-2026-05-27 \
  /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python \
  /Users/krisztiankoos/projects/learn-ukrainian/scripts/ai_agent_bridge/__main__.py \
  discuss wiki-driven-writer-pivot - --with cursor --max-rounds 1 \
  < /tmp/cursor-v7_1-vs-v8.md
```

Alternative: use `ab ask-cursor` for a one-shot Q&A instead of channel discussion.

Alternative if cursor stays rate-limited: proceed without cursor's input. The user's V7.1 direction is already clear; cursor is gravy.

### Recovering cursor's response

When you start fresh, run:
```bash
.venv/bin/python -c "
import sqlite3
db = sqlite3.connect('.worktrees/dispatch/gemini/path-b-writer-prompt-section-floor-2026-05-27/.mcp/servers/message-broker/messages.db')
rows = db.execute('SELECT from_agent, round_index, kind, created_at, body FROM channel_messages WHERE channel=\"wiki-driven-writer-pivot\" AND from_agent=\"cursor\" ORDER BY created_at').fetchall()
for from_agent, round_idx, kind, ts, body in rows:
    print(f'=== {from_agent} r{round_idx} {kind} {ts} ===')
    print(body)
    print()
"
```

If no cursor response yet: check task output file, or tail the cursor agent's session log under its configured runtime directory.

If task `bj33si2vx` or the re-fire task `bac0ynhl1` failed for any reason: re-fire with the same prompt file at `/tmp/cursor-v7_1-vs-v8.md`. **Important**: the channel DB lives in the gemini worktree, NOT main project. Use `AB_REPO_ROOT=/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/gemini/path-b-writer-prompt-section-floor-2026-05-27` env var when invoking the bridge with an absolute script path, otherwise the bridge resolves the wrong DB and reports "channel does not exist".

## 6-step opening sequence (next session)

1. **Read cursor's response** via the SQL snippet above. If still empty, wait or re-fire.
2. **Read this handoff** end-to-end + the ADR (`docs/decisions/pending/2026-05-27-v8-wiki-driven-writer.md`).
3. **Synthesize**: codex r1+r2 + gemini r1+r2 + cursor + user's V7.1 preference + B1+/seminars/activities constraints into a **revised ADR**. Title becomes something like `2026-05-27-v7.1-wiki-driven-writer.md` (rename file or supersede the existing V8 file).
4. **Surface revised ADR to user** for final approval (V7.1 / V8 / hybrid / reject).
5. On approval, implementation order (V7.1 path):
   - Edit `scripts/build/phases/linear-write.md`: delete redundant rules, strengthen the wiki-rendering rule, lock the voice-rewrite scope.
   - Add `scripts/audit/wiki_completeness_gate.py` (upstream hard-reject for thin wiki sections).
   - Extend `scripts/audit/checks/learner_state.py` with the layered vocab allowlist.
   - Extend `scripts/build/phases/wiki_manifest.py` to make wiki vocab minimum a first-class obligation.
   - Add seminar-track adjustments (different completeness criteria, full-UK voice rewrite, claim/evidence graph hooks).
   - Pilot on `a1/my-morning` (m20). 1-3 refires under V7.1 prompt; compare against Pt 10's worktree `185032` empirical baseline.
6. If m20 ships clean under V7.1, port to a second A1 module (`a1/my-greeting-and-goodbye`?) for validation, then promote V7.1 as default. If V7.1 fails after 2-3 refires, escalate to V8.

## State of the world at handoff

### Main branch
- Latest commit: `f0ae2f6b8f7e` (PR #2375 merge — agy-ladder rung).
- Pre-PR-#2372: `20ab69072d`. PR #2372 merged at `5f55b9c87224`. PR #2375 merged at `f0ae2f6b8f`.
- Local main is at `20ab69072d` (not pulled — per user direction "don't change the branch in main checkout"; main is reference only).

### Open PRs
- **PR #2374** (`claude/docs-pt9-10-v8-2026-05-27`) — docs bundle. Held; advisory review failure only. Awaiting user merge OR rewrite of the ADR inside (V8 → V7.1) before merge.

### Worktrees on disk
```
/Users/krisztiankoos/projects/learn-ukrainian                                                                                main (reference)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/gemini/path-b-writer-prompt-section-floor-2026-05-27        gemini/path-b-... (PR #2372 merged; branch still exists locally because worktree using it; channel DB here)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/claude/docs-pt9-10-v8-2026-05-27                            claude/docs-pt9-10-v8-... (PR #2374 open)
/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/agy-ladder-rung-2026-05-27                            codex/agy-ladder-rung-... (PR #2375 merged; branch still exists locally because worktree using it)
.worktrees/builds/a1-my-morning-20260527-073037/  pre-hardening
.worktrees/builds/a1-my-morning-20260527-073705/  pre-hardening
.worktrees/builds/a1-my-morning-20260527-161219/  Pt 9 mid-hardening (stale)
.worktrees/builds/a1-my-morning-20260527-163310/  ⭐ Pt 9 clean writer output (gate-blocked on wiki_coverage)
.worktrees/builds/a1-my-morning-20260527-163621/  Pt 9 mid-hardening (stale)
.worktrees/builds/a1-my-morning-20260527-163804/  Pt 9 killed mid-build
.worktrees/builds/a1-my-morning-20260527-185032/  ⭐⭐ Pt 10 — Path B baseline; 6/7 vocab + word_count short (under tactical fix now)
```

Build worktrees are forensic — keep until V7.1 m20 ships clean.

### Untracked artifacts in main checkout (bundled into PR #2374)
All these are already in PR #2374:
```
audit/2026-05-27-codex-brain-pick-m20/
audit/2026-05-27-wiki-driven-pivot-discussion/transcript.md
docs/decisions/pending/2026-05-27-v8-wiki-driven-writer.md
docs/dispatch-briefs/2026-05-27-{7 files}.md
docs/session-state/2026-05-27-pt9-hardening-works-wiki-gate-blocks.md
docs/session-state/2026-05-27-pt10-phase2a-validates-only-word-count-gap.md
docs/session-state/current.md (modified)
docs/session-state/2026-05-27-pt11-v8-pivot-discussion-v7.1-direction.md (this file — needs to be added to PR #2374 OR fired as a new docs commit on top)
```

### In-flight at handoff
- `bj33si2vx` — cursor consultation. Background task. Output to channel DB in gemini worktree.

### Open issues from Pt 9-11
- **#2368** — `/api/delegate/active` route handler regression. Low priority workaround via `/api/orient`.
- **#2369** — PR #2367 scope-creep evaluation (`_contract_yaml` vocabulary fields + dialogue-gloss "block-bottom" sentence). Read-only investigation comment posted; DialogueBox doesn't support `block-bottom`; sentence revertable.
- **#2373** — agy-cli fallback ladder rung. **CLOSED by PR #2375** (auto-close via "Resolves #2373" in PR body).

## Key context dumps for fresh-session resume

If next session is a fresh Claude Code instance: the multi-day arc is:

- **Pt 8** (2026-05-27 morning): m20 V7 anchor SHIPPED via PR #2364. Post-ship review found 6 substantive failure modes (kaleidoscope register, UK metalanguage to learner, scaffolding leak `Крок 5:`, hallucinated proper noun `Кнак`, folksy "is a thing" paraphrase, Grade 1 textbook blockquote in adult content).
- **Pt 9** (2026-05-27 afternoon): hardening PRs #2366 + #2367 + #2370 (4-PR Phase 1 hardening; codex brain-pick session named "visible compliance tokens" pattern).
- **Pt 10** (2026-05-27 late afternoon): wiki_coverage manifest cleanup (PR #2371) + Path B dispatched (PR #2372). Phase 2a refire #2 (worktree `185032`) validated hardening: vocab coverage 1/7 → 6/7, all hardening gates pass, single failure `word_count` 1058 < 1104 from structural-density shift.
- **Pt 11** (2026-05-27 night → 2026-05-28 early): user pivoted from "fix V7 prompt" to "render wiki as lesson". Multi-agent discussion. PR #2372 merged tactically. agy-ladder PR #2375 merged. V8 ADR drafted; user redirected to V7.1; cursor consultation in flight.

The Pt 8 m20 IS on production at PR #2364's merge commit — but had the 6 issues. Pt 9-10 fixed the pipeline (not the m20 itself). Pt 11 questions whether the pipeline fix is enough or if the architecture should shift.

## What changed in tooling

- **PR #2375**: gemini fallback ladder now has agy rung. If your local Gemini OAuth is rate-limited/rotated, agy (Antigravity) is tried before falling to gemini-cli flash. **NOT** a guaranteed answer-equivalent — agy has no MCP tool config in this path; treat as availability probe only.
- **#R-PROSE-FLOOR-A1** added to `linear-write.md` per PR #2372. Will survive into V7.1 (or get replaced under V8).
- **WRITER_PROMPT_CEILING_BYTES** bumped from 130KB to 132KB per PR #2372. Will likely drop back below 130KB under V7.1 (rule trimming) or V8 (smaller new prompt).
- **Wiki coverage gate** (PR #2371) — per-item matching + `wiki_coverage_required_items` block in writer prompt. Survives both V7.1 and V8.

## What I left unfinished

1. **Cursor consultation in flight** — response will arrive async. Pickup via SQL snippet above.
2. **ADR rewrite from V8 → V7.1** — pending cursor synthesis.
3. **PR #2374 merge** — pending the ADR rewrite (so the V7.1-recommended doc lands rather than the V8-recommended draft).
4. **This handoff file** — needs to be added to PR #2374 (as a follow-up commit) OR included in a new docs PR on top.
5. **Build worktrees cleanup** — Pt 9-10 forensic worktrees (`185032` is the most important; keep until V7.1 m20 ships clean). Old `073037` / `073705` / `161219` / `163621` / `163804` can be removed after V7.1 ships.

End of 2026-05-27 / 2026-05-28 Pt 11. ~6h continuous orchestrator session. Hand off cleanly.
