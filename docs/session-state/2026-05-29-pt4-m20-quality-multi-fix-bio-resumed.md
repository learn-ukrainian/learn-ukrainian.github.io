---
date: 2026-05-29
session: "Autonomous orchestrator. m20 anchor quality driven end-to-end across the rendered MDX (not just scores). 3 root-cause fixes shipped + 2 in flight; bio epic resumed. User-driven: STOP claude-tools (seat quota), USE the agent roster."
status: m20-render-quality-multi-fix · {/**/}-render-FIXED(#2420) · одіватися-erasure-FIXED · explanations-fix-in-flight · bio-religious-martyrs-dispatched
main_sha: 4458999da8
main_green: yes
---

# 2026-05-29 Pt4 — m20 rendered-MDX quality (the real product), multi-fix; bio epic resumed

## ⭐ THE REFRAME (user-forced, correct): review the RENDERED LESSON, not the score
User caught two real failures: (1) I was tuning gate scores while never RENDERING/reading the lesson the
learner sees; (2) the only viewable lesson was a **hand-placed, un-automated** build-#3 preview (3.5 REJECT).
**Systemic root cause:** the LLM QG reviews `module.md` PROSE, never the assembled MDX → MDX-assembly defects
(`{/**/}`, empty explanations, dup activities, meta in Resources) are invisible to every gate. Nothing reviews
the rendered artifact. This is the #M-11 trap, hit head-on.

## m20 status — codex GENERATOR build (`.worktrees/builds/a1-my-morning-20260529-180702/`)
`v7_build.py a1 my-morning --worktree --writer codex-tools --use-generator` →
- **python_qg ALL PASS** (the `--use-generator` path drives the retrieval the legacy charter path skipped —
  that's why my earlier claude-tools builds #7/#8/#9 failed chunk_context/resources_search: I OMITTED
  `--use-generator`. ALWAYS pass it.)
- **0 Knowledge Packet leaks** → #2417 (scaffolding-artifact gate + R-CITE-HONEST prompt) VALIDATED on generator path.
- **llm_qg 7.5 REVISE, terminal dim = decolonization** → the writer marked **одіватися** as "surzhyk", but
  search_heritage shows it's AUTHENTIC (Грінченко 1907 + СУМ-20, Russianism=False). Colonial erasure (кобета pattern).
- **Rendered MDX defects:** 4× `{/**/}`, **14 empty quiz explanations**, 1 Крок/[SN] hit (recheck), Activities-tab
  duplicates Lesson activities.

## Shipped this session (main = 4458999da8, green)
- **#2417 (merged earlier)** — `_SCAFFOLDING_ARTIFACT_RE` gate (`[\s_-]+` sep for snake_case) + R-CITE-HONEST
  "provenance → VERIFY comment only". Kills the "Knowledge Packet" tone leak deterministically.
- **wiki одіватися fix `52c9deb8a8`** — removed the heritage-mislabel from `wiki/pedagogy/a1/my-morning.md`
  bad-form list (tool-verified authentic). Kept genuine Russianism pairs завтрак/полотенце.
- **self-caused regression fix `9180c12f95`** — that wiki edit dropped m20 decolonization_pairs 3→2 →
  `test_m20_my_morning_wiki_passes_completeness_gate` went red on MAIN → fixed the snapshot (gate still PASS;
  l2_errors=6 covers distractor floor). LESSON: editing a wiki bad-form list moves the completeness-gate count.
- **#2420 (merged `4458999da8`)** — `convert_bad_form_markers` in `scripts/generate_mdx/converters.py` renders
  `<!-- bad -->X<!-- /bad -->` → `<del>X</del>` (was leaking as `{/**/}`). Wired into `_apply_shared_transforms`
  (`strip_only` for JSON-embedded props). Verified on real завтрак case. **Fixes EVERY decolonization module.**

## In flight (all OFF the user's Claude seat)
- **codex** `fix-quiz-explanations-codex-2026-05-29` (worktree, base 9180c12f95) — require non-empty `explanation`
  on quiz/translate items (writer prompt + python_qg gate) + test. (cursor first attempt rate_limited.)
- **deepseek** `review-m20-codex-build-2026-05-29` (read-only, deepseek-v4-pro) — independent content review
  (VESUM/russianism/decolonization/register/rendered-defects) of build 180702.

## Follow-ups filed (build AFTER m20 ships — delivery first)
- **#2418** — retrieval gates (`resources_search_attempted`/`chunk_context_for_all_refs`) have no ADR-008
  correction path; stochastic writer omission hard-fails good builds. Add writer-side re-prompt correction.
- **#2419** — deterministic heritage-defense gate: reject `<!-- bad -->` forms that search_heritage shows are
  authentic Ukrainian (prevents the одіватися/кобета erasure class). HIGHEST-value decolonization gate.

## NEXT — m20 to "passing" (resume here)
1. When explanations fix (codex) lands → review + merge (verify CI green on head, not stale).
2. **Rebuild m20: `v7_build.py a1 my-morning --worktree --writer codex-tools --use-generator`** — NEVER claude-tools
   (competes with user's interactive Claude seat → quota drain + the 61-min hang on build #8). Detached via Bash
   `run_in_background` + `timeout --signal=TERM 3000` (monitor-timeout SIGPIPE'd build #10 — don't rely on Monitor for the long silent writer leg).
3. Render → verify MYSELF on FRESH eyes: 0 `{/**/}`, real quiz explanations, decolonization PASS (одіватися gone),
   no dup activities, Section-4 ten-check on all 4 tabs. **Only deliver to user when actually clean** (user: "I'll
   check when YOU say you delivered a passing one").
4. Live PR #2364 (pre-V7.2) stays; on promote delete `starlight/src/content/docs/a1/my-morning-v72-*preview.mdx`
   (two untracked preview files I hand-placed: build3 + build6 — clean these up).

## Bio epic #2309 — RESUMED (user: "keep working on bio as well")
- Next block = **religious-martyrs / UGCC clergy** (Сліпий/Шептицький plans exist, dedup first). Brief at
  `/tmp/bio-religious-martyrs-brief.md`; dispatching to **codex** (anti-fabrication proven). Then Crimean-Tatar, scientists.
- **NEVER gemini/agy for factual bio** (§7 fabrication). §7 paths gated by #2413 validator. Route claude(quota-permitting)/codex only.

## Agent routing (LEARNED this session — persisted to MEMORY)
- **qwen EXCLUDED — too expensive (user 2026-05-29).** **claude-tools/claude-headless: avoid — burns user's
  interactive seat** (the session-long frustration). **deepseek = independent reviewer (use it off-seat, don't review inline).**
  **codex = V7 writer + bio + Green Team.** **gemini = wiki + bounded script/test fixes.** grok = lane unvalidated.
  agy = never factual content.
- **V7 builds: `--writer codex-tools --use-generator` is the canonical invocation.** Legacy (no `--use-generator`)
  skips retrieval gates; claude-tools drains the user seat.
