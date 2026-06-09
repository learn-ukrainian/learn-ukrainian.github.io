# Folk-experiential TEXT layer — implementation spec

> **Decision (user, 2026-06-10):** Build the TEXT-achievable folk-experiential surfaces now;
> defer audio-block + symbolic-decode + aural-genre-ID until folk audio is ingested and SigLIP
> `search_images` is wired for l2-uk-en. Origin of gap: the `folk-experiential` archetype SPEC
> exists in `scripts/pipeline/module_archetypes.py:226` but **no schema/parser/converter/component
> implements it**, so V7 builds emit a generic seminar module. POC design SSOT:
> `docs/poc/poc-folk-lesson-design.html` (worked example = koliadky-shchedrivky).

## Scope — 6 text surfaces to implement (3 audio/image surfaces DEFERRED)

| # | Surface | Kind | POC anchor | Build now? |
|---|---|---|---|---|
| 1 | **myth-box** (decolonization claim→truth) | content block | `.myth-box` (poc L74-77, L204-207) | ✅ |
| 2 | **high-culture-bridge** (folk→opera/lit/art flow) | content block | `.bridge-box` (poc L88-93, L211-214) | ✅ |
| 3 | **ritual-sequencing** (#42, order the rite steps) | activity | `.ritual-timeline`/badge-ritual (poc L96-98) | ✅ |
| 4 | **variant-comparison** (#43, compare regional variants) | activity | badge-variant / table.cmp (poc L108,L116) | ✅ |
| 5 | **motif-formula** (#44, identify recurring formula/motif) | activity | badge-motif / .mt-passage (poc L109,L121-122) | ✅ |
| 6 | **performance** (#45, perform/record a fragment) | activity | badge-perform / .rec-btn (poc L109,L123) | ✅ |
| — | audio-block (#1), symbolic-decode (#2), aural-genre-ID (#40) | — | poc L57-67,L79-86 | ❌ DEFERRED (no audio corpus; SigLIP deferred) |

## Implementation map — each ACTIVITY type touches 4 layers (clone the templates)

Clone templates that already span all 4 layers: **`comparative-study`** and **`highlight-morphemes`**.

1. **Registry** — `scripts/build/linear_pipeline.py` `_ACTIVITY_ITEM_AUTHORING_FIELDS` (~L7352-7381):
   add `"ritual-sequencing": _activity(...)`, `"variant-comparison": _activity(...)`,
   `"motif-formula": _activity(...)`, `"performance": _activity(...)` with their authoring fields.
2. **Parser** — `scripts/yaml_activities.py`: add a dataclass per type (model on `ComparativeStudyData`
   L345 / item dataclasses). Wire into the parser dispatch + `__init__.py` exports.
3. **MDX converter** — `scripts/generate_mdx/converters.py`: add `<type>_to_jsx` (model on
   `comparative_study_to_jsx` L179 / `highlight_morphemes_to_jsx` L136). Register in
   `scripts/generate_mdx/__init__.py`.
4. **Component** — `starlight/src/components/<Name>.tsx` (model on `ComparativeStudy.tsx`,
   `HighlightMorphemes.tsx`). Visual design per the POC badges/blocks above.

## CONTENT components (myth-box, high-culture-bridge) — emitted by the writer in module.md

These are not activities; they're rendered blocks inside the lesson prose. Two viable renderings —
the implementer picks the one consistent with how existing seminar content blocks render:
- **(preferred) custom MDX component** `<MythBox claim=… truth=… cite=…/>`, `<HighCultureBridge nodes=[…]/>`
  with a `.tsx` component + a converter that turns a structured writer block into the JSX; OR
- Starlight asides (`:::danger`/`:::tip`) if a custom component is disproportionate. The POC uses
  distinct styled boxes (claim in red, truth in green for myth-box; node→arrow→node flow for bridge),
  so the custom component matches the design better.
The writer emits them via a structured marker the assembler converts (mirror how `highlight-morphemes`
flows writer YAML → converter → component).

## WRITER ENFORCEMENT (the part that makes builds actually USE the layer)

Today the `folk-experiential` archetype text in `module_archetypes.py` is descriptive but the writer
falls back to generic activities because the schema didn't accept the folk types. After the types exist:
- Update the writer prompt / archetype injection so a FOLK build MUST include: ≥1 myth-box, ≥1
  high-culture-bridge, and folk activity families #42-#45 in place of generic seminar tasks (where the
  dossier supports them). Audio/symbolic surfaces remain optional/omitted until source material exists.
- Consider a soft build check (advisory, not a hard gate yet) that a folk module contains ≥1 myth-box +
  ≥1 bridge + ≥1 folk-family activity — so a regression back to generic content is visible.

## Dispatch plan
- **Dispatch A (rendering layer):** the 4 folk ACTIVITY types across all 4 layers + the 2 CONTENT
  components + tests (parser round-trip + converter snapshot + a fixture module that exercises each).
  No writer change yet — provable in isolation.
- **Dispatch B (writer enforcement):** archetype/writer-prompt update so folk builds emit the layer,
  + the advisory presence check. Then rebuild the 3 modules and verify against the POC (all 4 tabs,
  myth-box, bridge, folk-family activities present; UK tab labels; no stress; P2 cross-refs).

## Verify-before-promote (folk addendum to the §4 10-check list)
A folk module is design-conformant only if the rendered MDX shows: ≥1 myth-box (claim→truth), ≥1
high-culture-bridge, ≥1 ritual-sequencing/variant/motif/performance activity, the 4 UK-labelled tabs,
and rich Урок prose. Audio-block + symbolic-decode are EXPECTED-ABSENT until their corpora land
(note their absence explicitly; do not silently treat the module as fully POC-complete).
