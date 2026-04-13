## Linguistic Scan
No Russianisms, Surzhyk forms, paronym mixups, or banned Russian letters were found in the verified Ukrainian wordforms.

Problems found:
- Wrong learner-facing gloss: `Вона — українка. *(I am a Ukrainian woman.)*` mismatches the Ukrainian sentence. It should be `She is a Ukrainian woman.`
- Factually wrong grammar claim: `You must say **Хто це?** and never reverse the order to *Це хто?.` This is too absolute; internal reference material in `docs/references/dobra-forma/chapters/7.3.md` uses `А це хто?`, so the module should teach `Хто це? / Що це?` as the default beginner pattern, not as an absolute ban.

## Exercise Check
Markers present: `fill-in-dialogue`, `quiz-formal-informal`, `match-up-professions`, `fill-in-self-intro`.

All four markers match the four `activity_hints` in the plan, and each marker appears after the teaching it is supposed to test. They are also spread sensibly through the module rather than clustered at the end. No exercise-placement or marker-ID issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present and the four activity markers match the four hints, but plan references are not integrated: searches of the generated text for `Anna`, `Episode`, and `ULP` return 0 occurrences. |
| 2. Linguistic accuracy | 6/10 | The module teaches a wrong gloss in `Вона — українка. *(I am a Ukrainian woman.)*` and an overgeneralized grammar rule in `You must say **Хто це?** and never reverse the order to *Це хто?.` |
| 3. Pedagogical quality | 7/10 | The PPP flow is mostly intact and examples are plentiful, but the module overstates grammar in `The structure of the question is strict...` and wastes teaching space on hype like `an incredibly versatile and powerful tool for beginners.` |
| 4. Vocabulary coverage | 9/10 | Required items such as `мене звати`, `як тебе/вас звати?`, `це`, `звідки`, pronouns, professions, and nationality forms all appear in prose; recommended items like `його`, `її`, `друг`, `Канада`, and `Німеччина` are also included. |
| 5. Exercise quality | 10/10 | All four planned activity hints have matching markers, and each marker is placed after the relevant teaching section. |
| 6. Engagement & tone | 7/10 | The teacher voice is clear, but lines like `an incredibly versatile and powerful tool` and `absolutely perfect` add generic hype instead of substance. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and ordered correctly, marker count is complete, and the pipeline word count is 1580, above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian on its own terms, handles formal vs informal register appropriately, and avoids Russia-centered framing. |
| 9. Dialogue & conversation quality | 7/10 | Dialogues 1-2 are usable, but “Dialogue 3” is not actually dialogic: all four lines are spoken by `Софія`, so it reads as a fact list rather than a conversation. |

## Findings
[DIMENSION 2] [SEVERITY: critical]  
Location: `- **Вона — українка.** *(I am a Ukrainian woman.)*`  
Issue: The English gloss is wrong. `Вона` means `she`, not `I`. This teaches an incorrect pronoun mapping.  
Fix: Change the gloss to `*(She is a Ukrainian woman.)*`.

[DIMENSION 2] [SEVERITY: critical]  
Location: `The structure of the question is strict: the question word must always go first. You must say **Хто це?** and never reverse the order to *Це хто?.`  
Issue: This teaches a false absolute rule. `Хто це? / Що це?` are the neutral beginner patterns, but the categorical ban is inaccurate; internal reference material in `docs/references/dobra-forma/chapters/7.3.md` uses `А це хто?`.  
Fix: Rephrase this as a beginner-production guideline, not a grammatical impossibility.

[DIMENSION 1] [SEVERITY: major]  
Location: Module-wide; relevant sections begin `To state your name...`, `When talking about professions...`, and `To ask someone about their geographic origin...`  
Issue: The plan explicitly supplies ULP references for Episodes 3, 4, and 8, but the generated text never cites them. Searches for `Anna`, `Episode`, and `ULP` in the generated module return 0 matches.  
Fix: Add brief source mentions in the name, professions, and `Звідки?` sections.

[DIMENSION 9] [SEVERITY: major]  
Location:  
`> **Софія:** Це Андрій. Він зі Львова.`  
`> **Софія:** Він — інженер.`  
`> **Софія:** А це Оксана. Вона з Одеси.`  
`> **Софія:** Вона — лікарка.`  
Issue: Dialogue 3 is presented as a dialogue but only one speaker talks. It does not model an actual exchange.  
Fix: Turn it into a short multi-speaker interaction.

[DIMENSION 3] [SEVERITY: minor]  
Location: `The word **це** (this is) is an incredibly versatile and powerful tool for beginners.`  
Issue: This is inflated teacher-talk. It adds enthusiasm but no real instruction.  
Fix: Replace it with a tighter, information-first sentence.

## Verdict: REVISE
REVISE. There are critical learner-facing errors in linguistic accuracy, plus major plan and dialogue issues. This cannot pass with dimension scores below 9 and active findings that require fixes.

<fixes>
- find: "- **Вона — українка.** *(I am a Ukrainian woman.)*"
  replace: "- **Вона — українка.** *(She is a Ukrainian woman.)*"
- find: "The structure of the question is strict: the question word must always go first. You must say **Хто це?** and never reverse the order to *Це хто?."
  replace: "For beginners, treat **Хто це?** and **Що це?** as your default patterns. They are the clearest neutral forms and the ones you should produce first."
- find: |-
    > **Софія:** Це Андрій. Він зі Львова. *(This is Andriy. He is from Lviv.)*
    > **Софія:** Він — інженер. *(He is an engineer.)*
    > **Софія:** А це Оксана. Вона з Одеси. *(And this is Oksana. She is from Odesa.)*
    > **Софія:** Вона — лікарка. *(She is a doctor.)*
  replace: |-
    > **Софія:** Це Андрій. Він зі Львова. Він — інженер. *(This is Andriy. He is from Lviv. He is an engineer.)*
    > **Тарас:** Дуже приємно! *(Pleased to meet you!)*
    > **Софія:** А це Оксана. Вона з Одеси. Вона — лікарка. *(And this is Oksana. She is from Odesa. She is a doctor.)*
    > **Оксана:** Дуже приємно! *(Pleased to meet you!)*
- find: "To state your name, use **мене звати** followed by your name."
  replace: "To state your name, use **мене звати** followed by your name. This follows ULP Season 1, Episode 3, where **мене звати** is the core first-meeting pattern."
- find: "When talking about professions, Ukrainian grammar requires gender agreement."
  replace: "Following ULP Season 1, Episode 8, when talking about professions, Ukrainian grammar requires gender agreement."
- find: "To ask someone about their geographic origin, you use the question word **звідки** (where from)."
  replace: "To ask someone about their geographic origin, you use the question word **звідки** (where from). This section follows ULP Season 1, Episode 4, which introduces **Звідки ти? / Звідки ви?** as early conversation patterns."
- find: "The word **це** (this is) is an incredibly versatile and powerful tool for beginners."
  replace: "The word **це** (this is) is one of the most useful beginner tools."
</fixes>