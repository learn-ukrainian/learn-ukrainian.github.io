<!-- content-hash: d77575c7509d -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | **Plan Compliance** | 7/10 | Content sections match meta outline but diverge from plan file. Plan (plans/a1/) specifies a dedicated «Мовні помилки та практика» section (450w) which does not exist as a standalone H2. Plan point «легенда про слона Мурзу» for Pryvoz (plans file line 14) is absent from content. Objectives are met: learner can buy produce, ask prices, negotiate politely, describe wants. |
| 2 | **Language Quality** | 8/10 | Ukrainian in the content file is grammatically clean. Genitive forms correct: «кілограм картоплі», «кілограм яблук», «кілограм помідорів». Adjective agreement tables accurate (lines 154-158). Dialogues sound natural — «Як мед! Спробуйте!» (line 217), «Беріть більше, завтра не буде!» (line 223). **Docked for:** Russicism «здача» in vocabulary YAML (line 46) and two activities (lines 176, 276) directly contradicting the lesson which correctly teaches «решта» (lines 241, 258). |
| 3 | **Factual Accuracy** | 8/10 | Bessarabskyi rynok: Content says "Built in 1912" (line 31); research says "1910-1912 рр." — acceptable (completion year). Content says "one of the first indoor refrigeration systems in Eastern Europe" (line 31); research says "Перший критий ринок з холодильними камерами" — content is more cautious, which is fine. Pryvoz "Established in 1827" (line 34) matches research. Name etymology «привозити» confirmed. **Docked for:** Missing architect attribution (Генрик Гай) and the elephant Murza legend mentioned in the plan. |
| 4 | **Lesson Quality** | 8/10 | Warm tutor voice throughout. Strong opening hook: «Для студента ринок — це школа.» (line 17). Clear "today you'll learn" preview via the opening blockquote (line 11-13). Multiple quick wins: vocabulary tables, simple dialogues. Good "would I continue?" — pacing comfortable, instructions clear, Ukrainian introduced gently. **Docked for:** Section «Лексика та Граматика: Як купувати?» introduces ~12 new vocabulary items + genitive patterns + number agreement + price phrases + quality adjectives before any practice. Cognitive overload risk for A1 (>3 concepts before practice). |
| 5 | **Immersion** | 9/10 | 35.2% Ukrainian is within the 35-55% target band for module 37 (A1.4 phase). Ukrainian sentences always paired with English translations in parentheses. Good scaffolding pattern: Ukrainian bolded → (English translation). Dialogues use full Ukrainian with line-by-line translation. |
| 6 | **Activity Quality** | 7/10 | 10 activities with 6 types (match-up, group-sort, quiz, fill-in, unjumble, true-false) — good variety. Fill-in activities (Genitive drill, dialogue completion) are pedagogically excellent. **Docked for:** (a) Russicism «здача» in 2 unjumble items; (b) 4+ quiz questions test content recall not language (lines 57, 79, 90, 101); (c) unjumble answers lack punctuation — «Дайте будь ласка кілограм яблук» missing commas (line 166). |
| 7 | **LLM Fingerprint** | 8/10 | Section openings varied: «Для студента ринок — це школа.» / "To buy something..." / "Now, let's put it all together." / «Ось моя історія.» — no monotony. No «це не просто» / «це не лише» patterns. No generic AI clichés. Callouts use 5 different types. **Docked for:** Opening blockquote (line 13) uses "beating heart of the community" — mildly purple prose, and «Ринок — це життя, це серце міста.» (line 17) echoes the same "heart" metaphor two lines later. |
| 8 | **Richness** | 7/10 | 6 callout boxes (culture ×1, myth-buster ×1, tip ×1, warning ×2, observe ×1). 2 grammar tables (lines 89-97, 105-110). 1 adjective declension table (lines 154-158). 3 embedded dialogues. Audit reports richness 81% with gaps: cultural 2/3 (need +1 cultural/did-you-know), dialogues 0/4 (detection issue — dialogues exist but may not be in recognized format). |
| 9 | **Humanity & Warmth** | 8/10 | Direct address frequent: «Ви», "you" throughout. Encouragement: «Не бійтеся» (line 26), «Це легко» (line 78), «Спробуйте самі» (line 78), «Це просто, так?» (line 270). "Would I continue?" test: 4/5 pass. Progress celebration at end: «Тепер ви знаєте:» (line 306) with summary. **Docked for:** Could use one more "don't worry" moment in the grammar-heavy section 2. |
| 10 | **Vocabulary Coverage** | 5/10 | **CRITICAL**: Vocabulary YAML is malformed — all 23 entries use `  lemma:` (2-space indent) without list dashes (`- lemma:`). Audit reads 0 parseable items. Additionally, 5 words taught in content are missing from vocab: «літр» (line 69), «пляшка» (line 72), «пакет» (line 75), «картка» (line 238), «базар» (line 20). And «здача» (line 46) should be «решта». |

