---
title: "Learner Runtime And Build Split"
status: DRAFT
date: 2026-05-31
owner: Codex / orchestrator
scope: A1-C2 learner app, Starlight preview, Word Atlas, etymology build isolation
---

# Learner Runtime And Build Split

## Why This Exists

The A1 M1 rewrite showed that the product direction is a modern static-first
educational application: textbook-quality lesson content, workbook practice,
vocabulary, resources, and as much interaction as GitHub Pages can support.
Backend/AI personalization can come later, but the first public version must be
usable as static hosting for self-study, teacher-led study, and classroom use.

The current Starlight build is too coupled for that workflow. A single lesson
change rebuilds the ESUM etymology dynamic route set, producing roughly 38k
pages. That is useful for a full reference deploy, but it is the wrong default
for daily lesson writing.

## Product Decisions From A1 M1

- M1 is not a universal golden lesson. It is the quality bar for the
  `A1-zero-script-onboarding` archetype.
- A1/A2 need multiple archetypes because the learner state changes quickly:
  zero-script, script-building, survival dialogue, grammar first contact, and
  later A1/A2 expansion.
- B1+ core modules and each seminar track need their own archetypes.
- ULP / Anna Ohoiko-style ramped immersion remains the guiding approach.
  English leads early A1; Ukrainian increases only as the learner state can
  support it.
- The durable tab surface is `Lesson`, `Workbook`, `Vocabulary`, `Resources`.
  The internals of those tabs vary by archetype and track.
- Required resources should appear at the point of use inside the lesson or
  workbook, and also be listed canonically in the `Resources` tab.
- The internal wiki is AI-facing. Do not link unpublished wiki pages from
  student-facing lessons. A human-facing wiki can be a later product if it has
  a clear learner or teacher use case.

## Build Split

Normal author iteration should build the learner surface only:

```bash
npm run build:starlight
```

Full reference/deploy builds should opt into the ESUM route set:

```bash
npm run build:starlight:full
```

Implementation detail: `starlight/src/pages/etymology/[slug].astro` emits
dynamic pages only when `BUILD_ETYMOLOGY_ROUTES=1` is set. The GitHub Pages
deploy workflow uses the full build; local lesson builds and frontend CI use
the fast default.

## Service Wrapper

Run the Starlight preview through `services.sh` from the worktree being
previewed:

```bash
./services.sh restart starlight
./services.sh status
```

The wrapper binds Starlight to `127.0.0.1:4321` and tracks the listener for the
current worktree. In Codex desktop, Starlight is launched inside a detached
`tmux` session so the dev server survives the shell command that started it.

## Next Infra Work

1. Define a module archetype contract: learner state, prerequisites, allowed
   tab composition, allowed activity families, resource-placement policy, and
   acceptance tests.
2. Make the writer pipeline consume plan + config + resources + learner state
   as one contract before drafting.
3. Add deterministic gates for "introduced before use", plan coverage,
   resource coverage, activity type validity, and archetype fit.
4. Evaluate the POC shell in `docs/poc/` as the future learner runtime. Keep
   Starlight as a preview/docs/reference renderer until the custom shell is
   ready.
5. Keep Word Atlas / etymology as a separate product surface. Lessons should
   cross-link to it rather than duplicating etymology or morphology inline.
