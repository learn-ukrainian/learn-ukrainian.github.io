# Session Handoff — 2026-04-23 (full afternoon)

> Built the wiki + module writer-discipline infrastructure you asked
> for, found a critical tokenizer bug while testing, ran the first
> real Opus writer smoke on a1/colors (6 dims pass, 3 fail for real),
> and dispatched two focused Opus diagnostics on the failing dims.
>
> You return to: 7 open PRs queued for merge + 2 Opus diagnostics
> running + a clear merge order + clear next move.

---

## 7 open PRs, merge in this exact order

| # | Title | Why this order |
|---|---|---|
| **1448** | fix(build): preserve Cyrillic й/ї through NFKD in wiki_compressor tokenizer | **MUST land first.** Silent Unicode bug turning `білий→білии`, `жовтий→жовтии`, `країна→краина` in every plan's `factual_anchors`. Explains why Opus contract compliance kept failing 5×. Every future module build depends on this being right. |
| **1447** | feat(discipline): canonical-anchor registry + citation-bound prompts | Shared registry + writer prompt discipline + mechanical validator + module contract §7a. Both wiki and module writers benefit. 143 tests green. |
| **1442** | fix(wiki): strip Gemini MCP warning + idempotent generated_by_model | Cosmetic clean-up for compile logs; also collapses duplicate `generated_by_model:` entries. Small. |
| **1445** | Backfill wiki source attribution metadata (#1435) | Rewrites ~227 existing `*.sources.yaml` with real attribution via the #1434 resolver. Land AFTER #1447 so any backfilled wikis land clean. |
| **1443** | feat(quality): review-and-lock `things-have-gender` | Scale-lock batch (Claude Opus xhigh, 9/9/9/9/9) |
| **1444** | feat(quality): review-and-lock `what-is-it-like` | Scale-lock batch |
| **1446** | feat(quality): review-and-lock `how-many` | Scale-lock batch |

**Also previously merged this session**: #1437 (special-signs lock),
#1438 (checkpoint-first-contact lock), #1439 (#1434 compiler
attribution), #1440 (#1431 v2 shared contract architectural fix),
#1441 (#1403 auto-merge prevention).

**On `main` directly**: writer default switched from `gemini-tools` →
`claude-tools` (commit `5e2afbd092`). Any fresh A1 module build uses
Opus writer + Codex reviewer.

---

## a1/colors Opus rebuild — the real #1431 viability smoke

Fired earlier today as `v6_build.py a1 10 --writer claude-tools`.
Completed through review. R1 aggregate:

| Dim | Gemini v2 R2 | **Opus R1** | Δ |
|---|---:|---:|---|
| Factual | 5.0 | **8.0** | +3.0 ✅ |
| Language | 7.4 | **10.0** | +2.6 🔥 |
| Decolonization | 7.4 | **10.0** | +2.6 🔥 |
| Completeness | 8.8 | 9.0 | +0.2 |
| Plan Adherence | 7.4 | 8.5 | +1.1 ✅ |
| Dialogue | 6.4 | 10.0 | +3.6 🔥 |
| Actionable | 7.6 | **3.0** | **-4.6 ❌** |
| Naturalness | 4.9 | **4.0** | -0.9 ❌ |
| Honesty | 5.0 | **4.0** | -1.0 ❌ |

MIN = 3.0 → REJECT. **BUT six dims passed, and the Factual/Language/
Decolonization/Dialogue improvements are dramatic.** The «блакитний»-
for-flag class of hallucination is **gone** with Opus.

The three failing dims are *real writer-quality issues*, not bug
artifacts:

- **Actionable 3.0** — Opus produced code-switched pseudo-Ukrainian
  English like `"This модуль taught узгодження кольорів using the
  adjective правилами"`. Writer instructions leaked into student
  prose.
- **Naturalness 4.0** — Same code-switching: `"a вибір букета на
  квітковому ринку"` forces Ukrainian nouns into English syntax
  instead of bolded inline examples. v2 Gemini also failed this dim
  (4.9) — pattern survives writer change.
- **Honesty 4.0** — Opus **fabricated specific textbook citations**
  ("Vashulenko Class 2 illustrates hard group with жовтий м'яч and
  зелений листок" — that textbook doesn't teach the concept at that
  grade and doesn't use those examples). Pre-training-leak into
  corpus-grounded claims.

---

## Running now — 2 Opus diagnostics (90-min each)

Both dispatched via `delegate.py`. Results land as PRs.

### `claude-1449-colors-dim-diagnostics`

Diagnoses root cause of the 3 failing module dims (Actionable,
Naturalness, Honesty). Attribution among: **better plan / better
wiki / better prompt / better corpus / additive writer rule**.

Brief: `.worktree-briefs/claude-1449-colors-dim-diagnostics.md`
Report will land at:
`docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md`

Told to IGNORE failures that are artifacts of #1447 / #1448 (the
bug-report-meta-commentary inside the module), focus on what fails
even with those merged.

### `claude-1450-gemini-wiki-writer-diagnostic`

Diagnoses what Gemini needs to write wiki sources correctly. Core
failure evidence: invented `[S6]`/`[S7]`/`[S8]` citations in
`b2/academic-writing.sources.yaml` (we verified `S2318`, `S746`,
`S276` exist nowhere in sources.db). Pattern applies across many
wikis.

