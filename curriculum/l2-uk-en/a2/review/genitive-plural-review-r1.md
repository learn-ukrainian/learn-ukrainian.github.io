## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym confusions, or banned Russian letters (`ы, э, ё, ъ`) found.

Factual grammar errors found:
- The module repeatedly teaches plain plural instead of genitive plural: `Сьогодні ми вивчаємо родовий відмінок. Це **множина** іменників.` and `This is the **plural** of nouns.`
- The same terminology error recurs in the feminine section: `requires the Genitive **множина** (plural).`
- The neuter section repeats the same mistake: `When forming the **множина** (plural), you simply drop the final vowel.`
- The special-declension paragraph also says `when they form the plural` even though the forms discussed are genitive plural (`імен`, `телят`, `кошенят`).
- The quantity-word rule is overgeneralized: `Whenever you use words like **багато** ... you must use the Genitive plural.` The same module later correctly uses `багато соку`, which is genitive singular, so the rule as stated is false.

## Exercise Check
- 4 markers found: `match-up-masculine`, `quiz-genitive-endings`, `group-sort-endings`, `fill-in-all-genders`.
- Count matches the 4 `activity_hints` in the plan.
- Placement is logical: the match-up follows the masculine section; the quiz comes after the ending patterns are introduced; the group-sort and fill-in are cumulative and appear after all three genders.
- No marker-placement or exercise-count problems found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All three planned sections and core patterns are present, but the lesson repeatedly drifts from the plan’s target `Родовий відмінок множини` by calling it plain `множина`: `Це **множина** іменників.` |
| 2. Linguistic accuracy | 6/10 | Most forms are correct (`пісень`, `статей`, `морів`, `очей`), but the grammar explanations contain factual errors: `This is the **plural** of nouns`, `Genitive **множина** (plural)`, and `when they form the plural`. |
| 3. Pedagogical quality | 6/10 | There are many examples and dialogues, but the module misdefines the core topic and overgeneralizes the rule for quantity words: `Whenever you use words like **багато** ... you must use the Genitive plural`, even though the dialogue itself has `багато соку`. |
| 4. Vocabulary coverage | 9/10 | Required plan vocabulary is well covered in context: `множина`, `нульове закінчення`, `кілька`, `багато`, `мало`, `скільки`, `стаття`, `завдання`, `питання`, `людина/люди`. |
| 5. Exercise quality | 9/10 | The four exercise markers match the plan’s types and are placed after the relevant teaching blocks, with cumulative practice saved for the end. |
| 6. Engagement & tone | 9/10 | The module generally sounds like a teacher and uses concrete examples rather than gamified fluff. |
| 7. Structural integrity | 10/10 | All H2 sections are present and ordered correctly, markers are clean, and the pipeline word count is 2998, comfortably above the 2000 target. |
| 8. Cultural accuracy | 10/10 | No Russian-centered framing or cultural inaccuracies were found; the examples stay within Ukrainian contexts. |
| 9. Dialogue & conversation quality | 8/10 | Dialogues use named speakers and plausible situations, but some lines are stiff, especially `Тоді запиши: вода, мед і багато булок.` |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: masculine opening — `Сьогодні ми вивчаємо родовий відмінок. Це **множина** іменників.` / `*Today we are studying the Genitive case. This is the **plural** of nouns.*`  
Issue: The lesson defines the target as plain plural instead of genitive plural. This teaches the wrong grammatical category.  
Fix: Replace both Ukrainian and English wording with `родовий відмінок множини` / `Genitive plural of nouns`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: feminine opening — `requires the Genitive **множина** (plural)`  
Issue: This hybrid term is wrong and again collapses genitive plural into plain plural.  
Fix: Replace it with `Genitive plural`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: neuter opening — `When forming the **множина** (plural), you simply drop the final vowel.`  
Issue: The section again labels the target as plural rather than genitive plural.  
Fix: Change the wording to `When forming the Genitive plural...`

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: special-declension paragraph — `They undergo unique stem changes when they form the plural.`  
Issue: The forms discussed here are genitive plural forms (`імен`, `телят`, `кошенят`), so the explanation is grammatically mislabeled.  
Fix: Change `when they form the plural` to `when they form the Genitive plural`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: opening rule and summary — `We also use this form after the question word **скільки** ... and words denoting quantity...` / `Whenever you use words like **багато** ... you must use the Genitive plural.`  
Issue: This is overgeneralized and internally contradicted by the module’s own `багато соку`, where the noun is genitive singular. The rule needs to be restricted to countable nouns in this lesson.  
Fix: Qualify the rule with `when we talk about countable nouns` / `коли йдеться про злічувані предмети`.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: minor]  
Location: inventory dialogue — `Тоді запиши: вода, мед і багато булок.`  
Issue: The closing line sounds stiff and list-like rather than like live shop speech.  
Fix: Rephrase it as a natural instruction about ordering the missing items.

