# BIO Orchestrator Suite

Prompt version: 0.3
Last reviewed: 2026-07-04

## Source Assumptions

- BIO is a seminar biography track, not C1 core. It uses source-tier dossiers, decolonization review, portrait/image-rights rules, politically charged biography framing, and human-centered narrative prose.
- **SSOT module ordering / slugs:** `curriculum/l2-uk-en/curriculum.yaml` (`levels.bio.modules`; derive the live count from the manifest). The 2026-06-29 expansion is historical context only; roster framing lives in `docs/audits/bio-ukrainian-expansion-research-2026-06-29.md`, surface inventory in `docs/audits/bio-readiness-matrix-2026-06-29.md`.
- The 130/180-figure appendix in `docs/audits/bio-track-gap-audit-2026-05-26.md` covers the original roster only; do not treat it as the SSOT for +77.
- Current source surfaces include `curriculum/l2-uk-en/plans/bio/*.yaml`, `docs/research/bio/*.md`, `wiki/figures/*.md`, `wiki/figures/*.sources.yaml`, `curriculum/l2-uk-en/bio/<slug>/`, generated site BIO pages, BIO audits, and BIO best-practice docs.
- Every production module needs primary-voice readings where available: autobiographical writing, letters, poems, speeches, memoir passages, court statements, diaries, interviews, archival documents, or reliable contemporaneous documents by/about the figure.
- This suite covers readiness-gate, base-prep, production, quality audit, LLM-QG closure, and remediation. Use only the stage that matches the task.

## Goal

Orchestrate BIO from scattered source surfaces to shippable student modules.
The ultimate goal is not merely adding dossiers: every selected BIO figure must
reach module-ready or module-shipped state with the required plan, dossier, wiki
packet, image/rights notes, source/reading leads, module files, generated page,
deterministic gates, persisted LLM-QG, and independent review.

Do this without touching unrelated tracks. Keep source preparation separate from
module production, build production modules only after source artifacts pass, and
make each finished BIO page teach by telling the story of an important human
being rather than narrating how a lesson is constructed.

## Definition Of Ready And Done

Use these states in issue comments, worker prompts, and monitor handoffs:

- `inventory`: slug exists in `curriculum.yaml` or candidate queue, but surfaces
  have not been checked against live repo state.
- `source-ready`: dossier exists and passes xref/source-tier checks.
- `plan-ready`: plan YAML exists, parses, matches the dossier's figure and
  framing, and has no seminar-quality or title/subject drift blockers.
- `wiki-ready`: `wiki/figures/<slug>.md` and `.sources.yaml` exist, have clear
  source roles and portrait/image-rights notes, and pass wiki subject/source
  checks where applicable.
- `module-ready`: source-ready + plan-ready + wiki-ready, with reading/source
  leads and image-rights decisions recorded. This is the earliest state where a
  writer may build `curriculum/l2-uk-en/bio/<slug>/`.
- `module-built`: module, activities, vocabulary, resources, generated MDX, and
  permitted readings exist and pass deterministic gates. This is an observed
  artifact state: a legacy pilot may be `module-built` while still blocked from
  promotion by missing manual evidence.
- `qg-current`: the built module has current persisted LLM-QG state in the local
  LLM-QG store or a current module-local `llm_qg.json`; generated QG artifacts
  and telemetry DBs stay out of PR diffs.
- `shipped`: module-built + qg-current + independent review clear + merged.

If a slug is missing one or more prep surfaces, dispatch base-prep workers before
module writers. If a slug is built but lacks current LLM-QG, route QG closure
before claiming it shipped.

Use `.venv/bin/python scripts/audit/bio_readiness_ledger.py --format summary`
for the live roster. The ledger keeps fail-closed promotion milestones separate
from observed `artifact_state` and `release_state`; an existing build with no
current QG must remain visibly `qg-pending`. In a worktree, point
`LEARN_UKRAINIAN_LLM_QG_DB` or `--llm-qg-db` at the operator's read-only store.
If that store is unavailable, report QG as unknown rather than claiming zero
current results.

