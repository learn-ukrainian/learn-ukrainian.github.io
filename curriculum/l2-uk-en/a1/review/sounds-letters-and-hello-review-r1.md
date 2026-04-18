## Linguistic Scan
No linguistic errors found.

## Exercise Check
Six markers are present: `quiz-sounds-vs-letters`, `match-up-letters-sounds`, `fill-in-greetings`, `group-sort-vowels-consonants`, `letter-grid-alphabet`, `watch-and-repeat-ohoiko-videos`.

Marker count and overall contracted type order are correct: `quiz` → `match-up` → `fill-in` → `group-sort` → `letter-grid` → `watch-and-repeat`.

One placement issue: `<!-- INJECT_ACTIVITY: fill-in-greetings -->` appears after the consonant section at [sounds-letters-and-hello.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/sounds-letters-and-hello.md:42), before `## Привіт! (Hello!)` starts at [sounds-letters-and-hello.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/sounds-letters-and-hello.md:46). It tests greeting material before that material is taught.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All five contracted H2 sections are present and ordered, and the pipeline word count is 1223. But the section-1 contract explicitly requires “all 33 letters in order” at [contract.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/orchestration/sounds-letters-and-hello/contract.yaml:33), while the prose at [sounds-letters-and-hello.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/sounds-letters-and-hello.md:11) names the alphabet without actually listing the 33-letter sequence. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, bad case/gender forms, or banned Russian letters were found in the Ukrainian text. Core forms such as `Рада`, `радий`, `нормально`, and `привіт` are standard Ukrainian forms. |
| 3. Pedagogical quality | 7/10 | The module has solid textbook anchoring and concrete examples: `ма-ма`, `мо-ло-ко`, `У-ля`, and the `Привіт` sound analysis at [sounds-letters-and-hello.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/sounds-letters-and-hello.md:22) and [sounds-letters-and-hello.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/sounds-letters-and-hello.md:68). But learners are not shown the full alphabet sequence in the alphabet section, and the greetings fill-in is placed before the greetings lesson. |
| 4. Vocabulary coverage | 9/10 | Required target vocabulary appears naturally in context: `звук`, `літера`, `голосні`, `приголосні`, `Привіт`, `Як справи?`, `Добре`, `Чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 6/10 | This is a marker-only module, so marker count/order/type are the relevant checks, and those mostly pass. The major failure is placement: `fill-in-greetings` is at [sounds-letters-and-hello.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/sounds-letters-and-hello.md:42), before the greeting content begins at line 46. |
| 6. Engagement & tone | 8/10 | The tone is clear and teacherly, and the module uses concrete classroom content rather than empty hype. The dialogues and sound examples keep it grounded. |
| 7. Structural integrity | 10/10 | Clean markdown, all H2 headings present once, correct section order, and pipeline word count is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms, uses Ukrainian textbook pedagogy, and avoids Russian-centered framing. |
| 9. Dialogue & conversation quality | 9/10 | The module includes named-speaker dialogue (`Марко`, `Софія`) and uses the required reciprocal `А у тебе?`, with correct `Рада/Радий` contrast. |

## Findings
[DIMENSION 1] [SEVERITY: major]  
Location: [sounds-letters-and-hello.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/sounds-letters-and-hello.md:11) — “The complete collection of these thirty-three letters is called the **абетка** or **алфавіт** (alphabet). Each individual letter has its own specific name.”  
Issue: The contract requires this teaching beat to show “all 33 letters in order” ([contract.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/orchestration/sounds-letters-and-hello/contract.yaml:33)), but the prose never actually gives the alphabet sequence.  
Fix: Replace this paragraph with a concise version that includes the 33 letters in order.

[DIMENSION 5] [SEVERITY: major]  
Location: [sounds-letters-and-hello.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/sounds-letters-and-hello.md:42) — `<!-- INJECT_ACTIVITY: fill-in-greetings -->`  
Issue: The greetings fill-in marker appears before `## Привіт! (Hello!)`, so it tests `Привіт`, `Як справи?`, `Добре`, `Чудово`, and `А у тебе?` before those chunks are taught.  
Fix: Move `<!-- INJECT_ACTIVITY: fill-in-greetings -->` to the end of the `## Привіт! (Hello!)` section, before the watch-and-repeat marker.

## Verdict: REVISE
The module is structurally sound and linguistically clean, but it has two concrete contract failures: the alphabet section omits the required 33-letter sequence, and the greetings fill-in marker is placed before the greetings lesson. Those issues require fixes, so this cannot pass.

<fixes>
- find: "The complete collection of these thirty-three letters is called the **абетка** or **алфавіт** (alphabet). Each individual letter has its own specific name. Unlike English, Ukrainian spelling is highly phonetic. What you see on the page is almost exactly what you hear spoken aloud. There are no hidden silent letters to trip you up, except for the functional soft sign mentioned earlier, and no surprise pronunciations. Because the writing system is incredibly consistent, once you learn the sounds, you will be able to accurately read any word you encounter."
  replace: "The complete collection of these thirty-three letters is called the **абетка** or **алфавіт** (alphabet): А, Б, В, Г, Ґ, Д, Е, Є, Ж, З, И, І, Ї, Й, К, Л, М, Н, О, П, Р, С, Т, У, Ф, Х, Ц, Ч, Ш, Щ, Ь, Ю, Я. Each letter has its own specific name. Unlike English, Ukrainian spelling is highly phonetic. What you see on the page is almost exactly what you hear spoken aloud. There are almost no surprise pronunciations, so once you learn the sounds, you will be able to read new words much more confidently."
- find: "<!-- INJECT_ACTIVITY: fill-in-greetings -->\n<!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->\n<!-- INJECT_ACTIVITY: letter-grid-alphabet -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->\n<!-- INJECT_ACTIVITY: letter-grid-alphabet -->"
- find: "Every type of sound you learned in this module appears in this one word.\n\n<!-- INJECT_ACTIVITY: watch-and-repeat-ohoiko-videos -->"
  replace: "Every type of sound you learned in this module appears in this one word.\n\n<!-- INJECT_ACTIVITY: fill-in-greetings -->\n<!-- INJECT_ACTIVITY: watch-and-repeat-ohoiko-videos -->"
</fixes>