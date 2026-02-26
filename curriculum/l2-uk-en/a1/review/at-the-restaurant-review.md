<!-- content-hash: 64b37b2915b7 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|-----------------|
| 1 | **Lesson Quality** | 8/10 | Good lesson arc with practical focus, but lacks warmest opening markers and explicit learning preview. No "Привіт!" greeting, no "Today you'll learn..." preview. Closing has self-check questions but no celebratory "You can now..." moment. |
| 2 | **Language Quality** | 9/10 | Ukrainian is grammatically accurate throughout. No Russianisms in the teaching content (the «счёт» mention in [!myth-buster] is an appropriate anti-Russicism drill). Stress marks are applied inconsistently — present on «Капусня́к», «Гарні́р», «Замо́вити» but absent on multisyllabic words like вареники (line 142), котлета (line 143). Minor: confusing etymological notation at line 163. |
| 3 | **Immersion** | 9/10 | At 35.5%, falls exactly at the lower boundary of the target band (35-55% for Module 36). The progressive Ukrainian → English scaffolding is well-executed: cultural section (Section «Культурний контекст: Українська гостинність») uses lead-in Ukrainian sentences followed by English explanation, which is excellent pedagogy. The reading passage (lines 333-362) is a strong immersion element. |
| 4 | **Activity Quality** | 8/10 | 10 activities with 5 types (match-up ×3, quiz ×2, fill-in ×2, unjumble ×2, group-sort ×1). Good variety. However, the fill-in "Я буду..." activity (lines 148-212) has 5 of 8 items testing masculine inanimate accusative (borshch, salat, sup, chay, desert) where the answer is trivially identical to nominative — these don't test any transformation skill. Only 3 items (kavu, vodu, pitsu) test real accusative change. The genitive fill-in (lines 278-345) is better designed with genuine morphological challenges. |
| 5 | **Richness** | 7/10 | Audit reports 80% vs 95% threshold. Gaps: `dialogues: 0/4` — this is a **scanner false negative**: the module clearly has 4 well-constructed dialogues (lines 271-327) plus a reading passage (lines 329-362). However, `tables: 0/2` is a **genuine gap**: the accusative case explanation (lines 180-191) uses bullet lists where a 3-column table (Nominative → Accusative → Example) would be far clearer for an A1 visual learner. The sample menu (lines 136-156) is also in bullet format instead of a table. |
| 6 | **Factual Accuracy** | 9/10 | Cultural claims are accurate: the Перше/Друге/Третє meal structure is correct per research notes. «Будьмо!» explanation is accurate. Tipping at 10-15% is current. The proverb «Гість у дім — Бог у дім» (line 420) is a real Ukrainian proverb. «Хліб — усьому голова» (line 403) is authentic. One minor issue: the [!culture] box (line 40-42) claims soup is "almost always" included in бізнес-ланч — this is broadly true but becoming less universal in modern Kyiv restaurants. Not critical. |
| 7 | **LLM Fingerprint** | 8/10 | No "це не просто" / "це не лише" patterns detected. No generic AI clichés. However, example formatting is uniform across sections: every section uses the identical `* **Example:** «Ukrainian.» (English.)` bullet pattern (e.g., lines 50, 54, 94, 96). The 4 dialogues (lines 271-327) all follow the exact same structure: **Ситуація:** *italic English context* → bolded speaker names → identical line formatting. This structural monotony across 4 instances suggests template-driven generation rather than natural variation. |
| 8 | **Warmth & Humanity** | 8/10 | The module is friendly and practical but lacks the strongest beginner safety markers. Direct address ("you") is present throughout. The [!tip] boxes provide genuine guidance. However: zero explicit "Don't worry" moments, zero "Great job!" encouragement, zero "You've got this!" validation. The closest is the [!observe] box on line 373-375 about «будь ласка», which feels more instructional than encouraging. The closing (lines 430-442) skips emotional validation and goes straight to self-test questions. |
| 9 | **Plan Compliance** | 8/10 | All plan content_outline points are addressed, but several are in wrong sections: (a) «Будьмо!» toast appears in Section «Розминка: Структура меню та етикет» but the plan places it in "Підсумок та етикет"; (b) tipping etiquette appears in Section «Презентація: Як зробити замовлення» (lines 226-250) but the plan places it in "Вступ та культурний контекст"; (c) dietary needs are in Section «Презентація» but plan places them in "Практика: Типові ситуації". Two vocab items from the YAML (порція, резервація) don't appear in lesson body text. |

