## Linguistic Scan
No linguistic errors found.

## Exercise Check
The three markers are placed sensibly and in the right order after relevant teaching sections:
`quiz-comprehensive-review` after self-check, `match-up-questions-answers` after grammar, `fill-in-self-introduction` after the capstone dialogue.

The marker types match the plan’s three `activity_hints`, and the markers are spread across the module rather than clustered at the end.

One generated exercise has a logic problem:
`fill-in-self-introduction` includes `Я живу ____ Києві.`, but the module text teaches `Я з...`, not `жити в + locative`. A search of the prose found 0 occurrences of `живу`, `Я живу`, `в Києві`, and `Києві`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The reading section says `Read the following sentences aloud` and then gives 13 bullet sentences, not the planned `short Ukrainian text (8-10 sentences)`. The plan also calls for `Following Anna Ep10 'Я і моя сім'я' review pattern`, but that reference is not cited. In grammar, the plan requires `Мій/моя/моє + noun`, while the prose explains only `мій` and `моя`. |
| 2. Linguistic accuracy | 9/10 | No confirmed Russianisms, Surzhyk, calques, or paronym errors found. Forms such as `Її звати Олена`, `Його звати Іван`, `Я з Дніпра`, and `Моє прізвище — Коваль` are standard Ukrainian. |
| 3. Pedagogical quality | 6/10 | The review often explains in English instead of modeling in Ukrainian. The reading practice is fragmented into bullets instead of the planned connected review text, and the grammar summary undercovers the possessive pattern by stopping at `мій` / `моя` instead of the planned full set. |
| 4. Vocabulary coverage | 7/10 | The recommended words `ім'я` and `прізвище` are included, but the dialogue also adds extra words in `Це дуже цікаво` and `У вас гарна сім'я` beyond the plan’s recommended additions for this checkpoint. |
| 5. Exercise quality | 6/10 | Marker placement is good, but the generated `fill-in-self-introduction` tests an untaught structure with `Я живу ____ Києві.` instead of recycling the taught `Я з...` chunk. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and calm rather than gamified or corporate. Lines like `Evaluate your progress honestly` fit a checkpoint module. |
| 7. Structural integrity | 9/10 | All planned H2 sections are present and in order, the markdown is clean, and the pipeline word count is 1280, above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian independently, uses Ukrainian cities and names naturally, and avoids Russia-centric framing. |
| 9. Dialogue & conversation quality | 7/10 | The speakers are named and the formal register fits the conference setting, but the family phase is thin: after `Це моя дружина на фото.` the conversation moves almost directly to goodbye instead of developing the planned family exchange. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Читання` — `Read the following sentences aloud...` followed by 13 bullet sentences  
Issue: The plan requires `A short Ukrainian text (8-10 sentences)` and explicitly references Anna’s Episode 10 review pattern. The module gives a bullet list instead of a connected text and never cites the reference.  
Fix: Replace the bullets with one short connected review paragraph and name the ULP Episode 10 pattern explicitly.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Граматика` — `use **мій** ... and **моя** ...`  
Issue: The plan requires `Мій/моя/моє + noun`, but the grammar summary never teaches the neuter possessive `моє`.  
Fix: Add `моє` with a neuter example such as `моє ім'я`, and pair origin review with both `Звідки ти?` and `Звідки ви?`.

[VOCABULARY COVERAGE] [SEVERITY: major]  
Location: `Діалог` — `Це дуже цікаво.` / `У вас гарна сім'я.`  
Issue: These add extra vocabulary not signposted in the plan’s recommended additions, and they do not help realize the checkpoint’s core family-review goal.  
Fix: Replace these turns with a short family exchange built from already taught family nouns and `У мене є...`.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `Діалог` — `Це моя дружина на фото.` → `До побачення!`  
Issue: The plan asks for a full cycle `greeting → name → origin → profession → family → showing photos → goodbye`, but the family portion is only a photo mention plus a compliment, not an actual exchange.  
Fix: Expand those two turns into a brief mutual family exchange before goodbye.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: injected activity `fill-in-self-introduction` — `Я живу ____ Києві.`  
Issue: This tests `жити в + locative`, which is not taught in the module prose; the prose contains 0 occurrences of `живу` and `Києві`.  
Fix: Replace it with a taught origin pattern such as `Я ____ України.`

