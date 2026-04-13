## Linguistic Scan
No confirmed Russianisms, Surzhyk forms, calques, paronym errors, or forbidden Russian letters.

Problems found:
- `У чи В?` section: `"The core rule of the **у/в** alternation is beautifully simple: avoid consonant clusters at all costs."` This is too absolute; Ukrainian does not avoid all consonant clusters, only awkward ones in euphonic alternation.
- `У чи В?` section: `"prefixes like **уже/вже**"` is a grammatical terminology error. `уже/вже` are standalone word variants here, not prefixes.
- `Підсумок — Summary`: `"the absolute sentence-start exceptions ... where the rule of surrounding sounds does not apply"` is factually wrong. School-textbook rules still choose sentence-initial `у/в` and `і/й` by the following sound.

## Exercise Check
All 4 planned markers are present, correctly named, and placed after the relevant teaching:
`quiz-u-or-v`, `quiz-i-or-y`, `fill-in-z-iz-zi`, `quiz-euphony-comparison`.

They are spread sensibly through the module, and the marker IDs match the plan’s `activity_hints`. No exercise-placement or marker-coverage issues found. No inline DSL exercises were provided, so distractor logic cannot be audited here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections appear in order, and the planned vocabulary is present in prose (`Київ`, `Львів`, `офіс`, `парк`, `театр`). But the plan’s textbook anchors are not integrated: `Авраменко` and `Літвінова` do not appear in the module text. |
| 2. Linguistic accuracy | 6/10 | Two factual teaching errors: `"prefixes like **уже/вже**"` mislabels the forms, and `"absolute sentence-start exceptions ... surrounding sounds does not apply"` contradicts textbook rules for sentence-initial `в/у` and `і/й`. |
| 3. Pedagogical quality | 7/10 | The module has many examples and a decent teach-then-practice flow, but `"avoid consonant clusters at all costs"` and the inaccurate summary sentence teach an over-rigid model of euphony. |
| 4. Vocabulary coverage | 9/10 | All required alternations are central throughout, and all recommended items are used naturally: `Київ`, `Львів`, `офіс`, `парк`, `театр`. |
| 5. Exercise quality | 9/10 | The four markers match the plan exactly and follow the relevant sections in the right order. |
| 6. Engagement & tone | 7/10 | Readable teacher voice, but there is filler and generic uplift in lines like `"signature musical flow"` and `"your instincts are already perfectly aligning with Ukrainian euphony."` |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly, the inject markers are clean, and the pipeline word count is 1469, above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module explains Ukrainian on its own terms and avoids Russian-centered framing. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers and target forms are clear (`Я живу в Києві` / `Я живу у Львові`, `Ти й Олена` / `я і Максим`), though the dialogues are more illustrative than vivid. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `The core rule of the **у/в** alternation is beautifully simple: avoid consonant clusters at all costs.` / `This rule applies to the alternating preposition **у/в** and even to common prefixes like **уже/вже** (already).`  
Issue: The explanation is too absolute, and `уже/вже` are mislabeled as prefixes.  
Fix: Replace this with a more precise formulation: Ukrainian uses `у/в` to avoid awkward clusters and preserve smooth pronunciation; `уже/вже` should be described as word variants, not prefixes.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Do not forget the absolute sentence-start exceptions, such as **У мене є...** and **І він...**, where the rule of surrounding sounds does not apply because there is no preceding word.`  
Issue: This teaches the wrong rule. At sentence start, the choice still depends on the following sound; textbook material also allows sentence-initial `й` before a vowel.  
Fix: Replace the sentence with an accurate summary of sentence-initial usage: `У` before a consonant, `В` before a vowel, `І` before a consonant, `Й` before a vowel.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Rule-introduction paragraphs in `У чи В? (У or В?)` and `І чи Й? З, із, чи зі?`  
Issue: The plan explicitly anchors the module to `Авраменко Grade 5, p.117-118` and `Літвінова Grade 5, p.174-177`, but those references are not cited in the prose. Text search confirms 0 occurrences of `Авраменко` and 0 of `Літвінова`.  
Fix: Add brief source attributions in the opening rule paragraphs for `у/в` and `і/й, з/із/зі`.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `If you confidently chose **в**, **й**, and **зі**, your instincts are already perfectly aligning with Ukrainian euphony. The fundamental secret to mastering these rules is not treating them like rigid math equations, but rather constantly reading your sentences aloud.`  
Issue: This is filler-heavy and spends words on motivational phrasing instead of instruction.  
Fix: Compress it into a shorter, practice-focused close.

## Verdict: REVISE
Critical factual issues are present in the grammar explanation, so the module cannot ship as-is. The structure and exercise placement are solid, but the rule wording needs deterministic fixes.

<fixes>
- find: "The core rule of the **у/в** alternation is beautifully simple: avoid consonant clusters at all costs."
  replace: "As Авраменко Grade 5 (pp. 117-118) presents it, the core rule of the **у/в** alternation is simple: avoid awkward consonant clusters and keep pronunciation smooth."
- find: "This rule applies to the alternating preposition **у/в** and even to common prefixes like **уже/вже** (already)."
  replace: "This rule applies to the alternating preposition **у/в** and also appears in word variants like **уже/вже** (already)."
- find: "Just as prepositions alternate to preserve rhythm, the Ukrainian conjunction for \"and\" alternates between **і** and **й**."
  replace: "As Літвінова Grade 5 (pp. 176-177) shows, the Ukrainian conjunction for \"and\" alternates between **і** and **й** to preserve rhythm."
- find: "Do not forget the absolute sentence-start exceptions, such as **У мене є...** and **І він...**, where the rule of surrounding sounds does not apply because there is no preceding word."
  replace: "At the start of a sentence, there is no preceding word, so the choice depends on the following sound: **У мене є...** before a consonant, **В Одесі...** before a vowel, **І він...** before a consonant, and **Й учимося...** before a vowel."
- find: "If you confidently chose **в**, **й**, and **зі**, your instincts are already perfectly aligning with Ukrainian euphony. The fundamental secret to mastering these rules is not treating them like rigid math equations, but rather constantly reading your sentences aloud. If a sentence feels difficult, clunky, or harsh to pronounce, you likely need to apply an alternation. Keep practicing out loud, and soon these smooth transitions will become entirely automatic."
  replace: "If you chose **в**, **й**, and **зі**, you applied the core patterns correctly. Keep reading your sentences aloud: if one version is harder to pronounce, test the alternation and choose the smoother form."
</fixes>