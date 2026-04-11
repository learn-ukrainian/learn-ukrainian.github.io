## Linguistic Scan
Linguistic errors found:
1. **Feminine Instrumental Endings Error**: The text claims the typical feminine endings for the instrumental case are `-ою`, `-ею`, `-єю`, but provides `зустріччю` as the example (which uses the 3rd declension `-ю` ending with consonant doubling). This is factually incorrect and contradicts the rule it's trying to teach. 
2. **False Russicism**: The text claims translating "in ten minutes" as "в десять хвилин" is a Russicism. It is actually a literal translation from English (an Anglicism or calque). In Russian, the equivalent is "через десять минут", exactly the same structure as Ukrainian.

## Exercise Check
Marker placement issues found:
The text includes 9 `<!-- INJECT_ACTIVITY: ... -->` markers, but the plan only contains 6 `activity_hints`. The extra markers (`fill-in-duration-types`, `clock-time-match`, `mixed-prep-quiz`) placed at the end of sections 3, 4, and 5 do not map to any planned activities and will cause pipeline generation issues.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The text missed multiple specific plan points: it omitted the reading passage in Section 2 (`Перед сніданком я роблю зарядку...`), failed to cover days of the week (`у понеділок`, `щопонеділка`) in Section 4, and omitted the common error checks for `*після п'яти` and `*слідуючий тиждень` in the summary. The dialogue also deviated from the specific scheduling events requested in the plan. |
| 2. Linguistic accuracy | 7/10 | Contains a critical grammatical contradiction regarding feminine instrumental endings (`-ою`/`-ею` vs `зустріччю`) and incorrectly flags the English calque "в десять хвилин" as a Russicism. |
| 3. Pedagogical quality | 8/10 | The explanation distinguishing `через` and `за` is exceptional. However, presenting a mismatched example for a grammatical rule (feminine instrumental) degrades pedagogical clarity. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary words were included naturally and contextually in the prose. |
| 5. Exercise quality | 8/10 | The writer generated 3 extra unmapped activity markers that do not align with the plan. |
| 6. Engagement & tone | 10/10 | Excellent, encouraging teacher persona ("Уявіть, що час — це безперервна лінія", "Перед тим, як щось сказати..."). No generic corporate filler. |
| 7. Structural integrity | 9/10 | Clean markdown and robust word count (5061 words). However, the first H2 heading contains an improper capitalization ("Та" instead of "та"). |
| 8. Cultural accuracy | 10/10 | Superb use of textbook references. Authentic linguistic authorities like Avramenko, Zabolotnyi, and Lytvinova are cited appropriately. |
| 9. Dialogue & conversation quality | 8/10 | The dialogue flows naturally but ignored the specific scheduling constraints (Monday rehearsal, weekend excursion) from the plan. |

## Findings
[DIMENSION 1] [Major]
Location: Section 4 "Позначення часу доби і пір року"
Issue: The plan explicitly required teaching days of the week and frequency (`у понеділок`, `в п'ятницю`, `щопонеділка`, `цього понеділка`), but this was completely omitted from the section.
Fix: Insert a paragraph explaining days of the week at the end of Section 4.

[DIMENSION 1] [Major]
Location: Section 2 "Перед, після, до, під час"
Issue: The specific reading passage about a daily schedule (`Перед сніданком... Під час обіду...`) was omitted in favor of early placement of the dialogue.
Fix: Insert the reading passage after the grammatical explanation of cases.

[DIMENSION 1] [Minor]
Location: Section 6 "Підсумок"
Issue: The plan required noting common errors `*після п'яти` and `*слідуючий тиждень`, which were completely missed in the text.
Fix: Add these common errors to the bullet points and paragraph text in the summary.

[DIMENSION 2] [Critical]
Location: Section 2 "Для іменників жіночого роду типовими є закінчення **-ою**, **-ею** або **-єю**: «Я дуже хвилювалася **перед зустріччю** з директором»"
Issue: Grammatical contradiction. The word `зустріччю` takes the `-ю` ending (3rd declension), not `-ою`/`-ею`/`-єю` (1st declension). The example violates the rule it's trying to demonstrate.
Fix: Distinguish between 1st declension (`-ою`/`-ею`) and 3rd declension (`-ю`) feminine endings.

