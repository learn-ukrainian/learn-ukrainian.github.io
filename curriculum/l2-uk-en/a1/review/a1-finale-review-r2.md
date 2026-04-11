## Linguistic Scan
Errors found: 
- `ко́шту́є` and `виши́ва́нка` have double acute stress marks (orthographic error).
- "synthetic future tense... **прочита́ю**" — factual grammar error (`прочита́ю` is the simple perfective future; the synthetic future is `чита́тиму`).

## Exercise Check
- `<!-- INJECT_ACTIVITY: match-survival-phrases -->` (placed correctly after survival dialogues)
- `<!-- INJECT_ACTIVITY: order-day-events -->` (placed correctly after the evening reflection)
- `<!-- INJECT_ACTIVITY: fill-in-tenses -->` (placed correctly after the evening reflection)
- `<!-- INJECT_ACTIVITY: a1-grammar-quiz -->` (placed correctly at the end)
No issues found. Markers perfectly align with the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Covers every required point from the plan beautifully, seamlessly blending the wake-up routine, metro directions, souvenir shopping, and evening reflection. Word count is healthy (1389 words). |
| 2. Linguistic accuracy | 7/10 | Contains a critical grammatical mislabeling: `прочита́ю` is cited as the "synthetic future" when it is actually the simple perfective future (the synthetic future is `читатиму`). Additionally, `ко́шту́є` and `виши́ва́нка` incorrectly have double stress marks. |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. Grammar is presented via natural scenarios (survival phrases, ordering food, buying tickets) before explaining the mechanics. Shifts in tense are highlighted smoothly ("This shift from the past to the present shows you are narrating your own life."). |
| 4. Vocabulary coverage | 10/10 | All required and recommended words (готовий, вітаю, початок, сувенір, квиток, зустріти/зустрічати, круасан, карта, лінія, фільм, познайомитися, подорожувати, Лавра, готель) are naturally woven into the prose. |
| 5. Exercise quality | 10/10 | The four `INJECT_ACTIVITY` markers match the `activity_hints` in the plan and are placed right after their respective thematic sections. |
| 6. Engagement & tone | 8/10 | The tone is generally encouraging and warm, but the phrase "you will unlock the true engine of the language" violates the negative tone prompt against using gamified corporate language ("You have unlocked..."). |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present. No missing tags. The 1389-word count is excellent for A1 finale. |
| 8. Cultural accuracy | 10/10 | Highly authentic. Uses Hryvnias, standard Kyiv landmarks (Khreshchatyk, TSUM, Lavra), and classic Ukrainian dishes (борщ і вареники). |
| 9. Dialogue & conversation quality | 10/10 | Excellent short, natural exchanges that fit the A1 level perfectly while still sounding authentic (e.g., direct passerby instructions: "Їдьте на метро, станція Хрещатик"). |

## Findings
[2] [CRITICAL]
Location: "You will learn the elegant synthetic future tense, like saying **прочита́ю** (I will read) instead of just using **буду чита́ти**."
Issue: Factual grammar error. "Прочита́ю" is the perfective simple future, not the synthetic future. The synthetic future of "читати" is "читатиму" (imperfective). Learners will memorize the wrong term.
Fix: Replace "**прочита́ю**" with "**чита́тиму**" to accurately demonstrate the synthetic future.

[2] [MAJOR]
Location: "> **Ти:** Скі́льки ко́шту́є? *(How much does it cost?)*"
Issue: The word "коштує" contains two acute stress marks (`ко́шту́є`). It should only have one primary stress on the first syllable (`ко́штує`). 
Fix: Remove the second stress mark to make it "ко́штує".

[2] [MAJOR]
Location: "> **Ти:** Скільки коштує ця виши́ва́нка? *(How much does this vyshyvanka cost?)*"
Issue: The word "вишиванка" contains two acute stress marks (`виши́ва́нка`). Standard prose should only include one primary stress (`вишива́нка`).
Fix: Remove the first stress mark to make it "вишива́нка".

[6] [MINOR]
Location: "In A2, you will unlock the true engine of the language: **відмі́нки** (cases), which change word endings to show their role in a sentence."
Issue: The phrase "you will unlock" violates the tone policy against gamified/corporate language ("You have unlocked...", "Your journey begins...").
Fix: Replace "unlock" with "learn".

## Verdict: REVISE
The module is exceptional in narrative structure, flow, and pedagogy. However, the mislabeling of the synthetic future tense is a critical factual error that cannot ship to learners. The double stress marks and gamified tone phrase also require deterministic fixes.

<fixes>
- find: "> **Ти:** Скі́льки ко́шту́є? *(How much does it cost?)*"
  replace: "> **Ти:** Скі́льки ко́штує? *(How much does it cost?)*"
- find: "> **Ти:** Скільки коштує ця виши́ва́нка? *(How much does this vyshyvanka cost?)*"
  replace: "> **Ти:** Скільки коштує ця вишива́нка? *(How much does this vyshyvanka cost?)*"
- find: "You will learn the elegant synthetic future tense, like saying **прочита́ю** (I will read) instead of just using **буду чита́ти**."
  replace: "You will learn the elegant synthetic future tense, like saying **чита́тиму** (I will read) instead of just using **буду чита́ти**."
- find: "In A2, you will unlock the true engine of the language: **відмі́нки** (cases), which change word endings to show their role in a sentence."
  replace: "In A2, you will learn the true engine of the language: **відмі́нки** (cases), which change word endings to show their role in a sentence."
</fixes>