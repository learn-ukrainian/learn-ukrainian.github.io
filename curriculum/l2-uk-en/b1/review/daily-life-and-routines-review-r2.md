## Linguistic Scan
Two critical linguistic errors found:
1. Semantic error: "себе ви підводите" is used to explain the analytic meaning of "підводитися". However, "підводити себе" means "to let oneself down" / "to compromise oneself". It does not mean "to stand up" or "to raise oneself".
2. Grammatical case error: "За чверть дев'ята" (nominative) is incorrectly used as an adverbial of time answering "Коли?" instead of "За чверть до дев'ятої".

## Exercise Check
- `<!-- INJECT_ACTIVITY: daily-routine-fill-in -->` — Present, placed correctly after the morning routine section. Matches plan.
- `<!-- INJECT_ACTIVITY: household-chores-match -->` — Present, placed correctly after the chores section. Matches plan.
- `<!-- INJECT_ACTIVITY: daily-life-error-correction -->` — Present, placed correctly after the chores section (which covers the *стирати / *пилесос errors). Matches plan.
- `<!-- INJECT_ACTIVITY: sentence-builder-conditionals -->` — Present, placed correctly after the weekend planning conditionals section. Matches plan.
- `<!-- INJECT_ACTIVITY: quiz-grammar-choice -->` — Present, placed correctly after the reading passage. Matches plan.

Total: 5 activities as required. The distribution and focus perfectly map to the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Flawless mapping to the content outline. Incorporates the "day in my life" vlog concept ("Снідаю теплою кашею", "їду на роботу трамваєм"). All 4 dialogue situations and every single recommended vocabulary word are fully integrated. |
| 2. Linguistic accuracy | 8/10 | Very strong overall, but contains two critical errors that must be patched. "себе ви підводите" incorrectly teaches a Russian-style analytic reflexive (in Ukrainian "підводити себе" means "to let oneself down"). "**За чверть дев'ята** я спускаюся" mistakenly uses the nominative case for a temporal clause instead of the correct "За чверть до дев'ятої". |
| 3. Pedagogical quality | 9/10 | The explanation of "відпочивати" never taking "-ся" is fantastic and anticipates a very common learner error. The explanation of prefixes (за-, пере-, об-, до-) is clear and effectively contextualized. Lost one point due to the confusing "себе ви підводите" breakdown when attempting to explain reflexives. |
| 4. Vocabulary coverage | 10/10 | All required words (розпорядок дня, хатні справи, обов'язки, співбесіда, etc.) and recommended words (бутерброд, каша, велосипед, etc.) are integrated smoothly in communicative contexts without feeling like forced lists. |
| 5. Exercise quality | 10/10 | All 5 required exercise markers are present, mapped correctly to the plan's specs, and perfectly placed immediately following the grammatical/lexical concepts they are meant to test. |
| 6. Engagement & tone | 10/10 | Professional yet warm teacher persona. Transitions like "Давайте уважно подивимося" and "Зверніть увагу" are perfectly balanced without resorting to generic or gamified filler. |
| 7. Structural integrity | 10/10 | Word count is 4700 (comfortably exceeding the 4000 target). All H2 headings map cleanly to the plan. No trailing tags or markdown errors. |
| 8. Cultural accuracy | 10/10 | Brilliant decolonization points: explicitly teaches learners to avoid the Russianisms *стирати and *пилесос. Captures modern Ukrainian gender-balanced household dynamics naturally ("партнери намагаються рівномірно ділити..."). |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are highly authentic and rich in targeted grammar. Roommates hurrying in the morning, polite requests between colleagues, and family chore distribution all feature clear, distinct voices. |

## Findings

[2. Linguistic accuracy] [critical]
Location: Section "Мій день: ранок" — "Порівняйте цю різницю: ви можете підняти важку сумку з підлоги або підняти руку на уроці, але себе ви підводите або піднімаєтеся."
Issue: Using the analytic construction "себе ви підводите" to explain the reflexive "підводитися" is semantically wrong. In Ukrainian, "підводити себе" means "to let oneself down" or "to compromise oneself", not "to raise oneself".
Fix: Replace the phrase with "але самі ви підводитеся або піднімаєтеся."

[2. Linguistic accuracy] [critical]
Location: Section "Мій день: ранок" — "**За чверть дев'ята** *(at a quarter to nine)* я вже спускаюся в глибоке метро і їду на роботу."
Issue: "За чверть дев'ята" is the nominative form used strictly to answer "Котра година?" (What time is it?). To answer "Коли?" (At what time?), the sentence requires the genitive case with a preposition: "За чверть до дев'ятої".
Fix: Replace with "**За чверть до дев'ятої** *(at a quarter to nine)* я вже спускаюся в глибоке метро і їду на роботу."

## Verdict: REVISE
The writer produced an incredibly rich, pedagogically sound, and engaging module that hits every single plan requirement. The explanations of verb aspect and reflexives are highly tailored and culturally accurate. However, it contains a critical semantic error ("підводити себе") and a time-expression case error ("За чверть дев'ята я спускаюся"). These must be fixed via the deterministic find/replace pairs below before the module can ship.

<fixes>
- find: "але себе ви підводите або піднімаєтеся."
  replace: "але самі ви підводитеся або піднімаєтеся."
- find: "**За чверть дев'ята** *(at a quarter to nine)* я вже спускаюся в глибоке метро і їду на роботу."
  replace: "**За чверть до дев'ятої** *(at a quarter to nine)* я вже спускаюся в глибоке метро і їду на роботу."
</fixes>