[DIMENSION 2] [Major]
Location: Section 1 "Вони можуть сказати щось на кшталт «Я точно буду тут *в десять хвилин*. Це серйозна граматична помилка і помітний русизм *(Russicism)*."
Issue: Factual error. Translating "in ten minutes" as "в десять хвилин" is an Anglicism (literal translation), not a Russicism. Russian uses "через десять минут" just like Ukrainian.
Fix: Change "русизм" to "буквальний переклад з англійської".

[DIMENSION 5] [Minor]
Location: Sections 3, 4, and 5
Issue: 3 extra injected activity markers were generated that do not map to the plan's 6 `activity_hints`.
Fix: Remove the unmapped markers.

[DIMENSION 7] [Minor]
Location: First H2 Heading
Issue: Improper capitalization of the conjunction "Та".
Fix: Lowercase "Та" to "та".

## Verdict: REVISE
The module exceeds the word count and features excellent, engaging explanations. However, it contains a critical grammatical error regarding feminine instrumental endings, a factual error regarding a supposed Russicism, and completely misses several required points from the plan. Fixes are provided below to correct the structural and linguistic issues.

<fixes>
- find: "## Через + Зн.в. Та за + Зн.в."
  replace: "## Через + Зн.в. та за + Зн.в."
- find: "Вони можуть сказати щось на кшталт «Я точно буду тут *в десять хвилин*». Це серйозна граматична помилка і помітний русизм *(Russicism)*."
  replace: "Вони можуть сказати щось на кшталт «Я точно буду тут *в десять хвилин*». Це серйозна граматична помилка та буквальний переклад з англійської *(calque)*."
- find: "Для іменників жіночого роду типовими є закінчення **-ою**, **-ею** або **-єю**: «Я дуже хвилювалася **перед зустріччю** з директором» *(I was very nervous before the meeting with the director)*."
  replace: "Для іменників жіночого роду першої відміни типовими є закінчення **-ою**, **-ею** або **-єю** («перед лекцією»), а для третьої відміни — закінчення **-ю**: «Я дуже хвилювалася **перед зустріччю** з директором» *(I was very nervous before the meeting with the director)*."
- insert_after: "під час обід**у**, під час лекці**ї** (Родовий відмінок)."
  text: "\n\nПрочитайте цей короткий розклад дня і зверніть увагу на часові прийменники: «**Перед сніданком** я роблю зарядку. **Під час обіду** читаю новини. **Після роботи** гуляю в парку. **До вечері** намагаюся все зробити». Спробуйте самостійно визначити відмінок кожного виділеного іменника, спираючись на наші правила."
- find: "<!-- INJECT_ACTIVITY: fill-in-duration-types -->"
  replace: ""
- insert_after: "або **чверть до восьмої**."
  text: "\n\nТакож варто звернути увагу на дні тижня. Коли ми говоримо про одноразову подію в певний день, ми використовуємо прийменник «у» або «в» зі Знахідним відмінком: **у понеділок** *(on Monday)*, **у середу**, **в п'ятницю**. Якщо ж ми вказуємо на конкретний тиждень, додаючи займенник, прийменник зникає, і ми використовуємо Родовий відмінок: **цього понеділка** *(this Monday)*, **минулої середи** *(last Wednesday)*. Для регулярних подій ми використовуємо прислівники з часткою «що»: **щопонеділка** *(every Monday)*, **щосереди** *(every Wednesday)*. Наприклад: «У понеділок я йду до лікаря, але загалом я працюю вдома щопонеділка»."
- find: "<!-- INJECT_ACTIVITY: clock-time-match -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: mixed-prep-quiz -->"
  replace: ""
- find: "Правильний варіант: **за десять хвилин шоста** або просто **за десять шоста** *(ten to six)*."
  replace: "Правильний варіант: **за десять хвилин шоста** або просто **за десять шоста** *(ten to six)*. Також не кажіть «після п'яти» — правильно говорити **після п'ятої** *(after five o'clock)*."
- find: "Правильно казати: **цього року** *(this year)* або **минулого року** *(last year)*."
  replace: "Правильно казати: **цього року** *(this year)* або **минулого року** *(last year)*. Ще один поширений русизм — словосполучення «слідуючий тиждень». В українській мові слова «слідуючий» не існує, тому завжди кажіть **наступний тиждень** *(next week)*."
</fixes>
