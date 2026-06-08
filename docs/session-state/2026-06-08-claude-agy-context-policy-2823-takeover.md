# Claude orchestrator session handoff — 2026-06-08

Generated at end-of-session (user-requested handoff at the ~500K mark; autocompact
DISABLED this session so handoff is the only context guard).

## Canary / context integrity at handoff
- Autocompact OFF (user 2026-06-08). Policy now: handoff @~500K this phase, ~700K next, canary-gated.
- Brain-rot monitor shipped: `scripts/context_canary.py` (mint/score/log). Log: `batch_state/canary/canary_log.csv`.
- Data points this session: 250K → 8/8 (1.00); ~480K → 7/8 (0.88) PASS. The single "drift" was a STALE anchor (the `--to-model` fix changed reality mid-session), NOT rot — all immutable anchors (SHAs/counts/issues) scored 1.00.
- Refinement for next time: mint ONLY immutable anchors.

## Shipped + merged this session (all on origin/main)
1. **Dependabot**: merged trufflehog/mcp/inscriptis/stevedore/mypy(1→2). Closed #2825 stanza (1.12.1 imports `udtools` not installed → ModuleNotFoundError breaks `ukrainian_word_stress`; held at 1.11.0).
2. **Security #1896**: `scripts/safe_env.sh` (leak-proof env probe, SET/UNSET only) → `5cd67954ab`. Issue closed.
3. **Agy lane hardening #2739+#2362**: PR #2839 merged (`bf911f6d84`). Finalize auto-recovery on rc==0+dirty, valid `agy` X-Agent trailer, agy `file://` tool-result inlining. DeepSeek review caught a real **P1** (push/PR-fail-after-commit ambiguous state) → fixed with `reset --soft` rollback + GIT_* denylist + worktree guard. Both issues CLOSED.
4. **Agy --to-model fix** (`ca7da76fa5`): ported kubedojo's fix — `_extract_target_model` now reads `to_model` from the `data` JSON blob (the `messages` table never had a `to_model` column). **Verified live**: `ask-agy --to-model "Gemini 3.1 Pro (High)"` now engages pro (was silently flash forever). Unblocks agy model routing + the §7 re-test.
5. **Agy routing flip** (MEMORY #M0/#0, both source + auto-memory): "gemini lane" = agy as default unmetered lane. EXCEPTION held: wiki/factual writer (L73/L112) NOT flipped — pending §7 fabrication clearance.
6. **Context cap**: `start-claude.sh` autocompact 750K→1M (`40aaa0ffd4`); then user disabled autocompact entirely. Canary policy committed (`ecd6cfa4d2`).
7. **Color de-Sovietization** (`e4bf1398ee`): main `.lu-hero` led with navy `#003D82` + goldenrod `#B8860B` (imperial/Soviet read). Now flag-true azure gradient `#0057B8→#1A6FD4` + bright-yellow rule; `*-dark` tokens moved in-family (`#004B9C`/`#E6B800`) with a guard comment. **Needs manual Pages deploy (`deploy-pages.yml` workflow_dispatch) to go live.**

## Open epics / next actions (priority order)
1. **#2823 lightweight UI — TAKEN OVER, foundation only.** Audit posted to issue (comment 4652341381). KEY FINDING: **Starlight already removed** (pure Astro+MDX+React + `CourseLayout`) → AC#1 audit + AC#2 architecture (Astro-without-Starlight) DONE. 6-slice plan in the issue. NOTHING implemented to POC-fidelity yet; NO built-UI design review done. **User's open question: "do all pages look nice / best-practice?" → answer is NO/UNVERIFIED.** Next: slice 1 (de-Starlight cleanup: bulk-rename Tabs import, drop Vite alias + `--sl-*` aliases + dead CSS + `template` field), then slices 2-6. Slice 6 = the visual design review the user asked for (build site, screenshot every page class, assess fidelity/typography/contrast/responsive/dark-mode/a11y).
2. **Agy wiki-lane flip** (now unblocked by the --to-model fix): rigorous §7 re-test on agy `gemini-3.1-pro-high` + an OBSCURE bio + a COMPLETE reference (web, not partial corpus — this session's probe used ukrlib-stus which gives false-negatives). If clean → wire `agy` into `scripts/wiki/compiler.py` `WRITER_CHOICES` (currently only gemini/claude/gpt-5.5) + flip L73/L112.
3. **Trigger manual Pages deploy** to push the color fix live.

## §7 bakeoff result (for the flip decision)
agy-flash AND agy-pro produced NO CONFIRMED §7 fabrication on the Stus probe (facts accurate + richer on pro). BUT verification was corpus-limited (ukrlib-stus partial) — one pro quote «Терпи, терпи — терпець тебе шліфує» is a real Stus line absent from our corpus, scored unverifiable. Not a clean clearance; needs a complete reference.

## Hands-off (parallel agents — do not touch)
- Session-handoff protocol (another agent), #2832 coordination ledger (PR #2833 area), #2824 M8 MDX sync.

## Decisions locked this session
- Agy = default gemini-family dispatch lane (gemini-cli replaced); wiki/factual held pending §7.
- Autocompact OFF; graduated 500/700 handoff; canary-gated.
- #2823 architecture = Astro-without-Starlight (already in place; cleanup not migration).
- Brand colors = flag-true azure #0057B8 + yellow #FFD700; navy #003D82 + goldenrod #B8860B RETIRED (decolonization).
