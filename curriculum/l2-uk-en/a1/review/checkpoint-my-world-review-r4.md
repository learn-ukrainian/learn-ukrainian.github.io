## Linguistic Scan
Errors found:
1. **Pervasive manual stress marks** — The text includes dozens of manually injected acute accents (`U+0301`). The prompt specifically states: "Do NOT check for stress marks — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct." Their presence breaks the verification tools (causing VESUM to report 52 missing words due to token splitting) and introduces actual linguistic errors like double stresses (`ко́шту́є`, `виши́ва́нки`) and incorrect stresses (`Катя́` instead of `Ка́тя`, `писанки́` instead of `пи́санки` in plural nominative).
2. **Grammar Scope Violation (Genitive Plural)** — In A1.2, learners are only taught *nominative plurals* (plan: "Review: nominative plurals"). But the text introduces and explicitly teaches genitive plurals: "п'ять зо́шитів", "Скі́льки є книг?".
3. **Calque / Unnatural phrasing** — "Авжеж! Це українська традиція." sounds textbook-robotic for a casual street market exchange between friends.

## Exercise Check
Exercise markers are present, correctly ordered, and match the plan's activity hints exactly:
- `<!-- INJECT_ACTIVITY: quiz-gender-agreement -->` is after the Self-check section, testing what was just reviewed.
- `<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->` is correctly placed after the Dialogue.
- `<!-- INJECT_ACTIVITY: group-sort-vocabulary -->` is also after the Dialogue.
- `<!-- INJECT_ACTIVITY: quiz-singular-plural -->` is at the end of the Summary.

No missing markers; all 4 `activity_hints` are accounted for.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 4/10 | DEDUCT for: section word budgets are off by >25% (1516 vs 1200 words). The generated dialogue ignored the exact example sentences requested in the plan's `content_outline` ("Добрий день! У вас є сумки? — Так! Ця червона чи та синя..."). DEDUCT for teaching Genitive Plural ("Скільки є книг?", "п'ять зошитів") when the plan explicitly says "no morphology rules needed yet" for numbers and "nominative plurals" only. |
| 2. Linguistic accuracy | 2/10 | DEDUCT for pervasive injection of manual stress marks (`U+0301`), including double stress (`ко́шту́є`, `виши́ва́нки`) and incorrect stress (`Катя́`). This violates the project workflow and introduces hard linguistic errors. |
| 3. Pedagogical quality | 6/10 | DEDUCT for introducing Genitive Plural forms ("книг", "зошитів") while claiming "no morphology rules needed yet", confusing learners who only know nominative plurals. REWARD for good PPP flow and direct immediate confirmation in the reading section. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary from M08-M13 (стіл, книга, вікно, синій, червоний, глечик, вишиванка, etc.) is naturally integrated. |
| 5. Exercise quality | 9/10 | Markers match the plan exactly and are placed logically after the concept is taught. |
| 6. Engagement & tone | 8/10 | REWARD for direct tone in reading practice. DEDUCT for slightly robotic dialogue response ("Авжеж! Це українська традиція."). |
| 7. Structural integrity | 2/10 | DEDUCT heavily for word count (1516 is >25% over the 1200 target). DEDUCT for the widespread injection of unicode acute accents that break the deterministic pipeline. |
| 8. Cultural accuracy | 9/10 | Good use of specific cultural items (вишиванка, глечик, писанка, намисто) at a ярмарок. |
| 9. Dialogue & conversation quality | 7/10 | DEDUCT for ignoring the plan's specific dialogue lines and using an unnatural concluding response. REWARD for named speakers with a clear scenario. |

## Findings
[Structural integrity] [critical]
Location: Entire document (e.g., "Що ми зна́ємо?", "вікно́", "вели́кий")
Issue: Pervasive injection of manual stress marks (U+0301) throughout the text. This breaks the deterministic stress annotation pipeline and introduces incorrect/double stress marks (`ко́шту́є`, `виши́ва́нки`, `Катя́`). The project rules explicitly forbid manual stress marks.
Fix: Remove all U+0301 characters from the module.

[Linguistic accuracy] [critical]
Location: "Скільки вона ко́шту́є?", "виши́ва́нки"
Issue: Words have double stress marks, which is linguistically impossible/incorrect in this context.
Fix: Remove stress marks.

[Linguistic accuracy] [critical]
Location: "His friend Катя́ is helping him", "— **Катя:**"
Issue: Incorrect stress on the name "Катя". It should be "Ка́тя".
Fix: Remove stress marks.

[Pedagogical quality] [major]
Location: "Скі́льки є книг?", "п'ять зо́шитів"
Issue: Introduces Genitive Plural forms ("книг", "зошитів") while the plan strictly specifies A1.2 only covers "nominative plurals". This introduces concepts beyond the current level scope.
Fix: Rewrite examples to avoid Genitive Plural. Use nominative plurals like "два зошити", and change the question "Скільки є книг?" to avoid genitive.

[Plan adherence] [major]
Location: Entire document
Issue: Word count is 1516 words, which is 26% over the target of 1200 words.
Fix: Trim excess explanations and streamline the summary and grammar sections to hit the 1200-word target.

[Plan adherence] [major]
Location: Діало́г (Connected Dialogue)
Issue: The dialogue completely ignored the specific target sentences requested in the plan's `content_outline` ("Добрий день! У вас є сумки? — Так! Ця червона чи та синя? — Та синя...").
Fix: Rewrite the dialogue to include the specific shopping scenario sentences requested in the plan.

[Dialogue & conversation quality] [minor]
Location: "— **Катя:** Авже́ж! Це украї́нська тради́ція."
Issue: Response is stilted and textbook-robotic for a casual conversation between friends at a market.
Fix: Change to a more natural response like "Так, це дуже гарно."

## Verdict
**REJECT**

The pervasive injection of manual unicode stress marks breaks the deterministic stress pipeline and introduces critical linguistic errors (double stress on `коштує`, incorrect stress on `Катя`). Furthermore, the word count is massively over budget (+26%), the dialogue ignores the plan's explicit target sentences, and the text prematurely introduces Genitive Plural grammar. A full rebuild is required to enforce the "no stress marks" rule, respect the word budget, and adhere strictly to the A1 grammatical scope.
