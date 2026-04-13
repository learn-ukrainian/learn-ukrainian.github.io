## Linguistic Scan
- Grammar-teaching error in the Section 1 gloss: `> *Every Ukrainian verb has its pair. One verb describes the process, and the other verb shows the result.*` contradicts the Ukrainian sentence above it (`Більшість ... але є й одновидові та двовидові дієслова`) and teaches a false rule.
- Grammar-teaching error in Section 2: `When you see these letters expanding the end of a verb, they almost always signal a continuous, imperfective process.` This is too absolute. VESUM confirms perfective verbs with `-ува-` exist, e.g. `подарувати` (`verb:perf:inf`).
- Grammar-teaching error in Section 2: `Коли ми використовуємо суфікс «-ува-», дія стає довгою і повільною.` Aspect does not encode speed; imperfective marks process/repetition/non-completion, not “slow action.”
- Grammar-teaching error in Section 3: `класти / покласти` is presented as suppletion inside `Зовсім інші слова (суплетивізм)`. SУМ-11 definitions show same-root verbs, so this is not a suppletive pair.

## Exercise Check
- Marker inventory matches the 4 plan hints:
  - `quiz-find-partner`
  - `match-up-fill-in-the-blanks-with-the-correct-pair`
  - `fill-in-categorize`
  - `fill-in-choose-partner`
- Each marker comes after relevant teaching, so nothing is placed before the concept appears.
- Placement is uneven: `fill-in-categorize` and `fill-in-choose-partner` are back-to-back at the very end, while the intro section has no practice marker immediately after the first core concept.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All planned H2 sections appear in order, core examples such as `писати / написати`, `читати / прочитати`, `вирішувати / вирішити`, `брати / взяти`, `говорити / сказати` are covered, and the references are cited in the intro. |
| 2. Linguistic accuracy | 5/10 | The module teaches false rules: `Every Ukrainian verb has its pair`; `-ува-` / `-юва-` `almost always signal` imperfective; `дія стає довгою і повільною`; and `класти / покласти` is mislabeled as suppletion. |
| 3. Pedagogical quality | 6/10 | Method 2 gives unreliable heuristics: `Коли ми використовуємо суфікс «-ува-», дія стає довгою і повільною` and `almost always signal a continuous, imperfective process` overteach aspect and can cause learner error. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is integrated naturally in prose: `пара`, `префікс`, `суфікс`, `корінь`, `читати / прочитати`, `писати / написати`, `брати / взяти`, `говорити / сказати`. |
| 5. Exercise quality | 8/10 | All 4 planned marker types are present, but `<!-- INJECT_ACTIVITY: fill-in-categorize -->` and `<!-- INJECT_ACTIVITY: fill-in-choose-partner -->` are clustered at the end instead of being spread more evenly. |
| 6. Engagement & tone | 8/10 | The бабуся/онучка вареники frame is concrete and memorable, and the teacher voice stays instructional rather than gamified. |
| 7. Structural integrity | 10/10 | All planned sections are present, markdown is clean, and the pipeline word count is 3068, which is above the 2000 target. |
| 8. Cultural accuracy | 10/10 | The module uses specifically Ukrainian framing (`вареники`, `Бабуся`, `Онучка`) and avoids Russian-centered comparison. |
| 9. Dialogue & conversation quality | 8/10 | The opening dialogue has named speakers and a real situation; later examples are useful but mostly illustrative rather than conversational. |

## Findings
[DIMENSION] [SEVERITY: critical]  
Location: Section 1 — `> *Every Ukrainian verb has its pair. One verb describes the process, and the other verb shows the result.*`  
Issue: This English gloss contradicts the Ukrainian sentence above it and teaches a false rule. Not every Ukrainian verb has a regular aspectual pair.  
Fix: Change `Every` to `Most` and mention that some verbs are biaspectual or lack a regular pair.

[DIMENSION] [SEVERITY: critical]  
Location: Section 2 — `When you see these letters expanding the end of a verb, they almost always signal a continuous, imperfective process.`  
Issue: This is factually wrong as a rule. VESUM confirms perfective verbs with `-ува-` exist (`подарувати`), so the suffix is not a reliable aspect label by itself.  
Fix: Rephrase to say that `-ува-/-юва-` often appear in imperfectivization patterns such as `вирішити / вирішувати`, but are not universal imperfective markers.

