<!-- content-hash: cfb362725499 -->
# Рецензія: The Gender Code

**Level:** A1 | **Module:** 7
**Overall Score:** 7.6/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-20250514

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: 5/5 present ✅
- Vocabulary: 8/8 required in prose ✅, 12/12 recommended in prose ✅, 4 prose words missing from vocab YAML
- Grammar scope: PARTIAL — declension families objective unmet
- Objectives: 3/4 met, 1 MISSING (see below)
```

### Plan Adherence Checklist

**Objectives:**
- ✅ COVERED: "Learner can identify noun gender by word ending" — entire module teaches this
- ❌ MISSING: "Learner can categorize nouns into 4 declension families" — only a passing mention of "Family 4" on line 47: 「However, **ім'я́** belongs to a special historical group (Family 4) and is actually Neuter!」 No systematic overview of all 4 declension families exists
- ✅ COVERED: "Learner recognizes patterns: consonant (m), -а/-я (f), -о/-е (n)" — lines 15-19 and throughout
- ✅ COVERED: "Learner can identify common exceptions" — тато, день/ніч, ім'я all covered

**Section "Вступ (Introduction)" points:**
- ✅ COVERED: Three-gender system intro — line 3
- ✅ COVERED: Cultural Hook: Neuter Sun — line 7
- ✅ COVERED: Visual Mnemonic Framework — line 9

**Section "Презентація правил (Presentation of Rules)" points:**
- ✅ COVERED: Pattern Recognition — lines 15-19
- ✅ COVERED: Possessive pronouns as diagnostic tool — line 21
- ✅ COVERED: Syntactic Agreement — lines 23-26
- ✅ COVERED: Family Dialogue — lines 28-36

**Section "Практичні вправи (Practice Exercises)" points:**
- ✅ COVERED: Natural Gender Override Trap (тато) — line 40
- ✅ COVERED: Soft Sign Ambiguity — lines 42-45
- ✅ COVERED: Name Trap / Family 4 — line 47
- ✅ COVERED: Categorization drill — lines 52-55

**Section "Самостійна робота (Independent Work/Production)" points:**
- ✅ COVERED: "It" Trap Correction — lines 61-66
- ✅ COVERED: S.T.A.L.K.E.R. vocabulary — lines 68-71
- ✅ COVERED: Applying Agreement — lines 73-78

**Section "Культурний код та підсумок (Cultural Code and Summary)" points:**
- ✅ COVERED: Summary of gender prediction — line 84
- PARTIAL: Cultural Reflection — line 86 covers земля-мати but "сонце-життя" is fabricated (see Critical Issues)
- ✅ COVERED: Final Competency Check — lines 88-92

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm and encouraging throughout. Good arc from welcome → practice → celebrate. One engagement box is thin — only 「[!tip] The Golden Rule of Practice」 on line 49. Missing a second callout. |
| 2 | Language | 8/10 | <8 | English is clear and accessible. Ukrainian grammar is accurate. One issue: "memorised" (British spelling, line 84) should be "memorized" for consistency. The expression 「**со́нце-життя́** (Sun-Life)」 on line 86 is not a real Ukrainian compound. |
| 3 | Pedagogy | 8/10 | <7 | PPP structure well executed. Missing plan objective (4 declension families). Good contrastive pairs (тато/місто, день/ніч, земля/ім'я). The tip box on line 50 is excellent pedagogy: 「Don't just learn **соба́ка** (dog); learn **моя́ соба́ка**.」 |
| 4 | Activities | 8/10 | <7 | 8 activities with good variety (match-up ×2, quiz, fill-in, group-sort, true-false, anagram, unjumble). All items checked — correct answers, good explanations. Missing: no activity tests the "It" Trap (він/вона/воно for objects), which is heavily taught in section "Самостійна робота (Independent Work/Production)". |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Not overwhelmed, instructions clear, quick wins present, Ukrainian introduced gently with translations, encouraging throughout. |
| 6 | LLM Fingerprint | 7/10 | <7 | 「This system is the heartbeat of the language」 (line 5) — stacked abstract metaphor. 「You have successfully unlocked the Gender Code!」 (line 84) — gamified LLM rhetoric. 「You are not just learning rules; you are learning to think and feel in Ukrainian.」 (line 94) — "не просто X, а Y" pattern in English. The fabricated compound 「со́нце-життя́」 is LLM-typical invention. Structural monotony: sections 3-5 all open with "Let's..." |
| 7 | Linguistic Accuracy | 9/10 | <9 | All Ukrainian forms verified correct: possessive agreement (мій/моя/моє), adjective agreement (великий стіл, цікава книга, чисте вікно). Stress marks accurate where present. One fabricated cultural term: со́нце-життя́ is not attested. |

**Weighted Overall:** (8×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 9×1.3 + 7×1.0 + 9×1.5) / 8.9 = (12 + 8.8 + 9.6 + 10.4 + 11.7 + 7.0 + 13.5) / 8.9 = 73.0 / 8.9 = **8.2/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms detected
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — Romance language comparison (line 7) is legitimate cross-linguistic pedagogy, not Russian contrast
- Grammar scope: [CLEAN] — no grammar from later modules introduced
- Activity errors: [CLEAN] — all answers correct, no duplicate options
- Beginner safety: 5/5
- Factual accuracy: [1 ISSUE] — "со́нце-життя́" presented as Ukrainian cultural concept; not attested in textbooks or standard usage
- "95% predictability" (lines 13, 84) — plausible approximation but unsourced

## Critical Issues Found

### Issue 1: Fabricated Ukrainian Expression — "со́нце-життя́"
- **Location**: Line 86, Section "Культурний код та підсумок (Cultural Code and Summary)"
- **Original**: 「We say **со́нце-життя́** (Sun-Life) because the neuter sun is an impartial, balancing force for all living things.」
- **Problem**: "Земля-мати" (Mother Earth) is a well-established Ukrainian expression. "Сонце-життя" is NOT a standard Ukrainian compound noun or cultural concept. RAG textbook search returned no matches. VESUM does not list it. This appears to be an LLM fabrication presented as a real cultural expression. The plan itself lists it (line 63: "сонце-життя"), so this is a plan-inherited error, but the content should not present fabricated expressions as cultural facts.
- **Fix**: Replace with a real Ukrainian expression or reframe. E.g., refer to "ясне сонце" (bright sun) or "красне сонечко" (dear little sun) — both genuine folk expressions. Or simply drop the parallel and keep only земля-мати.
- **Severity**: HIGH

### Issue 2: Missing Plan Objective — 4 Declension Families
- **Location**: Entire module; plan objective #2: "Learner can categorize nouns into 4 declension families"
- **Problem**: The content only mentions "Family 4" once in passing (line 47: 「belongs to a special historical group (Family 4)」). There is no systematic presentation of what the 4 declension families are, how they differ, or how to categorize nouns into them. This is a plan objective that is entirely unmet.
- **Fix**: Add a brief overview table or callout box in section "Презентація правил (Presentation of Rules)" that previews the 4 families at recognition level (not full detail). E.g., a `[!did-you-know]` box explaining the 4 families exist and that learners will explore them more in later modules.
- **Severity**: MEDIUM

### Issue 3: Low Immersion (8.5% vs 15-35% target)
- **Location**: Whole module
- **Problem**: Module 7 falls in the 6-10 band, targeting 15-35% Ukrainian. At 8.5%, the immersion is well below minimum. Most Ukrainian appears only as bolded inline words with immediate English translations.
- **Fix**: Add 2-3 short Ukrainian reading practice blocks after key sections. E.g., after section "Практичні вправи (Practice Exercises)", add a 3-4 sentence block: "Це мій стіл. Стіл великий. А це моя книга. Книга цікава." These simple, repetitive sentences increase immersion without overwhelming the learner.
- **Severity**: MEDIUM

### Issue 4: Only 1 Engagement Box (need ≥2)
- **Location**: Only 「[!tip] The Golden Rule of Practice」 on line 49
- **Problem**: Audit reports engagement: 1/2. The module needs at least 2 engagement callout boxes. There are no `[!did-you-know]`, `[!culture]`, or `[!fun-fact]` boxes.
- **Fix**: Add a `[!did-you-know]` box. Natural candidate: a box in section "Культурний код та підсумок (Cultural Code and Summary)" about the cultural significance of земля-мати in Ukrainian folklore, or a box in section "Вступ (Introduction)" noting that Ukrainian has 3 genders while English lost its gender system centuries ago.
- **Severity**: MEDIUM

### Issue 5: Vocabulary YAML Missing Prose Words
- **Location**: Vocabulary file (`the-gender-code.yaml`)
- **Problem**: хліб (line 15), кімната (line 17), чоловік (line 53), жінка (line 54) all appear as teaching examples in the prose and/or activities but are absent from the vocabulary YAML. хліб is used in pattern recognition examples and the group-sort activity. кімната is used in the pattern recognition and match-up activity. чоловік and жінка are used in the categorization drill.
- **Fix**: Add all 4 words to the vocabulary YAML as supplementary items.
- **Severity**: LOW

### Issue 6: LLM Structural Monotony — "Let's..." Openings
- **Location**: Section openings
- **Problem**: 3 sections begin with "Let's..." variants: "Let's start with a beautiful cultural hook" (line 7, section "Вступ (Introduction)"), "Now, let's look at how we can actually predict" (line 13, section "Презентація правил (Presentation of Rules)"), "Let's dive into some practical exercises" (line 40, section "Практичні вправи (Practice Exercises)"). This is a structural monotony pattern.
- **Fix**: Vary section openings. E.g., section "Практичні вправи (Practice Exercises)" could open with "Time to put those rules to the test!" instead.
- **Severity**: LOW

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 86 | 「со́нце-життя́」 | Remove or replace with "красне сонечко" | Fabricated compound |
| 84 | "memorised" | "memorized" | Spelling inconsistency (British/American) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — content is well-paced with manageable chunks
- Instructions clear? **Pass** — always clear what the learner should do
- Quick wins? **Pass** — early successes with color-coding mnemonic, then progressive practice
- Ukrainian scary? **Pass** — introduced gently with translations
- Come back tomorrow? **Pass** — encouraging tone throughout, progress celebration at end

## Strengths
- **Excellent contrastive pairs**: тато/місто, день/ніч, земля/ім'я — each pair teaches a specific exception through comparison. This mirrors Vашуленко Grade 3 antonym-pairing methodology (confirmed in research notes).
- **S.T.A.L.K.E.R. cultural hook** is genuinely engaging for the target audience (teens + adults). 「If you are familiar with the famous Ukrainian video game franchise S.T.A.L.K.E.R., you can use its iconic vocabulary as classification anchors for our three buckets」 — creative and culturally authentic.
- **Golden Rule tip** on line 50: 「Don't just learn **соба́ка** (dog); learn **моя́ соба́ка**.」 — this is excellent A1 pedagogy that builds the right habits from day one.
- **Activity variety**: 8 activities across 7 types. The group-sort "three buckets" mirrors the color-coded mnemonic from the prose.
- **Dialogue block** (lines 30-34): 「Вдо́ма (At home)」 is natural and contextualizes family vocabulary beautifully.

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.2)

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 5: Replace 「This system is the heartbeat of the language」 with a simpler statement like "This system is the foundation of the language" — removes stacked metaphor
2. Line 86: Remove the fabricated 「со́нце-життя́」 and replace with genuine folk reference or simply expand земля-мати discussion
3. Vary section openings — change at least 1 of the 3 "Let's..." openings

**Expected score after fix:** 8/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 84: "memorised" → "memorized" for consistency
2. Line 86: Remove fabricated "сонце-життя" — this is a language accuracy issue when presenting Ukrainian cultural concepts

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add a brief declension families preview (callout box) in section "Презентація правил (Presentation of Rules)" to address the missing plan objective
2. Add 1 engagement box (e.g., `[!did-you-know]`) to meet richness gate

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add a second engagement callout box (fixes richness gate)
2. Add 2-3 short Ukrainian reading practice blocks (fixes immersion gap)

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Add a quiz or fill-in activity that tests він/вона/воно pronoun assignment for objects (matching the "It Trap" teaching in section "Самостійна робота (Independent Work/Production)")

**Expected score after fix:** 9/10

### Projected Overall After Fixes
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9 = 79.1 / 8.9 = **8.9/10**

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: N/A
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Grammar rules verified: Gender prediction rules match textbook references (Grade 3 p.110, Grade 4 p.35, Grade 6 p.129). Possessive pronoun diagnostic (мій/моя/моє) matches exactly.
- Cultural claims: "земля-мати" ✅ verified (genuine Ukrainian folk concept). "сонце-життя" ❌ not attested in textbooks or standard dictionaries. "95% predictability" — plausible but unsourced.
- D.0 Pre-Screen confirmation: STRESS_UNKNOWN for Зо́на and ста́рший — both confirmed valid in VESUM. INFO-level, no action needed.

## Verification Summary

- Content lines read: 94
- Activity items checked: 48 (8 match-up + 8 quiz + 8 fill-in + 8 match-up + 15 group-sort items + 8 true-false + 8 anagram + 6 unjumble = all)
- Ukrainian sentences verified: 25+
- Citations in bank: 20
- Issues found: 6

## Verdict

**FAIL**

Blocking issues: (1) Fabricated Ukrainian compound "сонце-життя" presented as cultural fact — must be removed or replaced with an attested expression; (2) Missing plan objective on 4 declension families needs at least a preview; (3) Immersion at 8.5% is below the 15% minimum for module 7 band; (4) Engagement boxes 1/2 — needs one more callout to pass richness gate. None of these are difficult fixes — one revision pass should bring this to PASS.