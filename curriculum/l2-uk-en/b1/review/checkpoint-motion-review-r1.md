## Linguistic Scan
No major Russianisms found in the general vocabulary (proper nouns like Дніпро, Карпати, Києва are correct). However, one critical pedagogical calque was identified: the text teaches "мова йде про" as a "спеціальна конструкція" (special construction) to use, but according to Antonenko-Davydovych's style guide, this is a calque. The natural Ukrainian construction is "йдеться про" or "мовиться про".

## Exercise Check
**CRITICAL FAILURE.** The writer completely ignored the `activity_hints` array in the plan (which specified exactly 6 activities: quiz, fill-in, match-up, error-correction, group-sort, free-write). Instead, the writer hallucinated 19 different `INJECT_ACTIVITY` markers with broken syntax, placing entire activity descriptions inside the ID field (e.g., `<!-- INJECT_ACTIVITY: quiz, Case agreement: 8 sentences... -->`). 

Additionally, the plan explicitly required a self-assessment framework to be placed *after each block*. The writer introduced the concept in the first paragraph but failed to actually place the self-assessment forms at the end of the blocks.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The text hallucinates 19 incorrect activity markers instead of the 6 planned ones. It also fails to place the self-assessment framework "after each block" as required. |
| 2. Linguistic accuracy | 8/10 | The text incorrectly teaches the calque "мова йде про" as a special standard construction instead of the correct "йдеться про". Everything else, including preposition/case government and prefix semantics, is very well explained. |
| 3. Pedagogical quality | 8/10 | Strong grammatical explanations with clear examples. However, teaching a calque ("мова йде про") as the target construction is a serious flaw. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary from the plan is integrated organically. |
| 5. Exercise quality | 2/10 | The `INJECT_ACTIVITY` markers use completely broken syntax instead of standard IDs, and the writer spammed 19 markers instead of the 6 planned ones. |
| 6. Engagement & tone | 4/10 | Heavy use of meta-commentary and generic hype, especially in the intro: "Це справжня нервова система української граматики...", "ми свідомо використовуємо науково-навчальний стиль мовлення...". The text frequently tells instead of shows. |
| 7. Structural integrity | 6/10 | The word count is 5177 words, which is nearly 30% over the 4000-word target. The text is bloated with meta-commentary. |
| 8. Cultural accuracy | 10/10 | Authentic proverbs ("Сім разів відміряй — один відріж") and good cultural context for travel in Ukraine. |
| 9. Dialogue & conversation quality | 9/10 | The oral exam dialogue is a realistic academic situation and successfully integrates the grammar points. |

## Findings

[Plan adherence] [Major]
Location: Throughout the module.
Issue: The plan specified 6 specific `activity_hints`, but the text hallucinates 19 `INJECT_ACTIVITY` markers with broken syntax (putting descriptions in the ID field).
Fix: Replace all 19 markers with the 6 correct markers from the plan, placed strategically at the end of the blocks.

[Plan adherence] [Major]
Location: End of Blocks 1-6.
Issue: The plan required a "Self-assessment framework: after each block, rate your confidence". The text introduces this idea but fails to actually place the forms at the end of the blocks.
Fix: Inject a self-assessment line at the end of each block.

[Linguistic accuracy] [Critical]
Location: Блок 5 (paragraph 2): "...ми завжди використовуємо спеціальну конструкцію: **мова йде про...**"
Issue: "Мова йде про" is a recognized calque/Russicism (Антоненко-Давидович confirms it). The correct, natural Ukrainian construction to teach is "йдеться про". Teaching the calque as the official rule is a critical error.
Fix: Change "мова йде про..." to "йдеться про...".

[Engagement & tone] [Major]
Location: Вступ (paragraphs 1 & 2).
Issue: The introduction is full of meta-commentary ("ми свідомо використовуємо науково-навчальний стиль") and generic hype ("справжня нервова система").
Fix: Delete the meta-commentary and hype to make the tone direct and professional.

