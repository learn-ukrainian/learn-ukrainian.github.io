## Linguistic Scan
No linguistic errors found. Word order over-generalizations in the text are pedagogical simplifications, not morphological or lexical Russianisms/Surzhyk. All verb conjugations, noun declensions, and vocabulary choices are correct standard Ukrainian.

## Exercise Check
- `<!-- INJECT_ACTIVITY: match-hobby-verbs -->`: Matches plan hint "Match the verb to the logical noun (hobbies)". Appears appropriately after the "Хо́бі і спорт" teaching block.
- `<!-- INJECT_ACTIVITY: fill-in-prepositions -->`: Matches plan hint "Choose the correct preposition for the activity". Appears after the explanation of the "грати у/на" and "ходити в/на" patterns.
- `<!-- INJECT_ACTIVITY: fill-in-frequency -->`: Matches plan hint "Complete the invitations and frequency sentences". Appears appropriately after the "Як часто?" frequency adverbs section.
All 3 exercise markers from the plan are present, matching the required type/focus, and logically placed after the concepts are taught.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All sections from `content_outline` are present and follow the planned structure. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, or calques found. Gender and case endings (e.g., `на скрипці`, `в кіно`) are correct. |
| 3. Pedagogical quality | 8/10 | Good PPP flow, but the explanation of word order for `ніколи / не` and numeric frequency expressions creates factually false absolute grammar rules ("inseparable" and "must go after the verb"). |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary used naturally in context. |
| 5. Exercise quality | 10/10 | 3 injection markers exactly match the plan's 3 activity hints and test what was just taught. |
| 6. Engagement & tone | 10/10 | Natural conversational tone. Explains structures effectively without excessive fluff. |
| 7. Structural integrity | 10/10 | Clean markdown, all headings and sections ordered correctly. |
| 8. Cultural accuracy | 10/10 | Culturally appropriate conversational patterns (e.g., distinguishing between `Ходімо!` and `Давай!`). |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are natural, named speakers (`Вітя`, `Оленка`) with distinct, realistic exchanges. |

## Findings

[Pedagogical quality] [critical]
Location: Як часто? (How Often?) — `One special rule: **ніколи** always requires **не** directly before the verb. This is Ukrainian double negation — you saw it in M19. The two words are inseparable:`
Issue: The text claims that "ніколи" and "не" are "inseparable". This is factually incorrect in Ukrainian linguistics. Other words can appear between them (e.g., "Я ніколи швидко не працюю" or "Ніколи я не працюю"). While acceptable as an A1 guideline, calling them "inseparable" is a false absolute rule.
Fix: Change "The two words are inseparable:" to "They usually go together in this order:"

[Pedagogical quality] [critical]
Location: Як часто? (How Often?) — `Beyond single-word adverbs, Ukrainian uses numeric frequency expressions. These go **after the verb** — the opposite position from single-word adverbs:`
Issue: The text creates a false grammar rule that numeric frequency expressions MUST go "after the verb". This is factually wrong; Ukrainian word order is flexible, and putting them before the verb ("Я двічі на тиждень граю у футбол") is perfectly natural and common.
Fix: Change "These go **after the verb** — the opposite position from single-word adverbs:" to "These often go **after the verb** or at the end of the sentence:"

## Verdict: REVISE
The module is high-quality, conversational, and successfully introduces vocabulary and grammar patterns. However, two pedagogical simplifications cross the line into factually incorrect grammatical rules regarding absolute word order. These are critical errors that must be fixed before publishing.

<fixes>
- find: "One special rule: **ніколи** always requires **не** directly before the verb. This is Ukrainian double negation — you saw it in M19. The two words are inseparable:"
  replace: "One special rule: **ніколи** always requires **не** before the verb. This is Ukrainian double negation — you saw it in M19. They usually go together in this order:"
- find: "Beyond single-word adverbs, Ukrainian uses numeric frequency expressions. These go **after the verb** — the opposite position from single-word adverbs:"
  replace: "Beyond single-word adverbs, Ukrainian uses numeric frequency expressions. These often go **after the verb** or at the end of the sentence:"
</fixes>
