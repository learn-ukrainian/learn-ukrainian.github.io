---
date: 2026-05-29
session: "Autonomous orchestrator. deepseek content review = authoritative m20 quality bar (NOT shippable). 6 m20 fixes shipped; assembler-injection blockers (B2/B3) remain. Bio: 3 UGCC dossiers (validator-clean). Roster fully used off the Claude seat."
status: m20-6-fixes-shipped · decolonization-FIXED(7.5→8.5) · now-engagement-8.2-limited · B2/B3-PHANTOM(stale-tracked-MDX) · render-verify-pending-passing-build · bio-#2422-MERGED
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
| B2 | Ukrainian writer-meta paragraph "in MDX" | ⚠️ LIKELY PHANTOM — was read from the STALE git-TRACKED `my-morning.mdx`, not pipeline output (see correction below) |
| B3 | `Крок 5` scaffolding "in MDX" | ⚠️ LIKELY PHANTOM — same stale-tracked-MDX source |
| M1 | одіватися mislabel "surzhyk" | ✅ FIXED `52c9deb8a8` (wiki) |
| M2 | MDX dialogue diverges from module.md (renderer rewrote it; +6 unexplained words) | ⛔ OPEN — verify on rebuild |
| M3 | "дивлюся телефон" calque → "дивлюся в телефон" | ⛔ OPEN — writer-stochastic |
| M4 | прокидатися/вмиватися are A2 (PULS) not A1 — needs acknowledgment note | ⛔ OPEN |
| M5 | Activities tab duplicates Lesson tab | ⛔ OPEN — assembler P2 (Section-5 known-broken #3) |
| m1 | йти/іти inconsistency | OPEN minor |
| m2 | activities act-5+ missing `id` | OPEN minor |
| m3 | empty quiz explanations | ✅ GATED (#2421 `quiz_translate_explanations`) — rebuild must fill them |
| m4 | полотенце nuance (in VESUM = smaller cloth) — refine label | OPEN minor (defensible as-is) |

## ✅ CORRECTION (rebuild 193432): B2/B3 are PHANTOM — they came from the STALE TRACKED MDX
`starlight/src/content/docs/a1/my-morning.mdx` is **git-tracked** (old promoted m20). Every build worktree
checks it out. Builds 180702 AND 193432 BOTH FAILED at llm_qg (REVISE → terminal) → the mdx phase never
ran → the my-morning.mdx in those worktrees is the **stale tracked file** (mtime = checkout time), NOT the
build's render. `git show HEAD:...my-morning.mdx | grep -c "Крок|зарядка|одіватися|{/**/}"` = 4 → the tracked
MDX is the OLD content. **deepseek's MDX-cited findings (B2 mdx:88, B3 mdx:195, M2 dialogue, m3 empty-expl)
were read from that stale file, not the current pipeline.** The current pipeline's **module.md is CLEAN**
(Крок=0, зарядка=0, одіватися=0). So there is **no confirmed assembler-injection bug** — do NOT chase one.
deepseek's module.md/content findings remain valid: B1 зарядка + M1 одіватися (both FIXED via wiki), M4
CEFR (real, minor), M3 calque (re-check current module.md), полотенце nuance (minor).

**RENDER VERIFICATION IS STILL PENDING** — but for a real reason: no fresh build has PASSED llm_qg, so none
has rendered + overwritten the tracked MDX. To verify the *current* pipeline's rendered output you must
EITHER (a) get a build to terminal PASS (clear engagement 8.2 — see below), OR (b) call `generate_mdx`
(core.py) on a fresh module.md+activities+vocab+resources artifact directly. Until then, the render layer
is unverified but module.md being clean is a strong positive signal. Also: **delete the stale tracked
my-morning.mdx** (or have promote overwrite it) so future builds don't checkout misleading content.

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

## NEXT (resume here) — UPDATED post-rebuild
Rebuild 193432: **decolonization 7.5→8.5 PASS** (одіватися+зарядка fixes worked, module.md clean), python_qg
ALL PASS, but **llm_qg 8.2 REVISE, now limited by ENGAGEMENT (8.2)** (warning: naturalness). The blocker
moved from decolonization → engagement. (The module_failed "decolonization" reason string conflicts with the
8.5 PASS dim response — verify the aggregate logic; min_dim=engagement is the real limiter.)
1. **Engagement 8.2 → clear the bar.** Read the fresh `llm-qg-engagement-response.raw.md` (193432) for what
   it flags; lift via writer prompt / exemplar (the #2389-pt3 lever) — this is now THE gate to a rendering build.
2. Once a build PASSES llm_qg → it renders + overwrites the (stale) tracked MDX → THEN verify the REAL render
   (0 `{/**/}` — #2420 handles it, explanations present — #2421 forces, no Крок/meta). B2/B3 were PHANTOM; do
   NOT pre-build an assembler-injection fix. Also re-check M3 "дивлюся телефон" calque in the fresh module.md.
3. **Delete the stale tracked `starlight/.../a1/my-morning.mdx`** so builds stop checking out misleading content.
3. Bio epic: after #2422 → next blocks Crimean-Tatar, scientists (route codex/claude-quota-permitting; NEVER gemini/agy for §7).
4. Clean up 2 hand-placed preview MDX (`a1/my-morning-v72-preview.mdx` + `-build6-preview.mdx`, untracked) on m20 promote.

## Routing (persisted MEMORY): qwen EXCLUDED (cost). claude-tools/headless AVOID (user's interactive seat —
session-long frustration). deepseek=independent reviewer (use off-seat; .result file not stdout). codex=V7
writer + bio + Green Team. gemini=wiki + bounded fixes. grok=unvalidated. agy=never factual.
**V7 build canonical: `--writer codex-tools --use-generator`.**