---

## Critical Issues Found

### Issue 1: CRITICAL — Vocabulary YAML malformed (0 parseable items)

**File:** `vocabulary/at-the-market.yaml`
**Lines:** 1-98 (entire file)

The vocabulary file contains 23 entries but uses bare `  lemma:` keys without YAML list dashes (`-`). The parser reads this as a single mapping with duplicate keys, resulting in **0 vocabulary items** registered in the audit.

**Current format (broken):**
```yaml
  lemma: ринок
  pos: noun
  gender: m
  ...
  lemma: кілограм
```

**Required format:**
```yaml
- lemma: ринок
  pos: noun
  gender: m
  ...
- lemma: кілограм
```

**Impact:** Audit shows `Vocabulary items: 0`. All vocabulary tracking broken. This must be fixed by adding `- ` prefix to every `lemma:` line.

### Issue 2: HIGH — Russicism «здача» in activities and vocabulary

**Files:** `vocabulary/at-the-market.yaml` line 46, `activities/at-the-market.yaml` lines 176 and 276

The track calibration explicitly lists `здача → решта` as a Russicism. The content file correctly teaches «решта»:
- Line 240: «**ре́шта** — change (money returned)»
- Line 258: «Ваша решта — шістдесят.»

But the supporting files contradict this:
- Vocabulary line 46: `lemma: здача` with example «Ваша здача.»
- Activity line 176: answer `"Ваша здача шістдесят гривень"`
- Activity line 276: answer `"Ось ваша здача"`

This means activities actively drill a Russicism the lesson explicitly avoids. All instances must be replaced with «решта».

### Issue 3: MEDIUM — Quiz questions test content recall, not language

**File:** `activities/at-the-market.yaml`

Several quiz items in the "Культура українського ринку" quiz (lines 32-122) are answerable from general knowledge without reading any Ukrainian text:

- Line 57: «Що таке знаменитий історичний «Привоз»?» — tests geography knowledge
- Line 79: «Де саме знаходиться знаменитий Бессарабський ринок?» — tests geography knowledge
- Line 90: «Що краще купувати на ринку, а не в супермаркеті?» — tests opinion/culture knowledge
- Line 101: «Чому українці люблять ходити на базар?» — tests culture knowledge

These should reference the module text or test language comprehension. For A1 this is less severe than in content-heavy tracks, but at least 2-3 should be reformulated to test Ukrainian reading (e.g., "Згідно з модулем, чому кияни кажуть «дорого, як на Бессарабці»?").

### Issue 4: MEDIUM — Vocabulary YAML missing 5 taught items

**File:** `vocabulary/at-the-market.yaml`

Words explicitly taught in the content with definitions and examples but absent from vocab YAML:
- «літр» — taught line 69 with definition and example
- «пляшка» — taught line 72 with definition and example
- «пакет» — taught line 75 with definition and example
- «картка» — taught line 238 with definition and example
- «базар» — taught line 20, distinguished from «ринок»

### Issue 5: LOW — Unjumble answers missing commas

**File:** `activities/at-the-market.yaml`

