## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym mix-ups, or forbidden Russian characters found.

Critical factual error:
- In **Порядкові числівники: -ий та -ій**, the sentence **«В українській мові кожне число має дві форми.»** is wrong. The textbook evidence returned by local search distinguishes **кількісні** and **порядкові**, and within **кількісні** also separates **власне кількісні / дробові / збірні / неозначено-кількісні**. This sentence teaches a false classification.

## Exercise Check
Markers found:
- `fill-in-ordinals`
- `fill-in-decline-in-context`
- `quiz-noun-agreement`
- `sort-numeral-cases`
- `match-up-expressions`

Checks:
- All 4 plan hint types are represented: fill-in, quiz, group-sort, match-up.
- Marker placement is mostly sensible and spread through the module.
- No inline DSL exercise blocks are present, so only marker placement can be checked here.
- One placement problem: the plan’s fill-in focus is **“Decline ordinal numerals in context (dates, addresses)”**, but `<!-- INJECT_ACTIVITY: fill-in-ordinals -->` appears before the address-use material in **Числа навколо нас**. If the downstream YAML follows the hint literally, part of that exercise will test address usage before it is taught.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned sections are present and the required vocabulary is well represented, but the ordinal section only demonstrates selected forms: **«п'ятого… п'ятому… п'ятим… на п'ятому»** instead of delivering the objective **“decline ordinal numerals in all cases”**. The fill-in marker also arrives before address-context teaching. |
| 2. Linguistic accuracy | 6/10 | Most Ukrainian forms are sound, but **«В українській мові кожне число має дві форми.»** is factually wrong. Local textbook search shows the standard school classification is broader than just cardinal vs ordinal. |
| 3. Pedagogical quality | 7/10 | The module has a PPP-like flow and many examples, but the teaching does not fully support the stated objective before practice: the ordinal explanation gives partial paradigms, not an all-case walkthrough. |
| 4. Vocabulary coverage | 9/10 | Required plan vocabulary is integrated naturally across prose and dialogues: **числівник, порядковий, кількісний, перший, третій, один, скільки, кілограм, коштувати, вік** all appear in context. |
| 5. Exercise quality | 8/10 | The marker set is strong and maps well to the plan overall, but the planned fill-in focus **“dates, addresses”** is only partially prepared before `fill-in-ordinals`. Actual YAML logic is not shown, so distractor quality cannot be verified here. |
| 6. Engagement & tone | 8/10 | The sports-day and market contexts help, and the examples are concrete, but the prose is often explanation-heavy rather than tightly example-driven. |
| 7. Structural integrity | 9/10 | Clean markdown, all major H2 sections present and ordered correctly, and the pipeline word count is **2851**, safely above target. |
| 8. Cultural accuracy | 9/10 | The module stays Ukrainian-centered and uses appropriate examples such as **День Незалежності**, **Тарас Шевченко**, and **Хрещатик** without Russian-comparison framing. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers and real situations are present. The market dialogue is functional and clear; the opening sports dialogue is slightly list-like rather than fully natural. |

## Findings
[2. Linguistic accuracy] [SEVERITY: critical]  
Location: **Порядкові числівники: -ий та -ій**, sentence **«В українській мові кожне число має дві форми.»**  
Issue: False grammar claim. Ukrainian school grammar does not reduce numerals to only two forms; besides **порядкові**, quantitative numerals are subdivided into **власне кількісні, дробові, збірні, неозначено-кількісні**.  
Fix: Replace it with scope-limited wording: **«В українській мові для цієї теми важливо розрізняти два основні типи числівників.»**

[1. Plan adherence] [SEVERITY: major]  
Location: **Порядкові числівники: -ий та -ій**, paragraph beginning **«Більшість порядкових числівників мають тверде закінчення…»**  
Issue: The plan objective says the learner should decline ordinal numerals **“in all cases”**, but the section only walks through selected forms: **«п'ятого», «п'ятому», «п'ятим», «на п'ятому»** plus one feminine form.  
Fix: Expand this paragraph to include accusative, vocative, and a compact feminine/plural paradigm.

[5. Exercise quality] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in-ordinals -->` after the date paragraph in the first section  
Issue: The plan’s fill-in focus is **dates, addresses**, but address-context usage is taught later in **Числа навколо нас**. If the activity generator follows the hint literally, the learner may be tested on address usage too early.  
Fix: Add one short address-context ordinal example before this marker so both date and address usage are taught before practice.

## Verdict: REVISE
REVISE. There is one critical factual/linguistic error and two major delivery issues. Several dimensions fall below 9, and the critical grammar claim alone blocks PASS.

<fixes>
- find: "В українській мові кожне число має дві форми."
  replace: "В українській мові для цієї теми важливо розрізняти два основні типи числівників."
- find: "Більшість порядкових числівників мають тверде закінчення **-ий**. Вони відмінюються так само, як прикметники твердої групи. Візьмемо для прикладу слово «п'ятий». У називному відмінку чоловічого роду це «п'ятий». Коли ми змінюємо відмінок, змінюється лише закінчення. У родовому відмінку ми кажемо «п'ятого», а у давальному — «п'ятому». В орудному відмінку форма буде «п'ятим», а в місцевому — «на п'ятому». Для жіночого роду початкова форма — це «п'ята». В орудному відмінку ми використовуємо форму «п'ятою»."
  replace: "Більшість порядкових числівників мають тверде закінчення **-ий**. Вони відмінюються так само, як прикметники твердої групи. Візьмемо для прикладу слово «п'ятий». У чоловічому роді маємо: називний — «п'ятий», родовий — «п'ятого», давальний — «п'ятому», знахідний для неістот — знову «п'ятий», для істот — «п'ятого», орудний — «п'ятим», місцевий — «на п'ятому», кличний — «п'ятий». Для жіночого роду бачимо той самий принцип: «п'ята», «п'ятої», «п'ятій», «п'яту», «п'ятою». У множині вживаємо форми «п'яті», «п'ятих», «п'ятим», «п'ятими»."
- find: "Порядкові числівники дуже часто використовуються для позначення дат. Коли ми говоримо про конкретний день, ми відповідаємо на питання «коли?». Тоді ми завжди використовуємо порядковий числівник у родовому відмінку. Наприклад, ми скажемо «двадцять першого березня» або «другого квітня». У складених числівниках змінюється лише останнє слово. Погляньмо на велике число «сто сорок п'ятий». Ми скажемо: «Я щойно вийшов зі сто сорок п'ятого кабінету»."
  replace: "Порядкові числівники дуже часто використовуються для позначення дат. Коли ми говоримо про конкретний день, ми відповідаємо на питання «коли?». Тоді ми використовуємо порядковий числівник у родовому відмінку. Наприклад, ми скажемо «двадцять першого березня» або «другого квітня». У складених числівниках змінюється лише останнє слово. Погляньмо на велике число «сто сорок п'ятий». Ми скажемо: «Я щойно вийшов зі сто сорок п'ятого кабінету». Так само порядкові числівники зручно тренувати в адресах і місцях у будинку: «ми живемо на третьому поверсі» або «зустрінемося в двадцять першій аудиторії»."
</fixes>