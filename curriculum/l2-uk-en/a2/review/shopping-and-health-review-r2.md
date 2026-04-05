## Linguistic Scan
Errors found:
1. **Gender/Case Error**: The noun "нежить" is incorrectly treated as feminine. Its Genitive form is "нежитю" (masculine), not "нежиті".
2. **Calque**: "знаходиться" is used for physical location (a Russian calque of "находится").
3. **Calque**: "рецепт від болю" is a calque of "рецепт от боли" (standard Ukrainian uses "рецепт на [щось]").
4. **Calque/Style**: "коштують занадто дорого" is a colloquial calque.
5. **Semantic/Paronym**: "відкусила скибку" means to bite off an entire slice, rather than a piece ("шматок").

## Exercise Check
All four `<!-- INJECT_ACTIVITY: ... -->` markers from the plan are present.
- They match the `activity_hints` focus, type, and item counts exactly.
- They are placed logically after the relevant instructional content (market interactions, doctor visit, pharmacy).
- No issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Covers all grammar points and dialogues, but misses the English translations in the final two H2 headings from the `content_outline`. |
| 2. Linguistic accuracy | 6/10 | Contains a critical grammar error teaching the wrong gender for "нежить" (`**Нежить** (runny nose) becomes **нежиті**`), plus several structural calques (`знаходиться`, `рецепт від болю`). |
| 3. Pedagogical quality | 9/10 | Excellent PPP flow. Introduces situations, establishes patterns with explicit examples, and reinforces them. |
| 4. Vocabulary coverage | 10/10 | All required (`ринок`, `кілограм`, `здоров'я`, etc.) and recommended words (`алергія`, `шматок`) are used organically in context. |
| 5. Exercise quality | 10/10 | Markers perfectly map to the plan's activity targets and are spread evenly throughout the module. |
| 6. Engagement & tone | 9/10 | Dialogues are highly natural and contextualized ("Я сам робив. Дійсно дуже смачний сир"). |
| 7. Structural integrity | 8/10 | Clean markdown, but H2 headers deviate slightly from the plan's exact strings. |
| 8. Cultural accuracy | 10/10 | Accurately describes the lively Ukrainian market (базар) culture, tasting food before buying, and counting eggs by tens (десяток). |
| 9. Dialogue & conversation quality | 10/10 | Excellent multi-turn conversations reflecting real-world market and medical scenarios with polite forms and named speakers. |

## Findings

[Linguistic accuracy] [critical]
Location: "**Нежить** (runny nose) becomes **нежиті**." and "краплі від нежиті"
Issue: "Нежить" is a masculine noun in Ukrainian. Its Genitive singular form is "нежитю", not "нежиті" (which incorrectly treats it as feminine). `mcp_rag_verify_lemma` confirms it is `noun:inanim:m`.
Fix: Change "нежиті" to "нежитю" in the explanation and all dialogue examples.

[Linguistic accuracy] [major]
Location: "Де знаходиться **кабінет лікаря**? (Where is the doctor's office located?)."
Issue: Using "знаходиться" for physical location is a classic Russian calque. In Ukrainian, use "розташований", "міститься", or omit the verb entirely.
Fix: Change to "Де **кабінет лікаря**? (Where is the doctor's office located?)."

[Linguistic accuracy] [minor]
Location: "Ці яблука коштують занадто **дорого** для мене (these apples cost too expensive for me)."
Issue: "Коштувати дорого" is an awkward phrase (often considered a calque). The English translation "cost too expensive" is also ungrammatical.
Fix: Change to "Ці яблука занадто **дорогі** для мене (these apples are too expensive for me)."

[Linguistic accuracy] [minor]
Location: "Вона з радістю відкусила **скибку кавуна** (she happily took a bite of a slice of watermelon)."
Issue: "Відкусити скибку" means to bite off an entire slice. One bites off a piece ("шматок").
Fix: Change to "Вона з радістю відкусила **шматок кавуна** (she happily bit off a piece of watermelon)."

[Linguistic accuracy] [minor]
Location: "У лікаря пацієнт завжди просить **рецепт від болю** (prescription for pain)."
Issue: "Рецепт від болю" is an unnatural calque. Standard Ukrainian is "рецепт на ліки" or "на знеболювальне".
Fix: Change to "У лікаря пацієнт завжди просить **рецепт на знеболювальне** (prescription for painkillers)."

[Linguistic accuracy] [minor]
Location: "Ціна на ці помідори — це цілком **нормально** (the price for these tomatoes is normal)."
Issue: Grammatical mismatch between the feminine subject "ціна" and the neuter adverb "нормально" as a predicate.
Fix: Change to "Ціна на ці помідори цілком **нормальна** (the price for these tomatoes is normal)."

[Structural integrity] [minor]
Location: `## У лікаря: що вас турбує?` and `## В аптеці та повсякденне здоров'я`
Issue: Missing the English translations in the H2 headings that were specified in the plan's `content_outline`.
Fix: Add the translations to the headings to match the plan perfectly.

[Engagement & tone] [minor]
Location: `— **Клієнт:** Добрий день! **Що ви порадите від** (What do you advise for) кашлю? *(Good day! What do you advise for a cough?)*`
Issue: Redundant and disruptive English insertion in the middle of a Ukrainian dialogue line when a full sentence translation is already provided at the end.
Fix: Remove the mid-sentence English insertion.

## Verdict: REVISE
The module has excellent pedagogical flow and engaging cultural dialogues, but it contains a critical grammatical error regarding the gender of the core vocabulary word "нежить" (taught as feminine instead of masculine). Additionally, several Russian calques ("знаходиться", "рецепт від болю") need to be corrected before the module can be published.

<fixes>
- find: "## У лікаря: що вас турбує?"
  replace: "## У лікаря: що вас турбує? (At the Doctor: What Troubles You?)"
- find: "## В аптеці та повсякденне здоров'я"
  replace: "## В аптеці та повсякденне здоров'я (At the Pharmacy and Everyday Health)"
- find: "Де знаходиться **кабінет лікаря**? (Where is the doctor's office located?)."
  replace: "Де **кабінет лікаря**? (Where is the doctor's office located?)."
- find: "**Нежить** (runny nose) becomes **нежиті**."
  replace: "**Нежить** (runny nose) becomes **нежитю**."
- find: "Дайте, будь ласка, хороші **краплі від нежиті** (drops for runny nose)."
  replace: "Дайте, будь ласка, хороші **краплі від нежитю** (drops for runny nose)."
- find: "— **Пацієнт:** А ці краплі від нежиті? *(And these drops for a runny nose?)*"
  replace: "— **Пацієнт:** А ці краплі від нежитю? *(And these drops for a runny nose?)*"
- find: "Ці яблука коштують занадто **дорого** для мене (these apples cost too expensive for me)."
  replace: "Ці яблука занадто **дорогі** для мене (these apples are too expensive for me)."
- find: "Вона з радістю відкусила **скибку кавуна** (she happily took a bite of a slice of watermelon)."
  replace: "Вона з радістю відкусила **шматок кавуна** (she happily bit off a piece of watermelon)."
- find: "У лікаря пацієнт завжди просить **рецепт від болю** (prescription for pain)."
  replace: "У лікаря пацієнт завжди просить **рецепт на знеболювальне** (prescription for painkillers)."
- find: "Ціна на ці помідори — це цілком **нормально** (the price for these tomatoes is normal)."
  replace: "Ціна на ці помідори цілком **нормальна** (the price for these tomatoes is normal)."
- find: "**Що ви порадите від** (What do you advise for) кашлю?"
  replace: "**Що ви порадите від** кашлю?"
</fixes>
