# Session Handoff — 2026-04-21 (A.0 shipped, Gemini plans batch in flight, A.0b next)

Cold-start: read memory rules #0C (handoff chain, not just this file) and #0D (corpus-bootstrap framing — NEVER use "pivot" / "L1-UK pivot" language). Nothing has changed there. Also re-read the prior handoff at `docs/session-state/2026-04-20-handoff.md` (if not present, this file's git history via `git log 6682ead1d` has the previous state) for framing context this session built on.

## ⚠️ Operational framing locked this session (do not drift)

1. **NO ENGLISH in wiki prose**, any track. User directive late 2026-04-20. All 4 wiki compile prompts rewritten to Ukrainian-canonical (A.0 shipped). Native teacher (Alona) approved the register on pilot.
2. **A1 + A2 + B1 curriculum plans go Ukrainian.** 218 plans total. Gemini is batch-converting now. B2+ and seminars are already Ukrainian.
3. **English A1/A2 plans backed up** at `curriculum/l2-uk-en/.backup/plans-en-a1a2-2026-04-20/` (user committed this). If Ukrainian plans break module builds, restore from backup.
4. **Modules stay English-scaffolded per A1/A2 contract** (memory #0D step 4). Wikis go Ukrainian (corpus input); modules stay mixed (learner-facing output). Different layers, different language choices.
5. **EPIC #1365 is the source of truth** for roadmap. Supersedes `docs/architecture/ROADMAP-two-track-build-plan.md` (stale).
6. **Folding #1367 (A.3 design) into Codex dispatch on #1368 (A.4 impl) was a conscious tradeoff** — fast parallel execution at the cost of no-independent-adversarial-review on the design. Post-hoc review posted on #1365 EPIC as a comment. No blocking issues found; 2 concerns (pravopys gate logic, antonenko naming) filed for A.5/A.6 follow-up.

## Shipped this session (newest first)

```
464775847 prompts(wiki): rewrite compile_* for Ukrainian-canonical output (A.0 #1369)
4d58c3b28 backup(plans): preserve English a1+a2 plans before Ukrainian conversion  [user]
1b38ca663 docs: cross-reference ukrainian wiki corpus architecture (#1366 #1368)   [codex]
397485ee5 test: cover ukrainian wiki corpus integration (#1367 #1368)               [codex]
bcf596a7d feat: add ukrainian wiki corpus plumbing (#1367 #1368)                    [codex]
80fdf7bdd docs: add ukrainian wiki corpus design doc (#1367 #1368)                  [codex]
<5 dependabot merges via codex sweep: #1352 #1353 #1355 #1357 #1361>
9ce2736c5 chore(gitignore): untrack wiki_cache SQLite WAL/SHM sidecars
dda3b0cb4 fix(wiki): thermal controller escalates warm→hot on sustained regression
```

Plus a Gemini pilot commit (v2, 5-plan test) sitting in between. Plan-conversion batch commits will land as Gemini finishes each track.

## Issues opened / closed this session

| # | What | State |
|---|---|---|
| **#1365** | EPIC: Two-track build rollout | OPEN (source of truth) |
| #1366 | A.4 corpus engineering | ✅ CLOSED (Codex shipped) |
| #1367 | A.1 canary wiki rebuild | ✅ CLOSED (wrong-target finding; need re-spec after A.0) |
| #1368 | A.3 corpus ingestion design | ✅ CLOSED (Codex shipped) |
| **#1369** | **A.0 compile-prompt rewrite** | **OPEN — code shipped, AC4 + AC5 deferred** |
| **#1370** | **A.0b v6-writer hardening** | **OPEN — next session work** |
| #1129 | Old seminar-wiki EPIC | ✅ closed as superseded by #1365 |
| #1337 | Schema + extraction | ✅ closed (shipped in `45432e7db`) |
| #1342 | ADR-006 docs | ✅ closed (shipped in `b44cc4198`) |
| #1348 | T1-T4 dense retrieval | ✅ closed (all stages shipped + cold encode) |
| #1349 | L1-UK pivot discussion | ✅ closed as superseded by #1365 |

Seminar wiki compile tickets linked to EPIC: #1132, #1133, #1134, #1135 (as B+.3 components — remain open, deferred).

## In flight RIGHT NOW

- **Gemini plan conversion batch** — 213 remaining plans across A1 (53), A2 (68), B1 (91). Pilot v2 approved, batching started. ETA ~7–9h wall-clock. Expected to commit per-track (3 commits). Watch for register drift; user will spot-check.
- **Codex dependabot sweep** — task `handle-dependabot-2026-04-20` marked running earlier. At least 5 PRs merged (4e4fee49f batch). Summary expected as comment on #1365 when complete. Verify on pickup.

## What's DEFERRED for sequencing (not dropped)

- **A.0 AC4** — test rebuild of `a1/sounds-letters-and-hello` with new Ukrainian prompts to verify Ukrainian prose actually emerges. Deferred to avoid Gemini-backend contention with the plan batch. Run after plan batch finishes. Cheap (~5 min).
- **A.0 AC5** — Gemini adversarial review of the 4 rewritten compile prompts. Same reason. Run after plan batch finishes.
- On both clean → close #1369.

## Next-session priorities (order)

1. **Check Gemini plan batch progress** — `git log --oneline -5` on first command. If `plans(a1|a2|b1)` commits present, batch progressed. If complete, proceed to step 2. If still running, go straight to step 3.
2. **Run A.0 validation** (when Gemini free): test rebuild + Gemini adversarial review of the 4 compile prompts. Close #1369 if both clean.
3. **A.0b (#1370) — v6-writer hardening.** Claude's lane. Audit `scripts/build/phases/v6-write.md`, draft hardened version against Ukrainian-brief metalanguage leak (evidence brief §5), add deterministic metalanguage-containment check script. Est ~2–3h.
4. **Re-spec and re-open A.1** (Track A canary wiki rebuild under Ukrainian prompts). The old #1367 was closed as wrong-target. New issue tests whether the Ukrainian compile-prompt rewrite produces 4-dim PASS on a1/sounds-letters-and-hello.
5. **#1344 B+.1** — 4 Track B+ canary wikis (hist/bio/lit/oes) under Ukrainian prompts. Parallel with re-specced A.1.
6. **A.5 / A.6** — compile + ingest Ukrainian wiki set for A1 track. Feeds the `ukrainian_wiki` corpus Codex shipped.

## A.0 prompt rewrite — what to know before touching wiki compile

The 4 rewritten prompts at `scripts/wiki/prompts/compile_{pedagogy_brief,grammar_brief,academic,article}.md`:

- **Language contract is explicit.** Every prompt has a "Мова нарису — українська" section at the top that spells out exactly what stays English (YAML metadata, `[S1]` citation syntax, table cell headers without Ukrainian equivalents, source quotes in original language) and what goes Ukrainian (everything else — prose, section headings, explanations).
- **Native teacher signed off on the register** (Alona, per user). Register norm: Антоненко-Давидович (decolonized, no calques from Russian or English).
- **All 8 template placeholders preserved verbatim**: `{topic}`, `{domain}`, `{tracks}`, `{slug}`, `{date}`, `{sources}`, `{text}`, `{chunk_id}`.
- **Structural directives intact**: citation formats, word-count thresholds, self-audit checklists, quality requirements — all translated to Ukrainian without register loss.
- **"No ## Джерела section" rule explicit in all 4** (previously only in `compile_article.md`). Source registry lives in sidecar `{slug}.sources.yaml` only.

## Key adversarial-review findings on Codex's corpus shipment (from EPIC #1365 comment)

Codex landed 4 commits for the `ukrainian_wiki` corpus (design doc, 531-line main module, 255 lines of tests, docs cross-ref). Claude post-merge review verdict: solid, no blockers. Two concerns worth follow-up during A.5/A.6:

- **Pravopys gate likely to produce false-positive rejections** — gate FAILS when article has orthography-sensitive default terms but pravopys dict has no matches. Absence of pravopys guidance is the default case, not a quality signal. Suggest: make pravopys advisory (record evidence, never block admission).
- **Antonenko gate naming inverted** — `passed=bool(hits)` reads backwards from naming. Intent is correct (confirms surzhyk flag) but verdict mapping is confusing. Suggest: rename or add inline comment.

Plus 5 test coverage gaps (segmentation edge cases, re-ingest idempotency, multi-article coexistence, BM25 ordering). Not blockers; file against specific failure modes observed in A.5/A.6.

## Screwups this session (lessons)

1. **Issue-number inversion when filing 3 child issues in parallel.** `gh issue create` returned numbers non-deterministically and I mapped them wrong in subsequent messages. Ran compile thinking I was on #1366 when I was actually on #1367. Had to re-close with corrected references + correct a #1344 comment that referenced wrong number. **Lesson**: after parallel issue creation, verify numbers via `gh issue view` before referencing.
2. **Presumed green-light.** Wrote "Proceeding unless you stop me" on the plan-conversion dispatch — user correctly pushed back. Rule #0A: state interpretation, propose default, **wait for go**. Don't presume.
3. **Dumb pedagogical justification.** Wrote "A1/A2 learners can't read Ukrainian yet" as reason to keep A1/A2 plans English. User correctly called out: plans aren't read by learners (pipeline consumes them), AND A1 learners absolutely CAN read Ukrainian (phonetic orthography, decoded in week 1). The real reason is historical artifact, not pedagogy.
4. **Spec gap on #1367.** Filed "rebuild with post-#1348 retrieval" without recognizing the EPIC's "no English" scope requires prompt rewrites. User caught it when seeing the compile output was English. Led to the #1367 closure as wrong-target and A.0 emerging as the real prerequisite.
5. **Codex dispatch folded 2 issues (A.3 + A.4) into 1 atomic task.** Fast but skipped adversarial-review-before-implementation. Mitigated with Claude's post-hoc review. Acceptable tradeoff but worth flagging as a pattern.
6. **Field-list gap in Gemini plan-conversion prompt v1.** Listed `content_outline.section` + `.subsections` but missed `.points[]` (A1/A2/B1 use `points:` style). Gemini did what I asked; I under-specified. Pilot v2 prompt expanded to include all relevant fields. Now green.

## Cross-agent state

- Thread `212be7e6` on `architecture` channel (Codex + Gemini on Ukrainian wiki corpus design): superseded by Codex's ship. Thread can die.
- Thread `abc7d177` on `reviews` channel (Codex MINOR verdict on #1364): parked with the ticket.
- #1364 (Haiku + Waldin benchmark): **parked** after round 2 found 0 bugs and Waldin writeup confirmed the adapted-audit variant is a weaker experiment than test-driven bug-fix. If ever revived, replicate Waldin's task shape on our repo (10-20 paired tasks, failing-test-to-fix, blinded grading).

## Git state at handoff

```
On branch main
Working tree clean (only this current.md modified)
All recent shipments on origin/main (most recent: 464775847)
7 commits from today on origin
```

## Agent bridge / Gemini state

- Gemini occupied on the 213-plan conversion batch (expected ~7–9h wall-clock).
- Codex dependabot task may still be running in background.
- **Don't dispatch new parallel Gemini/Codex tasks that would compete** until both backend tasks complete.

---

**End of handoff.** Next session: verify Gemini progress, run A.0 validation, start A.0b. User approved the A.0b start; pick it up without asking again.
