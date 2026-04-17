## Linguistic Scan
No linguistic errors found.

## Exercise Check
6 `INJECT_ACTIVITY` markers are present: `quiz`, `match-up`, `fill-in`, `group-sort`, `letter-grid`, `watch-and-repeat`. For this marker-only module, count, order, and type all match the contracted `activity_obligations`. No inline DSL exercises to review.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Section structure and budgets are strong: `309 / 253 / 254 / 278 / 157` words, all within the allowed tolerance. But the explicit `33 letters / 38 sounds` explanation says only `Я, Ю, Є, and Ї... can represent two distinct sounds` plus `The soft sign (Ь) is completely silent`, omitting hard/soft consonant pairs from that mismatch explanation. The hallway dialogue also uses `А як тебе звати?` instead of the contract’s required reciprocal chunk `А у тебе?`. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, or paronym errors found. Verified Ukrainian forms such as `привіт`, `рада`, `радий`, `бачити`, `деренчать`, `шелестять`, `чудово`, and `нормально` all exist in VESUM, and the text contains none of `ы э ё ъ`. |
| 3. Pedagogical quality | 8/10 | The sound-vs-letter distinction and the `привіт` sound analysis are well scaffolded. But the vowel-practice beat replaces the contracted progression `мА-мА / мО-лО-кО / У-ля` with `мама / молоко / ніс / сон`, so the planned one-sound `[у]` example is dropped. |
| 4. Vocabulary coverage | 10/10 | All required target items appear naturally in prose: `звук`, `літера`, `голосний`, `приголосний`, `привіт`, `як справи`, `добре`, `чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 10/10 | Marker-only module. Marker count matches the 6 contracted activities, order matches the contracted order, and each marker type matches exactly. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and mostly substantive, with concrete classroom framing like `Consider a short classroom exchange` and a usable sound analysis of `привіт`. |
| 7. Structural integrity | 10/10 | All five H2 headings are present and correctly ordered. Pipeline word count is `1236`, so the module clears the target. No duplicate sections or stray formatting artifacts beyond expected admonitions and activity markers. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms, uses Ukrainian pedagogical references, and avoids Russian-centered comparisons. |
| 9. Dialogue & conversation quality | 8/10 | The module includes named speakers and a multi-turn exchange, but the required reciprocal introduction chunk is not realized: the dialogue uses `А як тебе звати?` instead of `А у тебе?` in the name-exchange pattern. |

## Findings
[Plan adherence] [SEVERITY: major]  
Location: `Why is there a mismatch? Some specific letters, such as Я, Ю, Є, and Ї, have special roles and can represent two distinct sounds at once. Furthermore, one letter makes no sound at all.` and `Why is there a difference? Some letters, like **ї**, represent two sounds, while the soft sign (**ь**) represents no sound at all.`  
Issue: The module’s explicit explanation for `38 sounds > 33 letters` omits hard/soft consonant pairs, which are part of the contracted explanation for the mismatch.  
Fix: Add one sentence in the main explanation and one sentence in the summary noting that hard and soft consonant pairs also increase the number of sounds beyond the number of letters.

[Plan adherence / Pedagogical quality] [SEVERITY: major]  
Location: `For example, the word **мама** (mother) contains two [а] sounds. The word **молоко** (milk) contains three distinct [о] sounds. The word **ніс** (nose) has one [і], and **сон** (dream) has one [о].`  
Issue: The contracted vowel-hearing practice calls for `мама`, `молоко`, and `У-ля`; the module drops the planned `[у]` example and substitutes unrelated words.  
Fix: Replace the `ніс / сон` sentence with the contracted `[у]` example using `Уля`.

[Plan adherence / Dialogue & conversation quality] [SEVERITY: major]  
Location: `> **Софія:** Мене звати Софія. А як тебе звати? *(My name is Sofia. And what is your name?)*`  
Issue: The contract requires the named-speaker introduction dialogue to use the reciprocal chunk `А у тебе?`; this line repeats the full question instead.  
Fix: Change Sofia’s line to `Мене звати Софія. А у тебе? *(My name is Sofia. And you?)*`.

## Verdict: REVISE
The module is structurally strong and linguistically clean, but it has contract-level misses in plan adherence and dialogue realization. Because there are identified errors and dimensions below 9, this cannot pass as-is.

<fixes>
- find: |-
    The Ukrainian alphabet (**абетка** or алфавіт) contains exactly thirty-three letters, yet the spoken language produces thirty-eight different sounds. Why is there a mismatch? Some specific letters, such as Я, Ю, Є, and Ї, have special roles and can represent two distinct sounds at once. Furthermore, one letter makes no sound at all. The soft sign (Ь) is completely silent; it is only there to soften the preceding consonant. Because of this, the textbook by Litvinova for Grade 5 (page 130) asks a very important question: «Чи можна говорити "голосна літера"?» The answer is strictly no. Sounds are vowels or consonants, not letters. Letters only graphically represent the sounds.
  replace: |-
    The Ukrainian alphabet (**абетка** or алфавіт) contains exactly thirty-three letters, yet the spoken language produces thirty-eight different sounds. Why is there a mismatch? Some specific letters, such as Я, Ю, Є, and Ї, have special roles and can represent two distinct sounds at once. Hard and soft consonant pairs also increase the number of sounds beyond the number of letters. Furthermore, one letter makes no sound at all. The soft sign (Ь) is completely silent; it is only there to soften the preceding consonant. Because of this, the textbook by Litvinova for Grade 5 (page 130) asks a very important question: «Чи можна говорити "голосна літера"?» The answer is strictly no. Sounds are vowels or consonants, not letters. Letters only graphically represent the sounds.
- find: |-
    Ukrainian primary schools use a specific visual notation for sound models. Vowel sounds are always marked with a solid circle [•]. Let us practice hearing these vowels in simple words. For example, the word **мама** (mother) contains two [а] sounds. The word **молоко** (milk) contains three distinct [о] sounds. The word **ніс** (nose) has one [і], and **сон** (dream) has one [о]. To master these, watch the Anna Ohoiko pronunciation videos. Observe her mouth shape, listen to the native pronunciation, and repeat each vowel sound aloud to build muscle memory.
  replace: |-
    Ukrainian primary schools use a specific visual notation for sound models. Vowel sounds are always marked with a solid circle [•]. Let us practice hearing these vowels in simple words. For example, the word **мама** (mother) contains two [а] sounds. The word **молоко** (milk) contains three distinct [о] sounds. The name **Уля** contains one [у] sound. To master these, watch the Anna Ohoiko pronunciation videos. Observe her mouth shape, listen to the native pronunciation, and repeat each vowel sound aloud to build muscle memory.
- find: |-
    > **Софія:** Мене звати Софія. А як тебе звати? *(My name is Sofia. And what is your name?)*
  replace: |-
    > **Софія:** Мене звати Софія. А у тебе? *(My name is Sofia. And you?)*
- find: |-
    Test your understanding of the phonetic foundation and initial greetings with these self-check questions. How many letters make up the Ukrainian alphabet? There are thirty-three letters. However, how many sounds exist in the language? Ukrainian features thirty-eight distinct sounds. Why is there a difference? Some letters, like **ї**, represent two sounds, while the soft sign (**ь**) represents no sound at all.
  replace: |-
    Test your understanding of the phonetic foundation and initial greetings with these self-check questions. How many letters make up the Ukrainian alphabet? There are thirty-three letters. However, how many sounds exist in the language? Ukrainian features thirty-eight distinct sounds. Why is there a difference? Some letters, like **ї**, represent two sounds, hard and soft consonant pairs increase the number of sounds, while the soft sign (**ь**) represents no sound at all.
</fixes>