---

## Critical Issues Found

### Issue 1: Missing Markdown Tables (Richness Gap) — MEDIUM

**Location:** Lines 180-191 (Section «Презентація: Як зробити замовлення»)

The accusative case explanation uses nested bullet lists instead of a clear table. For an A1 learner encountering case morphology, a table is dramatically more scannable.

**Current format (lines 180-191):**
```
*   Masculine (inanimate): No change.
    *   Борщ (Nominative) → Я буду **борщ** (Accusative).
    *   Салат (Nominative) → Я буду **салат** (Accusative).
```

**Required fix:** Convert to a 3-column markdown table: | Gender | Nominative | Accusative (Я буду...) |. This also applies to the sample menu (lines 136-156), which would be clearer as a table with columns: Dish | Weight | Price.

### Issue 2: Fill-In Activity Imbalance — MEDIUM

**Location:** Activities YAML, lines 148-212 ("Я буду..." fill-in)

5 of 8 items test masculine inanimate accusative (борщ, салат, суп, чай, десерт) where the answer is trivially identical to the nominative form — the learner doesn't practice any morphological transformation. Only 3 items (каву, воду, піцу) test the feminine -а→-у change, which is the actual learning point.

**Required fix:** Replace 2-3 masculine items with feminine or neuter items that require actual case transformation, e.g., «Я буду {{answer}}.» → рибу (< риба), пасту (< паста), котлету (< котлета) — all of which appear in the lesson content.

### Issue 3: Vocab Items Not In Content — LOW

**Location:** Vocabulary YAML lines 58-72

