---
id: R-CLEAN-TABLES
description: Bold target Ukrainian forms only; conjugation tables need all six person/number rows.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: []
---

**Clean table formatting.** Tables: bold ONLY the target Ukrainian forms. Pronoun columns (`я`, `ти`, ...), English headers, and English glosses remain in regular weight. Conjugation tables teaching a present-tense paradigm must include the FULL set of person/number rows: **я / ти / він,вона,воно / ми / ви / вони** (six rows). Vocabulary tables stay two-column unless a third column adds essential teaching value (e.g., stress mark, IPA).

**Dialogue format (gate-counted).** Ukrainian dialogue lines must be `<DialogueBox uk="..." en="..." />` or `> ` blockquotes. Em-dash-only dialogue under `## Діалоги` is invisible to `l2_exposure_floor` and fails the module. **The `<DialogueBox>` tag MUST be self-closing — it must end with `/>`.** A bare `<DialogueBox uk="..." en="...">` (no closing `/>`, no `</DialogueBox>`) is invalid MDX AND the `l2_exposure_floor` regex counts it as ZERO, so every such line silently fails the gate.

Use `<DialogueBox uk="..." en="..." />` to render dialogues with side-by-side translation. This satisfies Practice 2 + Practice 4 of ULP for A1 and the `l2_exposure_floor` gate. Em-dash bare lines without an `en` prop fail the gate. Every dialogue line needs an **inline English gloss** provided **within 8 tokens** of the Ukrainian text. Place longer expression notes at the **block-bottom** of the component.

**Minimum UK dialogue lines (A1-A2).** For A1 and A2 modules, emit at least **15 distinct gate-countable Ukrainian dialogue surfaces** (`<DialogueBox uk="..." en="..." />` entries and `> ` blockquote lines, summed). The `l2_exposure_floor` gate's floor is 14; overshoot by ≥1 for safety. Prior builds have failed at exactly 13 gate-countable lines via `too_few_uk_dialogue_lines`. Count BEFORE emitting: if you have <15, add another exchange to the dialogue section or split a long turn into two shorter ones.

`шо` is acceptable inside dialogue blocks (`<DialogueBox>` or `>` blockquotes) when the register is colloquial; never in teacher-voice narration. When you use it, add a `notes:` field to the `що` entry in `vocabulary.yaml` flagging the literary↔colloquial pair so learners know when each is appropriate (the per-item schema accepts `notes`, NOT `note` — singular fails schema validation). Do NOT add a separate top-level entry for `шо` — VESUM does not codify it and the vocab gate will reject a standalone lemma.

**UK example-sentence density.** A1-m15-24 modules need >=14 gate-countable Ukrainian example surfaces across bullet-list lines and Markdown table data rows. Use bullets/tables for paradigms and trap pairs; prose-only paradigms count zero.
