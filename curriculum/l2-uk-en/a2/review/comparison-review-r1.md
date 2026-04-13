## Linguistic Scan
- Critical factual grammar error in **Вищий ступінь**: `«за» або «від» та знахідний відмінок` is wrong. `від` governs the **Genitive**, not the Accusative.
- Critical factual grammar error in **Вищий ступінь**: `«г», «ж» або «з» ... перетворюються на «жч»` is an incorrect rule. The examples given reflect different alternations (`дорогий → дорожчий`, `близький → ближчий`, `високий → вищий`), not one single `жч` pattern.

## Exercise Check
Markers found: `fill-in-comparative`, `true-false-constructions`, `match-up-match-adjective-to-its-superlative-form`, `quiz-irregular-forms-choose-the-correct-suppletive-form`, `error-correction-double-comparisons-find-and-fix-wrong-comparative-and-superlative-forms-e-g`, plus three extra end-of-module duplicates.

The first five markers are placed after the relevant teaching blocks and match the plan well. The problem is the final cluster of three extra markers at the end: they duplicate earlier activity types instead of introducing a new planned activity, so exercise distribution is uneven and likely redundant. No inline DSL exercise logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned sections appear in order, the phone-comparison dialogue is present, and the required comparison targets are taught; however the module uses 8 activity markers even though the plan hints specify 5 activity types, with three duplicate markers clustered at the end. |
| 2. Linguistic accuracy | 5/10 | The module teaches two wrong grammar claims: `«за» або «від» та знахідний відмінок` and `«г», «ж» або «з» ... перетворюються на «жч»`. |
| 3. Pedagogical quality | 6/10 | The module follows dialogue → explanation → practice, but the inaccurate case rule and inaccurate alternation rule appear in the presentation stage, so learners are explicitly taught false grammar. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is well integrated in prose and examples: `порівняння`, `більший`, `менший`, `кращий`, `гірший`, `найкращий`, `найбільший`, `солодший`, `цікавіший`, `ніж`; recommended modifiers `набагато`, `трохи`, `значно` also appear naturally. |
| 5. Exercise quality | 6/10 | The first five markers are well placed after the relevant teaching sections, but the last three markers duplicate earlier activity types and are clustered after the recap rather than after new instruction. |
| 6. Engagement & tone | 6/10 | The teacherly voice is present, but lines like `Це покаже вашу повагу до культури` turn grammar guidance into moralizing language-policing. |
| 7. Structural integrity | 7/10 | All H2 headings are present and the pipeline word count is 2278, but raw `<!-- VERIFY -->` comments remain in learner-facing prose. |
| 8. Cultural accuracy | 6/10 | The module repeatedly frames Ukrainian through anti-Russian policing (`Це пряме запозичення з російської граматики`, `Чиста українська мова`), instead of primarily explaining the Ukrainian norm on its own terms. |
| 9. Dialogue & conversation quality | 9/10 | The coffee/tea and phone-store dialogues are multi-turn, named-speaker exchanges tied to real comparison tasks. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Вищий ступінь**, paragraph beginning `Як правильно побудувати речення...`  
Issue: The text says `Другий варіант використовує прийменники «за» або «від» та знахідний відмінок.` This teaches the wrong case government. `за` takes Accusative here, but `від` takes Genitive.  
Fix: Replace the paragraph with a correct three-pattern explanation: `ніж + Nominative`, `за + Accusative`, `від + Genitive`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Вищий ступінь**, paragraph beginning `Коли ми додаємо суфікс «-ший»...`  
Issue: The rule `«г», «ж» або «з» ... перетворюються на «жч»` is false. The examples in the same paragraph come from different alternation patterns, so the explanation is grammatically wrong.  
Fix: Replace the paragraph with an accurate explanation that these are several different alternations and that learners should memorize them through examples.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: end of module: `<!-- INJECT_ACTIVITY: match-up-superlatives-match-adjective-to-its-superlative-form -->`, `<!-- INJECT_ACTIVITY: true-false-comparative-constructions-identify-correct-and-incorrect-comparative-constructions -->`, `<!-- INJECT_ACTIVITY: fill-in-comparative-form-the-comparative-from-the-base-adjective -->`  
Issue: These three markers duplicate activity types already placed after the relevant teaching sections. They are clustered at the end and are not aligned with the 5 hinted activity types in the plan.  
Fix: Remove the three duplicate end markers.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: several grammar boxes, e.g. `<!-- VERIFY -->*самий великий*`, `<!-- VERIFY -->*більш кращий*`, `<!-- VERIFY -->*самий*`  
Issue: Raw verification comments were left in learner-facing content.  
Fix: Remove all `<!-- VERIFY -->` comments from the prose.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: **Найвищий ступінь**, paragraph beginning `Завжди звертайте увагу на чистоту вашої мови.`  
Issue: The paragraph moralizes grammar (`чистота вашої мови`, `Це покаже вашу повагу до культури`) and frames the point as language policing rather than standard usage guidance.  
Fix: Replace it with neutral wording about standard Ukrainian usage.

## Verdict: REVISE
REVISE. The module has critical factual grammar errors, plus major exercise-structure, cultural-tone, and formatting issues. Multiple dimensions are below 9, and the severity gate is not met.

