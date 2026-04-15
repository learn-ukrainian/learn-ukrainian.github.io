## Linguistic Scan
No definitive Russianisms, Surzhyk, calques, or paronym errors found.

One factual grammar error found:
- `[CRITICAL]` In `В чи на?`, the tip says: `Ukrainian uses **у** instead of **в** before words starting with consonants ... and **в** after vowels`. That is too rigid and teaches the `у/в` alternation incorrectly. In this repo’s own euphony materials, `у/в` is based on surrounding sounds and smoothness, not a single next-word rule. Contrasts such as `Я живу в Києві` and `Тарас у Львові` show why the current wording is misleading.

## Exercise Check
- Marker inventory is complete: `match-up-nominative-locative`, `fill-in-answer-where`, `quiz-v-or-na`, `quiz-where-is-it`.
- Marker IDs match the activity YAML.
- Placement is weak: markers are clustered at lines 46, 48, 68, and 70. There is no activity after `Діало́ги` and none after `Підсумок`.
- `match-up` and `fill-in` fit locative teaching; `quiz-v-or-na` fits section 3; `quiz-where-is-it` is cumulative and would fit better after the summary.
- No definitive answer-key error was found in the generated activities I checked.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | The contract asks for a newcomer-neighbor wayfinding dialogue with `аптека`, `банк`, `пошта`, `кафе`, `лікарня`, `парк`, but the prose gives only `Де зараз Олена?` and `Де ти живеш?... В офісі, на другому поверсі.` `Захарійчук` is absent, and `місто → у/в місті` is not introduced as a core pair. |
| 2. Linguistic accuracy | 6/10 | The tip `Ukrainian uses **у** instead of **в** before words starting with consonants ... and **в** after vowels` teaches an inaccurate rule for `у/в` alternation. |
| 3. Pedagogical quality | 6/10 | The module often explains grammar in long English blocks, e.g. `There is a historical linguistic reason for this difference...`, and there is no practice immediately after the opening dialogues. |
| 4. Vocabulary coverage | 6/10 | Core chunks like `школа → в школі` and `робота → на роботі` are present, but prose searches returned `аптека=0`, `пошта=0`, `лікарня=0`, and `місто` appears only as `у/в місті`, not as the required nominative→locative pair. |
| 5. Exercise quality | 6/10 | All four markers exist, but they are bunched after sections 2 and 3, with no activity after `Діало́ги` or `Підсумок`, so practice is not evenly distributed. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and mostly substantive: `Memorize it to build your intuition!` and `Can you answer these simple questions in Ukrainian?` keep the voice instructional without gamified filler. |
| 7. Structural integrity | 5/10 | All H2s are present, but the pipeline total is 1162, below the 1200 target, and the pacing is visibly uneven: `В чи на?` is much longer than the thin summary. |
| 8. Cultural accuracy | 9/10 | The `в Україні` note is culturally aligned and decolonized: `Using **в Україні** affirms Ukraine's status as an independent state`. |
| 9. Dialogue & conversation quality | 6/10 | Speakers are named, but the required search-for-places scenario is missing, and much of the first dialogue is checklist Q&A: `А Тарас? ... А діти? ... А кішка?` |

## Findings
[Plan adherence] [SEVERITY: major]  
Location: `Діало́ги`, lines 5-21 — `Де за́раз Оле́на? ... А де ти працю́єш?`  
Issue: The required newcomer-neighbor wayfinding dialogue is missing. Searches on the prose returned `аптека=0`, `пошта=0`, `лікарня=0`; the adverb anchor is also mostly ignored (`там=0`, `вдома=0`, `далеко=0`, `близько=0`).  
Fix: Rewrite the dialogues section to keep the `Де Олена?` pattern but add the contracted wayfinding scene with `аптека`, `банк`, `пошта`, `кафе`, `лікарня`, `парк` and some of `тут/там/вдома/близько/далеко`.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `В чи на?`, line 55 — `Ukrainian uses **у** instead of **в** before words starting with consonants ... and **в** after vowels`  
Issue: This teaches the `у/в` alternation as a rigid next-word rule. That is factually wrong for Ukrainian euphony.  
Fix: Rewrite this section so it says the choice depends on surrounding sounds and smooth pronunciation, with contrasts like `в Києві`, `у Львові`, `в офісі`, `у банку`.

[Plan adherence] [SEVERITY: major]  
Location: `Місце́вий відмі́нок`, lines 27 and 39-44 — `In the fourth grade...` and the chunk list ending with `* парк → у/в парку (park)`  
Issue: The required textbook reference `Захарійчук` is missing, and the required core pair `місто → у/в місті` is not introduced as a nominative→locative chunk.  
Fix: Add the `Захарійчук Grade 4` reference to the section opening and add `* місто → у/в місті (city)` to the core chunk list.

