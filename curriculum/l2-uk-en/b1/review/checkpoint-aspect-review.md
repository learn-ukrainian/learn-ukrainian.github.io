## Linguistic Scan
Linguistic errors found: 
- 8 instances of the stylistic calque `Давайте + дієслово` (e.g., "давайте розглянемо", "давайте зробимо"). This is a direct calque of the Russian analytical imperative (давайте рассмотрим). Natural Ukrainian requires the synthetic 1st person plural imperative ("розгляньмо", "зробімо").

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz -->` (Found correctly placed after Section 1, matches plan focus)
- `<!-- INJECT_ACTIVITY: fill-in -->` (Found correctly placed after Section 1, matches plan focus)
- `<!-- INJECT_ACTIVITY: group-sort -->` (Found correctly placed after Section 2, matches plan focus)
- `<!-- INJECT_ACTIVITY: error-correction -->` (Found correctly placed after Section 2, matches plan focus)
- `<!-- INJECT_ACTIVITY: match-up -->` (Found correctly placed after Section 3, matches plan focus)
- `<!-- INJECT_ACTIVITY: open-writing -->` (Found correctly placed after Section 4/Підсумок, matches plan focus)

Total 6 activities correctly injected, perfectly aligning with the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module comprehensively covers every narrative and grammar point from the plan, including clear examples. However, it fails to include the exact required vocabulary term "видова пара" (it uses just "пара" instead: "Інший чудовий приклад — це пара «забувати» і «забути»."). |
| 2. Linguistic accuracy | 8/10 | The text contains 8 instances of the calque "давайте + [дієслово]" ("давайте розглянемо", "давайте проаналізуємо"), which is a Russianism for the imperative. Authentic Ukrainian uses synthetic forms ("розгляньмо", "проаналізуймо"). |
| 3. Pedagogical quality | 10/10 | Exceptional pedagogical framework. Explanations like "Префікс працює як важка кришка на каструлі: він закриває дію" and the differentiation between standard prohibitions and warnings ("Не падай" vs "Обережно, не впади!") are brilliant for an L2 learner. |
| 4. Vocabulary coverage | 8/10 | Required vocabulary is mostly integrated beautifully into context ("тло розповіді", "результативність", "наказовий спосіб"). However, "видова пара" is missing and must be injected. |
| 5. Exercise quality | 10/10 | All 6 planned exercise markers are placed perfectly after their corresponding theory sections to reinforce immediate learning. |
| 6. Engagement & tone | 10/10 | The tone is warm, professional, and engaging ("Уявіть собі, що ви — режисер кінофільму"). It avoids patronizing language and maintains an authentic teacher persona. |
| 7. Structural integrity | 9/10 | The text exceeds the 4000-word target (4687 words) with rich, substantive content and follows all Markdown heading structures. Deducting 1 point for a minor missing closing guillemet formatting artifact: `«Я **не буду читати** *(I will not read)* цю статтю виражає`. |
| 8. Cultural accuracy | 10/10 | Strong culturally authentic approach. Focuses deeply on the psychological rationale behind Ukrainian aspect choices rather than simply translating English tenses. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are highly realistic, clearly demonstrating context (teacher/student, coworkers, mother/son). Names and settings are natural and culturally appropriate. |

## Findings

[Linguistic accuracy] [Major]
Location: `Щоб краще зрозуміти, як це працює на практиці, давайте розглянемо типову життєву ситуацію.` (and 7 other similar locations)
Issue: Using "давайте" + verb as an imperative is a Russian syntactic calque (давайте рассмотрим). Ukrainian uses the synthetic 1st person plural imperative.
Fix: Replace with synthetic imperatives: "розгляньмо", "проаналізуймо", "порівняймо", "розберімо", "зробімо", "закріпімо".

[Vocabulary coverage] [Major]
Location: `Інший чудовий приклад — це пара «забувати» і «забути».`
Issue: The required vocabulary phrase "видова пара" is missing from the entire text.
Fix: Replace "пара" with "видова пара" to ensure the term is formally introduced.

[Structural integrity] [Minor]
Location: `Фраза «Я **не буду читати** *(I will not read)* цю статтю виражає`
Issue: Missing closing guillemet `»` after the quote.
Fix: Add the missing quotation mark: `цю статтю» виражає`.

## Verdict: REVISE
The pedagogy, depth, and tone of this module are outstanding. However, the repeated use of the "давайте" calque degrades the authenticity of the Ukrainian instruction, and a required vocabulary term is missing. Applying the deterministic fixes will resolve these issues.

<fixes>
- find: "Щоб краще зрозуміти, як це працює на практиці, давайте розглянемо типову життєву ситуацію."
  replace: "Щоб краще зрозуміти, як це працює на практиці, розгляньмо типову життєву ситуацію."
- find: "Тепер давайте детальніше проаналізуємо, як створюється тло розповіді"
  replace: "Тепер детальніше проаналізуймо, як створюється тло розповіді"
- find: "Давайте тепер детально порівняємо ці два аспекти на реальній практиці."
  replace: "Тепер детально порівняймо ці два аспекти на реальній практиці."
- find: "А тепер давайте розглянемо зовсім іншу життєву ситуацію."
  replace: "А тепер розгляньмо зовсім іншу життєву ситуацію."
- find: "Давайте спочатку розглянемо недоконаний вид. Фраза «Я **не буду читати** *(I will not read)* цю статтю виражає"
  replace: "Спочатку розгляньмо недоконаний вид. Фраза «Я **не буду читати** *(I will not read)* цю статтю» виражає"
- find: "Давайте детальніше розберемо цю різницю між стандартною забороною та емоційним попередженням."
  replace: "Детальніше розберімо цю різницю між стандартною забороною та емоційним попередженням."
- find: "Давайте зробимо фінальний структурований аналіз цих п'яти критичних зон перед тестом."
  replace: "Зробімо фінальний структурований аналіз цих п'яти критичних зон перед тестом."
- find: "Давайте надійно закріпимо наші знання за допомогою короткого списку головних правил."
  replace: "Надійно закріпімо наші знання за допомогою короткого списку головних правил."
- find: "Інший чудовий приклад — це пара «забувати» і «забути»."
  replace: "Інший чудовий приклад — це видова пара «забувати» і «забути»."
</fixes>