[DIMENSION] [SEVERITY: critical]  
Location: Section 2 — `Коли ми використовуємо суфікс «-ува-», дія стає довгою і повільною.`  
Issue: This teaches the wrong meaning of aspect. Imperfective does not mean “slow”; it means process, repetition, duration, or non-completion depending on context.  
Fix: Replace `довгою і повільною` with wording about process/repetition/non-completion.

[DIMENSION] [SEVERITY: critical]  
Location: Section 3 — `There are a few other common suppletive pairs...` and `Similarly, the physical action of putting or placing an object horizontally uses the irregular pair «класти» and «покласти».`  
Issue: `класти / покласти` is not suppletion; the verbs share the same root and differ by prefixation.  
Fix: Relabel this as a common high-frequency pair, and explicitly say it is not a true suppletive pair.

[DIMENSION] [SEVERITY: major]  
Location: End of module — `<!-- INJECT_ACTIVITY: fill-in-categorize -->` immediately followed by `<!-- INJECT_ACTIVITY: fill-in-choose-partner -->`  
Issue: Two markers are clustered at the end, so practice is less evenly distributed than it should be.  
Fix: Move `quiz-find-partner` to the end of the intro and move `fill-in-choose-partner` to the end of Method 1.

## Verdict: REVISE
Critical grammar-teaching errors are present, so this cannot pass as-is even though the structure, vocabulary coverage, and overall plan coverage are strong. The module needs targeted factual corrections and better exercise spacing.

<fixes>
- find: "> *Every Ukrainian verb has its pair. One verb describes the process, and the other verb shows the result.*"
  replace: "> *Most Ukrainian verbs have aspectual pairs. One verb describes the process, and the other verb shows the result, though some verbs are biaspectual or do not form a regular pair.*"
- find: "The most recognizable tool for this transformation is the addition of the suffixes «-ува-» or «-юва-». When you see these letters expanding the end of a verb, they almost always signal a continuous, imperfective process."
  replace: "One common tool for this transformation is the addition of the suffixes «-ува-» or «-юва-». In aspectual pairs like «вирішити / вирішувати» or «запитати / запитувати», these suffixes help form an imperfective partner, but they are not universal imperfective markers by themselves."
- find: "Коли ми використовуємо суфікс «-ува-», дія стає довгою і повільною."
  replace: "Коли ми використовуємо суфікс «-ува-», дія подається як процес або повторювана дія, а не як завершений результат."
- find: "There are a few other common suppletive pairs that you should add to your vocabulary list immediately."
  replace: "There are a few other common high-frequency pairs that you should add to your vocabulary list immediately."
- find: "Similarly, the physical action of putting or placing an object horizontally uses the irregular pair «класти» and «покласти»."
  replace: "Similarly, the physical action of putting or placing an object horizontally uses the common pair «класти» and «покласти». Unlike true suppletive pairs, these verbs share the same root and are formed with a prefix."
- find: "Throughout your journey, you should always memorize both forms at the exact same time. For a fuller explanation, compare Заболотний Grade 6, §52-54 and the Ukrainian Lessons article «Ukrainian Verb Aspect» listed in the references.\n\n## Спосіб 1: Додавання префікса (Method 1: Adding a Prefix) (~650 words)"
  replace: "Throughout your journey, you should always memorize both forms at the exact same time. For a fuller explanation, compare Заболотний Grade 6, §52-54 and the Ukrainian Lessons article «Ukrainian Verb Aspect» listed in the references.\n\n<!-- INJECT_ACTIVITY: quiz-find-partner -->\n\n## Спосіб 1: Додавання префікса (Method 1: Adding a Prefix) (~650 words)"
- find: "<!-- INJECT_ACTIVITY: quiz-find-partner -->\n\n## Спосіб 2: Зміна в корені або суфіксі (Method 2: Change in the Root or Suffix) (~650 words)"
  replace: "<!-- INJECT_ACTIVITY: fill-in-choose-partner -->\n\n## Спосіб 2: Зміна в корені або суфіксі (Method 2: Change in the Root or Suffix) (~650 words)"
- find: "<!-- INJECT_ACTIVITY: fill-in-categorize -->\n<!-- INJECT_ACTIVITY: fill-in-choose-partner -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-categorize -->"
</fixes>