- Line 166: answer «Дайте будь ласка кілограм яблук» — should have commas: «Дайте, будь ласка, кілограм яблук»
- Line 174: answer «Зважте будь ласка триста грам» — should have commas: «Зважте, будь ласка, триста грам»

For unjumble activities the word list doesn't include comma tokens, so the answer strings should reflect the expected output. If commas are intentionally omitted from the activity format, this is acceptable but teaches incorrect punctuation.

### Issue 6: LOW — Plan cultural hook missing (elephant Murza)

**File:** `at-the-market.md`, Section «Привоз: The Soul of Odesa» (line 33)

Plan file (plans/a1/at-the-market.yaml, line 14) specifies: «легенда про слона Мурзу». This anecdote about Pryvoz is absent from the content. While the Pryvoz section is engaging, this specific plan point is undelivered.

---

## Factual Verification

### Callout Box Check

| Callout | Location | Claim | Verdict |
|---------|----------|-------|---------|
| `[!culture]` "The Try It! Culture" | Line 24-26 | Sellers offer tastings of cheese, berries, grapes; refusing can be seen as doubting quality | ✅ PLAUSIBLE — Consistent with research note: «На українському базарі нормально і навіть бажано куштувати товар» |
| `[!myth-buster]` "Markets only for older people" | Line 43-45 | Farm-to-table movement popular among youth; Saturday market ritual | ✅ PLAUSIBLE — General cultural knowledge confirms this trend |
| `[!tip]` "Memorize the Chunk" | Line 98-100 | Memorize «кілограм картоплі» as one unit | ✅ CORRECT — Sound pedagogical advice for A1 |
| `[!warning]` "Common Error" | Line 112-116 | «Два кілограм» is wrong, «Два кілограми» is correct | ✅ CORRECT — Matches research: "2, 3, 4 + Nominative Plural" |
| `[!warning]` "Don't Translate I want" | Line 181-183 | «Я хочу...» sounds demanding; use «Дайте, будь ласка...» or «Можна...?» | ✅ CORRECT — Matches plan vocabulary_hints and cultural register |
| `[!observe]` "Haggling" | Line 261-268 | Supermarket: never; market with tags: usually no; without tags: yes | ✅ PLAUSIBLE — Reasonable cultural guidance |

### Grammar Rule Check

| Rule | Location | Verdict |
|------|----------|---------|
| Genitive after кілограм: картопля → картоплі | Line 83, 91 | ✅ CORRECT |
| Genitive after кілограм: яблука → яблук | Line 84, 94 | ✅ CORRECT |
| Genitive after кілограм: сало → сала | Line 85 | ✅ CORRECT |
| Numbers: 2-4 + кілограми (Nom.Pl) | Line 108 | ✅ CORRECT |
| Numbers: 5+ кілограмів (Gen.Pl) | Line 109 | ✅ CORRECT |
| Numbers: пів + кілограма (Gen.Sg) | Line 110 | ✅ CORRECT |
| Adjective agreement: свіжий/свіжа/свіже/свіжі | Lines 154-158 | ✅ CORRECT |

### Factual Claims Check

| Claim | Location | Research Cross-Ref | Verdict |
|-------|----------|-------------------|---------|
| Bessarabskyi built in 1912 | Line 31 | Research: "1910-1912 рр." | ⚠️ IMPRECISE — Completion year OK, but "1910-1912" would be more accurate |
| "one of the first indoor refrigeration systems in Eastern Europe" | Line 31 | Research: "Перший критий ринок з холодильними камерами" | ⚠️ MINOR — Content says "one of the first in Eastern Europe", research says "first covered market with refrigeration". Content version is more cautious but shifts the claim slightly |
| Pryvoz established 1827 | Line 34 | Research: "1827 р." | ✅ CORRECT |
| Pryvoz name from «привозити» (to bring) | Line 34 | Research: "Назва від 'привозити'" | ✅ CORRECT |
| «Дорого, як на Бессарабці» | Line 31 | Research: "дорого, як на Бессарабці" | ✅ CORRECT |

---

## Verification Summary

