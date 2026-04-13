## Linguistic Scan
No linguistic errors found.

## Exercise Check
All 4 plan-aligned activity markers are present and placed after the relevant teaching sections: `fill-in-dialogue`, `fill-in-accusative`, `quiz-situations`, `match-up-phrases`. The inline summary checklist is logically consistent with the taught phrases. No exercise-logic errors detected from the markers or inline content provided.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The prose never cites `ULP Season 1` or `State Standard 2024` (0 hits on search), the planned section budgets of 300 words are missed badly (`Діалоги` 475, `Як замовити` 598, `Культура кафе` 538, `Підсумок` 333), and the summary self-check becomes isolated micro-Q&A instead of the plan’s integrated “order a full meal, ask for the bill, and pay” task. |
| 2. Linguistic accuracy | 9/10 | Ukrainian forms are solid throughout: `Мені каву, будь ласка`, `Можна карткою?`, `Все було дуже смачно!`; VESUM-confirmed vocabulary is used consistently and no Russian-only letters appear. |
| 3. Pedagogical quality | 6/10 | The module introduces extra grammar metalanguage in `без ... genitive` / `з ... instrumental` even though the lesson focus is accusative ordering patterns, and long English commentary like `This is a crucial point for building authentic language skills from the very beginning.` weakens the PPP pacing. |
| 4. Vocabulary coverage | 8/10 | All required plan vocabulary appears in prose (`кафе`, `меню`, `рахунок`, `замовляти`, `офіціант`, `смачно`, `будь ласка`), and most recommended items are also used naturally (`ресторан`, `чайові`, `готівка`, `картка`, `гостре`, `вегетаріанське меню`). |
| 5. Exercise quality | 9/10 | The 4 markers match the 4 `activity_hints`, and each comes after the concept it tests. The additional summary Q&A also checks usable phrases rather than trivia. |
| 6. Engagement & tone | 6/10 | Several lines are filler rather than teaching, e.g. `You now have the essential cafe communication toolkit to comfortably navigate dining out in Ukrainian.` and `This is a crucial point for building authentic language skills from the very beginning.` |
| 7. Structural integrity | 9/10 | All planned H2 sections are present and in the right order, the activity markers are intact, and the pipeline word count is above target at 1818. |
| 8. Cultural accuracy | 9/10 | The core culture points are appropriate and decentered: asking for the bill directly, card/cash language, and polite cafe formulas are presented as Ukrainian norms, not through Russian comparison. |
| 9. Dialogue & conversation quality | 7/10 | The actual dialogue turns are usable, but long English narration like `Imagine a relaxing date...` and `After enjoying a pleasant meal and a long conversation...` takes space away from learner-facing Ukrainian conversation. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `When you want to say "to order" in Ukrainian...` / `Understanding local customs is just as important...`  
Issue: The plan lists `ULP Season 1, Episodes 11-12` and `State Standard 2024, Topic 3 (ресторан)` as references, but neither is cited anywhere in the module.  
Fix: Add one short citation in the ordering section and one short citation in the culture section.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Use this practical self-check checklist...` plus the 5 short Q&A items in `Підсумок — Summary`  
Issue: The plan’s self-check requires one integrated cafe task (`starter, main, drink` + bill + payment), but the module reduces this to isolated phrase recall.  
Fix: Add a single full-scenario self-check prompt with a model answer that combines ordering and paying.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: all four H2 sections  
Issue: Every section overshoots its 300-word plan budget by more than 10%, mainly because of expandable English narration and recap text.  
Fix: Compress the English scene-setting and summary exposition.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `You can easily customize your drinks using the preposition **без** (without) with the genitive case, or **з** (with) with the instrumental case.`  
Issue: This introduces new case terminology outside the lesson’s accusative scope and without dedicated teaching or practice.  
Fix: Present `без цукру` and `з лимоном` as ready-made chunks instead of naming new cases.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `This is a crucial point for building authentic language skills from the very beginning.` / `You now have the essential cafe communication toolkit to comfortably navigate dining out in Ukrainian.`  
Issue: These sentences add bulk but almost no instructional value.  
Fix: Replace them with shorter, direct teaching language.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `Imagine a relaxing date at a cozy, dimly lit Lviv café...` / `After enjoying a pleasant meal and a long conversation...`  
Issue: The section spends too many words on English scene description and too few on Ukrainian turns learners can reuse.  
Fix: Shorten the narration and use the saved space for task-focused dialogue support.

## Verdict: REVISE
Has multiple major findings, and several dimensions are below 9. This is not a rebuild, but it does need targeted tightening and a closer match to the plan before shipping.

<fixes>
- find: |-
    Imagine a relaxing date at a cozy, dimly lit Lviv café. The air smells of freshly roasted beans. Rostyk and Ivanka sit at a comfortable table near the large window. The waiter approaches to take their order. They will look at the menu, discuss the options, and order coffee, traditional borsch, and a fresh pastry.
  replace: |-
    Rostyk and Ivanka are on a date at a cozy Lviv cafe. They look at the menu, ask for a recommendation, and place a simple order.

- find: |-
    After enjoying a pleasant meal and a long conversation, it is time to conclude the date. Rostyk gets the attention of the waiter to ask for the total cost. He will check if he can use his bank card, and Ivanka will make sure to compliment the chef's work before they leave.
  replace: |-
    After the meal, Rostyk asks for the bill, checks whether he can pay by card, and Ivanka compliments the food before they leave.

- find: |-
    When you want to say "to order" in Ukrainian, the standard verbs are **замовляти** (imperfective) and **замовити** (perfective). This is a crucial point for building authentic language skills from the very beginning.
  replace: |-
    When you want to say "to order" in Ukrainian, use **замовляти** (imperfective) and **замовити** (perfective) for food and drinks. This matches the ordering formulas taught in **Ukrainian Lessons, Season 1, Episodes 11-12**.

- find: |-
    Understanding local customs is just as important as knowing the vocabulary.
  replace: |-
    Understanding local customs is just as important as knowing the vocabulary. This ordering-and-paying situation also matches **State Standard 2024, Topic 3 (ресторан)**.

- find: |-
    You can easily customize your drinks using the preposition **без** (without) with the genitive case, or **з** (with) with the instrumental case. If you need a refill, you simply ask for one more.
  replace: |-
    You can customize your drinks with short ready-made phrases. Learn these as whole chunks, and if you need a refill, simply ask for one more.

- find: |-
    You now have the essential cafe communication toolkit to comfortably navigate dining out in Ukrainian.
  replace: |-
    You can now handle a simple cafe visit in Ukrainian from ordering to paying.

- insert_after: |-
    Beyond just ordering, you are prepared to complete the entire dining experience gracefully. You understand the culture of paying the bill and the importance of asking **Рахунок, будь ласка** when you are ready to pay. You can confirm your payment method by asking **Можна карткою?** instead of relying entirely on cash. Most importantly, you know how to leave a warm, culturally appropriate compliment by telling the staff **Дуже смачно!** to show your appreciation for their hard work.
  replace: |-
    Beyond just ordering, you are prepared to complete the entire dining experience gracefully. You understand the culture of paying the bill and the importance of asking **Рахунок, будь ласка** when you are ready to pay. You can confirm your payment method by asking **Можна карткою?** instead of relying entirely on cash. Most importantly, you know how to leave a warm, culturally appropriate compliment by telling the staff **Дуже смачно!** to show your appreciation for their hard work.

    Self-check: Can you do the whole cafe task in one short response? Model: **Можна меню, будь ласка? Мені салат, борщ і чай, будь ласка. Рахунок, будь ласка. Можна карткою?**

- find: |-
    Use this practical self-check checklist to verify your readiness before you visit a real Ukrainian coffee shop. Read each question carefully and try to formulate the answer in your head before looking at the solution. Practice these functional phrases aloud multiple times until they feel completely natural and effortless to you.
  replace: |-
    Use this quick self-check before you visit a Ukrainian cafe. Answer each question aloud before you look at the model answer.
</fixes>