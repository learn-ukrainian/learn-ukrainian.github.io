## Linguistic Scan
Errors found. "Кружка" is a widely recognized Russianism (colloquialism) for mug, and standard Ukrainian uses "чашка" or "кухоль". More critically, there is a severe linguistic/phonetic hallucination: the writer claims the consonant alternation in "подрузі" is **к** to **ц**, but the nominative is "подруга" (stem ends in **г**), so the alternation is actually **г** to **з**. Additionally, the rule explanation for stating age mentions "рік або років", omitting "роки" for 2, 3, 4.

## Exercise Check
All four `<!-- INJECT_ACTIVITY: ... -->` markers are present. However, there is a structural flaw in placement:
- `<!-- INJECT_ACTIVITY: match-verbs-to-case -->` is placed at the end of Part 2, but it tests dative-governing verbs (`подарувати`, `допомагати`, `дякувати`) which are formally taught in Part 3. The marker must be moved to the end of Part 3.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covered almost all points, but failed to perfectly align the activity injections with the lesson pacing. |
| 2. Linguistic accuracy | 7/10 | Critical hallucination regarding phonetic rules ("change **к** to **ц** in **подрузі**" instead of **г** to **з**). Rule for age omits "роки" in the text description: "числа, та слова рік або років." Writer also used the Russianism "кружка", even though it was technically suggested by the plan. |
| 3. Pedagogical quality | 8/10 | Excellent PPP flow and clear English explanations, but teaching an incomplete age rule ("рік або років") creates a gap for learners who then see "три роки" in the examples. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words from the plan were integrated naturally. |
| 5. Exercise quality | 7/10 | The `match-verbs-to-case` activity is injected before the concept (dative-governing verbs) is explicitly taught in Part 3. |
| 6. Engagement & tone | 10/10 | Good teacher persona without generic, corporate-style enthusiasm. Encouraging and structured. |
| 7. Structural integrity | 10/10 | Clean markdown, target word count met (1647 words > 1500 target), all sections present. |
| 8. Cultural accuracy | 10/10 | Secret Santa situation is culturally familiar in modern Ukrainian offices, and envelope addressing follows authentic Ukrainian norms. |
| 9. Dialogue & conversation quality | 9/10 | Office dialogue is natural and demonstrates multiple Dative usages, though it relied on the sub-optimal word "кружка". |

## Findings

[Linguistic accuracy] [Critical]
Location: Частина 4 (Self-check list): "2. Do I remember to change **к** to **ц** in **подрузі**?"
Issue: The writer hallucinates the consonant alternation for "подруга". The stem ends in "г" (подруг-а), so the alternation is "г" to "з" (подрузі). Changing "к" to "ц" is completely wrong for this specific word.
Fix: Change "к to ц" to "г to з".

[Linguistic accuracy] [Major]
Location: Частина 3: "Конструкція складається з людини у давальному відмінку, числа, та слова рік або років."
Issue: The explanation of the age rule omits the word "роки" (used for 2, 3, 4), although the writer correctly uses it in the immediate example "три роки". Teaching only "рік" or "років" provides an incomplete grammatical rule.
Fix: Update the text to include "роки".

[Linguistic accuracy] [Minor]
Location: Частина 2: "**Новому колезі** — красиву кружку. *(To the new colleague — a beautiful mug.)*"
Issue: The word "кружка" is a Russianism/Surzhyk for "mug" in standard Ukrainian. Even though it was given in the plan, the writer should have opted for the standard "чашка" (or "кухоль").
Fix: Change "кружку" to "чашку".

[Exercise quality] [Major]
Location: End of Part 2
Issue: The `<!-- INJECT_ACTIVITY: match-verbs-to-case -->` marker is placed at the end of Part 2, before the dative-governing verbs (like дякувати, допомагати) are explicitly taught in Part 3. It must be moved to test the material after it is presented.
Fix: Move the marker from the end of Part 2 to the end of Part 3.

## Verdict: REVISE
The module contains a critical phonetic hallucination (г->з incorrectly taught as к->ц), an incomplete pedagogical rule for age, and misaligned activity injection. These flaws must be fixed before publishing.

<fixes>
- find: "2. Do I remember to change **к** to **ц** in **подрузі**?"
  replace: "2. Do I remember to change **г** to **з** in **подрузі**?"
- find: "Конструкція складається з людини у давальному відмінку, числа, та слова рік або років."
  replace: "Конструкція складається з людини у давальному відмінку, числа, та слова рік, роки або років."
- find: "**Новому колезі** — красиву кружку. *(To the new colleague — a beautiful mug.)*"
  replace: "**Новому колезі** — красиву чашку. *(To the new colleague — a beautiful mug.)*"
- find: "<!-- INJECT_ACTIVITY: fill-in-dative-endings -->\n\n<!-- INJECT_ACTIVITY: match-verbs-to-case -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-dative-endings -->"
- find: "<!-- INJECT_ACTIVITY: error-correction-dative -->"
  replace: "<!-- INJECT_ACTIVITY: match-verbs-to-case -->\n\n<!-- INJECT_ACTIVITY: error-correction-dative -->"
</fixes>
