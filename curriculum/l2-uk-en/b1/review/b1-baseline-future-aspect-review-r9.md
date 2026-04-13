## Linguistic Scan
Errors found:
- **українсько** (non-existent adverb form used in `традиційно українсько`). Valid adverbs are *по-українському*, *по-українськи*, or *українською*.
- **малююму** (used as a negative example instead of the plan-specified `малютиму`, creating an irrelevant trap).

## Exercise Check
- `quiz-aspect-identification` — matches plan.
- `match-up-aspect-pairs` — matches plan.
- `fill-in-complete-sentences-with-the-correct-simple-future-form` — **UNAUTHORIZED MARKER** (not in plan).
- `group-sort-sort-verb-forms-into-present-vs-simple-future` — **UNAUTHORIZED MARKER** (not in plan).
- `group-sort-future-forms` — matches plan.
- `fill-in-future-choice` — matches plan.
- `error-correction-aspect-tense` — matches plan.
- `free-write-future-plans` — matches plan.

Issue: The writer injected 2 extra markers not found in the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | Failed to cite textbook sources (Литвінова, Заболотний, Авраменко, Кравцова) in the text. Missed the preview of module M06. Injected two unauthorized activity markers not present in the plan. |
| 2. Linguistic accuracy | 8/10 | Used the non-existent adverb form `українсько` ("традиційно українсько"). Created an incorrect trap form `малююму` instead of the plan's `малютиму`. |
| 3. Pedagogical quality | 8/10 | Strong explanation of the aspect-tense matrix and PPP flow. However, the section on synthetic future has ~200 words of English theory with very few Ukrainian examples. |
| 4. Vocabulary coverage | 8/10 | Most required vocabulary is present, but `двовидовий` was only translated to English ("biaspectual") without the Ukrainian term. Missing recommended terms: `дійсний спосіб`, `основа інфінітива`, `часова форма`, `наголос`, and specific verb examples like `побачити`, `приїхати`, `веліти`, `женити`, `класти`, `покласти`. |
| 5. Exercise quality | 7/10 | Markers placed logically after concepts, but injected 2 extra `fill-in` and `group-sort` markers that do not correspond to the plan's `activity_hints`. |
| 6. Engagement & tone | 7/10 | Writer's persona relies heavily on generic enthusiasm: "unique and elegant feature", "beautiful one-word alternative", "fascinating piece of linguistic history", "proudly and uniquely Ukrainian". |
| 7. Structural integrity | 10/10 | Word count is 5618 (exceeds 4000). All H2 headings match the plan exactly. |
| 8. Cultural accuracy | 8/10 | Falsely claimed that "other East Slavic languages rely solely on a two-word analytic construction". (Belarusian also has a synthetic future form, e.g., *рабіцьму*). |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are natural, correctly formatted, and effectively demonstrate the contrast between perfective and imperfective verbs in context. |

## Findings

[Plan adherence] [Major]
Location: Throughout the prose and concluding section.
Issue: The writer ignored the plan's instruction to cite specific textbooks (Литвінова, Заболотний, Авраменко). Missed the preview for M06.
Fix: Add textbook citations into the text and insert the M06 preview at the end.

[Linguistic accuracy] [Critical]
Location: `Форма «працюватиму» звучить трохи більш літературно та традиційно українсько`
Issue: `українсько` is an incorrect adverb form. It violates Ukrainian derivation rules.
Fix: Change to `має традиційно українське звучання`.

[Linguistic accuracy] [Minor]
Location: `ви ніколи не скажете «малююму».`
Issue: The plan explicitly asked to use the common trap `малютиму` (losing the -ва-), but the writer invented `малююму`.
Fix: Replace `малююму` with `малютиму`.

[Vocabulary coverage] [Major]
Location: Section 1 (biaspectual verbs) and general theory sections.
Issue: The Ukrainian term `двовидові дієслова` was omitted (only "biaspectual" was used). Also missing `основа інфінітива`, `дійсний спосіб`, `наголос`, `часова форма`, `побачити`, `приїхати`, `веліти`, `женити`, `класти`, `покласти`.
Fix: Inject these terms into the corresponding sections.

[Exercise quality] [Major]
Location: End of "Проста форма майбутнього часу"
Issue: The writer injected two extra markers (`fill-in-complete-sentences-with-the-correct-simple-future-form` and `group-sort-sort-verb-forms-into-present-vs-simple-future`) that do not exist in the plan.
Fix: Remove the unauthorized markers.

[Engagement & tone] [Minor]
Location: Section 3 ("Складна (синтетична) форма майбутнього часу")
Issue: Contains excessive generic enthusiasm ("unique and elegant feature", "proudly and uniquely Ukrainian").
Fix: Neutralize the most overt generic praise.

