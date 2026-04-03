## Linguistic Scan
No linguistic errors found.

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-order -->`: Matches the plan. However, in the plan's `activity_hints`, every correct answer is at index 0 in the `{correct|wrong|wrong}` syntax.
- `<!-- INJECT_ACTIVITY: quiz-cafe-phrases -->`: Matches the plan. But the marker is placed BEFORE the section `Культура кафе`, despite testing phrases like "Тут вільно?" and "Все було дуже смачно!", which are only formally introduced in `Культура кафе`. Furthermore, all correct options in the plan's YAML structure are at index 0.
- `<!-- INJECT_ACTIVITY: fill-in-dialogue -->`: Matches the plan. All correct options in the plan are at index 0.
- `<!-- INJECT_ACTIVITY: match-cafe-phrases -->`: Matches the plan correctly.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Missed the "Я хочу" pattern from the plan. It only included "Я буду" in Pattern 4 ("**Pattern 4: Я бу́ду [accusative].**"). |
| 2. Linguistic accuracy | 10/10 | Excellent. All accusative endings and vocabulary usage are natural and correct. |
| 3. Pedagogical quality | 8/10 | The quiz `quiz-cafe-phrases` is placed at the end of `Як замовити`, but it tests the phrase "Тут вільно?", which is not taught until the next section (`Культура кафе`). |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary are integrated naturally into the prose. |
| 5. Exercise quality | 4/10 | The plan's `activity_hints` places the correct answer at index 0 for every single item in `fill-in-order`, `quiz-cafe-phrases`, and `fill-in-dialogue`. This makes the exercises trivially easy and flawed by design. |
| 6. Engagement & tone | 9/10 | Highly engaging context, especially the cultural explanation of the post-2022 cafe scene ("Ми варимо каву..."). Slight meta-commentary ("screenshot this"). |
| 7. Structural integrity | 10/10 | Perfect layout, exactly matches the required structure and word count (1210 words). |
| 8. Cultural accuracy | 10/10 | Excellent distinctions between кафе, ресторан, and кав'ярня. Authentic representation of Ukrainian cafe culture. |
| 9. Dialogue & conversation quality | 10/10 | Natural and authentic multi-turn dialogues with a mix of formal and casual interactions. |

## Findings

[1. Plan adherence] [major]
Location: `## Як замо́вити (How to Order)` section, "**Pattern 4: Я бу́ду [accusative].**"
Issue: The plan explicitly required teaching both "Я хочу / Я буду [accusative]", but the text omitted "Я хочу".
Fix: Add "Я хочу" to the pattern and its examples.

[3. Pedagogical quality] [major]
Location: `<!-- INJECT_ACTIVITY: quiz-cafe-phrases -->` marker placement at the end of `## Як замо́вити (How to Order)`.
Issue: The quiz tests the phrase "Тут вільно?", but this phrase is only formally introduced in the following `Культура кафе` section.
Fix: Move the `quiz-cafe-phrases` marker to the end of the `Культура кафе` section.

[5. Exercise quality] [critical]
Location: Plan's `activity_hints` block (all exercises).
Issue: All correct answers for the generated exercises (`fill-in-order`, `quiz-cafe-phrases`, `fill-in-dialogue`) are placed at index 0 in the options array.
Fix: The writer must shuffle the correct answers in the plan's YAML structure. (No fix provided below as `<fixes>` only apply to the `.md` content).

## Verdict: REVISE
The module is beautifully written and culturally accurate, but it requires structural fixes. The `Я хочу` pattern was omitted from the grammar section, and an exercise marker is placed pedagogically too early, testing a concept before it's formally taught. Additionally, the plan contains a critical exercise logic flaw (all correct answers at index 0) that must be addressed before the final YAML activities are generated.

<fixes>
- find: "**Pattern 4: Я бу́ду [accusative].**"
  replace: "**Pattern 4: Я хо́чу / Я бу́ду [accusative].**"
- find: "- **Я буду пі́цу.** — I'll have pizza.\n- **Я буду суп.** — I'll have soup."
  replace: "- **Я хо́чу пі́цу.** — I want pizza.\n- **Я буду суп.** — I'll have soup."
- find: "The numbers connect back to what you learned in earlier modules.\n\n<!-- INJECT_ACTIVITY: quiz-cafe-phrases -->\n\n## Культу́ра кафе (Cafe Culture)"
  replace: "The numbers connect back to what you learned in earlier modules.\n\n## Культу́ра кафе (Cafe Culture)"
- find: "<!-- INJECT_ACTIVITY: match-cafe-phrases -->\n\n## Підсумок — Summary"
  replace: "<!-- INJECT_ACTIVITY: match-cafe-phrases -->\n\n<!-- INJECT_ACTIVITY: quiz-cafe-phrases -->\n\n## Підсумок — Summary"
</fixes>
