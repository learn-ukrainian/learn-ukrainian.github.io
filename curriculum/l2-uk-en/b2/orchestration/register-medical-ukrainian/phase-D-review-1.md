# Рецензія: Медична українська: спілкування у сфері охорони здоров'я

**Reviewed-By:** claude-opus-4-6

**Level:** B2 | **Module:** b2-20
**Overall Score:** 8.3/10
**Status:** FAIL
**Reviewed:** 2026-02-25

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 6/6 present, but 2 header deviations:
  - Plan: "Медична документація та цифровізація" → Content: "Медична документація та цифровізація суспільства" (added "суспільства")
  - Plan: "Культура мовлення та корекція русизмів" → Content: "Культура мовлення: корекція суржику та русизмів" (added "суржику", changed conjunction to colon)
- Vocabulary: 30/20 from plan (10 required, 10 recommended = all present, +10 relevant extras)
- Grammar scope: CLEAN — no scope creep detected
- Objectives: Both objectives addressed (medical register analysis + communication skills)
- Activity hints: PARTIAL — fill-in 10/12 items (under), reading 3/4 texts (under)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Strong "Чому це важливо?" hook with practical framing; Amosov cultural section is compelling. But lecture-heavy format without discovery moments reduces engagement. |
| 2 | Coherence | 9/10 | <7 | Excellent arc: pharmacy → symptoms → doctor visit → treatment/Amosov → documentation → language correction. Logical progression from casual (pharmacy) to formal (documentation). |
| 3 | Relevance | 9/10 | <7 | Directly practical for B2 learners in Ukraine: Helsi.me, e-prescriptions, pharmacy interactions, medical documents for employment. Real-world applicability is outstanding. |
| 4 | Educational | 8/10 | <7 | Solid grammar explanations (біль gender, лікувати/лікуватися, відділ/відділення). However, no scaffolding from easy→hard within sections. Concept density is high without sufficient processing breaks. |
| 5 | Language | 9/10 | <8 | Ukrainian is natural and register-appropriate. No Russianisms in teaching content. Euphony respected. Some excessive verbosity (14 instances of extreme qualifiers like "надзвичайно", "абсолютно", "максимально", "категорично") but within acceptable range for teaching voice. |
| 6 | Pedagogy | 7/10 | <7 | No TTT structure — module is a straight lecture. Module type is "grammar" but no discovery/test-before-teach elements. Practice entirely in separate YAML, not integrated into prose. The [!tip] boxes ask reflective questions but don't require active production. |
| 7 | Immersion | 9/10 | <6 | 98.7% Ukrainian — well within B2.1 target of 95-100%. English appears only in parenthetical translations (e.g., "sick leave certificate", "Transitive verb"). Appropriate for level. |
| 8 | Activities | 8/10 | <7 | 14 activity types with good variety (quiz, fill-in, unjumble, error-correction, true-false, translate, select, match-up, reading, essay, group-sort, cloze). Distractors target real errors (gender of біль, суржик). But plan shortfalls: fill-in 10 vs 12+ required, reading 3 vs 4 texts required. |
| 9 | Richness | 9/10 | <6 | Culturally embedded: Amosov philosophy, Helsi.me interface, Ukrainian pharmacy culture, formal/informal medical term table. 12 callout boxes with varied types. Register comparison table (line 302-309). |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — practical topic with clear utility, but dense prose could overwhelm (several paragraphs exceed 500 words without breaks). At B2 this is manageable but not optimal. |
| 11 | LLM Fingerprint | 8/10 | <7 | Repetitive rhetorical formula «ніколи, за жодних обставин» appears 4 times (lines 152, 208, 247, 284). Section openings are varied (no structural monotony). No "це не просто" patterns. 14 instances of stacked extreme qualifiers across the text indicate some AI-typical over-emphasis. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL**: IPA stress error in vocabulary sidecar for "натщесерце": `` places stress on "тще" but correct stress is натщесе́рце → ``. Possible second stress error for "призначення" `` (standard: призначе́ння → ``). All grammar rule explanations are accurate. |
| 13 | Factual Accuracy | 9/10 | <8 | Amosov facts verified against research: cardiosurgeon, "система обмежень і навантажень", "1000 рухів", "Роздуми про здоров'я" — all accurate. Helsi.me description accurate. Quote «Лікарі лікують хвороби, а здоров'я треба здобувати самому» correctly attributed. No fabricated claims in callout boxes. |

