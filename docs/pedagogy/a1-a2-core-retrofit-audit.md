# A1/A2 Core Retrofit Audit Protocol

> Scope: a compact pre-rewrite protocol for A1/A2 core retrofit slices. Use
> this before editing plans, wikis, modules, activities, vocabulary, resources,
> prompts, or review rubrics.

## Purpose

A retrofit audit decides what needs repair before any rewrite starts. It is not
a lesson rebuild, research dossier, source-ingestion pass, or generated review
artifact.

Use this protocol with:

- `docs/pedagogy/a1-a2-lesson-construction.md`;
- `docs/pedagogy/commercial-source-policy.md`;
- `docs/pedagogy/a1-a2-retrofit-template.md`.

The audit must produce a short slice report that can guide later plan, wiki,
or module work without burying the task in seminar-scale research.

## Ground Rules

- Audit first; rewrite second.
- Keep the slice coherent, usually a unit, module range, or dependency chain.
- Preserve the source-of-truth hierarchy: State Standard, accepted decisions,
  immutable plan intent, wiki teaching packet, then generated lesson artifacts.
- Use Ukrainian-first immersion as the target, with controlled English only
  where it prevents beginner confusion.
- Do not ingest, copy, summarize, quote, store, extract, embed, or derive from
  paid or all-rights-reserved learning materials.
- Do not add screenshots, transcripts, audio, images, PDFs, extracted text,
  local private paths, or media files.
- Keep the evidence packet compact: bullets only, about 500 words by default,
  and skip non-applicable items.

## Slice Flow

1. Inventory source files.
   Record only paths and current state for the relevant plans, wiki packets,
   module markdown, activities, vocabulary, resources, and prompt/review
   guidance. Do not regenerate anything.
2. Capture learner state.
   Note prior vocabulary, prior grammar, expected script knowledge, stress
   support, listening readiness, and known review obligations from nearby
   modules.
3. Check teaching readiness.
   Compare the slice to the A1/A2 lesson-construction standard: Ukrainian-first
   artifacts, controlled English, narrow grammar load, recognition before
   production, lawful visual/audio support, pronunciation and reading support,
   cursive recognition before production, review cadence, cognitive load, and
   native Ukrainian teacher feedback opportunities.
4. Ground language-risk claims.
   Do not rely on memory for Ukrainian forms, Russian-interference traps, or
   common L2 errors. Use available project tools such as
   `mcp__sources__verify_word`, `mcp__sources__verify_words`,
   `mcp__sources__search_sources`, `mcp__sources__search_text`,
   `mcp__sources__search_style_guide`, `mcp__sources__check_russian_shadow`,
   `mcp__sources__search_ua_gec_errors`, `mcp__sources__query_r2u`,
   `mcp__sources__query_grac`, and `mcp__sources__query_cefr_level`. If a
   claim cannot be grounded, mark it `VERIFY` or omit it.
5. Classify debt.
   Assign each finding to one debt class below, with the smallest layer that
   can fix it. Do not patch generated lesson prose around a bad plan or thin
   wiki.
6. Decide rewrite readiness.
   End with one of: `ready for plan repair`, `ready for wiki repair`, `ready
   for module rebuild`, `needs prompt/pipeline repair first`, or `blocked by
   unresolved source/IP question`.

## Debt Classes

| Class | Use When | Repair Target |
| --- | --- | --- |
| Plan debt | Scope, grammar sequence, vocabulary intent, level boundary, or review cadence is wrong in source-of-truth planning. | `curriculum/l2-uk-en/plans/{level}/` |
| Wiki debt | Plan is sound but the teaching packet lacks sequence steps, examples, L2 errors, visual/audio/cursive affordances, or recognition-to-production path. | wiki/orchestration teaching packet |
| Module/activity debt | Source inputs are strong but the built lesson, activities, vocabulary, or resources fail the standard. | lesson artifacts after source repair |
| Vocabulary/resource debt | Target words, frequency, stress, lawful media, attribution, or resource roles are missing or unsafe. | vocabulary/resources source and generated files |
| Pipeline/review debt | Prompt, rule, audit, or reviewer guidance would keep reproducing the defect across modules. | scripts/build rules, prompts, or review rubrics |
| IP/media debt | Any proposed source, image, audio, video, transcript, or path violates commercial-source or licensing rules. | remove, replace, or block before rewrite |

## Slice Report Shape

Use this report shape in issue comments, handoffs, or planning docs:

```markdown
# A1/A2 Retrofit Audit: <slice>

## Verdict
- Status: ready for plan repair / ready for wiki repair / ready for module rebuild / blocked
- Smallest safe rewrite layer:
- Main risk:

## Evidence Packet
- See: docs/pedagogy/a1-a2-retrofit-template.md

## Debt Summary
| Finding | Class | Evidence | Repair target | Priority |
| --- | --- | --- | --- | --- |
| ... | plan/wiki/module/pipeline/IP | path + short note | file/layer | high/medium/low |

## Acceptance Checks Before Rewrite
- [ ] Audit happened before rewriting.
- [ ] Findings are classified by debt layer.
- [ ] Ukrainian-first immersion, controlled English, multimodal support,
      pronunciation/reading, cursive recognition, review cadence, cognitive
      load, and teacher-feedback needs are checked.
- [ ] Language-risk claims are tool-grounded or marked `VERIFY`.
- [ ] Lawful media/IP status is clear.
- [ ] No lesson regeneration happened in the audit slice.
```

## Native Teacher Criterion

Every A1/A2 retrofit audit must ask where native Ukrainian teacher, tutor, or
conversation feedback would materially improve the learner's outcome. This is
not a mandatory external approval gate before rewriting, but it is a first-class
teaching criterion.

Record opportunities for:

- pronunciation, stress, rhythm, and listening correction;
- short guided speaking or writing feedback;
- conversation practice using the module's controlled language;
- cultural or pragmatic feedback that static self-study cannot provide.

Frame these opportunities as better pedagogy for learners and as respectful
support for Ukrainian educators.
