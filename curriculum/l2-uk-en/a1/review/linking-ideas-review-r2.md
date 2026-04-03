## Linguistic Scan
Two critical linguistic errors found regarding prescriptive grammar rules:
1. The text claims a comma is placed before `а` "when it connects two full clauses with different subjects," which implies it is not always used. In Ukrainian, a comma is virtually always required before adversative conjunctions like `а` and `але` (including between homogeneous sentence parts).
2. The text claims "The reason clause always comes second" when using `бо` or `тому що`. While this is the most common word order, it is factually incorrect to say it *always* comes second, as subordinate clauses of reason can precede the main clause in Ukrainian (e.g., "Тому що йшов дощ, ми залишилися вдома").

## Exercise Check
Two injected activity markers are placed before the required concepts are fully taught:
- `<!-- INJECT_ACTIVITY: group-sort-conjunctions -->` is placed after the first dialogue, testing `та` and `тому що` before they are formally introduced or seen in context.
- `<!-- INJECT_ACTIVITY: fill-in-choose-conjunction -->` is placed after `але`, testing `бо` before the "Бо і тому що" section has begun.
Both must be moved to the end of the module.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Missed the opening question "Що ти робив сьогодні?" from Dialogue 2. Missed the required Ukrainian grammar term "сполучники сурядності" from the Grade 4-5 approach. |
| 2. Linguistic accuracy | 6/10 | Contained two false prescriptive rules regarding comma usage before "а" and the mandatory positioning of reason clauses. |
| 3. Pedagogical quality | 8/10 | Clear examples and PPP structure, though marred slightly by the inaccurate syntax rules being taught as facts. |
| 4. Vocabulary coverage | 10/10 | All required conjunctions (`і`, `та`, `а`, `але`, `бо`, `тому що`) and question word `чому` are well integrated. |
| 5. Exercise quality | 6/10 | Exercises 1 and 4 are placed prematurely, requiring students to answer using untaught vocabulary. |
| 6. Engagement & tone | 9/10 | Engaging conversational tone, though transitions are slightly meta ("Let's look at each one in detail"). |
| 7. Structural integrity | 10/10 | All sections align with the plan; clear markdown headings. |
| 8. Cultural accuracy | 10/10 | Dialogues sound like real modern Ukrainians; no Russianisms or calques. |
| 9. Dialogue & conversation quality | 9/10 | Very natural exchanges, but Dialogue 2 starts abruptly without its contextual question. |

## Findings
[1. Plan adherence] [major]
Location: Діалоги (Dialogues)
Issue: Dialogue 2 skips the opening question "Що ти робив сьогодні?", which makes the dialogue begin abruptly and violates the plan outline.
Fix: Insert the missing question from Соня before Данило's first line.

[1. Plan adherence] [major]
Location: Сполучники (Conjunctions)
Issue: The text fails to introduce the grade 4-5 grammatical term "сполучники сурядності" (coordinating conjunctions) as explicitly requested in the plan.
Fix: Add the term "сполучники сурядності" when introducing the first set of conjunctions.

[2. Linguistic accuracy] [critical]
Location: Сполучники (Conjunctions) -> Але
Issue: The text states "The same applies before а when it connects two full clauses with different subjects." This implies commas aren't always used before "а", which is factually wrong in Ukrainian grammar.
Fix: Simplify the rule to state that a comma is always put before "але" and "а".

[2. Linguistic accuracy] [critical]
Location: Бо і тому що (Because) -> Comma rule
Issue: The text claims "The reason clause always comes second:". This is factually incorrect as reason clauses can start a sentence in Ukrainian.
Fix: Remove the false prescriptive claim.

[5. Exercise quality] [major]
Location: Throughout the text
Issue: `<!-- INJECT_ACTIVITY: group-sort-conjunctions -->` and `<!-- INJECT_ACTIVITY: fill-in-choose-conjunction -->` are placed before their respective concepts are taught, which breaks the pedagogical flow.
Fix: Move these markers to the end of the module, right before the Summary section.

## Verdict: REVISE
The module contains critical factual errors regarding Ukrainian syntax rules and places exercises prematurely. It requires revisions before publishing.

<fixes>
- find: "> — **Данило:** Я працюва́в, а по́тім ходи́в у магази́н. *(I worked, and then went to the store.)*"
  replace: "> — **Соня:** Що ти роби́в сього́дні? *(What did you do today?)*\n> — **Данило:** Я працюва́в, а по́тім ходи́в у магази́н. *(I worked, and then went to the store.)*"
- find: "One conjunction replaces an entire sentence. That's efficient.\n\n### І / Та — \"and\" (addition)"
  replace: "One conjunction replaces an entire sentence. That's efficient.\n\nIn Ukrainian schools, the first group we learn are called **сполу́чники суря́дності** (coordinating conjunctions) because they connect equal parts.\n\n### І / Та — \"and\" (addition)"
- find: "Comma rule: **always put a comma before але.** The same applies before **а** when it connects two full clauses with different subjects."
  replace: "Comma rule: **always put a comma before але** and **а**."
- find: "Always put a comma before both **бо** and **тому що**. The reason clause always comes second:"
  replace: "Always put a comma before both **бо** and **тому що**:"
- find: "every conversation.\n\n<!-- INJECT_ACTIVITY: group-sort-conjunctions -->\n\nThese four"
  replace: "every conversation.\n\nThese four"
- find: "strong contrast or limitation.\n\n<!-- INJECT_ACTIVITY: fill-in-choose-conjunction -->\n\n## Бо і тому́ що (Because)"
  replace: "strong contrast or limitation.\n\n## Бо і тому́ що (Because)"
- find: "different functions, natural flow.\n\n<!-- INJECT_ACTIVITY: quiz-which-conjunction -->\n\n## Підсумок"
  replace: "different functions, natural flow.\n\n<!-- INJECT_ACTIVITY: fill-in-choose-conjunction -->\n\n<!-- INJECT_ACTIVITY: quiz-which-conjunction -->\n\n<!-- INJECT_ACTIVITY: group-sort-conjunctions -->\n\n## Підсумок"
</fixes>
