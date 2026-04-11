## Linguistic Scan

Found 2 linguistic errors:
1. **Russianism / Calque:** The phrase `Давайте подивимося` uses the "давайте + дієслово" construction, which is a calque from the Russian "давайте посмотрим". Natural Ukrainian requires the synthetic imperative form `Подивімося` or `Розгляньмо`.
2. **Calque:** The phrase `прямо зараз` is a direct calque from the Russian "прямо сейчас". A more natural and authentic Ukrainian expression for this context is `саме зараз` or `саме тепер`.

All other forms, morphology, spelling, and translations are accurate. The phonetical explanations (e.g. open/closed syllables and vowel alternations `о/е → і`) are factually correct. The text correctly identifies typical mistakes (like `Вчора я прочитав книжку три години`).

## Exercise Check

The plan requested 6 specific activities (`quiz`, `fill-in`, `group-sort`, `match-up`, `error-correction`, `open-writing`).
The writer placed 6 excellent inline markers with descriptive IDs (`<!-- INJECT_ACTIVITY: group-sort-distribute-verbs-between-i-and-ii-conjugation-classes -->`, etc.) immediately following the relevant pedagogical sections. These perfectly align with the plan.

However, there are two issues:
1. The writer erroneously added a 7th duplicate inline marker (`<!-- INJECT_ACTIVITY: fill-in -->`) under the section "Дієслова на -ся: зворотні дієслова", which has no corresponding plan hint.
2. The writer clustered 6 generic markers at the very end of the module. This violates the anti-clustering rule and duplicates the activities already injected inline.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Every point from the `content_outline` is covered. The text successfully explains conjugation classes, tense structures, verb aspect (perfective/imperfective), narrative foreground vs background, and reflexive verbs. All required vocabulary is present. |
| 2. Linguistic accuracy | 9/10 | Almost perfect, but deducted points for the Russianism "Давайте подивимося" instead of the synthetic imperative "Подивімося", and the temporal calque "прямо зараз" instead of "саме зараз". Gender agreement and phonetic rules are perfectly explained. |
| 3. Pedagogical quality | 10/10 | The PPP flow is perfectly executed. The use of a relatable café dialogue to introduce present/past contrasts works well. Excellent pedagogical metaphors are used (e.g., aspect as a "video recording vs photograph", and past tense verb as a "mirror of the subject"). |
| 4. Vocabulary coverage | 10/10 | All required vocabulary (`дієвідміна`, `особа`, `доконаний вид`, `видова пара`, etc.) is used naturally in the prose. Recommended terms like `тематичний голосний` and `постфікс` are also explicitly introduced and explained. |
| 5. Exercise quality | 8/10 | The 6 primary inline activities perfectly match the plan's `activity_hints`. Deducted points because the writer accidentally clustered 6 generic duplicate markers at the end of the module and added an extra `fill-in` marker under section 5. |
| 6. Engagement & tone | 10/10 | Tone is warm and encouraging. It uses clear, concrete Ukrainian examples rather than empty filler. The tone feels like a knowledgeable teacher leading a class. |
| 7. Structural integrity | 10/10 | Module achieves a word count of 4,994 words, easily surpassing the 4,000-word target. All headings are present, the markdown formatting is clean, and the sequence flows logically. |
| 8. Cultural accuracy | 10/10 | The module highlights a critical decolonization marker (the dropping of the final «-ть» in the 3rd person singular for 1st conjugation verbs) as a feature of Ukrainian linguistic identity. It perfectly represents the language on its own terms. |
| 9. Dialogue & conversation quality | 10/10 | The opening dialogue features named speakers (Олексій and Дарина) and a natural, multi-turn conversation that seamlessly introduces the grammar topic ("Скільки літ, скільки зим!", "Я ж все літо працював... А зараз що робиш?"). |

## Findings

[2. Linguistic accuracy] [CRITICAL]
Location: `Давайте подивимося на повну парадигму для дієслів «писати» та «знати». Я пишу, знаю.`
Issue: The phrase "давайте подивимося" uses the "давай(те) + дієслово" construction, which is a calque of the Russian "давайте посмотрим". Standard Ukrainian grammar dictates the use of the synthetic imperative for the first person plural.
Fix: Replace "Давайте подивимося" with "Подивімося".

[2. Linguistic accuracy] [CRITICAL]
Location: `Це логічно: якщо дія відбувається прямо зараз, у момент мовлення, вона ще триває і не може бути завершеною.`
Issue: The phrase "прямо зараз" is a calque of the Russian "прямо сейчас" when used in a temporal sense. It should be translated into authentic Ukrainian.
Fix: Replace "прямо зараз" with "саме зараз".

[5. Exercise quality] [MAJOR]
Location: `<!-- INJECT_ACTIVITY: fill-in -->` (under section 5) and the entire cluster of 6 generic markers at the end of the text.
Issue: The writer successfully placed the 6 required markers inline, but incorrectly added an extra inline marker under section 5 and unnecessarily clustered 6 duplicate generic markers at the end of the file. This creates duplicate, empty exercises.
Fix: Remove the duplicate `fill-in` marker under section 5 and the 6 clustered markers at the end of the module.

## Verdict: REVISE
The module is outstanding in its pedagogical approach, depth, and cultural awareness. It easily passes all quality gates structurally and exceeds the word count. However, the two critical linguistic calques ("Давайте подивимося", "прямо зараз") and the duplicated exercise markers must be fixed before publishing.

<fixes>
- find: |
    -уть(-ють).*

    Давайте подивимося на повну парадигму для дієслів «писати» та «знати». Я пишу, знаю.
  replace: |
    -уть(-ють).*

    Подивімося на повну парадигму для дієслів «писати» та «знати». Я пишу, знаю.
- find: |
    Теперішній час в українській мові мають лише дієслова недоконаного виду. Це логічно: якщо дія відбувається прямо зараз, у момент мовлення, вона ще триває і не може бути завершеною. Тому дієслова доконаного виду форм теперішнього часу не утворюють.
  replace: |
    Теперішній час в українській мові мають лише дієслова недоконаного виду. Це логічно: якщо дія відбувається саме зараз, у момент мовлення, вона ще триває і не може бути завершеною. Тому дієслова доконаного виду форм теперішнього часу не утворюють.
- find: |
    authentic and emotionally resonant.

    <!-- INJECT_ACTIVITY: fill-in -->

    ## Підсумок
  replace: |
    authentic and emotionally resonant.

    ## Підсумок
- find: |
    unique synthetic form ("робитиму"), which is a hallmark of the Ukrainian language.*

    <!-- INJECT_ACTIVITY: quiz -->
    <!-- INJECT_ACTIVITY: fill-in -->
    <!-- INJECT_ACTIVITY: group-sort-i-ii -->
    <!-- INJECT_ACTIVITY: match-up -->
    <!-- INJECT_ACTIVITY: error-correction -->
    <!-- INJECT_ACTIVITY: open-writing -->
  replace: |
    unique synthetic form ("робитиму"), which is a hallmark of the Ukrainian language.*
</fixes>