| Check | Status | Notes |
|-------|--------|-------|
| All H2 sections present from meta | ✅ PASS | All 4 sections match meta content_outline |
| Plan compliance | ⚠️ PARTIAL | Meta sections differ from plan sections; elephant Murza missing; no dedicated error-correction section |
| Vocabulary scope (plan required) | ⚠️ PARTIAL | All required words covered in content; vocab YAML malformed (0 items parsed) and missing 5 entries |
| Grammar scope | ✅ PASS | Genitive for quantities, numbers + nouns, adjective agreement — all within plan scope, no scope creep |
| Russianisms scanned | ⚠️ FOUND | «здача» in vocab YAML (line 46) and activities (lines 176, 276). Lesson correctly uses «решта». No «давайте» calques. No «кушати», «получати», «вообще» |
| Colonial framing | ✅ CLEAN | No "unlike Russian" patterns. Ukrainian features presented on own terms |
| LLM fingerprints | ✅ CLEAN | No structural monotony, no generic AI rhetoric, no «це не просто» patterns |
| Callout box accuracy | ✅ PASS | All 6 callout claims verified as plausible/correct |
| Grammar rules accuracy | ✅ PASS | All genitive, number agreement, and adjective rules are correct |
| Factual accuracy | ⚠️ MINOR | Bessarabskyi date imprecise (1912 vs 1910-1912); refrigeration claim slightly shifted from research |
| Activity errors | ⚠️ FOUND | Russicism «здача» in 2 unjumble activities; 4 quiz questions test content recall; missing commas in 2 unjumble answers |
| Beginner safety ("Would I Continue?") | ✅ PASS | 4/5 — warm, encouraging, clear instructions. Minor concern: grammar section packs many concepts before practice |

---

## Fix Plan

### Priority 1: Vocabulary YAML reformat (CRITICAL)
**File:** `vocabulary/at-the-market.yaml`
- Add `- ` prefix to every `lemma:` line (23 entries)
- Replace `lemma: здача` → `lemma: решта` with updated example: `"Ваша решта."`
- Add 5 missing entries: «літр», «пляшка», «пакет», «картка», «базар»

### Priority 2: Replace «здача» with «решта» in activities (HIGH)
**File:** `activities/at-the-market.yaml`
- Line 175-176: Change `["Ваша", "здача", "шістдесят", "гривень"]` → `["Ваша", "решта", "шістдесят", "гривень"]` and answer to `"Ваша решта шістдесят гривень"`
- Line 275-276: Change `["Ось", "ваша", "здача"]` → `["Ось", "ваша", "решта"]` and answer to `"Ось ваша решта"`

### Priority 3: Add 1 cultural callout to close richness gap (MEDIUM)
**File:** `at-the-market.md`
- Add a `[!culture]` or `[!did-you-know]` callout in Section «Лексика та Граматика: Як купувати?» or Section «Історія: Мій похід на Привоз» — e.g., about the elephant Murza legend at Pryvoz, which would also close the plan compliance gap.

### Priority 4: Reformulate 2-3 quiz questions for language testing (LOW)
**File:** `activities/at-the-market.yaml`
- Lines 57-67: Reformulate to reference module text, e.g., "Згідно з модулем, чим відомий «Привоз» в Одесі?"
- Lines 79-89: Reformulate, e.g., "Як кияни описують ціни на Бессарабському ринку?" (tests whether learner understood «Дорого, як на Бессарабці»)

---

## Verdict

**FAIL — Requires D.2 repair cycle.**

The content prose is solid: warm tutoring voice, accurate Ukrainian grammar, good cultural hooks, appropriate immersion level. However, three infrastructure issues prevent a pass:

1. **Vocabulary YAML is unparseable** (0/23 items — CRITICAL formatting error)
2. **Russicism «здача» in activities** directly contradicts the lesson's correct use of «решта»
3. **Richness below 95% threshold** (81%) with closable gaps

Estimated D.2 effort: LOW — all fixes are mechanical (YAML formatting, word replacement, add 1 callout). No prose rewrite needed.