## Linguistic Scan
Errors found:
1. "Давайте подивимося" — Russianism (calque of "давайте посмотрим").
2. "Давайте перевіримо" — Russianism (calque of "давайте проверим").
3. "проект" — Orthography error (according to the 2019 Pravopys §126, words with the Latin root -ject- must be spelled with 'є': проєкт).

## Exercise Check
Injected markers found:
- `<!-- INJECT_ACTIVITY: quiz-aspect-identification -->`
- `<!-- INJECT_ACTIVITY: match-up-aspect-pairs -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-simple-future-form-based-on-aspect -->`
- `<!-- INJECT_ACTIVITY: group-sort-future-forms -->`
- `<!-- INJECT_ACTIVITY: fill-in-future-forms -->`
- `<!-- INJECT_ACTIVITY: error-correction-aspect-tense -->`
- `<!-- INJECT_ACTIVITY: free-write-future-plans -->`

**Issues:** 7 markers were injected instead of the planned 6. The plan requires exactly one `fill-in` activity, but the writer injected two separate markers. The extra marker in Section 2 will be removed to align with the plan.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | DEDUCT for missing content_outline points: Section 4 is missing the "dialogue between two friends planning a trip". Section 5 is missing the "extended practice: learners retell a Ukrainian folk tale". Section 6 is missing the "learners complete a letter to a friend about summer plans". |
| 2. Linguistic accuracy | 7/10 | DEDUCT for Critical Russianisms ("Давайте подивимося", "Давайте перевіримо") and one Orthography error ("проект" instead of "проєкт"). |
| 3. Pedagogical quality | 9/10 | REWARD for excellent PPP flow and clear explanations of aspect limitations (e.g. perfective lacking present tense). |
| 4. Vocabulary coverage | 10/10 | REWARD for integrating all required and recommended vocabulary naturally. |
| 5. Exercise quality | 8/10 | DEDUCT for injecting 7 markers instead of the planned 6 (two `fill-in` markers were used). |
| 6. Engagement & tone | 9/10 | REWARD for a natural and encouraging tone without gamified language. |
| 7. Structural integrity | 10/10 | REWARD for clean markdown, correct section order, and a 4830 word count that comfortably exceeds the 4000-word target. |
| 8. Cultural accuracy | 10/10 | REWARD for culturally appropriate references (Kharkiv university, Sosyura). |
| 9. Dialogue & conversation quality | 9/10 | REWARD for the well-structured planning committee dialogue, but missing the other required dialogues. |

## Findings

[1. Plan adherence] [major]
Location: Section 4 (Складена (аналітична) форма майбутнього часу)
Issue: Missing the plan point "Reading practice: dialogue between two friends planning a trip, using all three future forms."
Fix: Inject a short dialogue between two friends at the end of the section.

[1. Plan adherence] [major]
Location: Section 5 (Вид і час — як вони працюють разом)
Issue: Missing the plan point "Extended practice: learners retell a Ukrainian folk tale using correct aspect-tense combinations."
Fix: Inject a short folk tale example at the end of the section.

[1. Plan adherence] [major]
Location: Section 6 (Дієвідмінювання у майбутньому часі)
Issue: Missing the plan point "Contextual practice: learners complete a letter to a friend about summer plans..."
Fix: Inject a short letter about summer plans at the end of the section.

[2. Linguistic accuracy] [critical]
Location: "Давайте подивимося, як це працює з дієсловом «працювати»."
Issue: Russianism. The imperative mood for the 1st person plural is formed without "давайте".
Fix: Change to "Подивімося, як це працює з дієсловом «працювати»."

[2. Linguistic accuracy] [critical]
Location: "Давайте перевіримо ваші знання."
Issue: Russianism.
Fix: Change to "Перевірмо ваші знання."

[2. Linguistic accuracy] [critical]
Location: "Ми будемо обговорювати наш новий проект протягом двох годин."
Issue: Orthography error. According to the 2019 Pravopys (§126), words with the Latin root -ject- must be spelled with 'є'.
Fix: Change "проект" to "проєкт".

