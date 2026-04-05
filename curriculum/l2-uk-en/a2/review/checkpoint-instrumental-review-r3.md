Now I have enough data to write the full review. Let me compile my findings.

## Linguistic Scan

All Ukrainian forms were verified against VESUM — 498/498 content words confirmed. The 7 "not found" items are proper nouns (Марія, Олег) and bare endings (-ами, -ими, -іми used as metalinguistic examples), all legitimate.

**Specific checks:**
- **ніж → ножем**: Confirmed by VESUM (`verify_lemma` shows `ножем` as `noun:inanim:m:v_oru`). Correct alternation і→о.
- **лікарем, слюсарем, столяром**: All three confirmed in VESUM. The pedagogical note about dictionary-checking is accurate.
- **грішми**: VESUM confirms both `грішми` and `грошима` as valid instrumental plural forms of `гроші`. The module teaches only `грішми` without mentioning the equally valid `грошима` — pedagogically incomplete for a review module.
- **дачею**: Confirmed in VESUM (`noun:inanim:f:v_oru:xp1`). Legitimate Ukrainian word.
- **подругою, вулицею, землею, надією, мрією**: All confirmed in VESUM. Ending categorization (hard -ою, soft/mixed -ею, vowel+я -єю) is correct.
- **життям, знанням, питанням**: All confirmed in VESUM as instrumental forms.

**Russicism/Surzhyk/Calque/Paronym checks:**
- No Russian characters (ы, э, ё, ъ) found.
- No Russianisms detected. Key words verified: пилосос (not пылесос), ганчірка (not тряпка).
- `search_style_guide` for "з його допомогою" — not flagged as calque.
- **"Я сильно захоплююся музикою"** — "сильно" exists in Ukrainian but is less natural in this collocation than "дуже". Not a Russicism per se, but a naturalness issue.

No critical linguistic errors found.

## Exercise Check

**Activity markers inventory:**
| Marker | Location | Matches plan hint? |
|--------|----------|-------------------|
| `group-sort` | End of Part 1 | ✅ Plan: "Sort Instrumental sentences by function" |
| `fill-in` | End of Part 1 | ✅ Plan: "Sentence transformation — put noun phrases into Instrumental" |
| `quiz` | End of Part 2 | ✅ Plan: "Mixed Instrumental case quiz covering all functions" |
| `error-correction` | End of Part 2 | ✅ Plan: "Find and correct grammar errors" |
| `open-ended` | End of Part 3 | ⚠️ Not in activity_hints but matches plan content_outline Ex 8 |
| `image-description` | End of Part 3 | ⚠️ Not in activity_hints but matches plan content_outline Ex 9 |
| `writing-prompt` | End of Part 3 | ⚠️ Not in activity_hints but matches plan content_outline Ex 10 |

All 4 plan `activity_hints` have corresponding markers. The 3 extra markers in Part 3 align with the plan's content_outline exercises 8-10 (open-ended questions, picture description, writing prompt). Markers are placed AFTER the relevant teaching — good sequencing. Distribution across sections is even (2 in Part 1, 2 in Part 2, 3 in Part 3).

