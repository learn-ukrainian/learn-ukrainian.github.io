**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Key Evidence |
|---|-----------|-------|-------------|
| 1 | **Language Quality** | 7/10 | Three gender agreement errors in Ukrainian prose: «цей універсальний слово» (line 117), «Відносний слово» (line 113), and a typo «словоа» (line 119). These are in the section *teaching* relative pronoun agreement — undermines credibility. |
| 2 | **Factual Accuracy** | 9/10 | Grammar rules (щоб+past, через+Acc, який agreement) are correctly explained. Cultural claims about калина and Будьмо are accurate. One minor issue: examples demonstrating який in Nominative (lines 124, 128) fail to actually use який. |
| 3 | **Lesson Quality** | 7/10 | Warm opening and good medical dialogue. But 5 sets of empty placeholder stubs (Модель/Практика/Самоперевірка, lines 100-107, 179-186, 259-266, 298-305, 323-330) break flow and feel robotic. No "rule table" for який as plan requires. |
| 4 | **LLM Fingerprint** | 7/10 | «не просто» appears 2× (lines 16, 256) — meets the ≤7 threshold. «надзвичайно» appears 4× (lines 16, 146, 208, 291). Heavy superlative stacking throughout: «дуже» appears 30+ times. Structural monotony: every H2 section ends with identical Модель/Практика/Самоперевірка stubs. |
| 5 | **Activity Quality** | 7/10 | 4 unjumble answer keys omit mandatory commas before subordinating conjunctions (lines 581, 590, 599, 627). One quiz question is implausible: «Де моє хворе горло, ___ сьогодні так сильно болить?» (activities line 503). In a module *teaching* complex sentence punctuation, incorrect punctuation in answer keys is a critical error. |
| 6 | **Richness** | 9/10 | 6 callout boxes with varied types (tip, warning, observe, fact, culture). Medical dialogue is authentic and engaging. Cultural hooks (калина, Будьмо) are meaningful. |
| 7 | **Immersion** | 9/10 | 71.5% Ukrainian — within 60-75% Band 2 target. English used appropriately for abstract syntax explanations. All medical dialogues and examples in Ukrainian. |
| 8 | **Plan Compliance** | 8/10 | All 5 sections present. All planned grammar points covered. Missing: plan explicitly requires «a rule table demonstrating gender, number, and case agreement» for який — content provides examples only, no table. |
| 9 | **Humanity & Warmth** | 8/10 | Warm «Вітаємо вас» opening. Multiple encouragement markers. The Будьмо cultural section is genuinely engaging. Loses a point for the 5 mechanical placeholder stubs and absence of "you can now..." celebration in the summary. |

---

## Critical Issues Found

### Issue 1: Gender Agreement Errors in Section Teaching Gender Agreement (CRITICAL)

**Location:** Section «Навичка 2: Опис та послідовність дій», lines 113, 117, 119

The section on який agreement contains three errors in the Ukrainian prose that directly contradicts the grammar being taught:

1. **Line 113** — Heading «Відносний слово: Який» — "слово" is neuter (середній рід), requires «Відносне слово: Який»
2. **Line 117** — «Використовуйте цей універсальний слово» — again, "слово" is neuter, requires «це універсальне слово»
3. **Line 119** — Heading «Узгодження словоа Який» — typo, "словоа" should be «слова»

**Impact:** A section that teaches learners to match adjective endings to noun gender contains visible adjective-noun gender mismatches. This destroys pedagogical credibility.

**Fix:** Replace «Відносний слово» → «Відносне слово», «цей універсальний слово» → «це універсальне слово», «словоа» → «слова»

### Issue 2: який Nominative Examples Don't Use який (CRITICAL)

**Location:** Section «Навичка 2: Опис та послідовність дій», lines 124, 128

The examples purporting to demonstrate який in Nominative case split into two separate sentences instead of using a relative clause:

- Line 124: «Це новий лікар. Він працює в нашій сучасній лікарні.» — English translation says "who works" but Ukrainian has no який
- Line 128: «Ось та аптека. Вона завжди працює вночі.» — English translation says "which always works" but Ukrainian has no яка

