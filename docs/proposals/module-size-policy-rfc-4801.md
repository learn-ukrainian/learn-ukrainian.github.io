# RFC 4801: Dossier-Led Module Size Policy

Status: Partially implemented
Issue: #4801
Owner: Codex orchestrator
Date: 2026-07-12

## Purpose

Module length should be justified by evidence and pedagogy, not by asking a
writer to inflate prose until a fixed multiplier is reached.

The governing rule is:

> The accepted evidence packet and learning work determine the range; the plan
> records the reviewed minimum; pedagogy determines the shape.

The original measure-only audit remains advisory. Reviewed per-plan overrides
now feed audit reporting and the writer-facing size-policy object, but they do
not create a hard ceiling or change `scripts/audit/config.py`. This rollout
touches only plans already undergoing accepted rebuild work; it does not bulk
change released modules or promote the advisory ranges into audit gates.

## Decision

Adopt the dossier-led principle, but with safeguards:

1. Keep plan `word_target` as the current floor until a plan review explicitly
   changes it.
2. Use source density to set an advisory ceiling, not a hard pass/fail gate.
3. Require source-saturation evidence before calling a seminar dossier genuinely
   sparse.
4. Normalize density by track. A short BIO dossier and a short FOLK dossier do
   not mean the same thing.
5. Treat C1-C2 core as research/evidence-packet led, not seminar-dossier led.
6. Do not apply the new policy retroactively to released A1-B2 content.

## Size Bands

Seminar bands:

| Band | Advisory range | Use when |
| --- | ---: | --- |
| Sparse | 3800-5000 | Sources give basic facts, limited reception, little controversy. Requires source-saturation evidence before lowering a plan. |
| Normal | 5000-6500 | Dossier supports a full seminar lesson with factual, interpretive, and pedagogical material. |
| Dense | 6500-8000 | Dossier has rich chronology, multiple sources, reception history, controversy, political/cultural context, and primary material. |
| Exceptional | 8000+ | Only with explicit justification. Compression would harm the learning goal. |

Core C1-C2 bands:

| Band | Advisory range | Use when |
| --- | ---: | --- |
| Core pedagogy standard | 3500-5000 | Grammar, skills, style, or workshop modules where practice and learner state drive the shape. |
| Core research extended | 4500-6500 | Content-heavy core modules with a real evidence packet: references, primary examples, corpus work, textbook grounding, or source-comparison tasks. |

The bands are intentionally advisory baselines. They are designed to reveal
pressure points and never replace the content-derived review of an individual
module.

## Algorithm

For each module plan:

1. Read the plan floor from `word_target`.
2. Read the plan outline budget from `content_outline[].words` when present.
3. Resolve the research packet:
   - seminar tracks: dossier reference in `references[]`, then
     `docs/research/{track}/{slug}.md`, then legacy
     `curriculum/l2-uk-en/{track}/research/`;
   - C1-C2 core: plan references, primary sources in outline sections, and
     source-heavy tasks act as the evidence packet.
4. Count deterministic density signals:
   - dossier words;
   - source references, including URLs, markdown links, corpus chunk IDs,
     `verify_quote` ledgers, source-signal lines, and named edition markers;
   - heading count;
   - primary/corpus/quote markers;
   - contested/decolonization markers;
   - variant/ritual/performance/regional markers.
5. Classify density with track-normalized thresholds.
6. Set `effective_min = plan.word_target`.
7. Set `advisory_ceiling = max(plan.word_target, band.max)` when a band has a
   numeric ceiling.
8. Report advisory status:
   - `advisory_ok`;
   - `missing_dossier`;
   - `missing_plan_word_target`;
   - `plan_review_needed`;
   - `below_plan_floor`;
   - `over_advisory_ceiling`;
   - `exceptional_justification_required`.

This avoids the bad failure mode where a sparse dossier makes a writer invent
depth. It also avoids the opposite failure mode where a plan can be silently
shrunk without review.

## Seminar Setup

The immediate calibration set is:

- 5 built BIO modules;
- 40 built FOLK modules;
- all available BIO and FOLK plans/dossiers for unbuilt pressure checks.

FOLK needs a special safeguard. `docs/folk-epic/folk-dossier-schema.md` already
says folk dossiers are the sole knowledge layer and that thin dossiers are
usually a writer failure, not a corpus gap. Therefore a sparse FOLK result is
not permission to build short by default. It is a signal to either prove source
saturation or improve the dossier.

BIO is different. Some figures are genuinely documented by compact reference
material, while others have rich conflict, reception, or primary-source depth.
Each BIO module therefore receives its own reviewed range after the available
evidence, learning work, and non-repetitive section map are established. No BIO
track-wide range is a quota or default minimum.

## Core C1-C2

Core modules have research, but the research object is not always a seminar
dossier. For C1-C2 the evidence packet may include:

- State Standard requirements;
- textbook or RAG grounding;
- corpus examples;
- source-comparison tasks;
- genre/register models;
- primary examples in the outline.

So C1-C2 should inherit the anti-bloat rule as:

> Never expand explanation beyond the learner-state and evidence packet.

