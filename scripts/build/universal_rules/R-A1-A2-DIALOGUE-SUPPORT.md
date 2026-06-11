---
id: R-A1-A2-DIALOGUE-SUPPORT
description: A1/A2 dialogue support uses gate-counted Ukrainian lines with nearby English support.
applies_to:
  levels: [a1, a2]
  tracks: [core]
  activity_profiles: [all]
slot: shared.contract
depends_on: [R-CLEAN-TABLES, R-AUDIENCE-LANGUAGE-A1]
---

**A1/A2 dialogue format (gate-counted).** Ukrainian dialogue lines must be `<DialogueBox uk="..." en="..." />` or `> ` blockquotes. Em-dash-only dialogue under `## Діалоги` is invisible to `l2_exposure_floor` and fails the module.

Use `<DialogueBox uk="..." en="..." />` to render dialogues with side-by-side translation. This satisfies Practice 2 + Practice 4 of ULP for A1 and the `l2_exposure_floor` gate. Em-dash bare lines without an `en` prop fail the gate. Every dialogue line needs an inline English gloss provided within 8 tokens of the Ukrainian text. Place longer expression notes at the block bottom of the component.

**Minimum UK dialogue lines (A1/A2).** For A1 and A2 modules, emit at least **15 distinct gate-countable Ukrainian dialogue surfaces** (`<DialogueBox uk="..." en="..." />` entries and `> ` blockquote lines, summed). The `l2_exposure_floor` gate's floor is 14; overshoot by at least 1 for safety. Prior builds have failed at exactly 13 gate-countable lines via `too_few_uk_dialogue_lines`. Count before emitting: if you have fewer than 15, add another exchange to the dialogue section or split a long turn into two shorter ones.

**UK example-sentence density.** A1-m15-24 modules need at least 14 gate-countable Ukrainian example surfaces across bullet-list lines and Markdown table data rows. Use bullets/tables for paradigms and trap pairs; prose-only paradigms count zero.
