---
date: 2026-05-22
session: "Engagement gates shipped + M1 plan fix + fresh build #12 firing — A1.1 build queue queued"
status: yellow-2-PRs-tonight + 1-build-in-flight + 4-A1-plan-followups-queued
main_sha: 954966b5ea  # PR #2204 merge
main_green: clean (review/review advisory persists on every PR)
working_tree_dirty: starlight/src/content/docs/a1/my-morning.mdx still has the manually-assembled build #11 preview; clean once promote runs
prs_merged_this_session:
  - "#2204 feat(linear_pipeline): engagement_floor + russianisms_strict gates"
prs_wip_unmerged:
  - "#2205 fix(plans/a1/sounds-letters-and-hello): drop 1pl imp + low-freq И key-word — awaiting CI"
active_dispatches: []
active_builds:
  - "a1/my-morning fresh build (claude-tools writer) at .worktrees/builds/a1-my-morning-20260521-224207 — fired 22:42 UTC, currently in writer phase"
builds_completed_this_session: []
headline_finding: "The engagement_floor + russianisms_strict gates landed (#2204) restoring the V6 pedagogical floor V7 had silently dropped. Build #11 of a1/my-morning had REVISE'd on engagement with no critique because no rubric existed — the new deterministic gates close that gap and the reviewer prompt narrows the LLM dim to judgment-only. Build #12 (fresh, claude-tools writer, --worktree) fired against this new gate set at 22:42 UTC. Plan-level audit follow-up #2205 also opened — M-2 + M-3 fixes on sounds-letters-and-hello v1.6.3 (Прочитаймо→Прочитай, ирій→іній). M5/M6/M7 plan fixes deliberately deferred to morning when human judgment can re-validate the Surzhyk-drill decisions."
next_session_first_item: "Read the build #12 result. If module_done → run scripts/sync/promote_module.py --latest --level a1 --slug my-morning to land the first complete V7 module on main. If still failing on the new engagement_floor, the writer log + module.md tells the story — most likely outcome is that the writer prompt does produce the callouts (the prompt is now explicit about the floor) and the LLM engagement dim either passes or returns concrete residual feedback."
---

# 2026-05-22→23 Engagement gates shipped + M1 plan fix + build #12 firing

## TL;DR

Two PRs tonight, one build in flight:

| # | Subject | Status |
|---|---|---|
| **#2204** | engagement_floor + russianisms_strict gates restore V6 pedagogical floor | **merged** |
| **#2205** | A1.1 M1 plan fix (1pl imp + low-freq И) | open, CI pending |
| Build #12 | fresh a1/my-morning against new gates | in flight |

The engagement-without-critique failure mode from build #11 is now structurally impossible: deterministic gates handle callout counting + META_NARRATION; the LLM dim is narrowed to "does the hook actually hook" judgment work only.

## Section 1 — PR #2204 landed: engagement_floor + russianisms_strict gates

### What V7 had dropped from V6 (the gap this PR closes)

| Dropped V6 signal | Where it lived | V7 status before this PR |
|---|---|---|
| `engagement & tone` rubric with REWARD/DEDUCT criteria + weights | `v6-review.md` L118 | LLM dim received no rubric beyond "map to {DIM}" — that's why the gemini-pro reviewer scored 6.5/10 REVISE with NO critique field on build #11 |
| Callout minimum (≥3 per module per V6, relaxed to ≥2 per `module-content-quality.md` L97) | V6 writer prompt L537 | not enforced anywhere in V7 |
| META_NARRATION ban (forbidden phrases like `In this section…`, `Welcome to A1…`, `You have unlocked…`) | V6 writer prompt + reviewer DEDUCT list | V7 writer prompt has `No English meta-narration` directive in prose section, but no deterministic check — writer could violate silently |
| SEVERE_RUSSIANISMS list (10-word V6 hard list) | `scripts/build/quick_verify.py` #1189 | quick_verify never wired into V7 pipeline |

### What the PR adds

Two deterministic gates wired into `run_python_qg`:

