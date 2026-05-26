---
date: 2026-05-26
session: "Part 6 of the 2026-05-26 multi-session day. Continuation of Pt 5 (codex-tools 27/28 gates, m20 3 tokens short). Drove three workstreams in parallel: (1) word_count overshoot bump to ship round #11, (2) wiki_coverage_gate XML row parser fix after round #11 surfaced a brand-new failure mode, (3) Bio R1a pilot dispatch + review + merge. Round #11 cleared 26/28 python_qg gates; wiki_coverage_gate then HARD-failed all 18 obligations as `implementation_map_missing` because codex-tools emitted `<row .../>` XML but the parser only matched bullet/pipe shapes. PR #2355 fixes that. Round #12 firing as this handoff is written."
status: round-12-in-flight; bio-pilot-merged; scale-up-awaits-user-ok
main_sha: 2386ff3c0a (post PR #2355)
main_green: clean
working_tree_dirty: 0 files (this handoff doc untracked until PR)
---

# 2026-05-26 — Part 6: wiki_coverage parser fix, round #12 firing, bio R1a pilot merged

Read this Pt 6 first. Pt 5 (`2026-05-26-pt5-codex-tools-3-words-short.md`) ended with round #10 missing word_count by 3 tokens. Pt 6 (this) executed the Path A overshoot bump → fired round #11 → discovered a fresh wiki_coverage parser bug → shipped parser fix → fired round #12 → all in parallel with the R1a bio pilot.

## TL;DR for the next orchestrator

1. **5 PRs merged this session.** Main `6f2a440859` → `2386ff3c0a` (5 commits).
2. **Round #12 IS RUNNING** via bridge `bc7lyi3n3` against thread `019e6063-c3da-78d1-acaa-4cd684a08786`. Expected outcome: `module_done` and codex opens m20 anchor PR.
3. **Bio R1a pilot validated 5-agent scale-up plan.** PR #2354 merged with excellent quality. Scale-up to 127 remaining figures **awaits user OK** per Pt 4 plan ("first codex, then gemini, then decide").
4. **First action when round #12 PR opens:** run the 10-check verify-before-promote per `docs/best-practices/v7-design-and-corpus.md` §4 against the codex-opened m20 PR. If green → approve + merge → m20 ships as first V7 A1 anchor. Then optionally fire round #13 with `--writer gemini-tools` for the empirical comparison per Pt 4 plan.

## What landed (in order of merge)

| PR | SHA | Summary |
|---|---|---|
| **#2349** | `c2dd1823e5` | Pt 5 session-state handoff (round #10 3-token miss forensic detail). |
| **#2350** | `6597f33752` | `linear-write.md` word_count overshoot guidance bumped 10-15% → **18-20%** with explicit per-section budgeting at ~1.20× minimum + enumerated the 5 token categories the gate strips. Empirical data from rounds #7-#10 inline. |
| **#2352** | `6add983a02` | 3 dispatch briefs (r1a-pilot + surzhyk-reclassify + writer-prompt-deltas) committed for forensic record. `pytest -x` invocations dropped per #1942 lint rule (caught by pre-commit dispatch-brief guardrail). |
| **#2354** | `76fc518675` | R1a pilot: 3 research dossiers (Драй-Хмара, Свідзінський, Сосюра) by codex GPT-5.5 xhigh. 1531-1553 words each, 4-5 T1/T2 sources per figure, ≥2 primary quotes each, NKVD case # 72569 / charge 54-10 / archival 07993 specifics, source disagreements flagged honestly, no unilateral plan additions (#2353 filed for cross-track gap). |
| **#2355** | `2386ff3c0a` | `parse_implementation_map` accepts `<row obligation_id="..." artifact="..." location="..." treatment="..." />` XML shape alongside the existing bullet/pipe shapes. End-to-end verified against round #11's writer_output.raw.md: now reads 18/18 obligations. +2 regression tests. |

## m20 anchor build round-by-round empirical record (extended)

| Round | Main SHA at build | Writer | Outcome | Gates failed | Key signal |
|---|---|---|---|---|---|
| #1-#3 | various pre-#2297 | claude-tools | `module_failed` | textbook_grounding, inject_activity_ids, surzhyk_clean | Pre-#2305 era; gate was masking writer issues |
| #4 | post-#2297 | claude-tools | `module_failed` | inject_activity_ids, surzhyk_clean (шо), textbook_grounding, tool_theatre | Step B masked by gate bug; surzhyk false-positive |
| #5 | post-#2305+#2306+#2307 | claude-tools | `module_failed` | vocab schema (`note` vs `notes`) | My typo in PR #2306 iteration; fixed in #2308 |
| #6 | post-#2308 | claude-tools | `module_failed` | textbook_grounding (Step B skipped), engagement_floor, tool_theatre | **claude-tools structural Step B blind spot** |
| #7 | post-#2305+#2306+#2307+#2308 | **codex-tools** | `module_failed` | textbook_grounding (parser bug), word_count 95% | **codex cleared Step B + tool_theatre on first try** |
| #8 | post-#2339 | codex-tools | `module_failed` | ONLY word_count (981/1200 = 82%) | Parser fix worked; 25/26 gates |
| #9 | post-#2340 | codex-tools | `module_failed` | l2_exposure_floor (13/14), engagement_floor (meta narration) | Word-count fix worked; 2 new content gates surfaced |
| #10 | post-#2344 | codex-tools | `module_failed` | ONLY word_count (1101 vs 1104 floor — **3 tokens** short) | 27/28 python_qg gates; closest yet |
| #11 | post-#2350 | codex-tools | `module_failed` | wiki_coverage_gate (ALL 18 obligations `implementation_map_missing`) | 28/28 python_qg gates; NEW failure mode revealed parser bug |
| #12 (in flight) | post-#2355 | codex-tools | expected `module_done` | — | Parser fix + writer same as #11 = expected ship |

## The wiki_coverage parser bug (round #11 → PR #2355)

### Symptom

Round #11 build at `~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/builds/a1-my-morning-20260526-200639/`:

- All 28 python_qg hard gates: PASSED (including word_count 1107/1104 floor, l2_exposure_floor 35 lines, chunk_context_calls=2, tool_theatre_violation_count=0)
- Post-QG `wiki_coverage_gate`: ALL 18 obligations FAIL with `implementation_map_missing` (coverage 0/18)
- 3 wiki_coverage correction iterations couldn't recover

### Root cause

Writer-parser format mismatch. The writer prompt's `<implementation_map>` parent tag doesn't specify the inner row shape:

```
<implementation_map>
<!-- rule_id: #R-IMPL-MAP-COMPLETE -->
List every `obligation_id` exactly once: obligation_id, artifact, location, treatment.
</implementation_map>
```

- **claude-tools** read this as a cue for markdown bullets (`- obligation_id: step-2\n  artifact: ...`) or compact-pipe (`step-2 | module.md | §Діалоги | ...`). Parser supports both.
- **codex-tools** (round #11) read the XML wrapper as a cue to nest XML row elements:
  ```
  <row obligation_id="ban-1" artifact="module.md" location="§Мій ранок"
       treatment="No Russian-language explanation appears." />
  ```
  Perfectly reasonable XML reading. **Parser didn't recognize this shape.**

Round #11 writer emitted 18 well-formed `<row .../>` entries; every one dropped silently → coverage 0/18 → terminal fail.

### Fix (PR #2355)

Added `_ROW_XML_RE` + `_ROW_XML_ATTR_RE` to `scripts/audit/wiki_coverage_gate.py::parse_implementation_map`. Constrained attribute body (one-or-more `key="value"` pairs, then `/>`) correctly handles values containing `/` and `>` (e.g. `treatment="Я прокидаюся. / Він прокидається."`).

End-to-end verified against round #11's actual writer output: 18/18 obligations parsed with all 4 fields populated. **The same module would have shipped under the patched parser.**

### Why this took 11 rounds to surface

Wiki_coverage_gate is the LAST gate in the build pipeline (runs after python_qg). Rounds #1-#10 all failed at python_qg before wiki_coverage_gate could run. Round #11 was the FIRST to pass python_qg → first to enter wiki_coverage_gate → first to expose this writer-parser mismatch. **This is a structural gating order observation:** late-pipeline gates only get exercised after early-pipeline gates pass, so they're under-tested empirically.

## Bio R1a pilot — what we learned

Per user direction ("pilot first then decide"), fired ONE codex dispatch for 3 R1a figures: Драй-Хмара (Block A, Kolyma 1939), Свідзінський (Block A, NKVD-burned alive 1941), Сосюра (Block D, censored 1951). Brief at `docs/dispatch-briefs/2026-05-26-r1a-pilot-3-bios-codex.md`. Stress-test: 3 different oppression patterns.

### Result quality

PR #2354 (merged):

| Figure | Words | T1/T2 sources | Primary quotes |
|---|---:|---:|---:|
| Драй-Хмара | 1551 | 5 | 2 |
| Свідзінський | 1553 | 4 | 2 |
| Сосюра | 1531 | 4 | 2 |

All within the 1200-2000 acceptable range. All ≥3 T1/T2 sources met. All ≥2 UA primary quotes met.

### Standouts that validate the F5 template

- **Hard document references**: NKVD case **№ 72569**, archival number **07993**, charge **art. 54-10 part II** Ukrainian SSR Criminal Code, 1964 rehabilitation reference. Not paraphrase.
- **Source disagreement flagged honestly**: my brief said "near Bryansk" for Свідзінський's death; codex pushed back via ЕСУ/ЕІУ/Solovey 2009 sources to identify Saltiv/Nepokryte (older testimony) or Butyrky/Kursk oblast (case-review line). Did NOT silently resolve.
- **Anti-hagiography contested-points sections** present for all 3.
- **No unilateral plan additions**: cross-track gap surfaced for Свідзінський filed as #2353 (bio-expansion-followup) — did NOT add plans without epic permission.
- **Honest tool-fail reports**: `verify_quote` returned no match for Свідзінський's primary excerpts because his text is not in the lit corpus → fell back to Solovey 2009 article with page numbers. Did NOT fabricate.

### What this validates for scale-up

The 5-agent split plan (Codex / Gemini-pro / DeepSeek-pro / Agy / Cursor across the 6 tiers) is **validated** by the pilot quality. **Awaits user OK** before firing — user explicitly chose "pilot first then decide."

Proposed scale assignments (modulo final adjustments after user reviews PR #2354):

| Tier | Figures | Recommended agent | Why |
|---|---|---|---|
| R1a-rest | 17 | Codex | Highest signal; Розстріляне Відродження needs careful source synthesis |
| R1b | 26 | Gemini-pro (paid) | Long-context synthesis across Прага+МУР+NY Group |
| R2 | 31 | DeepSeek-pro hermes | Mixed Tier-2 figures; cost-conscious; deepseek's per-figure tool calls fit |
| R3 | 32 | Gemini-pro | High-volume modern figures; Gemini's web search adds value |
| R4 | 9+4 | Codex + Claude xhigh | Politically charged (Block G OUN/UPA/UNR); keep epic's plan |
| R5 | 12 | Gemini-pro | Recent figures; web-search-heavy |

Batch 3 figures per dispatch (amortizes overhead, lets each agent build block-context). Peak in-flight: 2 Codex + 2 Gemini-pro + 1 DeepSeek + 1 Claude = 6 dispatches. Wall time ~1 working week vs 3 weeks for all-Codex.

## What's queued for the next session

**Immediate (within 30 min of session resume — assumes round #12 has finished):**

1. **Check round #12 outcome.** Read bridge task output at `/private/tmp/claude-501/-Users-krisztiankoos-projects-learn-ukrainian/52dec5e4-d494-4a7e-bcc0-65efac652f50/tasks/bc7lyi3n3.output` and the latest build worktree (most recent `~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/builds/a1-my-morning-*`).
2. **If `module_done`:** codex will have opened a PR. Run the 10-check verify-before-promote per `docs/best-practices/v7-design-and-corpus.md` §4 (look for the "10-check" or "verify-before-promote" section). Spot-check the four-tab MDX rendering, the wiki coverage breakdown, the python_qg gate matrix, and the writer telemetry against round #11 baseline. If everything clears → approve + merge → **m20 ships as first V7 A1 anchor under the post-reset architecture**.
3. **If `module_failed`:** Dump the failing gate's JSON. Diagnose. If wiki_coverage_gate STILL fails despite PR #2355: verify the parser fix took (`git log --oneline scripts/audit/wiki_coverage_gate.py | head -2` should show `0ecf2d9113`). If different gate fails: triage per Pt 4 brief's failure-mode catalog.

**On m20 ship (post-round-12 merge):**

4. **Fire round #13 with `--writer gemini-tools`** (or `agy-tools`/`cursor-tools` based on quota — see Pt 4 line 98 for pool selection) via `Monitor` on direct `v7_build.py` (NOT bridge — gemini-tools doesn't share codex thread state). Expected outcome: empirical comparison data point.
5. **After both empirical points:** update `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` with the codex vs gemini comparison and the new A1 writer default. **Strong empirical case to flip default from claude-tools.**

**Bio epic (Phase 1) scale-up — AWAITS USER OK:**

6. Ask user OK on the 5-agent split. If yes → fire 5 parallel research dispatches (R1a-rest + R1b + R2 + R3 + R5 — Hold R4 until F2-aligned briefing). Each batch = 3 figures.
7. As each dispatch lands → review against F5 template + acceptance criteria → merge. Track Phase 1 progress in #2309 epic comments.

**Latent (not blocking m20):**

- **Issue #2351** (claude-tools Step B blind spot, filed this session) — update with the codex round #11/#12 Step B data after round #12.
- **Issue #2353** (Svidzinskyi cross-track gap, filed by codex during pilot) — triage when convenient.
- **Codex thread state**: thread `019e6063-c3da-78d1-acaa-4cd684a08786` is still live and has the full round #4-#12 history. Session JSONL: `~/.codex/sessions/2026/05/25/rollout-2026-05-25T20-26-51-019e6063-c3da-78d1-acaa-4cd684a08786.jsonl` (~4.5MB by Pt 6 end).
- **Build worktrees**: 8 m20 build worktrees on disk under `~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/builds/a1-my-morning-*`. Per #M-10, keep until m20 ships.
- **Outside-project worktree**: `/Users/krisztiankoos/projects/.worktrees/session-handoff-pt5` was abandoned after PR #2349 merge; can be removed manually.

## Critical empirical conclusions (carried forward from Pt 4)

### codex-tools is the right A1 writer (pending gemini comparison)

Across rounds #7-#11, codex-tools:
- Made Step B `get_chunk_context` calls every round (claude-tools blind-spot DOES NOT recur with codex)
- Zero `tool_theatre_violation_count` every round
- Cleared 25/26 → 27/28 → **28/28 python_qg** gates progressively as prompt-side fixes landed
- Surfaced and survived 4 distinct failure modes that drove real pipeline improvements (parser bugs in PR #2339, prompt deltas in PR #2340/#2344/#2350, parser fix in PR #2355)

**Round #11's wiki_coverage failure was NOT a codex regression — it was a parser bug that codex's well-formed XML revealed.** PR #2355 closes that gap.

## Session totals

- **PRs opened**: 4 this session (#2350, #2352, #2355, plus #2349 + #2354 inherited/pilot).
- **PRs merged**: 5 (so far). Round #12 outcome adds 0-1 more PR (if codex opens m20 anchor).
- **m20 build rounds fired**: 2 (#11 + #12; #11 failed, #12 in flight).
- **Main commits**: `6f2a440859` → `2386ff3c0a` (5 squash commits).
- **Bio dossiers shipped**: 3 (R1a pilot).
- **Issues filed**: 2 (#2351 claude-tools Step B; #2353 cross-track gap by codex).
- **Bugs root-caused**: 2 (word_count gate gap explained as JSX scaffolding ratio; wiki_coverage parser-writer format mismatch).
- **Tasks completed**: 4 of 6 in the orchestrator TodoList. Remaining: m20 round #12 outcome handling; bio scale-up (user OK).

End of 2026-05-26 Pt 6 handoff.
