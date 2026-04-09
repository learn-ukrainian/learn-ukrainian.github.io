## Linguistic Scan
Found several linguistic errors and calques:
- Typo and grammatical error: "Це приємна подія" instead of "Ця приємна подія".
- Calques: "в даний момент" instead of "зараз", "вирішувати завдання" instead of "виконувати завдання".
- Syntactic Russianisms: multiple instances of "Давайте + [дієслово]" instead of the native Ukrainian imperative suffix "-імо"/"-мо" (e.g., "Давайте розглянемо" -> "Розгляньмо").
- Typo: "Давайте розгляне" instead of "Розглянемо" (which is also fixed to "Розгляньмо").

## Exercise Check
All exercise markers are present, matching the `activity_hints` in type and focus, and are correctly placed at the ends of their respective sections exactly where the relevant material concludes.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Perfectly follows the content outline and incorporates all vocabulary groups. Mentions the categories explicitly in Section 4: "Ми можемо розділити їх на чотири великі лексичні категорії для легкого запам'ятовування. Перша категорія — це люди..." |
| 2. Linguistic accuracy | 7/10 | Found a grammatical error ("Це приємна подія" instead of "Ця"), a typo ("Давайте розгляне"), calques ("в даний момент", "вирішувати завдання"), and 6 syntactic Russianisms ("Давайте" + verb instead of imperative suffix). |
| 3. Pedagogical quality | 10/10 | Excellent TTT flow, precise grammatical explanations (especially regarding Instrumental and Accusative cases with professional verbs), and strong comparative examples ("❌ «Він працює як лікар»" vs "✅ «Він працює лікарем»"). |
| 4. Vocabulary coverage | 10/10 | Successfully integrates all required and recommended vocabulary items naturally into the prose. |
| 5. Exercise quality | 10/10 | All 6 `INJECT_ACTIVITY` markers match the plan and are perfectly situated to test the immediately preceding content. |
| 6. Engagement & tone | 10/10 | Very natural, professional, and encouraging tone suitable for a B1 adult learner. The Lviv IT company scenario is authentic and sets a great professional context. |
| 7. Structural integrity | 10/10 | At 5461 words, the text easily clears the 4000-word target while maintaining clear markdown structure and logical paragraph flow. |
| 8. Cultural accuracy | 10/10 | The discussion on feminitives and the cultural transition from Soviet masculine default to the 2019 Pravopys is accurate, respectful, and highly informative. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues clearly demonstrate the taught grammar (aspect alternation and formal register) and feel sufficiently natural for a business context. |

## Findings

[2. Linguistic accuracy] [CRITICAL]
Location: "Це приємна подія означає, що вам дають вищу посаду та більшу заробітну плату."
Issue: Grammatical gender agreement error ("Це подія" instead of "Ця подія"). "Подія" is feminine.
Fix: Change "Це приємна подія означає," to "Ця приємна подія означає,"

[2. Linguistic accuracy] [CRITICAL]
Location: "яке ви займаєте в компанії в даний момент."
Issue: Calque from Russian ("в данный момент"). The natural Ukrainian phrasing is "на цей час" or "зараз".
Fix: Change "яке ви займаєте в компанії в даний момент." to "яке ви зараз займаєте в компанії."

[2. Linguistic accuracy] [CRITICAL]
Location: "ви працюєте разом і вирішуєте спільні завдання" (and two other instances)
Issue: Calque. In Ukrainian, one "виконує завдання" (executes tasks) but "розв'язує задачі" or "вирішує проблеми". "Вирішувати завдання" is an unnatural direct translation of "решать задачи".
Fix: Change "вирішуєте/вирішували/вирішувати" to "виконуєте/виконували/виконувати" when paired with "завдання".

[2. Linguistic accuracy] [CRITICAL]
Location: Multiple locations (e.g., "Для початку давайте розберемося", "Давайте розгляне п'ять")
Issue: Syntactic Russianism. Using "Давайте" + verb for the 1st-person plural imperative mimics Russian syntax ("давайте сделаем"). Modern, clean educational Ukrainian uses the imperative suffix (Розберімося, розгляньмо, проаналізуймо). Also includes a typo ("розгляне" instead of "розглянемо").
Fix: Replace all instances of "Давайте [дієслово]" with the correct imperative form.

## Verdict: REVISE
The module contains outstanding pedagogical explanations and deeply contextualized vocabulary, but suffers from several grammatical errors (wrong pronoun gender), typos, and syntactic calques ("давайте", "вирішувати завдання", "в даний момент") that must be cleaned up before publishing.

<fixes>
- find: "Для початку давайте розберемося з чотирма"
  replace: "Для початку розберімося з чотирма"
- find: "яке ви займаєте в компанії в даний момент."
  replace: "яке ви зараз займаєте в компанії."
- find: "ви працюєте разом і вирішуєте спільні завдання"
  replace: "ви працюєте разом і виконуєте спільні завдання"
- find: "Це приємна подія означає, що вам дають"
  replace: "Ця приємна подія означає, що вам дають"
- find: "які складні завдання ви успішно вирішували."
  replace: "які складні завдання ви успішно виконували."
- find: "Давайте разом розглянемо класичний приклад"
  replace: "Разом розгляньмо класичний приклад"
- find: "Давайте дуже детально проаналізуємо найважливіші"
  replace: "Детально проаналізуймо найважливіші"
- find: "Давайте розгляне п'ять дуже конкретних"
  replace: "Розгляньмо п'ять дуже конкретних"
- find: "ініціативу та вирішувати серйозні бізнес-завдання."
  replace: "ініціативу та виконувати серйозні бізнес-завдання."
- find: "Давайте послухаємо дуже типовий діалог"
  replace: "Послухаймо дуже типовий діалог"
- find: "Давайте дуже детально згадаємо та проаналізуємо"
  replace: "Дуже детально згадаймо та проаналізуймо"
</fixes>
