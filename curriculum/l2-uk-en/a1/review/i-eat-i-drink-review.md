## Linguistic Scan

Cannot meaningfully scan — the module contains only section headers and word-budget annotations, not actual prose. The ~8 lines of "content" are outline stubs, not teaching material. No Ukrainian prose exists to check for Russianisms, Surzhyk, calques, or paronyms.

No linguistic errors found in the header text itself (section titles are correct Ukrainian).

## Exercise Check

**No exercises found.** Zero `:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, or `:::true-false` blocks exist in the content. The plan specifies 4 activity blocks (2× fill-in, 1× quiz, 1× group-sort) with 30 total items. None were generated.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 1/10 | Content is section headers only. Zero of the plan's content_outline points are covered. No dialogues, no conjugation tables, no accusative explanation, no summary. 102/1200 words = 8.5% of target. |
| 2. Linguistic accuracy | 5/10 | Cannot evaluate — no prose exists. Section titles are linguistically correct but there's nothing substantive to review. Neutral score. |
| 3. Pedagogical quality | 1/10 | No teaching occurs. No PPP structure. No examples, no explanations, no practice. A learner would learn nothing from this module. |
| 4. Vocabulary coverage | 1/10 | None of the required vocabulary (їсти, пити, каву, воду, рибу) appears in teaching context. Only section-header mentions. |
| 5. Exercise quality | 1/10 | Zero exercises generated. Plan requires 4 activity blocks with 30 items. |
| 6. Engagement & tone | 1/10 | No content to engage with. Headers with word counts are not teaching material. |
| 7. Structural integrity | 1/10 | H2 headings match the plan, but contain zero content beneath them. 102 words vs 1200 target = 91.5% under. |
| 8. Cultural accuracy | 5/10 | Nothing to evaluate — no claims made, no content presented. Neutral score. |
| 9. Dialogue & conversation quality | 1/10 | Plan requires two dialogues (breakfast + lunch). Zero dialogues exist. |

## Findings

```
[STRUCTURAL INTEGRITY] [SEVERITY: critical]
Location: Entire module
Issue: Module contains 102 words against a 1200-word target (91.5% under). Content is section headers with word-budget annotations, not actual prose. The write phase appears to have failed — only the skeleton/outline was emitted, not the teaching content.
Fix: Full rebuild required. The writer must generate actual prose for all four sections.

[EXERCISE QUALITY] [SEVERITY: critical]
Location: Entire module
Issue: Zero exercises exist. The plan specifies 4 activity blocks (2× fill-in with 8 items each, 1× quiz with 6 items, 1× group-sort with 8 items = 30 total items). None were generated.
Fix: Full rebuild required. Writer must generate exercise placeholders for all 4 planned activities.

[PLAN ADHERENCE] [SEVERITY: critical]
Location: Section "Діалоги (Dialogues)"
Issue: Plan requires two full dialogues — breakfast conversation showing full conjugation of їсти/пити, and lunch conversation with plural subjects. Neither dialogue exists.
Fix: Full rebuild required.

[PLAN ADHERENCE] [SEVERITY: critical]
Location: Section "Їсти і пити (To Eat and To Drink)"
Issue: Plan requires full conjugation paradigms for їсти (irregular) and пити (Group I), plus the "що?" accusative question trigger from Grade 4 textbooks. None of this content exists.
Fix: Full rebuild required.

[PLAN ADHERENCE] [SEVERITY: critical]
Location: Section "Знахідний відмінок — неживе (Accusative Inanimate)"
Issue: Plan requires detailed accusative inanimate rules with examples for all three genders (masculine no change, neuter no change, feminine -а→-у / -я→-ю). No teaching content exists.
Fix: Full rebuild required.
```

## Verdict: REJECT

**5 critical findings.** The module is empty — it contains only section headers with word-budget annotations, not actual teaching content. 102 words out of 1200 target (8.5%). Zero exercises out of 4 required. Zero dialogues out of 2 required. This is not a content quality problem — it's a build failure. The write phase did not produce output. The module needs a complete rebuild from the write step.

No `<fixes>` block — find/replace cannot add 1,100 words of missing prose and 30 exercise items. Re-run the build pipeline from the `write` step.