## Verdict: REVISE
Multiple critical findings teach the wrong grammar category (`plural` instead of `genitive plural`) and overstate the quantity-word rule. The module’s structure, examples, and exercise placement are otherwise solid enough for targeted fixes rather than a full rebuild.

<fixes>
- find: "Сьогодні ми вивчаємо родовий відмінок. Це **множина** іменників. Коли ми рахуємо **людей** або предмети, нам потрібна ця форма."
  replace: "Сьогодні ми вивчаємо родовий відмінок множини іменників. Коли ми рахуємо **людей** або предмети, нам потрібна саме ця форма."
- find: "*Today we are studying the Genitive case. This is the **plural** of nouns. When we count **people** or objects, we need this form. If you have five or ten items, you change the word. We also use this form after the word **how many**. When there are **a lot**, **a little**, or just **a few** objects, we change the ending.*"
  replace: "*Today we are studying the Genitive plural of nouns. When we count **people** or objects, we need this form. If you have five or ten items, you change the word. We also often use this form after **how many** and after quantity words when we talk about countable things. When there are **a lot**, **a few**, or only a small number of objects, we change the ending.*"
- find: "We also use this form after the question word **скільки** (how many) and words denoting quantity, such as **багато** (a lot, many), **мало** (a little, few), and **кілька** (a few, several)."
  replace: "We also often use this form after the question word **скільки** (how many) and after quantity words such as **багато** (a lot, many), **мало** (few), and **кілька** (a few, several) when we talk about countable nouns."
- find: "Ми також використовуємо цю форму після слова **скільки**. Коли предметів **багато**, **мало** або є лише **кілька**, ми змінюємо закінчення."
  replace: "Ми також часто використовуємо цю форму після слова **скільки** та після слів **багато**, **мало** і **кілька**, коли йдеться про злічувані предмети."
- find: "In the dialogue, counting feminine nouns like \"пляшка\" (bottle) or \"банка\" (jar) with numbers from five upwards requires the Genitive **множина** (plural)."
  replace: "In the dialogue, counting feminine nouns like \"пляшка\" (bottle) or \"банка\" (jar) with quantity words and with numbers from five upward requires the Genitive plural."
- find: "Neuter nouns with hard stems ending in **-о** behave very much like feminine nouns. When forming the **множина** (plural), you simply drop the final vowel."
  replace: "Neuter nouns with hard stems ending in **-о** behave very much like feminine nouns. When forming the Genitive plural, you usually drop the final vowel."
- find: "Neuter nouns ending in **-тя** and words for young animals belong to a special declension group. They undergo unique stem changes when they form the plural."
  replace: "Neuter nouns ending in **-тя** and words for young animals belong to a special declension group. They undergo unique stem changes when they form the Genitive plural."
- find: "Whenever you use words like **багато** (a lot, many), **кілька** (a few, several), or **мало** (a little, few), you must use the Genitive plural."
  replace: "Whenever you use words like **багато** (a lot, many), **кілька** (a few, several), or **мало** (few) with countable nouns, you normally use the Genitive plural."
- find: "The same rule applies when you ask **скільки** (how many)."
  replace: "The same rule applies when you ask **скільки** about countable nouns."
- find: "> — **Продавець:** Зрозуміло. Тоді запиши: вода, мед і багато булок. *(Understood. Then write it down: water, honey, and a lot of buns.)*"
  replace: "> — **Продавець:** Зрозуміло. Тоді запиши: воду, мед і булки треба замовити. *(Understood. Then write it down: we need to order water, honey, and buns.)*"
</fixes>