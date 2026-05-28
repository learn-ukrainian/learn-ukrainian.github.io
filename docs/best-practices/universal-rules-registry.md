# Universal Rules Registry (V7.2)

This doc describes the universal-rules registry that lives at
`scripts/build/universal_rules/`. The registry is the single source of truth
for the universal layer of the wiki-driven prompt generator described in
[`docs/decisions/pending/2026-05-28-wiki-driven-prompt-generator.md`](../decisions/pending/2026-05-28-wiki-driven-prompt-generator.md).

> **Status (2026-05-28):** Step 4 — registry + loader scaffold only. Generator
> wiring (Step 5) and reviewer single-source emission (Step 6) are separate
> follow-ups. The legacy `scripts/build/phases/linear-write.md` template
> remains the active writer prompt during the migration; the registry runs
> parallel to it until the generator is wired.

## Why a registry

Today's writer prompt (`linear-write.md`) carries ~15 `#R-*` rules inline.
Reviewer prompts (`linear-review-dim.md`) and gate parsers re-state the same
rules in different words. Three hand-maintained descriptions of the same
contract drift apart with every prompt iteration. The wiki-driven generator
ADR resolves this by composing prompts from a registry at build time so the
writer prompt, reviewer prompt, and gate parser all read from one place.

The registry layer is the *universal* one — invariants and level/track
predicates that apply across modules. Lesson-specific content (vocabulary
domain, decolonization contrast pair, sequence steps) stays in the wiki.
RAG payloads (chunk text, citations) stay attached to `plan.references`.

## Fragment shape

Every fragment is an `R-<NAME>.md` file with YAML frontmatter followed by
markdown body. Filenames omit the `#` because the filesystem can't carry it;
the `Rule.telemetry_id` accessor restores the `#` prefix for compatibility
with the pipeline's existing telemetry keys (`#R-VESUM-ALL-WORDS`, etc.).

```yaml
---
id: R-VESUM-ALL-WORDS
description: Verify every Cyrillic word form in artifacts via mcp__sources__verify_words.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: []
---

Body markdown (rule semantics, examples, forbidden patterns). The body is
pasted verbatim into the rendered prompt by the generator (Step 5).
```

### Required frontmatter fields

| Field | Type | Notes |
|---|---|---|
| `id` | string | Must start with `R-` (no `#` prefix). Matches the filename stem. |
| `description` | string | One-line summary used in error messages and registry listings. |
| `applies_to.levels` | list[str] | Subset of `{a1, a2, b1, b2, c1, c2, all}`. Use `[all]` for universal rules. |
| `applies_to.tracks` | list[str] | Subset of `{core, seminar, all}`. |
| `applies_to.activity_profiles` | list[str] | Free-form list; use `[all]` until Step 5 introduces profile taxonomies. |
| `slot` | string | One of `writer.preamble`, `writer.body`, `reviewer.rubric`, `shared.contract` (see below). |
| `depends_on` | list[str] | Other rule ids (no `#` prefix) that must appear before this one. |

### Slots

| Slot | Generator behavior |
|---|---|
| `writer.preamble` | Emitted into the *opening* of the writer prompt (charter / voice / audience framing). |
| `writer.body` | Emitted into the writer prompt's protocol body (detailed authoring rules). |
| `reviewer.rubric` | Emitted into the reviewer prompt as rubric criteria (deterministic-side checks composed alongside subjective dims). |
| `shared.contract` | Emitted to **both** the writer and reviewer prompts. Use for rules where the writer is asked to do X and the reviewer is asked to verify X — single-source eliminates drift between the two surfaces. |

A rule has exactly one slot. A rule that semantically applies to both
prompts uses `shared.contract`; the generator (Step 5) is responsible for
emitting `shared.contract` fragments into both rendered prompts.

### Ordering

Within a rendered prompt, the generator concatenates rules in
topologically-sorted order over `depends_on`. Tie-break is filename
alphabetical (= the order `load_all_rules` returns by default). The
topological sort validates that every `depends_on` id exists in the *full*
registry (not just the filtered subset), so removing a rule that other
rules depend on still surfaces as `MissingDependencyError` before the
prompt is rendered.

## Loader API

`scripts/build/universal_rules_registry.py` exposes:

- `load_all_rules(directory=None) -> list[Rule]` — discovery + parsing.
  Returns rules in filename-alphabetical order. Each invocation re-reads
  the filesystem; callers that need caching wrap their own.
- `load_applicable_rules(level, track, activity_profile, slot=None, directory=None) -> list[Rule]` —
  filters by predicates and sorts topologically. Pass `slot=None` to load
  every slot.
- `get_rule(rule_id, directory=None) -> Rule` — single-rule fetch by id.
- `Rule` dataclass with frozen fields and a `telemetry_id` property that
  prepends `#` to match the pipeline's existing `rule_id` telemetry shape.

Errors:

- `MalformedFragmentError` — missing frontmatter, unknown slot, bad
  `applies_to` shape, etc. Raised eagerly on `load_all_rules`.
- `MissingDependencyError` — `depends_on` names a rule that does not
  exist as a fragment.
- `CircularDependencyError` — topological sort detected a cycle.

## What is *not* in the registry

Per the ADR, three categories explicitly do **not** live here:

1. **Lesson substance** — sequence steps, L2 errors, vocabulary minimum,
   decolonization contrast pairs. These live in the wiki and are inlined by
   the generator into the rendered prompt alongside the registry.
2. **RAG payloads** — chunk text, page citations, source attribution. These
   are attached to `plan.references` and inlined by the generator.
3. **Composition directives** — "include ≥1 bad-form contrast pair when
   applicable" is a universal rule (registry); "the pair for m20 is
   `завтрак` vs `сніданок`" is a composition junction (generator-side
   logic, Step 5). The registry is universal; junctions are not.

If a rule is candidate-for-registry but you're not sure: ask whether the
text would be identical for m21 and m22 in the same level. If yes,
registry. If it varies, wiki or composition.

## Roadmap

- **Step 4 (this scaffold):** registry + loader + tests. Generator not yet
  wired. The legacy `linear-write.md` template still drives builds.
- **Step 5:** `scripts/build/prompt_generator.py` consumes the registry
  alongside the wiki manifest and plan references; emits writer prompt +
  reviewer prompt + one Obligation Checklist. Wired into `writer_context()`
  + `review_context()` in `linear_pipeline.py`, behind an opt-in flag.
- **Step 6:** reviewer-side deterministic checks emitted from the same
  registry; `wiki_coverage_gate` consumes the shared checklist. Eliminates
  the writer/reviewer/parser drift class that produced today's m20 blocker.

## How to add a new universal rule

1. Pick an id `R-<NAME>` that matches an existing pipeline constant in
   `linear_pipeline.py` (`RULE_*`) when one exists; otherwise add the
   constant too so telemetry shows the rule id on gate failures.
2. Create `scripts/build/universal_rules/R-<NAME>.md` with frontmatter.
3. If the rule semantically mirrors in writer + reviewer, use
   `slot: shared.contract`.
4. Run the loader tests:
   `.venv/bin/python -m pytest tests/build/test_universal_rules_registry.py`.
5. Until Step 5 lands, also update `linear-write.md` (and `linear-review-dim.md`
   if the rule has a reviewer surface). Step 5 will collapse the duplication.
