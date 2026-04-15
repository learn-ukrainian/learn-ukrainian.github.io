## Linguistic Scan
No linguistic errors found.

## Exercise Check
Four activity markers are present, which matches the plan’s expected total count.

Placement is mostly logical:
- `fill-in` comes after `## Хотіти (To Want)`, where the `хочу / хочеш / хоче` paradigm is taught.
- `quiz` and `fill-in` come after `## Могти і мусити (Can and Must)`, where all three modals are available for contrast.
- The final `quiz` comes after `## Підсумок — Summary`.

Issue found:
- The marker IDs are not unique. `<!-- INJECT_ACTIVITY: fill-in -->` appears twice and `<!-- INJECT_ACTIVITY: quiz -->` appears twice. The plan has four distinct activity obligations, so these generic duplicate IDs do not map cleanly one-to-one to distinct exercise prompts.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All four contract sections are present and correctly ordered. Section pacing is on target: `Діалоги` 295 words, `Хотіти` 318, `Могти і мусити` 288, `Підсумок` 308. Core contract beats are covered, including `кава → каву`, `хочу + infinitive`, and the `могти / мусити` contrast. |
| 2. Linguistic accuracy | 10/10 | No Russian characters found. VESUM/tool spot checks support forms used in the module, including `Шкода`, `вільна`, `домовилися`, `порекомендувати`, and `прошу`. I found no definite Russianisms, Surzhyk, calques, paronym errors, or false grammar claims. |
| 3. Pedagogical quality | 8/10 | The module has a solid situation→pattern→practice flow, but one explanation spends too much space repeating the same point: `It communicates a strong, unavoidable personal obligation. It signifies a strong obligation or necessity... It carries a heavier weight...` That is teaching budget that could have gone to another learner-ready example. |
| 4. Vocabulary coverage | 10/10 | Required contract vocabulary is well covered in prose, including `хочеш`, `робити`, `гуляти`, `можу`, `мушу`, `працювати`, `Шкода`, `іти`, `каву`, `їсти`, `можете`, and `можуть`. |
| 5. Exercise quality | 6/10 | The module has the right number of markers, but the IDs are duplicated: `<!-- INJECT_ACTIVITY: fill-in -->` appears twice and `<!-- INJECT_ACTIVITY: quiz -->` appears twice. That makes the four distinct plan obligations ambiguous at injection time. |
| 6. Engagement & tone | 9/10 | The tone is mostly teacherly and controlled. Dialogues are concrete and useful, and the prose avoids corporate/gamified nonsense. |
| 7. Structural integrity | 10/10 | All required H2 headings are present, ordered correctly, and the pipeline word count is 1300, which clears the 1200 minimum. No stray formatting artifacts beyond the expected activity markers. |
| 8. Cultural accuracy | 10/10 | The module treats Ukrainian on its own terms and avoids Russian-comparison framing or cultural distortion. |
| 9. Dialogue & conversation quality | 9/10 | The weekend-planning dialogue is natural and multi-turn, and the café exchange closely follows the contract scenario. The café dialogue is somewhat transactional, but still usable and not robotic. |

## Findings
[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in -->` after `## Хотіти (To Want)`, `<!-- INJECT_ACTIVITY: quiz -->` and `<!-- INJECT_ACTIVITY: fill-in -->` after `## Могти і мусити (Can and Must)`, and `<!-- INJECT_ACTIVITY: quiz -->` after `## Підсумок — Summary`  
Issue: The module uses only two generic marker IDs (`fill-in`, `quiz`) for four different exercise obligations. That makes the intended mapping ambiguous for deterministic injection.  
Fix: Rename the four markers to unique IDs tied to their actual focus: one for `хотіти` conjugation, one for modal choice, one for the anchor-sentence completion, and one for regular-vs-irregular identification.

[PEDAGOGICAL QUALITY] [SEVERITY: minor]  
Location: `Understanding the conversational weight of **мусити** is vital. It communicates a strong, unavoidable personal obligation. It signifies a strong obligation or necessity, rather than a mild recommendation. It carries a heavier weight than the impersonal word **треба** (need to), which you will study later.`  
Issue: This repeats the same semantic point three times in English instead of using the space for a sharper contrast or another Ukrainian example.  
Fix: Compress the explanation to one sentence that keeps the `мусити` vs `треба` contrast without the repetition.

## Verdict: REVISE
The language and contract coverage are strong enough that this is not a reject. It is still not a pass because there are fixable quality issues, and the duplicated exercise marker IDs are a real pipeline/injection problem.

<fixes>
- find: |
    In standard conversational Ukrainian, stating **я хочу** is the direct and common way to express a want or desire. Polite conditional requests (like **хотів/хотіла би**) use different forms that you will learn later, but stating your desire directly is expected and perfectly normal here.

    <!-- INJECT_ACTIVITY: fill-in -->
  replace: |
    In standard conversational Ukrainian, stating **я хочу** is the direct and common way to express a want or desire. Polite conditional requests (like **хотів/хотіла би**) use different forms that you will learn later, but stating your desire directly is expected and perfectly normal here.

    <!-- INJECT_ACTIVITY: fill-in-conjugate-khotity -->
- find: |
    Understanding the conversational weight of **мусити** is vital. It communicates a strong, unavoidable personal obligation. It signifies a strong obligation or necessity, rather than a mild recommendation. It carries a heavier weight than the impersonal word **треба** (need to), which you will study later.
  replace: |
    Understanding the conversational weight of **мусити** is vital. It communicates a strong, unavoidable personal obligation and carries a heavier weight than the impersonal word **треба** (need to), which you will study later.
- find: |
    <!-- INJECT_ACTIVITY: quiz -->
    <!-- INJECT_ACTIVITY: fill-in -->
  replace: |
    <!-- INJECT_ACTIVITY: quiz-choose-modal -->
    <!-- INJECT_ACTIVITY: fill-in-complete-anchor -->
- find: |
    Building these sentences out loud bridges the gap between recognizing a written word and actively speaking it. Repeat the pattern aloud until you can switch quickly between **хочу**, **можу**, and **мушу** in your own sentences.

    <!-- INJECT_ACTIVITY: quiz -->
  replace: |
    Building these sentences out loud bridges the gap between recognizing a written word and actively speaking it. Repeat the pattern aloud until you can switch quickly between **хочу**, **можу**, and **мушу** in your own sentences.

    <!-- INJECT_ACTIVITY: quiz-regular-irregular -->
</fixes>