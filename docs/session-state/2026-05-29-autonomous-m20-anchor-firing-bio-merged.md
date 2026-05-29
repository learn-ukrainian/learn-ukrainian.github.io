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

**THE FORK (next chapter — needs a call):** Claude's human read of build #3 module.md = the content
is reasonable A1 (coherent reflexive-verb dialogue, sensible prose). A 3.5 on that + the wild variance
echoes the user's prior B2 read (Pt-13: "tone reviewer over-penalizes UK connectors in EN prose for an
A1 learner") + open issue **#2396** (recalibrate judges with opus-4-8). Two levers, possibly both:
- **(A) Writer-quality** — wire the 9.5/10 exemplar into the EMPTY `<example>` slot of
  `linear-write.generated.md` + lean the prompt (Q3 fast-follow #2389). Exemplar SOURCE CONFIRMED present:
  `.worktrees/builds/a1-my-morning-20260527-185032` (Pt-10 9.5 baseline). NOTE exemplar ADDS bytes → pair with diet.
- **(B) Reviewer-calibration** — #2396: the subjective-dim judge may be over-penalizing; recalibrate /
  re-examine the rubric before trusting 3.5 as ground truth. Cheaper to test: read 2-3 dim REJECT
  evidence blocks in the build's `_orchestration/` + judge if the critiques are fair.
- Recommend: (B)-quick-check FIRST (is 3.5 real?), THEN (A) exemplar if writer genuinely needs lift.
- Build #3 artifacts (forensics #M-10): `.worktrees/builds/a1-my-morning-20260529-084958/`
  (module.md + my-morning.mdx + llm_qg dim evidence in `_orchestration/`).

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
