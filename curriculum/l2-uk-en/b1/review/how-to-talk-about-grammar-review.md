<!-- content-hash: 8c7f8a6a6e13 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | **Language Quality** | 7/10 | Russicism at line 127: «найкрасивіше» uses base «красивий» (красивий → гарний per checklist). Grammar inaccuracy at line 242: «З, із + Орудний» omits Genitive and Accusative governance of «з». Euphony claim at line 260 overstates uniqueness. Otherwise solid Ukrainian throughout. |
| 2 | **Teaching Quality** | 8/10 | Strong teacher voice with analogies (music instrument, costumes, constructors). Good "How it works" applied examples. Missing some TTT structure — rules often presented before discovery. Section «Частини мови: самостійні категорії» is concept-dense but well-paced with H3 breaks. The «Практика: читаємо граматику українською» section is effective but short. |
| 3 | **Factual Accuracy** | 7/10 | Line 242: «З, із» presented as governing only Instrumental — this is a significant overgeneralization for a metalanguage module. Line 479: о/і alternation called «унікальною серед слов'янських мов» — overstated. Lines 24-25: Smotrytskyi "officially introducing" letter ґ is a stronger claim than research supports. |
| 4 | **LLM Fingerprint** | 7/10 | Line 27: confirmed LLM filler «In this lesson, we will». The word «унікальн*» appears 4 times (lines 29, 260, 416, 479, 498) — repeated uniqueness claims are an AI rhetoric pattern. Generic AI structure: 3+ H3 sections in «Частини мови: самостійні категорії» follow identical Definition→Questions→Examples→Context formula. |
| 5 | **Plan Compliance** | 6/10 | Missing: (a) Letter Ґ 1933 repression/1990s restoration cultural hook required by plan section 3; (b) просте/складне речення distinction; (c) Accusative vs Genitive drill («Бачу брата» vs «Немає брата»); (d) відміна іменника concept; (e) 7 case names missing from vocabulary sidecar despite being listed as "required" in plan. |
| 6 | **Activity Quality** | 8/10 | 4 types meeting all quantity thresholds (12 match-up pairs, 8 fill-in, 10 quiz, 8 error-correction). Error-correction items are strong and test real agreement/case errors. Quiz item "Скільки відмінків в українській мові?" tests pure recall rather than language processing. Overall solid variety. |
| 7 | **Immersion** | 9/10 | 91.9% Ukrainian is within the 60-100% range for B1 bridge modules. English used surgically for term equivalents and one bridge paragraph. Appropriate for the module's stated function. |
| 8 | **Engagement** | 8/10 | 7 callout boxes with varied types ([!history-bite], [!note], [!observe], [!tip], [!warning], [!culture] ×2). Good analogies: music/instrument, actor/costumes, constructor. The mnemonic aid is excellent. |

---

## Critical Issues Found

### Issue 1: Grammar Inaccuracy — Preposition «з» governance (CRITICAL)

**Location:** Section «Частини мови: службові слова», line 242
**Cited text:** «**З, із** + Орудний (*з другом*).»
**Problem:** This presents «з/із» as governing ONLY the Instrumental case. In reality, «з» governs three cases:
- **Genitive** (separation/origin): *з хати* (from the house), *з України* (from Ukraine)
- **Instrumental** (accompaniment): *з другом* (with a friend)
- **Accusative** (approximation): *з годину* (about an hour)

For a **metalanguage module** — whose entire purpose is teaching precise grammatical terminology — this is a serious omission. A learner trusting this rule would misanalyze «Я йду з хати» as Instrumental rather than Genitive.

**Fix:** Expand line 242 to show multiple case governance, or at minimum add "найчастіше" (most often) qualifier and note the Genitive usage with examples.

---

### Issue 2: Russicism — «найкрасивіше» (MEDIUM)

**Location:** Section «Частини мови: самостійні категорії», line 127
**Cited text:** «Це дозволяє нам будувати складні оцінки та висловлювати думки: «Київ — *найкрасивіше* місто, яке я бачив».»
**Problem:** «красивий» is flagged in the Russicism checklist (красивий → гарний / вродливий). The module itself uses «гарний» elsewhere (lines 17, 120, 124-127), making this inconsistent. An example sentence in a grammar teaching module should model standard Ukrainian.
**Fix:** Replace «найкрасивіше» with «найгарніше».

---

### Issue 3: Plan-Required Content Missing — Letter Ґ Cultural Hook (CRITICAL)

