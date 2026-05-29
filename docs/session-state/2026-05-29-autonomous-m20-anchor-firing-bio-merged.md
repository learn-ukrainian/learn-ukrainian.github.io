---
date: 2026-05-29
session: "Autonomous (user 'bbl go auto'). Architecture aligned (3-agent), m20 anchor fix shipped, m20 build re-firing, 20 bio dossiers merged."
status: m20-build-in-flight · bio-c12+r5-merged · architecture-confirmed
main_sha: 475030d389
main_green: yes
---

# 2026-05-29 — Autonomous drive: m20 anchor firing, bio-epic advancing

## ⭐ THE LIVE THING (check first) — PIPELINE SOLVED, WRITER-QUALITY IS THE NEXT CHAPTER
**m20 build #3 reached `module_done`** (Monitor `bm43nj4k9`, main `cda92e387b`) — FIRST
end-to-end completion under `--use-generator`. Every structural gate passed: writer-capture ✅
(6 calls), python_qg ✅, wiki_coverage ✅ 18/18 (err-1..err-6 cleared), Goodhart ✅,
MDX ✅ assembled. **The 4 pipeline bugs are gone.**

**BUT NOT PROMOTABLE: llm_qg `3.5 REJECT`** (all 4 subjective dims rejected, min=naturalness;
`terminal_verdict=PASS` so it completed). Build #2 scored **7.0 REVISE** — same pipeline, **3.5↔7.0
run-to-run variance.** Per #M-11 do NOT promote (live PR #2364 stays).

**(B) quick-check DONE — the 3.5 is REAL, reviewer is FAIR (NOT over-penalization).** Read the
naturalness dim evidence (`.../my-morning/llm-qg-naturalness-response.raw.md`): the writer (codex)
PASTED implementation_map scaffolding VERBATIM into the published "Дієслова на -ся" prose —
`Крок 1: спершу regular читати ... [S8]`, `Крок 2: use прокидатися... add -ся або -сь, with я/ти
practice [S3, S6]`, `Крок 4: teach дивитися...; note... [S7]` — i.e. leaked `Крок N:` labels,
`[SN]` source markers, EN↔UK code-switching, and writer-directed meta-verbs ("teach"/"note").
Textbook `#R-NO-SCAFFOLDING-LEAKS` / `#R-VOICE-META` violation (same class as Pt-9 "Крок 5:" leak).
The clean Діалоги section is why it's 3.5 not 0. (Claude's first "content looks reasonable" read was
INCOMPLETE — only saw the clean dialogue section, missed the leaked verbs section. The quick-check
caught it.) So #2396 reviewer-calibration is NOT the issue here.

**THE NEXT CHAPTER = WRITER-QUALITY (A), precisely diagnosed:**
1. **Wire the 9.5/10 exemplar** into the EMPTY `<example>` slot of `scripts/build/phases/linear-write.generated.md`
   (the generator output). Source CONFIRMED present: `.worktrees/builds/a1-my-morning-20260527-185032`
   (Pt-10 9.5 baseline module.md — clean prose, no Крок/[SN] leaks). This is #2389. Exemplar ADDS bytes → pair with diet.
2. **De-scaffold the impl_map → writer-prompt rendering** so `Крок N:` step labels + `[SN]` source markers are
   NOT presented as copyable prose. The writer must COVER the sequence content but RENDER clean A1 prose, not
   paste the manifest. (`render_for_writer_prompt` in `scripts/build/phases/implementation_map.py` + the
   wiki/obligation-checklist rendering feed these markers in.) Recurring leak class — worth a hard pre-emit check.
3. Re-build m20 → expect naturalness/tone to lift well above 3.5 once the leaks are gone; then verify-before-promote.
- Build #3 forensics (#M-10): `.worktrees/builds/a1-my-morning-20260529-084958/curriculum/l2-uk-en/a1/my-morning/`
  (module.md, my-morning.mdx, llm_qg.json + per-dim `llm-qg-*-response.raw.md`). Build #2 (7.0) at `...-082030`.

