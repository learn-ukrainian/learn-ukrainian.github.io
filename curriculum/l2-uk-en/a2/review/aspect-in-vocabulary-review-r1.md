## Linguistic Scan
- Critical factual grammar error: `Кожне українське дієслово має свою пару.` This is false; Ukrainian also has `одновидові` and `двовидові` verbs.
- Critical factual teaching error: Method 1 says `часто правильним і безпечним варіантом буде саме «по-»` and presents `по-` as the default perfectivizing prefix. That is unsafe and misleading.
- Critical factual phonetics error: the grammar box says `the wider «а» sound naturally takes longer to pronounce.` That is not a valid explanation of Ukrainian aspect morphology.

## Exercise Check
- Found 4 markers, matching the 4 `activity_hints`: `quiz-find-partner`, `match-up-fill-in-the-blanks-with-the-correct-pair`, `fill-in-categorize`, `fill-in-choose-partner`.
- Placement is mostly correct: the first marker follows Method 1, the second follows Method 2, and the last two come after all three formation types have been taught.
- No inline DSL exercises are present, so only marker placement could be checked here.
- No exercise-marker defects found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present and required pairs like `читати / прочитати`, `писати / написати`, `брати / взяти`, `говорити / сказати` appear, but the plan references are not cited in the prose: search confirmed `Заболотний` = 0 and `Ukrainian Lessons`/`ULP` = 0. |
| 2. Linguistic accuracy | 5/10 | The Ukrainian forms are mostly fine, but the module teaches false grammar/phonetics claims: `Кожне українське дієслово має свою пару`, `часто правильним і безпечним варіантом буде саме «по-»`, and `the wider «а» sound naturally takes longer to pronounce`. |
| 3. Pedagogical quality | 6/10 | The PPP shape exists, but Method 1 overgeneralizes: `This process is highly predictable... recognize perfective verbs instantly` and `often the correct and safe option will be exactly "по-"`. That trains guessing instead of pair memorization. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is integrated naturally: `пара`, `префікс`, `суфікс`, `корінь`, `читати / прочитати`, `писати / написати`, `брати / взяти`, `говорити / сказати`. Recommended words like `словник`, `запам'ятовувати`, `базовий` also appear. |
| 5. Exercise quality | 9/10 | All 4 planned activity types have corresponding markers, and each comes after the relevant teaching block. No inline exercise logic was available to inspect for distractor quality. |
| 6. Engagement & tone | 7/10 | The teacher voice is warm, but some prose is inflated and overconfident: `The absolute most universal and frequent prefix...` and `This process is highly predictable...`. That reads like filler and weakens trust. |
| 7. Structural integrity | 10/10 | All four H2 sections are present and ordered correctly, markers are clean, and the pipeline word count is 3132, which is above the 2000 target. |
| 8. Cultural accuracy | 10/10 | The module uses a credible Ukrainian kitchen scene with `вареники`, `Бабуся`, and `Онучка`, and it does not frame Ukrainian through Russian. |
| 9. Dialogue & conversation quality | 9/10 | The opening бабуся/онучка exchange is a natural multi-turn dialogue with named speakers and a real cooking task; later examples stay contextual rather than robotic. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: First section — `Кожне українське дієслово має свою пару.`  
Issue: This teaches a false absolute. Ukrainian does not consist only of neat aspectual pairs.  
Fix: Replace it with wording that most verbs have aspectual pairs, but some verbs are one-aspect or bi-aspectual.

[PEDAGOGICAL QUALITY] [SEVERITY: critical]  
Location: Method 1 — `This process is highly predictable...`, `The absolute most universal and frequent prefix...`, `часто правильним і безпечним варіантом буде саме «по-».`  
Issue: The section overstates predictability and teaches a bad heuristic. Learners should not guess perfective partners by defaulting to `по-`.  
Fix: Rephrase Method 1 to say prefixation is common, but the full pair must be memorized.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Method 2 grammar box — `the wider «а» sound naturally takes longer to pronounce.`  
Issue: False phonetics. The `о → а` alternation here is morphological, not a vowel-length rule.  
Fix: Replace the box with a morphology-based explanation.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Module-wide — references section from the plan vs generated prose  
Issue: The plan lists `Заболотний Grade 6, §52-54` and `ULP: Ukrainian Verb Aspect`, but neither is cited anywhere in the module text.  
Fix: Add one brief sentence pointing learners to both listed references.

