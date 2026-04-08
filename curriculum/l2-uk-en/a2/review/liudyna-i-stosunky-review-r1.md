## Linguistic Scan
Errors found:
1. **Calques / Surzhyk**: The text repeatedly uses the verb "виглядати" to mean "to look (appearance)" (e.g., «Як вона виглядає?», «Він виглядає дуже серйозно»). In normative Ukrainian (explicitly taught in Grade 11 textbooks as an "Антисуржик" rule), "виглядати" means "to look out" (e.g., from a window). The correct phrasing for appearance is "мати вигляд" or "бути на вигляд" (e.g., "Який він має вигляд?", "Він має дуже серйозний вигляд").
2. **Calque**: The phrase "Вона має гарну зовнішність" is an unnatural, literal translation of the English phrase "She has a beautiful appearance." Natural Ukrainian phrasing is "У неї гарна зовнішність" or simply "Вона дуже гарна."

## Exercise Check
- `<!-- INJECT_ACTIVITY: match-character-traits -->`: Correctly placed after the Character section. Tests what was just taught.
- `<!-- INJECT_ACTIVITY: quiz-character-choice -->`: Correctly placed after the Character section.
- `<!-- INJECT_ACTIVITY: group-sort-traits -->`: Misplaced. It is currently located after the "People Around Us" section (Section 3), but it focuses on sorting personality adjectives into positive and challenging traits, which was taught in Section 2. It must be moved to immediately follow Section 2.
- `<!-- INJECT_ACTIVITY: fill-in-adjective-agreement -->`: Acceptably placed after Section 3 as a concluding review of adjectives used in the preceding sections.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module misses the required `з + instrumental` preview construction from the plan (e.g., "Вона з карими очима") and relies entirely on "У неї..." and compound adjectives. It also misses the compound adjectives `світловолосий` and `темноволосий`. Furthermore, the specific dialogue setup planned for Section 1 (contrasting imperfective/perfective "допомагає/допоміг") is missing from the first dialogue. |
| 2. Linguistic accuracy | 6/10 | Repeated use of the calque/surzhyk "виглядати" for appearance ("Як виглядає твій новий колега?", "Він виглядає дуже серйозно"). Textbooks classify this as incorrect, preferring "мати вигляд". Additionally, "Вона має гарну зовнішність" is an unnatural literal translation. |
| 3. Pedagogical quality | 9/10 | The text follows the PPP flow beautifully, with numerous well-integrated contrast examples. However, failing to introduce the planned `з + instrumental` construction removes an important stepping stone. |
| 4. Vocabulary coverage | 9/10 | Most required vocabulary is present, but the word `стосунок` (relationship), which is explicitly required by the plan, is missing (the English word "relationships" is used in Section 3 without its Ukrainian equivalent). `світловолосий` and `темноволосий` are also omitted. |
| 5. Exercise quality | 8/10 | Exercises match the plan's focus, but `group-sort-traits` is placed after the wrong section, creating a pedagogical disconnect between the teaching of character traits and the subsequent test. |
| 6. Engagement & tone | 10/10 | Excellent teacher persona. The cultural notes (e.g., the significance of "добра людина" over "красива людина", and the positive connotation of "впертий") are fantastic and engaging. |
| 7. Structural integrity | 10/10 | The module exceeds the 2000-word target (3168 words), provides all required sections, and maintains clean formatting. |
| 8. Cultural accuracy | 10/10 | Strong, decolonized explanations of how Ukrainians view and describe people and relationships (e.g., the distinction between a "знайомий", "товариш", and a true "друг"). |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are natural and correctly formatted. They don't perfectly align with the specific situational prompts in the plan, but they function well in context. |

## Findings
[Dimension 1] [critical]
Location: Section 1 (Appearance: What Does a Person Look Like?)
Issue: The plan explicitly requires teaching the `з + instrumental` preview for appearance ("Вона з карими очима"), but the text only teaches "У неї..." and compound adjectives.
Fix: Add the `з + instrumental` construction to the explanation paragraph.

[Dimension 1] [major]
Location: Section 1 (Appearance: What Does a Person Look Like?)
Issue: Missing planned core vocabulary: `світловолосий`, `темноволосий`.
Fix: Add these compound adjectives to the hair description paragraph.

[Dimension 2] [critical]
Location: Section 1, Section 2 dialogues, and Summary
Issue: Repeated use of the calque "виглядати" to mean "to look like/appear". This is officially taught as a surzhyk error in Ukrainian schools; the correct normative phrasing uses "вигляд" (мати вигляд / на вигляд).
Fix: Replace instances of "Як виглядає...?", "Він виглядає..." with "Який на вигляд...?" and "Він має... вигляд".

[Dimension 2] [major]
Location: Section 1 bullet points
Issue: The phrase "Вона має гарну зовнішність" is an unnatural calque.
Fix: Change to "У неї гарна зовнішність."