For `independent_content_review`, reviewer independence is evaluated against
the module author/model family and recorded in the linked evidence. One
cross-family review may supply both corpus-hammer and content-review evidence
when it explicitly performs both checks; the ledger never infers either pass.

## Readiness Gate And Stage Sequencing

- **Readiness gate / audit:** inspect roster, source surfaces, rights, framing risks, LLM-QG state, and sequencing. Write only durable audit notes under `docs/audits/` when explicitly scoped.
- **Base prep (#4005 pattern):** write dossier -> plan YAML -> wiki packet, in that order, for promoted target slugs only. No `module.md`, activities, vocabulary, resources, site MDX, or generated output in base-prep PRs.
- **Production:** only after dossier, plan, and wiki packet pass. Write current-layout module files under `curriculum/l2-uk-en/bio/<slug>/` plus generated site MDX and permitted reading pages/resources.
- **Quality audit:** read built pages and source artifacts; record findings without writing generated `status/`, curriculum `audit/`, or curriculum `review/` artifacts.
- **LLM-QG closure:** for built modules without current LLM-QG, run or route the documented LLM-QG/parity path, persist the result, keep telemetry/QG artifacts out of PRs unless explicitly allowed, and treat near-threshold seminar modules as candidates for second independent review.
- **Remediation:** fix source authority, framing, narrative voice, activity placement, MDX/render, and validation blockers in small scoped PRs.

**Hard rule for +77 and later additions:** do not write any BIO module under `curriculum/l2-uk-en/bio/<slug>/...` until that slug's dossier, plan, and wiki packet exist and pass. The Bilash pilot (`oleksandr-bilash`, #4004) is an exception only because its source artifacts already existed and it was the first production/remediation pilot. It still must not be counted as shipped until `module_quality_audit.py --level bio` reports current LLM-QG.

**Known live follow-up as of 2026-07-04:** `oleksandr-bilash` is built and surface-policy clean, but `module_quality_audit.py --level bio --format json` reported `llm_qg_status: missing`, `needs_llm_qg: true`, and `second_review_reason: seminar_high_risk`. Re-check live state before acting, then route LLM-QG closure if still missing.

## Fleet Operating Model

BIO has hundreds of figures; do not run it as one agent doing every step. Use a
visible-worker pipeline, but keep the orchestrator accountable for integration.

- **Codex orchestrator/release manager:** owns live-state inspection, queue
  state, worktree/thread creation, branch naming, issue ledger updates, final
  diff review, deterministic gates, independent-review routing, merge decisions,
  scheduler updates, and artifact hygiene. The orchestrator does not write
  dossiers or modules inline except to fix a narrow release blocker.
- **Visible worker threads only for writing:** writer workers run in visible
  Codex app threads/worktrees, own their branch/PR, open draft PRs, and stop.
  Hidden `scripts/delegate.py` workers are allowed only if the user explicitly
  asks for invisible local delegation.
- **Parallelism target:** keep two independent writer workers active by default
  when scopes are disjoint. Use three only for low-risk one-file base-prep
  slices after the pipeline has stayed clean. Keep at most two open worker PRs
  awaiting orchestrator review at once.
- **Read-only helpers:** source/cross-track explorers may run in parallel with
  writer workers for existing curriculum links, source-tier packets, naming
  variants, image-rights notes, missing-surface matrices, and factual-risk
  summaries. They report claims and citations, not essays.
- **Worker ownership patterns:** dossier-only workers own
  `docs/research/bio/<slug>.md`; plan-only workers own
  `curriculum/l2-uk-en/plans/bio/<slug>.yaml`; wiki workers own
  `wiki/figures/<slug>.md` and `wiki/figures/<slug>.sources.yaml`; module
  writers own only the explicitly listed files under
  `curriculum/l2-uk-en/bio/<slug>/`, generated MDX, and permitted readings.
  Do not mix base-prep and module production in one worker unless a prior
  readiness matrix explicitly authorizes that slice.
- **Sequential merge queue:** workers may prepare independent PRs in parallel,
  but the orchestrator merges one PR at a time after scope, gates, CI, and
  independent review are clean. Merge order follows dependency order:
  dossier -> plan -> wiki -> module -> QG/remediation, unless the issue ledger
  records a reason to skip or hold a slug.
- **Specialist review routing:** use an independent non-Codex route for BIO
  factual/decolonization/content review. AGY/Gemini via the project bridge is a
  known working route; DeepSeek/Hermes-style review is suitable for
  decolonization and sensitive framing when available; Cursor/non-Codex review
  is suitable for UI/front-end or larger code diffs. Internal Codex helper
  review does not satisfy the independent-review gate.
- **Token economy and speed:** deterministic tools first. Do not ask a model to
  verify paths, whitespace, YAML parseability, CI state, or simple inventory.
  Summarize large logs/source dumps before cross-agent handoff.
  Keep worker briefs compact: slug, stage, owned files, known source leads,
  validation commands, forbidden writes, and stop condition.

## Monitor Wake Protocol

Every wake starts from live state, not memory:

1. Run `git status --short --branch` at repo root. Preserve unrelated dirty
   files and worktrees.
2. Inspect active visible worker threads/worktrees first. If any worker has a
   draft PR, review that PR before dispatching more writing.
3. Query open BIO PRs and the relevant GitHub issue/ledger. Do not rely only on
   the previous heartbeat summary.
4. Run or refresh the readiness matrix for the active queue: plan, dossier, wiki
   packet, module files, generated MDX, readings/resources, LLM-QG state, and
   known blockers.
5. Fill the pipeline only after review capacity is clear: target two active
   independent workers, not a single leisurely worker and not an unbounded pile
   of PRs.
6. Merge clean PRs one at a time, fast-forward root `main`, archive workers,
   clean worktrees/branches, update the ledger, then dispatch the next worker.

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

- `AGENTS.md` for Codex. Non-Codex workers may read their provider-specific
  instruction files when their runtime requires it; Codex workers should not
  load `CLAUDE.md` or `GEMINI.md` for normal startup.
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/prompts/orchestrators/shared/seminar-source-rules.md`
- `docs/prompts/orchestrators/shared/reading-section-rules.md`
- `docs/audits/bio-track-gap-audit-2026-05-26.md` (original roster scope only)
- `docs/audits/bio-ukrainian-expansion-research-2026-06-29.md` (+77 roster, framing, holds/watchlist)
- `docs/audits/bio-readiness-matrix-2026-06-29.md` (+77 surface inventory and #2535 gate)
- `docs/audits/bio-decolonization-checklist.md`
- `docs/best-practices/bio-research-source-tiers.md`
- `docs/best-practices/bio-image-rights.md`
- `docs/best-practices/bio-naming-canonical.md`
- `docs/best-practices/politically-charged-bios.md`
- `docs/templates/bio-research-dossier-template.md`
- Target plan: `curriculum/l2-uk-en/plans/bio/<slug>.yaml`
- Target dossier: `docs/research/bio/<slug>.md`
- Target wiki packet when production/remediation uses one: `wiki/figures/<slug>.md` and `wiki/figures/<slug>.sources.yaml`

## Allowed Writes

- Readiness gate / quality audit: `docs/audits/bio-<scope>-<date>.md` only when explicitly scoped.
- Base prep: `docs/research/bio/<slug>.md`, `curriculum/l2-uk-en/plans/bio/<slug>.yaml`, `wiki/figures/<slug>.md`, and `wiki/figures/<slug>.sources.yaml` for promoted slugs only.
- Production/remediation: `curriculum/l2-uk-en/bio/<slug>/module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`, generated `site/src/content/docs/bio/<slug>.mdx`, and permitted `site/src/content/readings/<reading-slug>.mdx`.
- Prompt-suite fixes: `docs/prompts/orchestrators/bio/**` and directly shared prompt-suite files only when the failure is cross-BIO or cross-seminar.
- PR body and final orchestration note metadata, including telemetry summary and review status.

## Forbidden Writes

- Do not touch `docs/prompts/orchestrators/b2/**` or unrelated track prompt suites.
- Do not change `.python-version`, `.yamllint`, `.markdownlint.json`, package files, or linter configs.
- Do not write generated `curriculum/l2-uk-en/**/status/*.json`, `curriculum/l2-uk-en/**/audit/*-review.md`, `curriculum/l2-uk-en/**/review/*-review.md`, `docs/*-STATUS.md`, or `data/telemetry/**` into the diff.
- Do not host non-public-domain or otherwise non-hostable full texts under `site/src/content/readings/`.
- Do not write module markdown, activities, vocabulary, site MDX, reading pages, or telemetry DB files during dossier-only base prep.

## Lifecycle Rules

- Readiness gate: verify roster position, source availability, reading candidates, portrait rights, politically charged framing, and cross-track dependencies before authoring production content.
- Base prep: validate source tiers, naming/transliteration, portrait/image rights, and dossier §7 cross-track paths with `scripts/audit/lint_bio_dossier_xref.py`. Fabricated "Existing" paths are blockers.
- Production: start from the person's life, works, sources, and reception. Build narrative, vocabulary, readings, activities, and resources around that evidence.
- Quality audit: read the learner-facing generated page, not just source files. Score factual grounding, decolonization, narrative voice, English leakage, internal-workflow leakage, LLM fingerprint, activities split, vocabulary usefulness, resource/readings behavior, and dark/light mode UI if touched.
- Remediation: fix source authority, historical framing, internal leakage, activity placement, and render blockers before style polish.

## BIO Narrative And Register Standard

BIO pages teach by telling the tale of a person. The prose should sound like a careful Ukrainian cultural biography for adult learners, not a prompt, lesson plan, audit memo, or author talking to themself.

Required learner-facing stance:

- Lead with a concrete human, historical, artistic, or moral scene: place, voice, work, decision, consequence, memory. Do not open with course mechanics.
- Explain why the figure matters through lived detail, works, choices, reception, and documented context. Let the reader infer learning value from the story.
- Use direct, fluent Ukrainian exposition. Keep teacher guidance rare and embedded in the narrative, not as self-referential instructions.
- Handle complexity in human terms: documented ambiguity, pressure, compromise, courage, error, reception, and legacy. Avoid flattening a person into a label.
- For Soviet/imperial contexts, name institutions and constraints when sourced, but do not let the security-service or regime frame swallow the Ukrainian cultural subject.

Forbidden learner-facing patterns in `module.md` and generated MDX:

- Meta-course nouns: `цей урок`, `цей модуль`, `ця біографія`, `у курсі`, `для учня`, `для рівня C1`, `навчальна біографія`, `сторінка`, `завдання`.
- Self-instructional phrases: `важливо показати`, `треба пам'ятати`, `не треба перетворювати`, `може працювати як вхід`, `урок виконав`, `сильна відповідь`, `добра відповідь`, `після цього уроку`.
- English scaffolding or prompt residue: `lesson`, `module`, `learner`, `workbook`, `inline`, `BIO track`, `source-tier`, `gate`, `prompt`, `audit`, `review`, `telemetry`, `LLM`.

## Learner-Facing Quality And Activity Placement

- Keep build/source-verification language out of learner pages: no `prompt`, `audit`, `review`, `telemetry`, `source-tier`, `gate`, `chunk_id`, `source_chunk`, corpus/service IDs, `learner-facing`, `hosted reading`, or validation-tool language in public prose.
- Student-visible body prose should be Ukrainian unless the current track/page component explicitly permits English UI labels or vocabulary glosses.
- Teach through the subject matter: source passages, biography, historical context, literary form, performance, register, and interpretation. Do not narrate how the lesson is being built.
- For any production/remediation module that uses inline practice, use Activity YAML V2 with `inline:` and `workbook:` lists. Never wrap the root in an `activities:` key.
- Each `inline:` activity must have exactly one matching `<!-- INJECT_ACTIVITY: <id> -->` marker in `module.md`. Workbook activities must not have prose markers.
- The Lesson tab must not absorb the entire practice set, and the Workbook/Activities tab must not be empty.
- PR/final notes for built-module work must report `inline=<n>`, `workbook=<n>`, rendered Lesson tab status, rendered Workbook/Activities tab status, English leakage status, internal-leakage status, and an LLM-fingerprint score.

## Activity Placement Contract

- BIO production/remediation must use Activity YAML V2 with `inline:` and `workbook:` lists whenever the lesson includes inline practice.
- `inline:` activities are short checks or interpretive pauses anchored in lesson prose. Each one must have exactly one matching `<!-- INJECT_ACTIVITY: <id> -->` marker in `module.md`.
- `workbook:` activities are the practice set for the Workbook/Activities tab: deeper reading, comparison, writing, vocabulary, and critical-analysis tasks. Workbook activities must not have prose markers.
- The Lesson tab must not absorb the entire practice set. The Workbook/Activities tab must not be empty.
- PR validation/final notes must report inline count, workbook count, and rendered tab behavior.

## Track-Specific Checks

- Russian/Soviet sources can be historical evidence, not authority over Ukrainian identity or motives.
- Do not write hagiography. Name documented contested ideology, civilian harm, collaboration allegations, memory disputes, or official-career compromises with sourced precision.
- For recent war-killed or captivity figures, avoid re-victimizing images and propaganda-origin material.
- **Canonicity over currency (+77):** the 13 living figures are buildable only on completed, settled work; never use predictive "future national leader" framing. Current-wartime watchlist figures excluded from new BIO additions: Берлінська, Вишебаба, Чорногуз, Чмут, Федоров, Буданов, Стерненко, Христов. `Залужний` is a deliberate single-case hold. `Сікорський` stays excluded because he fails the Ukrainian-civic filter.
- **HIST-alignment gate:** state-building, UNR/ZUNR, dissident, independence, and wartime figures must align historical framing with HIST instead of inventing a frame inside biography. Record alignment in dossier and plan.

## Quality Score Requirements

Every BIO production/remediation PR must include a compact quality score in the PR body and final note:

- `narrative_human_tone`: 1-10
- `visible_internal_leakage`: pass/fail with examples if fail
- `english_leakage`: pass/fail with examples if fail
- `llm_fingerprint_score`: 1-10, where 10 means natural, specific, source-grounded prose and 1 means obvious generic AI prose
- `activity_split`: `inline=<n>, workbook=<n>, rendered_lesson=<pass/fail>, rendered_workbook=<pass/fail>`

Treat scores below 8/10 or any leakage fail as blockers unless the PR is explicitly audit-only.

## Helpers

Use read-only helpers for source-tier packets, image-rights checks, politically charged framing review, rendered-page reading, leakage scoring, and activity placement verification. Summarize long findings; push bulky evidence behind a file path or PR link. The main orchestrator owns edits, PR creation, independent review routing, and merge decisions.

Independent BIO review must be read-only and must inspect source files and generated learner-facing MDX/page for factual grounding, Ukrainian-centered framing, narrative human tone, English/internal leakage, LLM fingerprint, and Lesson vs Workbook/Activities placement. Treat unresolved findings as blockers.

Use helper agents deliberately and record whether helpers were used. Helpers
are for bounded work that can run in parallel without lowering quality:
source-tier packets, image-rights checks, politically charged framing review,
cross-track path discovery, rendered-page reading, leakage scoring, activity
placement verification, and CI/build triage. Summarize long findings before passing them between agents.

Do not use the full fleet as theater. For a single narrow release-blocker fix,
one worker plus an independent non-Codex review may be the economical path. For
batches, prepare several read-only/source or one-file base-prep tasks in
parallel, then merge sequentially.

The main orchestrator owns edits, PR creation, independent review routing, and
merge decisions. Worker diffs are never trusted until the orchestrator reviews
changed files and validates scope.

## Validation Commands

Always run for any PR:

```bash
git status --short --branch
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Parse current BIO plans before production/remediation decisions:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import yaml

for path in sorted(Path("curriculum/l2-uk-en/plans/bio").glob("*.yaml")):
    yaml.safe_load(path.read_text(encoding="utf-8"))
print("bio plans parse")
PY
```

Base-prep dossier validation:

```bash
.venv/bin/python scripts/audit/lint_bio_dossier_xref.py --paths docs/research/bio/<slug>.md
```

Plan, discovery, and wiki readiness validation:

```bash
.venv/bin/python scripts/validate/lint_seminar_quality.py --paths curriculum/l2-uk-en/plans/bio/<slug>.yaml --severity high
.venv/bin/python scripts/validate/check_discovery_integrity.py --track bio --json
.venv/bin/python scripts/validate/check_wiki_subject.py --paths wiki/figures/<slug>.md
.venv/bin/python scripts/validate/lint_seminar_quality.py --paths wiki/figures/<slug>.md --severity high
```

Production/remediation validation:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en bio <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/bio/<slug>/vocabulary.yaml
.venv/bin/python scripts/validate/bio_surface_quality.py <slug> --strict
.venv/bin/python scripts/audit/check_mdx_generation_drift.py --files curriculum/l2-uk-en/bio/<slug>/module.md
.venv/bin/python scripts/audit/check_mdx_source_parity.py --files curriculum/l2-uk-en/bio/<slug>/module.md
.venv/bin/python -m scripts.build.verify_shippable bio <slug>
```

For rendered-page checks, build or preview the site when practical and verify `/bio/<slug>/` has no 404, no English/internal leakage in learner prose, and non-empty Lesson and Workbook/Activities tabs.

LLM-QG status and closure for built modules:

```bash
.venv/bin/python scripts/audit/module_quality_audit.py --level bio --format summary
.venv/bin/python scripts/audit/module_quality_audit.py --level bio --format json --output /tmp/bio-module-quality-audit.json
.venv/bin/python scripts/build/run_llm_qg_parity.py bio <slug> --reviewer <non-author-reviewer>
git diff --name-only | rg -n '(^|/)llm_qg\\.json$|^data/telemetry/'
```

`run_llm_qg_parity.py` writes `llm_qg.json` and persists the DB record; do not
commit `llm_qg.json` or telemetry DB files unless a task explicitly changes the
artifact policy. After closure, rerun `module_quality_audit.py --level bio` and
record whether the slug is `current_db`, `current_file_only`, or still missing
or stale. Built seminar modules with near-threshold results or sensitive content
should get a second independent non-Codex review.

## Expected Final Response

```text
BIO stage: <preflight | base-prep | production | quality-audit | llm-qg-closure | remediation>
Scope: <slugs or audit report>
Readiness state: <inventory | source-ready | plan-ready | wiki-ready | module-ready | module-built | qg-current | shipped>
Narrative/register: <score and blockers/no blockers>
Reading coverage: <hosted/link-only/excerpt-only/omit/needed counts>
Activity split: <inline=n, workbook=n, rendered lesson/workbook status or not applicable>
Quality score: <LLM fingerprint, English leakage, internal leakage, LLM-QG status, unresolved blockers>
Files changed: <paths>
Validation run: <commands and outcomes>
Telemetry: <posted | not module-build | unavailable with reason>
Independent review: <status>
Forbidden artifacts included: no
swarm_used: true/false
swarm_label: <none | helper | swarm>
swarm_note: <helpers used, or solo run; no swarm used>
```
