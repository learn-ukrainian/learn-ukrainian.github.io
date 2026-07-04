# Module Quality Gates

This runbook defines the audit stack for all `curriculum/l2-uk-en` modules:
A1, A2, B1+, C-level core tracks, and seminar tracks.

The rule is code first. Deterministic checks run for every module. LLM review is
reserved for quality judgments that regexes, YAML schemas, VESUM, and source
tools cannot make reliably.

## Level Policy

| Track family | English policy | Reviewer calibration |
| --- | --- | --- |
| A1 | English scaffolding is expected and often substantial. | Do not penalize English task support, grammar terminology, or line-level glosses when they support a Ukrainian-first teaching move. Hard-fail only AI/internal/path leakage and clear scaffolding replacement of Ukrainian anchors. |
| A2 | Easy Ukrainian becomes the default body voice; English support decreases. | Warn on English-led prose. Do not demand B1-style Ukrainian-only explanations. Penalize English paragraphs that take over the lesson. |
| B1+ core | Learner-facing prose should be Ukrainian-led. | English is exceptional and local. Naturalness, register, collocation, and grammar government are core review targets. |
| Seminars | Advanced Ukrainian teaching voice. | English leakage, school-textbook simplification, weak source framing, and decolonization failures are high-risk. |

## Code Gates

Run these on every built module before LLM review:

- Schema and structure: markdown/YAML parse, activity schema, component props,
  inline/workbook split, required artifacts, MDX render.
- Solvability: answer consistency, minimum correct options, fill-in answers,
  translate/quiz explanations, known activity-type constraints.
- Ukrainian surface validity: VESUM, known Russianisms/surzhyk/calques/paronyms,
  bad-form heritage handling, stress/ULP gates where applicable.
- Source and citation integrity: plan-reference match, source coverage,
  quote fidelity, wiki coverage, resource URL checks.
- Leakage and register surface gates:
  - AI/persona/scratchpad leakage.
  - Local path and internal artifact leakage.
  - Level-aware English leakage.
  - Pathos/gamified/register-warning phrases.

The current implementation adds `surface_policy` to Python QG. It scans
`module.md` with level-aware English policy, and scans YAML sidecars only for
AI/path/internal leakage so normal YAML English keys, glosses, and metadata do
not become false positives.

For an all-module coverage pass, run:

```bash
.venv/bin/python scripts/audit/module_quality_audit.py --format summary
```

For machine-readable triage, use JSON and save it outside committed artifact
paths unless a task explicitly asks for a report:

```bash
.venv/bin/python scripts/audit/module_quality_audit.py --format json --output /tmp/module-quality-audit.json
```

The report counts planned modules, built modules, surface-policy failures,
current DB-backed LLM-QG records, current compact `qg_evidence.json` file
records, file-only fallback records, stale records, and missing records. It also
reports the same coverage by `a1`, `a2`, `b1_plus`, and `seminar` reviewer
profiles. Each built-module row includes reviewer family/model, gate version,
prompt hash, content hash, and whether a second cross-family review is
recommended because the module is seminar, surface-gate flagged, or
missing/stale LLM-QG.

## LLM Gates

Use LLM review only for residual judgment:

- Native Ukrainian naturalness: grammar government, collocation, idiom, calqued
  passives, unnatural nominalizations, anthropomorphic metalanguage, and
  register shifts.
- Pedagogy: sequence quality, example quality, whether the lesson actually
  teaches the target, and whether an upstream plan frame is pedagogically
  unsupported.
- Tone: consistent teacher voice, correct register for the learner level, no
  generic motivational prose.
- Engagement: whether examples, callouts, and activities carry real teaching
  value rather than filler.
- Decolonization and seminar framing: historically accurate Ukrainian-centered
  framing, source skepticism, and no Russian-imperial/Soviet default frame.

The reviewer prompt must include the level policy above. A1/A2 English support
is not a defect by itself. B1+ and seminars are held to a Ukrainian-led standard.
Reviewer responses preserve `issue_ids` and `findings` in `llm_qg.json` and the
SQLite store so known issue classes can be audited later instead of being lost
inside prose evidence.

## Persistence

LLM-QG output is expensive and must not be lost.

- Raw forensic files remain in the run archive.
- Current queryable LLM-QG state is persisted to local SQLite at
  `data/telemetry/llm_qg.db`.
- The store is content-hash bound to `module.md`, `activities.yaml`,
  `vocabulary.yaml`, and `resources.yaml`.
