## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian-only characters (`ы`, `э`, `ё`, `ъ`) found.

Factual error found:
- `The letter Ґ with its little upturned tail is uniquely Ukrainian...` is inaccurate. Ґ is also used outside Ukrainian, including in Rusyn / Pannonian Rusyn sources ([Wiktionary](https://en.wiktionary.org/wiki/%D2%91), [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:%D2%90)).

## Exercise Check
All 6 planned activity markers are present: `letter-grid`, `quiz-sounds-vs-letters`, `group-sort-vowels-consonants`, `match-up-letters-to-sounds`, `watch-and-repeat-alphabet`, `fill-in-greeting`.

Placement is mostly correct: markers come after the relevant teaching sections, the set matches the plan’s 6 `activity_hints`, and the markers are distributed through the module rather than dumped at the end. No exercise-logic errors are visible from the markers themselves.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned H2 sections are present and the textbook references are integrated, but the summary says `The numbers differ because iotated letters... while the soft sign (Ь) makes absolutely no sound at all` and omits hard/soft pairs from the plan’s explanation of `33 літери, 38 звуків`. Section pacing is also far over the plan budgets: `Звуки і літери` ~562 words vs 300 planned, `Голосні звуки` ~424 vs 250, `Приголосні звуки` ~456 vs 250. |
| 2. Linguistic accuracy | 8/10 | No Russianisms/Surzhyk found, but `The letter Ґ with its little upturned tail is uniquely Ukrainian` is a factual error. |
| 3. Pedagogical quality | 7/10 | The module has examples and practice, but several sections open with long English-first exposition before learner-facing examples, e.g. `When you listen to someone speaking Ukrainian...` and `With the difference between a letter and a sound established...`, which weakens PPP flow for A1. |
| 4. Vocabulary coverage | 9/10 | All required plan vocabulary appears naturally in prose: `звук`, `літера`, `голосний`, `приголосний`, `привіт`, `як справи`, `добре`, `чудово`, `мама`, `молоко`. Recommended items are also used beyond the minimum. |
| 5. Exercise quality | 10/10 | All 6 planned activity types are represented by markers, and each marker follows the concept it is meant to practice. |
| 6. Engagement & tone | 9/10 | The teacher voice is energetic and concrete, especially in the dialogues and sound-analysis section, without gamified/corporate filler. |
| 7. Structural integrity | 10/10 | All planned headings are present and ordered correctly, markers are intact, and the deterministic word count is above target (`2096`). |
| 8. Cultural accuracy | 8/10 | The module treats Ukrainian on its own terms, but the claim that Ґ is `uniquely Ukrainian` is culturally/factually inaccurate. |
| 9. Dialogue & conversation quality | 9/10 | The module includes named, multi-turn dialogues in plausible beginner contexts: classroom greeting and hallway introduction. |

## Findings
[DIMENSION 2/8] [SEVERITY: critical]  
Location: `The letter Ґ with its little upturned tail is uniquely Ukrainian and represents a hard "g" sound.`  
Issue: `uniquely Ukrainian` is factually wrong. Ґ is not exclusive to Ukrainian.  
Fix: Change `uniquely Ukrainian` to a narrower accurate description such as `a distinctive letter in the Ukrainian alphabet`.

[DIMENSION 1] [SEVERITY: major]  
Location: `Why are the numbers different? The numbers differ because iotated letters (Я, Ю, Є, Ї) can make two distinct sounds, while the soft sign (Ь) makes absolutely no sound at all.`  
Issue: The summary omits hard/soft consonant pairs, which the plan explicitly includes in the explanation of why Ukrainian has 38 sounds but 33 letters.  
Fix: Add hard/soft pairs to this summary sentence.

[DIMENSION 1/3] [SEVERITY: major]  
Location: `When you listen to someone speaking Ukrainian...`, `With the difference between a letter and a sound established...`, and `The second family of sounds in the Ukrainian language...`  
Issue: The module overshoots the section budgets badly and spends too long in English-theory exposition before moving to concrete beginner examples and practice.  
Fix: Compress these opening paragraphs and move the learner-facing takeaway/examples earlier.

## Verdict: REVISE
REVISE. There is one critical factual error (`ґ` described as uniquely Ukrainian) and two major quality issues (incomplete plan-point summary and overlong theory-heavy openings). That fails the severity gate and leaves multiple dimensions below 9.

<fixes>
- find: "The letter Ґ with its little upturned tail is uniquely Ukrainian and represents a hard \"g\" sound."
  replace: "The letter Ґ with its little upturned tail is a distinctive letter in the Ukrainian alphabet and represents a hard \"g\" sound."

- find: "Why are the numbers different? The numbers differ because iotated letters (Я, Ю, Є, Ї) can make two distinct sounds, while the soft sign (Ь) makes absolutely no sound at all."
  replace: "Why are the numbers different? The numbers differ because iotated letters (Я, Ю, Є, Ї) can make two distinct sounds, many consonants come in hard and soft pairs, and the soft sign (Ь) makes absolutely no sound at all."

- find: |
    When you listen to someone speaking Ukrainian, what you are actually hearing is a series of sounds. When you read a Ukrainian book or a text message, what you are looking at is a series of letters. This might seem like an obvious statement, but confusing these two concepts is a frequent mistake. There is a golden rule taught to every Ukrainian student in the fifth grade. As the textbook by Заболотний (Grade 5, page 83) states: "Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо." This means we hear and pronounce a **звук** (sound), but we see and write a **літера** (letter). A letter is nothing more than a symbol on a piece of paper or a screen. A sound is the physical vibration your mouth and vocal cords produce. They are not the same thing. This distinction is the absolute foundation of Ukrainian phonetics. Ukrainian teachers drill this concept from the very first day of first grade because everything else in the language builds upon it. You cannot truly understand how Ukrainian works until you stop looking at words as just collections of letters and start hearing them as sequences of sounds.
  replace: |
    In Ukrainian, sounds and letters are different things. As the textbook by Заболотний (Grade 5, page 83) states: "Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо." We hear and pronounce a **звук** (sound), but we see and write a **літера** (letter). A letter is a written symbol. A sound is what you actually hear and say. This distinction matters immediately, because reading, spelling, and sound analysis all depend on separating what is written from what is pronounced.

- find: |
    With the difference between a letter and a sound established, the focus shifts to the two main families of sounds. The first family is the **голосний** (vowel sound). A vowel sound is created using only your voice. When you pronounce a vowel, the air flows completely freely from your lungs, through your throat, and out of your mouth with absolutely no obstruction from your lips, teeth, or tongue. Because nothing blocks the air, vowels are the musical core of the language. As the textbook by Большакова (Grade 1, page 24) teaches children through a poem: "Голосні почуєш в пісні, і у темному у лісі... Легко вимовляються, весело співаються!" (You will hear vowels in a song, and in a dark forest... They are easily pronounced, cheerfully sung!). You can sing a vowel sound. You can hold it for as long as you have breath. You can shout a vowel across a wide field to get someone's attention. Without vowels, human speech would just be a series of clicks, hisses, and pops.
  replace: |
    The first family is the **голосний** (vowel sound). A vowel is made with voice and free airflow, so you can stretch it and sing it. As the textbook by Большакова (Grade 1, page 24) teaches: "Голосні почуєш в пісні..." That is the key beginner test: if you can hold the sound, you are dealing with a vowel. In the examples below, you will hear this clearly in **мама**, **молоко**, and **Уля**.

- find: |
    The second family of sounds in the Ukrainian language is the **приголосний** (consonant sound). The word itself translates to "with a vowel," showing that these sounds are designed to attach themselves to vowels to build syllables. While vowels are made of pure voice, a consonant sound is made with voice plus noise, or sometimes with just noise alone. This noise happens because your mouth creates an obstruction. Your lips might close together, your tongue might tap the roof of your mouth, or your teeth might block the airflow. The textbook by Большакова (Grade 1, page 24) explains this beautifully: "Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять" (Consonants rattle and quietly rustle, loudly whistle and hiss). To prove this, try singing a pure consonant. Take the sound [к] or the sound [п] and try to hold a musical note with it. It is physically impossible. Consonants provide the structure and the hard edges of a word, while vowels provide the volume and the melody.
  replace: |
    The second family is the **приголосний** (consonant sound). A consonant is made with noise, or with voice plus noise, because the lips, tongue, or teeth interrupt the airflow. The textbook by Большакова (Grade 1, page 24) captures this well: "Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять." A simple beginner test is that you cannot sing [к] or [п] the way you can sing [а]. Consonants give words their structure; vowels give them voice.
</fixes>