# BIO Prompt Gate — 2026-06-29

**Issue:** #4006 `[bio][02-prompt-gate]` · **Epic:** #2309 · **Readiness gate:** #2535 · **Blocks:** #4005 (base prep) · **Pilot:** #4004 (`oleksandr-bilash`)

Purpose: audit and minimally repair the BIO prompt suite **before** any BIO base batch starts, so #4005 does not build dossiers / plans / wiki packets from stale prompt contracts. B2 and FOLK prompt drift previously caused bad builds; this gate prevents the same on BIO.

## Verdict

**PASS WITH WARNINGS — #4005 may start, under the constraints listed below.**

All four release-blocking prompt-contract defects were found and fixed in this pass (suite-orchestrator + dossier template). No remaining blocker requires code or further prompt work before #4005. Residual items are process constraints, not prompt bugs.

## Method

Read the BIO prompt suite, shared seminar rules, best-practice docs, the two 2026-06-29 expansion audits, and the three referenced scripts; then verified every path/assumption against the on-disk repo (worktree `codex/bio-ukrainian-expansion`). Determinist checks run:

- `levels.bio.modules` in `curriculum/l2-uk-en/curriculum.yaml` → **387 slugs** (first `knyahynia-olha`, last `artem-chekh`). Confirms the +77 expansion (`modules[310:387]`) landed and the 387-module SSOT is real.
- `curriculum/l2-uk-en/plans/bio/*.yaml` → 310 files; `docs/research/bio/*.md` → 310 files. Sampled +77 slugs (`oleksandr-bilash`, `pavlo-chubynskyi`, `heorhii-narbut`, `nestor-makhno`, `fedir-vovk`) absent from both → greenfield, matching the readiness matrix.
- Wiki layout: `wiki/figures/` exists (180 `*.sources.yaml` packets, naming `{slug}.md` + `{slug}.sources.yaml`); **`wiki/bio/` does not exist.** Sampled +77 slugs absent from `wiki/figures/`.
- Companion docs all present: `politically-charged-bios.md`, `bio-track-gap-audit-2026-05-26.md`, decolonization checklist, source-tiers, naming-canonical, image-rights, plus shared `repo-rules / validation-checklist / telemetry-and-pr / review-output-schema / reading-catalog-template / seminar-track-checklists`.

## Findings

### Blockers found and FIXED

| # | Finding | Where | Fix |
| --- | --- | --- | --- |
| B1 | **Stale roster SSOT.** Dossier template said "every figure researched in Phase 1 (R1a-R5, #2317-#2322)" and "Slug source: the 130-figure appendix in `bio-track-gap-audit-2026-05-26.md`." The +77 are NOT in that appendix — they come from the 2026-06-29 memo. An agent following the template would look in the wrong SSOT and mis-file dossiers under retired Phase-1 tickets. | `bio-research-dossier-template.md` header | Dual-roster header; named `curriculum.yaml` (387) as ordering SSOT; routed +77 slug source to the expansion memo + readiness matrix; explicit "do NOT look in the 130-figure appendix." |
| B2 | **Allowed-writes mismatch + missing readiness gate.** Orchestrator `Allowed Writes` listed only *production* paths (`curriculum/l2-uk-en/bio/`, site MDX, readings). It omitted the #4005 base-prep artifacts (`docs/research/bio/{slug}.md`, `plans/bio/{slug}.yaml`, wiki packet) and carried no #2535 no-module-writing gate or stage sequencing. An agent could jump straight to module writing, or not know where base artifacts go. | `suite-orchestrator.md` Goal/Lifecycle/Allowed Writes | Added a **Readiness Gate And Stage Sequencing** section (gate → base-prep → production); split Allowed Writes into base-prep vs production with the correct paths; added a base-prep Lifecycle line; "hard rule: no module until dossier + plan pass." |
| B3 | **Missing canonicity-over-currency / wartime watchlist.** Orchestrator only mentioned "recent war-killed/captivity" image care — nothing on the 13 LIVING figures (completed-work-only / no predictive biography) or the excluded current-wartime watchlist (Берлінська, Вишебаба, Чорногуз, Чмут, Федоров, Буданов, Стерненко, Христов; Залужний held; Сікорський excluded). | `suite-orchestrator.md` Track-Specific Checks + template acceptance criteria | Added the canonicity-over-currency rule + the named watchlist/holds as a hard exclusion to both files. |
| B4 | **Missing HIST-alignment gate.** The memo's Sequencing Decision requires a HIST-alignment checkpoint for state-building / UNR-ZUNR / dissident / independence / wartime figures (many of the +77). The orchestrator had no such gate, risking biographies that invent their own historical frame. | `suite-orchestrator.md` Track-Specific Checks + template acceptance criteria | Added an explicit HIST-alignment gate, recorded in dossier §6/§7 and the plan. |

