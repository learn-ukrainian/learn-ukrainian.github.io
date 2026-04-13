## Linguistic Scan
- `«Якщо завтра дощитиме, то ми вирішили **залишитися** (to stay) вдома».` This example contradicts the module’s own rule that real-condition result clauses here should use future or imperative forms; as taught, it models the wrong pattern for this lesson.
- `However, another word looks similar but has a completely different function: **якби** (if only).` and `It often translates to "if only" and expresses a strong wish about something that cannot be changed.` This is semantically misleading. `якби` is also a conditional conjunction, but for unreal/hypothetical conditions; “if only” is only one context-dependent gloss, not its core function.

## Exercise Check
4 activity markers are present:
- `fill-in-real-conditionals` after section 1
- `match-up-logical-results` after section 2
- `error-correction-verb-forms` after section 2
- `quiz-yakscho-vs-yakby` in section 3 after the `якщо/якби` contrast

Placement is generally correct: each marker comes after the relevant teaching. No inline DSL exercise blocks appear in the prose, so there is no exercise logic to audit here beyond marker placement.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The three H2 sections match the plan and the section sizes are on target (`~770/~770/~660` vs `700/700/600`). Required and recommended vocabulary is realized in prose (`порада`, `залишитися`, `парасольку`, `змокнеш`, `відпустку`). Deduction: the plan references are not integrated anywhere; searched content shows `Заболотний` = 0, `ULP` = 0, `Ukrainian Lessons` = 0. |
| 2. Linguistic accuracy | 6/10 | Two critical teaching inaccuracies: `«Якщо завтра дощитиме, то ми вирішили залишитися вдома»` mismatches the taught tense pattern, and `якби` is mischaracterized as having `a completely different function` and primarily meaning `if only`. |
| 3. Pedagogical quality | 7/10 | The module has good scenario-based teaching, but the faulty model sentence with `вирішили` directly undermines the grammar explanation, and the `якби` gloss risks teaching the wrong semantic contrast at A2. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears naturally in prose: `умова`, `результат`, `реальний`, `погода`, `допомогти`, `поспішиш`, `вільний`, `залишитися`, `порада`. Recommended vocabulary is also covered through natural forms: `якби`, `змокнеш`, `запізнишся`, `парасольку`, `відпустку`. |
| 5. Exercise quality | 10/10 | All four planned exercise types have markers, and each marker is placed after the relevant teaching section. No inline exercise logic errors are visible in the prose. |
| 6. Engagement & tone | 9/10 | The teacher voice is warm and concrete, using specific situations like garden planning, advice from a doctor, and weekend plans. The tone stays instructional rather than gamified. |
| 7. Structural integrity | 10/10 | All planned sections are present and correctly ordered. The markdown is clean, and the pipeline word count is `2427`, safely above target. |
| 8. Cultural accuracy | 10/10 | The module frames Ukrainian on its own terms and uses everyday Ukrainian contexts (`дача`, `Карпати`, family planning, advice) without Russian-centered comparison. |
| 9. Dialogue & conversation quality | 9/10 | The garden dialogue is natural, multi-turn, and aligned with the plan: `Якщо буде сонце, посадимо помідори... Якщо ти купиш насіння, я підготую грядку.` The rest of the module relies more on narrated examples than additional full dialogues. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Наприклад: «Якщо завтра дощитиме, то ми вирішили **залишитися** (to stay) вдома».`  
Issue: This model sentence contradicts the lesson’s own rule that the result clause in these A2 real conditionals uses future or imperative forms.  
Fix: Change the result clause to a future form, e.g. `«Якщо завтра дощитиме, то ми залишимося вдома».`

- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `However, another word looks similar but has a completely different function: **якби** (if only). This word introduces an unreal or hypothetical situation.`  
Issue: `якби` is not a “completely different function”; it is also a conditional conjunction, but for unreal/hypothetical conditions. This wording teaches the contrast inaccurately.  
Fix: Rephrase it as a different type of condition, not a completely different function.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `It often translates to "if only" and expresses a strong wish about something that cannot be changed.`  
Issue: This overnarrows the meaning of `якби`. In this module it should primarily be glossed as marking an unreal/hypothetical condition; `if only` is only one possible context.  
Fix: Replace this line with wording that makes unreal/hypothetical condition the primary meaning.

- [PLAN ADHERENCE] [SEVERITY: major]  
Location: module-wide; no integration around the rule sections or the `якщо/якби` contrast  
Issue: The source-of-truth plan includes `Заболотний Grade 5`, `Заболотний Grade 6`, and `ULP: If in Ukrainian — якщо vs якби`, but none are cited in the module text. I verified 0 occurrences of `Заболотний`, `ULP`, and `Ukrainian Lessons`.  
Fix: Add one short sentence in the `якщо/якби` section noting that this real-vs-unreal distinction matches the school textbook framing and the Ukrainian Lessons explainer.

## Verdict: REVISE
Critical teaching inaccuracies remain in the grammar explanation, so this cannot pass as-is even though coverage, structure, vocabulary, and exercise placement are otherwise strong.

<fixes>
- find: "Наприклад: «Якщо завтра дощитиме, то ми вирішили **залишитися** (to stay) вдома»."
  replace: "Наприклад: «Якщо завтра дощитиме, то ми залишимося вдома»."
- find: "However, another word looks similar but has a completely different function: **якби** (if only). This word introduces an unreal or hypothetical situation."
  replace: "However, another word looks similar but introduces a different type of condition: **якби** (if, hypothetically; sometimes \"if only\"). This word introduces an unreal or hypothetical situation."
- find: "It often translates to \"if only\" and expresses a strong wish about something that cannot be changed."
  replace: "In this module, treat it mainly as a marker of an unreal or hypothetical condition; in some contexts it can also mean \"if only.\""
- find: "Тому ми маємо чітко розділяти ці два важливі слова."
  replace: "Тому ми маємо чітко розділяти ці два важливі слова. Таке розрізнення реальної умови («якщо») і нереальної/гіпотетичної («якби») ви також побачите в шкільних підручниках Заболотного та в поясненні Ukrainian Lessons."
</fixes>