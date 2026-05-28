---
id: R-BAD-FORM-MARKER
description: Wrap non-VESUM teaching-contrast forms in HTML bad-form markers; decolonized framing.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: [R-VESUM-ALL-WORDS]
---

Decolonized framing is default. Ukraine has its own canon and history; Russian-imperial writers stay Russian; Holodomor is genocide; the war is a war, not a "conflict"; reject Soviet euphemisms such as "reunification" and "brotherly peoples."

**Bad-form marker convention (MANDATORY everywhere).** Any Ukrainian word form that is NOT in VESUM and appears only as a teaching contrast MUST be wrapped in `<!-- bad -->...<!-- /bad -->` markers in every artifact. Do not use italics or bare prose for bad forms.

```markdown
Stick to **<canonical Ukrainian form>** (not the Russian-borrowed <!-- bad -->X<!-- /bad -->),
and use **<native Ukrainian verb>** (not the surzhyk <!-- bad -->Y<!-- /bad -->).
```

**Positive requirement for A1-A2 vocabulary modules:** when the module covers vocabulary domains where L1-Russian-exposure learners are likely to substitute Russian borrowings (food/dining, household items, clothing, daily routines, family, body, time-of-day expressions, transportation, common verbs of action), include **AT LEAST ONE** explicit bad-form contrast pair using the marker syntax above. This is a pedagogical tool (contrast pairs accelerate L2 acquisition) AND satisfies the `llm_qg.decolonization` rubric's criterion (b) — see `scripts/build/phases/linear-review-dim.md` § `decolonization`. Pick the single most-likely L1 substitution for the module's topic from the wiki/plan/RAG content and include it concretely. One marker pair is sufficient; this isn't a quantity gate.

Modules whose topic does NOT involve L1-Russian-substitutable vocabulary (e.g. pure grammar abstractions, IPA-only phonetics drill, formal-letter templates) are exempt — but for those, document the exemption inline in your `<plan_reasoning>` so the reviewer doesn't dock for absence.

Apply the same convention in `module.md`, `activities.yaml` statements/items, and `vocabulary.yaml` usage lines when they name a wrong form. `type: error-correction` `sentence:` / `error:` fields are already excluded from VESUM; markers are optional there.

**CONCRETE FORBIDDEN PATTERNS — HARD REJECT.** These trip `vesum_verified`, `formatting_standards`, or `russianisms_clean` unless the bad form is comment-marked:
- `*X*, not *Y*` or `... not *Y*` — italic bad-form leak.
- `say X, not Y`, `X, а не Y`, `instead of Y`, `замість Y` — unmarked contrast.
- `(not Y)` / `(не Y)` — unmarked parenthetical contrast.
- true-false `statement: "X, а не Y."` when Y is malformed or Russianism.

REQUIRED: `Stick to **X** (not the Russian-borrowed <!-- bad -->Y<!-- /bad -->).`
When in doubt, omit the bad contrast and teach only the good form.

**Morpheme-bold notation.** Do not put hyphens/slashes inside bold spans: write `<verb> (**-suffix**)`, not `<verb>**-suffix**` or `**-suffix/-variant**`.

**Textbook syllable-break notation.** Keep textbook syllable hyphens only when the module teaches syllabification / склади. Otherwise strip display hyphens before learner-facing prose.

**Russianism floor.** `russianisms_strict` fails on any critical Russicism/calque/surzhyk finding. Check suspicious forms with `check_russian_shadow`, `search_style_guide`, `search_ua_gec_errors`, `search_heritage`, and `query_pravopys`. Never paste raw Russian forms into prose/dialogue; use a `<!-- VERIFY -->` placeholder or omit.
