## Linguistic Scan
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Числа 1-20` — “The words **п'ять** and **дев'ять** contain an apostrophe. This symbol acts like a tiny pause.”  
Issue: This teaches the apostrophe incorrectly. Local dictionary verification defines `апостроф` as marking hard pronunciation of the preceding consonant before iotated vowels, not a pause.  
Fix: Replace the explanation with a hard-pronunciation explanation.

## Exercise Check
Markers present in the module: `fill-in-numbers`, `quiz-prices`, `quiz-ages`, `dictation-phone`. These match the four planned `activity_hints`, and the activity YAML supplies 10 / 8 / 6 / 6 items respectively, so coverage is sufficient.

Placement is mostly correct, but `quiz-ages` is misplaced: it appears immediately after the prices block (`<!-- INJECT_ACTIVITY: quiz-prices -->` followed by `<!-- INJECT_ACTIVITY: quiz-ages -->`) instead of after the age teaching in the dialogue section. That weakens the teach-then-practice flow and clusters two markers in one spot.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned H2 sections are present, but the module does not naturally cite the planned ULP references anywhere (`ULP: 0` in module search), and recommended plan vocab `копійка` is absent (`копійка: 0`). |
| 2. Linguistic accuracy | 8/10 | Core Ukrainian forms verify cleanly in VESUM and there are no Russian-only characters, but the phonetics claim “This symbol acts like a tiny pause” is inaccurate for the apostrophe. |
| 3. Pedagogical quality | 7/10 | The module has a usable PPP spine, but `Числа 1-20` shifts into explicit rule-teaching — “We call this the 1, 2-4, 5+ pattern” — even though the plan says to learn these as chunks, not as grammar rules. |
| 4. Vocabulary coverage | 8/10 | Required core vocabulary is covered well, but recommended `копійка` never appears in the prose despite the price section being the obvious place to introduce it. |
| 5. Exercise quality | 8/10 | All four planned marker IDs exist and the activity YAML logic is sound, but `quiz-ages` is placed after the prices teaching rather than after the age teaching it tests. |
| 6. Engagement & tone | 9/10 | The teacher voice is warm and clear, with direct classroom phrasing like “Let us look at...” and practical self-checks at the end. |
| 7. Structural integrity | 10/10 | All required H2 headings are present and ordered correctly, markers are intact, and the pipeline word count is 1361, which is above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module stays Ukrainian-centered: hryvnia, shopping, age, and phone-number contexts are presented on their own terms without Russian-comparison framing. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues use named speakers and realistic everyday purposes; the age dialogue extends beginner conversation patterns effectively. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Числа 1-20` — “Let us start with the core building blocks...” and `Десятки і сотні` — “Let us apply these numbers directly to prices.”  
Issue: The plan cites ULP Season 1, Episode 5 and Episode 9, but the prose never anchors the pronunciation or price sections to those sources.  
Fix: Add one brief source-reference sentence in the 1-10 section and one in the prices section.

[VOCABULARY COVERAGE] [SEVERITY: minor]  
Location: `Десятки і сотні` — “The national currency is the **гривня** (hryvnia).”  
Issue: Recommended vocabulary `копійка` is missing. Module search confirms `копійка: 0`.  
Fix: Introduce `копійка` in the price paragraph alongside `гривня`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Числа 1-20` — “This symbol acts like a tiny pause. It creates a hard consonant separation before the soft vowel sound.”  
Issue: This is a wrong phonetic explanation of the Ukrainian apostrophe.  
Fix: Explain that the apostrophe shows the preceding consonant stays hard before the following vowel; do not describe it as a pause.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Числа 1-20` — “Unlike English, the numbers one and two change based on the gender of the noun they describe...” and “We call this the 1, 2-4, 5+ pattern.”  
Issue: The plan explicitly says these noun changes should be taught as memorized chunks, not as grammar rules. This explanation over-teaches morphology for A1.2.  
Fix: Replace the rule-heavy explanation with ready-made chunks: `один стіл`, `одна книга`, `два роки`, `п'ять років`, etc.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `Десятки і сотні` — `<!-- INJECT_ACTIVITY: quiz-prices -->` followed immediately by `<!-- INJECT_ACTIVITY: quiz-ages -->`  
Issue: The age quiz is not placed after the age teaching in the dialogue section, so practice does not follow the concept it tests.  
Fix: Move `<!-- INJECT_ACTIVITY: quiz-ages -->` to immediately after the age-formula explanation paragraph.

