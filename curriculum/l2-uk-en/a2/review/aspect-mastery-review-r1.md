## Linguistic Scan
No major Russianisms, Surzhyk, or Calques found. However, there is a morphological inaccuracy: the text claims that the sounds "ог" change to "ага" in `допомогти/допомагати`, which misrepresents the root vowel alternation (`о` -> `а`) combined with the addition of the imperfectivizing suffix `-а-`.

## Exercise Check
- `<!-- INJECT_ACTIVITY: group-sort-sort-aspect-pairs-by-formation-pattern-prefix-suffix-stem-change-suppletive -->`: Present and correctly placed after Section 1.
- `<!-- INJECT_ACTIVITY: match-up-match-imperfective-verbs-with-their-perfective-partners-from-the-30-pairs -->`: Present and correctly placed after Section 2.
- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-by-choosing-the-correct-aspect-based-on-context-sequence-interruption-habit-single-event -->`: Present and correctly placed after Section 3.
- `<!-- INJECT_ACTIVITY: quiz-read-a-mini-situation-and-choose-the-correct-aspect-form-with-justification -->`: Present and correctly placed after Section 3.
All markers match the plan's activity hints and are positioned logically after their relevant sections.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The text failed to use the exact 30 pairs organized into the specific groups defined in the plan (e.g., missed `робити/зробити`, `писати/написати` in Group A; missed `казати/сказати` in Group B). Dialogue 2 missed the explicitly planned future tense contrast (`Що ти будеш робити завтра?` vs `Що ти зробиш до п'ятниці?`). |
| 2. Linguistic accuracy | 8/10 | General usage is flawless, but the morphological claim that "звуки «ог» змінюються на «ага»" in `допомогти/допомагати` is a factual linguistic error. The alternation is the root vowel `о` -> `а` and the addition of a suffix. |
| 3. Pedagogical quality | 9/10 | Excellent explanations of aspect logic and clear minimal pairs ("Я варив борщ годину" vs "Я зварив борщ"), but slightly marred by the clunky morphology explanation. |
| 4. Vocabulary coverage | 8/10 | Uses the majority of the vocabulary naturally, but failed to include all 30 pairs exactly as stipulated in the plan's section 2 outline. |
| 5. Exercise quality | 10/10 | All markers are correctly placed, correspond to the plan's hints, and test the concepts just taught. |
| 6. Engagement & tone | 10/10 | Great teacher persona, encouraging and clear without useless filler or fluff. |
| 7. Structural integrity | 10/10 | Word count is 3056 (well above the 2000 target). All headers are present and logically ordered. |
| 8. Cultural accuracy | 10/10 | Contexts and examples are natural, appropriate, and authentic. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are highly natural and demonstrate the grammar perfectly, though the second dialogue deviated from the plan's required prompt. |

## Findings

[1. Plan adherence] [Major]
Location: `## 30 пар: Список і приклади`
Issue: The lists of 30 pairs deviate from the plan's exact requirements. Group A is missing `робити`, `писати`, `читати` and substituted them with other daily actions. Group B is missing `казати`, `записувати`. Group C has an extra pair (`телефонувати`).
Fix: Update the bulleted lists to match the exact 30 pairs requested in the plan's content outline.

[1. Plan adherence] [Major]
Location: `> — **Олег:** Що ти **плануєш** *(plan)* робити на вихідних?`
Issue: Dialogue 2 fails to include the specific grammatical contrast requested by the plan: `Що ти будеш робити завтра? (impf.) vs. Що ти зробиш до п'ятниці? (pf.)`.
Fix: Rewrite the opening of Dialogue 2 to explicitly include the future aspect contrast in the prompt questions.

[2. Linguistic accuracy] [Critical]
Location: `Один із найчастіших прикладів — це зміна звуків «ог» на «ага». Так працює пара **допомагати** *(to help, regularly)* та **допомогти** *(to help, once).*`
Issue: Claiming that the sound "ог" changes to "ага" is factually incorrect morphologically. The root vowel changes `о` -> `а` (`-мог-` -> `-маг-`) and the suffix `-а-` is added to form the imperfective.
Fix: Change the phrasing to correctly describe it as a change of vowels in the root.

## Verdict: REVISE
The module is very well-written and pedagogically strong, but it contains a critical morphological inaccuracy regarding stem changes and misses several specific requirements from the plan (exact 30 pairs lists, specific dialogue contrast). These must be fixed via find/replace.

<fixes>
- find: |
    Один із найчастіших прикладів — це зміна звуків «ог» на «ага». Так працює пара **допомагати** *(to help, regularly)* та **допомогти** *(to help, once)*.
  replace: |
    Один із найчастіших прикладів — це зміна голосних у корені слова (наприклад, «о» на «а»). Так працює пара **допомагати** *(to help, regularly)* та **допомогти** *(to help, once)*.
- find: |
    * **вмиватися** / **вмитися** *(to wash one's face / to finish washing)*
    * **одягатися** / **одягнутися** *(to get dressed / to finish dressing)*
    * **дивитися** / **подивитися** *(to watch / to take a look)*
  replace: |
    * **робити** / **зробити** *(to do / to finish doing)*
    * **писати** / **написати** *(to write / to finish writing)*
    * **читати** / **прочитати** *(to read / to finish reading)*
- find: |
    * **запитувати** / **запитати** *(to ask / to ask a question)*
    * **пояснювати** / **пояснити** *(to explain / to make clear)*
    * **вчити** / **вивчити** *(to learn / to memorize completely)*
    * **розуміти** / **зрозуміти** *(to understand / to grasp)*
    * **перекладати** / **перекласти** *(to translate / to finish translating)*
    * **писати** / **написати** *(to write / to finish writing)*
    * **читати** / **прочитати** *(to read / to finish reading)*
  replace: |
    * **питати** / **запитати** *(to ask / to ask a question)*
    * **пояснювати** / **пояснити** *(to explain / to make clear)*
    * **вчити** / **вивчити** *(to learn / to memorize completely)*
    * **розуміти** / **зрозуміти** *(to understand / to grasp)*
    * **перекладати** / **перекласти** *(to translate / to finish translating)*
    * **казати** / **сказати** *(to tell / to finish telling)*
    * **записувати** / **записати** *(to note down / to finish writing down)*
- find: |
    * **закінчувати** / **закінчити** *(to finish / to complete)*
    * **телефонувати** / **зателефонувати** *(to call / to make a phone call)*
  replace: |
    * **закінчувати** / **закінчити** *(to finish / to complete)*
- find: |
    > — **Олег:** Що ти **плануєш** *(plan)* робити на вихідних?
    > — **Анна:** Мені треба **купити** *(to buy)* телефон. Я хочу **поїхати** *(to go)* в центр.
    > — **Олег:** Я **буду дивитися** *(will be watching)* новий серіал. Я **почав** *(started)* його вчора.
  replace: |
    > — **Олег:** Що ти **будеш робити** *(will be doing)* завтра?
    > — **Анна:** Завтра я **буду відпочивати**. А що ти **зробиш** *(will get done)* до п'ятниці?
    > — **Олег:** До п'ятниці я **напишу** *(will finish writing)* статтю. А на вихідних я **буду дивитися** *(will be watching)* новий серіал. Я **почав** *(started)* його вчора.
</fixes>
