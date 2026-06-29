# B2 Rebuild Production Prompt Contract

> **REBUILD-SAFE CONTRACT 2026-06-29:** Do not use this prompt to continue
> old B2 production or build M69+. Current B2 M01-M68 is archived superseded
> preview generation by
> `docs/decisions/2026-06-29-b2-preview-archive-and-rebuild.md`.
> Use this contract only after PR 3 source readiness passes and PR 4 golden
> pilot acceptance explicitly authorizes rebuild-era production.

Prompt version: 1.0
Last reviewed: 2026-06-29

## Current Production Freeze

- B2 M01-M68 remain in the repo for provenance, source mining, comparison, and
  route stability only.
- Existing B2 LLM scores are content-validity provenance. They are not
  teaching-quality approval and must not be cited as proof that learner-facing
  B2 lessons are ready.
- Do not continue B2 production at M69.
- Do not hand-patch archived preview modules as if they were release candidates.
- Rebuilt B2 modules require fresh rebuild-era validation, route checks, and
  independent pedagogy review.

## Stage Gate

Run B2 rebuild work only in this order:

1. Prompt and deterministic gate hardening.
2. B2 source, plan, wiki, and research readiness audit.
3. One golden pilot rebuild accepted against this contract.
4. Small rebuild waves after the pilot is accepted.

If the current PR is stage 1 or stage 2, do not build modules.

## Startup Rules

- Read `AGENTS.md` for shared Codex runtime rules.
- Do not read `CLAUDE.md` or `GEMINI.md` as normal Codex startup context.
- Use Claude, Agy, Hermes, or other collaborators only through project bridge
  routes, not by importing provider-specific startup instructions.
- Use subtree worktrees:

```bash
git worktree add -b codex/b2-rebuild-<scope> .worktrees/dispatch/codex/b2-rebuild-<scope> origin/main
cd .worktrees/dispatch/codex/b2-rebuild-<scope>
test -e .venv || ln -s "$REPO_ROOT/.venv" .venv
```

- Every commit must include `X-Agent: codex/<task>`.

## Lesson Contract

A rebuilt B2 module is a taught lesson, not a reference article.

Reference-article behavior:

- opens with long abstract explanation before the learner does anything;
- piles up correct facts but does not model a decision;
- explains grammar or lexical contrasts only in prose;
- pushes practice into workbook-only activities;
- leaves the lesson tab without rendered activity markers.

Taught-lesson behavior:

- examples appear before compact rules;
- concepts are split into short chunks;
- normal modules contain 4-6 inline lesson activities;
- each inline activity is placed by `<!-- INJECT_ACTIVITY: <id> -->`;
- workbook activities consolidate after lesson practice;
- dense grammar and vocabulary contrasts use tables, grids, or decision rules;
- every major concept includes at least one learner decision, transformation,
  correction, or comparison moment.

## Source Rules

- Plans remain source of truth. Do not edit plans inside a build PR unless a
  preflight remediation PR explicitly scopes that change.
- Treat archived B2 module text as reference-mining material only. Do not copy
  its structure forward.
- Treat old B2 scores as provenance only. Rebuilt modules need fresh
  rebuild-era scoring.
- If source, wiki, or research readiness is missing, stop and record the
  blocker. Do not build around missing evidence.

## Activity Contract

Normal B2 `activities.yaml` uses V2 buckets:

```yaml
version: '1.0'
module: <slug>
level: b2
inline:
  - id: act-1
    type: quiz
    ...
workbook:
  - id: workbook-1
    type: reading
    ...
```

Rules:

- `inline` contains the lesson-tab activities.
- `workbook` contains consolidation practice after the taught lesson.
- Do not wrap activities in an `activities:` key.
- Do not reference workbook-only ids from `INJECT_ACTIVITY` markers.
- Normal modules should have 4-6 inline activities. Fewer than 4 is a hard
  failure; more than 6 needs a clear reason.

Explicit exemption shape:

```yaml
b2_rebuild_contract_exemption:
  reason: "checkpoint module uses workbook-only synthesis"
```

