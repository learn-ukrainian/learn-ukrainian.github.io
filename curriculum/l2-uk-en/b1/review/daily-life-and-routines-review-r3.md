## Linguistic Scan
Errors found: "за чверть до восьмої" (grammatical error — mixed/incorrect time construction) and "сонце встає" (stylistic calque from Russian).

## Exercise Check
- `fill-in-routine-verbs-complete-a-daily-routine-text-with-correct-reflexive-and-prefixed-verb-forms` is present, well-placed, and matches plan.
- `sentence-builder-write-plans-and-schedules-using-conditional-forms-and-temporal-expressions` is present, well-placed, and matches plan.
- `match-up-chores` is present, well-placed, and matches plan.
- `error-correction-daily` is present, well-placed, and matches plan.
- `sentence-builder-conditionals` is an extra, redundant marker that contradicts the plan's 5 hints limit.
- `quiz-grammar-choice` is present, well-placed, and matches plan.
Issue: The extra marker `sentence-builder-conditionals` needs to be removed.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module strictly follows the communicative objectives and sequence of the plan. However, a few required vocabulary items (обідати, вечеряти, пошук роботи, займатися спортом) were omitted from the text. |
| 2. Linguistic accuracy | 7/10 | Contains a critical grammatical error with time structures: "За чверть до восьмої я беру сумку" mixes two separate ways to tell time ("за чверть восьма" and "чверть до восьмої"). Contains a stylistic Russian calque: "сонце встає" instead of the normative "сонце сходить". |
| 3. Pedagogical quality | 10/10 | Adheres excellently to the PPP methodology. Grammatical properties like reflexivity and verbal prefixes are clearly contextualized with rich examples before dialogue introduction. |
| 4. Vocabulary coverage | 8/10 | Uses most vocabulary efficiently within natural sentences, but deducts points for entirely missing the verbs "обідати" / "вечеряти", phrase "пошук роботи", verb phrase "займатися (спортом)", and the full collocation "виносити сміття". |
| 5. Exercise quality | 9/10 | Activities match the plan's targeted learning focuses and locations, but 6 markers were placed instead of the expected 5, causing a duplicate mismatch. |
| 6. Engagement & tone | 10/10 | Excellent "vlogger" situational framing creates high engagement. The tone is encouraging, non-robotic, and fits a B1 language learner context perfectly. |
| 7. Structural integrity | 10/10 | Clean Markdown flow. All headings are correct. With 4995 words, it exceeds the target word count smoothly. |
| 8. Cultural accuracy | 10/10 | Explains cultural shifts correctly (egalitarian household roles, modern breakfast habits) and actively warns against Surzhyk or Russicisms ("стирати", "пилесос", "відпочиватися"). |
| 9. Dialogue & conversation quality | 10/10 | Outstanding, natural multi-speaker dialogues that incorporate polite forms, conditions, and situational verbs authentically. |

## Findings

[DIMENSION 2] [SEVERITY: critical]
Location: "За чверть до восьмої я беру сумку і виходжу з дому."
Issue: "За чверть до восьмої" is a mixed grammatical time construction (incorrectly combining "за чверть восьма" and "чверть до восьмої"). 
Fix: Replace with "За чверть восьма я беру сумку і виходжу з дому."

[DIMENSION 2] [SEVERITY: minor]
Location: "— **Влогер:** Я прокидаюся, коли сонце тільки встає, о пів на сьому."
Issue: "Сонце встає" is a calque from Russian "солнце встает". The correct Ukrainian literary collocation is "сонце сходить".
Fix: Replace with "— **Влогер:** Я прокидаюся, коли сонце тільки сходить, о пів на сьому."

[DIMENSION 4] [SEVERITY: major]
Location: Missing from various sections throughout the prose.
Issue: Required vocabulary words and phrases are completely missing from the text: verbs "обідати" and "вечеряти", phrase "пошук роботи", and verb collocation "займатися спортом". Additionally, "виносити сміття" was missing its explicit Ukrainian collocation in the prose (only "винеси" appeared in dialogue).
Fix: Insert these words naturally into the text.

[DIMENSION 5] [SEVERITY: major]
Location: "<!-- INJECT_ACTIVITY: sentence-builder-conditionals -->\n\n## Розпорядок дня: планування та поради"
Issue: The plan specifies 5 `activity_hints`, but 6 markers were injected into the text. The extra duplicate `sentence-builder` marker at the end of the weekend section violates the exact limit.
Fix: Remove the redundant marker `<!-- INJECT_ACTIVITY: sentence-builder-conditionals -->`.

## Verdict: REVISE
The text is exceptionally well-written in framing and pedagogy, successfully applying the complex PPP methodology to everyday contexts. However, a REVISE verdict is necessary to correct a mixed time construction error, a stylistic Russian calque, complete the integration of missing required vocabulary, and remove the extra redundant activity marker.

<fixes>
- find: "За чверть до восьмої я беру сумку і виходжу з дому."
  replace: "За чверть восьма я беру сумку і виходжу з дому."
- find: "— **Влогер:** Я прокидаюся, коли сонце тільки встає, о пів на сьому."
  replace: "— **Влогер:** Я прокидаюся, коли сонце тільки сходить, о пів на сьому."
- find: "«Завтра я поснідаю значно раніше.» — *Tomorrow I will have breakfast much earlier.*\n\nUnderstanding this precise aspectual contrast"
  replace: "«Завтра я поснідаю значно раніше.» — *Tomorrow I will have breakfast much earlier.*\n\nЗверніть увагу, що для інших прийомів їжі існують власні дієслова: вдень ми зазвичай обідаємо (have lunch), а ввечері — вечеряємо (have dinner).\n\nUnderstanding this precise aspectual contrast"
- find: "А щоб отримати хорошу посаду, вам спочатку потрібно успішно пройти складну співбесіду з керівником."
  replace: "Пошук роботи часто забирає багато часу, а щоб отримати хорошу посаду, вам спочатку потрібно успішно пройти складну співбесіду з керівником."
- find: "Коли настає вільний час, молодь часто йде в центр міста розважатися. Влітку дуже популярно кататися на велосипеді лісовими стежками."
  replace: "Коли настає вільний час, молодь часто йде в центр міста розважатися. Багато людей люблять займатися спортом, наприклад, влітку дуже популярно кататися на велосипеді лісовими стежками."
- find: "use the second-person imperative, such as «вимий» or «винеси»."
  replace: "use the second-person imperative, such as «вимий посуд» (wash the dishes) or «винеси сміття» (take out the trash)."
- find: "<!-- INJECT_ACTIVITY: sentence-builder-conditionals -->\n\n## Розпорядок дня: планування та поради"
  replace: "## Розпорядок дня: планування та поради"
</fixes>