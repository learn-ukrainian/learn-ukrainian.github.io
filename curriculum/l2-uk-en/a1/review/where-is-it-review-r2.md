## Linguistic Scan
[Critical] `## Місцевий відмінок (The Locative Case)`: “For feminine nouns ending in **-а** or **-я**, replace the final vowel with **-і**.” This overgeneralizes locative formation and teaches unsafe morphology. VESUM-backed locatives such as `аптека → аптеці` and `рука → руці` show stem changes; the stated rule would produce nonexistent forms like `бібліотекі`.

## Exercise Check
4/4 planned markers are present: `match-up-nominative-locative`, `fill-in-answer-where`, `quiz-v-or-na`, `quiz-where-is-it`.

Placement is coherent:
- `match-up-nominative-locative` and `fill-in-answer-where` come after the locative-form explanation.
- `quiz-v-or-na` and `quiz-where-is-it` come after the `В чи на?` section.

No inline DSL exercise blocks are present, so only marker coverage/placement could be audited here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The four planned H2 sections are present and most outline points are covered, but the plan’s newcomer-neighbor place-finding setup is underdelivered: `аптека` never appears in the prose, even though the source-of-truth scenario explicitly includes it. |
| 2. Linguistic accuracy | 6/10 | The sentence “For feminine nouns ending in **-а** or **-я**, replace the final vowel with **-і**.” is factually unsafe; verified locatives such as `аптека → аптеці` and `рука → руці` contradict that blanket rule. |
| 3. Pedagogical quality | 7/10 | The module follows a dialogue → explanation → practice flow, but it teaches the overgeneralized feminine-locative rule as a rule, not as a limited pattern, which risks learners producing wrong forms. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is contextualized naturally: `в школі`, `на роботі`, `у банку`, `у/в магазині`, `на вулиці`, `у місті`; recommended items like `у лікарні`, `у/в кафе`, `на площі`, `на вокзалі`, `на пошті`, `в парку` also appear. |
| 5. Exercise quality | 9/10 | All four marker IDs from `activity_hints` are present and each follows the relevant teaching section, so the exercise scaffolding is aligned even though the generated YAML content is not shown here. |
| 6. Engagement & tone | 9/10 | The tone stays teacherly and concrete, e.g. “Learn the preposition and the noun together as a single grammatical chunk,” without drifting into gamified filler. |
| 7. Structural integrity | 6/10 | The pipeline note gives `Word count: 1133 words`, which is below the 1200 target. H2 structure and ordering are otherwise clean. |
| 8. Cultural accuracy | 9/10 | “Never say **на Україні**” and the sovereignty framing are culturally aligned and avoid Russian-centered framing. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers help, but the opener “Добрий день! Де Олена? … А Тарас? … А діти?” reads like an unexplained interrogation rather than a natural social exchange. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Місцевий відмінок (The Locative Case)` — “For feminine nouns ending in **-а** or **-я**, replace the final vowel with **-і**.”  
Issue: This is a false blanket rule. Common locatives such as `аптека → аптеці` and `рука → руці` require stem changes, so the wording teaches learners to generate wrong forms.  
Fix: Replace the sentence with a safer A1 formulation: many feminine nouns have `-і` in the locative, sometimes with a stem change, so learners should memorize high-frequency place phrases.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)` — the prose includes `в школі`, `на роботі`, `в Києві`, `в офісі`, but not the plan’s explicit newcomer-neighbor place-finding setup; `аптека` has 0 occurrences in the module text.  
Issue: The source-of-truth scenario calls for asking where to find places such as `аптека`, `банк`, `пошта`, `кафе`, `лікарня`, `парк`, but the module never realizes that situation directly.  
Fix: Insert a short additional dialogue about finding places in a new city using locative answers such as `в аптеці`, `у банку`, `на пошті`, `у кафе`, `у лікарні`, `в парку`.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: Pipeline note — `Word count: 1133 words`  
Issue: The module is below the 1200-word target.  
Fix: Add a compact extra dialogue/example block; the place-finding dialogue above is the cleanest way to satisfy both the plan gap and the word-count requirement.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: opening dialogue — “**Новий мешканець:** Добрий день! Де Олена?”  
Issue: The newcomer immediately asks about unexplained third parties, which makes the exchange feel artificial and interrogative.  
Fix: Add one contextualizing clause to the opening line so the learner understands why these questions are being asked.

## Verdict: REVISE
REVISE — there is a confirmed critical grammar error, the module is under the target word count, and the opening dialogue plus missing place-finding scenario weaken plan execution. Multiple dimensions fall below 9 and require fixes.

<fixes>
- find: "For feminine nouns ending in **-а** or **-я**, replace the final vowel with **-і**."
  replace: "Many feminine nouns ending in **-а** or **-я** have **-і** in the locative, sometimes with a stem change, so learn the most common place words as fixed phrases."

- find: "> **Новий мешканець:** Добрий день! Де Олена? *(Good day! Where is Olena?)*"
  replace: "> **Новий мешканець:** Добрий день! Я ще нікого тут не знаю. Де зараз Олена? *(Good day! I do not know anyone here yet. Where is Olena now?)*"

- insert_after: "The preposition tells us the spatial relationship, and the ending confirms it."
  content: |
    One more everyday situation from this module is asking where to find places in a new city:

    > **Новий мешканець:** Скажіть, будь ласка, де можна купити ліки? *(Excuse me, where can I buy medicine?)*
    > **Сусід:** В аптеці, на цій вулиці. *(At the pharmacy, on this street.)*
    > **Новий мешканець:** А де зняти гроші або відправити листа? *(And where can I withdraw money or mail a letter?)*
    > **Сусід:** У банку й на пошті, вони біля площі. *(At the bank and at the post office; they are by the square.)*
    > **Новий мешканець:** А де випити каву або знайти лікаря? *(And where can I have coffee or find a doctor?)*
    > **Сусід:** У кафе біля парку, а лікар у лікарні недалеко. *(In the café by the park, and the doctor is in the hospital nearby.)*
</fixes>