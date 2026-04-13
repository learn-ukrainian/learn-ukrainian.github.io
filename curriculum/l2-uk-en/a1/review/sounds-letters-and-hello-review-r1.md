## Linguistic Scan
No Russianisms, Surzhyk, paronym slips, or banned Russian characters (`ы, э, ё, ъ`) found.

Factual issues found:
- In `Звуки і літери`: `This means that what you see is almost always exactly what you hear... Once you learn the specific sounds that these 33 symbols represent, you will have the ability to read absolutely any Ukrainian word out loud.` This overstates Ukrainian phonetic transparency; the plan itself says `(mostly) what you hear`.
- In `Приголосні звуки`: `This hard and soft distinction is a uniquely Slavic phonetic feature.` That cross-linguistic claim is too broad.

## Exercise Check
All 6 planned activity markers are present and spread through the module: `letter-grid`, `quiz-sounds-vs-letters`, `match-up-letters-to-sounds`, `group-sort-vowels-consonants`, `watch-and-repeat-alphabet`, `fill-in-greeting`.

Issue found:
- `<!-- INJECT_ACTIVITY: match-up-letters-to-sounds -->` appears right after the vowel section, but the plan says that exercise matches `А, О, У, М, К, Н` to sounds. Because `М, К, Н` are taught in the consonant section, this marker is placed before all prerequisite content.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned H2 sections are present and the textbook references are integrated, but the plan’s `У-ля (one [у])` example is replaced by `**око**`, and `А у тебе?` is absent from the greeting teaching even though the plan explicitly includes it. |
| 2. Linguistic accuracy | 8/10 | No Russianisms/Surzhyk/banned letters found, but `what you see is almost always exactly what you hear` and `uniquely Slavic phonetic feature` are factual overstatements. |
| 3. Pedagogical quality | 7/10 | The module gives examples and moves into dialogue practice, but it drops the planned `[у]` listening example and fails to teach the reciprocal chunk `А у тебе?` where learners would need it. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is covered in prose: `звук`, `літера`, `голосний`, `приголосний`, `привіт`, `як справи`, `добре`, `чудово`, `мама`, `молоко`; recommended items such as `тато`, `око`, `дім`, `ніс`, `сон`, `нормально` also appear. |
| 5. Exercise quality | 7/10 | Marker count matches the 6 planned activities, but `match-up-letters-to-sounds` is placed before consonants are taught even though the planned item set includes `М`, `К`, `Н`. |
| 6. Engagement & tone | 8/10 | Named speakers and classroom framing work, but phrases like `absolute foundation` and `absolutely any Ukrainian word` push the tone toward lecture-like absolutism. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and in order; markdown is clean; pipeline word count `2086` is safely above the target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms, uses Ukrainian-school references, and avoids Russian-centered framing. |
| 9. Dialogue & conversation quality | 8/10 | The dialogues use named speakers and plausible A1 situations, but the greeting exchange stops at `Добре, дякую!` instead of modeling the planned reciprocal `А у тебе?`. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `This means that what you see is almost always exactly what you hear... Once you learn the specific sounds that these 33 symbols represent, you will have the ability to read absolutely any Ukrainian word out loud.`  
Issue: This teaches an absolute rule about Ukrainian spelling-pronunciation correspondence. The plan says `(mostly) what you hear`; the generated prose removes that hedge and overpromises.  
Fix: Soften the claim to “usually very close” / “relatively consistent” / “strong first reading attempt.”

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `This hard and soft distinction is a uniquely Slavic phonetic feature.`  
Issue: The cross-linguistic claim is too broad.  
Fix: Rephrase it as a feature that is central to Ukrainian and unfamiliar to most English speakers.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Finally, listen to the word **око** (eye), which also clearly features the [о] sound prominently.`  
Issue: The plan explicitly specifies `У-ля (one [у])`; the module repeats another `[о]` example instead of giving the planned `[у]` listening example.  
Fix: Replace the `око` sentence with a clear `[у]` example such as `У-ля`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `When someone asks **як справи** (how are you), the most common and polite response is **добре** (fine, good).`  
Issue: The plan explicitly includes the reciprocal chunk `А у тебе?`, and a search confirms that exact phrase never appears in the module. `А тебе?` in the name dialogue is a different ellipsis.  
Fix: Expand this explanation to teach `чудово`, `нормально`, and `А у тебе?`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: match-up-letters-to-sounds -->` immediately after the vowel section.  
Issue: The planned match-up activity includes consonant pairs `М ↔ [м], К ↔ [к], Н ↔ [н]`, so the marker is placed before all required teaching is complete.  
Fix: Move this marker to after the consonant section.

## Verdict: REVISE
REVISE. The module is structurally complete and mostly strong on vocabulary coverage, but it contains two factual overstatements in phonetics and several concrete plan/exercise mismatches that need correction before shipping.

<fixes>
- find: |
    For English speakers, a major advantage is that Ukrainian spelling is highly phonetic. This means that what you see is almost always exactly what you hear. Unlike English, where the letter "a" sounds completely different in "cat," "father," and "late," Ukrainian letters are remarkably consistent. There are no silent letters hiding in words to trick you (except for the functional role of the soft sign Ь). There are no surprise pronunciations or unpredictable spelling rules to memorize. Once you learn the specific sounds that these 33 symbols represent, you will have the ability to read absolutely any Ukrainian word out loud.
  replace: |
    For English speakers, a major advantage is that Ukrainian spelling is highly phonetic. This means that what you see is usually very close to what you hear. Unlike English, where the letter "a" sounds completely different in "cat," "father," and "late," Ukrainian letters are relatively consistent. There are no silent letters hiding in words to trick you (except for the functional role of the soft sign Ь). Pronunciation patterns are much more predictable than in English, so once you learn the specific sounds that these 33 symbols represent, you will usually be able to make a strong first reading attempt aloud.
- find: |
    This hard and soft distinction is a uniquely Slavic phonetic feature. It does not exist in English, which means you will need to train your ear to hear the difference.
  replace: |
    This hard and soft distinction is central to Ukrainian phonetics and unfamiliar to most English speakers, which means you will need to train your ear to hear the difference.
- find: |
    Finally, listen to the word **око** (eye), which also clearly features the [о] sound prominently.
  replace: |
    Finally, listen to the name **Уля**. It gives you a clear [у] example: У-ля.
- find: |
    In this short exchange, you see the formal greeting "Добрий день" used respectfully with a teacher, followed by the informal greeting **привіт** (hi). When someone asks **як справи** (how are you), the most common and polite response is **добре** (fine, good).
  replace: |
    In this short exchange, you see the formal greeting "Добрий день" used respectfully with a teacher, followed by the informal greeting **привіт** (hi). When someone asks **як справи** (how are you), you can answer **добре** (fine, good), **чудово** (great), or **нормально** (okay), and ask the question back with **А у тебе?** (And you?).
- find: |
    <!-- INJECT_ACTIVITY: match-up-letters-to-sounds -->
  replace: ""
- find: |
    <!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->
  replace: |
    <!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->

    <!-- INJECT_ACTIVITY: match-up-letters-to-sounds -->
</fixes>