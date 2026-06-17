# Current — Claude Session Handoff (2026-06-17 — ATLAS finished data+design; 3 follow-ups in-flight)

> **ROLE:** main orchestrator. User: grind the queue, results-focused, use the FLEET (#M-12), self-merge after review + CI-green, don't manufacture obstacles, don't idle. Quality non-negotiable.

> **🔱 ACTIVE FOCUS → full detail in `docs/session-state/2026-06-17-claude-atlas-poc-plus-three-followups.md`.**
> **Atlas DONE (merged):** data #3405/#3416 (CEFR 99.9%, all sections at ceiling), determinism #3331, **POC design #3437** (browser-verified light+dark, 0 stubs, deployed). Also immersion #3393.
> **Atlas NOT "done" per user until 3 follow-ups land:** **#3150** auto-expansion (DISPATCHED `atlas-3150-autoexpand`, verify+merge), **#3450** inflected-form dedupe, **#3449** open dictionary dataset (owner decision: publish-all + attribute + takedown, NO gating). Sequence manifest-touching work one-at-a-time (#M-9). Codex stalls silent mid build/`make atlas` — cancel+recover the build yourself (recipe in the dated doc). Deploy is MANUAL (`gh workflow run deploy-pages.yml`).
> **HARD: never raise English (MEMORY #M-13).** Awareness-only: A2-cert merge-train PRs (e.g. #3451) are track work, not the Atlas follow-ups.

---
## (prior session) 2026-06-16 evening — §6 moat slice 3 SHIPPED; full merge-train + 3 dependabot rounds cleared

## ✅ SHIPPED + MERGED this session (~22 PRs)
- **§6 decolonization moat slice 3 (#3366, advances #3098):** 6 single-word lexical calques — слідуючий→наступний, багаточисельний→численний, міроприємство→захід, учбовий→навчальний + sense-restricted любий ("any" vs authentic "dear") / неділя ("week" vs authentic "Sunday"). VESUM-verified 6/6 + heritage-confirmed no over-flagging. Surgical 3-lemma manifest patch.
- **#3318** §6 slice 2 (collocations + виглядати/біля sense-splits). **#3319 / #3361** folk #3079 pipeline (VESUM-gate exemptions + frontier-aware self-converge). **#3335** B1 M16 cert (VESUM-reviewed inline). **#3327** postmortem hygiene. ~13 dependabot bumps merged across 3 rounds.

## 🔧 KEY TECHNIQUE — surgical manifest patch (USE THIS, NOT full re-enrich)
Full `make atlas` / `enrich_manifest` re-enrich is **lossy + non-deterministic**: `_wiki_reference` hits live uk.wikipedia uncached → drops ~200 wiki refs per run (filed **#3331**). To land a small lexicon change: run `_curated_calque` over the committed manifest deterministically (network-free), patch only affected lemmas' `heritage_status.curated_calque` + `§6_note`, regen fingerprint. Diff stays minimal; wiki refs preserved. (#3318 + #3366 both used this.)

## ⚠️ DEPENDABOT WHACK-A-MOLE — root cause #2716 (ESCALATED, needs proper fix)
Flat fully-pinned `requirements-lock.txt` lets Dependabot propose bumps past parents' caps. **7 cap-violation packages this session.** Ignore list now: pydantic-core, pypdfium2, starlette, lxml, tokenizers, openai. **TODO: add huggingface-hub `>=1.0`** (transformers caps `<1.0`; closed #3370, ignore not yet shipped). Proper fix (constraints-aware manifest) commented on #2716. **Rule:** cap-check EVERY major bump before merging (`importlib.metadata` requires-scan); close + ignore violations; merge within-cap + uncapped.

## ⏭️ OPEN QUEUE (pre-assessed)
1. **#3367 stanza 1.11→1.12.2 — FAILING 1 check.** Investigate the failure (test or cap). Left open.
2. **#3373 fix(build): auto-commit python_qg_correction_loop.json (#M-10 forensics)** — INFRA, my lane (v7_build.py + test). Run `/code-review` (build-pipeline LOGIC change) before merge.
3. **#3356 [codex] Harden A2 certification tooling** — infra/tooling, review before merge.
4. **#3098 broaden** — slices 1-3 done (participles, collocations, lexical). Next: prepositional-government calques ("по"+Dat) OR re-feed #2156 calque axis. **Dispatch sizing lesson: keep calque dispatches ≤6 candidates + `high` effort + commit-early** — v1 (18 candidates, xhigh) burned 2.3M tokens with NULL deliverable; v2 (6 candidates) succeeded.
5. Drafts (track-owned, leave): #3236 b1, #3374 a1.

## ⛔ NEEDS USER DECISION
- **Orphaned working-tree A2-immersion edits** (in main tree, NOT committed): `.agents/skills/content-review/content-review-prompt.md` + `.../plan-review/review-tiers/tier-1-beginner.md` impose 50-75% hard limits / "English as main voice" — **contradicts the 2026-05-23 SSOT directive** (`v7-design-and-corpus.md`: no hard limits, converge to full immersion by end of A2). Plus untracked `docs/prompts/a2-certification-orchestration-prompt.md`. **Recommend revert**; reconcile stale `module-content-quality.md:143` "A2 40-75%" vs SSOT. Left untouched (committing = system change needing explicit go).

## Quality patterns that earned their keep (reuse)
- **Verify before promote (#M-11):** a `grep -c '§6_note'` said "2" but the deterministic Python check found all 5 lemmas correct — trust the tool, not the grep. Slice-3 v1 re-enrich was caught lossy (+509/−2492) before any commit.
- **Cap-check before merging deps majors** — caught lxml/tokenizers/openai/pypdfium2/huggingface-hub cap-violations that flat-lock CI shows green.
- **Inline VESUM/heritage review IS the Claude seat** — verified слідуючий/любий/неділя via mcp__sources; filled the gap thin Agy+Cursor dispatch reviews leave.
- **Bounded dispatches deliver; over-scoped ones starve** (slice-3 v1 lesson).

## Atlas SSOT: `docs/atlas-data-coverage-strategy.md`. Track-owned (awareness-only): folk #3079, b1/a1/a2 content dispatches, BIO.
