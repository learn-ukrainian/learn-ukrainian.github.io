## Linguistic Scan
No linguistic errors found. The grammar explanations regarding the inanimate accusative case are highly accurate, and the distinction between the correct verb "замовляти" and the Russian calque "заказати" is excellent. The dialogue uses natural Ukrainian phrasing like "З вас сто двадцять гривень" and correctly applies the vocative case ("Іванко").

## Exercise Check
- `<!-- INJECT_ACTIVITY: match-up-functions -->` is injected after Section 1, but tests phrases from Sections 2 and 3 ("Скільки коштує?", "Тут вільно?"). This violates the rule against placing exercises before concepts are taught.
- `<!-- INJECT_ACTIVITY: fill-in-ordering-accusative -->` is correctly placed after Section 2.
- `<!-- INJECT_ACTIVITY: quiz-situation-choice -->` is correctly placed after Section 3.
- `<!-- INJECT_ACTIVITY: dialogue-completion-cafe -->` tests the dialogue from Section 1 and is currently placed at the end of the module. It should be swapped with `match-up-functions`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module covers almost all points, but missed two details from the plan: the phrase "Скільки коштує?" was omitted from Section 2 (only appearing in the Summary), and the distinction between a casual cafe (menu on wall) and a formal restaurant (menu at table) was omitted from Section 3. |
| 2. Linguistic accuracy | 10/10 | Excellent. Proper noun declension ("Іванко" as vocative), correct phrasing ("З вас сто двадцять гривень"), and explicit warning against the calque "заказати". |
| 3. Pedagogical quality | 10/10 | Great presentation of the PPP flow. The explanation of the accusative inanimate case ending rule ("only the main noun changes its ending") is crystal clear. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items from the plan are introduced naturally in context. |
| 5. Exercise quality | 8/10 | The exercises themselves match the plan, but `match-up-functions` tests concepts before they are taught, violating pedagogical flow. |
| 6. Engagement & tone | 10/10 | Warm and culturally insightful. The mention of Ukraine's high rate of contactless payment adds great real-world value. |
| 7. Structural integrity | 10/10 | Clean markdown, perfect section headings. Word count is 1402, well above the 1200 target. |
| 8. Cultural accuracy | 10/10 | Spot on regarding Lviv coffee culture, tipping etiquette, and modern payment habits in Ukraine. |
| 9. Dialogue & conversation quality | 10/10 | Very natural, multi-turn exchange. Uses realistic phrases like "одну хвилинку" and "Карткою чи готівкою?". |

## Findings
[1. Plan adherence] [major]
Location: Section 2 ("Як замовити — How to Order"), third paragraph: "In that situation, you simply point and ask: **А що це?** (And what is this?)."
Issue: The phrase "Скільки коштує?" is required by the plan outline but is missing from the teaching body (it only appears in the Summary).
Fix: Add "Скільки коштує?" when discussing asking questions about food.

[1. Plan adherence] [major]
Location: Section 3 ("Культура кафе — Cafe Culture"), third paragraph: "When you finish eating, there is an important point of etiquette regarding the **рахунок** (bill)."
Issue: The plan required explaining the difference between a cafe (casual, menu on wall) and a restaurant (formal, menu at table), which was omitted.
Fix: Insert this distinction right before discussing the bill etiquette.

[5. Exercise quality] [major]
Location: After Section 1 ("Діалоги") and Section 3 ("Культура кафе")
Issue: `match-up-functions` is injected immediately after the first section, testing phrases ("Скільки коштує?", "Тут вільно?") that haven't been taught yet. `dialogue-completion-cafe` is at the end of the module but tests Section 1 dialogue.
Fix: Swap the positions of `match-up-functions` and `dialogue-completion-cafe`.

## Verdict: REVISE
The module is beautifully written, highly authentic, and grammatically flawless. However, it requires a REVISE to insert two missing outline points and fix the chronological placement of the injected activities.

<fixes>
- find: "In that situation, you simply point and ask: **А що це?** (And what is this?)."
  replace: "In that situation, you simply point and ask: **А що це?** (And what is this?). To ask for the price, you say: **Скільки коштує?** (How much does it cost?)."
- find: "When you finish eating, there is an important point of etiquette regarding the **рахунок** (bill). In a traditional **ресторан** (restaurant) or a formal cafe, the waiter rarely brings the bill automatically."
  replace: "Before you pay, note the cultural difference between a **кафе** and a **ресторан**. A **кафе** is generally casual, and you might see the **меню** on the wall or a board. A **ресторан** is formal, and the waiter will always bring the menu to your table. When you finish eating, there is an important point of etiquette regarding the **рахунок** (bill). In a traditional **ресторан** (restaurant) or a formal cafe, the waiter rarely brings the bill automatically."
- find: |
    > **Офіціант:** Приходьте ще! *(Come again!)*

    <!-- INJECT_ACTIVITY: match-up-functions -->

    ## Як замовити — How to Order
  replace: |
    > **Офіціант:** Приходьте ще! *(Come again!)*

    <!-- INJECT_ACTIVITY: dialogue-completion-cafe -->

    ## Як замовити — How to Order
- find: |
    <!-- INJECT_ACTIVITY: quiz-situation-choice -->
    <!-- INJECT_ACTIVITY: dialogue-completion-cafe -->

    ## Підсумок — Summary
  replace: |
    <!-- INJECT_ACTIVITY: quiz-situation-choice -->
    <!-- INJECT_ACTIVITY: match-up-functions -->

    ## Підсумок — Summary
</fixes>
