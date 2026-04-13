## Linguistic Scan
- **Grammar-rule error:** In the counting section, the claim `"To speak correctly, you must always look at the last number in the sequence. It is this final digit that strictly determines the grammatical ending of the following noun."` is inaccurate. Ukrainian counting also requires checking whether the number ends in `11–14`, which overrides the last-digit pattern.

## Exercise Check
- All 4 planned markers are present:
  - `quiz-what-s-the-date-drill`
  - `fill-in-counting-objects-1-2-4-5-rule`
  - `match-up-accusative-genitive-negation`
  - `match-up-qa-quantities-dates`
- Marker types broadly match the plan’s `activity_hints`.
- Placement issue: `match-up-qa-quantities-dates` is clustered at the very end, after the negation section, even though it tests dates/quantities and should come right after the dates/counting teaching.
- No inline exercise-logic errors were visible because only markers, not generated YAML items, are present here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present and the required vocabulary is substantially covered, but the recommended plan vocabulary `числівник` and `додаток` does not appear in the prose, and the `match-up-qa-quantities-dates` marker is misplaced at the end. |
| 2. Linguistic accuracy | 7/10 | The Ukrainian forms are mostly solid, but the counting explanation says learners should “always look at the last number,” which is a wrong grammar rule because `11–14` override the last-digit pattern. |
| 3. Pedagogical quality | 7/10 | The module gives many examples, but the counting rule is overgeneralized before the exception logic is stated, and the quantities/dates practice is not placed immediately after the relevant teaching. |
| 4. Vocabulary coverage | 8/10 | Required items such as `число`, `місяць`, all 12 months, and `заперечення` are present, but recommended `числівник` and `додаток` are absent from the prose. |
| 5. Exercise quality | 8/10 | The marker inventory matches the plan, but `match-up-qa-quantities-dates` appears after the negation material instead of after the dates/counting material it is meant to reinforce. |
| 6. Engagement & tone | 8/10 | The teacher voice is mostly solid, but the counting dialogue derails into an unrelated historical sentence: `Оборона старого українського аеропорту...`, which feels pasted in rather than taught. |
| 7. Structural integrity | 10/10 | All major sections are present and ordered correctly, markers are intact, and the pipeline word count is `2979`, which is above target. |
| 8. Cultural accuracy | 10/10 | The module is Ukrainian-centered and uses appropriate cultural references such as Independence Day and Ukrainian month-name etymology. |
| 9. Dialogue & conversation quality | 7/10 | The hotel dialogue works, but the later “dialogue” is not a real exchange: one speaker abruptly states `Оборона старого українського аеропорту...` with no conversational setup. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Counting section — `"To speak correctly, you must always look at the last number in the sequence. It is this final digit that strictly determines the grammatical ending of the following noun."`  
Issue: This teaches a wrong rule. In Ukrainian, learners must also check whether the number ends in `11–14`; those endings override the last-digit pattern.  
Fix: Replace the rule with wording that explicitly says to check both the final digit and whether the number ends in `11–14`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Date explanation and negation explanation; search evidence: `числівник` = 0 occurrences, `додаток` = 0 occurrences.  
Issue: Two recommended grammar terms from the plan are missing from the prose.  
Fix: Introduce `числівник` in the date explanation and `додаток` in the negation explanation.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: End of module — `<!-- INJECT_ACTIVITY: match-up-qa-quantities-dates -->`  
Issue: The quantities/dates match-up is placed after the negation section, so it is not testing what was just taught.  
Fix: Move this marker to immediately after the counting section marker.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: Counting dialogue — `> — **Олена:** Оборона старого українського аеропорту безперервно тривала двісті сорок два дні.`  
Issue: This line is disconnected from the surrounding classroom-style quantity dialogue and makes the exchange sound stitched together rather than natural.  
Fix: Replace it with a quantity question that the next line directly answers.

## Verdict: REVISE
The module is not a reject, but it cannot pass as-is. It contains one critical grammar-rule error, plus major issues with plan vocabulary coverage, exercise placement, and dialogue coherence. Several dimensions are below 9 with concrete fixable problems.

<fixes>
- find: "To speak correctly, you must always look at the last number in the sequence. It is this final digit that strictly determines the grammatical ending of the following noun."
  replace: "To speak correctly, you usually look at the final digit, but you must also check whether the number ends in 11-14. These teen endings override the usual pattern and determine the grammatical form of the following noun."

- find: "First, the day is expressed as an ordinal numeral in the neuter gender, such as the Ukrainian words for first, second, or third."
  replace: "First, the day is expressed as an ordinal **числівник** in the neuter gender, such as the Ukrainian words for first, second, or third."

- find: "When you negate a transitive verb — a verb that normally takes a direct object in the Accusative case — the object often shifts into the Genitive case."
  replace: "When you negate a transitive verb — a verb that normally takes a direct **додаток** (object) in the Accusative case — the object often shifts into the Genitive case."

- insert_after: "<!-- INJECT_ACTIVITY: fill-in-counting-objects-1-2-4-5-rule -->"
  content: "<!-- INJECT_ACTIVITY: match-up-qa-quantities-dates -->"

- find: |
    <!-- INJECT_ACTIVITY: match-up-accusative-genitive-negation -->
    <!-- INJECT_ACTIVITY: match-up-qa-quantities-dates -->
  replace: "<!-- INJECT_ACTIVITY: match-up-accusative-genitive-negation -->"

- find: |
    > — **Олена:** Оборона старого українського аеропорту безперервно тривала двісті сорок два дні. *(The defense of the old Ukrainian airport lasted continuously for two hundred and forty-two days.)*
    > — **Марко:** Ми швидко купили чотири квитки на поїзд. *(We quickly bought four train tickets.)*
  replace: |
    > — **Олена:** А скільки квитків ви купили на поїзд? *(And how many train tickets did you buy?)*
    > — **Марко:** Ми швидко купили чотири квитки на поїзд. *(We quickly bought four train tickets.)*
</fixes>