- API readers prefer the current SQLite record and fall back to module-local
  `llm_qg.json` only when the file is newer than all learner-facing content.
- Corrupt local telemetry DBs degrade to missing QG rather than breaking the
  Monitor API.
- Generated QG artifacts and telemetry DBs stay out of PR diffs.
- Standalone parity runs via `scripts/build/run_llm_qg_parity.py` also persist
  to the SQLite store after writing `llm_qg.json`.

## Team Roles

Use five roles for implementation work on this system:

| Role | Owner | Responsibility |
| --- | --- | --- |
| Integrator | Main Codex thread | Architecture, worktree hygiene, final merge shape, tests, and resolving reviewer findings. |
| Deterministic-gates reviewer | Explorer or worker | Code-first checks, false-positive risk, level policy, activity solvability, and Python-QG integration. |
| Persistence/API reviewer | Explorer or worker | Durable QG storage, stale-state prevention, Monitor API behavior, and artifact-policy compliance. |
| Prompt/language reviewer | Language-focused reviewer | LLM prompt calibration for A1/A2/B1+/seminars and Ukrainian naturalness failure modes. |
| Independent reviewer | Non-author route | Final read-only review of the diff and prompt behavior before PR/merge. Internal Codex self-review is not enough. |

For broad sweeps, use one main integrator plus two or three parallel reviewers.
Do not use five implementation workers on the same files; that increases
merge risk without improving language quality.

## LLM Review Cost Model

Default production flow:

1. Run deterministic gates for every module.
2. Run one primary LLM-QG reviewer only after code gates pass or produce a
   bounded warning set.
3. Persist the LLM-QG result immediately.
4. Run a second cross-family LLM reviewer only for:
   - modules flagged by deterministic gates,
   - modules where the primary LLM-QG score is near threshold,
   - seminars and politically/factually sensitive tracks,
   - prompt-version canaries,
   - a random calibration sample.

Do not run 2x LLM review on every module by default. Measure marginal recall
first. If the second reviewer catches materially different issues on sampled
modules, expand the sample. If it mostly duplicates the primary reviewer, keep
it as a canary and escalation path.

## Review Of The LLM Check

The LLM check itself is reviewed in three layers:

- Machine checks: JSON shape, required evidence quotes, exact dimensions, score
  aggregation, persistence, and content-hash freshness.
- Calibration checks: prompt canaries for known defects such as `застереження
  каже`, bad passives, wrong government, bad lock/open/medicine collocations,
  A1/A2 English scaffolding, and seminar decolonization framing.
- Independent review: a non-author reviewer checks prompt changes and sampled
  LLM-QG outputs against the actual module text.

If the LLM gate misses a known seeded defect, treat that as a prompt/eval bug,
not as a module-only bug.

Run deterministic canary evaluation before paying for a large LLM batch:

```bash
.venv/bin/python scripts/audit/llm_qg_canaries.py --level b1 --list
.venv/bin/python scripts/audit/llm_qg_canaries.py --level b1 /tmp/reviewer-canary-result.json
```

The canary set includes required-catch cases (`застосунок має бути відкритий`,
`Застереження каже: ...`, AI leakage, path/internal leakage, B1/seminar English
leakage, seminar pathos) and false-positive protection for allowed A1/A2
English scaffolding.

Run the PR1 curriculum fixture harness before changing deterministic checks or
reviewer prompts:

```bash
.venv/bin/python scripts/audit/curriculum_qg_harness.py \
  --fixtures tests/fixtures/curriculum_qg/fixtures.yaml

.venv/bin/python scripts/audit/curriculum_qg_harness.py \
  --module-dir curriculum/l2-uk-en/b1/aspect-in-imperatives \
  --level b1 --slug aspect-in-imperatives
```

The fixture harness emits compact `curriculum_ua_qg_evidence.v1` records with
module id, level policy, checker version/config hash, content hash,
per-dimension scores, exact bounded findings/spans, and deterministic/LLM-source
metadata. It is a calibration harness, not a bulk LLM runner.

## Batch Rollout

Run in phases:

1. Calibrate on known bad and known good modules from A1, A2, B1, and at least
   one seminar track.
2. Run deterministic gates across all built modules and collect false positives.
3. Run primary LLM-QG only on modules that pass deterministic hard gates or need
   naturalness/pedagogy judgment.
4. Run second-review sampling and compare recall/cost.
5. Promote prompt and deterministic-gate changes only after sampled reviewers
   agree that A1/A2 support is preserved and B1+/seminar issues are caught.
