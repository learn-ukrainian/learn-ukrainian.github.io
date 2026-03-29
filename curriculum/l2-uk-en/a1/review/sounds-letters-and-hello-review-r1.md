## Linguistic Scan
- Found a **CRITICAL ERROR**: "Привіт, Оля!" incorrectly uses the nominative case instead of the proper vocative "Олю!". Teaching incorrect greeting grammar in the very first lesson is unacceptable.
- The text quotes an expanded version of a textbook poem containing the word "точуть" (e.g., "і гарчать, і точуть"). "Точуть" is a non-standard verb form (not found in VESUM) that appears in the textbook purely for rhyming purposes. The curriculum plan specifically provided a sanitized, grammatically correct version of the quote ("голосно свистять і шиплять") to avoid teaching A1 learners incorrect forms.

## Exercise Check
- The `match-up` activity from the plan is missing entirely.
- The `quiz-sounds-vs-letters` marker is misplaced. It tests content from Section 1 but is clustered at the very end of the module in Section 4.
- `match-false-friends` is hallucinated (it does not exist in the plan).
- `group-sort` is duplicated (appears after Section 2 and Section 3). Since it requires sorting into BOTH vowels and consonants, it should only appear once, after Section 3.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed the requirement to include Захарійчук's vowel notation `[•]`. Expanded the Большакова quote beyond the plan's boundaries. Missed recommended vocabulary "тато" and "сон". |
| 2. Linguistic accuracy | 8/10 | CRITICAL: "Привіт, Оля!" uses nominative instead of vocative. CRITICAL: Included the non-standard word "точуть" in the poem quote. |
| 3. Pedagogical quality | 10/10 | Excellent breakdown of the difference between sounds and letters. |
| 4. Vocabulary coverage | 9/10 | Used all required vocabulary naturally, but missed 2 recommended words. |
| 5. Exercise quality | 6/10 | Missing marker (`match-up`), hallucinated marker (`match-false-friends`), duplicated marker (`group-sort`), and poor placement (`quiz` at the very end). |
| 6. Engagement & tone | 10/10 | Very natural, warm, and clear tone. Does not rely on generic hype. |
| 7. Structural integrity | 10/10 | Clean formatting, headings match the plan, word count is excellent. |
| 8. Cultural accuracy | 10/10 | References Ukrainian textbooks perfectly, capturing the authentic way the language is taught to native speakers. |
| 9. Dialogue & conversation quality | 8/10 | Natural phrasing, but compromised by the vocative case error. |

## Findings
[1. Plan adherence] [MAJOR]
Location: Section "Голосні звуки (Vowel Sounds)", third paragraph ("Hear vowels in real words...")
Issue: Completely missed the plan's requirement to include the Захарійчук Grade 1 p.13 notation for vowel sounds (`[•]`). Also missed the recommended vocabulary words "тато" and "сон".
Fix: Add the Захарійчук `[•]` notation and the missing vocabulary to the examples paragraph.

[2. Linguistic accuracy] [CRITICAL]
Location: Section "Привіт! (Hello!)", dialogue block
Issue: "Привіт, Оля!" incorrectly uses the nominative case for direct address instead of the proper vocative "Олю!". 
Fix: Change "Оля!" to "Олю!".

[2. Linguistic accuracy] [CRITICAL]
Location: Section "Приголосні звуки (Consonant Sounds)", first paragraph
Issue: The writer ignored the plan's sanitized quote and expanded the Большакова poem to include "і точуть". This is a non-standard verb form (fails VESUM) used by the textbook author for rhyme. Teaching it to A1 learners is harmful.
Fix: Revert the quote and its English translation strictly to the safe version provided in the plan ("...голосно свистять і шиплять").

[5. Exercise quality] [MAJOR]
Location: Throughout the module
Issue: Activity markers are chaotic. `match-up` is missing. `quiz-sounds-vs-letters` is delayed until Section 4 instead of following Section 1. `group-sort` is prematurely placed in Section 2. `match-false-friends` is hallucinated.
Fix: Rearrange and consolidate markers: move `quiz` and `match-up` after Section 1, remove the premature `group-sort` from Section 2, and clean up the hallucinated markers from Section 4.

## Verdict: REVISE
The module has excellent tone and pedagogy, but suffers from two critical linguistic errors (ignoring the vocative case and introducing a non-standard verb form against the plan's explicit instructions) and messy activity markers. The deterministic fixes below resolve these issues.

<fixes>
- find: |
    Hear vowels in real words. **мАмА** — two [а] sounds. **мОлОкО** (milk) — three [о] sounds (from Большакова, p. 24). **око** (eye) — two [о] sounds. **дім** (house) — one [і] sound. **ніс** (nose) — one [і] sound. Every syllable in Ukrainian contains exactly one голосний звук.
  replace: |
    Hear vowels in real words. Захарійчук (Grade 1, p. 13) teaches a notation for sound models: vowel sounds are marked with a dot [•]. **мАмА** — two [а] sounds (two dots). **мОлОкО** (milk) — three [о] sounds (from Большакова, p. 24). **око** (eye) — two [о] sounds. **дім** (house) — one [і] sound. **ніс** (nose) — one [і] sound. **тато** (father) — two vowel sounds. **сон** (dream) — one vowel sound. Every syllable in Ukrainian contains exactly one голосний звук.
- find: |
    "Приголосні деренчать і тихенько шелестять, голосно свистять, скриплять, і гарчать, і точуть, співати не хочуть." — "Consonants rattle and quietly rustle, whistle loudly, screech, growl, and grind — they don't want to sing!"
  replace: |
    "Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять." — "Consonants rattle and quietly rustle, whistle loudly and hiss."
- find: |
    <div class="dialogue-line"><span class="speaker">Тарас:</span> Привіт, Оля! *(Hi, Olya!)*</div>
  replace: |
    <div class="dialogue-line"><span class="speaker">Тарас:</span> Привіт, Олю! *(Hi, Olya!)*</div>
- find: |
    <!-- INJECT_ACTIVITY: letter-grid -->

    ## Голосні звуки (Vowel Sounds)
  replace: |
    <!-- INJECT_ACTIVITY: letter-grid -->

    <!-- INJECT_ACTIVITY: quiz -->

    <!-- INJECT_ACTIVITY: match-up -->

    ## Голосні звуки (Vowel Sounds)
- find: |
    <!-- INJECT_ACTIVITY: watch-and-repeat -->

    <!-- INJECT_ACTIVITY: group-sort -->

    ## Приголосні звуки (Consonant Sounds)
  replace: |
    <!-- INJECT_ACTIVITY: watch-and-repeat -->

    ## Приголосні звуки (Consonant Sounds)
- find: |
    <!-- INJECT_ACTIVITY: fill-in -->

    <!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

    <!-- INJECT_ACTIVITY: match-false-friends -->

    ## Підсумок (Summary)
  replace: |
    <!-- INJECT_ACTIVITY: fill-in -->

    ## Підсумок (Summary)
</fixes>
