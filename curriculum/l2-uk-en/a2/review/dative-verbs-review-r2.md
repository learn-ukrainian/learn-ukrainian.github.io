## Linguistic Scan
2 errors found:
1. **"досвідника"** — A hallucinated linguistic term (a calque of the English "experiencer"). VESUM confirms it does not exist. The standard phrasing is "особи".
2. **"робити уроки"** — A known calque from the Russian "делать уроки" (confirmed via GRAC). It should be "робити/виконувати домашнє завдання".

## Exercise Check
4 exercise markers found:
1. `<!-- INJECT_ACTIVITY: fill-in-focus-... -->`
2. `<!-- INJECT_ACTIVITY: match-up-focus-... -->`
3. `<!-- INJECT_ACTIVITY: true-false-focus-... -->`
4. `<!-- INJECT_ACTIVITY: quiz-focus-... -->`
All markers are logically placed after the specific sections they test and exactly match the required `activity_hints` in type and focus.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Excellent coverage of grammatical points. The specific dialogue prompts (grandma carrying bags, advising new doctor) were slightly altered to different volunteering situations, but the grammar context remained. The plan explicitly asked to demonstrate the negative form "не дзвони їй", but an affirmative "Подзвони їй" was provided instead. |
| 2. Linguistic accuracy | 8/10 | Excellent explanation of the Russian interference with "дякувати", but a hallucinated calque term ("досвідника") was invented for "experiencer" instead of a natural Ukrainian grammatical term. "робити уроки" is also a Russian calque. |
| 3. Pedagogical quality | 8/10 | Great use of contrastive examples and the PPP flow. However, there is a minor contradiction: the text states a "strong preference" for the "-ові/-еві" endings for masculine people, but the immediate next example ("головному лікарю") uses the "-ю" ending, which confuses the rule just taught. |
| 4. Vocabulary coverage | 9/10 | Required and recommended vocabulary is present. However, the verbs `співчувати` and `заздрити` are presented as part of a bare list without their own contextual example sentences. |
| 5. Exercise quality | 10/10 | Exercise markers correspond exactly to the plan's requirements and are well distributed. |
| 6. Engagement & tone | 9/10 | Very supportive and clear tone. There are minor instances of empty filler sentences that just take up space without pedagogical value ("Сьогодні ми вивчаємо дуже важливу тему української граматики."). |
| 7. Structural integrity | 10/10 | Clean Markdown with all headers matching the outline. Word count is 3010, which provides fantastic depth well beyond the 2000 target. |
| 8. Cultural accuracy | 10/10 | Outstanding and direct warning against using direct Russian translations ("дякую вас"), directly supporting the decolonized pedagogy. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue sounds authentic, but there is a slight logical jump where the volunteer states they are about to call Ivan, and Ivan immediately responds "Я вже тут" and hands over water without the call taking place. |

## Findings
[DIMENSION] Linguistic accuracy [Critical]
Location: `## Мені подобається: Давальний відмінок досвідника (The Experiencer Dative with подобатися)`
Issue: "досвідника" is a hallucinated calque for the English linguistic term "experiencer". The word does not exist in standard Ukrainian or VESUM. The grammatical concept should be referred to as "давальний відмінок особи".
Fix: Replace "досвідника" with "особи".

[DIMENSION] Linguistic accuracy [Major]
Location: `Мій малий син допомагає старшому братові (brother) робити уроки.`
Issue: "робити уроки" is a calque of the Russian "делать уроки". Natural Ukrainian uses "робити/виконувати домашнє завдання".
Fix: Replace "робити уроки" with "робити домашнє завдання".

[DIMENSION] Pedagogical quality [Major]
Location: `Ми щиро дякуємо головному лікарю (the doctor).`
Issue: The text just established a "strong preference" for -ові/-еві endings for masculine people, but the very next example uses "-ю" (лікарю). This contradicts the rule and confuses learners.
Fix: Change `лікарю` to `лікареві`.

[DIMENSION] Vocabulary coverage [Major]
Location: `Інші корисні дієслова з давальним відмінком: довіряти (to trust), вибачати (to forgive), посміхатися (to smile), співчувати (to sympathize), та заздрити (to envy). Я довіряю другові (I trust my friend). Вона щиро посміхається дитині (she smiles at the child).`
Issue: The verbs `співчувати` and `заздрити` are presented as a bare list and lack contextual example sentences.
Fix: Add examples for them: `Ми співчуваємо колезі (we sympathize with the colleague). Вони нікому не заздрять (they do not envy anyone).`

[DIMENSION] Plan adherence [Minor]
Location: `Подзвони їй (her) завтра вранці, будь ласка.`
Issue: The plan explicitly requires demonstrating the negative form `не дзвони їй`, but the text provides an affirmative imperative.
Fix: Replace `Подзвони їй` with `Не дзвони їй`.

[DIMENSION] Engagement & tone [Minor]
Location: `Сьогодні ми вивчаємо дуже важливу тему української граматики. *(Today we are studying a very important topic of Ukrainian grammar.)*` and `Дуже важливо знати і використовувати правильну граматику. *(It is very important to know and use the correct grammar.)*`
Issue: These are empty filler sentences that add words but no pedagogical value.
Fix: Replace them with context-specific introductions.

[DIMENSION] Dialogue & conversation quality [Minor]
Location: `— Волонтер: Добре, тоді я дзвоню другові (I call the friend) Івану. Він має принести воду.`
Issue: The volunteer states they are going to call Ivan, but Ivan immediately speaks and hands over water, creating a disjointed flow.
Fix: Add a realization that Ivan is approaching so the prompt makes logical sense.

## Verdict: REVISE
This is a highly structured and beautifully comprehensive module that provides great depth well beyond the word count target. However, the inclusion of a hallucinated grammatical term ("досвідника"), a known Russian calque ("робити уроки"), and a pedagogical contradiction regarding the "-ові" noun ending require deterministic correction before it goes to learners.

<fixes>
- find: "## Мені подобається: Давальний відмінок досвідника (The Experiencer Dative with подобатися)"
  replace: "## Мені подобається: Давальний відмінок особи (The Experiencer Dative with подобатися)"
- find: "Мій малий син допомагає старшому братові (brother) робити уроки."
  replace: "Мій малий син допомагає старшому братові (brother) робити домашнє завдання."
- find: "Ми щиро дякуємо головному лікарю (the doctor)."
  replace: "Ми щиро дякуємо головному лікареві (the doctor)."
- find: "Вона щиро посміхається дитині (she smiles at the child)."
  replace: "Вона щиро посміхається дитині (she smiles at the child). Ми співчуваємо колезі (we sympathize with the colleague). Вони нікому не заздрять (they do not envy anyone)."
- find: "Подзвони їй (her) завтра вранці, будь ласка."
  replace: "Не дзвони їй (her) завтра вранці, будь ласка."
- find: "Сьогодні ми вивчаємо дуже важливу тему української граматики. *(Today we are studying a very important topic of Ukrainian grammar.)*"
  replace: "Ці дієслова вимагають особливої уваги. *(These verbs require special attention.)*"
- find: "Дуже важливо знати і використовувати правильну граматику. *(It is very important to know and use the correct grammar.)*"
  replace: "Граматика тут дуже специфічна. *(The grammar here is very specific.)*"
- find: "— Волонтер: Добре, тоді я дзвоню другові (I call the friend) Івану. Він має принести воду."
  replace: "— Волонтер: Добре, тоді я дзвоню другові (I call the friend) Івану. Хоча зачекай, він вже йде! Він має принести воду."
</fixes>
