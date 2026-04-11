## Linguistic Scan
Found 1 linguistic error:
- Pronoun gender mismatch: the word "слово" is neuter in Ukrainian, but it is incorrectly referred to with the feminine pronoun "вона".

## Exercise Check
- The `fill-in` marker is placed correctly at the end of the first section on verbs taking the dative.
- The `match-up` marker is placed correctly at the end of the `подобатися` section. 
- The `true-false` marker is placed correctly at the end of the age section.
- The `quiz` marker is placed correctly at the end of the dative vs. accusative comparison.
The markers completely match the plan's activity hints and test the exact grammar concepts just introduced. 

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The dialogue ignores the specific setting prompts ("Допомагаю бабусі нести сумки", "Раджу сусідці нового лікаря", "Мені подобається допомагати!"). Used an incorrect H2 heading ("Давальний відмінок особи" instead of "Давальний відмінок досвідника"). Failed to include the required age examples "Мені двадцять п'ять років. Дідусеві вісімдесят. Дитині три роки". Substituted the planned "розповідати ПРО ЩО" with "розповідати ЩО". |
| 2. Linguistic accuracy | 8/10 | CRITICAL ERROR: "Ви бачите, як змінюється слово «мама»? Вона має закінчення...". The noun "слово" is neuter and requires "воно", not "вона" (which incorrectly agrees with the quoted string rather than the grammatical subject). |
| 3. Pedagogical quality | 9/10 | Strong, clear explanations ("The action goes from the object to the person", "Age is treated as an experience that happens to someone"). PPP flow is maintained effectively. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words are properly introduced and placed in context. |
| 5. Exercise quality | 10/10 | All required activity markers are present, matching the planned type and focus perfectly. |
| 6. Engagement & tone | 10/10 | Excellent teaching persona that is encouraging without being overly gamified or patronizing. |
| 7. Structural integrity | 8/10 | The module includes an unrequested `## Підсумок` section at the end. The rubric strictly prohibits duplicate summary sections. Word count exceeds the budget beautifully. |
| 8. Cultural accuracy | 10/10 | Explicitly contrasts the correct Ukrainian dative structure against the common Russian interference ("дякую вас"), which is highly useful. |
| 9. Dialogue & conversation quality | 8/10 | The provided dialogue sounds natural, but it misses several of the specific narrative beats requested in the plan. |

## Findings
[1. Plan adherence] [major]
Location: `> — **Волонтер:** Олено, я зараз **допомагаю сусідці** *(I help the neighbor)* прибирати великий парк...`
Issue: The dialogue entirely missed the required narrative details from the plan ("Допомагаю бабусі нести сумки. Дзвоню другові. Раджу сусідці нового лікаря. Мені подобається допомагати!").
Fix: Rewrite the dialogue lines to accurately include these specific phrases.

[1. Plan adherence] [minor]
Location: `## Мені подобається: Давальний відмінок особи (The Experiencer Dative with подобатися)`
Issue: Used the wrong H2 heading ("особи" instead of "досвідника").
Fix: Change the heading to match the plan.

[1. Plan adherence] [minor]
Location: `Наприклад, ми кажемо: «Мені двадцять років». *(For example, we say: "To me twenty years".)* Дідусеві вісімдесят років. *(Grandpa is eighty years old.)*`
Issue: The plan explicitly asked to include the examples "Мені двадцять п'ять років", "Дідусеві вісімдесят", and "Дитині три роки", which were simplified or omitted.
Fix: Update the examples to exactly match the plan's list.

[1. Plan adherence] [minor]
Location: `Він розповідає нам історію. *(He tells us a story.)* Кому він розповідає? Нам. *(To whom does he tell? To us.)* Що він розповідає? Історію.`
Issue: The plan specified teaching the pattern "розповідати КОМУ (Dat.) ПРО ЩО (Acc.)", but the text taught "розповідати КОМУ (Dat.) ЩО (Acc.)".
Fix: Update the example to "розповідати нам про подорож" (or similar) to teach the intended structure.

[2. Linguistic accuracy] [critical]
Location: `Ви бачите, як змінюється слово «мама»? *(Do you see how the word "mom" changes?)* Вона має закінчення «-у» у знахідному відмінку, і «-і» у давальному.`
Issue: Pronoun gender mismatch. The noun "слово" (word) is neuter, so it must be referred to as "воно", not "вона".
Fix: Change "Вона має" to "Воно має".

[7. Structural integrity] [major]
Location: `## Підсумок`
Issue: Added a duplicate summary section at the very end. The rubric prohibits duplicate/meta summary sections not present in the plan outline.
Fix: Remove the entire "Підсумок" section.

## Verdict: REVISE
The module is high-quality in pedagogy and engagement, but it contains a critical grammatical error regarding pronoun agreement ("слово" -> "вона"), a structural violation (added "Підсумок" summary section), and multiple missed constraints from the plan regarding the dialogue and specific examples.

