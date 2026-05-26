---
date: 2026-05-26
session: "Part 7 of the 2026-05-26 multi-session day. Round #12 (codex-tools, BUILD_BASE 2386ff3c0a — post wiki_coverage parser fix) cleared EVERY pipeline gate (28/28 python_qg, 18/18 wiki_coverage, LLM wiki review PASS) but halted at llm_qg with terminal verdict REVISE on decolonization. NOT a pipeline bug — codex's decolonization scored 8.5, A1 floor is 9.0. New gating reality: the m20 anchor's remaining gap is a CONTENT/POLICY question, not a pipeline question."
status: round-12-halted-on-decolonization-8.5-vs-9.0-floor; user-decision-needed
main_sha: 24b0c64b9a (post PR #2356)
main_green: clean
working_tree_dirty: 0 files (this handoff doc untracked until PR)
---

# 2026-05-26 — Part 7: round #12 outcome — decolonization 8.5 vs A1 floor 9.0

Read this Pt 7 first. Pt 6 (`2026-05-26-pt6-wiki-coverage-parser-fix-round12-firing.md`) fired round #12 expecting `module_done`. Round #12 cleared every pipeline gate but halted on the LLM-QG terminal decolonization floor. This is a new class of gating signal — not a pipeline bug to fix, a policy question for the user.

## TL;DR for the next orchestrator / for the user

1. **Round #12 cleared EVERY pipeline gate** that was previously failing:
   - python_qg: 28/28 hard gates pass (word_count 1134 above 1104 floor; l2_exposure 32 dialogue lines)
   - wiki_coverage_gate: 18/18 obligations pass (PR #2355 parser fix worked end-to-end)
   - wiki_coverage_review LLM: PASS, 18 verdicts, zero keyword stuffing
   - Writer telemetry: chunk_context_calls=2, tool_theatre_violation_count=0
2. **The ONLY failing gate is `llm_qg` terminal decolonization at 8.5 vs A1 floor 9.0.** Per-dim breakdown:

   | Dim | Score | LLM verdict | A1 pass_floor | Threshold result |
   |---|---:|---|---:|---|
   | pedagogical | 8.2 | PASS | 9.0 | warning |
   | naturalness | 8.2 | PASS | 9.0 | warning |
   | decolonization | **8.5** | PASS | **9.0** | **TERMINAL FAIL** |
   | engagement | 7.5 | REVISE | 8.0 | warning |
   | tone | 8.2 | PASS | 8.0 | PASS |

3. **This is not a bug** — `LLM_QG_TERMINAL_DIMS = frozenset({"decolonization"})` (PR #2242 reset) means only decolonization terminates. A1 decolonization floor is 9.0 (`scripts/common/thresholds.py:195`). Codex's module scored 0.5 below.
4. **The bridge subprocess misread the per-dim "PASS" verdict label** in its summary. That label is the LLM-reviewer's qualitative bucket (PASS/REVISE/REJECT against an internal threshold); the aggregator uses the level-specific `pass_floor` (9.0 for A1 decolonization). They can disagree, and that disagreement is intentional per the architectural reset.

## What's in the module's decolonization content

The actual round #12 module had ONE substantive decolonization statement:

> "Choose the Ukrainian routine words themselves: **сніданок**, **рушник**, **одягатися**. A clean morning story does not need borrowed shortcuts; the Ukrainian words are short and practical."

Plus bad-form contrast markers (e.g. `<!-- bad -->завтрак<!-- /bad -->` → **сніданок**; `<!-- bad -->полотенце<!-- /bad -->` → **рушник**; `<!-- bad -->одіватися<!-- /bad -->` → **одягатися**).

The two LLM evidence_quotes the reviewer cited beyond the explicit statement were generic verb-conjugation and pronunciation rules — NOT decolonization moves. The reviewer found one substantive decolonization statement and scored 8.5.

## The actual question for the user

For an A1 morning-routine module, the decolonization opportunities are LIMITED. The natural moves are:
- Reject Russian borrowings (завтрак → сніданок, полотенце → рушник, одеваться → одягатися) ✓ done
- Use Ukrainian-canonical forms ✓ done
- Frame language choice as a stance ✓ partial (one statement)

To push to 9.0+, the writer would need 2-3 more explicit decolonization moves: a paragraph about WHY Ukrainian, era framing, more identity-vocabulary reflection. For a topic-neutral grammar-focused A1 module, that risks becoming political instruction instead of language instruction.

**This may be the first empirical evidence that the A1 decolonization floor of 9.0 is too strict for topic-neutral A1 modules.** Topic-loaded modules (bio, hist) can hit 9.0+ naturally because the content itself involves decolonization. A morning-routine grammar module can not, without forcing political content into a grammar lesson.

## Decision options (USER OK NEEDED)

| Option | Action | Trade-off |
|---|---|---|
| A | **Lower A1 decolonization floor from 9.0 → 8.5** for topic-neutral modules, retain 9.0 for bio/hist. Ship round #12 module. | Policy change. Two-tier floor across A1 needs careful design (which modules count as topic-neutral?). |
| B | **Strengthen writer prompt** with explicit A1 decolonization scaffolding (a "Why Ukrainian words" 2-3 line paragraph required per module). Re-fire round #13 with codex-tools. | Adds prompt complexity. May push score to 9.0 but risks politicizing grammar lessons. |
| C | **Fire round #13 with `--writer gemini-tools`** per Pt 4 plan ("first codex, then gemini, then decide"). See if gemini's decolonization framing naturally scores higher. | Empirical comparison data point. Burns gemini quota (user-cut). |
| D | **Accept the halt; pivot to bio research scale-up.** Codex's m20 module is shippable from a content-quality standpoint but doesn't clear the strict A1 floor. Bio epic #2309 has 127 figures ready for parallel research. | Defers m20 anchor decision; advances epic work. |

**My recommendation: C then A.** Fire round #13 with gemini-tools (empirical comparison; small quota burn). If gemini also lands below 9.0 → that's strong evidence the floor is too strict for topic-neutral modules → switch to A. If gemini lands 9.0+ → we have a new writer-default candidate → potentially flip the writer default per the 2026-05-06 decision card.

**Reason for NOT auto-firing C**: user said pilot-first on the bio epic; same caution applies here. Round #13 with gemini-tools is a separate empirical run that's worth the quota only if the user is OK with it.

## What's queued for the next session

**Immediate (within 15 min of user wake):**

1. **User picks A/B/C/D above** (or other).
2. If C: fire `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning --writer gemini-tools --effort xhigh --worktree` via Monitor tool. ETA ~25-40 min. Compare LLM-QG dim scores against round #12.
3. If A: edit `scripts/common/thresholds.py:195` lowering A1 decolonization pass_floor from 9.0 to 8.5; add a regression test; PR. Then run llm_qg on round #12 artifacts (or re-fire) to confirm pass. Then 10-check verify-before-promote → merge.

**Bio research scale-up (still awaits user OK from Pt 6):**

4. The R1a pilot (PR #2354) validated the F5 template + source-tier policy across 3 oppression patterns. The 5-agent split plan is documented in Pt 6. Awaits user OK to fire 5 parallel research dispatches (R1a-rest + R1b + R2 + R3 + R5; R4 OUN/UPA queued behind F2 alignment).

**Latent:**

- **Issue #2351** (claude-tools Step B blind spot) — now has even more codex contrast data. Update.
- **Issue #2353** (Svidzinskyi cross-track gap, filed by codex during pilot) — triage.
- **Build worktrees**: 9 m20 build dirs on disk under `~/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/builds/`. Per #M-10, keep until m20 ships.

## Round #12 build worktree (preserved)

`/Users/krisztiankoos/.codex/worktrees/3a9a/learn-ukrainian/.worktrees/builds/a1-my-morning-20260526-204640/`

Contents include the canonical artifacts (module.md, activities.yaml, vocabulary.yaml, resources.yaml, knowledge_packet.md, implementation_map.json, wiki_manifest.json), the LLM-QG per-dim prompts and raw responses (`llm-qg-{dim}-prompt.md`, `llm-qg-{dim}-response.raw.md` × 5), the writer_output.raw.md, writer_prompt.md, writer_tool_calls.json, python_qg.json, wiki_coverage_gate.json, wiki_coverage_review.json, llm_qg.json.

The actual generated module is at `curriculum/l2-uk-en/a1/my-morning/module.md` inside that worktree (1439 wc, 1134 gate count). The codex round #12 thread is the same `019e6063-c3da-78d1-acaa-4cd684a08786` at session JSONL `~/.codex/sessions/2026/05/25/rollout-2026-05-25T20-26-51-019e6063-c3da-78d1-acaa-4cd684a08786.jsonl`.

## Session totals (Pt 6 + Pt 7)

- **PRs merged this session**: 6 (#2349, #2350, #2352, #2354, #2355, #2356). Pt 7 handoff = next PR.
- **m20 build rounds fired this session**: 2 (#11 + #12). Both informative; neither shipped.
- **Bugs root-caused**: 3 (word_count gate gap; wiki_coverage parser-writer mismatch; bridge subprocess misreads per-dim PASS as terminal-PASS).
- **Bugs fixed**: 2 (PR #2350 word_count overshoot; PR #2355 wiki_coverage XML row parser).
- **Bugs documented for next session**: 1 (bridge subprocess summary misreads dim verdict — should report `aggregate.failing_dims` or `min_dim` instead).
- **Bio dossiers shipped**: 3 (R1a pilot, PR #2354).
- **Main commits**: `6f2a440859` → `24b0c64b9a` (6 squash commits).

End of 2026-05-26 Pt 7 handoff. The m20 anchor work has graduated from pipeline-bug land to content/policy land. Awaiting user decision.
