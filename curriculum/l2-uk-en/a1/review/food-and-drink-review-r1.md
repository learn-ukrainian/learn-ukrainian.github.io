## Linguistic Scan
Found 1 linguistic error: The phrase "по-українськи" is used 4 times in the self-check. This is a calque/colloquialism heavily influenced by the Russian pattern ("по-русски"). The correct standard Ukrainian form is "українською". The prompt's VESUM check also confirmed that "українськи" is not an attested form. 

No other Russianisms or Surzhyk were found. The writer correctly used the standard form "їси" instead of the colloquial "їш" from the plan.

## Exercise Check
- **Duplicate & Premature Marker**: `<!-- INJECT_ACTIVITY: quiz-meals-dishes -->` is injected twice. Its first appearance is at the end of the `Їжа` section. This is a critical pedagogical error because the quiz tests the word "компот", which is not taught until the following `Напої` section. The second instance at the end of `Напої` is correctly placed.
- **Clustering**: Because of the duplicate marker, there are 4 activity markers (`fill-in-z-chunks`, `match-food-drink`, `group-sort-food-drinks`, `quiz-meals-dishes`) clustered sequentially at the very end of the `Напої` section. While they pedagogically belong there (since they test both food and drink), the clustering is visually heavy.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The module missed the specific prompt for the self-check: "Name 5 foods and 3 drinks you like. Name one Ukrainian dish and why it matters." Instead, it used generic recall prompts ("Назви 5 овочів", "Який традиційний український суп?"). The deterministic word count is 1357, which is >10% over the 1200 word target. |
| 2. Linguistic accuracy | 8/10 | DEDUCT for using the calque "по-українськи" 4 times in the self-check instead of standard "українською". REWARD for correcting the plan's "їш" to the grammatically proper "їси". |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. Explicitly teaching `з + noun` as a chunk and deferring the instrumental case grammar to A2 is exactly the right pedagogical approach for A1 learners. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items were seamlessly integrated into the natural flow of the prose without resorting to bare lists. |
| 5. Exercise quality | 6/10 | DEDUCT for injecting `quiz-meals-dishes` prematurely (testing "компот" before it is introduced) and duplicating the marker. DEDUCT for clustering 4 markers at the end. |
| 6. Engagement & tone | 8/10 | DEDUCT for meta-commentary / corporate-speak: "You now have a toolkit for talking about food and drink in Ukrainian." This violates the "telling instead of showing" rule. |
| 7. Structural integrity | 7/10 | DEDUCT for the duplicate exercise marker artifact and for exceeding the +10% word count tolerance limit (1357 vs 1200 target). |
| 8. Cultural accuracy | 10/10 | Exceptionally strong, decolonized representation of borshch, salo, and varenyky, correctly referencing the UNESCO heritage list. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are highly natural, contextual, and feature named speakers with distinct voices (e.g., "Каша на плиті"). |

## Findings

[1. Plan adherence] [Major]
Location: `Підсумок — Summary` (Self-check section)
Issue: The self-check asks "Назви 5 овочів" and "Який традиційний український суп?", ignoring the plan's strict instruction to prompt for what the learner *likes* ("Name 5 foods and 3 drinks you like") and *why* a dish matters ("Name one Ukrainian dish and why it matters").
Fix: Update the self-check items to match the plan's specific pedagogical prompts.

[2. Linguistic accuracy] [Critical]
Location: `Підсумок — Summary` (Self-check section: "- Як по-українськи...")
Issue: "по-українськи" is a calque from Russian ("по-русски"). The standard, correct form is "українською". The VESUM check confirmed "українськи" is not an attested form. 
Fix: Replace all 4 instances of "Як по-українськи" with "Як українською".

[5. Exercise quality] [Critical]
Location: `Їжа` section, just before `Напої`
Issue: `<!-- INJECT_ACTIVITY: quiz-meals-dishes -->` is injected prematurely in the `Їжа` section (before "компот" is taught) and is a duplicate of the same marker at the end of the `Напої` section.
Fix: Delete the duplicate marker at the end of the `Їжа` section.

[6. Engagement & tone] [Minor]
Location: `Підсумок — Summary` (First paragraph)
Issue: "You now have a toolkit for talking about food and drink in Ukrainian." is "telling instead of showing" and falls under the penalized "You now possess..." phrasing pattern.
Fix: Remove the sentence and start directly with "Here are the key patterns in action:".

## Verdict: REVISE
The module contains a critical linguistic calque ("по-українськи"), a duplicated/prematurely placed exercise marker, and misses a specific pedagogical directive in the self-check. These must be addressed before the module can be published. 

<fixes>
- find: "- Як по-українськи \"breakfast\"? → **сніданок**"
  replace: "- Як українською \"breakfast\"? → **сніданок**"
- find: "- Як по-українськи \"lunch\"? → **обід**"
  replace: "- Як українською \"lunch\"? → **обід**"
- find: "- Як по-українськи \"dinner\"? → **вечеря**"
  replace: "- Як українською \"dinner\"? → **вечеря**"
- find: "- Як по-українськи \"drink\" (noun)? → **напій**"
  replace: "- Як українською \"drink\" (noun)? → **напій**"
- find: ":::\n\n<!-- INJECT_ACTIVITY: quiz-meals-dishes -->\n\n## Напої"
  replace: ":::\n\n## Напої"
- find: "- Назви 5 овочів. → **картопля, морква, цибуля, помідор, огірок**\n- Назви 3 напої. → **кава, чай, вода** (або **сік**, **компот**, **кефір**)\n- Який традиційний український суп? → **борщ**"
  replace: "- Назви 5 страв або продуктів, які ти любиш. → (наприклад: **борщ, картопля, хліб, яблуко, сир**)\n- Назви 3 напої, які ти любиш. → (наприклад: **кава, вода, сік**)\n- Назви одну українську страву. Чому вона важлива? → наприклад, **борщ** (національна спадщина ЮНЕСКО)"
- find: "You now have a toolkit for talking about food and drink in Ukrainian. Here are the key patterns in action:"
  replace: "Here are the key patterns in action:"
</fixes>
