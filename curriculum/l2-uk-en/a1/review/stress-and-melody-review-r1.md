## Linguistic Scan
- Factually wrong grammar classification in `Інтонація`: `Third, we have **спонукальні** (imperative) or **окличні** (exclamatory) sentences, which give commands or show strong emotion.` This teaches the wrong system. By purpose, the three types are `розповідні`, `питальні`, `спонукальні`; `окличні` is a separate dimension.
- Wrong syllable division in `Читаємо вголос`: `**ві-дпо-чи-нок**` should be `**від-по-чи-нок**`.

## Exercise Check
Found 4 markers:
- `match-stress-pairs`
- `quiz-sentence-types`
- `fill-in-punctuation`
- `quiz-find-stress`

Marker placement is correct:
- `match-stress-pairs` comes after the stress explanation.
- `quiz-sentence-types` and `fill-in-punctuation` come after the intonation explanation.
- `quiz-find-stress` comes after the read-aloud section.

Marker IDs match the 4 `activity_hints` in the plan, and the generated activities meet or exceed the planned item counts. No exercise logic issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All four planned sections appear in order and cover the plan’s core points: free/mobile stress, `замок / мука / атлас`, `Київ — столиця України`, and the final self-check. Minor deduction: the prose does not cite the plan’s named references in-text. |
| 2. Linguistic accuracy | 5/10 | Two critical teaching errors: `Third, we have **спонукальні** (imperative) or **окличні** (exclamatory) sentences` misclassifies sentence types, and `**ві-дпо-чи-нок**` gives a wrong syllable split. |
| 3. Pedagogical quality | 8/10 | The lesson has a clear teach-then-practice flow (`First, break the word into syllables. Second, find the stressed syllable. Finally, read the whole word...`), but the two critical phonetics/grammar errors make the teaching unsafe as written. |
| 4. Vocabulary coverage | 9/10 | Required/recommended vocabulary is integrated naturally in prose: `наголос`, `замок`, `кава`, `вода`, `столиця`, `мука`, `ранок`, `метро`, `фотографія`. |
| 5. Exercise quality | 10/10 | The four markers are staged immediately after the relevant teaching and align with the plan’s focus areas: stress pairs, sentence type by punctuation, punctuation fill-in, and stress-position quiz. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and concrete rather than gamified; lines like `Getting the stress wrong means you are saying a completely different word` keep the focus on usable phonetics. |
| 7. Structural integrity | 10/10 | All required H2 headings are present and ordered correctly, and the pipeline word count is 1327, which is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module treats Ukrainian phonetics on Ukrainian terms and uses `Київ — столиця України` naturally, with no Russia-centered framing. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue has named speakers and natural A1 small talk: `Привіт! Як справи?` / `Добре! А у тебе?` |

## Findings
[DIMENSION] [SEVERITY: minor]  
Location: Stress / Intonation / Reading Aloud — `The Ukrainian language has exactly 38 sounds.`; `We classify sentences by their main purpose.`; `Here is a word stress reading practice section.`  
Issue: The draft restates the plan’s sourced claims but never cites the plan’s named references in prose (`Заболотний Grade 5, p.73`, `Авраменко Grade 5, p.19`, `ULP Season 1, Episode 5`).  
Fix: Add brief in-text source attributions in those three sections.

[DIMENSION] [SEVERITY: critical]  
Location: `Інтонація` — `Third, we have **спонукальні** (imperative) or **окличні** (exclamatory) sentences, which give commands or show strong emotion.`  
Issue: This teaches wrong grammar. `Окличні` is not the third sentence-purpose type; it is a separate emotional/intonational dimension that can apply to `розповідні`, `питальні`, or `спонукальні` sentences.  
Fix: Rewrite the sentence so `спонукальні` remains the third main type and `окличні` is presented as a separate dimension.

[DIMENSION] [SEVERITY: critical]  
Location: `Читаємо вголос` — `Now try the word for rest: **ві-дпо-чи-нок**.`  
Issue: The syllable division is wrong. `дпо` is not a valid syllable here; the correct division is `від-по-чи-нок`. Wrong syllable division is a phonetics-teaching error.  
Fix: Replace `**ві-дпо-чи-нок**` with `**від-по-чи-нок**`.

## Verdict: REVISE
REVISE. The module is structurally strong and the exercise scaffolding is good, but it contains two critical teaching errors in core phonetics/grammar content, so it cannot pass as written.

<fixes>
- find: |-
    The concept of **наголос** (stress) is fundamental in Ukrainian. The Ukrainian language has exactly 38 sounds.
  replace: |-
    The concept of **наголос** (stress) is fundamental in Ukrainian. As Заболотний Grade 5, p.73 notes, the Ukrainian language has exactly 38 sounds.
- find: |-
    We classify sentences by their main purpose. There are three main types. First, we have **розповідні** (declarative) sentences, which tell you facts. Second, we have **питальні** (interrogative) sentences, which ask questions. Third, we have **спонукальні** (imperative) or **окличні** (exclamatory) sentences, which give commands or show strong emotion.
  replace: |-
    As Авраменко Grade 5, p.19 explains, we classify sentences by their main purpose. There are three main types. First, we have **розповідні** (declarative) sentences, which tell you facts. Second, we have **питальні** (interrogative) sentences, which ask questions. Third, we have **спонукальні** (imperative) sentences, which give commands. Any of these sentence types can also be **окличні** (exclamatory), which is a separate dimension that adds strong emotion.
- find: |-
    Now try the word for rest: **ві-дпо-чи-нок**. The stress is on the **и**.
  replace: |-
    Now try the word for rest: **від-по-чи-нок**. The stress is on the **и**.
- find: |-
    Here is a word stress reading practice section.
  replace: |-
    Following the stress-drill approach in ULP Season 1, Episode 5, here is a word stress reading practice section.
</fixes>