**Impact:** The examples are supposed to demonstrate Nominative relative clauses but contain zero relative pronouns. The learner sees the English gloss "who/which" but the Ukrainian model sentence uses separate clauses.

**Fix:** Combine into relative clauses: «Це новий лікар, який працює в нашій сучасній лікарні.» and «Ось та аптека, яка завжди працює вночі.»

### Issue 3: Unjumble Answer Keys Missing Commas (MAJOR)

**Location:** Activities file, unjumble type "Побудуйте складні речення", lines 581, 590, 599, 627

Four answer keys in the complex sentence unjumble omit commas before subordinating conjunctions:

- Line 581: «Я почекаю тут поки ти п'єш чай» — needs comma before «поки»
- Line 590: «Вона п'є сироп який дав їй лікар» — needs comma before «який»
- Line 599: «Ми йшли додому коли почався сильний дощ» — needs comma before «коли»
- Line 627: «Вони йдуть в аптеку бо дуже хворі» — needs comma before «бо»

**Impact:** In a checkpoint module explicitly teaching complex sentence construction, answer keys that model incorrect punctuation directly undermine the lesson. The content itself (lines 26, 39) carefully notes comma placement rules.

**Fix:** Add commas: «Я почекаю тут, поки ти п'єш чай», «Вона п'є сироп, який дав їй лікар», «Ми йшли додому, коли почався сильний дощ», «Вони йдуть в аптеку, бо дуже хворі»

### Issue 4: Implausible Activity Question (MINOR)

**Location:** Activities file, quiz "Оберіть правильний займенник «який»", line 503

«Де моє хворе горло, ___ сьогодні так сильно болить?» — "Where is my sick throat that hurts so badly today?" is semantically absurd. No one asks *where* their throat is. This is not a plausible Ukrainian sentence.

**Fix:** Replace with a natural sentence, e.g., «Це моє хворе горло, ___ сьогодні так сильно болить.» (keeping the яке answer)

### Issue 5: Heading Inconsistency (MINOR)

**Location:** Section «Навичка 2: Опис та послідовність дій», line 135

«**Plural (Plural):**» — Redundant English-only heading. All other gender headings use Ukrainian: «Чоловічий рід», «Жіночий рід», «Середній рід». The plural heading breaks the pattern.

**Fix:** Replace with «**Множина (Plural):**»

### Issue 6: Missing який Rule Table (MINOR — Plan Compliance)

**Location:** Section «Навичка 2: Опис та послідовність дій»

The plan (meta line 24-25) explicitly requires: «Provide a rule table demonstrating gender, number, and case agreement with the antecedent noun.» The content provides inline examples but no consolidated reference table.

**Fix:** Add a declension summary table for який/яка/яке/які showing at least Nominative and Accusative forms across genders.

### Issue 7: LLM Filler — «не просто» Pattern (MINOR)

**Location:** Lines 16, 256

- Line 16: «Ви навчитеся не просто говорити короткі базові фрази, а будувати складні, глибокі логічні речення.»
- Line 256: «Калина — це не просто корисна червона ягода.»

Per rubric: «не просто» / «це не лише» used 2+ times → LLM Fingerprint ≤ 7.

**Fix:** Rewrite at least one instance. E.g., line 16 could become: «Ви навчитеся будувати складні логічні речення замість коротких базових фраз.»

### Issue 8: Empty Placeholder Stubs (MINOR — Structural)

**Location:** Lines 100-107, 179-186, 259-266, 298-305, 323-330

Every section ends with identical triple stubs:
```
### Модель:
*Generic italic text*
### Практика:
*Generic italic text*
### Самоперевірка
*Generic italic text*
```

These contain no actual content and create mechanical repetition across all 5 sections (15 empty headings total). They break the reading flow and add no pedagogical value.

**Fix:** Either populate with real content (model answers, practice prompts, self-check questions) or remove entirely. Activities already serve the practice function.

---

## Factual Verification

