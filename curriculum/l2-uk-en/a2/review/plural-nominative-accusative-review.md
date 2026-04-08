## Linguistic Scan
Errors found:
1. **Russianisms/Calques**: "робити дію" is non-standard/calqued grammatical terminology. In Ukrainian, subjects "виконують дію" (perform an action). 
2. **Hallucination**: "підказник" — an unattested/non-standard word not found in VESUM or SUM-11. The correct equivalent for "clue/indicator" is "підказка" (feminine) or "орієнтир". 

No Russian letters found. No Surzhyk. Genders and case endings are correct across all four declension paradigms. 

## Exercise Check
All inline exercise markers are present, mapped to the correct concepts taught directly before them, and perfectly align with the `activity_hints` from the plan:
1. `<!-- INJECT_ACTIVITY: fill-in-nom-plural -->` (Tests Nom plural formation after the declension review)
2. `<!-- INJECT_ACTIVITY: sort-animate-inanimate -->` (Tests sorting after the rule is introduced)
3. `<!-- INJECT_ACTIVITY: quiz-acc-plural-choice -->` (Tests choice between Nom.Pl and Gen.Pl)
4. `<!-- INJECT_ACTIVITY: error-correction-plural -->` (Tests error correction at the end)

Total markers: 4 (Matches plan requirement exactly).

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module skipped the required `у/в (direction)` preposition from the plan: "combine with prepositions that take Accusative (через, на (direction), у/в (direction), про)". The preposition paragraph completely ignored `у/в`. It also missed the exact targeted contrast for the dialogue: "Nom plural: лев→леви. Acc animate plural: жираф→жирафів" (used nominative `жирафи` instead). |
| 2. Linguistic accuracy | 8/10 | The word "підказник" is an AI hallucination: "Контекст речення — це завжди наш найкращий граматичний підказник." Grammatical terminology is clunky: "Тут живі люди активно роблять дію" (must be "виконують дію"). |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. It uses a strong analogy ("golden rule", "split concepts in your mind") and provides abundant contrasting examples for animate vs. inanimate Accusative (e.g., "Студенти читають" vs. "бачу студентів"). English metalanguage is well-balanced. |
| 4. Vocabulary coverage | 9/10 | Covered almost all required/recommended words ("множина", "люди", "діти", "закінчення"), but missed the recommended word "чергування", using the English "consonant alternation" without giving the Ukrainian equivalent. |
| 5. Exercise quality | 10/10 | Markers perfectly track the pedagogical flow and the explicit instructions from the `activity_hints`. |
| 6. Engagement & tone | 9/10 | Very supportive, natural teacher persona. Minor deduction for slight filler ("Сьогодні ми зробили великий крок уперед", "Українська мова має дуже логічну та прозору структуру"). |
| 7. Structural integrity | 10/10 | 2412 words (solidly above the 2000 target). All H2 headings present. Markdown is clean and robust. |
| 8. Cultural accuracy | 10/10 | Uses natural, realistic situations (zoo, university, outdoor market). Decolonized perspective. |
| 9. Dialogue & conversation quality | 9/10 | The "zoo" and "market" dialogues are highly natural. Minor deduction for the "zoo" dialogue missing the accusative animate form "жирафів" that was explicitly requested by the plan. |

## Findings

[Plan adherence] [Critical]
Location: `> — Донька: Я бачу високі зелені дерева. А біля дерев стоять жирафи (giraffes).`
Issue: The plan explicitly asked to contrast `леви` (Nom) with `жирафів` (Acc. Animate) in the first dialogue. The writer used `жирафи` (Nom) instead, missing a critical early exposure opportunity.
Fix: Change the line to `Ти бачиш тих жирафів (giraffes)?`

[Plan adherence] [Critical]
Location: `Прийменник через (through, across) показує активний рух... Прийменник на (onto, for) часто показує час... Прийменник про (about) показує головну тему розмови...`
Issue: The plan strictly required covering the prepositions `через, на (direction), у/в (direction), про`. The writer completely omitted `у/в` from the list of Accusative direction prepositions.
Fix: Add the `у/в` preposition and its example to the paragraph.

[Linguistic accuracy] [Critical]
Location: `Контекст речення — це завжди наш найкращий граматичний підказник.`
Issue: "підказник" is a hallucinated/non-standard derivative not found in VESUM or dictionaries. The correct feminine noun "підказка" must be used, which requires changing the gender agreement of the surrounding adjectives.
Fix: Change to `Контекст речення — це завжди наша найкраща граматична підказка.`

[Linguistic accuracy] [Major]
Location: `слово «машини» самостійно робить дію.` and `Тут живі люди активно роблять дію, а неживі предмети її отримують.`
Issue: "Робити дію" is awkward, calqued terminology. In standard Ukrainian grammar terminology, a subject "виконує дію".
Fix: Change "робить" to "виконує" and "роблять" to "виконують".

## Verdict: REVISE
The module is very well-structured and grammatically accurate regarding the complex plurals and declensions. However, the missed `у/в` preposition from the plan, the hallucinated word `підказник`, and the calqued `робити дію` terminology require deterministic find/replace fixes.

<fixes>
- find: "> — Донька: Я бачу високі зелені дерева. А біля дерев стоять жирафи (giraffes)."
  replace: "> — Донька: Я бачу високі зелені дерева. Ти бачиш тих жирафів (giraffes)?"
- find: "Прийменник через (through, across) показує активний рух: «Ми довго їдемо через високі гори (mountains)». Прийменник на (onto, for) часто показує час: «Вони планують поїздку на наступні вихідні (weekend)». Прийменник про (about) показує головну тему розмови: «Мої друзі говорять про нові українські фільми (movies)»."
  replace: "Прийменник через (through, across) показує активний рух: «Ми довго їдемо через високі гори (mountains)». Прийменник на (onto, for) часто показує час: «Вони планують поїздку на наступні вихідні (weekend)». Прийменники у та в (into, to) позначають напрямок руху: «Студенти йдуть у світлі аудиторії (classrooms)». Прийменник про (about) показує головну тему розмови: «Мої друзі говорять про нові українські фільми (movies)»."
- find: "Контекст речення — це завжди наш найкращий граматичний підказник."
  replace: "Контекст речення — це завжди наша найкраща граматична підказка."
- find: "слово «машини» самостійно робить дію."
  replace: "слово «машини» самостійно виконує дію."
- find: "Тут живі люди активно роблять дію, а неживі предмети її отримують."
  replace: "Тут живі люди активно виконують дію, а неживі предмети її отримують."
</fixes>
