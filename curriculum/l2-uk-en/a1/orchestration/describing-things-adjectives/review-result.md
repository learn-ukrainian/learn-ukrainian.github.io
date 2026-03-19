# Рецензія: Describing Things - Adjectives

**Level:** A1 | **Module:** 11
**Overall Score:** 7.6/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-opus-4-6

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 4/4 present (all H2 headers match plan sections)
- Vocabulary: 8/8 required present in prose, 7/7 recommended present
- Grammar scope: PASS (no scope creep beyond Nominative adjectives)
- Objectives: PASS (all 4 objectives addressed)
- Activity hints: PARTIAL (3/4 types present; "Describe pictures" reframed as "Describe What You See")
```

**Plan Point Checklist:**

Section "Вступ: Світ прикметників (Introduction: The World of Adjectives)":
- Warm-up with Який/Яка/Яке/Які: **COVERED** — Lines 9-13
- Cultural Hook (Софійський собор): **COVERED** — Line 15
- Bridge to Gender Code: **COVERED** — Lines 17-21

Section "Презентація: Тверда група (Presentation: Hard Stem Adjectives)":
- Hard Stem endings with color-coded markers: **COVERED** — Lines 29-32 (emoji color codes)
- Adjective Placement (attributive vs predicative): **COVERED** — Lines 41-43
- Gender Mismatch correction (*новий машина → нова машина): **COVERED** — Line 34
- High-frequency opposites: **COVERED** — Lines 46-60

Section "Презентація 2: М'яка група та Специфіка (Presentation 2: Soft Stem and Nuances)":
- Soft Stem endings with синій + Kyiv Metro mnemonic: **COVERED** — Lines 64-70
- Hard/Soft confusion (*синий vs синій): **COVERED** — Line 72
- Plural consistency: **COVERED** — Lines 79-84

Section "Практика та Культурний контекст (Practice and Cultural Context)":
- Mavka cultural portrait: **COVERED** — Lines 90-96
- Real Estate persona practice: **COVERED** — Lines 98-106
- Final Synthesis (Який? pattern): **COVERED** — Lines 108-113

**Missing from research notes:** The research recommends the рідний край/рідна мова/рідне слово/рідні люди discovery warm-up from Vashulenko Grade 3. This powerful textbook-grounded pedagogical technique is absent from the content, replaced by a less structured introduction.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good arc (welcome→present→practice→celebrate) but no callout boxes break the wall-of-text feel. No visual tables for grammar paradigms. |
| 2 | Language | 8/10 | <8 | English prose is clear and warm. Ukrainian examples are grammatically correct. 「синий」on line 72 is used as an error example (contextually valid). Line 94 「Вона **зелена** Мавка.」is slightly unnatural (see issues). |
| 3 | Pedagogy | 8/10 | <7 | Strong PPP arc. Mavka + real estate contexts are excellent. Missing the рідний discovery exercise from research. No tables for paradigm presentation — bullet lists with emojis are less scannable than a proper grid. |
| 4 | Activities | 8/10 | <7 | 8 activities, good variety (fill-in ×3, match-up, true-false, group-sort, quiz, unjumble). Item counts below plan hints (8/25, 8/20, 10/15) but hints are non-binding. All answers are linguistically correct. |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — pacing is good, instructions clear, quick wins present, Ukrainian not scary. Fails: "zero copula construction" (line 43) is intimidating terminology for A1; no encouragement callouts. |
| 6 | LLM Fingerprint | 7/10 | <7 | Section openings follow a pattern: line 26 「In Ukrainian, most adjectives belong to the "Hard Stem" group.」, line 62 「While most adjectives are hard, a special group of adjectives belongs to the "Soft Stem" group.」, line 88 「To really master these adjectives, let's step into two different worlds」. Line 118 「You have successfully unlocked the power of description in Ukrainian!」is generic AI closing. 「the colorful companions to nouns」is LLM rhetoric. |
| 7 | Linguistic Accuracy | 8/10 | <9 | Line 43: "[is]" brackets flagged as IPA — should use parentheses. Line 94: 「Вона **зелена** Мавка.」 is an awkward predicate+NP structure without dash or copula marker. Line 128: self-check asks about старий+місто without giving answer — pedagogically fine but scanner flags it. |

**Weighted Overall:** (8×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 7×1.0 + 8×1.5) / 8.9 = (12 + 8.8 + 9.6 + 10.4 + 10.4 + 7.0 + 12.0) / 8.9 = 70.2 / 8.9 = **7.9/10**

## Auto-Fail Checklist Results

- Russianisms: **CLEAN** — no давайте calques, no known A1 Russianisms found
- Calques: **CLEAN** — no English calques detected
- Colonial framing: **CLEAN** — no "unlike Russian" comparisons
- Grammar scope: **CLEAN** — stays within Nominative adjective agreement
- Activity errors: **MINOR** — VESUM flags "ий" as standalone word in scan (false positive — it's an ending suffix in options like "-ий")
- Beginner safety: 4/5
- Factual accuracy: **CLEAN** — Софійський собор, Mavka/Лісова пісня, Kyiv Metro синя лінія all verified

## Critical Issues Found

### Issue 1: ZERO Engagement Boxes (AUDIT GATE FAILURE)
- **Location**: Whole module
- **Problem**: The module contains 0 callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]`, etc.). The audit requires minimum 1 for A1, and the richness gate shows `engagement: 0/2`. This is the primary reason for AUDIT FAIL status.
- **Fix**: Add at minimum 2 engagement callout boxes:
  1. A `> [!tip]` after line 34 about the gender mismatch rule (mnemonic aid)
  2. A `> [!cultural-note]` after line 15 about Софійський собор
  3. A `> [!did-you-know]` in section "Презентація 2: М'яка група та Специфіка" about the Kyiv Metro

