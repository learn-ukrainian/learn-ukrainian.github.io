## Linguistic Scan
No linguistic errors found in the Ukrainian text.

## Exercise Check
All four `<!-- INJECT_ACTIVITY: {id} -->` markers are present, logically placed after the relevant grammar instruction, and perfectly match the four `activity_hints` described in the plan (Vocative/Imperative, Conjunctions, Complex Sentences, Holiday Greetings).

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | The text follows the `content_outline` structure exactly, including sections for "Що ми знаємо?", "Читання", "Граматика", "Діалог", and "Підсумок". All specific plan points are systematically covered. |
| 2. Linguistic accuracy | 10/10 | The Ukrainian examples are natural, correctly inflected, and free of Russianisms or calques. Sentence structures with conjunctions are built properly. |
| 3. Pedagogical quality | 8/10 | The grammar rule stating "Masculine names ending in a hard consonant add **-е**: **Петро** becomes **Петре**" is factually incorrect because "Петро" ends in the vowel "-о". Also, using "**друг** (friend) becomes **друже**" as an example of simply adding "-е" without explaining the г → ж consonant mutation is misleading for beginners. |
| 4. Vocabulary coverage | 10/10 | The required nouns (плакат, квиток, напій, стілець) and verbs are effectively contextualized in the reading and dialogue sections. |
| 5. Exercise quality | 10/10 | The markers match the plan's `activity_hints` exactly and are inserted at the correct pedagogical moments immediately after each concept is explained. |
| 6. Engagement & tone | 7/10 | DEDUCT for self-congratulatory openers ("Welcome to the A1.7 Checkpoint.") and gamified/corporate filler ("Communication Hub", "Your mission in this module is practical", "major milestone in your Ukrainian journey"). |
| 7. Structural integrity | 9/10 | DEDUCT for a dangling sentence fragment at the start of the summary: "7 Communication phase." |
| 8. Cultural accuracy | 10/10 | Correctly explains the cultural/grammatical formula for Ukrainian holiday greetings using "З" + Instrumental. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue between Taras and Olena feels like a natural, purpose-driven conversation, integrating all grammar points seamlessly. |

## Findings
[Pedagogical quality] [critical]
Location: Граматика (Grammar Summary), paragraph 1: "Masculine names ending in a hard consonant add **-е**: **Петро** becomes **Петре**, **Тарас** becomes **Тарасе**, and **друг** (friend) becomes **друже**."
Issue: The rule is factually incorrect. "Петро" ends in the vowel "-о", not a hard consonant. Additionally, using "друг" as an example of simply adding "-е" without noting the consonant mutation (г → ж) is misleading.
Fix: Update the rule to accurately include nouns ending in "-о" and note the consonant change for "друг".

[Engagement & tone] [minor]
Location: Що ми знаємо? (What Do We Know?), paragraph 1: "Welcome to the A1.7 Checkpoint. This module serves as your "Communication Hub", where we integrate all the social skills you have acquired in the previous five lessons. [...] Your mission in this module is practical:"
Issue: Uses self-congratulatory openers and gamified/corporate language ("Communication Hub", "Your mission in this module is practical"), which violates the tone guidelines.
Fix: Remove the gamified filler and state the module's purpose directly.

[Structural integrity] [minor]
Location: Підсумок — Summary, paragraph 1: "7 Communication phase. This is a major milestone in your Ukrainian journey. Review your new capabilities:"
Issue: "7 Communication phase." is a dangling sentence fragment (likely a typo for "A1.7"). The paragraph also uses gamified language ("major milestone in your Ukrainian journey").
Fix: Combine and rephrase into a complete, non-gamified sentence.

## Verdict: REVISE
The module contains a critical pedagogical error regarding the vocative rule for masculine nouns ending in "-о", as well as some minor formatting and tone issues. These need to be addressed via the `<fixes>` block before publishing.

<fixes>
- find: "Masculine names ending in a hard consonant add **-е**: **Петро** becomes **Петре**, **Тарас** becomes **Тарасе**, and **друг** (friend) becomes **друже**."
  replace: "Masculine names ending in a hard consonant or **-о** take **-е**: **Тарас** becomes **Тарасе**, **Петро** becomes **Петре**, and **друг** (friend) becomes **друже** (notice the consonant change)."
- find: "Welcome to the A1.7 Checkpoint. This module serves as your \"Communication Hub\", where we integrate all the social skills you have acquired in the previous five lessons. Language is a tool for connection, and in a real-world scenario, you do not just recite vocabulary; you use it to achieve a specific goal. Your mission in this module is practical: you are helping your friends organize a lively school event."
  replace: "This Checkpoint integrates the communication skills you have acquired in the previous five lessons. Language is a tool for connection, and in a real-world scenario, you do not just recite vocabulary; you use it to achieve a specific goal. In this module, you are helping your friends organize a lively school event."
- find: "7 Communication phase. This is a major milestone in your Ukrainian journey. Review your new capabilities:"
  replace: "You have reached the end of the A1.7 Communication phase. Review your capabilities:"
</fixes>