**Location:** Section «Частини мови: службові слова» (missing content)
**Plan requirement:** Plan section 3 explicitly requires: *"Cultural Hook: The letter 'Ґ' as a symbol of systematicity. Discuss its repression in 1933 and restoration in the 1990s as part of returning historical truth to grammar."*
**Problem:** The content mentions Smotrytskyi introducing «ґ» in the introduction callout (line 24), but the 1933 repression and 1990s restoration — the decolonization narrative central to the plan's intent — are completely absent from the module.
**Fix:** Add a [!decolonization] or [!culture] callout in section «Частини мови: службові слова» covering the 1933 suppression of ґ (Skrypnyk-era orthography ban) and its 1990s restoration.

---

### Issue 4: Plan-Required Content Missing — просте/складне речення (MEDIUM)

**Location:** Section «Частини мови: службові слова» (missing content)
**Plan requirement:** *"Distinction between 'просте речення' (simple sentence) and 'складне речення' (complex sentence) using service words as structural glue."*
**Problem:** Grep confirms zero matches for either term. The section discusses conjunctions joining sentences but never introduces the formal terminology.
**Fix:** Add a brief paragraph or sub-section introducing «просте речення» and «складне речення» with examples showing how service words (particularly сполучники) transform simple sentences into complex ones.

---

### Issue 5: Vocabulary Sidecar — 7 Required Case Names Missing (MEDIUM)

**Location:** Vocabulary file `/curriculum/l2-uk-en/b1/vocabulary/how-to-talk-about-grammar.yaml`
**Plan requirement:** The plan lists all 7 case names (називний відмінок through кличний відмінок) under `vocabulary_hints.required`.
**Problem:** The vocabulary file has 18 items but includes only «відмінок» as a general term. The 7 individual case names are absent.
**Fix:** Add 7 entries: називний відмінок, родовий відмінок, давальний відмінок, знахідний відмінок, орудний відмінок, місцевий відмінок, кличний відмінок — with their question prompts as context.

---

### Issue 6: Factual Overstatement — «унікальна» Used 4 Times (MEDIUM)

**Locations:**
- Line 260 (section «Частини мови: службові слова»): «Це унікальна риса, якою українці пишаються» — about euphony. Euphonic alternations exist in many languages.
- Line 416 (section «Відмінки: сім ключів»): «Це унікальна, архаїчна і дуже красива риса...» — about vocative. Vocative exists in Polish, Czech, Romanian, Latin, Greek, etc.
- Line 479 (section «Граматичні категорії та будова слова»): «робить її унікальною серед слов'янських мов» — about о/і alternation. Overstated.
- Line 498 (section «Граматичні категорії та будова слова»): «Це унікальна риса слов'янських мов» — about aspect. Aspect exists in other language families.

**Problem:** Repeated «unique» claims (4× in one module) constitute both factual inaccuracy and an LLM rhetoric pattern of exaggeration.
**Fix:** Replace with more accurate terms: «характерна» (characteristic), «особлива» (distinctive), «важлива» (important). Keep «unique» at most once, for the genuinely distinctive feature (vocative as full productive case, perhaps).

---

### Issue 7: Colonial Framing — Vocative Defined by Russian Contrast (LOW)

**Location:** Section «Відмінки: сім ключів», line 416
**Cited text:** «Це унікальна, архаїчна і дуже красива риса української мови, яка відрізняє її від багатьох інших слов'янських мов (наприклад, російської, де цей відмінок зник).»
**Problem:** Defines Ukrainian's vocative by explicit contrast with Russian. Per guidelines, "References to Russian as comparison point" should be flagged.
**Fix:** Reframe positively: «Українська мова зберегла кличний відмінок як повноцінну граматичну категорію — разом із польською, чеською та румунською.» Present Ukrainian alongside peers, not defined against Russian.

---

### Issue 8: LLM Filler — Confirmed (LOW)

**Location:** Section «Вступ: сила метамови», line 27
**Cited text:** «In this lesson, we will learn the Ukrainian names for all the grammatical concepts you already know intuitively.»
**Problem:** D.0 pre-screen confirmed. "In this lesson, we will" is a generic AI opener.
**Fix:** Rewrite to specific: «This module gives you the Ukrainian names for every grammatical concept you already use intuitively — parts of speech, cases, and sentence structure.»

---

### Issue 9: Missing Accusative vs Genitive Drill (LOW)

**Location:** Section «Відмінки: сім ключів» (missing from cases discussion)
**Plan requirement:** *"Addressing Learner Error (Accusative vs Genitive): Specific drill on 'Бачу брата' (Acc) vs 'Немає брата' (Gen) to clear confusion with animate nouns."*
**Problem:** The [!warning] box at line 373 addresses Accusative vs DATIVE confusion, not Accusative vs Genitive. The animacy concept is mentioned in the Noun section (lines 50-54) but never drilled with the specific Acc/Gen parallel the plan requires.
**Fix:** Add a brief comparison box or example pair in the Accusative section: «Бачу **брата** (Знахідний: кого?) vs Немає **брата** (Родовий: кого?)» with explanation of why both use the same form for animate nouns.

---

