## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or banned Russian characters were found in the Ukrainian text I checked.

- Factual phonetics error: `Next, look at the word for photograph: **фо-то-гра-фі-я**. The stress falls on the third **а**.` SУМ-11 gives `ФОТОГРА́ФІЯ`, so the stressed syllable is `гра`.
- Factual intonation error: `The punctuation tells you exactly which melody to use.` This is wrong in the module’s own system, because both `Це кава?` and `Що це?` take `?`, but the module assigns them different melodies.

## Exercise Check
- Marker inventory matches the 4 plan hints: `match-stress-pairs`, `quiz-sentence-types`, `fill-in-punctuation`, `quiz-find-stress`.
- Placement is correct: each marker appears after the relevant teaching section.
- Markers are reasonably spread through the module, not clustered at the end.
- No inline DSL exercise blocks are present (`:::quiz` 0, `:::fill-in` 0), so item-level distractor logic cannot be verified from this prose alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned sections and all 4 activity markers are present, and the planned vocab appears in prose. But section pacing drifts well past the plan budgets: 430/360/336/279 words vs planned 350/300/300/250. |
| 2. Linguistic accuracy | 6/10 | Critical factual error: `фо-то-гра-фі-я... The stress falls on the third **а**.` SУМ-11 gives `ФОТОГРА́ФІЯ`. Another inaccurate rule is `The punctuation tells you exactly which melody to use.` |
| 3. Pedagogical quality | 7/10 | The module has many examples, but it teaches an internally contradictory intonation rule: it distinguishes yes/no vs question-word melody, then says punctuation alone determines melody. |
| 4. Vocabulary coverage | 10/10 | Required vocab is used in prose: `наголос`, both senses of `замок`, `кава`, `вода`, `столиця`; recommended `мука`, `ранок`, `метро`, `фотографія` also appear in context. |
| 5. Exercise quality | 9/10 | All 4 planned markers appear after the relevant teaching. Marker types match the plan; no inline exercise logic problems are visible in the prose provided. |
| 6. Engagement & tone | 8/10 | Mostly teacherly and clear, but `When Ukrainians speak, they use clear, distinct syllables without mumbling` slips into overgeneralization instead of instruction. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly; markdown is clean; pipeline word count is 1361, above target. |
| 8. Cultural accuracy | 8/10 | `When Ukrainians speak, they use clear, distinct syllables without mumbling` essentializes speakers instead of giving neutral pronunciation guidance. |
| 9. Dialogue & conversation quality | 9/10 | Named speakers are used, and the short greeting exchange is natural enough for A1 phonetics practice. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Next, look at the word for photograph: **фо-то-гра-фі-я**. The stress falls on the third **а**. Say it: **фотографія**.`  
Issue: This teaches the wrong stress location. SУМ-11 gives `ФОТОГРА́ФІЯ`, so the stressed syllable is `гра`.  
Fix: Change the explanation to `The stress falls on **гра**.`

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `The punctuation tells you exactly which melody to use.`  
Issue: This contradicts the module’s own explanation. Both yes/no questions and question-word questions use `?`, but the lesson assigns them different melodies.  
Fix: Rephrase this sentence so punctuation marks sentence type, while question melody depends on yes/no vs question-word structure.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: filler-heavy section intros and asides, e.g. `This forms the rhythmic heart of Ukrainian pronunciation.` / `The technique is simple but powerful.` / `Let's recap the core concepts of this module with a comprehensive self-check.`  
Issue: The prose overshoots every section budget from the plan: 430/360/336/279 words vs 350/300/300/250.  
Fix: Trim the introductory filler and summary framing so the sections stay closer to the planned pacing.

[CULTURAL ACCURACY] [SEVERITY: minor]  
Location: `When Ukrainians speak, they use clear, distinct syllables without mumbling.`  
Issue: This is an over-broad cultural claim about speakers rather than a pronunciation instruction.  
Fix: Rephrase it as learner guidance about careful pronunciation practice.

## Verdict: REVISE
REVISE. The module has good coverage and correctly placed exercise markers, but it contains two critical teaching inaccuracies and misses the plan’s section pacing by a clear margin. That fails both the severity gate and the all-dimensions-≥9 gate.

<fixes>
- find: "The concept of **наголос** (stress) is fundamental in Ukrainian. As Заболотний Grade 5, p.73 notes, the Ukrainian language has exactly 38 sounds. When you speak, **наголос** determines which syllable in a word is pronounced louder and longer. This forms the rhythmic heart of Ukrainian pronunciation. Ukrainian stress is **вільний** (free). It can fall on any syllable in a word. It is also **рухомий** (mobile), meaning it shifts between forms of the exact same word. For example, look at the word for leg: **нога** (stress on the last syllable). But when we talk about plural legs, it becomes **ноги** (stress on the first syllable). This system is completely unlike French, where stress is always fixed on the last syllable, or Czech, where it is always on the first. In Ukrainian, the stress dances around."
  replace: "**Наголос** (stress) is fundamental in Ukrainian. As Заболотний Grade 5, p.73 notes, the language has 38 sounds, and stress shows which syllable is louder and longer. Ukrainian stress is **вільний** (free) and **рухомий** (mobile): it can fall on any syllable and shift between forms. For example, **нога** has stress on the last syllable, but **ноги** shifts it to the first. This differs from French, where stress is fixed on the last syllable, and Czech, where it is fixed on the first."
- find: "For A1 learners, focus on identifying the three punctuation patterns that match these melodies. We use a period (.) for statements. We use a question mark (?) for questions. We use an exclamation mark (!) for emotions or commands. The punctuation tells you exactly which melody to use."
  replace: "For A1 learners, focus on the three punctuation patterns: a period (.) for statements, a question mark (?) for questions, and an exclamation mark (!) for emotions or commands. Punctuation shows the sentence type, but for questions you still need to know whether the melody rises (yes/no question) or falls (question word)."
- find: "Next, look at the word for photograph: **фо-то-гра-фі-я**. The stress falls on the third **а**. Say it: **фотографія**."
  replace: "Next, look at the word for photograph: **фо-то-гра-фі-я**. The stress falls on **гра**. Say it: **фотографія**."
- find: "When Ukrainians speak, they use clear, distinct syllables without mumbling. Exaggerating the stressed syllable during your practice will help you achieve this natural, rhythmic sound."
  replace: "In careful pronunciation practice, say each syllable clearly and exaggerate the stressed syllable slightly. This will help you build a more natural Ukrainian rhythm."
- find: "Let's recap the core concepts of this module with a comprehensive self-check. Answering these questions helps solidify your understanding of Ukrainian phonetics."
  replace: "Let us recap the core concepts with a short self-check."
</fixes>