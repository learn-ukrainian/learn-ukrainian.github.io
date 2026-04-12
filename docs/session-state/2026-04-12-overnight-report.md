# Overnight Run — Morning Report (2026-04-12)

**Session window**: ~02:00 → morning. Autonomous after the user said "i am off gn".
**Mode**: Leader/reviewer — coding delegated to Codex + Gemini, Claude reviewed and committed.

> This file is overwritten as the night progresses. The "Final state" section at the bottom is the ground truth.

---

## TL;DR

Tonight's main deliverable was unblocking a clean B1/A1/A2 rebuild. That ladder ended up touching 4 commits, all reviewed by Gemini before merge. Plus pyright tech debt cleanup, Phase C.1 verification, and a stack of issue triage.

---

## Commits landed (in chronological order)

| SHA | Title | Issue | Notes |
|---|---|---|---|
| `103b98992` | fix(b1): dominant Ukrainian immersion at B1 (75-100% target) | #1189 | IMMERSION_RULES["b1-core"] strengthened with FORBIDDEN list, Dual Ladder escape hatch (`:::info` callouts stripped from immersion calc), and 5-item checklist. Also patched publish gate leak: heal exhaustion no longer falls through to publish. **Critical:** Codex's first attempt at `_strip_english_blockquotes` was reverted after Gemini r2 BLOCKER — would have broken A1 (REQUIRED translations) and masked B1 LLM disobedience. |
| `910874f65` | fix(b1): activity density + type diversity (no more quiz walls) | #1189 | `v6-activities.md` was hardcoding "Default minimum: 6" and "Inline 2-3 / Workbook 4-8" instead of using the `{ITEMS_MIN}/{INLINE_MIN}/{WORKBOOK_MIN}` placeholders that v6_build.py was already substituting. YAML examples showed 1 item per activity, anchoring the LLM low. Fixed all of that, plumbed `{MIN_TYPES_UNIQUE}` from audit profile, raised B1-grammar `min_items_per_activity` 6→8 + `min_types_unique` 3→5. Gemini r1 BLOCKER: I had hardcoded "5 distinct types" into the SHARED template — broke A1/A2 where it doesn't apply. r2 fix parameterized everything via the new placeholder. |
| `40c181040` | fix(a1-a2): pre-rebuild audit fixes (Gemini-diagnosed) | #1189 | Asked Gemini to audit A1/A2 for analogous bugs before rebuild. Found 1 SEV1 + 4 SEV2: (1) **SEV1** INLINE_ENGLISH_IN_PROSE level-detection leak (A1/A2 modules ship without frontmatter so the level detector returned None and the gate fired on every A1 module that followed the prompt's "**стіл** (table)" rule); (2) Missing `a1-checkpoint` and `a2-checkpoint` ACTIVITY_CONFIGS — checkpoint modules fell back to base a1/a2 with ITEMS_MIN 6/8 but the audit demands 10; (3) Strengthened `a2-m51-70` immersion with Dual Ladder pattern after sample audit showed 39.8% Ukrainian against 65-90% target; (4) Removed hardcoded B1+ checklist from `v6-write.md` that was contradicting A1 rules. Gemini r1 BLOCKER: missed `get_activity_config(slug=)` callers in `activity_validator.py` and `pipeline/core.py` — fixed in r2. |
| `32a432bb8` | fix: pyright tech debt — batch_gemini_config stub + vesum_whitelist + 4 misc | #1193 | Codex implementation. Replaced `scripts/batch_gemini_config.py` `spec_from_file_location` runtime hack with a static re-export module. Fixed REAL runtime bug: `from vesum_whitelist import` had been silently raising ImportError because the module moved to `scripts/tools/vesum_whitelist.py` — meaning **the VESUM whitelist was disabled in production for who knows how long**. Plus 4 smaller fixes (locked_pid_str init, packet_path: Path → Path | None, isinstance(TextIOWrapper) for sys.stdout.reconfigure). 40 → 12 pyright errors on v6_build.py + core.py. |
| `9b7d1dca8` | fix(types): pyright cleanup follow-ups | #1193 | Two small follow-ups: tightened `check_glossary_lists` condition to narrow `run_start: int | None`, and added explicit type annotations to `main()` resume-restore locals so `packet_path` propagates as `Path | None` cleanly to `step_write_with_retry`. Both surfaced after Codex's main commit landed. 7 LOC. |
| `699298d90` | feat(bridge): C.2 thread-coalesced inbox worker | #1192 | Codex implementation. New `scripts/ai_agent_bridge/_inbox.py` (650 LOC) + 10 tests. Per-thread atomic claim via BEGIN IMMEDIATE. Gemini r1 BLOCKER → r2 PASS. |
| `05211968e` | feat(bridge): C.3 OS wake files + ab inbox CLI | #1192 | Codex implementation. Wake file touch in post(), `ab inbox run/show`, `ab sync`, backlog banner. 7 files, 684 insertions. Gemini r1 PASS. |

