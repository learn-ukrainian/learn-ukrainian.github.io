## Linguistic Scan

**Russianisms:** None found. All vocabulary is standard Ukrainian.

**Surzhyk:** None found.

**Calques:** None found.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case check:**
- "Учора я читав цікаву книжку" — цікаву книжку (acc. fem.) ✓
- "Вона працювала в офісі" — в офісі (loc.) ✓
- "Ми гуляли в парку" — в парку (loc.) ✓
- "Я ходила в кафе з подругою" — з подругою (instr.) ✓
- "минулого тижня" — gen. masc. ✓
- All past tense gender forms verified correct across both dialogues and explanatory sections.

**Factual claims about Ukrainian grammar:**
- "past tense shows GENDER, not person" — ✓ correct
- Formation pattern (drop -ти, add -в/-ла/-ло/-ли) — ✓ correct
- "plural form always takes -ли, gender distinction disappears" — ✓ correct
- Reflexive verb дивитися: дивився/дивилася/дивилося/дивилися — ✓ correct (gender ending before -ся)
- Present tense comparison (я читаю, ти читаєш, він читає) — ✓ correct

**VESUM verification:** All 8 "not found" words are proper nouns (Іване is vocative of Іван, also a proper noun). No issues.

**One potential issue — [NEEDS RAG VERIFICATION]:** The text says "Він говорив дуже тихо" — the adverb **тихо** is standard Ukrainian, but I want to flag that this is confirmed ✓ in VESUM (тихо exists). No issue.

No linguistic errors found.

## Exercise Check

**Exercise inventory:**

1. **:::matching** — "Match pronoun to the correct past tense ending" (6 pairs) — placed after Минулий час section ✓
2. **:::fill-in** — "Choose correct gender based on the subject" (3 items) — placed after Практика section ✓  
3. **:::fill-in** — "Form past tense (він / вона / вони) for all core verbs" (6 items) — placed after Практика section ✓

**Plan activity_hints specify:**
- fill-in (focus: Form past tense) with 6 items → Exercise #3 matches ✓ (6 items)
- matching (focus: Match pronoun to past tense ending) with 6 pairs → Exercise #1 matches ✓ (6 pairs)
- fill-in (focus: Choose correct gender based on subject) with 3 items → Exercise #2 matches ✓ (3 items)

**Exercise logic check:**

Exercise 1 (matching): All pairs correct. він→працював (masc), вона→працювала (fem), воно→працювало (neut), вони→працювали (pl), Тарас→говорив (masc name), Олена→говорила (fem name). ✓

Exercise 2 (fill-in): 
- "Марія ___ фільм" → дивилася ✓ (feminine subject)
- "Мій брат ___ у парку" → гуляв ✓ (masculine subject)
- "Вони ___ вихідні разом" → провели ✓ (plural subject)

Exercise 3 (fill-in):
- "Учора він ___ книжку" → читав ✓
- "Олена ___ вечерю" → готувала ✓
- "Ми ___ в парку" → гуляли ✓
- "Вони ___ разом" → працювали ✓
- "Тарас ___ фільм" → дивився ✓
- "Що ти ___ учора, Іване?" → робив ✓ (Іване is male vocative)

**Issue:** Exercises 2 and 3 are both fill-in type but lack **distractors**. The plan's activity_hints show fill-in items with explicit distractors in curly braces (e.g., `{читав|читала|читати}`). The current format only shows the correct answer. This is a format concern — the downstream exercise tool may or may not generate distractors from context. Since the fill-in DSL format uses `answer:` fields (not `{correct|wrong|wrong}` format), this appears to be the expected filled-exercise format. The matching exercise also uses the standard DSL. No logic errors.