Exemptions must be rare, metadata-scoped, and reasoned. The deterministic gate
reports them as informational findings so reviewers can see them.

## Deterministic Gate Contract

Normal B2 modules must fail deterministic audit when any of these are true:

- `activities.yaml` has no `inline` bucket.
- `inline: []` or fewer than 4 inline activities appears without exemption.
- `module.md` has no `INJECT_ACTIVITY` markers.
- a marker references an activity outside `inline`, including workbook-only ids;
- an inline activity is not injected into the lesson;
- a concept H2 section has more than 900 words before lesson practice;
- a B2 grammar or lexical contrast module has no table, contrast grid, or
  decision-rule block;
- raw callouts such as `[!note]` appear outside accepted blockquote syntax.

The 900-word concept-section threshold is calibrated above the B1 p95
pre-practice span. Do not replace it with a whole-module "words before first
marker" threshold; that false-fails B1-shaped lessons.

## Required Build Rhythm

For each major concept:

1. Give a short Ukrainian example first.
2. Ask the learner to decide, compare, transform, or correct.
3. State the rule compactly.
4. Show a table, grid, or decision rule when forms contrast.
5. Place an inline activity marker before moving into the next dense concept.

Workbook practice may be longer, but it does not substitute for lesson-tab
practice.

## Helper Swarm Policy

Default to solo work for prompt/gate PRs and one-module pilot rebuilds unless a
helper materially reduces risk or wall-clock time.

- Use `gpt-5.4-mini` explorer helpers for bounded source lookup, prompt
  consistency checks, docs/index checks, and simple validation summaries.
- Use `gpt-5.3-codex-spark` worker helpers only for narrow mechanical edits
  with a clearly owned file set.
- The main orchestrator owns planning, integration, final review, PR creation,
  independent-family review routing, merge decisions, and git hygiene.
- Do not let helpers read secrets, source `.envrc`, call `gh`, request reviews,
  open PRs, merge PRs, or revert unrelated changes.
- Record helper roles in PR text; set `swarm_used: true` when any helper or
  reviewer thread did bounded build work. Solo runs still require
  `swarm_used: false`, `swarm_label: none`, and `swarm_note`.
- Use Headroom compression for helper output or logs over 200 lines or 20 KB;
  pass the hash plus a short summary.

## Validation

Adapt module numbers to `curriculum/l2-uk-en/curriculum.yaml`:

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en b2 <module_num>
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/<slug>/vocabulary.yaml
.venv/bin/python scripts/generate_mdx.py l2-uk-en b2 <module_num> --validate
.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/<slug>/module.md
git diff --check
.venv/bin/python scripts/audit/lint_agent_trailer.py
```

Remove generated local cache/status/audit outputs before staging. Do not commit
`curriculum/l2-uk-en/**/status/*.json`, curriculum `audit/*-review.md`,
curriculum `review/*-review.md`, or `data/telemetry/**`.

## Telemetry Workflow

For module-build PRs, persist telemetry through `POST /api/telemetry/module-builds`
and include the same summary in PR text. Required fields include `pr_number`,
`pr_url`, `swarm_used`, `swarm_label`, and `swarm_note`. If no module is built,
state that telemetry is not applicable for the prompt/gate PR.

## Independent-Family Review Gate

Before merge, request read-only independent-family review. Prefer Claude Opus 4.8
through the project bridge when available; otherwise use an approved
non-Codex route such as Gemini 3.1 Pro High through Agy. Include PR diff,
validation summary, artifact-clean statement, and blocker-only instructions.
Record reviewer identity, review model, review scope, unresolved findings, and
final disposition in PR text. Merge rule: unresolved findings are blockers.

## PR Body Requirements

For rebuild PRs, include:

- stage and scope;
- modules rebuilt or statement that no modules were built;
- files changed;
- validation commands and outcomes;
- telemetry summary when module build telemetry applies;
- `swarm_used`, `swarm_label`, and `swarm_note`;
- independent review identity, model, scope, and final disposition;
- unresolved review findings count;
- forbidden artifacts included: no.