### Issue 2: IPA-Banned Brackets on Line 43
- **Location**: Line 43, section "Презентація: Тверда група (Presentation: Hard Stem Adjectives)"
- **Original**: 「«Книга **гарна**» (The book [is] beautiful). «Дім **новий**» (The house [is] new).」
- **Problem**: The `[is]` notation triggers the IPA scanner (D.0 items #1-2). While contextually it means "omitted verb," square brackets are banned project-wide for IPA reasons.
- **Fix**: Replace `[is]` with `(is)` or rephrase as "(The book — beautiful)" or use em-dash: "The book — beautiful"

### Issue 3: Awkward Ukrainian on Line 94
- **Location**: Line 94, section "Практика та Культурний контекст (Practice and Cultural Context)"
- **Original**: 「Вона **зелена** Мавка. (She is a green Mavka, tied to nature.)」
- **Problem**: "Вона зелена Мавка" is grammatically strange — it reads as "She [is] green Mavka" which is an unnatural predicate + bare proper noun construction. In natural Ukrainian, this would be "Вона — зелена Мавка" (with a dash acting as copula) or simply "Зелена Мавка" as a noun phrase.
- **Fix**: Change to `Вона — зелена Мавка.` or restructure as `Це зелена Мавка.`

### Issue 4: No Grammar Paradigm Tables
- **Location**: Lines 29-32 and 67-70 (both presentation sections)
- **Problem**: The plan specifies "visual scaffolding with color-coded gender markers." The content uses emoji bullet lists, which are less scannable than actual markdown tables. For A1 beginners, clean paradigm tables are the standard presentation in Ukrainian textbooks (Grades 3-4).
- **Fix**: Convert the bullet-list paradigms into proper markdown tables with gender headers.

### Issue 5: Missing рідний Discovery Hook
- **Location**: Section "Вступ: Світ прикметників (Introduction: The World of Adjectives)"
- **Problem**: The research notes specifically recommend the Vashulenko Grade 3 рідний paradigm (рідний край / рідна мова / рідне слово / рідні люди) as a discovery warm-up — "Students see the pattern before the rule is stated." This textbook-grounded technique is absent. The content jumps from question words directly to Софійський собор without a pattern-discovery moment.
- **Fix**: Add a short discovery exercise between the Який/Яка/Яке/Які introduction and the Софійський собор hook, presenting the рідний paradigm and asking learners to spot the pattern.

### Issue 6: Linguistic Accuracy — AUTO-FAIL (score 8 < threshold 9)
- **Location**: Multiple
- **Problem**: The Linguistic Accuracy dimension scores 8/10 which is below the auto-fail threshold of 9. The issues are: (a) "[is]" bracket notation, (b) "Вона зелена Мавка" unnaturalness, (c) the word "синий" appearing in prose without clear error marking (asterisk prefix like *синий would be conventional). While "синий" is used pedagogically to show a common error, it should be typographically distinguished more clearly.
- **Fix**: Fix items (a), (b), and mark "синий" with an asterisk prefix (*синий) to follow linguistic convention for erroneous forms.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 43 | 「(The book [is] beautiful)」 | (The book _(is)_ beautiful) | IPA-banned notation |
| 72 | 「«**синий**»」 | «***синий**» or prefix with asterisk | Error form not marked conventionally |
| 94 | 「Вона **зелена** Мавка.」 | Вона — зелена Мавка. | Missing dash copula |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is comfortable, new words introduced 3-5 at a time
- Instructions clear? **Pass** — always know what to learn next
- Quick wins? **Pass** — early examples with familiar nouns (місто, дім, кава)
- Ukrainian scary? **Pass** — Ukrainian introduced gently with translations
- Come back tomorrow? **Soft Fail** — no encouragement callouts, no "don't worry" moments, the closing at line 118 is generic. A nervous beginner gets no emotional support between sections.

## Strengths

- **Excellent cultural hooks**: Софійський собор and Mavka from Лісова пісня provide memorable, authentic Ukrainian context. The Kyiv Metro 「синя лінія」mnemonic (line 66) is practical and verifiable.
- **Smart error prevention**: Explicitly addressing the *новий машина error (line 34) and *синий spelling error (line 72) targets the two most common A1 adjective mistakes. This is evidence-based pedagogy from the research notes.
- **Real estate roleplay** (lines 98-106): Functional context that naturally cycles through all three genders + plural. This is the plan's persona executed well.
- **Activities are solid**: 8 activities with good variety. The unjumble and group-sort types add kinesthetic variety beyond fill-in drills.
- **Word count healthy**: 1670/1200 (139%) — well above target with no padding.

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Engagement Boxes: Add 2-3 callout boxes

**What to fix:**
1. After line 15 (Софійський собор): Add `> [!cultural-note]` about the cathedral's UNESCO status and significance
2. After line 34 (gender mismatch): Add `> [!tip]` with a mnemonic for remembering gender agreement
3. After line 66 (Kyiv Metro): Add `> [!did-you-know]` about the Metro line colors

**Expected impact:** Engagement 0→2+, richness gap closed, Experience Quality 8→9

### Linguistic Accuracy: Fix bracket notation + naturalness

**What to fix:**
1. Line 43: Change `[is]` to `_(is)_` or parenthetical
2. Line 94: Add dash — `Вона — зелена Мавка.`
3. Line 72: Mark error form with asterisk prefix

**Expected impact:** Linguistic Accuracy 8→9

### LLM Fingerprint: Vary section openings

**What to fix:**
1. Line 118: Replace 「You have successfully unlocked the power of description in Ukrainian!」with something specific: "You can now describe a нова квартира, an old Софійський собор, and a синє море — all with the right endings."
2. Vary at least one section opening — e.g., section "Презентація 2: М'яка група та Специфіка" could open with the Kyiv Metro hook instead of the generic "While most adjectives are hard..."

**Expected impact:** LLM Fingerprint 7→8

### Pedagogy: Add рідний discovery exercise

**What to fix:**
1. In section "Вступ: Світ прикметників", after line 13 (Які?), add the рідний paradigm discovery exercise from research notes.

**Expected impact:** Pedagogy 8→9

### Projected Overall After Fixes
```
Experience: 9×1.5 = 13.5
Language: 8×1.1 = 8.8
Pedagogy: 9×1.2 = 10.8
Activities: 8×1.3 = 10.4
Beginner Safety: 9×1.3 = 11.7
LLM Fingerprint: 8×1.0 = 8.0
Linguistic Accuracy: 9×1.5 = 13.5
Total: 76.7 / 8.9 = 8.6/10
```

## D.0 Pre-Screen Triage

| # | D.0 Finding | Verdict |
|---|-------------|---------|
| 1-2 | IPA_BANNED `[is]` | **CONFIRMED** — brackets must be changed, though not actual IPA |
| 3-6 | AGREEMENT_ERROR lines 80-84 | **DISMISSED** — These are singular→plural transformation examples. Scanner confused by multiple forms on one line. Pedagogically correct. |
| 7-12 | AGREEMENT_ERROR lines 121-122 | **DISMISSED** — Summary paradigm listings showing all four forms. Not agreement errors. |
| 13 | AGREEMENT_ERROR line 128 | **DISMISSED** — Self-check question asking learner to determine correct form. Intentionally mismatched. |
| 14 | LOW_ENGAGEMENT | **CONFIRMED** — 0 engagement boxes. Critical fix. |
| 15 | ACTIVITY_VESUM_FAIL "ий" | **DISMISSED** — "ий" appears as a suffix in options ("-ий"), not a standalone word. False positive. |

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: N/A
- Named figures verified: Lesya Ukrainka + Лісова пісня + Мавка — CORRECT
- Cultural claims: Софійський собор in Kyiv — CORRECT; Kyiv Metro синя лінія — CORRECT
- Claims without research grounding: 0

## Verification Summary

- Content lines read: 132
- Activity items checked: 63 (across 8 activities)
- Ukrainian sentences verified: 22
- Citations in bank: 17
- Issues found: 6

## Verdict

**FAIL**

The module is well-structured with strong cultural hooks and correct Ukrainian grammar throughout. However, it fails the audit engagement gate (0 callout boxes vs minimum 2) and the Linguistic Accuracy auto-fail threshold (8/10 < 9 required) due to banned `[is]` bracket notation and the unnatural "Вона зелена Мавка" construction. Fixing the engagement boxes, bracket notation, and adding the рідний discovery exercise would bring this to passing quality.