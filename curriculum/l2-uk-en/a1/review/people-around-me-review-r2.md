## Linguistic Scan
No linguistic errors found.

## Exercise Check
All plan `activity_hints` have corresponding markers.
However, two markers are injected before the concepts they test are formally taught:
- `fill-in-animate-accusative` tests both masculine and feminine forms but is placed before the rule section.
- `fill-in-family-friends` tests dialogue sentences and masculine forms but is placed immediately before the masculine rule is taught.
Count is adequate (4).

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | The module strictly follows the `content_outline`, hitting the 1200 word target (1242 words) and covering all grammatical points (masculine genitive=accusative, whom vs what). |
| 2. Linguistic accuracy | 10/10 | Perfect grammatical explanations. Properly distinguishes `кого?` vs `що?`. Accurately cites textbook rules (Заболотний, Караман). Phrases like "Я чекаю лікаря" and "Я чекаю його" are natural and correct. |
| 3. Pedagogical quality | 8/10 | Very strong PPP flow, but DEDUCT for exercises placed before the concept is taught. Specifically, `fill-in-animate-accusative` and `fill-in-family-friends` are placed too early in the text. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary (`бачити`, `знати`, `любити`, `чекати`, `шукати`, `друг`, `подруга`) is naturally integrated into the prose. Some recommended words (`колега`, `викладач`, `продавець`) are absent from the prose. |
| 5. Exercise quality | 8/10 | DEDUCT for exercises placed before the concept is taught. `fill-in-family-friends` tests masculine forms but is injected before the masculine rule is taught. |
| 6. Engagement & tone | 10/10 | Excellent integration of the Ukrainian school curriculum approach (Grade 4 mnemonic). The conversational examples (wedding photos, colleagues at work) feel natural and authentic. |
| 7. Structural integrity | 9/10 | Clean markdown, but DEDUCT for the inclusion of meta-commentary at the very end (`**Deterministic word count: 1242 words**...`). |
| 8. Cultural accuracy | 10/10 | Accurately references Ukrainian grade school linguistics methodology. Zero Russianisms or Surzhyk. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue "Ходімо, я тебе познайомлю" and the workplace chat are highly natural, with culturally appropriate multi-turn exchanges. |

## Findings
[Exercise quality] [Major]
Location: `<!-- INJECT_ACTIVITY: fill-in-animate-accusative -->` and `<!-- INJECT_ACTIVITY: fill-in-family-friends -->`
Issue: `fill-in-animate-accusative` tests both masculine and feminine forms but is placed after "Кого? (Whom?)" before the rules are explicitly taught. `fill-in-family-friends` tests masculine dialogue forms but is placed immediately before the masculine rule.
Fix: Move `fill-in-family-friends` after the Dialogues section. Move `fill-in-animate-accusative` to the end of the "Знахідний відмінок — живе" section.

[Structural integrity] [Minor]
Location: `**Deterministic word count: 1242 words** (calculated by pipeline, do NOT estimate manually)`
Issue: The module contains leftover meta-commentary from the LLM prompt.
Fix: Remove the meta-commentary line.

## Verdict: REVISE
The module is linguistically and pedagogically excellent, but has a Major issue with activity marker placement breaking the pedagogical sequence, plus a Minor issue with a stray meta-commentary string.

<fixes>
- find: "accusative case) with animate nouns — **кого?**\n\n## Кого? (Whom?)"
  replace: "accusative case) with animate nouns — **кого?**\n\n<!-- INJECT_ACTIVITY: fill-in-family-friends -->\n\n## Кого? (Whom?)"
- find: "Compare: **кава → каву**, **мама → маму** — identical ending. Feminine animate accusative requires no new rule at all.\n\n<!-- INJECT_ACTIVITY: fill-in-family-friends -->\n\nNow the rule that matters most in this module."
  replace: "Compare: **кава → каву**, **мама → маму** — identical ending. Feminine animate accusative requires no new rule at all.\n\nNow the rule that matters most in this module."
- find: "The accusative of **брат** is **брата** — exactly like **нема́ брата** (there is no brother). The next section shows this pattern in full.\n\n<!-- INJECT_ACTIVITY: fill-in-animate-accusative -->\n\n## Знахідний відмінок — живе́ (Accusative Animate)"
  replace: "The accusative of **брат** is **брата** — exactly like **нема́ брата** (there is no brother). The next section shows this pattern in full.\n\n## Знахідний відмінок — живе́ (Accusative Animate)"
- find: "The test you should apply every time: before writing the form, ask the question. **Кого?** → take the genitive form. **Що?** → leave masculine as is.\n\n<!-- INJECT_ACTIVITY: group-sort-animate-inanimate -->"
  replace: "The test you should apply every time: before writing the form, ask the question. **Кого?** → take the genitive form. **Що?** → leave masculine as is.\n\n<!-- INJECT_ACTIVITY: fill-in-animate-accusative -->\n\n<!-- INJECT_ACTIVITY: group-sort-animate-inanimate -->"
- find: "<!-- INJECT_ACTIVITY: quiz-accusative-animate -->\n\n**Deterministic word count: 1242 words** (calculated by pipeline, do NOT estimate manually)"
  replace: "<!-- INJECT_ACTIVITY: quiz-accusative-animate -->"
</fixes>