1. **`engagement_floor`** — `_engagement_floor_gate(text, plan)`:
   - **Callouts**: ≥2 per module. Accepts both Starlight directive blocks (`:::tip|:::note|:::caution|:::warning|:::important|:::info`) and GitHub-style admonitions (`> [!myth-buster]`, `> [!history-bite]`, `> [!tip]`, etc.). Pattern is case-insensitive multi-line. The floor is intentionally LOW — exceeding it is rewarded by the LLM engagement dim's residual judgment, not by stacking more callouts.
   - **META_NARRATION**: HARD 0. Catches `Let us begin/explore/examine/look/learn/see/consider/now`, `In this section/module/lesson/chapter/unit`, `Welcome to A1`, `Congratulations on completing`, `You have unlocked`, `You now possess`, `Your journey begins/starts/continues`. Note: bare `Notice that…` / `Observe how…` are deliberately NOT in this list — V6 rewarded them when content-anchored ("Notice the soft sign in **писатися**"), and that distinction stays in the LLM dim.

2. **`russianisms_strict`** — `_russianisms_strict_gate(text)`:
   - Wraps the project's mature 676-line `check_russicisms` (curated regex patterns: `приймати участь`, `самий кращий`, `получати`, `відноситися`, `слідуючий`, `давайте попрактикуємо`, dozens more)
   - PLUS the UA-GEC corpus (`check_ua_gec_calques`): 8,937 human-annotated Ukrainian error→correction pairs from the Grammarly UA team, filtered to F/Calque + F/Collocation + G/Case + G/Gender tags.
   - Gate fails on any `critical` severity finding (3+ distinct russicisms per existing severity rule). Lower-severity findings surface as advisory signal to the LLM dim.
   - Note: `_split_narrative_zones` skips dialogue + code + quote contexts — the gate runs on prose only, so quoted "wrong" learner forms in dialogue activities are not flagged.

### Reviewer prompt rewrite (`linear-review-dim.md`)

Added an explicit "JUDGMENT ONLY — do NOT re-litigate deterministic gates" scope preamble. Per-dim residual rubric for engagement / pedagogical / naturalness / decolonization / tone. A reviewer score that re-states what a deterministic gate already enforces is declared a reviewer-protocol failure.

### Writer prompt rewrite (`linear-write.md`)

Both gates documented with explicit thresholds + the heritage-defense escape hatch via `mcp__sources__search_heritage` for ambiguous archaism cases (load-bearing example: `кобета`/`кобіта` is regional, not russicism — the heritage tool surfaces Lviv + СУМ-20 evidence and keeps `is_russianism=false`). Russianism authority hierarchy spelled out: VESUM → Правопис 2019 → Горох → Антоненко-Давидович → Грінченко.

### Tests

- `tests/build/test_engagement_floor_gate.py` (NEW, 16 tests): callout counting, both directive syntaxes, META_NARRATION variants, russianism critical-vs-warning behavior, UA-GEC calque shape.
- `tests/build/test_linear_pipeline.py::test_run_python_qg_passes_structural_fixture`: fixture updated with two content-anchored callouts (reflexive-verb mnemonic + `-ся` myth-buster) so the existing canary passes the new floor.

### CI

