---
id: R-ACTIVITY-COMPOSITION
description: Activities composed from layered vocab allowlist; distractors only from wiki inventory.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: [R-RENDERER-CHARTER]
---

**Activity composition (bounded, not rendered).** Wiki names the activity formats (`Вправа 1: fill-in reflexive verbs`); you compose concrete items. The same layered vocab allowlist from the V7.1 Renderer Charter applies: every Ukrainian token in `sentence:`, `prompt:`, `options:`, `items:` fields (and in distractors for MCQ/select) must come from `wiki.vocabulary_minimum ∪ plan.targets.new_vocabulary ∪ plan.targets.vocabulary_hints ∪ cumulative_learner_state.taught_lemmas ∪ closed_class_function_words ∪ proper_nouns_in_wiki_examples`. The `learner_state` vocab gate scans `activities.yaml` token-by-token; unsupported content lemmas in activity items fail the gate just like prose lemmas do.

**Distractor supply (critical at A1).** Source wrong-form distractors for MCQ, select, and error-correction items ONLY from: (a) the wiki's L2 errors table (`## Типові помилки L2`), (b) the wiki's decolonization bad-form pairs (`<!-- bad -->...<!-- /bad -->` markers), or (c) the cumulative learner state. **Never invent Russianisms or fabricate wrong forms to fill an activity slot.** If the wiki's distractor inventory is insufficient for an activity (fewer wrong forms than the activity needs items), surface that gap via `<implementation_map>` `treatment="deferred — wiki distractor inventory thin"`; do not paper over by inventing. The upstream `wiki_completeness_gate` enforces ≥6 distractors at A1/A2 (L2-errors + bad-form pairs combined), but module-specific shortages can still happen — surface them honestly.

**Activity item count vs INLINE/WORKBOOK split.** The `{ACTIVITY_COUNT_TARGET}` placeholder carries the per-level target; the split rule (INLINE 4-6 + WORKBOOK 6-9 at A1, etc.) is enforced by the activity-schema gate. Schema fields stay canonical per "Activity Authoring Fields" (HARD FAIL on aliases like `wrong:`/`incorrect:` instead of `error:`).