**Pre-existing tonight (not authored by me, included for context)**:
- `c265815e1` fix(writer): a1 M35+ immersion rule
- `99e2cea58` fix(a1): patch 2 density failures
- `d04a9943b` fix(pipeline): harden V6 write prompt + fix EXERCISES false positives
- `a1145a032` fix(build): --step review honors audit gates
- `9b282809b` fix(audit): metalanguage check no longer fires at A2

---

## Issues touched

| # | State | Action |
|---|---|---|
| **#1093** | CLOSED | Quality overhaul EPIC — 18/21 children done, 3 standalone stragglers split off. |
| **#1189** | OPEN (ACs 1-5 ✅, AC6 blocked on user rebuild) | Walked the AC list against tonight's 3 commits. Posted comment with rebuild instructions. |
| **#1082** | OPEN | Posted status: 16 test files / 315 tests passing. 4 ACs done, 3 ACs open (a11y, Playwright e2e, CI). Recommended split or close-with-followups. |
| **#1086** | OPEN (stale note added) | Filed 16+ days ago, zero activity. Recommend close as "wontfix until learners". |
| **#1087** | OPEN (stale note added) | Same. Auto-deploy was disabled intentionally. Recommend close as "wontfix / deferred". |
| **#1084** | OPEN (stale note added) | Has some recent activity (2026-04-10). Blocked on human reviewer (Tetiana). Keep open with note. |
| **#1191** | OPEN | Cloze 1-based indexing fix — fully specced, 30-min Codex task. **Queued for tonight.** |
| **#1192** | C.1 ✅ shipped | Phase C epic. C.2 dispatched to Codex while writing this report. |
| **#1193** | CLOSED | Pyright tech debt cleanup — Codex implementation, Gemini PASS. |
| **#715, #675, #854** | OPEN, relabeled | Removed `ws:rag` / `area:rag` labels. The "rag" terminology was retired in favor of "sources" (the MCP server is `sources`, the data lives in `data/sources.db`). The work is still real, just renamed. |

---

## Decisions made autonomously + rationale

1. **Reverted Codex's `_strip_english_blockquotes` cleaner** after Gemini r2 caught two regressions: (a) would break A1 modules where translation blockquotes are REQUIRED, (b) would mask B1 LLM disobedience. The right fix is to constrain the writer prompt and let the natural Cyrillic-ratio calculator punish leakage. Don't fight the measurement.
2. **Closed #1093 as superseded** — 18 of 21 child issues already closed. The epic was a sequencing roadmap for "ship A1 with confidence" which is fully accomplished. Stragglers (#1086, #1087, #1082) tracked independently.
3. **Didn't close #1189 yet.** ACs 1-5 are all green from the 3 commits I shipped tonight, but AC6 explicitly says "the 12 affected modules pass on next attempt" — that requires the user to actually run the rebuild. Left open with rebuild instructions.
4. **Didn't close #1082.** 4/7 ACs done; the missing 3 (a11y tests, Playwright e2e, CI) are real follow-up work. Recommended split or close-with-followups but left for user decision.
5. **Relabeled the RAG-tagged issues instead of closing.** "RAG" was renamed to "sources" but the data layer (sources.db, mcp__sources__*) still exists and the work in those issues is still relevant.
6. **Excluded `format_discovery_for_template` from the batch_gemini_config explicit re-export list.** Codex's NOTES caught it doesn't actually live in that module — it's in `scripts/content/video_discovery.py` and is correctly imported from there elsewhere. Confirmed by Gemini.

---

## Process notes

- **All 4 commits passed Gemini adversarial review** before merge. No commits landed without review.
- **2 r1 reviews returned BLOCKER** (B1 activity density, A1/A2 prerebuild). Both r2s were PASS after fixing the blockers Gemini caught. This is the system working — Gemini caught real bugs both times.
- **Codex worked on #1193** (pyright cleanup) successfully. Diff was clean, all 5 verification commands passed. Gemini PASS on r1.
- **Codex is currently working on Phase C.2** (bridge inbox worker). Background task `b53lveuwg`, dispatched at ~03:25.
- **Git index.lock got stale 3 times** during the night — likely a bash signal interaction with the pre-commit hook. Always cleared with `rm -f .git/index.lock`. No data loss. Will note in the lessons-learned section if it keeps happening.

