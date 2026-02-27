**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Language | 7/10 | Colonial framing at line 153 (Ukrainian numerals defined by contrast with Russian). Grammar explanation error at line 46 (claims non-living objects don't change in Accusative — incorrect for feminine nouns). English prose is warm and accessible. |
| 2 | Factual Accuracy | 7/10 | The statement at line 46 that non-living nouns "does not change" in Accusative is factually wrong for feminine nouns (книга→книгу, аптека→аптеку). This directly contradicts Activity #6 item 4 which correctly tests аптека→аптеку. Arsenalna depth (105.5m) appears correct. |
| 3 | Immersion Balance | 6/10 | Measured at 18.5% Ukrainian against target 25-40%. For an A1.2 module (sequence 20), the tier guidance suggests 40-60% Ukrainian. The content is overwhelmingly English with Ukrainian only in example sentences and the integration dialogue. |
| 4 | Richness | 7/10 | Two solid cultural hooks (Arsenalna station in section «Навичка 2: Місцевий відмінок», Zoloti Vorota in section «Навичка 5: Орієнтування в місті»). Good hospitality note in section «Навичка 3: Родовий відмінок». However, vocabulary item "вулиця" never appears in prose, "зупинка" only in activities. No named Ukrainian films, songs, or media references beyond metro stations. |
| 5 | Lesson Quality | 7/10 | Arc structure is solid (WELCOME→PREVIEW→PRESENT→PRACTICE→CELEBRATE). However, the grammar error in section «Навичка 1: Знахідний відмінок» could cause real learner confusion. Structural monotony across skill sections (all follow identical Model→Practice→Self-Check subpattern). The integration dialogue in section «Інтеграція: Практика в місті» is effective. |
| 6 | Humanity & Warmth | 7/10 | "Don't worry about making mistakes" at line 19, "that's okay" at line 34, "Congratulations!" at line 359, "Good luck!" at line 372. But encouragement is front-loaded and back-loaded — sections «Навичка 1» through «Навичка 5» have zero explicit encouragement phrases. No "Great!", "Well done!", or "Молодець" anywhere in the module. |
| 7 | LLM Fingerprint | 7/10 | Three consecutive sections open identically: «The Accusative Case is for the "direct object"» (line 40), «The Locative Case is your GPS» (line 86), «The Genitive Case is very common» (line 136) — all "The [X] Case is..." pattern. All five skill sections share identical internal structure (explanation → warning box → Model → Practice → Self-Check). |
| 8 | Activity Quality | 7/10 | Good variety: group-sort (2), match-up (2), quiz (2), fill-in (3), unjumble (1). Total 10 activities. However, Activity #6 "Правильне закінчення" item 4 (аптека→аптеку) contradicts the prose claim that non-living objects don't change. Quiz items at activity #7 "Числа та іменники" are pedagogically sound. |

---

## Critical Issues Found

### Issue 1: Grammar Error — Feminine Accusative Misrepresentation (CRITICAL)

**Location:** Section «Навичка 1: Знахідний відмінок», lines 45-48

**Content:** The prose states:
> «This is the easy part. The word **does not change**. It looks exactly like it does in the dictionary (Nominative case).»
> «**Я бачу парк.** (I see a park.)»
> «**Я читаю журнал.** (I read a magazine.)»

**Problem:** This rule is only true for masculine and neuter inanimate nouns. Feminine nouns in -а/-я always change in the Accusative regardless of animacy: книга→книгу, аптека→аптеку, вода→воду, кава→каву. The examples only show masculine nouns (парк, журнал), hiding the error. Activity #6 item 4 correctly tests «Він іде в ____.» with answer «аптеку» (line 204-207) — directly contradicting the prose explanation. A learner who trusts the prose rule would answer "аптека" and get it wrong.

**Fix:** Rewrite lines 45-48 to specify: "For **masculine** non-living nouns, the word does not change (парк→парк, журнал→журнал). For **feminine** nouns in -а/-я, the ending changes: -а→-у, -я→-ю (книга→книгу, аптека→аптеку)."

---

### Issue 2: Colonial Framing — Ukrainian Defined Through Russian Comparison (CRITICAL)

**Location:** Section «Навичка 3: Родовий відмінок», line 153

**Content:**
> «After the numbers 2, 3, and 4, Ukrainian uses the **Nominative plural** form. This is an important difference from Russian, which uses the Genitive singular in the same position (Russian: "два студента"; Ukrainian: "два студенти").»

**Problem:** This defines a Ukrainian grammatical feature by comparing it to Russian. An A1 learner doesn't need to know what Russian does. The Ukrainian rule should stand on its own.

**Fix:** Remove the Russian comparison entirely. Replace with: "After the numbers 2, 3, and 4, Ukrainian uses the **Nominative plural** form. Think of it this way: you're counting visible things, so they stay in their basic plural form."

---

### Issue 3: Vocabulary IPA Error — Double Stress Mark

**Location:** Vocabulary file, line 95-96

**Content:** `ipa: ''` for коштувати

**Problem:** Two primary stress marks (ˈkɔʃtu and ˈʋɑtɪ). Ukrainian words have exactly one primary stress. The correct stress is коштува́ти, so the IPA should be ``.

**Fix:** Change to `ipa: ''` (remove the first stress mark).

---

### Issue 4: Immersion Below Target

**Location:** Entire module

**Problem:** Measured at 18.5% Ukrainian against a 25-40% target. For A1.2 (module 20), the tier guidance suggests 40-60%. The vast majority of the content is English prose with Ukrainian appearing only in example sentences and the integration dialogue.

**Fix:** Increase Ukrainian content by:
- Adding Ukrainian section headers with English translations (not just Ukrainian H2s with English bodies)
- Using more Ukrainian in the Practice and Self-Check subsections
- Adding short Ukrainian phrases inline throughout explanations (with translations in parentheses)
- Making the integration dialogue longer and adding a second shorter dialogue mid-module

---

### Issue 5: Integration Section Deviates from Outline

**Location:** Section «Інтеграція: Практика в місті», lines 308-340

**Problem:** The meta outline specifies «Сценарій: Турист біля метро 'Арсенальна' шукає парк Вічної Слави» but the actual content has Tom looking for a coffee shop near Zoloti Vorota. Also, the meta says «Інтеграція: Практика в Києві» but the content header reads «Інтеграція: Практика в місті».

**Fix:** Either update the dialogue to match the outline (Arsenalna → Park of Eternal Glory scenario) or update the meta to reflect the actual scenario. The coffee shop scenario works well pedagogically, so updating the meta is the simpler path.

---

### Issue 6: Vocabulary-Content Mismatch

**Location:** Vocabulary file vs. content prose

**Problem:** "вулиця" (street) appears in the vocabulary file (line 63) but is never used in the content prose. "зупинка" (stop) appears only in activities (match-up), never in prose. Both are highly relevant navigation words that should appear in the lesson text.

**Fix:** Incorporate «вулиця» and «зупинка» into section «Навичка 5: Орієнтування в місті» — e.g., «Ідіть по вулиці прямо до зупинки» in the directions practice or transport vocabulary subsection.

---

### Issue 7: Mid-Module Encouragement Desert

**Location:** Sections «Навичка 1» through «Навичка 5» (lines 38-305)

**Problem:** Between "Don't worry about making mistakes" (line 19) and "Congratulations!" (line 359), there are approximately 2,200 words with zero explicit encouragement. A nervous A1 beginner working through five grammar skills needs periodic reassurance.

**Fix:** Add at least 2-3 encouragement moments within the skill sections:
- After section «Навичка 1: Знахідний відмінок» Self-Check: "If you got this, great — the Accusative is your first tool."
- After section «Навичка 3: Родовий відмінок» Self-Check: "Three cases down! You're doing really well."
- Before section «Навичка 5: Орієнтування в місті»: "You've reviewed the grammar. Now let's use it!"

---

## Factual Verification

### Callout Box Verification

1. **[!culture] "Kyiv Underground"** (section «Навичка 2: Місцевий відмінок», lines 112-116): Claims Arsenalna station is "the deepest in the world (105.5 meters)." This is a widely cited and accepted fact. The IPA `` is plausible. **PASS.**

2. **[!culture] "Golden Gate"** (section «Навичка 5: Орієнтування в місті», lines 270-272): Claims Zoloti Vorota is "famous for its mosaics and looks like an underground palace" and mentions meeting "by the monument to Yaroslav the Wise." The station IS known for its ornate interior with mosaics depicting scenes from Kyivan Rus. The Yaroslav the Wise monument is near the station exit. **PASS.**

3. **[!culture] "Ukrainian Hospitality"** (section «Навичка 3: Родовий відмінок», lines 172-174): Claims "a host will rarely say 'Немає...'" and that «Квитків немає» is common for sold-out events. This is culturally plausible and pedagogically useful. **PASS.**

### Grammar Rule Verification

1. **Line 46:** "Non-living objects: The word does not change." — **FAIL.** Only true for masculine/neuter inanimate. Feminine inanimate nouns DO change (аптека→аптеку). See Critical Issue #1.

2. **Line 102:** "Almost all singular nouns get the ending -і." — Acceptable A1 simplification. The -у exception for парк is noted. **PASS with caveat** (other -у exceptions like вокзалу, мосту exist but are reasonable to defer).

3. **Line 153:** "Ukrainian uses the Nominative plural form [after 2, 3, 4]" — The grammatical claim itself is correct for standard teaching. The problem is the Russian comparison, not the rule statement. **PASS** (grammar); **FAIL** (framing).

4. **Line 217:** «Його» (his) and «її» (her) do not change — **PASS.** These possessive pronouns are invariable.

5. **Line 221:** «Їхній» (masc.), «їхня» (fem.), «їхнє» (neut.) and colloquial «їх» — **PASS.** Standard forms.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Colonial framing | **FOUND** | Line 153: Ukrainian numerals defined by comparison to Russian |
| Grammar accuracy | **ERROR** | Line 46: Feminine accusative misrepresented as unchanged |
| Factual claims | PASS | Arsenalna depth, Zoloti Vorota description verified |
| IPA accuracy | **ERROR** | Vocab "коштувати" has double stress mark |
| Outline compliance | **PARTIAL** | Section structure matches meta but integration scenario diverges |
| Vocabulary coverage | **GAP** | вулиця absent from prose; зупинка only in activities |
| Activity accuracy | PASS | All activity answers are grammatically correct |
| Prose-activity consistency | **CONFLICT** | Line 46 prose contradicts activity #6 item 4 |
| Encouragement density | **LOW** | ~2200 words between encouragement markers |
| Structural monotony | **DETECTED** | 3 sections with "The [X] Case is..." openings |
| Immersion | **BELOW TARGET** | 18.5% vs 25-40% target |

**Section Coverage:**
- Section «Огляд: Навігація» — reviewed (warmth, preview quality)
- Section «Навичка 1: Знахідний відмінок» — reviewed (Critical Issue #1: grammar error)
- Section «Навичка 2: Місцевий відмінок» — reviewed (culture box verified, consonant shifts accurate)
- Section «Навичка 3: Родовий відмінок» — reviewed (Critical Issues #2 colonial framing, #1 factual accuracy)
- Section «Навичка 4: Присвійні займенники» — reviewed (possessive forms correct, good gender agreement practice)
- Section «Навичка 5: Орієнтування в місті» — reviewed (vocabulary gap: вулиця/зупинка missing from prose)
- Section «Інтеграція: Практика в місті» — reviewed (effective dialogue, scenario deviates from outline)

---

## Verdict

**FAIL — Revision Required**

The module has a solid pedagogical arc and effective cultural hooks, but three issues prevent passing:

1. **Grammar error** (line 46) that will cause learner confusion — the prose teaches an incorrect rule that the module's own activities contradict.
2. **Colonial framing** (line 153) that defines Ukrainian grammar through Russian comparison — must be removed.
3. **Immersion at 18.5%** is below even the minimum 25% threshold.

**Priority fixes:**
1. Fix the feminine accusative explanation in section «Навичка 1: Знахідний відмінок» (Critical)
2. Remove the Russian comparison in section «Навичка 3: Родовий відмінок» (Critical)
3. Fix the IPA double stress in vocabulary (Quick fix)
4. Add Ukrainian text throughout to bring immersion above 25% (Moderate effort)
5. Add mid-module encouragement phrases (Quick fix)
6. Incorporate missing vocabulary (вулиця, зупинка) into prose (Quick fix)