| Claim | Verified? | Notes |
|-------|-----------|-------|
| «тому що» requires a comma before it | ✅ Correct | Standard Ukrainian punctuation rule |
| «бо» is colloquial register | ✅ Correct | Confirmed by State Standard §4.4.2 in research notes |
| «через» + Accusative for cause | ✅ Correct | Standard grammar |
| «щоб» + past tense when subjects differ | ✅ Correct | Core A2.2 grammar rule |
| «щоб» vs «що б» distinction | ✅ Correct | Conjunction vs pronoun+particle |
| «який» declines like a hard-stem adjective | ✅ Correct | Standard grammar |
| «після того як» requires comma before «як» | ✅ Correct | Standard punctuation |
| «приймати ліки» not «брати ліки» | ✅ Correct | Confirmed in research notes as common learner error |
| «Будьмо» is imperative form of «бути» | ✅ Correct | 1st person plural imperative |
| Калина as national symbol of Ukraine | ✅ Correct | Well-established cultural fact |
| Малина, калина, мед as traditional cold treatments | ✅ Correct | Confirmed in research Cultural Hooks section |

**Grammar Rule Verification:**
- The explanation that «боліти» uses the body part as subject + person in Genitive with у/в (line 203) is correct.
- The explanation of Accusative with «мати» and Genitive with «немає» (lines 215-221) is correct.
- No grammar overgeneralizations found.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Colonial framing | ✅ Clean | No Russian comparisons found. Ukrainian grammar presented on its own terms. |
| Russicisms | ✅ Clean | No instances of приймати участь, самий кращий, слідуючий, скучати, нравитися found. |
| Anglicisms | ✅ Clean | Content explicitly corrects "брати ліки" anglicism. No "робити рішення" or similar patterns. |
| LLM fingerprint | ⚠️ Flag | «не просто» 2×; «надзвичайно» 4×; structural monotony (5× identical Модель/Практика/Самоперевірка stubs) |
| Callout monotony | ✅ Clean | 6 callouts, all different types (tip, warning ×2, observe, fact, culture) |
| Structural monotony | ⚠️ Flag | Every H2 section opens with a 1-2 sentence Ukrainian hook then switches to English explanation — same pattern throughout |
| Factual accuracy | ✅ Clean | All grammar rules and cultural claims verified |
| Plan compliance | ⚠️ Gap | Missing який declension table explicitly requested in plan |
| Activity errors | ❌ Found | 4 unjumble answers missing commas; 1 implausible quiz question |
| Grammar errors in content | ❌ Found | 3 gender agreement errors / typos in section «Навичка 2: Опис та послідовність дій» |

**Section Coverage Verification:**
- Section «Вступ та цілі» — reviewed: warm opening, good goal-setting, minor LLM filler
- Section «Навичка 1: Синтаксис логіки: Причина та Мета» — reviewed: grammar explanations accurate, register distinction clear
- Section «Навичка 2: Опис та послідовність дій» — reviewed: contains 3 grammar errors (Issues 1-2), missing rule table (Issue 6)
- Section «Навичка 3: Медицина, тіло та народні методи» — reviewed: medical vocab well-presented, cultural content authentic
- Section «Навичка 4: Практичне застосування та підсумок» — reviewed: dialogue is well-constructed, Будьмо section is engaging

---

## Verdict

**FAIL — Targeted Repair Required (D.2)**

**Rationale:** The module has strong content architecture, accurate grammar explanations, and genuinely engaging cultural elements. However, three gender agreement errors in the section *teaching* gender agreement (Issues 1-2) represent a credibility-destroying contradiction. Four missing commas in unjumble answer keys (Issue 3) directly undermine the module's core teaching of complex sentence punctuation. These are not cosmetic issues — they are pedagogical self-contradictions in a checkpoint module.

**Mandatory fixes for D.2:**
1. Fix 3 gender agreement errors/typos in section «Навичка 2: Опис та послідовність дій» (lines 113, 117, 119)
2. Rewrite 2 який Nominative examples to actually contain який (lines 124, 128)
3. Add commas to 4 unjumble answer keys (activity lines 581, 590, 599, 627)
4. Fix implausible quiz question (activity line 503)
5. Fix heading «Plural (Plural)» → «Множина (Plural)» (line 135)

**Recommended fixes (non-blocking):**
6. Add який declension summary table per plan requirement
7. Rewrite 1 instance of «не просто» to reduce LLM fingerprint
8. Either populate or remove 15 empty Модель/Практика/Самоперевірка stubs