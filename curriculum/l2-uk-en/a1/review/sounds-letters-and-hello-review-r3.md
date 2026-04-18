## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or banned Russian characters found.

One factual phonetics error remains in the consonant section: `[=]` is described as “a double dash,” and the hard/soft contrast is called “a uniquely Slavic characteristic.” The first mislabels the notation; the second overstates the linguistics.

## Exercise Check
6 `INJECT_ACTIVITY` markers found.

Order matches `activity_obligations` exactly: `quiz`, `match-up`, `fill-in`, `group-sort`, `letter-grid`, `watch-and-repeat`.

This is a marker-only module, so the exercise check passes on count, order, and type.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Section order is correct, required vocabulary is present, and section pacing is within tolerance (`307 / 257 / 244 / 278 / 143` words by section). The miss is in the consonant beat: the prose only says `There are a few special consonant letters to recognize,` instead of delivering the contracted Anna Ohoiko consonant inventory and example-word framing. |
| 2. Linguistic accuracy | 7/10 | Ukrainian forms are clean, but the consonant paragraph says soft sounds are `marked with a double dash [=]` and calls the hard/soft contrast `a uniquely Slavic characteristic.` |
| 3. Pedagogical quality | 8/10 | Good textbook grounding and concrete examples (`ма-ма`, `мо-ло-ко`, `Привіт` sound analysis), but the consonant section underdelivers the planned guided inventory work and stays more explanatory than practice-oriented. |
| 4. Vocabulary coverage | 9/10 | All required targets appear naturally in prose: `звук`, `літера`, `голосні`, `приголосні`, `Привіт`, `Як справи`, `Добре`, `Чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 10/10 | Marker-only module: 6 markers present, order matches the contract exactly, and every marker type matches the contracted type prefix. |
| 6. Engagement & tone | 9/10 | Clear, teacherly, and concrete; the poems, classroom exchange, and `Привіт` sound analysis keep the lesson grounded in actual language. |
| 7. Structural integrity | 6/10 | All H2 headings are present and ordered correctly, but the pipeline word count is `1165`, below the `1200` floor. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian on its own terms and avoids Russia-centric framing. |
| 9. Dialogue & conversation quality | 9/10 | Both contracted situations are present, named speakers are used where required, and the second dialogue includes reciprocal `А у тебе?`. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `A consonant sound can be **тверді** (hard), marked with a single dash [–] in sound models, or **м'які** (soft), marked with a double dash [=]. This fundamental distinction between hard and soft sounds does not exist in English. It is a uniquely Slavic characteristic that gives the language its flowing rhythm.`  
Issue: `[=]` is not a “double dash”; it is the equals-sign notation used here for soft consonants. The sentence also overstates the linguistics: this contrast is important in Ukrainian and common across Slavic languages, not “uniquely Slavic.”  
Fix: Change `double dash [=]` to `equals sign [=]` and narrow the final claim to `It is a major feature of Ukrainian and other Slavic languages.`

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `There are a few special consonant letters to recognize. The letter **Ґ** represents the hard [g] sound, exactly like the "g" in "go." However, the much more common letter **Г** represents a deep, pharyngeal [h] sound. Another unique letter is **Щ**, which always represents two distinct sounds spoken together: [шч].`  
Issue: The contract’s third consonant teaching beat requires the Anna Ohoiko consonant inventory and the “see the letter / hear the sound / example words” framing. The prose only highlights Ґ, Г, and Щ, so that beat is undercovered.  
Fix: Add one sentence naming the contracted consonant set and stating that the videos show the letter, the sound, and example words.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: `PIPELINE NOTE — Word count: 1165 words`  
Issue: The module misses the 1200-word minimum.  
Fix: Add at least 35 words of contracted content; the consonant-video insert below is sufficient if applied.

## Verdict: REVISE
There is a critical factual error in the consonant notation/linguistics paragraph, and the module is also below the 1200-word floor.

<fixes>
- find: |-
    Ukrainian has thirty-two consonant sounds, but uses only twenty-two consonant letters to write them. This happens because many consonants come in pairs. A consonant sound can be **тверді** (hard), marked with a single dash [–] in sound models, or **м'які** (soft), marked with a double dash [=]. This fundamental distinction between hard and soft sounds does not exist in English. It is a uniquely Slavic characteristic that gives the language its flowing rhythm.
  replace: |-
    Ukrainian has thirty-two consonant sounds, but uses only twenty-two consonant letters to write them. This happens because many consonants come in pairs. A consonant sound can be **тверді** (hard), marked with a single dash [–] in sound models, or **м'які** (soft), marked with an equals sign [=]. This fundamental distinction between hard and soft sounds does not exist in English. It is a major feature of Ukrainian and other Slavic languages.
- insert_after: |-
    There are a few special consonant letters to recognize. The letter **Ґ** represents the hard [g] sound, exactly like the "g" in "go." However, the much more common letter **Г** represents a deep, pharyngeal [h] sound. Another unique letter is **Щ**, which always represents two distinct sounds spoken together: [шч].
  content: |-
    Anna Ohoiko's consonant videos then walk through **М, Н, С, К, Л, Р, Б, В, Д, П, Т, Г, Ґ, З, Ж, Ш, Х, Й, Ч, Щ, Ц, Ф** one by one: you see the letter, hear the sound, and meet it in example words.
</fixes>