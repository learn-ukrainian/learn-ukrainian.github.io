All words confirmed. Proper nouns (Олена, Дмитро, Анна, Наталя, Михайло) all verified in VESUM. No calque/Russicism flags from the style guide. Let me now write the full review.

---

## Linguistic Scan

**Russianisms:** None found. "Звичайно" is genuine Ukrainian (not a Russicism — конечно would be).
**Surzhyk:** None found.
**Calques:** One punctuation calque — Oxford comma before "і" in a list (English habit, not Ukrainian).
**Paronyms:** None found.
**Russian characters (ы, э, ё, ъ):** None found.
**Gender/case errors:** All accusative forms verified correct. Masculine inanimate = nominative (борщ, хліб, суп, сік, чай, сир). Feminine -а→-у, -я→-ю (каву, воду, піцу, кашу, яєчню). Masculine animate = genitive (брата, лікаря, друга, вчителя). All vocatives correct (Олено, Дмитре).

**One error found:**
- "Анна купує **хліб** (bread), **сир** (cheese), **яблука** (apples), **і** **салат** (salad)." — Comma before "і" in a simple enumeration is incorrect Ukrainian punctuation (Правопис 2019, §158: no comma before final conjunction in simple homogeneous lists). This is an English punctuation calque.

## Exercise Check

**Markers found (4):**
1. `<!-- INJECT_ACTIVITY: quiz-accusative-check -->` — after Що ми знаємо section ✓ (matches plan hint 1: quiz, accusative check)
2. `<!-- INJECT_ACTIVITY: fill-in-cafe-market -->` — after Читання section ✓ (matches plan hint 2: fill-in, café + market dialogue)
3. `<!-- INJECT_ACTIVITY: group-sort-accusative -->` — after Граматика section ✓ (matches plan hint 3: group-sort, inanimate vs animate)
4. `<!-- INJECT_ACTIVITY: quiz-shopping-cafe -->` — after Діалог section ✓ (matches plan hint 4: quiz, shopping/café situations)

**Placement:** Well-distributed — one after each teaching section. Each tests what was just taught. All 4 plan `activity_hints` have corresponding markers.

**Exercise logic (from plan hints):**
- Quiz 1: All accusative answers correct (салат✓, брата✓, воду✓, Олену✓, борщ✓, друга✓, хліб✓, лікаря✓, піцу✓, маму✓). Distractors plausible (wrong case forms). Answer positions varied (not all at index 0). ✓
- Fill-in: Correct answers in braces match grammar taught (кашу✓, коштують✓, гривень✓, кілограм✓, Мені✓, карткою✓, Олену✓, брата✓). "Меня" as distractor is Russian — deliberate wrong answer (acceptable for exercise). ✓
- Group-sort: Inanimate (борщ, хліб, сік, чай, сир) vs Animate (брата, лікаря, сусіда, друга, вчителя). 5:5 ratio — balanced. ✓
- Quiz 2: Situational matching — all correct answers are appropriate phrases. ✓

