## Linguistic Scan
No critical linguistic errors found. The module uses completely natural Ukrainian, handles cases and prepositions beautifully, and avoids Russianisms (e.g., "аптека відчинена", "здати проєкт", "ставлення до"). One minor stylistic polish item found ("йти пішки" vs "дійти пішки").

## Exercise Check
- Marker 1 (`fill-in`): Placed after Section 2. Matches plan.
- Marker 2 (`match-up`): Placed at the end. Matches plan.
- Marker 3 (`quiz`): Placed at the end. Matches plan.
- Marker 4 (`group-sort`): Placed at the end. Matches plan.
Issue: Three out of four markers are clustered at the very end of the module. However, because these activities test all three meanings of *до* (direction, time, purpose) as dictated by the plan, their placement at the end is pedagogically necessary.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 4/10 | The word count is 3440, massively exceeding the 2000-word target by 72%. Required references (Заболотний, ULP) are missing from the text. |
| 2. Linguistic accuracy | 9/10 | Excellent overall accuracy. Minor stylistic issue with "швидко йти пішки" instead of the more natural "швидко дійти пішки". |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. Clear explanations with abundant, natural examples. Rules are well-contextualized. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items from the plan are integrated naturally into the text. |
| 5. Exercise quality | 8/10 | Activities match the plan, but three out of four are clustered at the very end of the module (though constrained by the plan's integrative focus). |
| 6. Engagement & tone | 7/10 | Contains meta-commentary ("Let's look closer at", "Let's summarize") and generic fluff ("В українській мові ми часто говоримо про час..."). |
| 7. Structural integrity | 3/10 | Failed word count validation. The text is 3440 words against a strict 2000-word target. |
| 8. Cultural accuracy | 10/10 | No cultural inaccuracies. Culturally appropriate examples used throughout. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are natural and correctly formatted. |

## Findings

[Plan adherence] [critical]
Location: `**Deterministic word count: 3440 words**`
Issue: The module word count (3440 words) is 72% over the target word budget of 2000 words. This is a fundamental structural failure that violates the plan's parameters.
Fix: Requires a complete rewrite to condense the content.

[Plan adherence] [major]
Location: End of module
Issue: Required textbook references (Заболотний Grade 5, §31; ULP: 10 Uses of Genitive Case) are missing.
Fix: Add a "Джерела (References)" section at the end of the text.

[Engagement & tone] [minor]
Location: `В українській мові ми часто говоримо про час та його межі. *(In the Ukrainian language, we often talk about time and its limits.)* `
Issue: Generic fluff sentence that adds no pedagogical value.
Fix: Remove the sentence.

[Engagement & tone] [minor]
Location: `Let's look closer at the Genitive endings you need for these directional phrases. The ending depends on the gender of the noun and whether its stem is hard or soft.`
Issue: Meta-commentary. The text should teach directly without announcing its pedagogical moves.
Fix: Remove the meta-commentary portion.

[Engagement & tone] [minor]
Location: `You now have a complete picture of how versatile the preposition **до** is when paired with the Genitive case. It is one of the most frequent words in the Ukrainian language. Let's summarize its main functions so you can confidently use it in any situation.`
Issue: Meta-commentary and generic enthusiasm.
Fix: Replace with a direct transition.

[Linguistic accuracy] [minor]
Location: `Від вокзалу до нашого готелю можна швидко йти пішки.`
Issue: "Йти пішки" describes the process of walking, while "дійти пішки" describes reaching a destination, which is much more idiomatic in this context.
Fix: Change "йти" to "дійти".

## Verdict: REJECT
The module's word count (3440 words) is 72% over the 2000-word target. This is a fundamental structural failure that cannot be fixed with simple string replacements. While the linguistic quality is excellent, the module requires a full rewrite to condense the material and respect the planned word budgets.

<fixes>
- find: "<!-- INJECT_ACTIVITY: group-sort, Sort 8 phrases into categories: Direction vs. Time vs. Abstract/Purpose -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort, Sort 8 phrases into categories: Direction vs. Time vs. Abstract/Purpose -->\n\n## Джерела (References)\n- Заболотний Grade 5, §31: Прийменник до з родовим відмінком\n- [ULP: 10 Uses of Genitive Case](https://www.ukrainianlessons.com/genitive-case/)"
- find: "В українській мові ми часто говоримо про час та його межі. *(In the Ukrainian language, we often talk about time and its limits.)* "
  replace: ""
- find: "Let's look closer at the Genitive endings you need for these directional phrases. The ending depends on the gender of the noun and whether its stem is hard or soft."
  replace: "The Genitive ending depends on the gender of the noun and whether its stem is hard or soft."
- find: "You now have a complete picture of how versatile the preposition **до** is when paired with the Genitive case. It is one of the most frequent words in the Ukrainian language. Let's summarize its main functions so you can confidently use it in any situation."
  replace: "Here is a summary of the main functions of **до** + Genitive case:"
- find: "Від вокзалу до нашого готелю можна швидко йти пішки."
  replace: "Від вокзалу до нашого готелю можна швидко дійти пішки."
</fixes>