**Weighted Overall:** (8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 7×1.2 + 9×1.0 + 8×1.3 + 9×0.9 + 8×1.3 + 8×1.0 + 8×1.5 + 9×1.5) / 15.5 = (12.0 + 9.0 + 9.0 + 9.6 + 9.9 + 8.4 + 9.0 + 10.4 + 8.1 + 10.4 + 8.0 + 12.0 + 13.5) / 15.5 = 129.3 / 15.5 = **8.3/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms in teaching content; Russianisms appear only in deliberate error-correction examples
- Calques: [CLEAN] — calques discussed pedagogically, not used in teaching voice
- Grammar scope: [CLEAN] — stays within medical register domain
- Activity errors: [CLEAN] — no factual errors in activity items found
- Beginner safety: 4/5
- Factual accuracy: [CLEAN] — Amosov facts, Helsi.me description, medical terminology all verified
- Colonial framing: [CLEAN] — [!decolonization] box on line 63 is a legitimate exception (explains interference source); line 61 uses «інших слов'янських мов» rather than naming Russian directly
- LLM fingerprint: Repetitive formula «ніколи, за жодних обставин» ×4 flagged but below auto-fail threshold

## Critical Issues Found

### Issue 1: IPA Stress Error — натщесерце (Linguistic Accuracy — AUTO-FAIL)
- **Location**: Vocabulary sidecar, line 145 / `vocabulary/register-medical-ukrainian.yaml`
- **Original**: `ipa: ''`
- **Problem**: Stress mark placed on "тще" syllable. The standard Ukrainian stress is натщесе́рце — stress falls on the "сер" syllable.
- **Fix**: Change to `ipa: ''`

### Issue 2: Possible IPA Stress Error — призначення (Linguistic Accuracy)
- **Location**: Vocabulary sidecar, line 59 / `vocabulary/register-medical-ukrainian.yaml`
- **Original**: `ipa: ''`
- **Problem**: Stress placed on "зна" syllable, corresponding to при**зна́**чення. Standard stress is призначе́ння with stress on "чен" syllable. Needs verification.
- **Fix**: If confirmed, change to `ipa: ''`

### Issue 3: Activity Count Shortfall — Plan Non-Compliance (Activities)
- **Location**: Activities YAML / `activities/register-medical-ukrainian.yaml`
- **Problem**: Plan specifies fill-in 12+ items but only 10 provided (lines 174-244). Plan specifies 4 reading texts but only 3 provided (reading-1, reading-2, reading-3 — lines 722-753).
- **Fix**: Add 2 more fill-in items to reach 12. Add 1 more reading text (e.g., a medical discharge summary or a pharmacist consultation dialogue).

### Issue 4: No TTT Structure in Grammar Module (Pedagogy)
- **Location**: All 6 H2 sections — section «Вступ: Медичний регістр та культура аптеки» through section «Культура мовлення: корекція суржику та русизмів»
- **Problem**: Module type is "grammar" but uses pure lecture format. Every section follows Explain → Example → More Explanation. No discovery tasks, no test-before-teach moments. The [!tip] boxes (lines 93, 102, 124, 201) ask reflective questions but these are passive — they don't constitute a TTT "test" phase.
- **Fix**: Add at least 2 discovery micro-tasks at section openings. For example, in section «Опис симптомів та відчуттів» (line 49), present 3 sentences with "біль" in different genders and ask learners to identify which is correct BEFORE explaining the rule. In section «Консультація: Діалог лікар-пацієнт» (line 127), present fill-the-gap dialogue sentences BEFORE explaining лікувати/лікуватися distinction.

### Issue 5: Repetitive Absolute Prohibition Formula (LLM Fingerprint)
- **Location**: Lines 152, 208, 247, 284
- **Original**: «ніколи, за жодних обставин» appears 4 times across the module
- **Problem**: This exact phrasing repeated 4 times creates a rhetorical monotony pattern. Real teachers vary their emphatic language.
- **Fix**: Keep 1-2 instances and vary the rest: replace with «у жодному разі», «за жодних умов», «ні в якому випадку», or simply «ніколи».

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| vocab:145 | IPA `` | `` | IPA Stress |
| vocab:59 | IPA `` | `` (verify) | IPA Stress |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass] — B2 learners can handle density, though some paragraphs push limits
- Instructions clear? [Pass] — Grammar explanations are thorough and well-illustrated
- Quick wins? [Pass] — Gender of "біль" and "брати участь" are clear, actionable takeaways
- Ukrainian scary? [Pass] — Practical medical context motivates learning
- Come back tomorrow? [Fail] — Lecture-only format without integrated practice may reduce return motivation; no sense of progressive mastery within the lesson itself