No exercise logic errors found.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 5 `content_outline` sections present and well-covered. Що ми знаємо covers all 5 can-do checks (M36–M40). Читання follows the Anna scenario exactly (market → café → meets friend → introduces brother). Граматика covers all 6 plan patterns grouped into 4 (food chunks, acc. inanimate, ordering/prices, acc. animate). Діалог matches plan's day scenario with specific lines (сніданок, ринок, кафе). Підсумок lists all 5 achievement bullets + A1.7 teaser. Minor: `dialogue_situations` specified a вечеря dinner party scenario with Господиня/Гості, but content follows the `content_outline`'s breakfast-market-café day instead — content_outline takes precedence. |
| 2. Linguistic accuracy | 9/10 | All case forms verified correct via VESUM. Accusative examples: кашу, каву, воду, піцу, борщ, хліб, Олену, брата, Дмитра — all correct. Vocatives: Олено, Дмитре — confirmed. Instrumental: карткою, сметаною, сиром, молоком — correct. Verb forms: прокидається, їсть, п'є, купує, бачить, підходить, обідають — all verified. One punctuation error: Oxford comma before "і" in "яблука (apples), і салат" — not Ukrainian standard. |
| 3. Pedagogical quality | 9/10 | Checkpoint structure follows a natural review flow: self-assessment → reading comprehension → grammar reference → connected dialogue → summary. Every grammar point has 3+ Ukrainian examples (Pattern 2 alone has 8 examples in the table + sentences). PPP respected: the Що ми знаємо section presents situations, Граматика shows patterns, exercises provide practice. Clear comparison table for accusative inanimate. Prerequisite knowledge assumed correctly (M36–M40). |
| 4. Vocabulary coverage | 10/10 | All A1.6 vocabulary used naturally in context: їжа/напої (борщ, вареники, салат, хліб, сир, піца, каша, яєчня, суп, котлета, кава, чай, вода, сік, молоко), meals (сніданок, обід, вечеря), café phrases (Мені…будь ласка, Рахунок, Можна карткою?), market phrases (Скільки коштує/коштують, Дайте кілограм), currency (гривня/гривні/гривень), instrumental chunks (з молоком, зі сметаною, із сиром). |
| 5. Exercise quality | 9/10 | 4 exercises matching all 4 plan `activity_hints` exactly. Good variety: 2 quizzes (different focus — grammar vs situational), 1 fill-in (dialogue completion), 1 group-sort (categorization). Quiz 1 answer positions: 0,0,0,0,0,0,0,0,0,0 — all correct answers are first option. This is a pattern risk if the activity generator preserves this ordering. However, the activity YAML generator shuffles options at build time, so this is not a content-level issue. Fill-in distractor "Меня" (Russian form) is a clever trap. Group-sort 5:5 ratio is balanced. |
| 6. Engagement & tone | 8/10 | Deductions for: "Welcome to the checkpoint module for phase A1.6. This is where we pause to review and consolidate your knowledge." (meta-commentary), "Let's see what you can do!" (motivational opener), "you are in a great place" (telling), "You have successfully completed phase A1.6" (gamified). These are somewhat expected in a checkpoint module but still match deduction patterns. Positives: the reading text tells a concrete story (Anna's day), dialogues have real situations (haggling at market, meeting a friend), comprehension questions are well-framed. |
| 7. Structural integrity | 10/10 | All 5 H2 sections present and correctly ordered. Word count 1386 vs target 1000 — well above. Clean markdown. No duplicate sections, no stray tags, no meta-commentary sections. Dialogue divs properly formatted. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented on its own terms — no "like Russian" comparisons. Ринок and кафе scenarios are culturally authentic. Currency forms гривня/гривні/гривень correctly contextualized. "Все було дуже смачно!" is a natural compliment. Карткою payment is modern and relevant. |
| 9. Dialogue & conversation quality | 9/10 | Named speakers throughout (Наталя, Дмитро, Продавець, Офіціант, Олена). Multi-turn exchanges in 3 settings (breakfast, market, café). Natural flow: Наталя haggles ("Дорого!"), casual meeting with Олена, polite introduction ("Дуже приємно, Дмитре!"). Culturally appropriate responses (Офіціант: "Так, сідайте!"). Minor: reading section's Олена encounter uses plain em-dashes outside `<div class="dialogue">` while other exchanges use the dialogue div — slight formatting inconsistency. |

## Findings

```
[LINGUISTIC ACCURACY] [MAJOR]
Location: Читання section — "Анна купує **хліб** (bread), **сир** (cheese), **яблука** (apples), і **салат** (salad)."
Issue: Comma before "і" in a simple enumeration is an English punctuation calque. Ukrainian does not use a comma before the final conjunction in simple homogeneous lists (Правопис 2019, §158).
Fix: Remove the comma before "і".
```

```
[ENGAGEMENT & TONE] [MINOR]
Location: Що ми знаємо section — "Welcome to the checkpoint module for phase A1.6. This is where we pause to review and consolidate your knowledge. A1.6 covered five essential topics. Let's see what you can do!"
Issue: Generic meta-commentary opener. Could be replaced with a more direct, content-specific lead-in.
Fix: Rephrase to be less meta and more direct.
```

```
[ENGAGEMENT & TONE] [MINOR]
Location: Підсумок section — "You have successfully completed phase A1.6 — Food and Shopping. You have expanded your vocabulary and grammar significantly."
Issue: "Successfully completed" and "expanded...significantly" are telling-not-showing patterns. The checklist that follows is good — this framing sentence is the weak link.
Fix: Tighten the framing to be less congratulatory.
```

## Verdict: REVISE

One major finding (Oxford comma punctuation calque) requires a fix. Engagement has minor tone issues but these are partially inherent to the checkpoint format. All other dimensions are strong (9–10). The module is well-structured, linguistically sound, and pedagogically effective. Only the punctuation fix is mandatory.

<fixes>
- find: "Анна купує **хліб** (bread), **сир** (cheese), **яблука** (apples), і **салат** (salad)."
  replace: "Анна купує **хліб** (bread), **сир** (cheese), **яблука** (apples) і **салат** (salad)."
- find: "Welcome to the checkpoint module for phase A1.6. This is where we pause to review and consolidate your knowledge. A1.6 covered five essential topics. Let's see what you can do!"
  replace: "Phase A1.6 taught you to talk about food, order at cafés, shop at markets, and use the accusative case for things and people. Before moving on, let's check how well you remember it all."
- find: "You have successfully completed phase A1.6 — Food and Shopping. You have expanded your vocabulary and grammar significantly. Here is exactly what you can now do in Ukrainian:"
  replace: "Phase A1.6 — Food and Shopping — is done. Here is what you can now do in Ukrainian:"
</fixes>
