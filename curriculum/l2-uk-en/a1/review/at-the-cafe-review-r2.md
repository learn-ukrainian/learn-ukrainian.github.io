## Linguistic Scan
Linguistic errors found:
1. Incorrect stress on the accusative form of "вода": the text uses `воду́` instead of the correct `во́ду` (stress shift to the first syllable in accusative).
2. Typographical error with double stress marks on the word "коштує": `ко́шту́є`. Ukrainian words can only have one primary stress.

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-order -->`: Present, placed correctly after accusative patterns.
- `<!-- INJECT_ACTIVITY: quiz-cafe-phrases -->`: Present, placed correctly after menu questions.
- `<!-- INJECT_ACTIVITY: fill-in-dialogue -->`: Present, placed correctly after cafe culture.
- `<!-- INJECT_ACTIVITY: match-cafe-phrases -->`: Present, placed correctly after cafe phrases.
All four planned activities are represented by markers and placed appropriately to test what was just taught.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The text misses the explicit inclusion of the required imperfective verb `замовляти` (only the perfective `замовити` is used in a heading). All other plan points are covered. |
| 2. Linguistic accuracy | 7/10 | Contains a critical stress error for the accusative form of water (`воду́` instead of `во́ду`) and a double stress typo on `ко́шту́є`. Otherwise, gender and case usage is accurate. |
| 3. Pedagogical quality | 8/10 | Excellent grammar modeling, but suffers from redundant padding: the explanation of the bill and tips is repeated almost verbatim across two sections ("Діалоги" and "Культура кафе"). |
| 4. Vocabulary coverage | 9/10 | All required and recommended vocabulary is naturally integrated, except for the missing imperfective form of `замовляти`. |
| 5. Exercise quality | 10/10 | Exercise markers perfectly match the plan's `activity_hints` in quantity, focus, and placement. |
| 6. Engagement & tone | 10/10 | Exceptional cultural grounding. The inclusion of the 2023 Kyiv barista quote («Ми варимо каву — значить, ми живемо.») provides meaningful, decolonized context without empty cheerleader tone. |
| 7. Structural integrity | 9/10 | Markdown structure is clean and word count hits the target, but the copy-pasted cultural paragraph hurts structural flow. |
| 8. Cultural accuracy | 10/10 | Correctly distinguishes the functional and cultural differences between a кафе, ресторан, and кав'ярня in modern Ukraine. Accurately portrays tipping and billing etiquette. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues model natural, everyday exchanges for ordering and paying without sounding overly robotic. |

## Findings

[Linguistic accuracy] [critical]
Location: Section "Як замо́вити", Pattern 2 examples.
Issue: Incorrect stress on the accusative form of "вода". The stress shifts to the first syllable in the accusative case ("во́ду"), but the text uses "воду́".
Fix: Change `**Можна воду́?**` to `**Можна во́ду?**`.

[Linguistic accuracy] [critical]
Location: Section "Як замо́вити", list of essential phrases.
Issue: Typographical error with double stress marks on the word "коштує" ("Скі́льки ко́шту́є?").
Fix: Remove the second acute accent to make it "ко́штує".

[Vocabulary coverage] [major]
Location: Section "Як замо́вити", first paragraph.
Issue: The required vocabulary word "замовляти" (imperfective) is missing from the prose. Only the perfective "замовити" is used in the section heading.
Fix: Integrate the word into the introductory sentence.

[Pedagogical quality] [major]
Location: Section "Діало́ги", paragraph after the second dialogue.
Issue: The explanation of the bill and tips ("A рахунок (bill) in Ukraine doesn't come to your table automatically...") is repeated almost verbatim in the "Культура кафе" section, reading like repetitive AI padding.
Fix: Rewrite the observation in the Dialogue section to avoid repeating the exact cultural rule taught later.

## Verdict: REVISE
The module is highly engaging and culturally rich, but it contains critical linguistic errors regarding stress patterns (`воду́`, `ко́шту́є`), misses a required vocabulary lemma, and includes repetitive structural padding. These issues must be fixed before publishing.

<fixes>
- find: "**Можна воду́?**"
  replace: "**Можна во́ду?**"
- find: "**Скі́льки ко́шту́є?**"
  replace: "**Скі́льки ко́штує?**"
- find: "There are four polite ways to order at a Ukrainian **кафе**."
  replace: "When you want to order (**замовля́ти**) at a Ukrainian **кафе**, there are four polite ways to do it."
- find: "A **рахунок** (bill) in Ukraine doesn't come to your table automatically — you always ask for it. And **чайові́** (tips)? About 10% is standard, but never obligatory."
  replace: "Notice how Ростик has to ask for the **рахунок** (bill) to be brought to the table. He might also leave **чайові́** (tips) before leaving."
</fixes>
