## Linguistic Scan
- `## Минулий час`: `You simply remove this **-ти** ending to find the verb stem. Once you have the stem, you add a specific single-letter or two-letter suffix to create the past tense.` and `Every verb follows the same predictable pattern based on its infinitive stem.` This is factually wrong as a universal rule. Local lemma verification shows common counterexamples: `йти → йшов/йшла/йшли`, `їсти → їв/їла/їли`, `могти → міг/могла/могли`.
- `## Summary`: `You take the infinitive stem of the verb and add **-в** for a masculine subject, **-ла** for a feminine subject, **-ло** for a neuter subject, and **-ли** for plural subjects.` repeats the same overgeneralization as a blanket rule.

## Exercise Check
- Found 3 markers: `matching-pronoun-ending`, `fill-in-core-verbs`, `fill-in-choose-gender`.
- Marker IDs match the 3 `activity_hints` in the plan.
- Placement is acceptable: the matching marker comes after `## Минулий час`; the two fill-in markers come after `## Практика`.
- No exercise-logic errors are visible from the markers themselves.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The four planned sections are present, but the practice point in the plan asked for explicit core-verb paradigms and the module stops at `The verb **говорити** (to speak) follows the exact same logic.` instead of giving `говорив / говорила / говорило / говорили`. |
| 2. Linguistic accuracy | 6/10 | The Ukrainian example sentences are fine, but the grammar explanation says `You simply remove this **-ти** ending...` and `Every verb follows the same predictable pattern...`, which is false for common verbs such as `йти → йшов`, `їсти → їв`, `могти → міг`. |
| 3. Pedagogical quality | 6/10 | The module has a PPP shape, but it teaches an overgeneralized rule as fact and then introduces irregular `**провів вихідні**` later with no warning, which undermines the learner model it just taught. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears naturally in prose or inflected form: `учора`, `робив/робила`, `читав`, `працювала`, `гуляв`, `готувала`, `дивився`, `говорили`; recommended items like `вихідні`, `суботу`, `неділю`, `разом`, `фільм`, `провів` are also present. |
| 5. Exercise quality | 9/10 | All 3 expected markers are present and aligned to the plan: `matching-pronoun-ending`, `fill-in-core-verbs`, `fill-in-choose-gender`. Their placement follows the teaching sequence. |
| 6. Engagement & tone | 9/10 | The office/weekend scenario and named speakers keep the module teacherly and concrete, and the examples stay focused on the target grammar. |
| 7. Structural integrity | 10/10 | `## Dialogues`, `## Минулий час (Past Tense)`, `## Практика (Practice)`, and `## Summary` are all present and ordered correctly. The pipeline word count is 1626, so the module is safely above target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms, with no Russian-centered framing and no cultural inaccuracies in the scenarios shown. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues use named speakers, a plausible Monday-morning context, and multi-turn weekend sharing rather than isolated transactional lines. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Минулий час` — `You simply remove this **-ти** ending to find the verb stem. Once you have the stem, you add a specific single-letter or two-letter suffix to create the past tense.` / `Every verb follows the same predictable pattern based on its infinitive stem.` and `## Summary` — `You take the infinitive stem of the verb and add **-в** for a masculine subject, **-ла** for a feminine subject, **-ло** for a neuter subject, and **-ли** for plural subjects.`  
Issue: The module states a beginner pattern as if it were the universal formation rule for Ukrainian past tense. That is false and teaches wrong grammar. Verified counterexamples: `йти → йшов/йшла/йшли`, `їсти → їв/їла/їли`, `могти → міг/могла/могли`.  
Fix: Re-scope the rule to “many common verbs at A1” and explicitly note that some verbs have irregular past forms.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Практика` — `When discussing weekends, Ukrainians frequently use the verb **провести** (to spend time). The common vocabulary phrase for spending the weekend is **провів вихідні** for a man, **провела вихідні** for a woman, and **провели вихідні** for a group.`  
Issue: The module introduces an irregular past-tense form immediately after teaching a supposedly universal regular rule, but it does not warn the learner that `провести` must be memorized separately.  
Fix: Add a short note that `провести` is a common irregular verb and that these weekend phrases should be learned as chunks.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Практика` — `The verb **говорити** (to speak) follows the exact same logic.`  
Issue: The plan asked for explicit core-verb paradigms in past tense; `говорити` is named but its forms are not actually shown.  
Fix: Replace the sentence with the full paradigm: `говорив / говорила / говорило / говорили`.

## Verdict: REVISE
Critical factual grammar overgeneralization means this cannot pass as-is. The structure, vocabulary coverage, and exercises are solid, but the grammar explanation teaches a false universal rule and needs deterministic correction.

<fixes>
- find: "You simply remove this **-ти** ending to find the verb stem. Once you have the stem, you add a specific single-letter or two-letter suffix to create the past tense."
  replace: "For many common verbs at this level, you can remove this **-ти** ending to find the stem and then add a past-tense ending. This is a useful beginner pattern, but not every Ukrainian verb forms the past tense this way."
- find: "The past tense in Ukrainian is incredibly systematic compared to English! There are no irregular vowel changes to memorize for regular verbs. Every verb follows the same predictable pattern based on its infinitive stem."
  replace: "The past tense in Ukrainian is systematic for many common verbs at A1. Learn this pattern first, but remember that some verbs have irregular past forms that you will study later."
- find: "The verb **говорити** (to speak) follows the exact same logic."
  replace: "The verb **говорити** (to speak) becomes **говорив**, **говорила**, **говорило**, and **говорили**."
- find: "When discussing weekends, Ukrainians frequently use the verb **провести** (to spend time). The common vocabulary phrase for spending the weekend is **провів вихідні** for a man, **провела вихідні** for a woman, and **провели вихідні** for a group."
  replace: "When discussing weekends, Ukrainians frequently use the verb **провести** (to spend time). This verb is common but irregular, so learn these forms as a chunk: **провів вихідні** for a man, **провела вихідні** for a woman, and **провели вихідні** for a group."
- find: "The mechanical formation of the past tense in Ukrainian is highly systematic. You take the infinitive stem of the verb and add **-в** for a masculine subject, **-ла** for a feminine subject, **-ло** for a neuter subject, and **-ли** for plural subjects. The most important rule to remember is that gender dictates the ending of the verb. The grammatical person does not change the suffix; the physical gender of the subject does."
  replace: "For many common verbs at A1, past tense formation is systematic: you take the infinitive stem and add **-в** for a masculine subject, **-ла** for a feminine subject, **-ло** for a neuter subject, and **-ли** for plural subjects. The most important rule to remember is that gender dictates the ending of the verb. The grammatical person does not change the suffix; the speaker's or subject's gender does."
</fixes>