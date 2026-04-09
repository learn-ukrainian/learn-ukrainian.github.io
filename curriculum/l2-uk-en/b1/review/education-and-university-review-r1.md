## Linguistic Scan
Found multiple linguistic errors and calques:
1. **Russianism / Calque**: The construction "Давайте + дієслово" (Давайте послухаємо, Давайте прочитаємо) is a literal translation of the Russian imperative form. In authentic formal Ukrainian, the synthetic imperative form is required (Послухаймо, Прочитаймо, Потренуймося).
2. **Critical Factual Error**: The text incorrectly states that the acronym "виш" comes from "вищий навчальний заклад". The correct origin of "виш" is "вища школа" (ВНЗ stands for вищий навчальний заклад).
3. **Case Error**: "називається філологічний" — the verb *називатися* in formal register requires the instrumental case (*філологічним*).
4. **Semantic Issue**: "який дорівнював п'яти рокам" — a degree does not "equal" five years, it *requires* five years (*вимагав*). 

## Exercise Check
All exercise markers are present and correctly mapped:
- `<!-- INJECT_ACTIVITY: reading-ua-system -->` is placed after the section on the Ukrainian system.
- `<!-- INJECT_ACTIVITY: quiz-edu-terms -->` correctly assesses Section 1.
- `<!-- INJECT_ACTIVITY: match-disciplines -->` and `<!-- INJECT_ACTIVITY: essay-specialty -->` correspond to Section 2 (disciplines).
- `<!-- INJECT_ACTIVITY: fill-in-academic-life -->` follows Section 3.
- `<!-- INJECT_ACTIVITY: error-correction-participles -->` appropriately follows Section 4 grammar teachings.
Overall, 6 markers were found, which matches the 6 hints in the plan perfectly. No issues found with the injected markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The module skipped the exact requirements for `dialogue_situations` (omitted the interaction about KNU, the dean's office, grade book, and scholarship between a Senior and Freshman). It also completely omitted the word "конспект" and the 6 requested sentences for rewrite practice from Section 4. |
| 2. Linguistic accuracy | 8/10 | Identified multiple instances of the "Давайте + дієслово" calque. Found a case error ("називається філологічний") and a factual error about the etymology of the acronym "виш". |
| 3. Pedagogical quality | 9/10 | The integration of Phase 7 grammar into academic contexts is very strong. Clear distinctions are made between spoken and scientific registers. Lack of the 6-sentence practice exercise holds this back from a perfect 10. |
| 4. Vocabulary coverage | 9/10 | Good contextual use of the provided terminology, with the notable exception of the required word "конспект", which was not integrated. |
| 5. Exercise quality | 10/10 | The markers are injected at logically sound intervals immediately following the teaching of relevant material. |
| 6. Engagement & tone | 10/10 | The tone is professional yet highly encouraging. It appropriately guides the student through complex grammar without gamified jargon. |
| 7. Structural integrity | 10/10 | The word count sits at a robust 4893 words, safely surpassing the 4000-word target. The formatting and headers adhere cleanly to the module template. |
| 8. Cultural accuracy | 9/10 | Explains the Ukrainian academic system and the transition to Bologna standards brilliantly. Deducting 1 point for the incorrect history of the word "виш". |
| 9. Dialogue & conversation quality | 7/10 | Dialogue 1 failed to set up the scenario mandated by the plan, offering a generic conversation about specializations instead of the navigational dialogue requested. Dialogues 2 and 3 are solid. |

## Findings

[Plan adherence] [Critical]
Location: Section 1, Dialogue 1 ("Давайте послухаємо розмову двох студентів... Максим: Привіт, Олено...")
Issue: The generator completely ignored the `dialogue_situations` instruction, which required a specific dialogue in KNU between a Senior and Freshman discussing the dean's office, grade book, and scholarship.
Fix: Rewrite Dialogue 1 to combine the specialization talk with the exact required scenario from the plan.

[Linguistic accuracy] [Major]
Location: Throughout the text ("Давайте послухаємо", "Давайте потренуємося", "Давайте прочитаємо", "Давайте проаналізуємо")
Issue: Using "Давайте" to form the 1st person plural imperative is a Russian calque (давайте сделаем). Authentic Ukrainian requires the synthetic verb form.
Fix: Replace all instances with the proper imperative forms (Послухаймо, Потренуймося, Прочитаймо, Проаналізуймо).

[Linguistic accuracy] [Critical]
Location: "Це популярна абревіатура, утворена від словосполучення «вищий навчальний заклад»."
Issue: Factual linguistic error. The acronym "виш" is derived from "вища школа", not "вищий навчальний заклад" (which forms ВНЗ).
Fix: Replace "вищий навчальний заклад" with "вища школа" in this sentence.

[Linguistic accuracy] [Critical]
Location: "Наприклад, факультет, де студенти глибоко вивчають мови, називається філологічний (philological)."
Issue: The verb "називатися" takes the instrumental case in formal literary Ukrainian.
Fix: Change "філологічний" to "філологічним".

[Linguistic accuracy] [Minor]
Location: "який дорівнював п'яти рокам безперервного навчання"
Issue: Semantic phrasing error. A degree doesn't "equal" five years of study; the degree program requires five years.
Fix: Replace with "який вимагав п'яти років безперервного навчання".

[Plan adherence] [Major]
Location: End of Section 4 ("Навчальний процес: дієприкметники і дієприслівники").
Issue: The plan expressly required the inclusion of the recommended word "конспект" via the sentence "Прочитавши статтю, зробіть конспект", and also asked to provide 6 informal sentences for the learner to rewrite. Both plan points were ignored.
Fix: Append the missing content to the end of the section just before the activity marker.

## Verdict: REVISE
The text is highly informative, dense, and beautifully written for B1-B1.5 standards. However, it contains several critical linguistic errors regarding etymology ("виш"), case ("називається"), and widespread calques ("Давайте"). Furthermore, it missed key elements of the plan (Dialogue 1 scenario, "конспект", and practice sentences). The module must be revised using the fixes below to ensure structural and linguistic integrity. 

<fixes>
- find: |
    Давайте послухаємо розмову двох студентів, які зустрілися біля головної бібліотеки у перші осінні дні навчання. Цей діалог покаже вам живу студентську мову.
    > — **Максим:** Привіт, Олено! Дуже радий тебе бачити. На якому ти зараз **курсі** *(year of study)*?
    > — **Олена:** Привіт, Максиме! Я вже на третьому курсі. А ти досі вчишся на **юридичному факультеті** *(law faculty)*?
    > — **Максим:** Так, я майбутній юрист. Моя **спеціальність** *(major)* — міжнародне право і міжнародні відносини. Наша **кафедра** *(department)* вимоглива, тому нам доводиться багато читати. А як твоя улюблена філологія?
    > — **Олена:** Чудово! Я вивчаю сучасну українську літературу. До речі, цього складного семестру ми аналізуємо тексти, написані відомими українськими дисидентами. Це дуже цікаво і пізнавально.
    > — **Максим:** Звучить справді серйозно. Бажаю тобі великого успіху на майбутніх семінарах!
    > — **Олена:** Дякую тобі! І тобі теж успішного та легкого навчання!
  replace: |
    Послухаймо розмову двох студентів, які зустрілися біля головної бібліотеки у свій перший тиждень у Київському національному університеті. Цей діалог покаже вам живу студентську мову.
    > — **Олена (старшокурсниця):** Привіт, Максиме! Вітаю з початком навчання! На якій ти **спеціальності** *(major)*?
    > — **Максим (першокурсник):** Привіт, Олено! Я на **юридичному факультеті** *(law faculty)*. Підкажи, будь ласка, де знаходиться **деканат** *(dean's office)*? Мені треба віднести документи.
    > — **Олена:** Він на другому поверсі. До речі, успішно **записавшись на курс** *(having registered for the course)*, ти скоро отримаєш свою **залікову книжку** *(grade book)*.
    > — **Максим:** Дякую! Наша **кафедра** *(department)* дуже сувора. А як твоя філологія?
    > — **Олена:** Чудово! Якщо будеш гарно вчитися, **стипендія** *(scholarship)* виплачуватиметься щомісяця. А взимку, **захистивши курсову** *(having defended the term paper)*, ти без проблем складеш першу **сесію** *(exam period)*.
    > — **Максим:** Звучить серйозно. Дякую за цінні поради!
- find: "Давайте послухаємо коротку розмову студента"
  replace: "Послухаймо коротку розмову студента"
- find: "Давайте потренуємося це робити просто зараз."
  replace: "Потренуймося це робити просто зараз."
- find: "Давайте прочитаємо типовий діалог"
  replace: "Прочитаймо типовий діалог"
- find: "Давайте проаналізуємо цей текст"
  replace: "Проаналізуймо цей текст"
- find: "Це популярна абревіатура, утворена від словосполучення «вищий навчальний заклад»."
  replace: "Це популярна абревіатура, утворена від словосполучення «вища школа»."
- find: "Наприклад, факультет, де студенти глибоко вивчають мови, називається філологічний *(philological)*."
  replace: "Наприклад, факультет, де студенти глибоко вивчають мови, називається філологічним *(philological)*."
- find: "який дорівнював п'яти рокам безперервного навчання"
  replace: "який вимагав п'яти років безперервного навчання"
- find: |
    ваші есе будуть отримувати лише найвищі бали від найсуворіших викладачів на факультеті.
  replace: |
    ваші есе будуть отримувати лише найвищі бали від найсуворіших викладачів на факультеті.

    Для кращого розуміння, запам'ятайте цей класичний приклад з **конспектом** *(lecture notes)*: «**Прочитавши статтю** *(Having read the article)*, зробіть детальний конспект». Ця конструкція показує чітку послідовність: спочатку ви завершили читання, а потім почали писати. Тепер виконайте самостійну практику. Перетворіть ці 6 розмовних речень на формальні академічні:
    1. Студентка готується до іспиту і п'є каву.
    2. Я написав дипломну роботу і відчуваю полегшення.
    3. Професор, який пояснює матеріал, дуже цікавий.
    4. Ми провели експеримент і отримали гарні результати.
    5. Стаття, яку опублікували вчора, стала популярною.
    6. Коли ми використовуємо словник, ми робимо менше помилок.
</fixes>
