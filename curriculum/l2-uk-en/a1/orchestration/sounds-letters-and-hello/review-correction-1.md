<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [1. Plan adherence] [major]
  Location: Entire module
  Issue: The module falls significantly short of the 1200-word target. Most sections are 30-40% below their allocated word budgets. For example, the plan asks for 250 words for "Читаємо", but the text provides only a brief list and a few short sentences totaling ~150 words.
  Fix: Expand the prose in each section to meet the specified word budgets. Add deeper phonetic explanations, more reading practice examples, and more cultural context for the greetings and city names.
- NOTE: [5. Exercise quality] [minor]
  Location: `:::quiz` (title: "Звук чи літера?")
  Issue: The quiz contains 4 items, but the plan's `activity_hints` required 6 items.
  Fix: Add 2 more questions to the quiz block to meet the target (e.g., test the concept of the soft sign Ь or the total number of consonant sounds).
- NOTE: [5. Exercise quality] [minor]
  Location: `:::group-sort` under the "Перші слова" section
  Issue: The sorting activity tests vowels vs. consonants, but it is placed at the end of the "Перші слова" section. This breaks the pedagogical flow, as vowels and consonants were taught in the first section.
  Fix: Move the `:::group-sort` activity to the end of the "Звуки і літери" section.
- NOTE: [1. Plan adherence] [minor]
  Location: `:::true-false` under the "Читаємо" section
  Issue: An extra true-false activity was generated, which was not requested in the `activity_hints` of the plan.
  Fix: Remove the true-false activity to strictly adhere to the plan, or if retained, ensure the orchestrator plan is updated to expect 5 activities instead of 4.
</correction_directive>