## Linguistic Scan
No linguistic errors found. (Note: stress marks are ignored per instructions).

## Exercise Check
- `count-syllables`: Placed correctly after the Syllables section.
- `match-up`: Placed BEFORE the letter Ї is taught, which is incorrect since it tests iotated vowels.
- `divide-words`: Placed at the end of the Vowels section. It tests word splitting (аптека, молоко, університет), so it belongs in the "Читання слів" section.
- `quiz`: Placed in the middle of "Читання слів". It tests minimal pairs (meaning), so it fits better at the end of the Vowels section where minimal pairs (кит/кіт) are taught.
- `odd-one-out`: Placed correctly at the end of "Читання слів".

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The plan explicitly specifies "ап-те-ка", but the text uses "а-пте-ка". The word count (1778 words) is nearly 50% over the target of 1200. |
| 2. Linguistic accuracy | 8/10 | The syllable division "яб-лу-ко" in the dialogue is phonetically incorrect for Ukrainian (must be "я-блу-ко"). |
| 3. Pedagogical quality | 6/10 | Activity markers are placed before their concepts are fully taught. The syllable splitting of "яблуко" violates Ukrainian Grade 1 rules. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words are included in appropriate contexts. |
| 5. Exercise quality | 9/10 | The injected markers map exactly to the plan's activity hints. |
| 6. Engagement & tone | 9/10 | Tone is grounded and instructional, leveraging Ukrainian textbooks well. |
| 7. Structural integrity | 7/10 | Clean structure, but the word count is significantly over the target limit. |
| 8. Cultural accuracy | 10/10 | Excellent integration of actual Ukrainian textbook concepts and reading methods. |
| 9. Dialogue & conversation quality | 6/10 | Dialogues are purely transactional and interrogative ("Скільки складів у слові...?", "А це?"). |

## Findings

[DIMENSION] 1. Plan adherence [SEVERITY: major]
Location: Section "Склади", "Читання слів" - "а-пте-ка → а... пте... ка → аптека"
Issue: The plan explicitly specifies "ап-те-ка" for syllable division, but the text uses "а-пте-ка".
Fix: Change "а-пте-ка" to "ап-те-ка" to match the plan.

[DIMENSION] 3. Pedagogical quality [SEVERITY: critical]
Location: Section "Читання слів" - "Аня: Яб-лу-ко... яблуко!"
Issue: The syllable division "яб-лу-ко" is phonetically incorrect for Ukrainian (it should be "я-блу-ко" as per open syllable rules taught in Grade 1, e.g., Bolshakova). Teaching the wrong phonetic division is a critical error.
Fix: Change "Яб-лу-ко" to "Я-блу-ко" and rewrite the dialogue.

[DIMENSION] 3. Pedagogical quality [SEVERITY: major]
Location: Section "Голосні літери" - activity markers placement
Issue: `<!-- INJECT_ACTIVITY: match-up -->` is placed BEFORE the letter Ї is taught. `<!-- INJECT_ACTIVITY: divide-words -->` is placed at the end of the Vowels section instead of the Reading Words section.
Fix: Move `match-up` to after the Ї paragraph. Swap the positions of `divide-words` and `quiz`.

[DIMENSION] 9. Dialogue & conversation quality [SEVERITY: major]
Location: Sections "Склади" and "Читання слів"
Issue: The dialogues are purely transactional interrogations where Marko quizzes Anya ("Скільки складів у слові...?", "А це?").
Fix: Rewrite the dialogues to be natural conversations about noticing and reading signs/objects.

## Verdict: REVISE
The module contains a critical phonetic error ("яб-лу-ко"), several major sequencing issues with activity markers, and interrogative dialogues. It must be revised before publishing.

<fixes>
- find: |
    Now **апте́ка** (pharmacy): vowels А, Е, А → three syllables **а-пте-ка** → stress on the second syllable → consonants П, Т, К are hard.

    For reading, apply звуковий аналіз as a practical strategy: (1) spot the vowels, (2) split into syllables, (3) read each syllable aloud slowly, (4) blend the syllables together at natural speed. Try it: **а-пте-ка** → а... пте... ка → **аптека**. Done.
  replace: |
    Now **апте́ка** (pharmacy): vowels А, Е, А → three syllables **ап-те-ка** → stress on the second syllable → consonants П, Т, К are hard.

    For reading, apply звуковий аналіз as a practical strategy: (1) spot the vowels, (2) split into syllables, (3) read each syllable aloud slowly, (4) blend the syllables together at natural speed. Try it: **ап-те-ка** → ап... те... ка → **аптека**. Done.