<fixes>
- find: |-
    Коли ми додаємо суфікс «-ший», деякі приголосні звуки змінюються. Це регулярний фонетичний процес. Якщо основа прикметника закінчується на літери «г», «ж» або «з», ми маємо зміну. Ці звуки разом із суфіксом перетворюються на «жч». Наприклад, слово «дорогий» стає словом «дорожчий». Слово «близький» перетворюється на «ближчий». Інше важливе правило стосується літери «с». Якщо основа має літеру «с» в кінці, вона перетворюється на «щ». Тому слово «високий» стає словом «вищий». Також суфікси «-к-», «-ок-», «-ек-» зазвичай випадають перед утворенням нової форми. Слово «тонкий» перетворюється на «тонший», а слово «глибокий» стає словом «глибший». Спочатку ці зміни здаються складними, але ви швидко до них звикнете.
  replace: |-
    Коли ми додаємо суфікс «-ший», у деяких прикметниках відбуваються чергування приголосних. Наприклад, слово «дорогий» стає словом «дорожчий», «близький» перетворюється на «ближчий», а «високий» — на «вищий». Також у словах на кшталт «тонкий» і «глибокий» маємо форми «тонший» та «глибший». Тут працюють різні моделі чергування, тому не варто зводити всі такі форми до одного правила. Найкраще запам'ятовувати їх разом із конкретними прикладами.
- find: |-
    Як правильно побудувати речення для порівняння двох предметів? Ми маємо два зручні варіанти. Перший варіант використовує слово **ніж** (than) та називний відмінок. Наприклад: «Київ **більший** (bigger), ніж Львів». Це дуже чітка і зрозуміла конструкція. Другий варіант використовує прийменники «за» або «від» та знахідний відмінок. Наприклад: «Київ більший за Львів». Обидва варіанти є абсолютно правильними та взаємозамінними. Ви можете вільно обирати той, який вам більше подобається. Мій новий телефон **менший** (smaller), але він набагато кращий за старий. У розмовній мові українці дуже часто використовують прийменник «за». Конструкція зі словом «ніж» трохи частіше зустрічається в текстах. Головне правило — завжди пам'ятати про правильний відмінок після цих маленьких слів.
  replace: |-
    Як правильно побудувати речення для порівняння двох предметів? Ми маємо три нормативні варіанти. Перший варіант використовує слово **ніж** (than) та називний відмінок. Наприклад: «Київ **більший** (bigger), ніж Львів». Другий варіант використовує прийменник «за» та знахідний відмінок: «Київ більший за Львів». Третій варіант використовує прийменник «від» та родовий відмінок: «Київ більший від Львова». Усі три конструкції є правильними. Мій новий телефон **менший** (smaller), але він набагато кращий за старий. У розмовній мові українці дуже часто використовують прийменник «за». Головне правило — завжди пам'ятати про правильний відмінок після цих маленьких слів.
- find: "Remember to always use the prepositions **за** or **від** + Accusative, or the conjunction **ніж** + Nominative when comparing two items. Avoid using the naked Genitive case, which is a grammatical transfer from Russian."
  replace: "Remember to use **за** + Accusative, **від** + Genitive, or **ніж** + Nominative when comparing two items. Avoid using the bare Genitive without a linking word."
- find: |-
    Завжди звертайте увагу на чистоту вашої мови. Використання слова «самий» для утворення найвищого ступеня є грубою помилкою. Це пряме запозичення з російської граматики, яке псує красу українського речення. Справжня українська мова вимагає використання виключно префікса «най-». Тому ми завжди говоримо «найбільший» замість помилкового варіанту. Ми кажемо «найкращий», коли описуємо щось ідеальне. Якщо ви чуєте слово «самий» поруч із прикметником, знайте правду. Це звичайна мовна калька. Ваша мета — говорити правильно і природно. Тому обирайте традиційні українські префікси. Це покаже вашу повагу до культури.
  replace: |-
    У стандартній українській мові для найвищого ступеня краще вживати форми з префіксом «най-» або конструкції з «найбільш» і «найменш». Тому ми говоримо «найбільший» і «найкращий». Якщо ви чуєте слово «самий» поруч із прикметником у значенні найвищого ступеня, орієнтуйтеся на літературну норму: «найбільший», «найкращий», «найбільш цікавий». Так ваше мовлення буде точним і природним.
- find: "(e.g., <!-- VERIFY -->*самий великий*, <!-- VERIFY -->*самий кращий*)."
  replace: "(e.g., *самий великий*, *самий кращий*)."
- find: "Forms like <!-- VERIFY -->*більш кращий* or <!-- VERIFY -->*найбільш найпопулярніший* are logically redundant and incorrect."
  replace: "Forms like *більш кращий* or *найбільш найпопулярніший* are logically redundant and incorrect."
- find: "Always say **кращий**, never <!-- VERIFY -->*більш кращий*."
  replace: "Always say **кращий**, never *більш кращий*."
- find: "Finally, never use the word <!-- VERIFY -->*самий* to form the superlative; this is a direct Russianism. Always use the `най-` prefix instead."
  replace: "Finally, in neutral standard usage, prefer the `най-` prefix or the forms `найбільш/найменш` instead of *самий* + adjective."
- find: |-
    <!-- INJECT_ACTIVITY: match-up-superlatives-match-adjective-to-its-superlative-form -->
    <!-- INJECT_ACTIVITY: true-false-comparative-constructions-identify-correct-and-incorrect-comparative-constructions -->
    <!-- INJECT_ACTIVITY: fill-in-comparative-form-the-comparative-from-the-base-adjective -->
  replace: ""
</fixes>