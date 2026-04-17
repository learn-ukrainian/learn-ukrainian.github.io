## Linguistic Scan
No linguistic errors found.

## Exercise Check
Six `INJECT_ACTIVITY` markers are present. Count, order, and marker types match the contract exactly: `quiz`, `match-up`, `fill-in`, `group-sort`, `letter-grid`, `watch-and-repeat`.

One placement issue remains: `<!-- INJECT_ACTIVITY: fill-in -->` appears after `## Приголосні звуки (Consonant Sounds)` even though its contracted focus is the greeting dialogue from `## Привіт! (Hello!)`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All five H2 sections are present and most beats are covered, but four sections are over budget by more than 10%: `Звуки і літери` 382 vs target 300, `Голосні звуки` 300 vs 250, `Привіт!` 337 vs 250, `Підсумок` 175 vs 150. The contract also requires a separate classroom `Вчитель/Учні` greeting exchange with `Добрий день`, and `Добрий день` does not appear in the module. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, or incorrect Ukrainian forms found. VESUM-checked forms used in the module include `вчитель`, `учні`, `привіт`, `радий`, `рада`, and `нормально`. |
| 3. Pedagogical quality | 7/10 | Textbook framing is strong, and examples like `мама`, `молоко`, and the `привіт` sound analysis are useful, but the greeting `fill-in` activity marker is placed before the `Привіт!` section teaches the chunks it is meant to test. |
| 4. Vocabulary coverage | 10/10 | The prose naturally includes the contracted core items: `звук`, `літера`, `голосний`, `приголосний`, `привіт`, `як справи`, `добре`, `чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 10/10 | Marker-only module: marker count matches the 6 obligations, order matches the contract, and each marker type matches exactly. |
| 6. Engagement & tone | 7/10 | The summary uses rubric-banned journey language: `You have taken your first step into the Ukrainian language...` and `Your phonetic journey has officially begun.` |
| 7. Structural integrity | 10/10 | All required H2 headings are present and in the contracted order, markdown is clean, and the pipeline word count is 1387, which is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms through Ukrainian school pedagogy and textbook references, without Russian-centered framing. |
| 9. Dialogue & conversation quality | 8/10 | The Марко/Софія dialogue has named speakers and uses reciprocal `А у тебе?`, but the separate contracted classroom `Вчитель/Учні` greeting exchange is missing. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Привіт! (Hello!)` — `A **Вчитель** (teacher) often asks the **учні** (students) to practice basic greetings. Here, two new classmates meet in the hallway before their first Ukrainian lesson and introduce themselves.`  
Issue: The contract requires two dialogue acts in this module. The class greeting exchange with `Вчитель` / `Учні` and `Добрий день!` is missing; search confirms `Добрий день` does not appear anywhere in the module.  
Fix: Rewrite `## Привіт! (Hello!)` to include a short classroom exchange with `Вчитель:` / `Учні:` using `Привіт!` and `Добрий день!`, then keep the Марко/Софія hallway dialogue.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Звуки і літери (Sounds and Letters)`, `## Голосні звуки (Vowel Sounds)`, `## Привіт! (Hello!)`, `## Підсумок (Summary)`  
Issue: These sections exceed the contracted word budgets by more than 10%: 382/300, 300/250, 337/250, and 175/150 respectively.  
Fix: Regenerate only these sections to fit their budget ranges while preserving the contracted beats, textbook references, and required vocabulary.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: immediately after `## Приголосні звуки (Consonant Sounds)` — `<!-- INJECT_ACTIVITY: fill-in -->`  
Issue: The fill-in activity tests greeting chunks (`Привіт`, `Як справи`, `Добре`, `А у тебе?`) before the learner reaches the greeting section that teaches them.  
Fix: Move `<!-- INJECT_ACTIVITY: fill-in -->`, `<!-- INJECT_ACTIVITY: group-sort -->`, and `<!-- INJECT_ACTIVITY: letter-grid -->` to the end of `## Привіт! (Hello!)`, immediately before `<!-- INJECT_ACTIVITY: watch-and-repeat -->`, so the greeting activity comes after the relevant teaching while marker order remains intact.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `## Підсумок (Summary)` — `You have taken your first step into the Ukrainian language by mastering its phonetic foundation.` / `Your phonetic journey has officially begun.`  
Issue: This is generic milestone language the rubric explicitly warns against; it adds mood but not teaching value.  
Fix: Rewrite the summary as a direct recap/self-check without journey framing.

## Verdict: REVISE
REVISE. No linguistic errors were found, but there are major contract and pedagogy issues: one required dialogue act is missing, four sections are materially over budget, and the greeting fill-in marker is placed before the greeting content.

<fixes>
- find: |
    <!-- INJECT_ACTIVITY: fill-in -->
    <!-- INJECT_ACTIVITY: group-sort -->
    <!-- INJECT_ACTIVITY: letter-grid -->
  replace: ""
- find: |
    There are two vowel sounds and four consonant sounds. Every type of sound you learned here appears in this one word.

    <!-- INJECT_ACTIVITY: watch-and-repeat -->
  replace: |
    There are two vowel sounds and four consonant sounds. Every type of sound you learned here appears in this one word.

    <!-- INJECT_ACTIVITY: fill-in -->
    <!-- INJECT_ACTIVITY: group-sort -->
    <!-- INJECT_ACTIVITY: letter-grid -->
    <!-- INJECT_ACTIVITY: watch-and-repeat -->
</fixes>

<rewrite-block section="Звуки і літери (Sounds and Letters)">
Rewrite only this section. Keep the exact H2 heading. Reduce it to 270-330 words. Preserve the Заболотний quote, the sound-vs-letter distinction, the 33 letters vs 38 sounds explanation, the role of Я/Ю/Є/Ї and Ь, the Litvinova “голосна літера” point, and a brief alphabet note with only 1-2 concise examples instead of the current extra filler.
</rewrite-block>

<rewrite-block section="Голосні звуки (Vowel Sounds)">
Rewrite only this section. Keep the exact H2 heading. Reduce it to 225-275 words. Preserve the Большакова poem, the 6 vowel sounds vs 10 vowel letters distinction, the [•] notation, and the `мама` / `молоко` listening examples, but cut repeated English explanation so the section stays within budget.
</rewrite-block>

<rewrite-block section="Привіт! (Hello!)">
Rewrite only this section. Keep the exact H2 heading. Reduce it to 225-275 words. Include both contracted dialogue acts: 1. a short classroom exchange with `Вчитель:` and `Учні:` using `Привіт!`, `Добрий день!`, `Як справи?`, `Добре.` 2. the named-speaker `Марко:` / `Софія:` hallway dialogue with `А у тебе?`. Keep the gendered `Рада/Радий тебе бачити!` note and the sound analysis of `привіт`.
</rewrite-block>

<rewrite-block section="Підсумок (Summary)">
Rewrite only this section. Keep the exact H2 heading. Reduce it to 135-165 words. Preserve the self-check format and the key answers about 33 letters, 38 sounds, vowels vs consonants, `голосна літера`, `привіт`, and `як справи`, but remove the generic “first step/journey” phrasing.
</rewrite-block>