## Strengths
- **Outstanding cultural integration**: Ukrainian pharmacy culture as first point of contact (section «Вступ: Медичний регістр та культура аптеки»), Amosov philosophy with real quote (section «Медичні інструкції та філософія Амосова»), and Helsi.me digital health system create genuinely useful cultural context
- **Excellent error-correction pedagogy**: Section «Культура мовлення: корекція суржику та русизмів» handles суржик correction well — "осмотр → огляд/обстеження" distinction with functional differentiation, "приймати участь → брати участь" with explanation of legitimate uses of "приймати"
- **Rich activity variety**: 14 activity types covering recognition (quiz, true-false), production (essay, fill-in), analysis (error-correction), and synthesis (cloze). The error-correction activities target real learner errors (gender of біль, відділ/відділення).
- **Decolonization done right**: The [!decolonization] callout (line 63) explains interference source without defining Ukrainian by contrast with Russian. The main text (line 61) carefully uses «інших слов'янських мов» rather than naming Russian directly.
- **Practical Helsi.me template**: The digital complaint template (section «Медична документація та цифровізація суспільства», lines 261-273) is immediately actionable for learners living in Ukraine.

## Fix Plan to Reach 9.0/10 (REQUIRED — score is 8.3)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Vocab line 145: Change IPA for "натщесерце" from `` to `` — corrects stress placement
2. Vocab line 59: Verify and likely correct IPA for "призначення" from `` to `` — standard stress is призначе́ння

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 8/10
**What to fix:**
1. Section «Опис симптомів та відчуттів» (line 49): Insert a 3-sentence discovery task before the grammar rule. Present sentences with біль in masculine, feminine, and neuter and ask learner to identify the correct one. Then teach the rule.
2. Section «Консультація: Діалог лікар-пацієнт» (line 127): Insert a mini-dialogue with blanks (лікувати/лікуватися) before the formal explanation. Let learners attempt before explaining.
3. Section «Медична документація та цифровізація суспільства» (line 222): Before the відділ/відділення explanation, present 4 real-world locations and ask learner to classify them. Then teach the rule.

**Expected score after fix:** 8/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Add 2 fill-in items to reach 12+ (plan requirement). Focus on medical documentation terms (лікарняний лист, виписка).
2. Add 1 reading text — a realistic medical discharge summary or pharmacy consultation vignette with 3 comprehension tasks.

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Lines 152, 208, 247, 284: Replace 2-3 of the 4 «ніколи, за жодних обставин» instances with varied emphatic phrases (e.g., «у жодному разі», «за жодних умов»).
2. Reduce extreme qualifier density: Review the 14 instances of "надзвичайно/абсолютно/максимально/категорично" and remove 4-5 where they don't add pedagogical value.

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add discovery tasks (as per Pedagogy fixes above) to create engagement beats.
2. Break the longest paragraphs in sections «Вступ: Медичний регістр та культура аптеки» and «Консультація: Діалог лікар-пацієнт» into smaller chunks. Lines 16, 22, and 24 are each full paragraphs exceeding 500 characters.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 9×1.0 + 9×1.3 + 9×0.9 + 8×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 9.6 + 9.9 + 9.6 + 9.0 + 11.7 + 8.1 + 10.4 + 9.0 + 13.5 + 13.5) / 15.5
= 135.8 / 15.5
= 8.76/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not applicable — B2 Core, not seminar)
- Dates checked: 0 (no specific historical dates in content)
- Named figures verified: 1 (Микола Амосов — facts confirmed against research notes: cardiosurgeon, "система обмежень і навантажень", "1000 рухів", "Роздуми про здоров'я")
- Primary quotes cross-referenced: 1/1 matched (Amosov quote on line 194 matches reading activity text on line 727 and research notes)
- Chronological sequence: CONSISTENT (no historical timeline to verify)
- Claims without research grounding: 0

Callout box verification:
- [!culture] "Амосов у масовій культурі" (line 182): Claims his name is known by every Ukrainian, 1000 рухів system, Київський інститут серцево-судинної хірургії named after him — all plausible and widely documented. PASS.
- [!decolonization] (line 63): Explains Russian interference on біль gender — accurate linguistic fact. PASS.
- [!culture] "Що у вас є від..." (line 36): Describes pharmacy culture — culturally accurate. PASS.
- [!quote] (line 193): Amosov quote verified against research and activity reading text. PASS.

## Verification Summary

- Content lines read: 332
- Activity items checked: 131 (across 14 activity blocks)
- Ukrainian sentences verified: 40+
- IPA transcriptions checked: 30/30 (2 stress errors found)
- Factual claims verified: 8
- Issues found: 5

## Verdict

**FAIL**

Auto-fail triggered by Linguistic Accuracy (8/10 < 9 threshold) due to confirmed IPA stress error on "натщесерце" in vocabulary sidecar. The fix is straightforward: correct the stress placement in 1-2 IPA transcriptions, add 2 fill-in items and 1 reading text to meet plan requirements, and add 2-3 discovery micro-tasks for TTT compliance. The content itself is well-written, culturally rich, and pedagogically sound in its explanations — the blocking issues are in the vocabulary sidecar IPA and structural pedagogy, not in the prose quality.