### Confirmed-clean (no fix needed)

- **`wiki/bio/` not assumed by prompts.** The orchestrator never wrote `wiki/bio/`; only the readiness matrix uses it as an inventory column (correctly marked "absent"). I still made the prompt name the canonical `wiki/figures/{slug}.md` + `{slug}.sources.yaml` so base prep targets the real layout. No contradiction remains.
- **Validation commands** parse `plans/bio/*.yaml` + `lint_agent_trailer.py` — still valid. Added the base-prep `lint_bio_dossier_xref.py` invocation (the script exists and targets `docs/research/bio/*.md` §7).
- **Shared seminar / reading / validation rules** carry no contradiction with BIO base prep. `scripts/validate/bio_subjects.py` is a helper module (no CLI) — not cited as a command, correctly.
- **No unresolved placeholders or stale paths** remain in the two edited files after the fixes.

### Warnings / residual risk (process, not prompt bugs)

1. **Issue remap not yet done.** Per the readiness matrix, #2330-#2337 / #2451 were scoped to the original roster and should be refreshed (scope-exclude or extend to the +77) before an agent treats a +77 slug as in-scope for an original-phase ticket. Track this alongside #4005; it is not a prompt-contract defect.
2. **HIST track maturity.** The HIST-alignment gate is now in the prompt, but it is a *checkpoint*, not an automated test — alignment quality depends on HIST coverage existing for the figure. Reviewers must verify it manually during base prep.
3. **First batch only.** #4005 should start from the readiness matrix "First Claude Batch" (10 settled, deceased, T1-rich, PD-portrait figures anchored by the `oleksandr-bilash` pilot). The high-CW pair (`maksym-zalizniak`, `ivan-gonta`), `nestor-makhno`, `ulas-samchuk`, all LIVING figures, and Soviet co-optation cases beyond Bilash are deliberately out of the opening batch.
4. **Block-label drift.** The original A–K block scheme does not cover the six +77 groups; the template now allows an expansion-group label, but plan/dossier reviewers should not force a +77 figure into an A–K block.

## Constraints on #4005 (the conditions of PASS WITH WARNINGS)

- Write base-prep artifacts in order **dossier → plan → wiki packet**; no `module.md` at base-prep stage.
- Honor the canonicity-over-currency and current-wartime watchlist exclusions; LIVING figures = completed-work-only.
- Run the HIST-alignment checkpoint for state-building / UNR-ZUNR / dissident / independence / wartime figures.
- Open base prep only for promoted slugs, starting from the readiness-matrix first batch / the #4004 pilot.
- Validate dossier §7 with `lint_bio_dossier_xref.py`; fabricated "Existing" cross-track paths = gate failure.

## Files changed

- `docs/prompts/orchestrators/bio/suite-orchestrator.md` — Source Assumptions (387 SSOT + +77 + gate), Read First (+2 audits), Readiness Gate section (new), Allowed Writes (base-prep vs production split), Lifecycle Rules (base-prep line), Track-Specific Checks (canonicity + watchlist + HIST-alignment), Validation Commands (dossier xref lint).
- `docs/templates/bio-research-dossier-template.md` — dual-roster header + SSOT pointer + no-module-writing gate note, Block field (+expansion groups), acceptance criteria (canonicity + HIST-alignment).
- `docs/audits/bio-prompt-gate-2026-06-29.md` — this report.

## Validation output

- Prompt-suite structural validator: **29 prompts checked; `bio/suite-orchestrator.md` clean** (the only 3 errors are pre-existing `Helpers And Headroom` gaps in `b2/*` orchestrators, untouched by this pass).
- `bio/suite-orchestrator.md` retains the required `shared/repo-rules.md` + `shared/validation-checklist.md` references (3 matches).
- `markdownlint-cli2` on both edited files: **0 errors**.
- `git diff --check`: clean.
- No YAML touched (edits are Markdown only); `curriculum.yaml`, `.python-version`, `.yamllint`, `.markdownlint.json` untouched.

---

*Read-only gate audit + minimal prompt repair. No BIO modules, plan YAMLs, dossiers, or wiki packets were authored. No staging, commit, push, or PR.*