Two vocabulary items have lemmas and examples but never appear in the lesson content:
- «порція» (portion) — example: «Це велика порція.» — not used anywhere in the .md file
- «резервація» (reservation) — example: «У вас є резервація?» — only appears as a heading on line 81 (### Крок 1: Резервація), never in running text or dialogue

**Required fix:** Add at least one contextual use of each word in the lesson body. E.g., in the sample menu, add portion sizes with the word «порція»; in Діалог 1, the waiter could ask «У вас є резервація?».

### Issue 4: Missing Warm Opening Markers — LOW

**Location:** Lines 9-17 (opening of module)

The module opens with a formal blockquote «Чому це важливо?» followed by English prose. There is no warm greeting ("Привіт!"), no explicit learning preview ("Today you'll learn how to..."), and no emotional orientation for a nervous beginner. Compare with the [!observe] box on line 373 which at least addresses the learner directly.

**Required fix:** Add a brief warm opening before the blockquote: a "Привіт!" greeting and a 1-2 sentence preview of what the learner will be able to do by the end (e.g., "By the end of this lesson, you'll be able to order a full meal, handle the bill, and impress your waiter with polite Ukrainian.").

### Issue 5: Confusing Notation for A1 Learner — LOW

**Location:** Line 163

The text reads: «Деруни́ — це млинці з картоплі. Дуже смачно зі **сметаною** (< **смета́на** — sour cream).»

The `(<` notation is linguistic convention for "derived from" and is not explained anywhere. An A1 learner has no context for what `<` means here. It's particularly confusing because the intent is just to show the nominative/dictionary form.

**Required fix:** Replace `(< **смета́на** — sour cream)` with a clearer format like `(**смета́на** — sour cream)` or simply add «смета́на» to the vocabulary list.

---

## Factual Verification

### Callout Box Verification

| Callout | Type | Location | Verdict |
|---------|------|----------|---------|
| "The 'First' Rule" — soup daily for health | [!culture] | Line 40-42 | **PASS** — Culturally accurate belief widely held in Ukraine. The claim about бізнес-ланч starting with soup is generally true. |
| "Замовити чи забронювати?" | [!tip] | Lines 91-92 | **PASS** — Both verbs are correctly described. Research notes confirm: «бронювати» for tables, «замовити» for ordering. |
| "Don't say 'What is this?' for ingredients" | [!warning] | Lines 204-205 | **PASS** — Pragmatically accurate. «З чого це?» is the correct question for ingredients. |
| "Счёт" vs "Рахунок" | [!myth-buster] | Lines 249-250 | **PASS** — Correctly identifies «счёт» as Russian and «рахунок» as standard Ukrainian. Aligns with plan requirement and research notes. Not colonial framing — this is a legitimate anti-Russicism drill. |
| Eye contact during toast | [!tip] | Lines 74-75 | **PASS** — Culturally accurate. Eye contact during toasting is indeed considered polite. |
| Polite markers | [!observe] | Lines 373-375 | **PASS** — Correct pragmatic advice about «будь ласка» usage. |
| «Гість у дім — Бог у дім» | [!quote] | Line 420 | **PASS** — Authentic Ukrainian proverb. Widely attested. |

### Grammar Rule Verification

| Rule | Location | Verdict |
|------|----------|---------|
| Masculine inanimate accusative = nominative | Line 180-183 | **PASS** — Correct for A1 scope |
| Feminine -а → -у in accusative | Lines 184-188 | **PASS** — Correct: кава→каву, паста→пасту, вода→воду, котлета→котлету |
| Neuter accusative = nominative | Lines 189-191 | **PASS** — Correct: вино→вино, м'ясо→м'ясо |
| «Без» + Genitive case | Lines 209-224 | **PASS** — Correct: без м'яса, без цукру, без глютену, без молока |
| «Я буду» + Accusative for ordering | Lines 170-176 | **PASS** — Standard colloquial Ukrainian ordering pattern |

### Colonial Framing Check

No colonial framing detected. The «счёт» vs «рахунок» comparison (line 249-250) is an explicit anti-Russicism correction within a [!myth-buster] box — this is a legitimate pedagogical approach per plan requirements. No other Russian comparisons found anywhere in the module.

---

## Verification Summary

| Check | Result | Notes |
|-------|--------|-------|
| Russianisms in content | CLEAN | No Russianisms in teaching text. «Счёт» mentioned only in myth-buster for correction. |
| Colonial framing | CLEAN | No "Unlike Russian..." patterns. |
| LLM filler phrases | CLEAN | No "це не просто", "це не лише", generic AI clichés found. |
| Factual accuracy | PASS | All cultural claims, proverbs, and grammar rules verified. |
| Grammar correctness | PASS | All Ukrainian sentences grammatically correct. Accusative and genitive forms accurate. |
| Plan coverage | PARTIAL | All plan points covered but in rearranged section order. Two vocab items missing from prose. |
| Activity quality | PARTIAL | Good variety (5 types) but accusative fill-in is imbalanced toward trivial masculine items. |
| Richness | BELOW THRESHOLD | 80% vs 95%. Missing tables (genuine gap). Dialogues present but not scanner-detected (likely false negative). |
| Beginner safety | ADEQUATE | Not overwhelming, clear instructions, but lacks explicit encouragement beats. |

---

## Verdict

**CONDITIONAL PASS** — The module is pedagogically strong with accurate Ukrainian, good cultural integration, and comprehensive restaurant coverage. The word count significantly exceeds target (2863/2000). However, two issues require attention before full PASS:

1. **Richness gap (tables):** Add at least 2 markdown tables — one for the accusative case paradigm (lines 180-191) and one for the sample menu (lines 136-156). This directly serves A1 visual learners and closes the richness gap.
2. **Activity rebalancing:** In the "Я буду..." fill-in, replace 2-3 trivial masculine inanimate items with feminine items requiring actual morphological change (e.g., риба→рибу, котлета→котлету).

The warm opening and vocab coverage issues are recommended but not blocking.

**Fix Plan:**

| Priority | Action | Location | Effort |
|----------|--------|----------|--------|
| HIGH | Convert accusative explanation to markdown table (3 columns: Gender/Nominative/Accusative) | Lines 178-191 | Small |
| HIGH | Convert sample menu to markdown table (Dish/Weight/Price) | Lines 136-156 | Small |
| HIGH | Replace 2-3 masculine fill-in items with feminine items (риба→рибу, котлета→котлету, паста→пасту) | Activities YAML lines 157-204 | Small |
| MEDIUM | Add warm opening: "Привіт!" + learning preview before the blockquote | Before line 11 | Small |
| LOW | Add «порція» and «резервація» in contextual sentences within the lesson body | Various | Small |
| LOW | Replace `(< **смета́на**)` notation with plain parenthetical | Line 163 | Trivial |