[Dimension 4] [major]
Location: Section 3 (Люди навколо нас)
Issue: The required vocabulary word `стосунок` (relationships) is missing from the text; only the English translation is used in the explanation.
Fix: Add the Ukrainian word `стосунки` to the explanation.

[Dimension 5] [major]
Location: Exercise inject markers after Section 3
Issue: The `group-sort-traits` activity is placed after the relationships section rather than the character traits section, causing a pedagogical sequence error.
Fix: Move the `group-sort-traits` marker to immediately follow the `quiz-character-choice` marker at the end of Section 2.

## Verdict: REVISE
The module contains excellent cultural context and explanations, but it repeatedly uses the pervasive calque/surzhyk "виглядати" for physical appearance, which violates the strict decolonized linguistic standards (and formal school curriculum rules) of the project. Additionally, minor plan deviations (missing `з + instrumental`, misplaced exercise marker, and a missing vocabulary word) must be corrected.

<fixes>
- find: |-
    To ask what someone looks like, we use the question: «Як він виглядає?» (What does he look like?) or «Як вона виглядає?» (What does she look like?).
  replace: |-
    To ask what someone looks like, we use the question: «Який він на вигляд?» (What does he look like?) or «Яка вона на вигляд?» (What does she look like?).
- find: |-
    *   Як виглядає твій новий колега? *(What does your new colleague look like?)*
  replace: |-
    *   Який на вигляд твій новий колега? *(What does your new colleague look like?)*
- find: |-
    *   Як вона виглядає? *(What does she look like?)*
  replace: |-
    *   Яка вона на вигляд? *(What does she look like?)*
- find: |-
    *   Вона має гарну зовнішність. *(She has a beautiful appearance.)*
  replace: |-
    *   У неї гарна зовнішність. *(She has a beautiful appearance.)*
- find: |-
    You can use the construction «У нього/неї...» (He/she has...) or form a compound adjective like **кароока** (brown-eyed). For example, «У неї карі очі» (She has brown eyes) and «Вона кароока» mean the exact same thing.
  replace: |-
    You can use the construction «У нього/неї...» (He/she has...), use the preposition **з** + instrumental (with), or form a compound adjective like **кароока** (brown-eyed). For example, «У неї карі очі» (She has brown eyes), «Вона з карими очима» (She is with brown eyes), and «Вона кароока» mean the exact same thing.
- find: |-
    In Ukrainian, hair color is often described as **темне** (dark), **світле** (light/fair), **русяве** (light brown), **руде** (red), or **сиве** (grey). For length and style, we use **коротке** (short), **довге** (long), **хвилясте** (wavy), and **пряме** (straight).
  replace: |-
    In Ukrainian, hair color is often described as **темне** (dark), **світле** (light/fair), **русяве** (light brown), **руде** (red), or **сиве** (grey). You can also use compound adjectives like **темноволосий** (dark-haired) and **світловолосий** (fair-haired). For length and style, we use **коротке** (short), **довге** (long), **хвилясте** (wavy), and **пряме** (straight).
- find: |-
    > — **Марія:** Він виглядає дуже серйозно. *(He looks very serious.)*
  replace: |-
    > — **Марія:** Він має дуже серйозний вигляд. *(He looks very serious.)*
- find: |-
    > — **Оксана:** Який він? Він виглядає дуже серйозним. *(What is he like? He looks very serious.)*
  replace: |-
    > — **Оксана:** Який він? Він має дуже серйозний вигляд. *(What is he like? He looks very serious.)*
- find: |-
    How do we act toward these people? To describe relationships, we use specific verbs of interaction.
  replace: |-
    How do we act toward these people? To describe relationships (**стосунки**), we use specific verbs of interaction.
- find: |-
    <!-- INJECT_ACTIVITY: match-character-traits -->
    <!-- INJECT_ACTIVITY: quiz-character-choice -->

    ## Люди навколо нас: родичі, друзі, знайомі (People Around Us)
  replace: |-
    <!-- INJECT_ACTIVITY: match-character-traits -->
    <!-- INJECT_ACTIVITY: quiz-character-choice -->
    <!-- INJECT_ACTIVITY: group-sort-traits -->

    ## Люди навколо нас: родичі, друзі, знайомі (People Around Us)
- find: |-
    <!-- INJECT_ACTIVITY: fill-in-adjective-agreement -->
    <!-- INJECT_ACTIVITY: group-sort-traits -->

    ## Описуємо людину цілком (Describing a Person Fully)
  replace: |-
    <!-- INJECT_ACTIVITY: fill-in-adjective-agreement -->

    ## Описуємо людину цілком (Describing a Person Fully)
- find: |-
    1. **Як виглядає ваша найкраща подруга?** *(What does your best friend look like?)*
  replace: |-
    1. **Яка на вигляд ваша найкраща подруга?** *(What does your best friend look like?)*
</fixes>
