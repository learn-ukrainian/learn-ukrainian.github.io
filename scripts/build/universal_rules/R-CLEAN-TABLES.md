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

**Dialogue format.** B1+ dialogue should be Ukrainian-only blockquote or prose dialogue unless a component contract explicitly allows an English-support field outside the body. If any level uses a `<DialogueBox>` component, the tag MUST be self-closing — it must end with `/>`. A bare `<DialogueBox uk="...">` (no closing `/>`, no `</DialogueBox>`) is invalid MDX and silently fails component parsing.

At B1+, do not add English dialogue glosses; teach meaning through Ukrainian context, response, paraphrase, and recall questions.

`шо` is acceptable inside dialogue blocks (`<DialogueBox>` or `>` blockquotes) when the register is colloquial; never in teacher-voice narration. When you use it, add a `notes:` field to the `що` entry in `vocabulary.yaml` flagging the literary↔colloquial pair so learners know when each is appropriate (the per-item schema accepts `notes`, NOT `note` — singular fails schema validation). Do NOT add a separate top-level entry for `шо` — VESUM does not codify it and the vocab gate will reject a standalone lemma.
