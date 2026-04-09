## Linguistic Scan
Errors found:
1. **Calque (Critical):** "Давайте виходити" is a literal translation of the Russian "давайте выходить". In Ukrainian, the synthetic imperative must be used ("Виходьмо").
2. **Russianism / Style (Major):** "Давайте + дієслово 1-ї ос. мн. майб. ч." (e.g., "давайте розглянемо", "давайте подивимося") is a Russian-influenced colloquialism that contradicts the decolonized style standard of the curriculum. The pure Ukrainian forms are the synthetic imperative ("розгляньмо", "подивімося") or just the future tense ("розглянемо").
3. **Pedagogical / Linguistic Error (Major):** "радітися" is presented as a personal emotion verb ("де суб'єкт повністю віддається своєму глибокому радісному стану"). `mcp_rag_search_definitions` (СУМ-11) and `mcp_rag_query_grac` confirm that "радітися" is strictly an impersonal verb ("йому радіється"). Presenting it as a personal active emotion verb alongside "сердитися" and "хвилюватися" is incorrect.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-focus-on-identifying-verbs-that-only-exist-in-reflexive-form -->` (Placed in Section 2, logically testing emotion verbs like боятися, сподіватися).
- `<!-- INJECT_ACTIVITY: group-sort-focus-on-sorting-verbs-into-the-5-semantic-categories -->` (Placed at the end of Section 2, matching the 5 categories).
- `<!-- INJECT_ACTIVITY: fill-in-euphony-reflexive -->` (Placed at the end of Section 3 on Euphony).
- `<!-- INJECT_ACTIVITY: error-correction-reflexive -->` (Placed in Section 5 after discussing вибачаюся, дякуюся).
- `<!-- INJECT_ACTIVITY: match-up-reflexive-shift -->` (Placed at the end of Section 5 after discussing contrastive pairs).

All 5 markers are present, logically placed, and match the `activity_hints` exactly.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The text misses four specific citations required by the plan: Кравцова (4 клас, с. 111), Заболотний (8 клас, с. 96), Заболотний (7 клас, с. 51), and Кравцова (4 клас, с. 111) for pronunciation. It mentions the grade levels but omits the author/page citations. |
| 2. Linguistic accuracy | 7/10 | Contains a critical calque "Давайте виходити" (Russian: давайте выходить) instead of "Виходьмо", multiple instances of the Russian-influenced "давайте + дієслово" (e.g., "Давайте розглянемо", "Давай побачимося"), and misidentifies "радітися" as a personal emotion verb. |
| 3. Pedagogical quality | 9/10 | Excellent breakdown of the semantic categories and contrastive pairs ("вчити" vs "вчитися", "збирати" vs "збиратися"). The explanation of phonetic traps (-шся, -ться) is highly effective and clear. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary is seamlessly and naturally integrated into the text. |
| 5. Exercise quality | 10/10 | All 5 markers are present, placed logically immediately after the relevant teaching sections, and perfectly match the focus of the `activity_hints`. |
| 6. Engagement & tone | 10/10 | Very natural, encouraging tone ("Сьогодні ми поговоримо про дуже важливу і цікаву частину..."). The scenarios (like the morning chaos in the student dormitory) are highly engaging and relatable. |
| 7. Structural integrity | 10/10 | Word count is 4730 (exceeding the 4000 target). Clean markdown formatting. All sections are present with correct headings. |
| 8. Cultural accuracy | 10/10 | Contexts are beautifully localized to Ukraine (a dormitory in Kyiv, going to the Carpathians, names like Оксана and Тарас). |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are lively, multi-turn, and sound like real students talking, using the target grammar authentically. |

## Findings
1. [1. Plan adherence] [Minor]
Location: Section 2 (Власне зворотні дієслова): "У цій групі граматичний суб'єкт і об'єкт дії — це одна й та сама особа."
Issue: Missing the direct citation from Кравцова Grade 4 p.111 as requested in the plan.
Fix: Add the citation natively into the sentence.

2. [1. Plan adherence] [Minor]
Location: Section 2 (Взаємні дієслова): "Тут логіка суфікса кардинально змінюється, адже дія більше не замикається на одній людині. Натомість ця дія обов'язково виконується двома..."
Issue: Missing the direct citation from Заболотний Grade 8 p.96 as requested in the plan.
Fix: Add the citation and quote natively.

3. [1. Plan adherence] [Minor]
Location: Section 3 (Милозвучність): "Базове правило, яке вивчають українські школярі у сьомому класі, є простим."
Issue: Missing the citation for Заболотний Grade 7 p.51.
Fix: Add the citation natively.

4. [1. Plan adherence] [Minor]
Location: Section 3 (Pronunciation): "Усі українські школярі ще в четвертому класі детально вчать фонетичні правила для цих форм."
Issue: Missing the citation for Кравцова Grade 4 p.111.
Fix: Add the citation natively.

5. [2. Linguistic accuracy] [Major]
Location: Section 2 (Стану та емоцій): "Хоча ми маємо звичайне слово «радіти», іноді в художніх українських текстах можна зустріти форму «радітися» (to rejoice), де суб'єкт повністю віддається своєму глибокому радісному стану."
Issue: "радітися" is strictly an impersonal verb (йому радіється) according to СУМ-11. Teaching it as a personal active emotion verb where the subject completely surrenders to the state is linguistically inaccurate.
Fix: Replace the example with "засмутитися".

6. [2. Linguistic accuracy] [Critical]
Location: Section 4 (Dialogue): "одягаємося (are getting dressed). Давайте виходити, бо ми точно запізнимося"
Issue: "Давайте виходити" (давайте + інфінітив) is a direct calque from Russian "давайте выходить". In Ukrainian, the synthetic imperative "Виходьмо" must be used.
Fix: Replace with "Виходьмо".

7. [2. Linguistic accuracy] [Major]
Location: Various sections ("Тепер давайте дуже детально розглянемо...", "Давайте разом розглянемо...", "Давайте провідміняємо...", "Давайте подивимося...", "Давайте розглянемо...", "Давайте разом потренуємо...", "Тепер давайте подивимося...", "Тарас: Давай побачимося...", "Давайте розберемо...", "Нарешті, давайте згадаємо...")
Issue: The construction "давайте + дієслово" is heavily influenced by Russian syntax and contradicts the high stylistic standards of the curriculum.
Fix: Remove "давайте" to use the standard future tense, or replace with the beautiful synthetic imperative (розгляньмо, подивімося, зустріньмося).

## Verdict: REVISE
The text is pedagogically excellent, but the presence of the critical "Давайте виходити" calque, multiple stylistic Russianisms, and the pedagogical error regarding the verb "радітися" require automated fixes before the module can be safely published to learners. The missing plan citations also need to be injected.

<fixes>
- find: "У цій групі граматичний суб'єкт і об'єкт дії — це одна й та сама особа. Тобто діяч виконує певну дію, яка повністю спрямована на нього самого"
  replace: "Як зазначає Кравцова (4 клас, с. 111), ці слова «виражають дію, спрямовану на самого виконавця». У цій групі граматичний суб'єкт і об'єкт дії — це одна й та сама особа. Тобто діяч виконує певну дію, яка повністю спрямована на нього самого"
- find: "Тут логіка суфікса кардинально змінюється, адже дія більше не замикається на одній людині. Натомість ця дія обов'язково виконується двома"
  replace: "Тут логіка суфікса кардинально змінюється. Заболотний (8 клас, с. 96) пояснює, що це дія, яка є «здійснюваною двома й більше особами та взаємно спрямованою». Натомість ця дія обов'язково виконується двома"
- find: "Базове правило, яке вивчають українські школярі у сьомому класі, є простим. Ми завжди використовуємо коротку форму «-сь»"
  replace: "Базове правило (Заболотний, 7 клас, с. 51), яке вивчають українські школярі у сьомому класі, є простим. Ми завжди використовуємо коротку форму «-сь»"
- find: "Усі українські школярі ще в четвертому класі детально вчать фонетичні правила для цих форм. Коли ви бачите надруковане закінчення «-шся»"
  replace: "Усі українські школярі ще в четвертому класі (Кравцова, с. 111) детально вчать фонетичні правила для цих форм. Коли ви бачите надруковане закінчення «-шся»"
- find: "Хоча ми маємо звичайне слово «радіти», іноді в художніх українських текстах можна зустріти форму «радітися» (to rejoice), де суб'єкт повністю віддається своєму глибокому радісному стану."
  replace: "Також ми маємо слово «засмутитися» (to become sad), де суб'єкт повністю віддається своєму сумному стану."
- find: "одягаємося (are getting dressed). Давайте виходити, бо ми точно запізнимося"
  replace: "одягаємося (are getting dressed). Виходьмо, бо ми точно запізнимося"
- find: "Тепер давайте дуже детально розглянемо морфологію і подивимося"
  replace: "Тепер дуже детально розглянемо морфологію і подивимося"
- find: "Давайте разом розглянемо початкову форму дієслова"
  replace: "Разом розглянемо початкову форму дієслова"
- find: "Давайте провідміняємо слово у звичайному теперішньому часі."
  replace: "Провідміняймо слово у звичайному теперішньому часі."
- find: "Давайте подивимося на один дуже типовий приклад."
  replace: "Подивімося на один дуже типовий приклад."
- find: "Давайте розглянемо ще кілька корисних контрастних пар"
  replace: "Розгляньмо ще кілька корисних контрастних пар"
- find: "Давайте разом потренуємо правильну вимову"
  replace: "Разом потренуймо правильну вимову"
- find: "Тепер давайте подивимося, як усі ці різні типи"
  replace: "Тепер подивімося, як усі ці різні типи"
- find: "Тарас: Давай побачимося біля головного входу"
  replace: "Тарас: Зустріньмося біля головного входу"
- find: "Давайте розберемо його значення."
  replace: "Розберімо його значення."
- find: "Нарешті, давайте згадаємо дуже популярне дієслово"
  replace: "Нарешті, згадаймо дуже популярне дієслово"
</fixes>