- find: |
    **а-пте-ка** → **аптека** (pharmacy). **мо-ло-ко** → **молоко** (milk).
  replace: |
    **ап-те-ка** → **аптека** (pharmacy). **мо-ло-ко** → **молоко** (milk).
- find: |
    Look at **люди́на** (person): Л is softened by Ю. In **вечі́рнє** (evening, neuter adjective), Н is softened by Є.

    <!-- INJECT_ACTIVITY: match-up -->

    **Ї** stands apart.
  replace: |
    Look at **люди́на** (person): Л is softened by Ю. In **вечі́рнє** (evening, neuter adjective), Н is softened by Є.

    **Ї** stands apart.
- find: |
    **Ї** is distinctly Ukrainian — Russian has no equivalent letter.

    Now, the critical minimal pairs: **И** vs **І**.
  replace: |
    **Ї** is distinctly Ukrainian — Russian has no equivalent letter.

    <!-- INJECT_ACTIVITY: match-up -->

    Now, the critical minimal pairs: **И** vs **І**.
- find: |
    Listen carefully to model pronunciations and practice hearing the contrast before you drill.

    <!-- INJECT_ACTIVITY: divide-words -->

    ## Чита́ння слів (Reading Words)
  replace: |
    Listen carefully to model pronunciations and practice hearing the contrast before you drill.

    <!-- INJECT_ACTIVITY: quiz -->

    ## Чита́ння слів (Reading Words)
- find: |
    Most Ukrainian syllables are open — ending in a vowel — which makes blending easier than you might expect.

    <!-- INJECT_ACTIVITY: quiz -->

    Time to read.
  replace: |
    Most Ukrainian syllables are open — ending in a vowel — which makes blending easier than you might expect.

    Time to read.
- find: |
    These look intimidating, but the vowel-counting method handles them completely. Finish with Ukrainian city names as a confidence-builder: **Ки-їв** (Kyiv — note the Ї), **О-де-са** (Odesa), **Хар-ків** (Kharkiv), **Дні-про** (Dnipro), **Пол-та-ва** (Poltava).

    Three special combinations appear in Ukrainian words
  replace: |
    These look intimidating, but the vowel-counting method handles them completely. Finish with Ukrainian city names as a confidence-builder: **Ки-їв** (Kyiv — note the Ї), **О-де-са** (Odesa), **Хар-ків** (Kharkiv), **Дні-про** (Dnipro), **Пол-та-ва** (Poltava).

    <!-- INJECT_ACTIVITY: divide-words -->

    Three special combinations appear in Ukrainian words
- find: |
    > **Марко́:** Скільки складів у слові "молоко"? *(How many syllables in the word "moloko"?)*
    > **Аня:** Три голосні́ — О, О, О. О́тже, три склади: мо-ло-ко! *(Three vowels — O, O, O. So, three syllables: mo-lo-ko!)*
    > **Марко:** Пра́вильно! А "банк"? *(Correct! And "bank"?)*
    > **Аня:** Ті́льки оди́н! *(Only one!)*
  replace: |
    > **Марко́:** Дивись, на пакеті написано: мо-ло-ко. Три склади. *(Look, on the carton it says: mo-lo-ko. Three syllables.)*
    > **Аня:** Так, бо там три голосні́ — О, О, О. *(Yes, because there are three vowels — O, O, O.)*
    > **Марко:** А ось тут написано "банк". *(And right here it says "bank".)*
    > **Аня:** Ті́льки одна голосна. Оди́н склад! *(Only one vowel. One syllable!)*
- find: |
    > **Аня:** Бі-блі-о-те-ка... **бібліотека**! *(Library!)*
    > **Марко:** Так! А це? *(Yes! And this?)*
    > **Аня:** Яб-лу-ко... **яблуко**! *(Apple!)*
    > **Марко:** А це — **шоколад**! *(And this is chocolate!)*

    Аня uses the syllable method — splitting each word, then blending. Марко confirms and adds a new word. This is exactly how the method works in practice: slow and careful at first, then faster with each repetition.
  replace: |
    > **Аня:** Дивись на вивіску: бі-блі-о-те-ка... **бібліотека**! *(Look at the sign: bi-bli-o-te-ka... library!)*
    > **Марко:** Ага! А поруч супермаркет. Там є я-блу-ко... **яблуко**! *(Aha! And nearby is a supermarket. There is an apple!)*
    > **Аня:** А я хочу **шоколад**! Шо-ко-лад. *(And I want chocolate! Sho-ko-lad.)*

    Аня and Марко use the syllable method — splitting each word, then blending. This is exactly how the method works in practice: slow and careful at first, then faster with each repetition.
</fixes>