The core rule should reduce redundant explanation, not cap practice. If a C2
professional module needs more tasks, models, and source-comparison scaffolding,
that is pedagogical density. If it only repeats explanation to reach 5000 words,
that is bloat.

## Config And Prompt Migration

Do not solve this by changing scalar numbers in `scripts/audit/config.py`.

The current scalar model should migrate toward an effective size policy:

```yaml
size_policy:
  floor_words: 5000
  recommended_range: [5000, 6500]
  ceiling_words: 6500
  basis: research_dossier
  saturation_evidence: required_when_sparse
  exceptional_justification: required_above_ceiling
```

For a reviewed per-plan override, `word_target` remains the deterministic
minimum and must equal `floor_words`. The recommended range describes the
intended landing zone; `ceiling_words` is an advisory anti-padding boundary,
not a second minimum. A module above that ceiling needs explicit source and
pedagogical justification. Every override must record a nonempty review basis
and saturation evidence; malformed or partial overrides do not bypass the
track configuration floor.

The override schema is deliberately track-generic: evidence-led review can
occur during a scoped rebuild on any track, and the validator should not encode
a second track allowlist. Generic support is not blanket permission to lower a
track target. The plan must opt in with a complete reviewed policy, the floor
must still equal `word_target`, and invalid overrides block automatic expansion.
Released A1-B2 plans remain untouched unless a separately reviewed rebuild puts
that plan in scope.

Expected later consumers:

- writer prompt placeholders;
- expansion retry logic;
- plan review;
- content review;
- deterministic audit reporting;
- eventual build metadata.

Known behavior surfaces to revisit later:

- `scripts/common/thresholds.py` exposes `LevelThresholds.target_words` and
  documents the value as the minimum total words per module;
- `scripts/audit/config.py` mirrors target-word values for audit-side gates and
  variant overrides;
- `scripts/audit/gates.py` treats word count as a floor with warning bands and
  soft caps;
- `scripts/config.py` encodes the B1+ `OVERSHOOT_FACTOR` / `get_overshoot_factor()`
  multiplier;
- `scripts/pipeline/core.py` injects `WORD_CEILING = word_target * 1.5` and B1+
  overshoot rules into prompt placeholders;
- `scripts/audit/review_plan.py` checks outline section budgets against
  `word_target`;
- `scripts/build/phases/v6-write.md`, `scripts/build/phases/linear-write.md`,
  and `agents_extensions/shared/phases/gemini/*.md` contain hard minimum,
  section-budget, overshoot, and 150% maximum language;
- `agents_extensions/shared/skills/plan-review/plan-review-prompt.md` and
  `agents_extensions/shared/skills/plan-review-seminar/plan-review-seminar-prompt.md`
  encode fixed target tables and section-budget checks;
- `agents_extensions/shared/rules/`, `agents_extensions/shared/agents/`, and
  `agents_extensions/shared/memory/` restate target minimum and overshoot rules;
- seminar plan-review prompts contain FOLK target drift between 4000 and 5000;
- docs such as `docs/best-practices/context-engineering.md`,
  `docs/best-practices/audit-standards.md`,
  `docs/design/dimensional-review.md`,
  `docs/agent-channels/pipeline/context.md`, and
  `docs/best-practices/wiki-plan-review-and-lock.md` still encode the old
  fixed-floor framing.

Those are intentionally not changed in this Phase 1 PR.

## Released Content Policy

Do not bulk-touch released A1-B2 content for this policy.

Touch released content only when:

1. it is already in a rebuild or correction scope;
2. a review identifies concrete bloat or quality regression;
3. a future advisory gate flags it and a human/track owner accepts the rewrite.

For existing BIO/FOLK modules, use the report for calibration and triage. Do
not rewrite modules just because the advisory band changes.

## Rollout Plan

1. Phase 1: RFC plus measure-only command. Complete; no hard enforcement.
2. Phase 2: run the report over BIO/FOLK and unbuilt C1-C2 candidates; post
   calibration summary to #4801. In progress.
3. Phase 3: add advisory `size_policy` metadata to new/rebuilt plans only.
   Implemented for reviewed exemplars, beginning with Bilash.
4. Phase 4: let the writer-facing policy consume valid reviewed overrides and
   block malformed overrides. Implemented at the policy-object layer; broader
   prompt migration remains pending.
5. Phase 5: promote selected advisory statuses into gates only after exemplar
   modules validate the thresholds. Not started.

## Measurement Command

Run the advisory report:

```bash
.venv/bin/python scripts/audit/module_size_policy_audit.py --tracks bio folk --built-only
```

JSON output:

```bash
.venv/bin/python scripts/audit/module_size_policy_audit.py --tracks bio folk --built-only --format json
```

The command writes no files and returns success even when it reports
`plan_review_needed` or `over_advisory_ceiling`. That is deliberate in Phase 1.

## Model Consultation Summary

Claude Opus 4.8 xhigh and Gemini 3.1 Pro High were consulted before this RFC.
The final policy follows their shared pressure on two points:

- avoid a raw dossier-word-count multiplier;
- require evidence and pedagogical justification before expanding or shrinking.

The adopted deviation is that sparse dossiers do not automatically permit
shorter modules. Sparse must be earned through source-saturation evidence,
especially for FOLK.
