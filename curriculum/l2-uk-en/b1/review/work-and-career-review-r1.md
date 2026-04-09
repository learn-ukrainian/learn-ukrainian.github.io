## Linguistic Scan
Errors found:
- **проє প্রকল্পটি** — Typographical error, duplication/corruption of the word "проєктом".
- **безкінечно** — Not in VESUM. Russicism/Surzhyk derived from Russian "бесконечно". The correct Ukrainian adverb is "без кінця" or "нескінченно".
- **прийом** — "граматичний прийом" is a calque of Russian "грамматический прием". In standard educational Ukrainian, it should be "граматичний засіб".
- **закінчення** (used to refer to "-ець" and "-чиня") — Critical morphological error. These are derivational suffixes (суфікси), not endings (закінчення). An ending in Ukrainian implies an inflectional morpheme.

## Exercise Check
All activity markers are correctly present in the prose, evenly distributed after the relevant instruction sections, and strictly align with the `activity_hints` required by the plan:
- `<!-- INJECT_ACTIVITY: vocab-match-up -->` (after vocabulary section)
- `<!-- INJECT_ACTIVITY: vocab-group-sort -->` (after vocabulary section)
- `<!-- INJECT_ACTIVITY: fill-in-aspect-work -->` (after aspect section)
- `<!-- INJECT_ACTIVITY: quiz-aspect-logic -->` (after aspect section)
- `<!-- INJECT_ACTIVITY: role-play-interview -->` (after interview section)
- `<!-- INJECT_ACTIVITY: open-writing-bio -->` (after interview section)

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | DEDUCTION: Missed "Preview: checkpoint-aspect (M12)" at the end of the module. DEDUCTION: The 5-sentence practice template didn't match the required `Після [чого?] я [pf]. [X] років я [impf]...` pattern. DEDUCTION: Skipped the required interview closing formula "Дякую за можливість". |
| 2. Linguistic accuracy | 7/10 | DEDUCTION: Typo "проє প্রকল্পটি" instead of "проєктом". DEDUCTION: Used the Russicism "безкінечно" instead of "без кінця". DEDUCTION: Used the calque "граматичний прийом" instead of "засіб". |
| 3. Pedagogical quality | 6/10 | DEDUCTION: Incorrectly taught "-ець" and "-чиня" as "закінчення" (endings). In Ukrainian grammar, these are derivational "суфікси" (suffixes). Calling a suffix an ending is a fundamental morphological error. REWARD: Excellent explanation of aspect choice using the "тло та подія" (background vs event) metaphor. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words (професія, посада, фах, обов'язки, звільнення, etc.) are embedded naturally throughout the prose. |
| 5. Exercise quality | 10/10 | All 6 activity markers exactly match the IDs from the plan and are placed logically after the corresponding instructional chunks. |
| 6. Engagement & tone | 10/10 | The tone is professional, encouraging, and uses excellent narrative frames (e.g., comparing the perfective sequence to "сходинки"). No filler text. |
| 7. Structural integrity | 9/10 | Word count is robust (5448 words). All plan headings are present as H2s. DEDUCTION: One corrupted typo token in the text. |
| 8. Cultural accuracy | 10/10 | Excellent integration of the 2019 Orthography update regarding feminitives (фемінітиви). Accurately frames the historical suppression of female job titles during the Soviet era. |
| 9. Dialogue & conversation quality | 10/10 | The dialogues (both the formal interview with "Керівник відділу" and the casual lunch between "Олександр" and "Тетяна") are extremely natural and successfully demonstrate register switching. |

## Findings

[Plan Adherence] [major]
Location: Section "Підсумок: робота і вид дієслова", last paragraph.
Issue: Missing the preview for the M12 checkpoint as explicitly required by the plan (`Preview: checkpoint-aspect (M12)`).
Fix: Add the preview sentence to the final paragraph.

[Plan Adherence] [major]
Location: Section "Підсумок: робота і вид дієслова", the fourth self-check question.
Issue: The template for the 5-sentence narrative does not follow the specific grammatical structure requested by the plan.
Fix: Replace the generic template with the requested aspect alternation template `Після [чого?] я [pf]. [X] років я [impf]. Потім [pf]. Зараз я [impf]`.

[Plan Adherence] [major]
Location: Section "На співбесіді: ситуативне мовлення", end of the interview tips paragraph.
Issue: The plan requests teaching the job interview structure including "4. Завершення: Дякую за можливість." This formula was entirely skipped.
Fix: Insert the closing formula after the discussion of salary expectations.

[Linguistic Accuracy] [critical]
Location: Section "Вид дієслова у розповіді про роботу", first paragraph.
Issue: Uncaught typo in the text: "проє প্রকল্পটি" instead of "проєктом".
Fix: Replace "проє প্রকল্পটি" with "проєктом".

[Linguistic Accuracy] [critical]
Location: Section "Вид дієслова у розповіді про роботу", last paragraph.
Issue: Usage of "безкінечно", which is a Russicism (from бесконечно) and not attested in VESUM. The correct Ukrainian adverb is "без кінця" or "нескінченно".
Fix: Replace "безкінечно" with "без кінця".

[Pedagogical Quality] [critical]
Location: Section "Професія і фах: базова лексика", paragraph about feminitives.
Issue: The text refers to the derivational suffixes "-ець" and "-чиня" as "закінчення" (endings). In Ukrainian morphology, an ending is an inflectional morpheme (флексія), while these are strictly suffixes (суфікси). This teaches learners incorrect grammar terminology.
Fix: Change "закінчення" to "суфікс".

[Linguistic Accuracy] [minor]
Location: Section "Вид дієслова у розповіді про роботу", third paragraph.
Issue: "граматичний прийом" is a calque from the Russian "грамматический прием". In Ukrainian educational texts, "граматичний засіб" is the standard term.
Fix: Change "граматичний прийом" to "граматичний засіб".

## Verdict: REVISE
The module provides exceptionally good explanations of aspect and register, but requires fixes for a critical morphological terminology error ("закінчення" instead of "суфікс"), an active Russicism ("безкінечно"), a corrupted word token, and several missing structural elements from the plan.

<fixes>
- find: "Я **працювала** *(worked)* над цим архітектурним проє প্রকল্পটি майже пів року"
  replace: "Я **працювала** *(worked)* над цим архітектурним проєктом майже пів року"
- find: "ви роками писали заяву, повільно збирали особисті речі і безкінечно прощалися з колегами."
  replace: "ви роками писали заяву, повільно збирали особисті речі і без кінця прощалися з колегами."
- find: "Для тих слів, які мають закінчення на «-ець», ми використовуємо спеціальне закінчення **-чиня**."
  replace: "Для тих слів, які мають суфікс «-ець», ми використовуємо спеціальний суфікс **-чиня**."
- find: "Цей потужний граматичний прийом є ефективним саме на співбесіді"
  replace: "Цей потужний граматичний засіб є ефективним саме на співбесіді"
- find: "Ваш базовий шаблон: «Раніше я довго працював на фабриці, але потім я раптово змінив компанію. Зараз я успішно працюю в зовсім іншій перспективній сфері»."
  replace: "Ваш базовий шаблон: «Після [чого?] я [pf]. [X] років я [impf]. Потім [pf]. Зараз я [impf]»."
- find: "Будьте готові назвати адекватну суму, адже ваша **зарплата** *(salary)* — це справедлива винагорода за ваш професійний досвід та важку працю."
  replace: "Будьте готові назвати адекватну суму, адже ваша **зарплата** *(salary)* — це справедлива винагорода за ваш професійний досвід та важку працю. На завершення зустрічі обов'язково скажіть: «Дякую за можливість»."
- find: "Бажаю вам дуже успішної, легкої та стрімкої кар'єри у майбутньому!"
  replace: "Бажаю вам дуже успішної, легкої та стрімкої кар'єри у майбутньому! Наступний крок — це модуль 12 (checkpoint-aspect), велика діагностична робота з усіх видових контекстів."
</fixes>
