## Linguistic Scan
No linguistic errors found.

## Exercise Check
Markers found: `fill-in-dialogues`, `match-up-body-parts`, `fill-in-symptoms`, `quiz-logical-response`. All four appear after the relevant teaching sections, are reasonably spread across the module, and semantically cover the four `activity_hints` from the plan. No inline DSL exercise blocks are present, so there is no visible distractor logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned sections are present, but the plan references are uncited (`State Standard`: 0 hits; `Grade 1-2`: 0 hits), and `нога/око/вухо/ніс` never enter the main `У мене болить...` practice pattern. |
| 2. Linguistic accuracy | 10/10 | No Russianisms/Surzhyk/calques found in the Ukrainian text; VESUM verification supports `нежить` and `нежитю`, and Russian letters `ы э ё ъ` occur 0 times. |
| 3. Pedagogical quality | 6/10 | The module opens with off-target filler (`Це велика лікарня... Я купую ліки тут.`) instead of moving straight into the practical scene, and the body-section note overstates `рука/нога` by saying learners “do not need separate words for "hand" or "foot"”. |
| 4. Vocabulary coverage | 8/10 | Required plan vocab appears, but several body parts stay trapped in lists: exact searches for `У мене болить нога/око/вухо/ніс` return 0. |
| 5. Exercise quality | 9/10 | Four markers appear after the relevant sections and cover the four plan hints; no inline exercise logic is visible to audit further. |
| 6. Engagement & tone | 6/10 | The prose leans on generic directives and filler: `You must remember that noun gender...`, `Recognizing the gender helps reinforce your grammatical reflex...`, `This core vocabulary allows you to handle the vast majority of standard medical complaints.` |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present and ordered correctly, markers are clean, and the pipeline word count is 1201. |
| 8. Cultural accuracy | 10/10 | No Russian-centric framing or cultural misinformation; the module treats Ukrainian on its own terms. |
| 9. Dialogue & conversation quality | 9/10 | Two multi-turn dialogues use named speakers and stay on-topic for doctor/pharmacy situations, though the pharmacy scene is intentionally simple. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Тіло (The Body)` opening paragraph — `"The vocabulary for the head and face area is fundamental. Memorize these basic nouns:"`  
Issue: The module never cites or integrates the plan’s named references (`State Standard 2024, §3`; `Grade 1-2 textbook: Частини тіла`).  
Fix: Add a brief reference sentence before the noun list.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Dialogues` opening lines — `"**Це велика лікарня.** ... **Я купую ліки тут.**"`  
Issue: The section opens with off-target filler and extra vocabulary instead of moving directly into the practical doctor/pharmacy scene promised by the plan.  
Fix: Replace the filler mini-paragraph with target-chunk micro-context using `У мене болить...`, `У мене температура`, `Мені погано`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Тіло (The Body)` note — `"You do not need separate words for "hand" or "foot" in basic everyday communication; the context makes your meaning perfectly clear."`  
Issue: This overstates the simplification and turns a useful A1 shortcut into a factual claim about the language.  
Fix: Rephrase it as an A1-scoping note: focus on `рука` and `нога` now; learn more specific terms later.

[VOCABULARY COVERAGE] [SEVERITY: major]  
Location: `## У мене болить... (It Hurts...)` example list ending with `"* **У мене болить рука.** (My arm hurts.)"`  
Issue: `нога`, `око`, `вухо`, and `ніс` are listed as key body parts, but they never appear inside the module’s main symptom pattern; exact searches for `У мене болить нога/око/вухо/ніс` return 0.  
Fix: Add these nouns to the beginner pattern list so learners see them in the target chunk.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `## Тіло (The Body)` explanation paragraph — `"You must remember that noun gender (masculine, feminine, neuter) remains an important concept here. As taught in previous modules, the gender of a body part dictates the adjective agreement when you describe it. Recognizing the gender helps reinforce your grammatical reflex for building accurate sentences."`  
Issue: This is overly abstract and directive for A1; it explains pedagogy instead of giving short, usable guidance.  
Fix: Replace it with a brief recognition-focused cue.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `## Summary` sentence — `"This core vocabulary allows you to handle the vast majority of standard medical complaints."`  
Issue: Empty overclaim/filler; it adds confidence language instead of teaching new Ukrainian.  
Fix: Replace it with a concrete, bounded claim about describing common problems clearly and politely.

## Verdict: REVISE
REVISE. The Ukrainian itself is clean, but there are multiple major issues in plan adherence, pedagogy, vocabulary activation, and tone, and dimensions 1, 3, 4, and 6 fall below 9.

<fixes>
- find: "The vocabulary for the head and face area is fundamental. Memorize these basic nouns:"
  replace: "The vocabulary for the head and face area is fundamental. This topic aligns with the State Standard 2024 thematic area «здоров’я» and the Grade 1-2 textbook topic «Частини тіла». Memorize these basic nouns:"
- find: |
    **Це велика лікарня.** (This is a big hospital.)
    **Тут працює гарний лікар.** (A good doctor works here.)
    **А там є аптека.** (And there is a pharmacy there.)
    **Я купую ліки тут.** (I buy medicine here.)
    > *This is a big hospital. A good doctor works here. And there is a pharmacy there. I buy medicine here.*
  replace: |
    **У мене болить горло.** (My throat hurts.)
    **У мене температура.** (I have a fever.)
    **Мені погано.** (I feel bad.)
    > *My throat hurts. I have a fever. I feel bad.*
- find: "In Ukrainian, the word **рука** refers to the entire arm, including the hand. Similarly, the word **нога** refers to the entire leg, including the foot. You do not need separate words for \"hand\" or \"foot\" in basic everyday communication; the context makes your meaning perfectly clear."
  replace: "In Ukrainian, the word **рука** can refer to the whole arm or the hand, and **нога** can refer to the whole leg or the foot. For this A1 module, focus on these two high-frequency words; you can learn more specific terms later."
- find: |
    * **У мене болить голова.** (My head hurts.)
    * **У мене болить живіт.** (My stomach hurts.)
    * **У мене болить горло.** (My throat hurts.)
    * **У мене болить спина.** (My back hurts.)
    * **У мене болить зуб.** (My tooth hurts.)
    * **У мене болить рука.** (My arm hurts.)
  replace: |
    * **У мене болить голова.** (My head hurts.)
    * **У мене болить живіт.** (My stomach hurts.)
    * **У мене болить горло.** (My throat hurts.)
    * **У мене болить спина.** (My back hurts.)
    * **У мене болить зуб.** (My tooth hurts.)
    * **У мене болить рука.** (My arm hurts.)
    * **У мене болить нога.** (My leg hurts.)
    * **У мене болить вухо.** (My ear hurts.)
    * **У мене болить око.** (My eye hurts.)
    * **У мене болить ніс.** (My nose hurts.)
- find: "You must remember that noun gender (masculine, feminine, neuter) remains an important concept here. As taught in previous modules, the gender of a body part dictates the adjective agreement when you describe it. Recognizing the gender helps reinforce your grammatical reflex for building accurate sentences. Look at these clear examples demonstrating the pattern:"
  replace: "Notice the gender pattern: body-part gender changes adjective agreement. As taught in previous modules, use these examples for recognition, not as a new grammar rule to master here:"
- find: "This core vocabulary allows you to handle the vast majority of standard medical complaints."
  replace: "This core vocabulary lets you describe a few common problems clearly and politely."
</fixes>