All non-advisory blocking checks green. `review / review` failed as expected (Gemini-Dispatch auth-broken advisory — handoff Section 7 #9, every PR shows it, safe to ignore for merge decisions).

## Section 2 — PR #2205: M1 plan fix

Plan-review 2026-05-13 (`audit/2026-05-13/first-7-summary` M-2 + M-3) flagged two MEDIUM issues on `sounds-letters-and-hello`:

- **M-2**: 1pl imperative `Прочитаймо «Привіт» по літерах` in `content_outline[3].points[3]`. State Standard 2024 §4.2.4.2 limits A1 imperative to 2nd-person only — 1pl + 3rd-person belong to A2. Used as teacher meta-language, but writer could render in prose. Swap to 2sg `Прочитай`.
- **M-3**: Key-word `ирій` for letter И is extremely low-frequency (poetic/mythological — folklore "warm southern land for migratory birds"). NUS A1 bukvars pair И with `іній` (frost — high-frequency, concrete) per Захарійчук 1кл. с.46, Большакова 1кл. с.32. Swap to `іній`.

Version 1.6.2 → 1.6.3. New `plan_fixes` entry with rationale + source citations. `lifecycle: locked` preserved via standard `plan_fixes` + `.bak` discipline.

PR open at #2205, awaiting CI. Merge unblocks the A1.1 letter-module build queue when a1/my-morning ships.

## Section 3 — Build #12 (fresh) firing right now

```
.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --worktree --writer claude-tools
```

- Worktree: `.worktrees/builds/a1-my-morning-20260521-224207/`
- Started: 22:42 UTC 2026-05-21
- Writer: claude-tools (per writer-selection ADR `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` REVISED 2026-05-12 — codex-tools had `tool_calls_total=0`, claude-tools 4 calls + module)

**Key difference from build #11**: writer prompt now documents both new gates. Expected outcomes (in priority order):

1. **Most likely (P0.7)**: writer produces callouts (the prompt is explicit) → `engagement_floor` passes → llm_qg engagement dim either passes (residual quality only) or returns concrete residual feedback → mdx → green.
2. **Possible (P0.25)**: writer still emits ≤1 callout (e.g. interprets "≥2" as "1 is fine if rich") → `engagement_floor` fails with concrete feedback → ADR-008 correction path applies → second iteration adds callouts.
3. **Edge (P0.05)**: writer adds 2+ callouts but `russianisms_strict` triggers on something the writer didn't realize was a calque → critical finding lists offending phrases → correction.

If module_done lands: `scripts/sync/promote_module.py --latest --level a1 --slug my-morning` to land the first complete V7 module on main.

## Section 4 — Deferred to morning (M5/M6/M7 plan fixes)

The plan-review 2026-05-13 audit named 4 NEEDS_FIX plans for the A1.1 batch. Tonight I applied only M1 (purely mechanical word swaps). M5/M6/M7 require a fresh judgment pass and are deliberately queued for the morning:

| # | slug | issue | why it needs daylight judgment |
|---|---|---|---|
| M5 | who-am-i | HIGH: `Підсумок` section has `words: 0` | Two fix options (delete OR allocate 50+rebalance). The note "Самоперевірка включена до практики діалогів" suggests the section was intentionally zeroed — deciding which option to take needs the orchestrator to look at the actual section content first, not a mechanical rule. |
| M6 | my-family | MEDIUM: `муж/чоловік` Surzhyk-framing oversimplified | `муж` IS in VESUM as Ukrainian (archaic/elevated: "державні мужі"). Framing as wrong vs `чоловік` is overreach — like the `тато/папа` case M6 itself dropped in v1.4.0. Fix is either drop the row OR add register-note. The "drop" call is cleanest but loses a teachable Surzhyk-drill row. Morning judgment. |
| M7 | checkpoint-first-contact | HIGH: `тато/папа` pair contradicts M6's documented discipline | M6's v1.4.0 changelog explicitly dropped this exact pair with the reasoning "VESUM lists `папа` without restrictive tags." M7 then re-introduces the contradiction. Fix is remove the row from M7. Mechanically clear, but the wider question is: should M7's whole Surzhyk-drill activity get the VESUM-verify discipline added inline, to prevent regression? That's an activity-level rewrite, not a 1-line swap. |

Plus the cross-cutting CC-1 item: add `pedagogical_deviations_from_standard:` field convention to plans that use case-form frozen chunks before the State Standard introduction module (M5 acc, M5/M6 gen). That's a curriculum-wide schema enhancement — bigger than a single PR, separate workstream.

## Section 5 — A1.1 build queue (status as of handoff)

| seq | slug | plan version | plan status | build status |
|-----|------|--------------|-------------|--------------|
| 1 | sounds-letters-and-hello | 1.6.3 (PR #2205 pending) | NEEDS_FIX → FIXED on #2205 merge | not built |
| 2 | reading-ukrainian | locked | LOCK_NOW (PASS) | not built |
| 3 | special-signs | locked | LOCK_NOW (PASS) | not built |
| 4 | stress-and-melody | locked | LOCK_NOW (PASS, 1 MEDIUM TTS forward-looking) | not built |
| 5 | who-am-i | locked v1.2.0 | NEEDS_FIX (HIGH: Підсумок=0) | not built |
| 6 | my-family | locked v1.4.0 | PASS borderline (MEDIUM муж/чоловік) | not built |
| 7 | checkpoint-first-contact | locked v1.2.1 | NEEDS_FIX (HIGH: тато/папа contradiction) | not built |

The first 3 plans that are LOCK_NOW + pass — `reading-ukrainian`, `special-signs`, `stress-and-melody` — can enter the build queue immediately once a1/my-morning ships and the V7 pipeline is proven end-to-end on a real module.

## Section 6 — Active state at handoff

- **Active dispatches**: 0
- **Active builds**: 1 (a1/my-morning, in writer phase, ETA ~14 min for writer + ~5-15 min for downstream)
- **Open PRs**: 1 (#2205, CI pending)
- **Origin/main**: `954966b5ea` (PR #2204 merge)
- **Build worktrees preserved per #M-10** (do not delete):
  - `.worktrees/builds/a1-my-morning-20260521-202848` (build #11 — manually-assembled MDX source, still live on starlight)
  - `.worktrees/builds/a1-my-morning-20260521-195056` (build #10)
  - older builds from yesterday's cascade
- **Starlight dev server up** on http://localhost:4321 (PID 45551)
- **Monitor API up** on http://localhost:8765
- **Sources MCP up** on http://localhost:8766

## Section 7 — Open follow-ups (renumbered)

| # | Subject | Priority | Notes |
|---|---|---|---|
| 1 | a1/my-morning build #12 result | **P0 in flight** | If module_done → promote. If gate fail → investigate correction path. |
| 2 | Merge #2205 (M1 plan fix) | P0 morning | small mechanical PR, CI pending |
| 3 | Apply M5/M6/M7 plan fixes | P0 morning | per Section 4 — needs daylight judgment on Surzhyk-drill rows |
| 4 | Fire builds for first 7 A1 modules (after #1 lands + plan fixes done) | **P0 the "tough work"** | start with the 3 LOCK_NOW plans (M2/M3/M4) once my-morning proves the pipeline |
| 5 | inline/workbook activity split | P1 | V7 writer emits flat array; activity_repair.py patches but writer has no control over placement |
| 6 | Other V6 anti-patterns deterministically | P1 | `Українською:` meta-frame, mixed-language clauses, Forbidden Tropes — separate small PRs |
| 7 | Cross-validate gemini-tools + deepseek-tools writers | P1 | inherited |
| 8 | `pedagogical_deviations_from_standard:` plan field convention (CC-1) | P2 | curriculum-wide schema enhancement |
| 9 | Holistic gate-quality audit | P2 | may be moot once #1, #3 land |
| 10 | codex-tools rollout-flush race | P2 | inherited |
| 11 | PR #2168 amelina stub blocker | low | inherited (Gemini PR with Curriculum Plans CI fail) |
| 12 | `review / review` CI auth broken | P2 | inherited; every PR shows this advisory fail; safe to ignore for merge decisions |

## Section 8 — Tonight's wins

- ✅ Engagement gap that built #11 silently shipped past is now structurally impossible
- ✅ Russianism detection layer (676 patterns + 8,937 UA-GEC pairs) finally wired into pipeline
- ✅ Reviewer dim narrowed to judgment-only — no more "REVISE 6.5/10 with no critique"
- ✅ M-2 + M-3 plan fixes shipped on PR #2205 — first of 4 first-7 plan follow-ups
- ✅ Build #12 of a1/my-morning firing against the new gate set

User went to sleep with `i ma goiong to see contnue on your own and utilise the agents, fiscuss things with them , work togehter, we are really close to be able to ship a module and then have to start wroking on the first 7 modules of a1 which will be tough`.

The first complete V7 module is one Monitor notification away. Tomorrow's tough work starts with three LOCK_NOW plans + four plan-fix small PRs + a deterministic gate layer that finally enforces what V6 used to.

Good night.