No exercise logic issues found in inline content.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All three sections present with correct focus. Word count 1802 vs 1500 target ✅. Section word budgets reasonable. **Missing:** Required vocabulary word "вправа" (exercise) never appears — module uses "завдання" throughout. Plan's content_outline Exercise 1 ("short text about someone's day... identify all nouns in Instrumental and label each function") is not clearly represented as a distinct exercise in the prose; the group-sort marker partially covers it but the "analyze a provided text" format is absent. All other content_outline points are well covered. Textbook references (Захарійчук Grade 4 ending rules) are reflected in the content's approach. |
| 2. Linguistic accuracy | 9/10 | All forms verified via VESUM. Ending categorizations match Grade 4 Захарійчук textbook exactly (hard -ом, soft/sibilant -ем, -й stems -єм). Gender/case correct throughout. **Minor:** "Я сильно захоплююся музикою" — "сильно" is less natural than "дуже" in this collocation. грішми is valid but module omits equally valid грошима without note. |
| 3. Pedagogical quality | 8/10 | Good PPP structure: forms review → discrimination exercises → free production. 3+ examples per grammar point throughout (e.g., 3 examples each for -ом, -ем, -єм masculine endings; 3 examples for feminine -ою, -ею, -єю). The tip box on о/е alternation is helpful. **However:** For a `focus: review` checkpoint, the module leans heavily on re-teaching (explaining endings from scratch) rather than activating prior knowledge. The plan's Exercise 1 (identify-and-label in context) would better serve review pedagogy than the current form-listing approach. The з vs. bare instrumental discrimination section (Part 2) is excellent — great contrastive examples ("Я пишу ручкою" vs "Я гуляю з ручкою"). |
| 4. Vocabulary coverage | 8/10 | Required vocab used: орудний відмінок ✅, контрольна точка ✅, завдання ✅, речення ✅, відповідь ✅, текст ✅, перевірка ✅. **Missing: "вправа"** (exercise) — a required vocabulary word, never appears. Recommended vocab: правильний ✅ ("правильна відповідь"), словосполучення ✅, описати ✅, визначити ✅. New words introduced in context, not as bare lists. |
| 5. Exercise quality | 8/10 | All 4 plan activity_hints have corresponding markers, well-placed after relevant teaching. Extra Part 3 markers align with content_outline. The inline Підсумок self-check questions (4 questions with answers) provide good review reinforcement. **Deduction:** The plan calls for specific item counts (quiz: 8, fill-in: 8, group-sort: 8, error-correction: 6) — cannot verify counts since YAML is generated separately. The Part 3 writing prompt instructions are clear and well-scaffolded ("список з 6 різних конструкцій... побудуйте навколо них історію"). |
| 6. Engagement & tone | 7/10 | **Motivational openers:** "Вітаємо!" (opening word). **Gamified praise:** "Ви чудово впоралися з цією контрольною точкою!" — tells rather than shows. **Generic encouragement:** "Тепер ви повністю готові до вивчення нових тем" — could apply to any course unchanged. **Meta-commentary:** "Давайте зробимо детальний граматичний аналіз" — lecturing about what we'll do instead of doing it. **Positives:** The з/без прийменника caution box with the humorous "walking around with a pen as your friend" image is engaging and memorable. The picnic dialogue is natural and situation-grounded. The kitchen description scene in Part 3 is concrete and vivid. |
| 7. Structural integrity | 9/10 | Clean markdown. Three H2 sections matching plan + Підсумок summary. Word count 1802 (120% of 1500 target) ✅. Tip/caution/note boxes used appropriately. No stray tags or formatting artifacts. No duplicate summary sections. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms throughout. No "like Russian but..." comparisons. Examples use Ukrainian cultural context (picnic by a river, кава з цукром, Ukrainian kitchen). Decolonized approach — instrumental case taught through Ukrainian grammar tradition (Захарійчук textbook alignment), not mapped from Russian. |
| 9. Dialogue & conversation quality | 9/10 | Picnic dialogue between Олег and Марина is natural, multi-turn, with named speakers and distinct voices. Matches plan's dialogue_situation exactly (автобусом, з дітьми, з ковбасою, під деревом). Covers all instrumental functions organically. **Minor:** Could be slightly longer — only 7 lines for a module that's supposed to demonstrate all functions in connected discourse. But it accomplishes the plan's goal efficiently. |

## Findings

**[VOCABULARY COVERAGE] [MAJOR]**
Location: Entire module
Issue: Required vocabulary word "вправа" (exercise) from plan's `vocabulary_hints.required` never appears in the module. The module uses "завдання" (task) throughout but never introduces "вправа".
Fix: Replace one instance of "завдання" with "вправа" in a natural context, or add it alongside "завдання".

**[ENGAGEMENT] [MINOR]**
Location: Opening of Part 1 — "Вітаємо!"
Issue: Motivational opener. The scoring rubric deducts for motivational openers that could apply to any course.
Fix: Replace with a direct, content-focused opening.

**[ENGAGEMENT] [MINOR]**
Location: Підсумок, final lines — "Ви чудово впоралися з цією контрольною точкою! Тепер ви повністю готові до вивчення нових тем."
Issue: Gamified praise + generic encouragement. "You did great!" tells rather than shows. "You are fully ready for new topics" could apply to any course unchanged.
Fix: Replace with a concrete forward-looking statement about what the learner can now do.

**[LINGUISTIC ACCURACY] [MINOR]**
Location: Part 1 — "«Я сильно захоплююся музикою»"
Issue: "сильно" is less natural than "дуже" in this collocation with "захоплюватися". While "сильно" exists in Ukrainian, "дуже захоплююся" is more standard.
Fix: Replace "сильно" with "дуже".

**[PEDAGOGICAL QUALITY] [MINOR]**
Location: Part 1 — "гроші стають грішми (with money)"
Issue: VESUM confirms both `грішми` and `грошима` as valid instrumental plural forms. A review module should acknowledge both forms exist, especially since learners may encounter either in real texts.
Fix: Add "(або грошима)" after "грішми".

## Verdict: REVISE

The module is linguistically sound (all forms VESUM-verified, no Russianisms) and structurally complete. The main issues are: one missing required vocabulary word ("вправа"), engagement problems (motivational openers/closers), and minor naturalness issues. No critical errors that would require a rebuild. All issues are fixable with targeted find/replace.

<fixes>
- find: "Вітаємо! Це **контрольна точка**"
  replace: "Це **контрольна точка**"
- find: "Це корисне **завдання** (task) — спробуйте розповісти"
  replace: "Це корисна **вправа** (exercise) — спробуйте розповісти"
- find: "«Я сильно захоплююся музикою»"
  replace: "«Я дуже захоплююся музикою»"
- find: "**гроші** стають **грішми** (with money)"
  replace: "**гроші** стають **грішми** (або **грошима**) (with money)"
- find: "Ви чудово впоралися з цією контрольною точкою!  Тепер ви повністю готові до вивчення нових тем."
  replace: "Після цієї контрольної точки ви вмієте вживати орудний відмінок у всіх його функціях — від знарядь та супроводу до просторових прийменників і професій."
</fixes>