<fixes>
- find: "## Мені подобається: Давальний відмінок особи (The Experiencer Dative with подобатися)"
  replace: "## Мені подобається: Давальний відмінок досвідника (The Experiencer Dative with подобатися)"
- find: "Ви бачите, як змінюється слово «мама»? *(Do you see how the word \"mom\" changes?)* Вона має закінчення «-у» у знахідному відмінку, і «-і» у давальному."
  replace: "Ви бачите, як змінюється слово «мама»? *(Do you see how the word \"mom\" changes?)* Воно має закінчення «-у» у знахідному відмінку, і «-і» у давальному."
- find: |
    > — **Волонтер:** Олено, я зараз **допомагаю сусідці** *(I help the neighbor)* прибирати великий парк. Тобі потрібна допомога?
    > — **Олена:** Ні, я вже все зробила. Але я **раджу тобі** *(I advise you)* трохи відпочити.
    > — **Волонтер:** Добре, тоді я **дзвоню другові** *(I call the friend)* Івану. Він має принести воду.
    > — **Іван:** Привіт! Я вже тут. Тримай свіжу воду та смачну їжу.
    > — **Волонтер:** Я щиро **дякую тобі** *(I thank you)* за цю велику допомогу!
  replace: |
    > — **Волонтер:** Олено, я зараз **допомагаю бабусі** *(I help the grandma)* нести сумки. А ти що робиш?
    > — **Олена:** Я **раджу сусідці** *(I advise the neighbor)* нового лікаря.
    > — **Волонтер:** Добре, тоді я **дзвоню другові** *(I call the friend)* Івану. Він має принести воду. **Мені подобається допомагати!** *(I like helping!)*
    > — **Іван:** Привіт! Я вже тут. Тримай свіжу воду та смачну їжу.
    > — **Волонтер:** Я щиро **дякую тобі** *(I thank you)* за цю велику допомогу!
- find: "Наприклад, ми кажемо: «Мені двадцять років». *(For example, we say: \"To me twenty years\".)* Дідусеві вісімдесят років. *(Grandpa is eighty years old.)*"
  replace: "Наприклад, ми кажемо: «Мені двадцять п'ять років». *(For example, we say: \"To me twenty-five years\".)* Дідусеві вісімдесят. *(Grandpa is eighty.)* Дитині три роки. *(The child is three years old.)*"
- find: |
    Формула така: дієслово + кому? + що?
    Я даю мамі квіти. *(I give mom flowers.)* Кому я даю? Мамі. *(To whom do I give? To mom.)* Що я даю? Квіти. *(What do I give? Flowers.)*
    Він розповідає нам історію. *(He tells us a story.)* Кому він розповідає? Нам. *(To whom does he tell? To us.)* Що він розповідає? Історію. *(What does he tell? A story.)*
  replace: |
    Формула така: дієслово + кому? + що? (або про що?)
    Я даю мамі квіти. *(I give mom flowers.)* Кому я даю? Мамі. *(To whom do I give? To mom.)* Що я даю? Квіти. *(What do I give? Flowers.)*
    Він розповідає нам про подорож. *(He tells us about the trip.)* Кому він розповідає? Нам. *(To whom does he tell? To us.)* Про що він розповідає? Про подорож. *(About what does he tell? About the trip.)*
- find: |
    ## Підсумок

    Ми вивчили дуже важливу тему сьогодні. *(We learned a very important topic today.)* Давальний відмінок має три головні ролі у таких реченнях.

    По-перше, дієслова **допомагати** *(to help)*, **дякувати** *(to thank)* та **дзвонити** *(to call)* вимагають форми «кому?». *(First, the verbs "to help", "to thank", and "to call" require the "to whom?" form.)* Дія йде до людини. *(The action goes to the person.)*

    По-друге, дієслово **подобатися** *(to like)* має зворотну структуру. *(Second, the verb "to like" has a reverse structure.)* Людина стоїть у давальному відмінку, а річ — у називному. *(The person is in the dative case, and the thing is in the nominative.)*

    По-третє, ми використовуємо давальний відмінок для віку. *(Third, we use the dative case for age.)*

    Перевірте свої знання: *(Check your knowledge:)*

    - Як правильно сказати: «дякую тебе» чи «дякую тобі»? *(How to say it correctly: "thank you [acc.]" or "thank you [dat.]"?)* Правильно: «дякую тобі». *(Correct: "thank you [dat.]".)*
    - Яку форму має дієслово «подобатися», якщо мені подобаються книги? *(What form does the verb "to like" have if I like books?)* Множина: «подобаються». *(Plural: "they are pleasing".)*
    - Яку форму слова **рік** *(year)* ми вживаємо для числа 22? *(Which form of the word "year" do we use for the number 22?)* Форма: «двадцять два роки». *(Form: "twenty-two years".)*
  replace: ""
</fixes>
