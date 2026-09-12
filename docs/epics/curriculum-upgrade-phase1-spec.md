# Curriculum upgrade Phase 1 — V7 machinery (#7994)

Status: implemented machinery; acceptance remains open for the immersion decision
in [RESIDUAL.md](../../RESIDUAL.md). This is one PR, not curriculum publication.

## Frozen outcome and denominator

A driver upgrades the existing `a1/things-have-gender` artifacts through V7 into
parallel `a1-v2` lesson artifacts and a module landing plus three lesson pages,
each with four tabs. The original A1 and all plans remain unchanged.

- Operator dispatch and #7994 Phase 1 decisions, 2026-09-12: Option A, parallel
  level, preserve-and-expand, no named narrator, marked attributed quotation,
  deterministic stress after review, Gemini/AGY or Codex writers later.
- Held-out Phase 0: `0801b58beece2b2b6380327fb24fd0e3ff129dd5` on
  `agy/cu-p0-pilot-writer-things-have-gender` (#7991).
- Original four artifacts: `7829e74b6031cdcc4ef69895b5f42e0643569e44`;
  the runtime reads the existing worktree artifacts and records every input hash.
- Approved design SHA-256:
  `935c9b632b89b0b4bc3dd124bced27743a93b3dba7a924b8ece5ff28d01a91b6`.
- `tests/fixtures/curriculum_upgrade/gold.json` records pinned commits and every
  fixture SHA-256. Fixtures are test data, never copied to product paths by a build.

Non-goals: merge/deploy; publish the preview as live A1; archive/rename A1; edit
original module or plans; edit agent skills; new pipeline or pedagogy; run live
writers in this PR. Driver Grok owns independent non-OpenAI exact-head review and
merge disposition. Codex owns this implementation, integration and verification.

## CLI and phase sequence

Run from a dispatch worktree with the shared interpreter:

```sh
/home/ops/learn-ukrainian/.venv/bin/python scripts/build/v7_build.py a1 things-have-gender --upgrade --dry-run
/home/ops/learn-ukrainian/.venv/bin/python scripts/build/v7_build.py a1 things-have-gender --upgrade --writer gemini-tools --worktree
/home/ops/learn-ukrainian/.venv/bin/python scripts/build/v7_build.py a1 things-have-gender --upgrade --writer codex-tools --worktree
/home/ops/learn-ukrainian/.venv/bin/python -m scripts.build.verify_shippable a1-v2 things-have-gender --lesson
```

Only the first command is authorized for live execution in this PR. Existing
`--out`, `--telemetry-out`, `--writer-timeout`, `--effort`, `--no-resume` and
`--keep-worktree` apply. `--lesson-map PATH` supplies reviewed titles, proper names
and bounded unverified declarations; ownership, provenance, closure and exemptions
must still match fresh deterministic derivation. Targets may only increase. `--upgrade` accepts base A1 only and rejects
`--use-generator`. Output defaults to `curriculum/l2-uk-en/a1-v2/{slug}/`.
Custom `--out` must remain in the build worktree and cannot overlap original A1
or plans. Custom output MDX is under `--out/mdx`; default MDX is under
`site/src/content/docs/a1-v2/{slug}/`.

1. Read existing plan and four module artifacts; record SHA-256 inputs.
2. Deterministically derive and validate `lessons.yaml`; save full rendered
   `writer_prompt.md`. Dry-run exits 0 here, with `mode=upgrade` JSONL events and
   `writer_invoked=false`; no model, wiki retrieval, or annotation runs.
3. Invoke the existing V7 writer backend once per lesson with the upgrade template,
   originals, read-only map, and cumulative learner state. Parse strict JSON
   structured artifacts using the Phase 0 placement shape. Resume writer artifacts
   only when a receipt binds the exact scoped prompt and raw response hashes; `--no-resume` reruns the writer.
4. Existing independent V7 review dimensions run per lesson, then across the module
   for coherence. Review context explicitly covers the split and closure.
5. Run `stress_annotator.annotate_file` on all four artifacts, after review.
6. Assemble landing and lesson MDX as drafts; run complete lesson gates and each page's Node
   render gate. Any failed gate stops with exit 1 and a diagnostic artifact. Only after gates pass
   are the pages marked publishable; failed pages stay drafts.

Upgrade skips knowledge/wiki packet, wiki manifest/completeness/coverage phases,
plan writing, and fresh-from-scratch authoring. It retains V7 transports, strict
artifact parsing, reviews, stress annotator, component renderer and worktree
artifact persistence. Ordinary V7 builds keep their single-module path.

## Slices and schemas

| Slice | Implementation | Contract |
|---|---|---|
| (a) Manifest/config | `curriculum.yaml`, `scripts/level_config.py`, config resolvers, site content collection | Explicit `base_level: a1`; one selected preview module; A1 activities/personas/audit/immersion |
| (b) Map | `scripts/build/lesson_map.py`, `schemas/lesson-map.schema.json` | Ordered deterministic section ownership, introduction to lesson 1, final closure, every original activity recorded |
| (c) Writer | `v7_build.py`, `linear_pipeline.py`, `phases/linear-write-upgrade.md` | Existing transports, preserved originals, real scoped prompt and dry-run |
| (d) Gates | `lesson_gates.py`, `verify_shippable.py`, ported pilot checker | Phase 0 preservation/activity/vocab/stress/render checks plus current V7 immersion gates; unresolved exposure conflict remains blocking |
| (e) Assembly | `lesson_assembler.py`, activity renderer, `LevelLanding.tsx`, site route | Four tabs, complete real activity components, dialogues, landing unions, cumulative vocabulary, lesson navigation and counters |
| (f) Docs | This spec, lesson contract v4, presentation and design notes, decision record | Published lesson unit and already-approved boundaries |

`lessons.yaml`: top-level `lessons`, `closes_module`, `provenance`,
`items_min_exempt`, `proper_names`. Each lesson has `n`, `title`, `sections`,
`minutes: 60`, `word_target >= 550`, activities `{total >= 10, inline: [4,6],
workbook: [6,9]}`, `unverified_stress` (at most 10), `unverified_lemmas` (at most 5).
Only the final lesson closes the module. Intro ownership is implicit lesson 1.

Derivation packs non-final outline sections in order to the 550-word planning
minimum, reserves the final outline section for closure, and attaches unplanned
source headings to the preceding planned section. For this denominator the result
is gold's two/one/two section split. Inline provenance follows exact source markers.
Workbook originals without ownership metadata retain order and are distributed
proportionally; this is deterministic initial placement, not semantic attribution.
Coherence review must verify placement. Existing IDs survive; id-less workbook
originals get `act-w1` onward. Short original activities receive declared exemptions;
new activities cannot inherit an exemption.

Artifacts are `lesson-{n}/{module.md,activities.yaml,vocabulary.yaml,resources.yaml}`.
Activities use explicit `inline` and `workbook` arrays. Vocabulary is allocated once
across source lessons; the published vocabulary tab accumulates earlier entries.
Each resource needs title and URL, chunk ID or source. Input originals never change.
Reports/prompts/telemetry are local build artifacts and are not product curriculum.

## Held-out evaluation and completion

Routing card `acceptance_cmd` (cwd is the assigned dispatch worktree):

```sh
/home/ops/learn-ukrainian/.venv/bin/python -m pytest tests/build/test_lesson_map.py tests/build/test_lesson_assembler.py tests/build/test_lesson_gates.py tests/build/test_v7_upgrade.py -q
```

- [x] Deriver matches pinned gold section lists, intro owner, closure and provenance.
- [x] Fixture assembler emits landing and three pages with preserved paragraphs,
  complete activities, vocabulary union and resource coverage.
- [x] CLI dry-run loads originals, derives map, saves real prompt, emits upgrade
  events and stops before model calls; both writer routes tested with fixture responses.
- [x] Offline adversarial tests reject missing originals, altered answers, missing
  oracle, render loss, and incorrect stress positions.
- [ ] Resolve the existing module-level dialogue exposure floor for lesson mode;
  the explicit held-out test records the current blocking rejection.
- [ ] Full site Astro/Playwright CI proof on the produced lesson pages. The isolated
  real-component build/browser proof is reproducible with
  `node tests/build/upgrade_browser_check.mjs batch_state/cu-p1-gold/assembled`.
- [ ] Driver routes exact-head cross-family review; required CI passes.

Done requires all six slices, successful acceptance command and affected checks,
empty protected-tree diff against `origin/main`, a pushed conventional commit with
X-Agent trailer, and a PR linked to #7994. A draft with an unchecked in-scope residual
is not Phase 1 completion. No threshold changes, silent skips, or manual fixture
publication can close the gap. New architecture/policy decisions stop the affected
slice and name the operator/advisor decision and driver owner in `RESIDUAL.md`.