## Verdict: REVISE
The module contains an excellent and thorough grammatical breakdown of motion verbs. However, the writer completely failed the exercise injection protocol and bloated the text with meta-commentary. The fixes below correct the calque, clean up the tone, inject the missing self-assessments, and repair the broken activity markers.

<fixes>
- find: "Ця **контрольна робота** *(assessment)* є підсумком масштабного і надзвичайно важливого етапу. Вона комплексно перевіряє ваші знання матеріалу з модулів від двадцять сьомого до тридцять шостого. Це четвертий етап рівня B1, який ми заслужено називаємо «Всесвіт дієслів руху»."
  replace: "Ця **контрольна робота** *(assessment)* комплексно перевіряє ваші знання матеріалу з модулів від двадцять сьомого до тридцять шостого («Всесвіт дієслів руху»)."
- find: "Концепція напрямку та руху — це справжня нервова система української граматики на цьому етапі навчання. Глибоке розуміння того, як **односпрямований** *(unidirectional)* та **різноспрямований** *(multidirectional)* рух органічно поєднується з префіксами напрямку, дає вам велику свободу. Це дозволяє вам вільно та максимально точно описувати будь-яку **подорож** *(journey)*, зміну локації або звичайну щоденну рутину."
  replace: "Розуміння того, як **односпрямований** *(unidirectional)* та **різноспрямований** *(multidirectional)* рух поєднується з префіксами напрямку, дозволяє вам вільно та точно описувати будь-яку **подорож** *(journey)*, зміну локації або звичайну щоденну рутину."
- find: "Для цієї роботи ми свідомо використовуємо **науково-навчальний** *(scientific-educational)* стиль мовлення у всіх поясненнях та інструкціях. Це означає, що всі тексти будуть максимально чіткими, структурованими, академічними та подаватимуться виключно українською мовою. Виконайте всі запропоновані **завдання** *(exercises)* послідовно, крок за кроком."
  replace: "Виконайте всі запропоновані **завдання** *(exercises)* послідовно, крок за кроком."
- find: "спеціальну конструкцію: **мова йде про...** *(it is about / the talk goes about...)* нові фінансові"
  replace: "спеціальну конструкцію: **йдеться про...** *(it is about / the talk goes about...)* нові фінансові"
- find: "Правильний та усвідомлений вибір найбільш влучного синоніма яскраво демонструє ваш справжній, глибокий рівень практичного володіння мовою."
  replace: "Правильний та усвідомлений вибір найбільш влучного синоніма яскраво демонструє ваш справжній, глибокий рівень практичного володіння мовою.\n\n**Самооцінка (Блок 1):** [ ] Впевнено | [ ] Потребую повторення | [ ] Не розумію"
- find: "Розуміння цих парних просторових зв'язків дозволить вам будувати точні маршрути без помилок."
  replace: "Розуміння цих парних просторових зв'язків дозволить вам будувати точні маршрути без помилок.\n\n**Самооцінка (Блок 2):** [ ] Впевнено | [ ] Потребую повторення | [ ] Не розумію"
- find: "Завжди враховуйте цю важливу специфіку фізичного простору під час ваших розповідей."
  replace: "Завжди враховуйте цю важливу специфіку фізичного простору під час ваших розповідей.\n\n**Самооцінка (Блок 3):** [ ] Впевнено | [ ] Потребую повторення | [ ] Не розумію"
- find: "Наприклад, відомі і дуже сміливі мандрівники часто мріють **об'їхати** *(to travel around)* весь світ на своєму кораблі."
  replace: "Наприклад, відомі і дуже сміливі мандрівники часто мріють **об'їхати** *(to travel around)* весь світ на своєму кораблі.\n\n**Самооцінка (Блок 4):** [ ] Впевнено | [ ] Потребую повторення | [ ] Не розумію"
