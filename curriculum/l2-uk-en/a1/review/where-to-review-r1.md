## Linguistic Scan
No linguistic errors found.

## Exercise Check
4 markers are present: `fill-in-accusative`, `quiz-de-or-kudy`, `group-sort-de-kudy`, `quiz-yty-or-ikhaty`.

They appear after the relevant teaching sections and map cleanly to the 4 `activity_hints` in the plan. Marker placement is acceptable; I do not see any sequencing problem from the prose side. I cannot audit downstream YAML answer logic here because only the markers are visible.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Core grammar is covered, but the first dialogue uses `Я йду на роботу... Потім іду в магазин` instead of the planned `на пошту` / `в аптеку` split-up scenario, and `ULP` / `Episode 18` never appears. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym slips, bad case endings, or forbidden Russian letters found; spot-checks with local VESUM/RAG confirmed forms such as `Одесу`, `Львів`, `додому`, `вулицю`, and the locative/accusative pairs. |
| 3. Pedagogical quality | 7/10 | The module has a clear PPP shape, but some rule presentation is too English-heavy before examples, e.g. `There is excellent news for learners... the "No-Change" rule...`. |
| 4. Vocabulary coverage | 8/10 | All required plan vocabulary appears in prose, and several recommended items do too, but planned dialogue vocabulary `пошта` and `аптека` is absent. |
| 5. Exercise quality | 9/10 | All 4 expected markers are present and placed after the relevant teaching: accusative formation, `Де?` vs `Куди?`, sorting, and `йти` vs `їхати`. |
| 6. Engagement & tone | 8/10 | Mostly teacherly, but some wording is overstated: `fundamental concept in Ukrainian grammar` and `Ukrainian grammar forces you...`. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and ordered correctly; markers are intact; pipeline word count is 1529, which is above the 1200 target. |
| 8. Cultural accuracy | 9/10 | No Russia-centering or factual cultural distortion; the Ukrainian errand/travel framing is acceptable. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers and a real errands scenario help, but the conversations are still very question-led, and the first dialogue misses the more natural split-up / meet-up pattern from the plan. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> **Оксана:** Я йду на роботу. *(I am going to work.)*` / `> **Оксана:** Потім іду в магазин. *(Then I am going to the shop.)*`  
Issue: The first dialogue diverges from the plan’s source-of-truth scenario, which specifically foregrounds `на пошту`, `в аптеку`, and the meet-up in `кафе`. That weakens coverage of the planned feminine-direction examples in the dialogue itself.  
Fix: Replace the dialogue lines with the planned split-up scenario using `на пошту`, `в аптеку`, and `зустрінемося в кафе`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `It is Saturday morning in the city. Oksana and Stepan are running errands together, but they have a long list of tasks to complete. They need to split up to visit different places around town efficiently. Listen as they coordinate their plans.`  
Issue: The plan explicitly cites `ULP Season 1, Episode 18`, but the generated module never names or integrates that reference.  
Fix: Replace the opening paragraph so it explicitly cites Ukrainian Lessons Podcast, Episode 18.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `There is excellent news for learners when forming these directional phrases: the "No-Change" rule applies to a massive portion of the Ukrainian vocabulary. Inanimate masculine nouns and all neuter nouns look completely identical to their basic nominative forms when used in the accusative case for direction. You do not need to memorize any new endings for these categories; simply take the dictionary form and add the correct preposition.`  
Issue: This is padded with motivational English instead of stating the rule directly. For an A1 grammar module, the rule should be brief and immediately usable.  
Fix: Replace it with a concise rule-first explanation, then let the bullet examples do the work.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `This dialogue introduces a fundamental concept in Ukrainian grammar: the strict separation of direction and location. Notice that Stepan specifically says **я йду в банк** to express his direction of movement. He does not say **я в банку**, which would mean he is already inside the bank standing still. Ukrainian grammar forces you to choose between moving toward a destination and resting at a location.`  
Issue: The tone is inflated and absolutist. It sounds like hype, not a calm teacher explanation.  
Fix: Replace it with a shorter contrast that simply shows `я йду в банк` versus `я в банку`.

## Verdict: REVISE
REVISE. The module is linguistically clean, but it has major plan-adherence and pedagogy issues, and multiple dimensions fall below 9. These are fixable by targeted edits rather than a full rebuild.

<fixes>
- find: |-
    It is Saturday morning in the city. Oksana and Stepan are running errands together, but they have a long list of tasks to complete. They need to split up to visit different places around town efficiently. Listen as they coordinate their plans.
  replace: |-
    It is Saturday morning in the city. This opening dialogue follows the same everyday pattern as Ukrainian Lessons Podcast, Episode 18: two friends compare where they are going and use **Куди?** to talk about direction.
- find: |-
    > **Оксана:** **Куди** (where to) ти йдеш? *(Where are you going?)*
    > **Степан:** Я йду в банк. А ти? *(I am going to the bank. And you?)*
    > **Оксана:** Я йду на роботу. *(I am going to work.)*
    > **Степан:** А потім? *(And then?)*
    > **Оксана:** Потім іду в магазин. *(Then I am going to the shop.)*
    > **Степан:** А потім ходімо в кафе! *(And then let's go to a cafe!)*
  replace: |-
    > **Оксана:** **Куди** (where to) ти йдеш? *(Where are you going?)*
    > **Степан:** Я йду в банк. А ти? *(I am going to the bank. And you?)*
    > **Оксана:** Я йду на пошту. *(I am going to the post office.)*
    > **Степан:** А потім? *(And then?)*
    > **Оксана:** Потім іду в аптеку. *(Then I am going to the pharmacy.)*
    > **Степан:** А потім зустрінемося в кафе! *(And then we will meet in a cafe!)*
- find: |-
    This dialogue introduces a fundamental concept in Ukrainian grammar: the strict separation of direction and location. Notice that Stepan specifically says **я йду в банк** to express his direction of movement. He does not say **я в банку**, which would mean he is already inside the bank standing still. Ukrainian grammar forces you to choose between moving toward a destination and resting at a location.
  replace: |-
    This dialogue shows the key contrast for this module: **я йду в банк** means movement toward a place, while **я в банку** means the speaker is already there.
- find: |-
    There is excellent news for learners when forming these directional phrases: the "No-Change" rule applies to a massive portion of the Ukrainian vocabulary. Inanimate masculine nouns and all neuter nouns look completely identical to their basic nominative forms when used in the accusative case for direction. You do not need to memorize any new endings for these categories; simply take the dictionary form and add the correct preposition.
  replace: |-
    For inanimate masculine and neuter place nouns, the accusative for direction is the same as the nominative. Add the preposition **в/у** or **на**, but do not change the noun ending.
</fixes>