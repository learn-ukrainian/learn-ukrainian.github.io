## Linguistic Scan
- Factual lexical error in `## Синій ≠ блакитний`: `голубий` is described as “a Russian-influenced word.” VESUM and СУМ attest `голубий` as a standard Ukrainian adjective, so this claim is wrong.
- Semantic overstatement in `## Синій ≠ блакитний` and `## Підсумок — Summary`: `strictly required` and `exclusively` teach the `синій` / `блакитний` contrast as absolute. The evidence supports a common/useful distinction, not a rigid rule with no overlap.

## Exercise Check
- Found 4 markers: `quiz-color-matching`, `fill-in-color-agreement`, `group-sort-hard-soft-stem`, `quiz-blue-shades`.
- Marker count matches the 4 `activity_hints` in the plan.
- IDs match the plan’s exercise types/focuses.
- Placement is acceptable: the first three markers follow `## Кольори`, and `quiz-blue-shades` follows `## Синій ≠ блакитний`.
- No exercise-logic errors are visible from the markers alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The plan’s dialogue situations require `зелене листя` and `сіре пальто`; the generated text has `Є також білі лілії та жовті соняшники.` and `А де мій білий светр і коричневі черевики?` I searched the module text: `листя` = 0, `пальто` = 0. |
| 2. Linguistic accuracy | 6/10 | `голубий` is called “a Russian-influenced word,” but VESUM and СУМ attest `голубий` as Ukrainian. The module also says the blue distinction is `strictly required` and later `exclusively`, which overstates usage. |
| 3. Pedagogical quality | 7/10 | The hard/soft-stem contrast is explained well with `синій стіл`, `синя книга`, `синє вікно`, but the blue section teaches nuance as dogma: `strictly required` / `exclusively`. |
| 4. Vocabulary coverage | 7/10 | Core color vocabulary is present, but the plan-specific agreement models `зелене листя` and `сіре пальто` never appear in the prose. |
| 5. Exercise quality | 9/10 | All four planned activity markers are present and each comes after the relevant teaching block. |
| 6. Engagement & tone | 9/10 | The module uses concrete settings and useful cultural hooks like the flag and `вишиванка`, without falling into gamified nonsense. |
| 7. Structural integrity | 9/10 | All planned H2 sections are present and ordered correctly, marker syntax is clean, and the pipeline word count is 1572, above target. |
| 8. Cultural accuracy | 6/10 | The `голубий` claim and the absolute `синій` / `блакитний` framing flatten real Ukrainian usage instead of teaching it accurately. |
| 9. Dialogue & conversation quality | 9/10 | Both dialogues use named speakers and concrete objects rather than anonymous drill lines. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Синій ≠ блакитний`: `You might occasionally hear someone use the word **голубий** for light blue. However, you should know that this is a Russian-influenced word. As a dedicated learner of authentic Ukrainian, you should always prefer and use the proper native word **блакитний**.`  
Issue: `голубий` is attested in VESUM and СУМ as a Ukrainian adjective. Teaching it as non-Ukrainian is false.  
Fix: Replace this claim with wording that treats `голубий` as an attested Ukrainian word while still teaching `блакитний` as the module’s preferred beginner term.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Синій ≠ блакитний`: `Ukrainian actually has two completely distinct basic blues, and enforcing this distinction in your speech is strictly required.` and `## Підсумок — Summary`: `**синій** is exclusively for a dark, deep blue, while **блакитний** is exclusively for a light, sky blue.`  
Issue: The module turns a common lexical distinction into an absolute rule. That is too rigid and teaches false certainty.  
Fix: Soften the wording to `commonly distinguishes`, `most often`, and `usually`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)`: `> **Продавець:** Червоні. Є також білі лілії та жовті соняшники.`  
Issue: The plan explicitly requires `зелене листя (n, leaves)` in the flower-market dialogue. I searched the content and `листя` appears 0 times.  
Fix: Add `зелене листя` to the seller’s line.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)`: `> **Дмитро:** Гарно. А де мій білий светр і коричневі черевики?`  
Issue: The plan explicitly requires `сіре пальто (n, coat)` in the outfit dialogue. I searched the content and `пальто` appears 0 times.  
Fix: Add `сіре пальто` to the clothing example.

## Verdict: REVISE
The module is structurally sound and the exercise scaffold is present, but it contains two critical lexical inaccuracies and misses two plan-required dialogue examples. That is a `REVISE`, not a `PASS`.

<fixes>
- find: "You might occasionally hear someone use the word **голубий** for light blue. However, you should know that this is a Russian-influenced word. As a dedicated learner of authentic Ukrainian, you should always prefer and use the proper native word **блакитний**."
  replace: "You might occasionally hear someone use the word **голубий** for light blue. This word also exists in Ukrainian, but for this module it is clearer to teach **блакитний** as the main beginner term for light blue."
- find: "Ukrainian actually has two completely distinct basic blues, and enforcing this distinction in your speech is strictly required."
  replace: "Ukrainian commonly distinguishes two shades of blue in everyday vocabulary, and this distinction is very useful to understand and use."
- find: "Additionally, always remember the strict semantic difference between the two Ukrainian blues: **синій** is exclusively for a dark, deep blue, while **блакитний** is exclusively for a light, sky blue."
  replace: "Additionally, remember the usual distinction between the two Ukrainian blues: **синій** most often refers to a darker blue, while **блакитний** usually refers to a lighter, sky-blue shade."
- find: "> **Продавець:** Червоні. Є також білі лілії та жовті соняшники. *(Red. There are also white lilies and yellow sunflowers.)*"
  replace: "> **Продавець:** Червоні. Є також білі лілії, жовті соняшники й зелене листя. *(Red. There are also white lilies, yellow sunflowers, and green leaves.)*"
- find: "> **Дмитро:** Гарно. А де мій білий светр і коричневі черевики? *(Nice. And where is my white sweater and brown shoes?)*"
  replace: "> **Дмитро:** Гарно. А де мій білий светр, сіре пальто і коричневі черевики? *(Nice. And where are my white sweater, grey coat, and brown shoes?)*"
</fixes>