# BIO Orchestrator Suite

Prompt version: 0.1
Last reviewed: 2026-06-22

## Source Assumptions

- BIO is a seminar biography track, not C1 core. It uses source-tier dossiers, decolonization review, portrait/image-rights rules, and politically charged biography framing.
- **SSOT for module ordering / slugs is `curriculum/l2-uk-en/curriculum.yaml` (`levels.bio.modules`, 387 slugs).** The 2026-06-29 expansion appended **+77 new slugs** (`modules[310:387]`) in six groups; their roster and framing live in `docs/audits/bio-ukrainian-expansion-research-2026-06-29.md`, with the surface inventory in `docs/audits/bio-readiness-matrix-2026-06-29.md`. The 130/180-figure appendix in `docs/audits/bio-track-gap-audit-2026-05-26.md` is the ORIGINAL roster only — do not treat it as the SSOT or as covering the +77.
- Current source surfaces include `curriculum/l2-uk-en/plans/bio/*.yaml`, `docs/research/bio/*.md`, `wiki/figures/*.md` (+ `wiki/figures/*.sources.yaml`), `docs/audits/bio-track-gap-audit-2026-05-26.md`, `docs/best-practices/bio-research-source-tiers.md`, `docs/best-practices/bio-image-rights.md`, and `docs/best-practices/politically-charged-bios.md`.
- Every module needs primary voice readings when available: letters, poems, speeches, memoir passages, court statements, diaries, interviews, or archival documents by/about the figure.
- This suite covers **readiness-gate, base-prep, production, quality audit, and remediation.** Use only the stage that matches the task. The +77 are under the **no-module-writing readiness gate (#2535)** — see the Readiness Gate section before any base-prep or production work.

## Goal

Orchestrate BIO work in small batches without touching B2. Verify source-tier coverage, build biographies with primary readings and careful rights/framing, audit decolonization and factuality, and remediate blockers.

## Readiness Gate And Stage Sequencing

The +77 expansion roster sits behind a **no-module-writing readiness gate (#2535)**, enforced through the **#4006 prompt gate** before the **#4005 base-prep** issue. Keep the stages distinct; do not collapse them:

1. **Readiness gate (#2535):** inventory and promotion only. A slug is NOT ready just because a row could be filled (memory #M-11: deterministic gates are necessary but not sufficient).
2. **Base prep (#4005):** for a promoted slug, write — in order — the research dossier (`docs/research/bio/{slug}.md`), then the plan YAML (`curriculum/l2-uk-en/plans/bio/{slug}.yaml`), then the wiki packet (`wiki/figures/{slug}.md` + `wiki/figures/{slug}.sources.yaml`). NO `module.md` / activities / vocabulary at this stage.
3. **Production:** build the module source + site MDX only after dossier + plan pass.
4. **Quality audit / remediation:** as below.

**Hard rule:** do not write any BIO module (`curriculum/l2-uk-en/bio/<slug>/...`) for a +77 slug until its dossier AND plan exist and pass. The pilot is `oleksandr-bilash` (#4004); start base prep from the readiness matrix's "First Claude Batch" only.

## WORKTREE_ROOT Setup

```bash
REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
cd "$REPO_ROOT"
git fetch origin main
git worktree add -b codex/bio-<stage>-<batch> .worktrees/dispatch/codex/bio-<stage>-<batch> origin/main
cd .worktrees/dispatch/codex/bio-<stage>-<batch>
test -e .venv || ln -s "$REPO_ROOT/.venv" .venv
export WORKTREE_ROOT="$(pwd)"
pwd
git status --short --branch
git rev-parse --show-toplevel
```

## Read First

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- `docs/audits/bio-track-gap-audit-2026-05-26.md` (ORIGINAL roster scope only)
- `docs/audits/bio-ukrainian-expansion-research-2026-06-29.md` (+77 roster, framing, holds/watchlist)
- `docs/audits/bio-readiness-matrix-2026-06-29.md` (+77 surface inventory, #2535 gate, first batch)
- `docs/audits/bio-decolonization-checklist.md`
- `docs/best-practices/bio-research-source-tiers.md`
- `docs/best-practices/bio-image-rights.md`
- `docs/best-practices/bio-naming-canonical.md`
- `docs/best-practices/politically-charged-bios.md`
- `docs/templates/bio-research-dossier-template.md`
- target `curriculum/l2-uk-en/plans/bio/<slug>.yaml`

## Allowed Writes

- Readiness gate or quality audit: `docs/audits/bio-<scope>-<date>.md`
- Base prep (#4005), for scoped promoted target slugs only:
  - research dossier `docs/research/bio/<slug>.md` (per `docs/templates/bio-research-dossier-template.md`)
  - plan YAML `curriculum/l2-uk-en/plans/bio/<slug>.yaml` (per `bio-naming-canonical.md` + `bio-image-rights.md`)
  - wiki packet `wiki/figures/<slug>.md` and `wiki/figures/<slug>.sources.yaml` (the canonical wiki layout is `wiki/figures/`, NOT `wiki/bio/`)
- Production (only after dossier + plan pass), for scoped target slugs only:
  - current-layout source files under `curriculum/l2-uk-en/bio/<slug>/`
  - `site/src/content/docs/bio/<slug>.mdx`
  - hostable readings under `site/src/content/readings/`
- PR body or final orchestration note text

## Forbidden Writes

- `docs/prompts/orchestrators/b2/**`
- unrelated BIO plans, dossiers, modules, or image assets
- non-hostable copyrighted full text or images
- `.python-version`, `.yamllint`, `.markdownlint.json`
- generated `status/`, curriculum `audit/`, curriculum `review/`, and `data/telemetry/**` artifacts

## Lifecycle Rules

- Preflight: verify Tier 1/Tier 2 source packs, primary voice readings, portrait rights or fallback, and content-warning fields for politically charged figures.
- Base prep (#4005): write dossier → plan YAML → wiki packet (in that order) for promoted slugs only. Validate dossier §7 cross-track paths with `scripts/audit/lint_bio_dossier_xref.py`. Do not advance to production until both dossier and plan pass.
- Production: foreground Ukrainian agency and the specific oppression mechanism; cite narrow, not broad; include primary voice when legally usable.
- Quality audit: run the decolonization checklist, source-tier audit, naming/transliteration check, portrait-rights check, and reading-link/copyright review.
- Remediation: fix source authority and framing blockers before prose polish.

## Track-Specific Checks

- Russian/Soviet sources are historical evidence, not authority over Ukrainian identity or motives.
- Do not write hagiography. Name documented contested ideology, civilian harm, collaboration allegations, or memory disputes with sourced precision.
- For recent war-killed or captivity figures, avoid re-victimizing images or propaganda-origin material.
- **Canonicity over currency (+77):** for the 13 LIVING figures, build only on completed, settled work — no predictive "future national leader" framing. **Current-wartime watchlist figures are excluded from new BIO additions** (Берлінська, Вишебаба, Чорногуз, Чмут, Федоров, Буданов, Стерненко, Христов); `Залужний` is a deliberate single-case hold; `Сікорський` stays excluded (fails the Ukrainian-civic filter). Do not open base-prep for any of these. Source: `docs/audits/bio-ukrainian-expansion-research-2026-06-29.md`.
- **HIST-alignment gate:** for state-building, UNR/ZUNR, dissident, independence, and wartime figures, align the historical frame with HIST (run the HIST-alignment checkpoint) rather than inventing a frame inside the biography. Record the alignment in the dossier and plan.

## Helpers And Headroom

Use read-only helpers for source-tier packets, image-rights checks, and politically charged framing review. Compress long findings with Headroom.

## Validation Commands

Adapt to current target layout:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path("curriculum/l2-uk-en/plans/bio").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("bio plans parse")
PY
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

For base-prep dossiers, validate §7 cross-track paths (fabricated "Existing" paths = gate failure):

```bash
.venv/bin/python scripts/audit/lint_bio_dossier_xref.py --paths docs/research/bio/<slug>.md
```

For built modules, add activity, vocabulary, generated MDX, liveness, and site checks from `shared/validation-checklist.md`.

## Expected Final Response

```text
BIO stage: <preflight | production | quality-audit | remediation>
Scope: <slugs or audit report>
Source-tier coverage: <summary>
Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>
Portrait rights: <hosted/link-only/omit/needed counts>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted | not module-build | unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
