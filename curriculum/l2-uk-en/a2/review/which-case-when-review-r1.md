## Linguistic Scan
- No Russianisms, Surzhyk, paronym errors, forbidden Russian characters, or confirmed calques found.
- Critical grammar-teaching error: `Але для фраз зі словами «наступний» або «минулий» ми завжди обираємо родовий відмінок.` This is false as an absolute. The repo’s textbook corpus attests other standard patterns such as `наступну добу` and `минулої суботи`, so the rule must be narrowed to specific no-preposition time phrases, not taught as universal.

## Exercise Check
- Marker inventory is complete: 4/4 markers are present, and the IDs match the plan’s `quiz`, `group-sort`, `fill-in`, and `true-false` hints.
- Placement is weak: there is no practice marker after the first “Дієслово вирішує” section, while both `quiz-case-verb-prep` and `true-false-case-pairs` are clustered after the final section.
- The fill-in marker line contains a stray inline annotation after the HTML comment, which looks like an artifact rather than publishable prose.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned H2 sections are present, and core examples from the plan appear: `думати про майбутнє`, `у четвер`, `хлопець у червоному светрі`, `бігати по кімнаті`, `у 2014 році`. But the generated content contains no in-prose citation of `Заболотний` or `ULP`, despite the plan listing them as references. |
| 2. Linguistic accuracy | 7/10 | The line `Але для фраз зі словами «наступний» або «минулий» ми завжди обираємо родовий відмінок` teaches a false absolute rule. The note below repeats the same overgeneralization. |
| 3. Pedagogical quality | 7/10 | The algorithm section says to ask case questions such as `кого?`, `що?`, `кому?`, `ким?`, but omits Genitive and Locative prompts even though this module heavily teaches both. That makes the advertised “decision process” incomplete. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is fully present in prose: `відмінок`, `прийменник`, `дієслово`, `напрямок`, `місце`, `час`, `характеристика`, `думати`, `боятися`, `користуватися`. Recommended vocabulary also appears naturally: `алгоритм`, `контекст`, `керувати`, `майбутнє`. |
| 5. Exercise quality | 7/10 | The markers are not evenly distributed. `group-sort` comes after section 2, `fill-in` after section 3, but both `quiz-case-verb-prep` and `true-false-case-pairs` sit at the very end, so the verb-governed cases in section 1 get no immediate practice. |
| 6. Engagement & tone | 9/10 | The teacherly frame is clear and useful, especially `Сьогодні ми граємо в граматичних детективів` and the steady use of concrete sentence examples. |
| 7. Structural integrity | 8/10 | The module has all planned sections and exceeds the 2000-word target, but this line is a formatting artifact: `<!-- INJECT_ACTIVITY: fill-in-mixed-cases --> [fill-in, Complete sentences ...]`. |
| 8. Cultural accuracy | 10/10 | The module stays Ukrainian-centered, makes no Russia-comparison shortcuts, and uses culturally neutral Ukrainian examples. |
| 9. Dialogue & conversation quality | 7/10 | The opening exchange is mostly teacher interrogation with short answer retrieval: `Де тут називний відмінок?` → `Слово «президент».` → `А чому ми кажемо «з прем'єром»?` It is functional, but not a natural multi-turn conversation. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Особливі випадки: Час, характеристика, шлях` — `Але для фраз зі словами «наступний» або «минулий» ми завжди обираємо родовий відмінок.`  
Issue: This teaches a false absolute. Ukrainian also uses non-genitive time phrases with these adjectives.  
Fix: Narrow the claim to common no-preposition expressions like `наступного тижня`, `минулого року`.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: note in `Особливі випадки` — `switch to the Genitive case for phrases with "next" or "last"`  
Issue: The quick tip repeats the same wrong generalization.  
Fix: Rephrase it so it refers only to common no-preposition time expressions.

- [PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Алгоритм вибору відмінка` — `ask the case question, such as «кого?», «що?», «кому?», or «ким?»`  
Issue: The algorithm omits Genitive and Locative question patterns, so it does not actually support the full case set taught in the module.  
Fix: Expand the list to include `кого? чого?` and locative prompts such as `у кому? у чому? / на кому? на чому?`.