[5. Exercise quality] [minor]
Location: "<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-simple-future-form-based-on-aspect -->"
Issue: The plan only requires 6 activities, including one `fill-in`. The writer injected a second `fill-in` marker which will cause pipeline errors.
Fix: Remove the extra marker in Section 2.

## Verdict: REVISE
The module contains critical linguistic errors (Russianisms and a 2019 Pravopys orthography error) and is missing several mandated content outline points (dialogues and folk tale practice). These must be corrected before the module can pass.

<fixes>
- find: "Давайте подивимося, як це працює з дієсловом «працювати»."
  replace: "Подивімося, як це працює з дієсловом «працювати»."
- find: "Давайте перевіримо ваші знання."
  replace: "Перевірмо ваші знання."
- find: "Ми будемо обговорювати наш новий проект протягом двох годин."
  replace: "Ми будемо обговорювати наш новий проєкт протягом двох годин."
- find: "<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-simple-future-form-based-on-aspect -->\n\n## Складна"
  replace: "## Складна"
- find: "<!-- INJECT_ACTIVITY: fill-in-future-forms -->"
  replace: "А зараз прочитайте діалог двох друзів, які планують подорож. Зверніть увагу на використання різних форм майбутнього часу:\n\n> — **Олена:** Привіт! Ми поїдемо в Карпати наступного тижня? *(Will we go to the Carpathians next week?)*\n> — **Марк:** Так, я якраз буду купувати квитки на потяг. *(Yes, I will be buying the train tickets right now.)*\n> — **Олена:** Чудово! Я складу маршрут нашої мандрівки. *(Great! I will put together the route for our trip.)*\n> — **Марк:** А я шукатиму нам житло. Я буду писати власникам готелів сьогодні ввечері. *(And I will be looking for accommodation for us. I will be writing to hotel owners tonight.)*\n> — **Олена:** Домовилися. Я впевнена, що ми відпочинемо ідеально. *(Agreed. I am sure we will rest perfectly.)*\n\n<!-- INJECT_ACTIVITY: fill-in-future-forms -->"
- find: "<!-- INJECT_ACTIVITY: error-correction-aspect-tense -->"
  replace: "Щоб краще зрозуміти це, прочитайте короткий переказ української народної казки «Котигорошко», звертаючи увагу на види дієслів:\n\nЖили собі дід та баба. Вони постійно сумували (недок., тло) за своїми синами, яких викрав Змій. Одного разу жінка пішла (док., подія) на річку і побачила (док., подія) горошину. З цієї горошини згодом народився (док., результат) хлопчик — Котигорошко. Коли він виріс (док.), він сказав (док.): «Я піду (док., майбутнє) шукати братів і буду битися (недок., майбутній процес) зі Змієм, поки не переможу (док., фінальний результат)». У цій історії недоконаний вид описує тривалі стани (сумували, буду битися), а доконаний — ключові події, що рухають сюжет (пішла, народився, переможу).\n\n<!-- INJECT_ACTIVITY: error-correction-aspect-tense -->"
- find: "<!-- INJECT_ACTIVITY: free-write-future-plans -->"
  replace: "А тепер порівняйте це з неформальним листом до друга про літні плани, де також гармонійно поєднуються всі три форми:\n\nПривіт, Сашку! Цього літа я планую багато подорожувати. Спочатку я поїду до Львова. Там я буду гуляти старовинними вулицями та питиму найсмачнішу каву. Після цього я поїду в гори. Я обов'язково піднімуся на Говерлу! А що ти робитимеш улітку? Напиши мені, коли матимеш час.\n\n> *Hi, Sashko! This summer I plan to travel a lot. First I will go to Lviv. There I will be walking along ancient streets and drinking the most delicious coffee. After that, I will go to the mountains. I will definitely climb Hoverla! And what will you be doing in the summer? Write me when you have time.*\n\n<!-- INJECT_ACTIVITY: free-write-future-plans -->"
</fixes>