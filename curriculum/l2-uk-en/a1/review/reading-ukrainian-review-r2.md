## Linguistic Scan
No linguistic errors found.

## Exercise Check
- All 5 planned markers are present in the module and are placed after relevant teaching sections: `count-syllables`, `match-up`, `odd-one-out`, `divide-words`, `quiz`.
- Marker spread is good across the lesson rather than clustered at the end.
- The publish-time exercise layer is broken: `activities/reading-ukrainian.yaml` has no matching IDs for `count-syllables`, `odd-one-out`, or `divide-words`; it uses `syllable-sort`, `tf-reading-rules`, and `divide-words-workbook` instead.
- The planned `odd-one-out` exercise type is missing from the YAML entirely.
- Both quiz blocks are pattern-guessable: `quiz` uses `correct: 0` for all 8 items, and `quiz-sounds` uses `correct: 0` for all 6 items.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Core plan points are covered and references are integrated, but section pacing is far off the plan budgets: `## Склади` is 412 words vs 250 planned, `## Голосні літери` 401 vs 300, `## Читання слів` 591 vs 500. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, surzhyk, calques, paronym misuse, bad case/gender forms, or factual phonetics errors were found in the module prose. |
| 3. Pedagogical quality | 7/10 | The decoding sequence is sound in `find the vowels: **И** and **А** ... **кни-га**`, but the lesson is very English-heavy and practice stays thin relative to the amount of explanation. |
| 4. Vocabulary coverage | 8/10 | All required/recommended vocab appears, but several items occur only as segmented decoding strings: `**лю-ди-на**, **ву-ли-ця**, **шо-ко-лад**, **фо-то-гра-фі-я**`, not as normal contextualized words. |
| 5. Exercise quality | 3/10 | Prose markers exist, but `activities/reading-ukrainian.yaml` lacks IDs for `count-syllables`, `odd-one-out`, and `divide-words`; the planned `odd-one-out` activity is missing; both quizzes put every correct answer at index 0. |
| 6. Engagement & tone | 7/10 | The voice is mostly teacherly, but lines like `The beauty of these simple vowels` and `massive, long words` drift toward generic hype rather than precise teaching. |
| 7. Structural integrity | 8/10 | All H2 headings are present and the pipeline word count is 1386, but the exercise mapping is structurally broken at publish time. |
| 8. Cultural accuracy | 10/10 | Fully Ukrainian-centered; `Київ — столиця України` is correct and there is no Russian-centric framing. |
| 9. Dialogue & conversation quality | 5/10 | `Це **каша** чи **вода**? ... **Вода** ось тут.` and `Я шукаю **бібліотеку**. Де вона? ... **Бібліотека** там.` are named dialogues, but they still read like label drills rather than plausible A1 exchanges. |

## Findings
- [PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Склади`, `## Голосні літери`, `## Читання слів`  
Issue: Section word budgets are off by well over 10%: 412/250, 401/300, 591/500. The module covers the right material, but the pacing is much heavier than the plan specifies.  
Fix: Trim explanatory English and move some practice/examples into exercises or tighter dialogues so the sections land closer to the planned budgets.

- [VOCABULARY COVERAGE] [SEVERITY: major]  
Location: `Читання слів` — `**лю-ди-на** (person), **ву-ли-ця** (street), and **шо-ко-лад** (chocolate)`; `**фо-то-гра-фі-я** (photography)`  
Issue: Several target words are only shown as syllable-divided decoding forms, not as normal unsplit vocabulary in context.  
Fix: Introduce each target word once in standard orthography inside a sentence or dialogue, then show the syllable split.

- [EXERCISE QUALITY] [SEVERITY: major]  
Location: module markers `<!-- INJECT_ACTIVITY: count-syllables -->`, `<!-- INJECT_ACTIVITY: odd-one-out -->`, `<!-- INJECT_ACTIVITY: divide-words -->` versus `activities/reading-ukrainian.yaml`  
Issue: The activity file has no matching IDs for 3 of the 5 markers, so the planned injections will not resolve cleanly at publish time.  
Fix: Regenerate or rewrite `activities/reading-ukrainian.yaml` so its IDs match the module markers and the plan’s hinted exercise types.

- [EXERCISE QUALITY] [SEVERITY: major]  
Location: `activities/reading-ukrainian.yaml` — `quiz` and `quiz-sounds`  
Issue: Every answer key is at position `0`, making both quizzes pattern-guessable instead of diagnostic.  
Fix: Reshuffle options and vary the `correct` indices across items.

- [EXERCISE QUALITY] [SEVERITY: major]  
Location: `activities/reading-ukrainian.yaml`  
Issue: The plan requires an `odd-one-out` exercise, but no `odd-one-out` activity exists in the YAML.  
Fix: Add a real `odd-one-out` block testing syllable count, as specified in `activity_hints`.

- [DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `Читання слів` — `Це **каша** чи **вода**? ... **Вода** ось тут.`; `Я шукаю **бібліотеку**. Де вона? ... **Бібліотека** там.`  
Issue: The dialogues are serviceable but flat, overly echoic, and not anchored in a believable situation.  
Fix: Rewrite them as short real-world A1 exchanges with a clearer setting and at least one response that adds information instead of repeating the noun.

## Verdict: REJECT
No linguistic errors were found in the prose, but the module is not shippable as a full lesson artifact. Three of the five activity markers do not map to real activity IDs, the planned `odd-one-out` exercise is missing, and both quizzes are answer-patterned. Combined with the budget drift and weak contextualization/dialogue work, this needs an exercise-layer rebuild and a tighter prose pass rather than minor patching.