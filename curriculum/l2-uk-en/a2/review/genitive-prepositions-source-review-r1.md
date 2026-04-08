## Linguistic Scan
Errors found:
1. "знаходиться" in the context of spatial location is a Russianism/calque (from "находиться").
2. "до їжі" is a lexical error; normative Ukrainian uses "до їди" for the temporal process of eating. 
3. "ранковий сніданок" is a tautology.

## Exercise Check
All four `INJECT_ACTIVITY` markers match the plan's `activity_hints` in ID, type, and count. They are placed correctly after their respective instructional sections (e.g., `quiz-euphony-variants` appears immediately after the "З/із/зі" euphony rule section). No DSL exercises were found inline, which is expected for A1/A2 modules utilizing the marker system.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Word count (3758) strongly exceeds the target (2000). However, required vocabulary words (`джерело`, `походження`) are missing from the text. Additionally, plan references (Заболотний, ULP) were not explicitly cited. |
| 2. Linguistic accuracy | 7/10 | Identified a Russianism calque ("знаходиться" instead of "розташовано" for location) and a semantic error ("до їжі" instead of the prescriptive normative "до їди"). |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. Introduces the situation naturally with an international dinner, explains grammar rules simply, and uses multiple context-rich examples. No overly long English theory blocks. |
| 4. Vocabulary coverage | 8/10 | Included almost all required and recommended words (e.g., `сніданок`, `вечеря`, `дитинство`, `шовк`), but missed `джерело` and `походження`. |
| 5. Exercise quality | 10/10 | Markers perfectly align with the `activity_hints` from the plan, and appear exactly where the concepts have just been taught. |
| 6. Engagement & tone | 10/10 | Warm, supportive teacher tone without being generic. The decolonization tip regarding "з України" is extremely valuable and engaging. |
| 7. Structural integrity | 10/10 | Clean Markdown. All H2 headings from the plan outline are present. The word count is well above the target. |
| 8. Cultural accuracy | 10/10 | Factually correct. Strong emphasis on euphony and a great decolonized rule addressing the "з України" vs obsolete colonial forms. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are multi-turn, very natural, and feature distinct voices. Minor deduction for a speaker using the tautology "ранкового сніданку". |

## Findings

[Plan adherence] [major]
Location: Entire module text
Issue: Required vocabulary words "джерело" and "походження" are missing, and plan references (Заболотний, ULP) are not cited.
Fix: Inject "джерело" and "походження" into the explanation of the preposition "з", and add a references callout before the summary.

[Linguistic accuracy] [critical]
Location: Section "Як далеко це знаходиться?"
Issue: The verb "знаходиться" used for "is located" is a widespread calque from Russian "находиться". Standard Ukrainian strictly prefers "розташовуватися" or "бути/стояти" for physical locations.
Fix: Replace "Як далеко це знаходиться?" with "Як далеко це розташовано?" and "Мій старий дім знаходиться далеко від центру" with "Мій старий дім розташований далеко від центру".

[Linguistic accuracy] [critical]
Location: Dialogue in "Що було потім? Після + родовий"
Issue: "Я не можу пити каву до їжі" contains a lexical error. "Їжа" refers to food as a physical substance, while the process of eating is "їда". The normative temporal construction is "до їди" / "після їди".
Fix: Replace "до їжі" with "до їди".

[Linguistic accuracy] [minor]
Location: Dialogue in "Що було потім? Після + родовий"
Issue: The phrase "ранкового сніданку" is a tautology (pleonasm) since a breakfast is already a morning meal by definition.
Fix: Remove the adjective to simply read "Після сніданку".

## Verdict: REVISE
The module is highly pedagogical, culturally rich, and excellently paced, making it extremely strong overall. However, it contains a critical calque ("знаходиться"), a semantic inaccuracy ("до їжі"), a tautology ("ранкового сніданку"), and missed some required vocabulary. These errors trigger the severity gate, requiring a revision through deterministic fixes.

<fixes>
- find: "Цей прийменник завжди вимагає після себе родовий відмінок. *(This preposition always requires the Genitive case after it.)*"
  replace: "Цей прийменник завжди вимагає після себе родовий відмінок. *(This preposition always requires the Genitive case after it.)*\nВін показує ваше походження або джерело дії. *(It shows your origin or the source of an action.)*"
- find: "Як далеко це знаходиться? *(How far is it located?)*"
  replace: "Як далеко це розташовано? *(How far is it located?)*"
- find: "— Мій старий дім знаходиться далеко від центру *(from the center)*."
  replace: "— Мій старий дім розташований далеко від центру *(from the center)*."
- find: "> — **Катерина:** Я розумію, але я не можу пити каву **до їжі**. *(I understand, but I cannot drink coffee before food.)*"
  replace: "> — **Катерина:** Я розумію, але я не можу пити каву **до їди**. *(I understand, but I cannot drink coffee before food.)*"
- find: "> — **Олег:** **Після ранкового сніданку** я відразу починаю працювати. *(After morning breakfast I immediately start working.)*"
  replace: "> — **Олег:** **Після сніданку** я відразу починаю працювати. *(After breakfast I immediately start working.)*"
- find: "## Підсумок — Summary"
  replace: ":::note Джерела\nЦей модуль використовує матеріали: Заболотний Grade 5, §31 та ULP: 10 Uses of Genitive Case.\n:::\n\n## Підсумок — Summary"
</fixes>