## Verdict: REVISE
REVISE. There are no confirmed Ukrainian-language errors, but there are multiple major plan, pedagogy, dialogue, and exercise issues, and several scored dimensions fall below 9.

<fixes>
- find: |-
    This is a short narrative where a person introduces themselves, talks about their family members, and states everyone's professions. Every single phrase here is a pattern you have practiced before. Read the following sentences aloud, paying attention to the sounds and the natural rhythm of the language:

    * **Привіт!** (Hi!)
    * **Мене звати Анна.** (My name is Anna.)
    * **Я з України.** (I am from Ukraine.)
    * **Я з Києва.** (I am from Kyiv.)
    * **Це моя сім'я.** (This is my family.)
    * **Це моя мама.** (This is my mom.)
    * **Її звати Олена.** (Her name is Olena.)
    * **Вона вчителька.** (She is a teacher.)
    * **Це мій тато.** (This is my dad.)
    * **Його звати Іван.** (His name is Ivan.)
    * **Він інженер.** (He is an engineer.)
    * **Я студентка.** (I am a student.)
    * **Дуже приємно!** (Very nice to meet you!)
  replace: |-
    This is a short connected review text in the style of Anna's self-introduction review from ULP Season 1, Episode 10. Read it aloud once slowly, then once more smoothly.

    **Привіт! Мене звати Анна. Я з Києва, з України. Я студентка. Це моя сім'я. Це моя мама, її звати Олена, вона вчителька. Це мій тато, його звати Іван, він інженер. Дуже приємно!** (Hi! My name is Anna. I am from Kyiv, from Ukraine. I am a student. This is my family. This is my mother, her name is Olena, she is a teacher. This is my father, his name is Ivan, he is an engineer. Very nice to meet you!)
- find: |-
    Finally, review your possessive pronouns and expressions of origin. You must match the gender for your pronouns: use **мій** (my) for masculine nouns like **мій тато** (my dad), and **моя** (my) for feminine nouns like **моя мама** (my mom). When talking about your origin, reiterate the fixed chunk: **Звідки ти?** (Where are you from?), and answer clearly with **Я з...** (I am from...). This establishes your background immediately.
  replace: |-
    Finally, review your possessive pronouns and expressions of origin. You must match the gender for your pronouns: use **мій** (my) for masculine nouns like **мій тато** (my dad), **моя** (my) for feminine nouns like **моя мама** (my mom), and **моє** (my) for neuter nouns like **моє ім'я** (my name). When talking about your origin, review both chunks: **Звідки ти?** / **Звідки ви?** (Where are you from?) — **Я з...** (I am from...).
- find: |-
    > **Богдан:** Це дуже цікаво. Це моя дружина на фото. *(This is very interesting. This is my wife in the photo.)*
    > **Соломія:** Дуже гарно! У вас гарна сім'я. *(Very nice! You have a nice family.)*
  replace: |-
    > **Богдан:** Це моя дружина на фото. У мене є дружина і брат. А у вас є сім'я? *(This is my wife in the photo. I have a wife and a brother. Do you have a family?)*
    > **Соломія:** Так, у мене є мама, тато і сестра. *(Yes, I have a mother, a father, and a sister.)*
- find: |-
      - sentence: Я живу ____ Києві.
        answer: в
        options:
        - в
        - з
        - на
        - до
  replace: |-
      - sentence: Я ____ України.
        answer: з
        options:
        - в
        - з
        - на
        - до
</fixes>