## m20 pipeline fixes shipped this session (4 — first-anchor latent-bug sweep)
1. **#2404** (merged `475030d389`) — wiki_coverage seeded-claim fallback for err-obligations (cursor's catch: gate ignored pre-seeded sidecar) + Goodhart sentinel + correction-YAML validity + de-dup'd err-stub prompt render (under 135KB ceiling).
2. **#2407** (merged `00dd5f18de`) — codex 0.135.0 namespace-join (`mcp__sources` no trailing `__` → `mcp__sourcesget_*` → false `mcp_tools_never_invoked` on EVERY codex build). 3rd capture artifact; autopsy at `docs/bug-autopsies/codex-tool-capture.md`.
3. **#2408** (merged `cda92e387b`) — order activity accepts item-string permutation as `correct_order` (codex emits ordered strings, not int indices).
All have regression tests. Each benefits every future build, not just m20.

## Architecture decision — CONFIRMED (lead agenda, answered)
3-agent alignment (codex+gemini+cursor) + code verification: **per-module deterministic prompt generation is RIGHT.** Keep it. Refinements:
- Typed obligation OBJECT as SSOT (already ~built: `build_obligation_checklist_object` + `seeded_map` exist).
- m20 blocker root cause (cursor caught, code-confirmed): `wiki_coverage_gate.check_wiki_coverage:372` failed `implementation_map_missing` when the writer omitted a row; the pre-seeded sidecar was read only to ENRICH metadata, never to supply the claim. FIXED in #2404: `_claim_from_seeded_entry` fallback + still runs substance check (no bypass) + Goodhart `duplicate_l2_error_contrast_claim` sentinel.
- Prompt 143KB > ceiling → de-dup'd err-stub render (#2404 follow-on commit). Full diet + exemplar wiring = fast-follow (#2389).

## Shipped this session (main 475030d389)
- **#2402** C345 — 15 émigré dossiers (fabrication-verified 31/31 paths).
- **#2405** R5 — 9 war-killed dossiers (codex corrected my brief's "Ілля Цибух"→"Ірина Цибух"; honest-resolution worked).
- **#2406** C12 — 11 émigré dossiers (all §7 plan paths verified real).
- **#2404** m20 gate-seam fix + de-dup (the anchor unblock). All on main.

## Queued (autonomous, after anchor ships)
1. **Full prompt-diet <130KB + wire 9.5/10 exemplar** into empty `<example>` slot (linear-write.generated.md) — #2389. NOTE: exemplar ADDS bytes, so must come with real diet.
2. **R5 agy-3** (hlib-babich, maks-levin, viktor-hurniak) — 3 dossiers STAGED in worktree `.worktrees/dispatch/agy/bio-r5-warkilled-2026-05-28` + dangling commit `589ca75a30`; branch tangled (HEAD reset to briefs commit cb759acc1f). Do CLEAN: new branch off main, add only the 3 files, PR. Completes R5 to 12/12.
3. **#2400** (gemini Block D, PR open) — GENUINE fabrication (~20 nonexistent plan paths cited "Existing"). Inline: verify each with `test -e`, relabel fakes→"Candidate (Phase 2+)", fix metadata (#2318→#2317, Gemini-1.5-Pro→gemini-3.1-pro), push to gemini branch, then merge. DON'T merge until fixed.
4. **Bio-epic expansion** toward 130 (epic #2309): next blocks = Helsinki Group depth, religious martyrs, Crimean-Tatar, scientists. Use claude (headroom confirmed by user) + codex.

## Writer/agent policy (confirmed this session)
codex-tools = V7 writer. Claude HAS headroom now (user direction — overrides #M0 seat-competition caution). gemini just fabricated (#2400) — avoid for fabrication-risky factual research. Bio briefs MUST carry the anti-fabrication guard (`test -e` every §7 plan path; identity-resolve-or-flag).

## What NOT to do
- Don't raise WRITER_PROMPT_CEILING_BYTES — diet instead.
- Don't merge #2400 until fabrication relabeled.
- Don't do concurrent git-worktree ops while a build's worktree is being created (lock contention — hit twice this session; clear stale 0-byte locks only after confirming no git process).
