---
date: 2026-05-29
session: "Autonomous orchestrator. deepseek content review = authoritative m20 quality bar (NOT shippable). 6 m20 fixes shipped; assembler-injection blockers (B2/B3) remain. Bio: 3 UGCC dossiers (validator-clean). Roster fully used off the Claude seat."
status: m20-6-fixes-shipped · deepseek-review-is-the-bar · assembler-injection-B2/B3-OPEN · rebuild-in-flight · bio-#2422-merging
main_sha: 2ccc5cb9c0
main_green: yes
---

# 2026-05-29 Pt5 — deepseek review is the quality bar; 6 m20 fixes; assembler-injection is the remaining blocker

Continues pt4. **The reframe holds: review the RENDERED MDX, not the score.** deepseek (the independent
VESUM reviewer) produced the authoritative assessment of the codex generator build (180702):
`batch_state/tasks/review-m20-codex-build-retry-2026-05-29.result` (READ IT — 11 findings, all tool-backed).

## deepseek review findings (verdict: NOT shippable) — status
| # | Finding | Status |
|---|---|---|
| B1 | **зарядка = Russianism** (ЕСУМ "запозичення з рос."; r2u→руханка; руханка VESUM-std) | ✅ FIXED `2ccc5cb9c0` (wiki зарядка→руханка) |
| B2 | **Ukrainian writer-meta paragraph injected into MDX prose** (mdx-only, NOT in module.md) | ⛔ OPEN — assembler injection |
| B3 | **`Крок 5` scaffolding injected into MDX** (mdx-only, NOT module.md; PASSED python_qg) | ⛔ OPEN — assembler injection |
| M1 | одіватися mislabel "surzhyk" | ✅ FIXED `52c9deb8a8` (wiki) |
| M2 | MDX dialogue diverges from module.md (renderer rewrote it; +6 unexplained words) | ⛔ OPEN — verify on rebuild |
| M3 | "дивлюся телефон" calque → "дивлюся в телефон" | ⛔ OPEN — writer-stochastic |
| M4 | прокидатися/вмиватися are A2 (PULS) not A1 — needs acknowledgment note | ⛔ OPEN |
| M5 | Activities tab duplicates Lesson tab | ⛔ OPEN — assembler P2 (Section-5 known-broken #3) |
| m1 | йти/іти inconsistency | OPEN minor |
| m2 | activities act-5+ missing `id` | OPEN minor |
| m3 | empty quiz explanations | ✅ GATED (#2421 `quiz_translate_explanations`) — rebuild must fill them |
| m4 | полотенце nuance (in VESUM = smaller cloth) — refine label | OPEN minor (defensible as-is) |

## ⛔ THE KEY REMAINING m20 BLOCKER: assembler injects impl_map text into MDX (B2+B3)
PROVEN: `Крок 5: Розширення...` and the `Контролюй чистоту словника...` meta-paragraph are in the
**rendered MDX but NOT in module.md** (`grep -c "Крок" module.md`=0, MDX=1; same for the meta para).
So the MDX assembler (`scripts/generate_mdx/`) injects implementation_map / wiki-step text into the
learner-facing lesson — invisible to every module.md-level gate (the #M-11 theme). Source: wiki line 31
is a `Крок 5:` pedagogy step containing that prose; it reaches the MDX via the assembler, NOT via the
writer. **NEXT-SESSION P0: trace how impl_map/wiki-step text lands in the MDX** (module.md INJECT markers
are only `INJECT_ACTIVITY: act-1..4` — clean; the Крок-5 text comes from elsewhere). Candidate: a fallback
that dumps unrendered impl_map rows, or the writer/renderer pulling wiki-step prose. Then fix + add a
**rendered-MDX gate** (the missing review layer — scan the assembled .mdx for `Крок N:`, leaked meta,
`{/**/}`, empty explanations). NOTE: build 180702 FAILED at llm_qg (REVISE) so its artifact may be
inconsistent — RE-VERIFY B2/B3 on the FRESH rebuild before deep-diving the assembler.

## Shipped to main this session (Pt3+Pt4+Pt5), main `2ccc5cb9c0` green
#2417 (scaffolding-artifact gate + R-CITE-HONEST), #2420 (`<!-- bad -->`→`<del>`, fixes EVERY decolonization
module), #2421 (`quiz_translate_explanations` hard gate), wiki одіватися `52c9deb8a8`, completeness-test
regression fix `9180c12f95` (self-caused), wiki зарядка→руханка `2ccc5cb9c0`.

## In flight
- **m20 rebuild** `/tmp/m20-rebuild-final.jsonl` (codex-tools `--use-generator`, base 2ccc5cb9c0, detached
  `timeout 3000`, task `b5yiiklwm`). On done: render → re-check ALL deepseek findings on the FRESH artifact.
- **bio #2422** (3 UGCC dossiers Шептицький/Сліпий/Гузар; dedup-correct; §7 validator CLEAN — I ran it;
  Wikipedia-verified). pytest watcher `bau2nddja` → MERGE when green (content-only).

## Follow-ups filed: #2418 (retrieval correction path), #2419 (heritage-defense gate — #M-11-grade,
build it; would've caught одіватися deterministically).

## NEXT (resume here)
1. m20 rebuild done → render → verify on FRESH eyes: 0 `{/**/}`, real explanations (#2421 should force),
   decolonization PASS (одіватися+зарядка gone), **re-check B2/B3 (Крок 5 + meta-paragraph) in the fresh MDX**,
   dialogue matches module.md (M2), no dup activities (M5), Section-4 ten-check. **Deliver to user ONLY when
   actually clean** (user: "I'll check when YOU say you delivered a passing one"). DO NOT use claude-tools.
2. If B2/B3 recur on fresh build → trace + fix the assembler impl_map injection + add rendered-MDX gate.
3. Bio epic: after #2422 → next blocks Crimean-Tatar, scientists (route codex/claude-quota-permitting; NEVER gemini/agy for §7).
4. Clean up 2 hand-placed preview MDX (`a1/my-morning-v72-preview.mdx` + `-build6-preview.mdx`, untracked) on m20 promote.

## Routing (persisted MEMORY): qwen EXCLUDED (cost). claude-tools/headless AVOID (user's interactive seat —
session-long frustration). deepseek=independent reviewer (use off-seat; .result file not stdout). codex=V7
writer + bio + Green Team. gemini=wiki + bounded fixes. grok=unvalidated. agy=never factual.
**V7 build canonical: `--writer codex-tools --use-generator`.**
