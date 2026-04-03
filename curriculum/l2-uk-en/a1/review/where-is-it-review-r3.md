## Linguistic Scan
Linguistic errors found:
1. Euphony violation: "зараз в школі" (consonant + в + consonant cluster) is a harsh, unnatural cluster in Ukrainian. It must be "зараз у школі".
2. Factual error in linguistic rule: The text claims "Use в before a vowel, and use у before a consonant". This is factually incorrect for Ukrainian and contradicts the text's own examples (like "в школі", "в місті", "в Києві", which all correctly use 'в' before a consonant when following a vowel).

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in -->` marker present after Locative Case section. Matches plan (focus: Answer Де?).
- `<!-- INJECT_ACTIVITY: quiz -->` marker present after "В чи на?" section. Matches plan (focus: В or на?).
- `<!-- INJECT_ACTIVITY: match-up -->` marker present after "В чи на?" summary. Matches plan (focus: Match nominative to locative).
- `<!-- INJECT_ACTIVITY: quiz -->` marker present at the end of the module. Matches plan (focus: Where is it?).
All exercises are appropriately placed after the relevant teaching sections and match the planned hints exactly. No issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Covers all outline points perfectly, including the ULP Ep17 pattern and the Grade 4 helper word method ("you can always use the Grade 4 helper-word test: can you ask на кому? or на чому?"). |
| 2. Linguistic accuracy | 8/10 | Good overall, but contains a harsh euphony violation ("зараз в школі") and teaches a factually incorrect euphony rule ("Use в before a vowel, and use у before a consonant"). |
| 3. Pedagogical quality | 8/10 | The PPP flow is excellent, but teaching learners to "use у before a consonant" and then immediately giving them examples like "в школі" and "в Києві" creates a massive pedagogical contradiction that will confuse students. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary from the plan is naturally integrated into the dialogues and examples (школа, робота, банк, магазин, кафе, вокзал, etc.). |
| 5. Exercise quality | 10/10 | All four planned activity markers are present and placed logically after the concepts are taught. |
| 6. Engagement & tone | 10/10 | Tone is encouraging and grounded. The cultural note on "в Україні" is powerful and clear. No corporate speak or forced enthusiasm. |
| 7. Structural integrity | 8/10 | All H2 headings match the plan exactly, but the word count is 1581 words, which is significantly over (>31%) the strict 1200-word budget. |
| 8. Cultural accuracy | 10/10 | The module explicitly and correctly addresses the decolonized "в Україні" vs imperial "на Україні" distinction. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues feel natural, feature named speakers, and provide excellent contextualized examples of the locative case in use. |

## Findings
[Linguistic accuracy] [Critical]
Location: `## Місце́вий відмі́нок (The Locative Case)` — "*Brief rule:* Use **в** before a vowel, and use **у** before a consonant or to avoid awkward consonant clusters. This is the euphony rule helping the language flow smoothly, as we saw with **у банку** versus **в офісі**."
Issue: The euphony rule is factually incorrect and contradicts the module's own examples. In Ukrainian, `в` is used *after* a vowel (even before a consonant, like `живу в Києві`), not just *before* a vowel. Telling learners to use `у` before all consonants makes examples like `в школі` and `в Києві` seem like errors, causing massive confusion.
Fix: Update the brief rule to accurately reflect basic Ukrainian euphony (using `у` between consonants, and `в` after/before vowels).

[Linguistic accuracy] [Major]
Location: `## Діало́ги (Dialogues)` — "Привіт! Вона́ за́раз **в шко́лі**."
Issue: Violates Ukrainian euphony rules. "зараз" ends in a consonant, and "школі" starts with a consonant cluster. Between consonants, "у" must be used to avoid the unpronounceable cluster "з в шк".
Fix: Change `в шко́лі` to `у шко́лі`.

[Structural integrity] [Minor]
Location: Entire module
Issue: The word count is 1581 words, which significantly exceeds the plan's strict target of 1200 words (>31% overage).
Fix: No automated fix applied for word count to avoid breaking content flow, but a manual trim of the English meta-explanations in the future is recommended.

## Verdict: REVISE
The module is highly engaging and covers the locative case effectively, but the contradictory and factually incorrect euphony rule, combined with a euphony violation in the dialogue, necessitates a revision.

<fixes>
- find: "*Brief rule:* Use **в** before a vowel, and use **у** before a consonant or to avoid awkward consonant clusters. This is the euphony rule helping the language flow smoothly, as we saw with **у банку** versus **в офісі**."
  replace: "*Brief rule:* Use **в** after a vowel or before a vowel, and use **у** between consonants or to avoid awkward consonant clusters. This is the euphony rule helping the language flow smoothly, as we saw with **у банку** versus **в офісі**."
- find: "Привіт! Вона́ за́раз **в шко́лі**."
  replace: "Привіт! Вона́ за́раз **у шко́лі**."
</fixes>