## Verdict: REVISE
REVISE. There is one critical phonetics error, plus major plan/pedagogy/exercise issues. Several dimensions are below 9 and the findings require direct fixes before shipping.

<fixes>
- find: |-
    Let us start with the core building blocks: the numbers from one to ten. Listen carefully to how they sound.
  replace: |-
    Let us start with the core building blocks: the numbers from one to ten. Listen carefully to how they sound. Ukrainian Lessons Season 1, Episode 5 focuses on this pronunciation set.

- find: |-
    Pronunciation requires special attention here. The words **п'ять** and **дев'ять** contain an apostrophe. This symbol acts like a tiny pause. It creates a hard consonant separation before the soft vowel sound. You must clearly separate the sounds. The number **сім** features a distinct, soft 'і' sound. It does not sound like the English word "same".
  replace: |-
    Pronunciation requires special attention here. The words **п'ять** and **дев'ять** contain an apostrophe. In Ukrainian, the apostrophe shows that the consonant before the following vowel stays hard; it is not a pause sound. So in **п'ять** and **дев'ять**, pronounce the consonant clearly before the next vowel. The number **сім** has a clear Ukrainian **і** sound.

- find: |-
    Unlike English, the numbers one and two change based on the gender of the noun they describe. The number **один** is masculine. You say **один стіл** (one table). For feminine nouns, you use **одна**, like **одна книга** (one book). For neuter nouns, you use **одне**, like **одне вікно** (one window). The number two also changes. Use **два** for masculine and neuter words: **два столи** (two tables), **два вікна** (two windows). Use **дві** for feminine words: **дві книги** (two books).
  replace: |-
    For now, learn the most common combinations as ready-made chunks: **один стіл** (one table), **одна книга** (one book), **одне вікно** (one window), **два столи** (two tables), **два вікна** (two windows), **дві книги** (two books).

- find: |-
    Ukrainian uses a strict counting pattern for nouns. We call this the 1, 2-4, 5+ pattern. You should memorize these as rhythmic chunks.
    *   Number 1 pairs with a singular noun: **один рік** (one year).
    *   Numbers 2, 3, and 4 pair with a plural noun: **два роки** (two years), **три студенти** (three students). 
    *   Numbers 5 and above (up to 20) require a different noun ending: **п'ять років** (five years), **десять гривень** (ten hryvnias).
  replace: |-
    At this level, treat these as patterns you can repeat: **один рік** (one year), **два роки** (two years), **три студенти** (three students), **п'ять років** (five years), **десять гривень** (ten hryvnias). You do not need the grammar rule yet.

- find: |-
    Let us apply these numbers directly to prices. The national currency is the **гривня** (hryvnia). It follows the exact same 1, 2-4, 5+ counting pattern we learned earlier.
  replace: |-
    Let us apply these numbers directly to prices. The national currency is the **гривня** (hryvnia), and smaller amounts use **копійка** (kopek). Ukrainian Lessons Season 1, Episode 9 teaches these numbers through real prices. It follows the same ready-made patterns we learned earlier.

- find: |-
    This dialogue uses a highly specific formula. To ask someone's age, you say **Скільки тобі років?** (How old are you?). The word **скільки** means how many. To reply, you do not use the verb "to have" like in some languages, and you do not use "to be" like in English. Instead, you use a fixed chunk: **мені** (to me), **тобі** (to you), or **їй** (to her) followed by the number. **Мені двадцять п'ять** literally translates as "to me is twenty-five". Treat this entire phrase as a single memorized chunk.
  replace: |-
    This dialogue uses a highly specific formula. To ask someone's age, you say **Скільки тобі років?** (How old are you?). The word **скільки** means how many. To reply, you do not use the verb "to have" like in some languages, and you do not use "to be" like in English. Instead, you use a fixed chunk: **мені** (to me), **тобі** (to you), or **їй** (to her) followed by the number. **Мені двадцять п'ять** literally translates as "to me is twenty-five". Treat this entire phrase as a single memorized chunk.

    <!-- INJECT_ACTIVITY: quiz-ages -->

- find: |-
    <!-- INJECT_ACTIVITY: quiz-prices -->

    <!-- INJECT_ACTIVITY: quiz-ages -->
  replace: |-
    <!-- INJECT_ACTIVITY: quiz-prices -->
</fixes>