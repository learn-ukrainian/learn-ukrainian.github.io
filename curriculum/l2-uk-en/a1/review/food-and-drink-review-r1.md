## Linguistic Scan
No linguistic errors found.

## Exercise Check
- `fill-in-z-chunks` (matches `fill-in` hint): Tests vocabulary (`вода`, `м'ясо`, `картопля`) before it is introduced in the text. Must be moved.
- `quiz-meals-dishes` (matches `quiz` hint): Tests time words (`вдень`) before they are explained in the summary. Must be moved.
- `match-food-drink` (matches `match-up` hint): Placed correctly.
- `group-sort-food-drinks` (matches `group-sort` hint): Placed correctly.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The plan explicitly lists "галушки" as an iconic cultural food to include, but it is missing from the prose. |
| 2. Linguistic accuracy | 10/10 | No linguistic errors found. Gender assignments (каша, f; м'ясо, n; борщ, m) are accurate, and natural vocabulary ("зазвичай", "щоранку") is used. |
| 3. Pedagogical quality | 7/10 | Exercises test concepts before they are taught. `fill-in-z-chunks` tests "вода" and "м'ясо" right after the first dialogue, before the Food/Drinks sections introduce them. `quiz-meals-dishes` asks about "вдень" before it is explained in the Summary. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is present naturally. From the recommended list, "піца" is missing. |
| 5. Exercise quality | 9/10 | Exercises match the plan's focus well, but suffer from the pedagogical placement issues noted above. |
| 6. Engagement & tone | 8/10 | Some meta-commentary is present ("A learner who knows борщ... is not just vocabulary-trained — they carry a signal of respect"). This tells rather than shows. |
| 7. Structural integrity | 9/10 | A stray HTML comment `<!-- A2-word -->` was left in the prose after "компот". |
| 8. Cultural accuracy | 10/10 | Excellent integration of UNESCO's recognition of Ukrainian borshch and natural cultural context for salo and varanyky. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are natural, multi-turn, and effectively use the target chunks ("Кашу з молоком чи без? З молоком, звичайно!"). |

## Findings
[Plan adherence] [Major]
Location: `### Ukrainian iconic dishes`
Issue: The plan explicitly lists `галушки` as a cultural note / iconic food, but it is missing from the text.
Fix: Add `галушки` to the list of iconic dishes and the summary.

[Pedagogical quality] [Major]
Location: `<!-- INJECT_ACTIVITY: fill-in-z-chunks -->`
Issue: The `fill-in-z-chunks` activity is injected before the vocabulary words it tests (`вода`, `м'ясо`, `картопля`) are introduced in the subsequent `Їжа` and `Напої` sections.
Fix: Move the `fill-in-z-chunks` marker to the end of the `Напої` section, after the chunk list is fully explained.

[Pedagogical quality] [Major]
Location: `<!-- INJECT_ACTIVITY: quiz-meals-dishes -->`
Issue: The quiz asks "Що ми їмо вдень?" but the association of "вдень" with "обід" is only explicitly taught later in the `Підсумок — Summary` section.
Fix: Move the `quiz-meals-dishes` marker to the `Підсумок` section, after the three meals table and time words are explained.

[Vocabulary coverage] [Minor]
Location: `> **Марко:** Зазвичай суп або омлет. *(Usually soup or an omelette.)*`
Issue: The recommended vocabulary word `піца` is missing from the module.
Fix: Add `піца` to Marko's dialogue about dinner.

[Structural integrity] [Minor]
Location: `**компот** (compote, m) <!-- A2-word -->, **лимонад**`
Issue: A stray HTML comment tag `<!-- A2-word -->` was left in the prose.
Fix: Remove the comment tag.

[Engagement & tone] [Minor]
Location: `A learner who knows **борщ**, **вареники**, **сало**, **деруни** is not just vocabulary-trained — they carry a signal of respect.`
Issue: The phrase "is not just vocabulary-trained" is meta-commentary and gamified language.
Fix: Rewrite to sound more natural ("Knowing [dishes] shows respect for Ukrainian culture.").

## Verdict: REVISE
The module requires revision due to major pedagogical issues with exercise placement (testing concepts before they are introduced) and the omission of a required cultural vocabulary word (галушки).

<fixes>
- find: ":::\n\n<!-- INJECT_ACTIVITY: fill-in-z-chunks -->\n\n## Їжа (Food)"
  replace: ":::\n\n## Їжа (Food)"
- find: "- **риба з рисом** — fish with rice\n\n### Reading Practice"
  replace: "- **риба з рисом** — fish with rice\n\n<!-- INJECT_ACTIVITY: fill-in-z-chunks -->\n\n### Reading Practice"
- find: "*(Yes! And carrot, onion, sour cream.)*\n\n<!-- INJECT_ACTIVITY: quiz-meals-dishes -->\n\n## Напої (Drinks)"
  replace: "*(Yes! And carrot, onion, sour cream.)*\n\n## Напої (Drinks)"
- find: "mean **сніданок**.\n\n:::tip Your Cultural Passport"
  replace: "mean **сніданок**.\n\n<!-- INJECT_ACTIVITY: quiz-meals-dishes -->\n\n:::tip Your Cultural Passport"
- find: "> **Марко:** Зазвичай суп або омлет. *(Usually soup or an omelette.)*"
  replace: "> **Марко:** Зазвичай суп, омлет або піца. *(Usually soup, an omelette or pizza.)*"
- find: "**компот** (compote, m) <!-- A2-word -->, **лимонад**"
  replace: "**компот** (compote, m), **лимонад**"
- find: "These four dishes are not just vocabulary — they are cultural identity."
  replace: "These five dishes are not just vocabulary — they are cultural identity."
- find: "**Деруни** (pl) — potato pancakes made from grated **картопля**, often served with **сметана**."
  replace: "**Деруни** (pl) — potato pancakes made from grated **картопля**, often served with **сметана**.\n\n**Галушки** (pl) — soft dough dumplings boiled in water or broth, a staple of central Ukrainian cuisine."
- find: "A learner who knows **борщ**, **вареники**, **сало**, **деруни** is not just vocabulary-trained — they carry a signal of respect."
  replace: "Knowing **борщ**, **вареники**, **сало**, **галушки**, and **деруни** shows respect for Ukrainian culture."
- find: "**Деруни** = картопля + сметана."
  replace: "**Деруни** = картопля + сметана. **Галушки** = тісто + вода."
</fixes>
