---
date: 2026-05-29
session: "Autonomous multi-agent. m20 writer-quality: de-scaffold + extraction fixes VALIDATED; 3rd gate bug (VESUM comment-strip) proven + fix dispatched. Bio epic: R5 12/12, Block D de-fab, Helsinki Group merged. 5 agents engaged."
status: m20-rebuild#6-in-flight (all 3 gate fixes merged) · bio-epic-advanced · 7-PRs-merged
main_sha: 4c4c045076
main_green: yes
---

# 2026-05-29 Pt2 — m20 writer-quality cracked open (2 fixes validated, 3rd in flight); bio epic advanced

## ⭐ THE LIVE THING — m20 (a1/my-morning) writer-quality, precisely tracked

**Trajectory:** 3.5 REJECT (scaffolding leak) → **6.8 REVISE** (de-scaffold killed the leak) →
**both fixes validated, build now blocked only by a proven 3rd gate bug.**

| Build | Score | What it proved |
|---|---|---|
| #3 (pre-fix) | 3.5 REJECT, all 4 dims rejected | `Крок N:`/`[SN]` scaffolding pasted into prose |
| #4 (de-scaffold #2412) | 6.8 REVISE, 0 rejected | leak GONE (`scaffolding_leak` gate passes); residual = `_extract_required_items` noise |
| #5 (de-scaffold + extraction #2415) | FAILED at python_qg | **`scaffolding_leak` PASSES + `register_consistency` PASSES** (both fixes validated!); failed ONLY on 3rd gate bug below |

**3rd gate bug (PROVEN, fix in flight):** `vesum_verified` false-fails on Cyrillic that appears
ONLY inside `<!-- VERIFY: ...check_russian_shadow(word='одіватися') -->` annotation comments.
`_strip_metalinguistic` (linear_pipeline.py ~7853) strips `_AVOID_MARKER_RE` bad-markers but NOT
regular `<!-- -->` comments. Reproduced:
`_build_vesum_text("...<!-- VERIFY: ...word='одіватися' -->", [],[],[])` → одіватися survives → False fail.
The writer did everything RIGHT (одягатися 20×, одіватися bad-marked, russian-shadow documented).
LATENT + BROAD: any build whose VERIFY comments cite a non-VESUM form (Russianism/typo/dialectism)
false-fails. **Fix dispatched:** `vesum-gate-strip-comments-2026-05-29` (codex, watcher `buwrza6or`):
add `_strip_comments(text)` AFTER `_AVOID_MARKER_RE` in `_strip_metalinguistic` + tests. Ordering is
critical (comments-first would expose bad-marker inner text).

**NEXT (resume here):** All 3 gate fixes MERGED (#2412/#2415/#2416). **Rebuild #6 is IN FLIGHT**
(Monitor `bb4xlus0a`, build worktree `.worktrees/builds/a1-my-morning-20260529-1219*`). On
`module_done`: **verify-before-promote on FRESH context** (#M-11: read the artifact, not just the
score — that's how all 3 bugs were caught; do it with clean judgment, not a bloated session). Read
`llm_qg.json` per-dim + grep module.md for `Крок/[SN]` + `одіватися`-in-prose + register shifts.
Expect a clean completion + the first real llm_qg score with all fixes. If still <bar (≈8), the last
lever is **#2389 part 3: wire the 9.5/10 exemplar** into the generator `<example>` slot
(linear-write.generated.md) via the wiki/RAG composition boundary (NOT a registry rule).
**DO NOT PROMOTE until verify clears.** Live PR #2364 (pre-V7.2) stays; delete
`starlight/src/content/docs/a1/my-morning-v72-preview.mdx` on promote.

Build #5 forensics: `.worktrees/builds/a1-my-morning-20260529-115829/curriculum/l2-uk-en/a1/my-morning/`
(python_qg.json shows scaffolding_leak✅ register_consistency✅ vesum_verified✗одіватися).

## The 3 m20-surfaced gate bugs — same family ("gates must exclude comments/markers")
1. **#2412** (MERGED) — `render_for_writer_prompt` rendered `Крок/[SN]` scaffolding raw → writer pasted it. Fix: `strip_writer_scaffolding` sanitizer + new `scaffolding_leak` python_qg gate (excludes comments+fenced code). Deepseek caught an English-`Step N:` FP, fixed before merge.
2. **#2415** (MERGED) — `_extract_required_items` swept discourse markers (наприклад), descriptive phrases, pronouns, single letters into "vocabulary to introduce" → writer spliced untranslated UA into EN prose. Fix: extract only real lemmas (stopword list + word-count guard + infinitive salvage).
3. **vesum-gate-strip-comments** (IN FLIGHT) — VESUM gate doesn't strip `<!-- -->` comments → VERIFY-annotation Cyrillic false-fails.

## Shipped to main this session (6 PRs, main 90d453c89c, all green)
- **#2409** R5 agy-3 (Babich/Levin/Hurniak) → **R5 12/12**. Caught+fixed 5 fabricated §7 paths; identities Wikipedia-verified.
- **#2411** Block D de-fabrication (6 dossiers, ~18 fake §7 paths → verified-real); **#2400 closed** as superseded.
- **#2412** de-scaffold render + scaffolding_leak gate.
- **#2413** §7 fabrication validator (`scripts/audit/lint_bio_dossier_xref.py` + pre-commit hook); **#2410 closed**. Repo sweep = 0 fabrications (corpus clean; the "~12 backlog" was a false alarm — those are correctly-labelled Potential/Candidate).
- **#2414** Helsinki Group bio block — 6 founders (Rudenko/Tykhy/Lukianenko/Kandyba/Meshko/Marynovych), 0-FAKE §7, identities verified, explicitly declared missing quotes rather than fabricating.
- **#2415** extraction-noise fix.

## Bio epic #2309 state
R5 12/12 ✅ · Block D de-fabbed ✅ · Helsinki Group ✅. §7 fabrication now DETERMINISTICALLY GATED (#2413).
**Next blocks** (handoff queue): religious martyrs (UGCC clergy — Slipyj/Sheptytsky plans exist, dossiers may not — dedup first), Crimean-Tatar, scientists. **Route to claude** (proven exemplary anti-fabrication this session) or codex. **NEVER gemini/agy for factual bio** (they fabricate §7 — the bug fixed in #2400/#2410/#2415; gemini-code-assist even wrongly suggested Бабіч→Бабич, a Russian-shadow error, on #2409).

## Agent utilization (user asked twice — addressed)
This session: codex (×4: #2411, #2412, #2415, vesum-fix), cursor (#2413 validator), claude (#2414 Helsinki), deepseek (#2412 adversarial review — caught the Step-N FP), + orchestrator. 5/8 engaged. gemini/agy deliberately idle (fabrication risk; no fabrication-safe task queued). Codex cap 2 respected.

## Guards / lessons reinforced
- **#M-11 verify-before-promote is load-bearing**: all 3 gate bugs were caught by READING THE ARTIFACT, not the score. 6.8 alone hid the extraction bug; the build-fail hid that both fixes actually worked.
- **Advisory rules don't bind generating models; deterministic gates do** — recurring theme (scaffolding leak rule existed but writer ignored it; F5 §7 prompt-fix didn't bind gemini; validator #2413 fixes it).
- Independent verification of every dispatch self-report (re-ran test-e on #2409/#2411/#2414 diffs; re-ran extraction on real m20 claims; reproduced the VESUM bug) — caught cursor `needs_finalize`, the одруж under-extraction edge, etc.
- Branch-delete-after-merge warnings are just worktrees holding branches — clean the worktree, then `git branch -D`.
