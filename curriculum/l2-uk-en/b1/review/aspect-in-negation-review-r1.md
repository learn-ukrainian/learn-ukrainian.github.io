## Linguistic Scan
Found several critical linguistic errors:
- "прийом їжі" — Russianism (calque of "прием пищи").
- "остаттньо" — misspelled word, not found in VESUM (should be "остаточно").
- "давайте проаналізуємо", "давайте заглибимося", "давайте уявимо" — Russianisms (calque of "давайте сделаем"). In Ukrainian, the imperative mood for the 1st person plural is formed without "давайте" (e.g., "проаналізуймо", "заглибмося").
- "двері відкритими" — Russianism (calque of "открывать дверь"). Doors are "відчиненими".
- "підійшли до висновку" — calque of "подошли к выводу" (should be "дійшли висновку").

## Exercise Check
All 6 `INJECT_ACTIVITY` markers match the plan's `activity_hints` exactly.
They are perfectly distributed throughout the text, appearing right after the relevant teaching section (e.g., diagnostic quiz after the introduction, error-correction after discussing common mistakes).
No inline DSL blocks were used, which is correct for core modules.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | The module perfectly follows the TTT pedagogy outlined in the plan. All four sections are present and well-expanded. It includes the exact contrastive dialogue ("Ти вже обідав? — Ні, не обідав. vs Ще не пообідав") from the outline. |
| 2. Linguistic accuracy | 8/10 | Several calques from Russian were identified: "прийом їжі", "двері відкритими", and the colloquial Russianism "давайте" + 1st person plural ("давайте заглибимося"). Also, a typo ("остаттньо" instead of "остаточно"). |
| 3. Pedagogical quality | 10/10 | The pedagogical approach is excellent. It starts with a conceptual hook, explicitly names the "pragmatic shift," and uses clear, high-contrast minimal pairs (e.g., "Він не жив у Києві" vs "Він не переїхав у Київ") to teach a very nuanced topic. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary such as "прагматика", "очікування", "загальне заперечення", and specific verbs like "обговорювати", "вирішувати", "домити" are integrated naturally into the explanations. |
| 5. Exercise quality | 10/10 | The exercise markers correspond exactly to the plan and are logically placed after the conceptual explanations. |
| 6. Engagement & tone | 10/10 | The tone is warm and professional. It encourages the learner to trust their intuition ("Не бійтеся помилятися. Цей тест створений не для оцінювання...") and avoids corporate/gamified filler. |
| 7. Structural integrity | 10/10 | The pipeline counted 4815 words, which comfortably exceeds the 4000-word target. The H2 headings match the `content_outline`. |
| 8. Cultural accuracy | 10/10 | The module smoothly references real Ukrainian grammar textbooks (Заболотний, Литвінова) and their specific pages as authorities on the topic, which grounds the lesson in authentic Ukrainian pedagogy. |
| 9. Dialogue & conversation quality | 10/10 | The dialogues (roommates discussing cleaning, student and professor discussing a paper) are highly contextualized and demonstrate the exact pragmatic nuance the module is teaching. |

## Findings
[Linguistic accuracy] [Critical]
Location: "Ви планували поїсти, ви очікуєте на цей прийом їжі, але ви просто запізнюєтеся з виконанням цього плану."
Issue: "прийом їжі" is a Russianism (calque of "прием пищи"). In Ukrainian, it should be "цю їду" or in this specific breakfast context, "цей сніданок".
Fix: Replace "на цей прийом їжі" with "на цей сніданок".

[Linguistic accuracy] [Critical]
Location: "Щоб остаттньо закріпити це розуміння, давайте заглибимося в один дуже життєвий приклад."
Issue: "остаттньо" is misspelled (should be "остаточно"). Additionally, "давайте заглибимося" is a Russianism (calque of "давайте углубимся"); standard Ukrainian requires the synthetic imperative "заглибмося".
Fix: Replace the phrase with "Щоб остаточно закріпити це розуміння, заглибмося в один дуже життєвий приклад."

[Linguistic accuracy] [Critical]
Location: "Тепер давайте дуже детально проаналізуємо результати вашого діагностичного тесту."
Issue: "давайте проаналізуємо" uses the Russian "давайте + verb" imperative structure. According to Ukrainian textbook standards (e.g., Zabolotnyi 7th grade), the correct form is "проаналізуймо".
Fix: Replace with "Тепер дуже детально проаналізуймо результати вашого діагностичного тесту."

[Linguistic accuracy] [Critical]
Location: "Щоб краще відчути цю своєрідну шкалу зобов'язань, давайте уявимо дуже типову побутову ситуацію."
Issue: "давайте уявимо" uses the Russian imperative structure.
Fix: Replace with "Щоб краще відчути цю своєрідну шкалу зобов'язань, уявімо дуже типову побутову ситуацію."

[Linguistic accuracy] [Critical]
Location: "Слово «ще» надійно захищає нас від категоричних оцінок і завжди залишає двері відкритими для майбутніх звершень."
Issue: "відкритими" applied to doors is a Russianism (calque of "открывать дверь"). Doors are "відчиненими".
Fix: Replace "двері відкритими" with "двері відчиненими".

[Linguistic accuracy] [Minor]
Location: "Отже, ми підійшли до найважливішого висновку нашої теми."
Issue: "підійшли до висновку" is a calque of Russian "подошли к выводу". The natural Ukrainian collocation is "дійшли висновку".
Fix: Replace "підійшли до найважливішого висновку" with "дійшли найважливішого висновку".

## Verdict: REVISE
The module is beautifully written, theoretically deep, and pedagogically sound, comfortably exceeding the word count target. However, it contains several critical linguistic errors (Russianisms like "прийом їжі", "давайте + verb", and "відкриті двері") that must be corrected before publication.

<fixes>
- find: "ви очікуєте на цей прийом їжі, але ви просто"
  replace: "ви очікуєте на цей сніданок, але ви просто"
- find: "Щоб остаттньо закріпити це розуміння, давайте заглибимося в один дуже життєвий приклад."
  replace: "Щоб остаточно закріпити це розуміння, заглибмося в один дуже життєвий приклад."
- find: "Тепер давайте дуже детально проаналізуємо результати вашого"
  replace: "Тепер дуже детально проаналізуймо результати вашого"
- find: "шкалу зобов'язань, давайте уявимо дуже типову"
  replace: "шкалу зобов'язань, уявімо дуже типову"
- find: "залишає двері відкритими для майбутніх звершень"
  replace: "залишає двері відчиненими для майбутніх звершень"
- find: "Отже, ми підійшли до найважливішого висновку нашої теми."
  replace: "Отже, ми дійшли найважливішого висновку нашої теми."
</fixes>
