## Linguistic Scan
[Linguistic accuracy] Factual grammar error found.

Location: `:::caution ... While **і** simply adds information together, **а** is used to show a direct contrast between two distinct objects. Use **але** when you are contrasting two qualities of the exact same object. :::`

Issue: This teaches an over-restrictive and incorrect rule. Dictionary evidence shows both **а** and **але** can mark adversative contrast; **але** is not limited to “two qualities of the exact same object.”

Fix: Replace the rule with a weaker, accurate explanation: **і** adds information; **а** and **але** both express contrast, with **але** typically sounding stronger.

No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian letters were found in the Ukrainian examples.

## Exercise Check
`quiz-question-word`, `fill-in-endings`, `match-up-opposites`, and `fill-in-describe-room` are all present.

The marker IDs align with the four `activity_hints`, and placement is mostly appropriate: the quiz and endings fill-in come after the question-word explanation, and the opposites/description tasks come after the adjective section.

No exercise-logic defect is visible from the marker-only source.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All four planned H2 sections are present and the module cites **Вашуленко Grade 3, p.131** and **Пономарова Grade 3, p.98**, but the plan grammar includes `який/яка/яке/які` and `які` appears 0 times in the prose; the second dialogue also uses `сумка/телефон` instead of the plan’s stated book-fair item set. |
| 2. Linguistic accuracy | 8/10 | The Ukrainian examples themselves are morphologically correct, but the caution box gives a factually wrong rule for `а` vs `але`. |
| 3. Pedagogical quality | 7/10 | The module has a usable present-explain-practice flow and many examples, but it under-teaches the planned paradigm by omitting `які`, and it gives learners an incorrect contrast rule. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary appears in prose (`великий, маленький, новий, старий, гарний, чистий, дорогий, дешевий`), and recommended vocabulary also appears (`поганий, брудний, світлий, темний, а, але`). |
| 5. Exercise quality | 9/10 | Four markers are present for four planned activities, and each marker sits after the relevant teaching section. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and concrete, with usable examples like `Моя кімната велика і світла.` and `Вікно велике і чисте.`; it avoids gamified/corporate framing. |
| 7. Structural integrity | 5/10 | Headings are clean and ordered correctly, but the pipeline word count is **1029**, below the **1200** target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms and uses Ukrainian school-textbook references without Russia-centric framing. |
| 9. Dialogue & conversation quality | 6/10 | The dialogues have named speakers and clear turns, but dialogue 2 is thin and misses the plan’s specified weekend book-fair situation. |

## Findings
[Plan adherence] [SEVERITY: major]  
Location: `In the second dialogue, they stop at a shop window and describe what they see.` ... `**Софія:** Яка гарна сумка!` ... `**Софія:** А телефон? Який він?`  
Issue: The plan’s `dialogue_situations` specifies a weekend book fair with `книга, атлас, фото, плакат, листівка` and explicitly says “NOT bags or furniture.” The module instead uses `сумка` and `телефон`.  
Fix: Replace the second dialogue with a book-fair exchange using the planned item set.

[Plan adherence] [SEVERITY: major]  
Location: `To ask "what kind?" in Ukrainian, match the question word to the noun’s gender: **який** for masculine, **яка** for feminine, and **яке** for neuter.`  
Issue: The plan grammar includes `який/яка/яке/які`, but the module teaches only singular forms. Search check: `які` appears 0 times in the module prose.  
Fix: Add a short plural subsection with `які` plus 2-4 plural examples.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `While **і** simply adds information together, **а** is used to show a direct contrast between two distinct objects. Use **але** when you are contrasting two qualities of the exact same object.`  
Issue: This is a wrong grammar rule. Both **а** and **але** can express contrast; **але** is not restricted to “two qualities of the exact same object.”  
Fix: Rewrite the note so it distinguishes additive **і** from contrastive **а/але**, without inventing a false distribution rule.

[Structural integrity] [SEVERITY: major]  
Location: `PIPELINE NOTE — Word count: 1029 words`  
Issue: The module is below the required 1200-word target.  
Fix: Insert additional directly relevant teaching content; the missing `які` explanation is the cleanest place to add it.

## Verdict: REVISE
REVISE. The module has one critical teaching error (`а` vs `але`) and multiple major plan/structure misses (wrong dialogue setting/items, missing `які`, and word count below target), so it does not meet the PASS gate.

<fixes>
- find: |
    In the second dialogue, they stop at a shop window and describe what they see.

    > **Софія:** Яка гарна сумка! *(What a beautiful bag!)*
    > **Тарас:** Так, але вона дорога. *(Yes, but it is expensive.)*
    > **Софія:** А телефон? Який він? *(And the phone? What kind is it?)*
    > **Тарас:** Він великий і дешевий. *(It is big and cheap.)*

    Here **гарна** and **дорога** match the feminine noun **сумка**, while **великий** and **дешевий** match the masculine noun **телефон**.
  replace: |
    In the second dialogue, they stop at a book fair stand and describe what they see.

    > **Софія:** Яка цікава книга! *(What an interesting book!)*
    > **Тарас:** Так, а ось новий атлас. *(Yes, and here is a new atlas.)*
    > **Софія:** А плакат? Який він? *(And the poster? What kind is it?)*
    > **Тарас:** Він великий. А листівка — маленька. *(It is big. And the postcard is small.)*

    Here **цікава** and **маленька** match the feminine nouns **книга** and **листівка**, while **новий** and **великий** match the masculine nouns **атлас** and **плакат**.
- insert_after: |
    * **Яке фото?** (What kind of photo?) → **Старе фото.** (An old photo.)
  content: |
    One more form is useful from the beginning: **які** for plural nouns. When you describe more than one object, both the question word and the adjective move to the plural. This lets you talk about groups of familiar things from this module, not only single objects.

    * **Які плакати?** (What kind of posters?) → **Нові плакати.** (New posters.)
    * **Які вікна?** (What kind of windows?) → **Чисті вікна.** (Clean windows.)
    * **Які листівки?** (What kind of postcards?) → **Маленькі листівки.** (Small postcards.)

    The form **які** does not mark masculine, feminine, or neuter. It simply marks “more than one.” Compare the singular and plural patterns aloud:

    * **Який плакат?** → **Великий плакат.**
    * **Які плакати?** → **Великі плакати.**
    * **Яке вікно?** → **Чисте вікно.**
    * **Які вікна?** → **Чисті вікна.**

    The main focus of this module is singular agreement, so you do not need to memorize every plural ending yet. For now, notice the pattern: singular nouns use **який / яка / яке**, while plural nouns use **які**. If you read signs, labels, or fair displays, this form appears naturally, so seeing it now makes the full system easier to recognize later.
- find: |
    :::caution
    Pay close attention to the small conjunctions. While **і** simply adds information together, **а** is used to show a direct contrast between two distinct objects. Use **але** when you are contrasting two qualities of the exact same object.
    :::
  replace: |
    :::caution
    Pay close attention to the small conjunctions. **і** simply adds information together. Both **а** and **але** can express contrast, but **а** is often milder when comparing two items, while **але** usually sounds stronger as “but.”
    :::
</fixes>