All verified. Now I have everything I need for the review.

---

## Linguistic Scan

**Russianisms:** None found. All vocabulary is standard Ukrainian.

**Surzhyk:** None found.

**Calques:** None found. "Дивитися телевізор," "дивитися фільм," "лягати спати" — all natural Ukrainian collocations.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case errors:** None found. All adjective-noun agreement is correct (гарячу каву — acc.f, холодну воду — acc.f, цікаву книгу — acc.f, нову книгу — acc.f, цікавий фільм — acc.m, типовий день — acc.m, вільний день — acc.m).

**Factual claims:** "The word обіду is the genitive form of the noun обід (lunch)" — correct. "These words are adverbs. This means their form is frozen." — correct for вранці, вдень, ввечері, вночі.

**Conjugation tables:** All forms verified against VESUM (снідаю/снідаєш/снідає, обідаю/обідаємо/обідають, лягаю/лягаєш/лягаємо, вечеряє/вечеряємо, відпочиваєте). All correct.

**One minor discrepancy with plan:** The model text says "О дванадцятій лягаю спати" but the plan specifies "О одинадцятій лягаю спати." Not a linguistic error, but a plan deviation.

No linguistic errors found.

## Exercise Check

**Exercise inventory:**

1. `:::fill-in` — "Choose the correct part of the day" (4 items) — placed after Section 2 (parts of the day). Matches plan activity_hint #3.
2. `:::match-up` — "Match the activity to the logical time of day" (8 pairs) — placed after Section 2. Matches plan activity_hint #1.
3. `:::fill-in` — "Complete the logical sequence of the day" (6 items) — placed after Section 3. Matches plan activity_hint #2.

**All 3 plan activity_hints accounted for.** ✓

**Exercise logic check:**

- Fill-in #1: All answers correct (каву=вранці, вечеряємо=ввечері, працює з 9 до 5=вдень, гуляють у парку=після обіду). ✓
- Match-up: All 8 pairs are logically correct and match the plan's specified pairs exactly. ✓
- Fill-in #2: Answers correct (Спочатку for waking, снідаю after, працюю during day, обідаю at 1:00, Потім for reading, Нарешті for bed). ✓

**Placement:** Exercises are placed after the relevant teaching content. Fill-in #1 and match-up come after parts-of-the-day teaching. Fill-in #2 comes after sequence words teaching. ✓

**Issue:** The plan's fill-in activity_hints specify multiple-choice distractors (e.g., `{Спочатку|Потім|Нарешті}`) but the `:::fill-in` DSL uses open-answer format. Per review instructions, this is likely the tool's expected format — flagging as minor.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 plan sections present with correct H2 headings. Both dialogues match plan specifications (past tense chunks in D1, буду+inf in D2). All sequence words (спочатку, потім, після того, нарешті, також, а потім, після цього) covered. Model text present. Parts of day covered. Self-check present. One minor deviation: plan says "О одинадцятій" but content says "О дванадцятій." Section budgets are all proportionally over since total is 2029 vs 1200 target, but no section is disproportionately short. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian forms verified against VESUM. Conjugation paradigms correct (снідаю/снідаєш/снідає, лягаю/лягаєш/лягаємо). Past tense forms correct (-ла for female, -в for male). Gender/case agreement verified (гарячу каву, холодну воду, цікавий фільм). No Russianisms, surzhyk, calques, or paronyms. Factual claim about обіду being genitive of обід is correct. |
| 3. Pedagogical quality | 9/10 | PPP structure clear: Present (dialogues introduce chunks), Practice (model text + examples), Produce (self-check at end). Past tense correctly presented as vocabulary chunks, not grammar — exactly per plan ("past tense grammar = M48-49"). Future буду+inf also as chunks. Conjugation review references M16 appropriately. No scope creep beyond A1. Progressive complexity within sections. |
| 4. Vocabulary coverage | 10/10 | All 7 required vocab items used naturally in prose: вранці, вдень, ввечері (Section 2 with 3 examples each), обідати, вечеряти, відпочивати (Section 3 with conjugated examples), після (throughout). All 7 recommended items present: прокидатися, вмиватися, одягатися (Section 3), вночі (Section 2), після обіду (Section 2 with cultural explanation), також (Section 3), лягати спати (Section 3 with conjugation), типовий, вільний (Section 2). Words introduced in context, not as isolated lists. |
| 5. Exercise quality | 8/10 | All 3 plan activity_hints matched by type and focus. Item counts match plan (8 pairs, 6 fill-ins, 4 fill-ins). Exercises test language skill (matching activities to time of day, choosing correct sequence words) not content recall. Correct placement after teaching. Minor: fill-in exercises lack the multiple-choice distractors specified in plan's activity_hints — open-answer is harder for A1 learners. |
| 6. Engagement & tone | 9/10 | Authoritative but warm ("Let us look at..."). No LLM filler phrases. Good cultural hook about asking about someone's day being genuine care. "після обіду" etymology/culture note is engaging. Weekend routine example at the end provides relatable contrast. Appropriate for teens/adults. |
| 7. Structural integrity | 10/10 | All 4 H2 headings from plan present in correct order. Word count 2029 ≥ 1200 target. No duplicate sections. No meta-commentary. Clean markdown with proper dialogue div wrappers. |
| 8. Cultural accuracy | 10/10 | No "like Russian but..." comparisons. Ukrainian presented on its own terms. Cultural note about lunch traditions in Ukraine is accurate and adds value. Decolonized throughout. |
| 9. Dialogue & conversation quality | 9/10 | Dialogue 1 (two friends meeting for coffee) is natural and culturally appropriate — matches plan's Як пройшов твій день pattern. Speaker roles clear (Максим asks, Олена shares). Dialogue 2 (planning tomorrow) flows naturally from D1. Not stilted. Real conversational patterns. Minor: both dialogues feature the same two speakers — slight variation would add richness, but this is cosmetic. |

## Findings

**[1. Plan adherence] [SEVERITY: minor]**
Location: Section 2, model text — "О дванадцятій лягаю спати."
Issue: Plan specifies "О одинадцятій лягаю спати" but content changed bedtime from 11:00 to 12:00.
Fix: Change to match plan exactly.

**[5. Exercise quality] [SEVERITY: minor]**
Location: All three `:::fill-in` exercises
Issue: Plan's activity_hints specify multiple-choice format with distractors (e.g., `{Спочатку|Потім|Нарешті}`) but exercises use open-answer format. For A1 learners, multiple-choice scaffolding is pedagogically preferable — open recall is significantly harder.
Fix: This is a tool/format concern. If the deterministic tool supports distractors, they should be added. Not a content fix.

## Verdict: PASS

This is a well-crafted A1 module. Linguistically flawless — all Ukrainian verified against VESUM with zero errors. Strong plan adherence across all 4 sections. Pedagogically sound with proper PPP structure, past tense and future correctly scoped as vocabulary chunks (not grammar), and conjugation review appropriately referenced to M16. All required and recommended vocabulary used naturally in prose. Exercises match plan activity_hints in type, focus, and item count. Two minor findings only (bedtime discrepancy with plan, exercise format), neither affecting shippability. No critical or major findings.