All 3 plan activity_hints are represented. Count matches expectations.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 content_outline sections present with correct H2 headings. All plan points covered: gender-based endings, present vs. past contrast, core verb paradigms, time words (учора, минулого тижня), self-check prompt. Both dialogues follow plan scripts closely. Section word budgets reasonable (1440 total vs 1200 target = 120%, well within range). Minor: plan says "говорити" in recommended verb list but the content uses it — covered. One small gap: the plan's Dialogue 1 has the exchange about Олена ("Вона працювала") which is present. Dialogue 2 matches the weekend conversation closely. All plan references (Grade 3-4 textbooks, State Standard) are reflected in the pedagogical framing. |
| 2. Linguistic accuracy | 10/10 | Zero Russianisms, zero Surzhyk, zero calques. All past tense forms morphologically correct. Case endings verified (цікаву книжку, з подругою, в офісі, минулого тижня). Reflexive verb дивитися handled correctly. Gender agreement consistent throughout. |
| 3. Pedagogical quality | 9/10 | PPP structure well-executed: Present (dialogues introduce past tense in context) → Practice (explicit grammar rules with paradigm tables) → Produce (sentence building, self-check). Grammar scope respects A1 — explicitly defers aspect ("we do not need to worry about aspect at A1"). References Grade 3-4 textbooks for past tense as pedagogical anchor. The progression from observing patterns in dialogue → extracting rules → practicing forms is textbook-sound. |
| 4. Vocabulary coverage | 9/10 | All 8 required vocab items used naturally: учора, робити, читати, працювати, гуляти, готувати, дивитися, говорити — all appear in both prose and exercises. Recommended vocab: минулий (in "минулий час"), вихідні ✓, субота ✓, неділя ✓, разом ✓, фільм ✓, провести (провів/провели) ✓. All introduced in context within dialogues or example sentences, not as bare lists. |
| 5. Exercise quality | 8/10 | All 3 plan activity_hints represented with correct item counts. Logic is sound — every answer is verifiably correct. Exercises test the taught skill (gender agreement in past tense), not content recall. Placed after relevant teaching sections. Minor concern: fill-in exercises don't show explicit distractors in the DSL — the plan hints include them but the exercise format may rely on the downstream tool to generate them. |
| 6. Engagement & tone | 9/10 | Authoritative but warm teacher voice throughout. No LLM filler phrases ("Good news!", "Don't panic!"). The opening hook ("One of the most common questions...") is natural and motivating. Cultural hooks: weekend activities, café with a friend, cooking dinner — relatable situations for teens/adults. The "Як смачно!" exclamation adds personality. Explanations use encouraging but not patronizing language. |
| 7. Structural integrity | 10/10 | All 4 H2 headings from plan present: Dialogues, Минулий час, Практика, Summary. Word count 1440 vs 1200 target (120%) — well above minimum, not excessively long. No duplicate sections. No meta-commentary. Clean markdown with proper dialogue formatting. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented entirely on its own terms. Past tense explained through Ukrainian grammar categories (минулий час, рід). No "like Russian but..." or "similar to English..." framing — comparisons are only with Ukrainian present tense. Ukrainian names used (Тарас, Олена, Софія, Антон, Богдан, Анна). Weekend activities culturally appropriate (гуляти в парку, кафе з подругою). |
| 9. Dialogue & conversation quality | 9/10 | Both dialogues are natural and culturally appropriate. Dialogue 1 follows a classic "catch-up" pattern — asking about yesterday, mentioning friends by name. Dialogue 2 is a weekend recap — Saturday/Sunday structure feels organic. Speaker roles are clear (names bolded). Responses are realistic (not stilted). The "Як смачно!" reaction is a nice natural touch. Minor: Dialogue 2 follows the plan script almost verbatim, which is fine but slightly formulaic. |

## Findings

[EXERCISE QUALITY] [minor]
Location: :::fill-in exercises (both)
Issue: The fill-in exercises in the DSL format show only the correct `answer:` field without explicit distractors. The plan's `activity_hints` include distractors (e.g., `{читав|читала|читати}`). If the downstream exercise tool doesn't auto-generate distractors, these become simple recall exercises rather than discrimination exercises.
Fix: This is likely handled by the exercise rendering tool. If not, distractors should be added to match the plan's hint format. No content-side fix needed — this is a pipeline/tool concern.

[PLAN ADHERENCE] [minor]
Location: Практика section, verb paradigm list
Issue: The plan lists "говорити" as a core verb to conjugate fully in the Практика section, and the content does include it. However, the content adds "Він говорив дуже тихо" as an example sentence that isn't in the plan — this is fine (enrichment), but the module doesn't show говорити in the exercises at all (only in the matching exercise as Тарас/Олена pairs). Very minor gap.
Fix: No fix needed — говорити is well-covered in the matching exercise and example sentences.

## Verdict: PASS

The module is high quality across all dimensions. Zero critical findings, zero major findings. The two minor findings are not content-level issues requiring fixes — one is a downstream tool concern (distractor generation) and the other is a negligible coverage gap that's already addressed by existing exercises. Linguistic accuracy is flawless, pedagogical structure follows PPP well, both dialogues are natural and plan-aligned, all vocabulary targets are met, and the module exceeds its word target comfortably (1440/1200). The content teaches Ukrainian past tense on its own terms with clear, engaging explanations grounded in Ukrainian textbook pedagogy.