- find: "Знання і розуміння таких давніх культурних висловів робить вашу щоденну українську мову справді природною, багатою, глибокою та живою."
  replace: "Знання і розуміння таких давніх культурних висловів робить вашу щоденну українську мову справді природною, багатою, глибокою та живою.\n\n**Самооцінка (Блок 5):** [ ] Впевнено | [ ] Потребую повторення | [ ] Не розумію"
- find: "Після цього я **обійду** *(will walk around)* місцевий парк, щоб не йти через темні алеї, і нарешті швидко **прийду** *(will arrive)* додому."
  replace: "Після цього я **обійду** *(will walk around)* місцевий парк, щоб не йти через темні алеї, і нарешті швидко **прийду** *(will arrive)* додому.\n\n**Самооцінка (Блок 6):** [ ] Впевнено | [ ] Потребую повторення | [ ] Не розумію"
- find: "<!-- INJECT_ACTIVITY: quiz, Case agreement: 8 sentences requiring correct ending for nouns after prepositions (e.g., \"навпроти будинку\", \"над головою\"). -->"
  replace: "<!-- INJECT_ACTIVITY: quiz -->"
- find: "<!-- INJECT_ACTIVITY: quiz, Preposition choice: 6 sentences choosing the most natural synonym (e.g., \"біля\" vs \"поруч з\") based on context clues. -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz, Preposition vs Adverb: 4 sentence pairs to distinguish function (e.g., \"Він стояв навпроти\" vs \"Він стояв навпроти кінотеатру\"). -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz, Verb choice: 8 sentences selecting between pairs like нести/носити or везти/возити based on temporal markers. -->"
  replace: "<!-- INJECT_ACTIVITY: error-correction -->"
- find: "<!-- INJECT_ACTIVITY: fill-in, Conjugation: Full present tense paradigms for 4 irregular base verbs (ходити, їхати, бігти, летіти). -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in, Prepositions of direction: 4 sentences choosing between \"в\", \"на\", \"до\", \"з\", \"від\" for specific travel contexts. -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz, Prefix selection: 8 sentences choosing between arrival (при/до) and departure (пі/від) prefixes. -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort -->"
- find: "<!-- INJECT_ACTIVITY: fill-in, Aspect pairs: 6 items converting perfective prefixed verbs to imperfective (e.g., приїхати -> приїжджати). -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: group-sort, Journey ordering: Arrange 6 sentences into a logical travel sequence (Start -> Transit -> Arrival). -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz, Prefix selection: 10 sentences testing all 6 prefixes in this section (e.g., \"Він ___йшов (passed) повз мене\"). -->"
  replace: "<!-- INJECT_ACTIVITY: match-up -->"
- find: "<!-- INJECT_ACTIVITY: match-up, Opposite pairs: 6 items matching spatial opposites (зайти/вийти, підійти/відійти, заїхати/виїхати). -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in, Preposition + case: 6 items completing sentences like \"зайти ___ (into) будинок\", \"проїхати ___ (past) театр\". -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz, Air/water motion: 6 sentences testing prefixed forms of \"летіти\" and \"пливти\" in travel contexts. -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz, Literal vs Figurative: 8 sentences to categorize usage (e.g., \"Годинник іде\" vs \"Хлопчик іде\"). -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in, Figurative expression completion: 4 items (e.g., \"Справи ___ (go) вгору\"). -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz, Reading comprehension: 6 questions testing details of the narrative's motion and route. -->"
  replace: "<!-- INJECT_ACTIVITY: free-write -->"
- find: "<!-- INJECT_ACTIVITY: fill-in, Dialogue completion: 6 exchanges in a station dialogue where motion verbs are missing. -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: free-write, Travel Plan: Write a 6-sentence plan for a weekend trip using 8 prefixes and 5 transport terms. -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in, Один день із життя мандрівника: 10 blanks testing prefixes, base verbs, and case agreement. -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in -->"
</fixes>