[Exercise quality] [SEVERITY: major]  
Location: marker positions at lines 46, 48, 68, 70  
Issue: Practice is clustered after sections 2 and 3. There is no exercise after `Діало́ги`, and the cumulative `quiz-where-is-it` appears before the summary instead of after it.  
Fix: Move `fill-in-answer-where` to the end of `Діало́ги` and move `quiz-where-is-it` to the end of `Підсумок`.

[Structural integrity] [SEVERITY: major]  
Location: `Підсумок`, lines 74-82, plus pipeline note `Word count: 1162`  
Issue: The module is below target, and the summary does not deliver the contract’s full recap of common chunks: `в школі`, `на роботі`, `у банку`, `в парку`, `на вулиці`.  
Fix: Expand the summary with the missing core chunks and a short model Q&A, then place the final cumulative quiz after that recap.

## Verdict: REVISE
Critical grammar misinformation is present, and multiple contract requirements are missed, but the problems are still section-scoped and fixable with targeted rewrites plus marker moves.

<fixes>
- find: |
    Ukrainian children learn grammar using specific helper questions, which naturally link grammatical cases to their real-world function. In the fourth grade, students learn that the locative case, or **місцевий відмінок**, answers the questions **на/у ко́му? на/у чому́?** (on/in whom? on/in what?).
  replace: |
    As Захарійчук Grade 4 presents it, Ukrainian children learn grammar using specific helper questions, which naturally link grammatical cases to their real-world function. In the fourth grade, students learn that the locative case, or **місцевий відмінок**, answers the questions **на/у ко́му? на/у чому́?** (on/in whom? on/in what?).

- insert_after: |
    * парк → у/в парку (park)
  content: |
    * місто → у/в місті (city)

- find: |
    Notice the preposition **на** is used for the street (**на вулиці**), while **в** is used for the city (**в Києві**) and the building (**в офісі**).

    ## Місце́вий відмі́нок (The Locative Case)
  replace: |
    Notice the preposition **на** is used for the street (**на вулиці**), while **в** is used for the city (**в Києві**) and the building (**в офісі**).

    <!-- INJECT_ACTIVITY: fill-in-answer-where -->

    ## Місце́вий відмі́нок (The Locative Case)

- find: |
    <!-- INJECT_ACTIVITY: match-up-nominative-locative -->

    <!-- INJECT_ACTIVITY: fill-in-answer-where -->
  replace: |
    <!-- INJECT_ACTIVITY: match-up-nominative-locative -->

- find: |
    <!-- INJECT_ACTIVITY: quiz-v-or-na -->

    <!-- INJECT_ACTIVITY: quiz-where-is-it -->

    ## Підсумок — Summary
  replace: |
    <!-- INJECT_ACTIVITY: quiz-v-or-na -->

    ## Підсумок — Summary

- insert_after: |
    *   **Де ви живете́?** (Where do you live?) Do you live **у/в місті** (in a city) or **на вулиці** (on a street)?
  content: |

    Keep these core chunks together: **в школі**, **на роботі**, **у банку**, **в парку**, **на вулиці**, **у місті**. You can also contrast common fixed phrases such as **у лікарні** but **на пошті**, or **в місті** but **на площі**.

    For example: **Де Олена? — Вона в школі. Де Тарас? — Він на роботі. Де гроші? — Вони у банку. Де діти? — Вони в парку.** If you can answer **де?** with whole phrases like these, you are already using the locative case correctly.

    <!-- INJECT_ACTIVITY: quiz-where-is-it -->
</fixes>

<rewrite-block section="Діало́ги (Dialogues)">
Rewrite only this section. Keep the exact H2 heading. Preserve the contract’s first dialogue pattern (`Де Олена? — Вона в школі. ... А кішка? — Вона на дивані!`), but make the second dialogue the required newcomer-neighbor wayfinding scene from the contract. The rewritten section must naturally include `аптека`, `банк`, `пошта`, `кафе`, `лікарня`, and `парк`, and it should also bring in some of the missing adverbs from the wiki anchor such as `тут`, `там`, `вдома`, `близько`, or `далеко`. Keep named speakers, keep the focus on answering `де?`, and bring the section into the 270-330 word budget.
</rewrite-block>

<rewrite-block section="В чи на? (В or На?)">
Rewrite only this section. Keep the exact H2 heading. Shorten the section to the contract budget, preserve the core contrasts (`в школі`, `у банку`, `на вулиці`, `на площі`, `на роботі`, `на пошті`, `на вокзалі`, `в Україні`), but remove the rigid euphony tip. Replace it with an accurate explanation that `у/в` choice depends on surrounding sounds and smooth pronunciation, using contrasts like `в Києві`, `у Львові`, `в офісі`, and `у банку`. Keep the cultural note about `в Україні`, but express it more compactly.
</rewrite-block>