## Factual Verification

| Claim | Location | Verdict | Notes |
|-------|----------|---------|-------|
| Smotrytskyi published Grammar in 1619 | Line 24, section «Вступ: сила метамови» | ✅ Confirmed | Matches research notes |
| Smotrytskyi "officially introduced" letter ґ | Line 25, section «Вступ: сила метамови» | ⚠️ Overstated | Research says he "systematized grammar"; the specific ґ attribution is debatable — the letter existed before him |
| Mnemonic: Н-Р-Д-З-О-М-К | Lines 299-308, section «Відмінки: сім ключів» | ✅ Correct | Content correctly uses «Окуляри» (О) for Орудний; note that BOTH plan and meta incorrectly have «Горішки» (Г) |
| Present tense only imperfective | Line 92, section «Частини мови: самостійні категорії» | ✅ Correct | Standard grammatical fact |
| «З, із» governs only Instrumental | Line 242, section «Частини мови: службові слова» | ❌ Incorrect | «З» also governs Genitive (origin/separation) and Accusative (approximation) |
| Euphony is «unique» (унікальна) | Line 260, section «Частини мови: службові слова» | ❌ Overstated | Many languages have euphonic alternations |
| Vocative "unique" to Ukrainian among Slavic | Line 416, section «Відмінки: сім ключів» | ❌ Incorrect | Polish, Czech, and other Slavic languages preserve the vocative |
| О/І alternation "unique" among Slavic | Line 479, section «Граматичні категорії та будова слова» | ⚠️ Overstated | Distinctive but not truly unique |
| Aspect is «unique» to Slavic languages | Line 498, section «Граматичні категорії та будова слова» | ⚠️ Overstated | Aspect exists in other language families (Semitic, some Niger-Congo) |
| Shevchenko «Заповіт» quote | Lines 553-559, section «Практика: читаємо граматику українською» | ✅ Correct | «Як умру, то поховайте мене на могилі» is authentic |
| Grammar analysis of Shevchenko | Lines 556-559, section «Практика: читаємо граматику українською» | ✅ Correct | All POS/case/mood identifications accurate |

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| **Russianisms** | ⚠️ 1 found | «найкрасивіше» (line 127, section «Частини мови: самостійні категорії») — красивий is a flagged Russicism |
| **Colonial framing** | ⚠️ 1 found | Russian used as comparison baseline for vocative (line 416, section «Відмінки: сім ключів») |
| **Grammar accuracy** | ❌ 1 error | «З, із + Орудний» omits Genitive/Accusative governance (line 242, section «Частини мови: службові слова») |
| **Factual accuracy** | ⚠️ Multiple | 4× «unique» overstatements, 1 overstated attribution (Smotrytskyi/ґ) |
| **LLM filler** | ⚠️ 1 confirmed | «In this lesson, we will» (line 27, section «Вступ: сила метамови») |
| **LLM fingerprint** | ⚠️ Moderate | 4× «унікальна» repetition, identical H3 structure across 6 POS subsections |
| **Plan compliance** | ❌ 5 gaps | Missing: Ґ cultural hook, просте/складне речення, Acc/Gen drill, 7 case vocab entries, відміна іменника |
| **Activity quality** | ✅ Good | All 4 types present, quantities met, error-correction items are strong |
| **Word count** | ✅ 5225/4000 | 130.6% — well above minimum |
| **Engagement** | ✅ 7 boxes | Varied types, good mnemonic, strong analogies |

---

## Verdict

**CONDITIONAL PASS — Requires targeted fixes before final approval.**

The module demonstrates strong pedagogical craft: warm teacher voice, effective analogies, thorough coverage of all parts of speech and cases, and well-structured activities. The 5225-word count (130.6%) reflects genuine depth, not padding.

However, three issues require repair before this module can pass:

1. **Grammar inaccuracy** (line 242): «З, із + Орудний» is factually incomplete and misleading for a metalanguage module. This is the highest-priority fix.
2. **Plan compliance gaps**: The missing Ґ decolonization narrative, missing просте/складне речення distinction, and missing 7 case names from vocabulary sidecar represent significant departures from the approved plan.
3. **Repeated factual overstatements**: 4× «unique» claims damage credibility. A metalanguage module that teaches precision should model precision.

**Priority Fix Order:**
1. Fix «з/із» governance (grammar accuracy — critical)
2. Add Ґ cultural hook with 1933/1990s narrative (plan compliance)
3. Replace «найкрасивіше» → «найгарніше» (Russicism)
4. Reduce «унікальна» to 1 occurrence, use accurate alternatives
5. Add просте/складне речення paragraph
6. Add 7 case names to vocabulary sidecar
7. Reframe vocative description without Russian contrast
8. Rewrite LLM filler at line 27
9. Add Accusative vs Genitive comparison (plan compliance)