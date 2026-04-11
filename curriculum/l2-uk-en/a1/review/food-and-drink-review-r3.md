## Linguistic Scan
No linguistic errors found.

## Exercise Check
- The `<!-- INJECT_ACTIVITY: match-up-food-vocab -->` marker is placed right before the "Напої (Drinks)" section. This is incorrect because the activity tests `вода` and `сік`, which are not introduced until the "Напої" section itself.
- The `<!-- INJECT_ACTIVITY: group-sort-food-drinks -->`, `<!-- INJECT_ACTIVITY: fill-in-chunks -->`, and `<!-- INJECT_ACTIVITY: quiz-meals-dishes -->` markers are all clustered consecutively at the end of the "Напої" section, which violates the rule to spread markers out across the module and not cluster them.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The text misses the required `references` from the plan ("ULP Season 1, Episodes 11-13" and "State Standard 2024, Topic 3 (ресторан)"). All other plan points, including vocabulary, outline, and objectives, are meticulously covered. |
| 2. Linguistic accuracy | 10/10 | Excellent. The generated text is free from Russianisms, Surzhyk, or calques. Accurate and natural phrasing is used throughout. No linguistic errors found. |
| 3. Pedagogical quality | 10/10 | Strong PPP flow. The grammar rule (`з + noun`) is taught practically as a chunk without overwhelming the learner with instrumental case theory. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words are included and introduced in context rather than as bare lists. |
| 5. Exercise quality | 7/10 | The `match-up-food-vocab` marker tests vocabulary before it is formally introduced. Furthermore, three markers are heavily clustered at the end of the "Напої" section. |
| 6. Engagement & tone | 10/10 | Warm, inviting tone. The teacher persona effectively uses the culinary context to engage the learner naturally. |
| 7. Structural integrity | 10/10 | All H2 headings are present. Word count (1520) exceeds the 1200 target. |
| 8. Cultural accuracy | 10/10 | Accurate and respectful cultural details. Mentions `борщ` as UNESCO heritage, highlights the sacred role of `хліб`, and correctly includes `сало`, `вареники`, `компот`, and `узвар`. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are realistic, culturally natural, and effectively use the target phrases in multi-turn exchanges. |

## Findings
[1. Plan adherence] [major]
Location: Entire module text.
Issue: The plan lists references (`ULP Season 1, Episodes 11-13`, `State Standard 2024, Topic 3 (ресторан)`) which are completely omitted from the text.
Fix: Add a "Ресурси (Resources)" callout at the end of the Summary to point the learner to the required external materials.

[5. Exercise quality] [major]
Location: `<!-- INJECT_ACTIVITY: match-up-food-vocab -->` (placed right before `## Напо́ї (Drinks)`) and the cluster of three markers at the end of the `Напої` section.
Issue: The match-up activity tests concepts (`вода`, `сік`) before they are taught. Markers are clustered together instead of being distributed naturally (e.g., placing comprehensive review activities in the Summary).
Fix: Relocate `match-up-food-vocab`, `group-sort-food-drinks`, and `quiz-meals-dishes` to the `Підсумок — Summary` section. Keep `fill-in-chunks` at the end of the `Напої` section where the `з + noun` chunking is taught.

## Verdict: REVISE
The text is linguistically solid and pedagogically excellent, but the missing references and the misplacement/clustering of the activity markers require a revision.

<fixes>
- find: "**салат** (salad).\n\n<!-- INJECT_ACTIVITY: match-up-food-vocab -->\n\n## Напо́ї (Drinks)"
  replace: "**салат** (salad).\n\n## Напо́ї (Drinks)"
- find: "* **м'ясо з картоплею** — meat with potatoes\n\n<!-- INJECT_ACTIVITY: group-sort-food-drinks -->\n<!-- INJECT_ACTIVITY: fill-in-chunks -->\n<!-- INJECT_ACTIVITY: quiz-meals-dishes -->\n\n## Підсумок — Summary"
  replace: "* **м'ясо з картоплею** — meat with potatoes\n\n<!-- INJECT_ACTIVITY: fill-in-chunks -->\n\n## Підсумок — Summary"
- find: "sparkling water.)*\n\nBefore moving forward, verify that you can confidently answer the following questions:"
  replace: "sparkling water.)*\n\n<!-- INJECT_ACTIVITY: match-up-food-vocab -->\n<!-- INJECT_ACTIVITY: group-sort-food-drinks -->\n<!-- INJECT_ACTIVITY: quiz-meals-dishes -->\n\nBefore moving forward, verify that you can confidently answer the following questions:"
- find: "Name one traditional Ukrainian cold drink (**компот** or **узвар**).\n\nIf you can answer these questions and name your favorite foods, you are ready to practice."
  replace: "Name one traditional Ukrainian cold drink (**компот** or **узвар**).\n\nIf you can answer these questions and name your favorite foods, you are ready to practice.\n\n:::note Ресурси (Resources)\nTo hear this vocabulary in action, listen to **Ukrainian Lessons Podcast (ULP), Season 1, Episodes 11-13**, where Anna introduces food and drink vocabulary and cafe ordering. This module's vocabulary also aligns with the communicative situations (restaurant, ordering food) outlined in the **Ukrainian State Standard 2024, Topic 3**.\n:::"
</fixes>