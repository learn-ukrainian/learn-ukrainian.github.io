## Linguistic Scan
No linguistic errors found.

## Exercise Check
- `group-sort` marker only mentions `летіти` and is placed before Section 3, even though the plan required it to include `пливти` forms. This asks learners to sort forms they haven't been taught yet. It needs to be moved to after Section 3 and updated to include `пливти`.
- All other markers match the plan, have appropriate item counts, and are placed correctly after the relevant pedagogical sections.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Excellent coverage of outline points, but missing the term "злітна смуга" from the Section 4 vocabulary list. Found: "подивитися у вікно на літаки, готуючись до польоту." |
| 2. Linguistic accuracy | 9/10 | One minor calque/stylistic inconsistency: "по гучномовцю гучно і офіційно оголошується посадка". In Section 1, the text correctly used the natural "через гучномовець", but reverted to the Russian-influenced "по" construction here. |
| 3. Pedagogical quality | 9/10 | Very strong PPP flow and clear explanations. Minor factual inconsistency in the summary: the text claims "ми завжди кажемо **переплисти** *(to swim across)*, а не «перепливти»", which contradicts Section 3's accurate statement that the form with "-пливти" exists but "-плисти" is more common. |
| 4. Vocabulary coverage | 9/10 | All required and recommended words are included, but "злітна смуга" from the outline was omitted. |
| 5. Exercise quality | 8/10 | The `group-sort` marker was placed before Section 3, asking learners to sort forms of `летіти` but omitting `пливти` (contrary to the plan). This violates the rule against placing exercises before the concept is taught. |
| 6. Engagement & tone | 10/10 | Engaging tone, great contextual examples, and natural dialogues. Avoids overly corporate language. |
| 7. Structural integrity | 10/10 | All H2 headings exactly match the `content_outline`. Sections are ordered correctly. Word count is in range. |
| 8. Cultural accuracy | 10/10 | Culturally neutral, appropriate references to Boryspil, Black Sea, Odesa, and standard Ukrainian contexts. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are natural, properly formatted with named speakers, and provide excellent communicative context. |

## Findings
[1. Plan adherence] [major]
Location: Section 4 (Авіаційна та морська лексика) — "подивитися у вікно на літаки, готуючись до польоту."
Issue: The plan explicitly requires introducing the vocabulary word "злітна смуга" in this section, but it is entirely missing from the generated text.
Fix: Add "злітна смуга" to the description of the airport in Section 4.

[2. Linguistic accuracy] [minor]
Location: Section 4 — "по гучномовцю гучно і офіційно оголошується посадка *(boarding)*."
Issue: "по гучномовцю" is a stylistic calque (influenced by Russian "по громкоговорителю"). The text correctly used "через гучномовець" in Section 1, but used the calque here.
Fix: Replace "по гучномовцю" with "через гучномовець".

[3. Pedagogical quality] [minor]
Location: Section 6 — "Зверніть особливу увагу на неправильну форму: ми завжди кажемо **переплисти** *(to swim across)*, а не «перепливти»."
Issue: This is factually slightly incorrect and contradicts Section 3. Both forms exist in standard Ukrainian, but "-плисти" is preferred for euphony. "Ми завжди кажемо... а не..." is too absolute.
Fix: Soften the claim to "ми найчастіше кажемо **переплисти**".

[5. Exercise quality] [major]
Location: `<!-- INJECT_ACTIVITY: group-sort, Sort prefixed forms of летіти (прилетіти, залетіти, облетіти, etc.) by meaning category (Arrival, Direction, Limit), 12 items -->`
Issue: The `group-sort` activity marker lacks `пливти` (which was in the plan) and is placed after Section 2, before learners have been taught `пливти`.
Fix: Remove the marker from Section 2 and inject an updated version (including `пливти`) after Section 3.

## Verdict: REVISE
The module is high-quality and very well-written, featuring excellent, clear explanations of unidirectional and multidirectional verbs. However, it requires a revision to address a missing vocabulary word ("злітна смуга"), a misplaced exercise marker that violates the teaching order, and minor stylistic/factual inconsistencies ("по гучномовцю", "перепливти").

<fixes>
- find: "подивитися у вікно на літаки, готуючись до польоту."
  replace: "подивитися у вікно на літаки, які вирушають на злітну смугу *(runway)*, готуючись до польоту."
- find: "по гучномовцю гучно і офіційно оголошується"
  replace: "через гучномовець гучно і офіційно оголошується"
- find: "ми завжди кажемо **переплисти** *(to swim across)*, а не «перепливти»."
  replace: "ми найчастіше кажемо **переплисти** *(to swim across)*, а не «перепливти»."
- find: "<!-- INJECT_ACTIVITY: group-sort, Sort prefixed forms of летіти (прилетіти, залетіти, облетіти, etc.) by meaning category (Arrival, Direction, Limit), 12 items -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: quiz, Focus on choosing летіти/літати or пливти/плавати and correct prefix based on context, 8 items -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort, Sort prefixed forms of летіти and пливти by prefix meaning, 12 items -->\n<!-- INJECT_ACTIVITY: quiz, Focus on choosing летіти/літати or пливти/плавати and correct prefix based on context, 8 items -->"
</fixes>