- [EXERCISE QUALITY] [SEVERITY: major]  
Location: marker placement — `<!-- INJECT_ACTIVITY: quiz-case-verb-prep -->` appears only at the very end, after section 4.  
Issue: Practice is not evenly spaced; section 1 teaches verb-governed cases but gets no immediate check.  
Fix: Move the quiz marker to the end of section 1, right after the `думати про + Acc.` teaching block.

- [PLAN ADHERENCE] [SEVERITY: major]  
Location: whole generated content — search in the generated-content block returned 0 hits for `Заболотний`, `ULP`, or `Ukrainian Cases Overview`.  
Issue: The plan’s references are not integrated into the prose at all.  
Fix: Add one short sentence in the introduction explicitly grounding the method in the listed references.

- [STRUCTURAL INTEGRITY] [SEVERITY: minor]  
Location: `<!-- INJECT_ACTIVITY: fill-in-mixed-cases --> [fill-in, Complete sentences ...]`  
Issue: The bracketed note after the marker is a stray formatting artifact.  
Fix: Leave only the HTML marker.

- [DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: opening dialogue block beginning `— **Вчитель:** Читаємо перший текст.`  
Issue: The exchange is almost entirely teacher prompts plus one-line retrieval answers, which matches the rubric’s “interrogation” failure mode.  
Fix: Replace it with a short collaborative exchange where students explain multiple forms in fuller turns.

## Verdict: REVISE
REVISE. There is a critical grammar-teaching error about `наступний/минулий` time phrases, plus major pedagogy, exercise-placement, reference-integration, and dialogue-quality issues. Multiple dimensions are below 9, and the identified errors require concrete fixes.

<fixes>
- find: "Сьогодні ми граємо в граматичних детективів. Ми читаємо українську газету і шукаємо кожен **відмінок** (grammatical case)."
  replace: "Сьогодні ми граємо в граматичних детективів. Ми читаємо українську газету і шукаємо кожен **відмінок** (grammatical case). Такий спосіб аналізу спирається на шкільні підручники Заболотного та огляд ULP: спочатку визначаємо слово, яке керує формою, а потім обираємо закінчення."

- find: |
    > — **Вчитель:** Читаємо перший текст. «Президент зустрівся з прем'єром. Для журналістів підготували зал». Де тут називний відмінок? *(Let's read the first text. "The president met with the prime minister. They prepared a hall for the journalists". Where is the nominative case here?)*
    > — **Студенти:** Слово «президент». Це суб'єкт, він робить дію. *(The word "president". It is the subject, he is doing the action.)*
    > — **Вчитель:** Правильно. А чому ми кажемо «з прем'єром»? *(Correct. And why do we say "with the prime minister"?)*
    > — **Студенти:** Тому що тут є **прийменник** (preposition) «з». Це орудний відмінок. *(Because there is the preposition "with" here. It is the instrumental case.)*
    > — **Вчитель:** Чудово! А слово «журналістів»? *(Great! And the word "journalists"?)*
    > — **Студенти:** Це родовий відмінок після прийменника «для». *(It is the genitive case after the preposition "for".)*
    > — **Вчитель:** А слово «зал»? *(And the word "hall"?)*
    > — **Студенти:** Це знахідний відмінок. Це об'єкт дії «підготували». *(It is the accusative case. It is the object of the action "prepared".)*
  replace: |
    > — **Вчитель:** Читаємо перший текст. «Президент зустрівся з прем'єром. Для журналістів підготували зал». Які відмінки ви вже бачите? *(Let's read the first text. "The president met with the prime minister. They prepared a hall for the journalists". Which cases can you already see?)*
    > — **Студенти:** «Президент» — це називний, бо це суб'єкт. «З прем'єром» — орудний, бо тут прийменник «з». *("President" is the nominative because it is the subject. "With the prime minister" is instrumental because of the preposition "з".)*
    > — **Вчитель:** Добре. А як пояснити «для журналістів» і «зал»? *(Good. And how do we explain "for the journalists" and "hall"?)*
    > — **Студенти:** «Для журналістів» — це родовий після прийменника «для», а «зал» — знахідний, бо це об'єкт дії «підготували». *("For the journalists" is genitive after the preposition "для", and "hall" is accusative because it is the object of the action "prepared".)*

