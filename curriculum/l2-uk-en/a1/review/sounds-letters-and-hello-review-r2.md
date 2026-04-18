## Linguistic Scan
No linguistic errors found.

## Exercise Check
6 `INJECT_ACTIVITY` markers are present, which matches the 6 contracted activity obligations. All marker IDs use the correct contracted type prefixes.

Issue found: the marker order does not match `activity_obligations`. The prose order is `quiz -> match-up -> group-sort -> letter-grid -> fill-in -> watch-and-repeat`, but the contract requires `quiz -> match-up -> fill-in -> group-sort -> letter-grid -> watch-and-repeat`.

Because this is a marker-only module, I did not score distractors or answer logic.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All core beats are covered, including `33 letters / 38 sounds`, `[•]`, `[–]`, `[=]`, and the `Привіт` sound analysis. Required vocabulary is present. Deduction: section pacing drifts past the contract budgets; computed from the file body, `Звуки і літери` runs 351 words vs max 330, and `Привіт!` runs 288 vs max 275. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian characters found. The Ukrainian chunks used in dialogue and examples are standard, and the phonetics claims checked align with the contracted school-textbook framing. |
| 3. Pedagogical quality | 9/10 | The module teaches through concrete examples rather than bare lists: `ма-ма`, `мо-ло-ко`, `У-ля`, and `П [п] ... т [т]`. Textbook references to Заболотний, Большакова, and Захарійчук are integrated into the explanations. |
| 4. Vocabulary coverage | 10/10 | All required targets appear in prose: `звук`, `літера`, `голосний`, `приголосний`, `Привіт`, `Як справи`, `Добре`, `Чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 8/10 | Marker count matches the contract and each marker type matches exactly, but the marker order does not: the module places `group-sort` and `letter-grid` before `fill-in`, contrary to the contracted sequence. |
| 6. Engagement & tone | 9/10 | The tone stays clear and teacherly, with concrete attention points like the `Привіт` sound analysis and short classroom exchanges rather than hype or gamified filler. |
| 7. Structural integrity | 10/10 | All five H2 sections are present and in the contracted order. The pipeline word count is 1233, so the module clears the 1200-word target, and the markdown is clean. |
| 8. Cultural accuracy | 10/10 | The module explains Ukrainian on its own terms and avoids Russian-centered framing. Register guidance around `Привіт` and `Добрий день` is culturally appropriate for A1. |
| 9. Dialogue & conversation quality | 9/10 | The required named-speaker dialogue is present: `Марко` and `Софія` exchange names and use the reciprocal `А у тебе?`. The teacher/student exchange also fits the first-classroom scenario. |

## Findings
[Plan adherence] [SEVERITY: major]  
Location: `## Звуки і літери (Sounds and Letters)` / `## Привіт! (Hello!)` — for example, “The most important distinction in Ukrainian phonetics is the difference between a sound and a letter.” and “Following Anna Ohoiko from the Ukrainian Lessons Podcast Episode 1, you can build your first conversation.”  
Issue: Two sections are over their contracted budgets. File-body counts are 351 words for `Звуки і літери` (max 330) and 288 words for `Привіт!` (max 275).  
Fix: Trim redundant explanatory sentences in those two sections without removing any contracted beats or required vocabulary.

[Exercise quality] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->`, `<!-- INJECT_ACTIVITY: letter-grid-alphabet -->`, `<!-- INJECT_ACTIVITY: fill-in-greetings -->`  
Issue: Marker order violates the contracted `activity_obligations`. The third required type is `fill-in`, but the module places `group-sort` and `letter-grid` before it.  
Fix: Move `group-sort` and `letter-grid` so the prose marker sequence becomes `quiz -> match-up -> fill-in -> group-sort -> letter-grid -> watch-and-repeat`.

## Verdict: REVISE
The module is linguistically clean and contract-heavy content is mostly present, but it has two ship-blocking quality issues: section-budget drift and a marker-order mismatch against the contracted activity sequence. With those fixed, it is close to passable.

<fixes>
- find: |
    The most important distinction in Ukrainian phonetics is the difference between a sound and a letter. Teachers in Ukraine drill this fundamental concept into students from the very first grade to ensure complete understanding. The golden rule, established by the linguist **Заболотний** in the standard fifth-grade textbook, is perfectly clear: «**Звуки** ми **чуємо** й **вимовляємо**, а **букви** **бачимо** й **пишемо**». We hear and pronounce **звуки** (sounds), but we see and write **букви** (letters). These are definitely not the same thing. A letter is merely a graphical symbol drawn on paper. A sound is the actual physical noise that your mouth produces when you speak.
  replace: |
    The most important distinction in Ukrainian phonetics is the difference between a sound and a letter. The golden rule from **Заболотний**'s standard fifth-grade textbook is clear: «**Звуки** ми **чуємо** й **вимовляємо**, а **букви** **бачимо** й **пишемо**». We hear and pronounce **звуки** (sounds), but we see and write **букви** (letters). A letter is merely a graphical symbol drawn on paper. A sound is the actual physical noise that your mouth produces when you speak.
- find: |
    The complete collection of these thirty-three letters is called the **абетка** or **алфавіт** (alphabet): А, Б, В, Г, Ґ, Д, Е, Є, Ж, З, И, І, Ї, Й, К, Л, М, Н, О, П, Р, С, Т, У, Ф, Х, Ц, Ч, Ш, Щ, Ь, Ю, Я. Each letter has its own specific name. Unlike English, Ukrainian spelling is highly phonetic. What you see on the page is almost exactly what you hear spoken aloud. There are almost no surprise pronunciations, so once you learn the sounds, you will be able to read new words much more confidently.
  replace: |
    The complete collection of these thirty-three letters is called the **абетка** or **алфавіт** (alphabet): А, Б, В, Г, Ґ, Д, Е, Є, Ж, З, И, І, Ї, Й, К, Л, М, Н, О, П, Р, С, Т, У, Ф, Х, Ц, Ч, Ш, Щ, Ь, Ю, Я. Each letter has its own specific name. Unlike English, Ukrainian spelling is highly phonetic, so what you see on the page is almost exactly what you hear spoken aloud.
- find: |
    The greeting **Добрий день** establishes a polite tone. The students use **Добре** to state they are doing well.
  replace: |
    Here **Добрий день** and **Добре** form a simple classroom exchange.
- find: |
    Following Anna Ohoiko from the Ukrainian Lessons Podcast Episode 1, you can build your first conversation.
  replace: |
    Following Anna Ohoiko's Episode 1, you can build your first conversation.
- find: |
    The greeting **Привіт** is strictly informal. Always default to **Добрий день** when speaking to teachers or strangers.
  replace: |
    The greeting **Привіт** is strictly informal. Use **Добрий день** with teachers or strangers.
- find: |
    The phrase **Як тебе звати?** asks for a name. The reply uses **Мене звати** to answer.
  replace: |
    The pair **Як тебе звати? / Мене звати ...** covers the basic name exchange.
- find: |
    <!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->
    <!-- INJECT_ACTIVITY: letter-grid-alphabet -->
  replace: ""
- find: |
    <!-- INJECT_ACTIVITY: fill-in-greetings -->
    <!-- INJECT_ACTIVITY: watch-and-repeat-ohoiko-videos -->
  replace: |
    <!-- INJECT_ACTIVITY: fill-in-greetings -->
    <!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->
    <!-- INJECT_ACTIVITY: letter-grid-alphabet -->
    <!-- INJECT_ACTIVITY: watch-and-repeat-ohoiko-videos -->
</fixes>