## Linguistic Scan
1 linguistic error found:
- Russian calque / Semantic error: `масло (butter — also used for oil; context tells you which)`. This is a critical factual error. In Ukrainian, `масло` refers exclusively to animal fat (butter), while `олія` refers to liquid plant fat (oil). Treating them as the same word depending on context is a direct transfer of Russian semantics (`масло` means both in Russian). 

## Exercise Check
- Marker IDs match the `activity_hints` from the plan.
- The DSL formats and exercise logic match the expected output.
- **ISSUE**: All four `<!-- INJECT_ACTIVITY -->` markers are clustered consecutively at the end of the `Напої` section. This violates the rule against clustering exercises at the end and tests concepts out of rhythm with the prose.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covers all required points and communicative situations, but failed to embed the required target word `їжа` natively into the prose (used only as a header). |
| 2. Linguistic accuracy | 7/10 | CRITICAL ERROR: The text teaches a Russianism by claiming `масло` is also used for oil depending on context. (СУМ-11 confirms `масло` = animal fat, `олія` = plant fat). Otherwise, good use of cases and vocabulary. |
| 3. Pedagogical quality | 9/10 | Excellent breakdown of grammar as chunks (PPP applied effectively). Slight deduction due to the clustering of activity markers out of logical sequence. |
| 4. Vocabulary coverage | 9/10 | All recommended items used. Deduction because the required core word `їжа` was only used in a heading, not contextualized in the prose. |
| 5. Exercise quality | 8/10 | Exercises are well-formed logically, but the placement is flawed. `match-food-drink` and `group-sort` belong before the `з + noun` section, not clustered with the others at the very end. |
| 6. Engagement & tone | 9/10 | Rich cultural notes (UNESCO, Kotliarevsky), but includes minor meta-commentary: "These next words are not just vocabulary — they are symbols of Ukrainian identity." |
| 7. Structural integrity | 9/10 | Headings match the plan perfectly. The block of 4 consecutive markers slightly disrupts the visual flow. |
| 8. Cultural accuracy | 10/10 | Superb context around Borshch, Salo, and Varenyky. Strong decolonized framework. |
| 9. Dialogue & conversation quality | 9/10 | Logical flaw in Dialogue 1: Marco exclaims "Смачно! Дякую." (Delicious!) immediately after Olenka says "The porridge is on the stove," meaning he reacts to the taste before eating it. |

## Findings
[Linguistic accuracy] [critical]
Location: `**масло** (butter — also used for oil; context tells you which)`
Issue: Critical Russianism/Factual Error. In Ukrainian, "масло" is strictly animal fat (butter), while "олія" is plant-based fat (oil). Claiming "масло" is used for both is teaching Russian semantics as Ukrainian.
Fix: Remove the incorrect parenthetical note.

[Vocabulary coverage] [minor]
Location: `Food is woven into Ukrainian daily life...`
Issue: The required vocabulary word "їжа" (food) is not explicitly introduced in the prose text, only appearing as a section header.
Fix: Introduce it naturally in the opening sentence.

[Dialogue & conversation quality] [minor]
Location: `> **Оленка:** Добре. Каша на плиті. *(Good. The porridge is on the stove.)* \n> **Марко:** Смачно! Дякую. *(Delicious! Thanks.)*`
Issue: Logical flaw. Marco exclaims "Delicious!" when the porridge is still on the stove and he hasn't tasted it yet.
Fix: Change Marco's response to "Супер! Дякую."

[Exercise quality] [major]
Location: `<!-- INJECT_ACTIVITY: fill-in-z-chunks -->` through `<!-- INJECT_ACTIVITY: quiz-meals-dishes -->`
Issue: All four activity markers are clustered together at the end of the "Напої" section. They should be distributed after the relevant concepts are taught.
Fix: Move the `match-food-drink` and `group-sort-food-drinks` markers before the `How «з + noun» works at A1` subsection.

[Engagement & tone] [minor]
Location: `These next words are not just vocabulary — they are symbols of Ukrainian identity.`
Issue: Meta-commentary ("telling instead of showing"). The cultural importance should be self-evident from the excellent descriptions of the dishes.
Fix: Delete the sentence.

## Verdict: REVISE
The module has a critical linguistic error teaching Russian semantics for the word "масло" instead of distinguishing it from "олія". The clustering of activities and the logical hiccup in the dialogue also require straightforward deterministic fixes. 

<fixes>
- find: "**масло** (butter — also used for oil; context tells you which)"
  replace: "**масло** (butter)"
- find: "Food is woven into Ukrainian daily life"
  replace: "Food (**їжа**) is woven into Ukrainian daily life"
- find: |
    > **Оленка:** Добре. Каша на плиті. *(Good. The porridge is on the stove.)*
    > **Марко:** Смачно! Дякую. *(Delicious! Thanks.)*
  replace: |
    > **Оленка:** Добре. Каша на плиті. *(Good. The porridge is on the stove.)*
    > **Марко:** Супер! Дякую. *(Super! Thanks.)*
- find: |
    :::

    These next words are not just vocabulary — they are symbols of Ukrainian identity.

    **Борщ** — the national dish
  replace: |
    :::

    **Борщ** — the national dish
- find: |
    **Алкогольні напої** (for recognition only): **пиво** (beer), **вино** (wine).

    ### How «з + noun» works at A1
  replace: |
    **Алкогольні напої** (for recognition only): **пиво** (beer), **вино** (wine).

    <!-- INJECT_ACTIVITY: match-food-drink -->

    <!-- INJECT_ACTIVITY: group-sort-food-drinks -->

    ### How «з + noun» works at A1
- find: |
    Recognizing the pattern is enough at A1.
    :::

    <!-- INJECT_ACTIVITY: fill-in-z-chunks -->

    <!-- INJECT_ACTIVITY: match-food-drink -->

    <!-- INJECT_ACTIVITY: group-sort-food-drinks -->

    <!-- INJECT_ACTIVITY: quiz-meals-dishes -->

    ## Підсумок — Summary
  replace: |
    Recognizing the pattern is enough at A1.
    :::

    <!-- INJECT_ACTIVITY: fill-in-z-chunks -->

    <!-- INJECT_ACTIVITY: quiz-meals-dishes -->

    ## Підсумок — Summary
</fixes>
