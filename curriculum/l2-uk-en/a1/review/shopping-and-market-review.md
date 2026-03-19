<!-- content-hash: 2b402b64a186 -->
# Рецензія: Shopping and Market

**Level:** A1 | **Module:** 40
**Overall Score:** 7.8/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-20250514

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: All 5 H2 sections present (PASS)
- Vocabulary: 10/10 required present in prose, 4/4 recommended present
- Grammar scope: MINOR issue (case terminology inconsistency)
- Objectives: 3/4 fully met (hygiene products partially met)
```

### Plan Adherence Checklist (content_outline.points)

**Section "Скільки коштує? (How much?)"**
- "Key question pattern: Скільки коштує...?" — COVERED (line 5-9)
- "Price expressions with гривня" — COVERED (lines 17-19)
- "Answering price questions" — COVERED (lines 21-24)

**Section "У магазині (In the Store)"**
- "Polite request patterns: Дайте, будь ласка..." — **MISSING** ❌ (Plan requires three patterns: Дайте будь ласка, Я хочу купити, Можна. Content only has Хліб будь ласка and Я хочу купити. The imperative formula "Дайте, будь ласка..." is completely absent.)
- "Polite request patterns: Можна...?" — **PARTIAL** ⚠️ (Можна appears only in section "Практика" line 142 as 「Можна платити карткою?」, not in section "У магазині" where the plan places it.)
- "Checking availability: Є...? У вас є...?" — COVERED (lines 45-48)
- "Learner error: using мати instead of є" — COVERED (lines 43-44)
- "Basic shopping dialogue structure" — COVERED (lines 50-59)

**Section "Кількість та одиниці (Quantities and Units)"**
- "Units of measurement" — COVERED (lines 68-72)
- "Genitive with quantities" — COVERED (lines 76-80)
- "Numbers with units: 2-4 + Gen. sg., 5+ + Gen. pl." — COVERED (lines 84-92)

**Section "Засоби гігієни (Hygiene Products)"**
- "Essential hygiene vocabulary" — COVERED (lines 106-110)
- "Asking where to buy items: Де можна купити...?" — COVERED (lines 112-120)

**Section "Практика (Practice)"**
- "Shopping role-play dialogues" — COVERED (lines 126-143)
- "Price asking and answering drills" — COVERED (lines 145-148)
- "Quantity expression practice" — COVERED (lines 150-153)

**Vocabulary Hints (required — all 10 verified in prose):**
коштувати ✅, купити ✅, гривня ✅, кілограм ✅, літр ✅, пачка ✅, пляшка ✅, магазин ✅, ринок ✅, мило ✅

**Activity Hints:**
- fill-in (10 items) ✅
- quiz (10 items) ✅
- match-up (10 items) ✅ (but see quality issues)
- unjumble (6 items) ✅ (but see punctuation issue)

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good lesson arc with warm closing, but no Ukrainian greeting (no "Привіт!") and opening is generic English |
| 2 | Language | 8/10 | <8 | Grammar terminology inconsistency on line 84; "ень" is a false positive (suffix notation). Clean Ukrainian otherwise |
| 3 | Pedagogy | 7/10 | <7 | Missing "Дайте, будь ласка" plan point; "Можна...?" misplaced from section "У магазині" to section "Практика" |
| 4 | Activities | 7/10 | <7 | Unjumble missing comma in 「Хліб будь ласка」; match-up has nonsense unit "будь ласка (by item)" for хліб |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — good pacing, clear instructions, but no warm Ukrainian welcome |
| 6 | LLM Fingerprint | 8/10 | <7 | Opening line is generic; example formatting is varied (dialogues, bullet lists, drills) |
| 7 | Linguistic Accuracy | 8/10 | <9 | Line 84 labels feminine 2-4 forms as "Genitive singular" — inconsistent with line 18's "Nominative plural" for the same rule with гривні |

**Weighted Overall:** (8×1.5 + 8×1.1 + 7×1.2 + 7×1.3 + 8×1.3 + 8×1.0 + 8×1.5) / 8.9 = (12 + 8.8 + 8.4 + 9.1 + 10.4 + 8.0 + 12.0) / 8.9 = 68.7 / 8.9 = **7.7/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no здача, кушати, давайте + perfective calques, etc. found. Uses correct решта.
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no "unlike Russian" comparisons
- Grammar scope: [CLEAN] — no grammar from later modules; Instrumental for карткою correctly presented as frozen phrase
- Activity errors: [2 FOUND] — unjumble punctuation, match-up bad pairing
- Beginner safety: 4/5
- Factual accuracy: [CLEAN] — callout on line 99 about пакет is culturally accurate

## Critical Issues Found

### Issue 1: Missing Plan Point — "Дайте, будь ласка..." (MEDIUM-HIGH)
- **Location**: Section "У магазині (In the Store)"
- **Problem**: The plan explicitly requires three polite request patterns: "Дайте, будь ласка... (Give me, please...). Я хочу купити... (I want to buy...). Можна...? (May I...?)." The content only covers "Я хочу купити..." and "Item + будь ласка." The imperative formula "Дайте, будь ласка" is entirely absent. The plan's `grammar` field also lists "Shopping imperative phrases (Дайте, будь ласка)" as a grammar point. The summary on line 158 even claims 「You explored polite request patterns like **Хліб, будь ласка** and **Я хочу купити**」 — inadvertently confirming the gap.
- **Fix**: Add "Дайте, будь ласка..." as a third polite request formula in section "У магазині", with 2-3 examples (Дайте хліб, будь ласка. Дайте воду, будь ласка.). Also add "Можна мило, будь ласка?" to the same section. Research notes say to treat "Дайте, будь ласка" as a frozen chunk, not a productive imperative.

### Issue 2: Grammatical Terminology Inconsistency (MEDIUM)
- **Location**: Line 84, Section "Кількість та одиниці (Quantities and Units)"
- **Original**: 「The feminine words **пачка** and **пляшка** change their ending to **-и** (Genitive singular form).」
- **Problem**: Line 18 correctly describes the 2-4 pattern for гривні as "Nominative plural" but line 84 calls the identical pattern for пачки/пляшки "Genitive singular form." While the forms are homonymous for -а/-я feminines, using two different case labels for the same numerical agreement rule within one module is confusing for A1 learners. Modern Ukrainian grammar describes 2-4 agreement as Nominative plural. Calling it "Genitive singular" follows the Russian grammatical tradition.
- **Fix**: Change to "Nominative plural ending **-и**" for consistency with line 18 and Ukrainian grammatical tradition.

### Issue 3: Activity Error — Unjumble Missing Comma (MEDIUM)
- **Location**: Activities file, line 195
- **Original**: 「answer: "Хліб будь ласка"」
- **Problem**: The content teaches 「Хліб, будь ласка.」 (line 33) with a comma. The unjumble answer omits the comma, teaching incorrect punctuation. In Ukrainian, "будь ласка" is separated by a comma when it follows the item.
- **Fix**: Change answer to "Хліб, будь ласка"

### Issue 4: Activity Error — Match-up Nonsense Pairing (MEDIUM)
- **Location**: Activities file, line 175-176
- **Original**: 「right: "будь ласка (by item)"」 for хліб
- **Problem**: The activity instruction says "Match each product with the unit of measurement typically used when buying it." "будь ласка (by item)" is not a unit of measurement. This is confusing and breaks the activity's internal logic. Хліб is typically sold by штука or as a whole item.
- **Fix**: Change to `right: "штука"` — штука is already taught in the module as a unit (line 72).

### Issue 5: Low Immersion (17.7% vs 20% minimum) (LOW-MEDIUM)
- **Location**: Entire module
- **Problem**: Pre-computed immersion is 17.7%, below the 20% floor. Module 40 is in the 21+ band. The English prose dominates even in sections where more Ukrainian examples could be woven in.
- **Fix**: Add 2-3 more Ukrainian example sentences in sections "Засоби гігієни" and "У магазині" to nudge immersion above 20%. For example, add a short dialogue asking for зубна паста at an аптека.

### Issue 6: Missing Vocabulary Items in YAML (LOW)
- **Location**: Vocabulary file
- **Problem**: зубна паста (toothpaste) and туалетний папір (toilet paper) are taught in section "Засоби гігієни" (lines 107, 110) but absent from the vocabulary YAML. These are useful survival vocabulary words.
- **Fix**: Add both to the vocabulary YAML.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 84 | 「The feminine words **пачка** and **пляшка** change their ending to **-и** (Genitive singular form).」 | "The feminine words **пачка** and **пляшка** change their ending to **-и** (Nominative plural)." | Grammar terminology |
| Act. 195 | 「answer: "Хліб будь ласка"」 | answer: "Хліб, будь ласка" | Punctuation |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is comfortable, new words introduced in small groups
- Instructions clear? **Pass** — always knew what to do, English scaffolding present
- Quick wins? **Pass** — early simple phrases (Скільки коштує?), dialogues to read aloud
- Ukrainian scary? **Pass** — introduced gently with translations
- Come back tomorrow? **Borderline Pass** — the opening lacks warmth (no "Привіт!", no persona voice). The closing is warm (「You have done an amazing job today!」) but the opening reads like a textbook paragraph, not a tutor greeting.

## Strengths

- **Excellent dialogues**: Both the market dialogue (lines 128-133) and store dialogue (lines 137-143) are natural, realistic, and perfectly scaffolded for A1. They model complete transactions.
- **Strong number-noun agreement teaching**: The гривня paradigm (lines 17-19) is clear and well-structured, with immediate practice sentences (lines 22-24).
- **Good cultural note**: The пакет note (line 99) is accurate, practical, and not filler — 「In Ukraine, you will often be asked if you need a bag (**пакет**).」
- **Correct use of решта** (not здача) — proper Ukrainian, avoiding the Russicism.
- **Preposition contrast** (у магазині vs на ринку) is explicitly called out on line 126 — 「while we say **у магазині** (in the store), we say **на ринку** (at the market).」 This is a known learner error and the module handles it well.
- **Activities are well-designed overall**: The fill-in dialogue (10 items) tests real shopping patterns, the quiz covers quantities correctly, and the unjumble forces word-order practice.

## Fix Plan to Reach 9/10 (REQUIRED — current 7.7/10)

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Section "У магазині": Add "Дайте, будь ласка..." as a polite request pattern with 2-3 examples, and add "Можна...?" with 1-2 examples. This closes the biggest plan gap. (~60 words)
2. Move or duplicate "Можна платити карткою?" context into section "У магазині" so all three request patterns are taught together before practice.

### Activities: 7/10 → 9/10
**What to fix:**
1. Activity line 195: Fix unjumble answer from "Хліб будь ласка" to "Хліб, будь ласка"
2. Activity line 175-176: Change match-up pair for хліб from "будь ласка (by item)" to "штука"

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 84: Change "(Genitive singular form)" to "(Nominative plural)" for consistency with line 18 and Ukrainian grammatical tradition.

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Line 1: Add a warm opening with "Привіт!" and a brief learning preview before diving into content.
2. Add one more engagement box (e.g., a [!tip] or [!did-you-know] about market culture in section "Практика").

### Projected Overall After Fixes
```
Experience 9×1.5 + Language 8×1.1 + Pedagogy 9×1.2 + Activities 9×1.3 +
Beginner Safety 9×1.3 + LLM 8×1.0 + Linguistic Accuracy 9×1.5
= 13.5 + 8.8 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5 = 78.0 / 8.9 = 8.8/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: N/A
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0
- Callout boxes checked: 1 (line 99 — пакет note is accurate)
- Grammar rules verified: гривня paradigm correct, quantity Genitive correct, шампунь gender correct

## Verification Summary

- Content lines read: 168
- Activity items checked: 36 (10 fill-in + 10 quiz + 10 match-up + 6 unjumble)
- Ukrainian sentences verified: 28
- Citations in bank: 16
- Issues found: 6

## Verdict

**FAIL**

Blocking issues: (1) Missing plan-required "Дайте, будь ласка..." polite request pattern — this is a plan adherence failure. (2) Two activity errors (unjumble missing comma, match-up nonsense unit). (3) Linguistic accuracy below 9 due to inconsistent grammar terminology (Genitive singular vs Nominative plural for the same 2-4 agreement rule). All are fixable in one pass.

---

## Post-Fix Re-Score (automated)

**Scored by:** claude-opus-4-6 (on fixed content)
**Overall Score:** 6.3/10
**Verdict:** FAIL

| Dimension | Score |
|-----------|-------|
| experience | 7/10 |
| language | 8/10 |
| pedagogy | 6/10 |
| activities | 5/10 |
| beginner_safety | 6/10 |
| llm_fingerprint | 6/10 |
| linguistic_accuracy | 8/10 |