## Verdict: REVISE
Critical factual teaching errors are present in the grammar explanation, so this cannot pass as-is. The structure and vocabulary coverage are strong, but the module needs targeted corrections before shipping.

<fixes>
- find: |
    Кожне українське дієслово має свою пару. Одне дієслово описує процес, а інше дієслово показує результат.
  replace: |
    Більшість українських дієслів мають видові пари. Одне дієслово описує процес, а інше показує результат, але є й одновидові та двовидові дієслова.
- find: |
    The first and most common way to form an aspectual **пара** (pair) is by adding a **префікс** (prefix) to the basic, imperfective verb. Think of it like adding a small grammatical tag to the very beginning of the word to announce, "This action is now successfully finished." This process is highly predictable in its structure, and once you start noticing these short additions, you will be able to recognize perfective verbs instantly in any text.
  replace: |
    The first and most common way to form an aspectual **пара** (pair) is by adding a **префікс** (prefix) to an imperfective verb. This pattern is common, but it is not fully automatic, so learners should memorize the whole pair instead of relying on the prefix alone.
- find: |
    The absolute most universal and frequent prefix you will encounter in the Ukrainian language is «по-». In a vast majority of cases, it simply flips the verb from a continuous process into a completed, singular action without changing its core, fundamental meaning at all. It is essentially the default tool the language reaches for to create a perfective partner when no other specific nuance is required.

    Якщо ви не знаєте, який саме префікс потрібен новому слову, часто правильним і безпечним варіантом буде саме «по-». Наприклад, ми кажемо «думати», коли процес мислення триває, і «подумати», коли ми вже завершили цю дію. Інші дуже популярні пари — це «снідати» та «поснідати», а також «бачити» і «побачити».

    > *If you do not know exactly which prefix a new word needs, often the correct and safe option will be exactly "по-". For example, we say "думати" (to think) when the process of thinking continues, and "подумати" when we have already finished this action. Other very popular pairs are "снідати" (to have breakfast) and "поснідати", as well as "бачити" (to see) and "побачити".*
  replace: |
    One common way to build a perfective partner is with a prefix, but there is no single universal prefix that works safely for every new verb. Learners should memorize the whole pair, because prefixes such as «по-», «з-», «на-», and «про-» can help form aspectual partners in some verbs while also adding lexical nuance.

    Якщо ви не знаєте, який префікс потрібен новому слову, краще не вгадувати. Краще вчити дієслова готовими парами: «думати / подумати», «снідати / поснідати», «бачити / побачити».

    > *If you do not know which prefix a new verb needs, it is better not to guess. It is better to learn verbs as ready-made pairs: "думати / подумати", "снідати / поснідати", "бачити / побачити".*
- find: |
    :::info
    **Grammar box**
    When a verb root changes from «о» to «а» (like допомогти → допомагати), the wider «а» sound naturally takes longer to pronounce. This phonetic stretching perfectly matches the grammatical shift from a quick result to a continuous process!
    :::
  replace: |
    :::info
    **Grammar box**
    When a verb root changes from «о» to «а» (like допомогти → допомагати), treat this as a morphological pattern that belongs to the pair. The important point for learners is the aspectual relationship, not an imagined difference in vowel length.
    :::
- find: |
    The imperfective verb is considered the **базовий** (basic) form. It is the raw, pure name of the action. When you want to talk about completing that action, you reach for its perfective partner. Throughout your journey, you should always memorize both forms at the exact same time.
  replace: |
    The imperfective verb is considered the **базовий** (basic) form. It is the raw, pure name of the action. When you want to talk about completing that action, you reach for its perfective partner. Throughout your journey, you should always memorize both forms at the exact same time. For a fuller explanation, compare Заболотний Grade 6, §52-54 and the Ukrainian Lessons article «Ukrainian Verb Aspect» listed in the references.
</fixes>