[Cultural accuracy] [Critical]
Location: `While other East Slavic languages rely solely on a two-word analytic construction for the imperfective future, Ukrainian retains this beautiful one-word alternative.`
Issue: It is factually wrong to claim other East Slavic languages *solely* rely on the analytic form. Belarusian also has a synthetic future form (e.g., рабіцьму).
Fix: Contrast it specifically with Russian, which does rely solely on the two-word construction.

## Verdict: REVISE
The module has a critical linguistic error (`українсько`), a factual error regarding East Slavic languages, and deviations from the plan (missing textbook citations, extra markers, and omitted vocabulary). These must be corrected via the deterministic find/replace protocol before publication.

<fixes>
- find: "Форма «працюватиму» звучить трохи більш літературно та традиційно українсько, тоді як"
  replace: "Форма «працюватиму» звучить трохи більш літературно та має традиційно українське звучання, тоді як"
- find: "ви ніколи не скажете «малююму»."
  replace: "ви ніколи не скажете «малютиму»."
- find: "First, there are biaspectual verbs. These verbs look exactly the same"
  replace: "First, there are biaspectual verbs (двовидові дієслова). These verbs look exactly the same"
- find: "While other East Slavic languages rely solely on a two-word analytic construction for the imperfective future, Ukrainian retains this beautiful one-word alternative."
  replace: "Unlike Russian, which relies solely on a two-word analytic construction for the imperfective future, Ukrainian retains this one-word alternative."
- find: "The Ukrainian language possesses a unique and elegant feature that distinguishes it from its linguistic neighbors: the synthetic, or compound, form of the future tense."
  replace: "The Ukrainian language possesses a distinct feature: the synthetic, or compound, form of the future tense."
- find: "This fascinating piece of linguistic history explains why the full infinitive remains perfectly visible inside the modern conjugation. By mastering this form, you are connecting with the deep historical roots of the Ukrainian language and embracing a structure that is proudly and uniquely Ukrainian."
  replace: "This linguistic history explains why the full infinitive remains perfectly visible inside the modern conjugation."
- find: "The system is wonderfully logical if you remember one core principle"
  replace: "The system is strictly logical if you remember one core principle"
- find: "The concept of verbal aspect is the soul of the Ukrainian verb."
  replace: "As highlighted in standard textbooks like Литвінова Grade 7, the concept of verbal aspect is the soul of the Ukrainian verb within the дійсний спосіб (indicative mood), which states facts across all tenses."
- find: "We are now ready to build the first of the three future tense forms: the simple form."
  replace: "Following the curriculum of Литвінова Grade 7, we are now ready to build the first of the three future tense forms: the simple form."
- find: "Now that you know how to build the three future forms, it is time to look at the entire system."
  replace: "Using the aspect-tense matrix from Авраменко Grade 7, it is time to look at the entire system."
- find: "брати (to take) matching with взяти (to have taken)."
  replace: "брати (to take) matching with взяти (to have taken), or класти (to put) matching with покласти (to have put)."
- find: "Common examples are often loan words like атакувати (to attack) or телеграфувати (to telegraph)."
  replace: "Common examples are loan words like атакувати (to attack) or телеграфувати (to telegraph), as well as native verbs like веліти (to command) and женити (to marry)."
- find: "Similarly, **попросити** shifts the consonant for the first person singular: я попрошу, ти попросиш."
  replace: "Similarly, **попросити** shifts the consonant for the first person singular: я попрошу, ти попросиш. Other common perfective forms include побачити (побачу, побачиш) and приїхати (приїду, приїдеш)."
- find: "the correct grammatical form will appear naturally.*"
  replace: "the correct grammatical form will appear naturally.*\n\n**Preview of next module: Людина і стосунки (M06)**\nIn the next module, we will describe people and relationships, applying the future tense in context: «Я познайомлю тебе з моєю подругою» (I will introduce you to my friend), «Ми будемо зустрічатися щотижня» (We will be meeting every week)."
- find: "<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-simple-future-form -->\n<!-- INJECT_ACTIVITY: group-sort-sort-verb-forms-into-present-vs-simple-future -->"
  replace: ""
- find: "Зверніть особливу увагу на те, що частина «ти» з інфінітива завжди зберігається всередині слова."
  replace: "Зверніть особливу увагу на те, що уся основа інфінітива (infinitive stem), включаючи «ти», завжди зберігається всередині слова."
- find: "Це дієслово не підпорядковується загальним правилам виду, тому воно функціонує"
  replace: "Це дієслово не підпорядковується загальним правилам виду, і його наголос (stress) залишається стабільним, тому воно функціонує"
- find: "Choosing the correct future tense in Ukrainian might seem complex"
  replace: "Choosing the correct часова форма (tense form) for the future in Ukrainian might seem complex"
</fixes>