Deliberately NOT self-review: Opus diagnoses Gemini's output because
different priors = different blind spots.

Report will land at:
`docs/reports/2026-04-23-gemini-wiki-writer-diagnosis.md`

Both diagnostics are **diagnostic-only** — no code/prompt/plan
changes land from them. They produce reports + ready-to-dispatch
follow-up briefs. You approve before implementation.

Monitor `bncr8m659` armed on both task IDs.

---

## Key findings today (for future you)

1. **Opus writer DOES fix the factual-hallucination class** (flag
   colors, Russianisms, decolonization framing) — Factual went
   5.0→8.0, Decolonization 7.4→10.0, Language 7.4→10.0.

2. **The remaining failure classes are different under Opus than
   under Gemini**: Gemini failed on parametric fact leaks; Opus
   fails on scaffolding-voice mixing (code-switching English+
   Ukrainian) and on fabricated specific citations.

3. **Infrastructure bugs were masking the real writer-quality
   signal.** #1448 (tokenizer) meant contract-compliance demanded
   impossible-to-satisfy Ukrainian forms and Opus kept trying for 5
   rounds before giving up + writing a meta-commentary bug report
   inside the module (!). That bug report then polluted the Honesty
   dim score.

4. **MIN≥8 rule is the right gate.** Six dims at 8+ and three at 3-4
   is not "passing with caveats" — it's a real failure that needs
   real fixes (or we mint a polished Potemkin module).

---

## What to do first when you return

In order:

1. **Read PR #1448 body first** — understand the tokenizer bug;
   merge it.
2. **Merge PR #1447** — canonical anchors + discipline.
3. **Merge PR #1442** — compile-strip cosmetic.
4. **Check status of the two diagnostic dispatches**. If they've
   finished, you'll have 2 more PRs open with the diagnosis reports.
   Read them before merging anything else.
5. **Re-fire a1/colors build** after #1447 + #1448 merge:

   ```
   rm -rf curriculum/l2-uk-en/a1/orchestration/colors
   rm curriculum/l2-uk-en/a1/colors.md
   rm curriculum/l2-uk-en/a1/review/colors-*
   .venv/bin/python scripts/build/v6_build.py a1 10 --writer claude-tools
   ```

   This is the REAL #1431 viability smoke — Opus writer + Codex
   reviewer + canonical anchors + clean tokenizer + citation
   discipline. Expected to cross MIN≥8 if the three failing dims
   were genuinely artifact-dominated, or to cleanly reveal what
   still breaks if they weren't.

6. **Act on the two diagnostic reports** — each will include a
   dispatch-ready follow-up brief. Approve or refine and fire.

7. **Merge the scale-lock PRs** (#1443 / #1444 / #1446 / #1445) in
   any order. They're independent.

---

## State of the pipeline

- **A1 locks**: 14/55 on main; 17/55 once you merge the 3 scale-lock
  PRs. ~38 A1 slugs left to lock. Next slugs in sequence:
  `this-and-that`, `many-things`, `i-have-i-dont-have`, `i-want-i-can`.
- **A1 modules**: 1 built end-to-end through v6 pipeline (colors,
  which is our current REJECT). 0 passing MIN≥8. 40 legacy `.md`
  files exist but predate current pipeline.
- **Wiki compile**: B2 batch partially started (1 article compiled,
  pending discipline rollout). Once #1447 + #1448 merge, safe to
  kick off the full B2 batch (113 slugs).

---

## Services + environment

All healthy:
- api:8765 — monitor API
- sources MCP:8766 — writer's retrieval tool
- starlight:4321 — user-facing render of compiled wikis

Shell state:
- `GEMINI_AUTH_MODE=subscription` set
- `GEMINI_API_KEY` unset (subscription mode)

Gemini ladder (unchanged from pre-session):
- rung 1: gemini-3.1-pro-preview (primary)
- rung 2: gemini-3-flash-preview (fallback when 3.1-pro rate-limits)
- rung 3: gemini-2.5-pro (emergency)

---

## Open architectural threads — pick up when you have time

1. **Wiki dim-review is still in shadow mode** (`scripts/wiki/
   review.py`). With #1447 landed, the next leverage is turning
   fix-loop ON with a hard-gate. ~1h of work.
2. **#1286 review transport** — worktree has uncommitted Codex work.
   Partial fix (transport hardening works, live `task_complete`
   still broken by upstream Codex 0.122.0). Decide: commit partial
   or wait for upstream.
3. **Codex dispatch pattern** — 3 of 4 Codex dispatches this
   session stopped after writing code + passing tests but did NOT
   commit/push/PR. I had to finalize 2 of them (#1434, #1403). The
   dispatch brief template needs a "your work is NOT done until git
   commit + push + gh pr create" section. I've added this language
   to the most recent briefs; should promote into the dispatch
   template.

---

## Critical rules observed this session

- No auto-merge ever (INCIDENT #1403). User merged #1439 when asked;
  then "you merge you idiot" was explicit user override on the
  previous session's PRs.
- Writer default on main switched to claude-tools per #1431 v2
  finding. Rollback = 1-line edit if needed.
- Action bias stayed strong — no option menus, one decisive
  recommendation per question.
- Subagent/dispatch cap held (max 2 Claude + 2 Codex in flight).