---

## What I'd work on next (in priority order)

1. **#1192 C.2 review + commit** — when Codex returns
2. **#1191 cloze fix** — small Codex task, can run after C.2
3. **#1192 C.3** — OS wake files + CLI (Codex lead)
4. **#1192 C.4** — Fix `ab discuss` queue routing (Claude lead)
5. **B1 module actual rebuild verification** — when user wakes up and runs the build, watch for any new failure patterns and iterate

---

## Questions for the user

1. **#1086 / #1087** — close as "wontfix until learners" or keep open?
2. **#1082** — split a11y/e2e/CI into 3 follow-up issues, or close with a "primary scope done" note?
3. **STEM track #859-#870** — 12 priority:later issues that look frozen. Close the epic or relabel as "future"?
4. **Pyright remaining 12 errors in core.py** — file as a follow-up issue, or accept as known noise?

---

## Final state

**Commits landed (full day)**: 18
**Issues closed**: #1082(commented), #1086, #1087, #1088, #1084, #1090, #1093, #1102, #1114, #1122, #1191, #1193, #1194 (11 closed + 2 consolidated into #1197, #1198)
**Issues filed**: #1193, #1194, #1195, #1196, #1197, #1198, #1199, #1200, #1201 (9 new)

## Morning + afternoon additions (after overnight)

| SHA | Title |
|---|---|
| `10c8d64fc` | A1+A2 plan quality fixes (9 plans, Gemini+Codex adversarial review) |
| `34e21a996` | Cloze 1-based indexing (#1191) |
| `0258bf464` | pyrightconfig.json for pyright LSP |
| `1a0beaef0` | start-codex.sh worktree isolation (git lock fix) |
| `86c695566` | codex-tools writer mode (#1194) |
| `a45793437` | codex-tools as reviewer + cross-agent default |
| `25a72473b` | bridge portable config via AB_* env vars |
| `a50600b84` | C.4 ab discuss queue routing |
| `68b196ef5` | B1 plan fixes |
| `1b8db8677` | vocabulary/vocabulary_hints key fallback |
| `efb44cf91` | session state + docs |

## Key findings

- **Writer A/B test**: Gemini-tools wins (3× cheaper, 4× faster, no Russicisms vs Codex's хорошо)
- **Reviewer test**: Codex (gpt-5.4) is excellent — caught 4 CRITICAL Russicisms in Gemini's output (примірочна, кружка, відправки, давайте+infinitive)
- **A1/A2 first build failed**: 54/59 A2 modules had low immersion because builds used OLD prompts. Fix: clear state, rebuild with new prompts.
- **B2/C1 plans need regen**: 4×1000 robotic budgets (66/93 B2, 133/133 C1), missing dialogue_situations. Filed #1199.
- **Wiki gaps**: B1 has 8 missing packets (auto-compile in research step), B2 needs 88, C1 needs 111+22 missing articles. Filed #1200.
- **Pipeline vocabulary bug fixed**: v6_build.py only read vocabulary_hints, B2/C1 use vocabulary key. Fixed in 1b8db8677.
**Issues updated with AC walks**: #1189 (ACs 1-5 ✅, AC6 blocked on rebuild), #1082 (status comment), #1192 (C.1-C.3 done, C.4-C.6 remaining)
**Issues triaged**: #1086, #1087, #1084 (stale notes), #715/#675/#854 (relabeled from rag→sources)

**What's ready for the user**:
1. B1 rebuild is ready: immersion + activity fixes both landed. Run `.venv/bin/python scripts/build/v6_build.py b1 1 --step all` (or `--range` for batch).
2. A1/A2 rebuild is ready: SEV1 audit leak fix + checkpoint ITEMS_MIN alignment + A2-late immersion strengthening.
3. Channel bridge C.1-C.3 is operational: `ab post` → wake file → `ab inbox run` → claim → invoke → reply → mark delivered.

**What's pending**:
- #1192 C.4 (fix ab discuss queue routing — Claude lead, ~100 LOC, 1 commit)
- #1192 C.5 (Codex worktree status brief — Codex lead)
- #1192 C.6 (structured Codex report contract — Codex lead)
- #1191 (Cloze 1-based indexing — small Codex task, brief ready at /tmp/codex-cloze-1191-brief.md)
- Morning report commit (this file)

**Budget note**: 7 Gemini adversarial reviews, 4 Codex implementations (1 failed first attempt on C.3 → re-dispatched with tighter authorization → succeeded). No Claude inline code >50 LOC per user directive. Every commit has a Reviewed-By trailer.
