===PLAN_PATCH_START===
decision: patch
complaint_summary: Expository filler prose and abstract coaching, combined with factually narrow or incorrect modal definitions.
rationale: This patch broadens the definitions of 'могти' and 'мусити' to prevent linguistic errors, replaces the 'generated-sounding' dialogue scenario with a concrete one, and enforces specific grammar terminology to satisfy anchor requirements and reduce meta-narration.
changes:
  - path: dialogue_situations[0].setting
    action: replace
    value: Deciding which movie to watch or where to walk
    reason: Replaces the vague 'negotiating' phrasing that the reviewer identified as sounding generated.
  - path: content_outline[0].points[0]
    action: replace
    value: 'Dialogue: Olya and Denys decide on an evening plan (cinema or walk). Use "Я хочу піти...", "Я не можу...", "Я мушу...". Focus on natural speech, not abstract descriptions.'
    reason: Forces a concrete scenario to improve tone and satisfy the [DIALOGUE_ACT] requirement.
  - path: content_outline[1].words
    action: replace
    value: 280
    reason: Tightens the budget to fix the [WORD_BUDGET] violation and force the removal of 'filler' grandiosity.
  - path: content_outline[1].points[0]
    action: replace
    value: 'Хотіти is irregular (Group I): я хочу, ти хочеш, він хоче, ми хочемо, ви хочете, вони хочуть. Note the т→ч change and the specific ending for each person. Uses: + infinitive or + noun in Accusative (e.g., хочу каву).'
    reason: Fixes [FACTUAL_ANCHOR] 'ending' and clarifies case usage to prevent linguistic errors.
  - path: content_outline[1].points[1]
    action: replace
    value: 'Negation: Я не хочу їсти. Note that "не" typically precedes the modal, but avoid teaching absolute "never" rules as placement can vary for emphasis.'
    reason: Directly corrects the teaching of an incorrect absolute rule regarding negation.
  - path: content_outline[2].points[0]
    action: replace
    value: 'Могти (can/able to) is irregular (Group I): я можу, ти можеш, ми можемо, вони можуть (г→ж change). It expresses ability, possibility, or permission (e.g., skills or requests).'
    reason: Broadens the definition to correct the 'strictly physical' error in the prose.
  - path: content_outline[2].points[1]
    action: replace
    value: 'Мусити (must/have to) is Group II. It expresses obligation or necessity. Clarify that it denotes a requirement but not necessarily an "immediate" urgency.'
    reason: Corrects the linguistic error identifying 'мусити' solely with immediate action.
  - path: content_outline[3].points[0]
    action: replace
    value: 'Summary: Compare desire, ability, and obligation with three simple sentences from a daily routine. Avoid abstract coaching and meta-narration like "In this module".'
    reason: Removes the summary filler and fixes the [META_NARRATION] violation.
===PLAN_PATCH_END===