- find: "Для днів тижня ми використовуємо прийменник «у» або «в» та знахідний відмінок. Наприклад, ми часто кажемо «у четвер», «у середу» або «у п'ятницю». Іноді ми можемо сказати про час навіть без прийменника. Якщо ви хочете сказати про свої плани, ви можете сказати: «Цю неділю я відпочиваю». Але для фраз зі словами «наступний» або «минулий» ми завжди обираємо родовий відмінок. Наприклад, ми кажемо «наступного тижня» або «минулого року»."
  replace: "Для днів тижня ми використовуємо прийменник «у» або «в» та знахідний відмінок. Наприклад, ми часто кажемо «у четвер», «у середу» або «у п'ятницю». Іноді ми можемо сказати про час навіть без прийменника. Якщо ви хочете сказати про свої плани, ви можете сказати: «Цю неділю я відпочиваю». Але в поширених часових фразах без прийменника, як-от «наступного тижня» або «минулого року», ми часто використовуємо родовий відмінок."

- find: "**Quick tip** — Use the Accusative case for days of the week (`у понеділок`), but remember to switch to the Genitive case for phrases with \"next\" or \"last\" (`наступного вівторка`, `минулого тижня`)."
  replace: "**Quick tip** — Use the Accusative case for days of the week (`у понеділок`), but remember that many common no-preposition time phrases use the Genitive case (`наступного тижня`, `минулого року`)."

- find: |
    > *When you dream or think about something, you use the preposition "про" and the accusative case. I often think about the future. They dream about a trip. We are thinking about a new plan.*

    ## Прийменник вирішує: Один прийменник — різні відмінки (~600 words)
  replace: |
    > *When you dream or think about something, you use the preposition "про" and the accusative case. I often think about the future. They dream about a trip. We are thinking about a new plan.*

    <!-- INJECT_ACTIVITY: quiz-case-verb-prep -->

    ## Прийменник вирішує: Один прийменник — різні відмінки (~600 words)

- find: |
    <!-- INJECT_ACTIVITY: quiz-case-verb-prep -->
    <!-- INJECT_ACTIVITY: true-false-case-pairs -->
  replace: |
    <!-- INJECT_ACTIVITY: true-false-case-pairs -->

- find: "<!-- INJECT_ACTIVITY: fill-in-mixed-cases --> [fill-in, Complete sentences with the correct noun form — mixed cases triggered by different prepositions and verbs, including time expressions (у четвер), characteristics (у червоному светрі), and path (по кімнаті), 8 items]"
  replace: "<!-- INJECT_ACTIVITY: fill-in-mixed-cases -->"

- find: "When you speak Ukrainian, choosing the correct **відмінок** (grammatical case) can feel overwhelming. To make it easier, we use a simple three-step algorithm. The first step is to look for a **прийменник** (preposition). If there is one, it usually dictates the case immediately. If there is no preposition, move to step two: check the **дієслово** (verb). Many verbs require a specific case for their object. Finally, step three: if you are still unsure, ask the case question, such as «кого?», «що?», «кому?», or «ким?»."
  replace: "When you speak Ukrainian, choosing the correct **відмінок** (grammatical case) can feel overwhelming. To make it easier, we use a simple three-step algorithm. The first step is to look for a **прийменник** (preposition). If there is one, it usually dictates the case immediately. If there is no preposition, move to step two: check the **дієслово** (verb). Many verbs require a specific case for their object. Finally, step three: if you are still unsure, ask the case question, such as «кого? що?», «кого? чого?», «кому?», «ким?», or locative prompts like «у кому? у чому?» / «на кому? на чому?`."
</fixes>