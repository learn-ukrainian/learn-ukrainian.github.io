# A1 Naturalness Scan Protocol

## Purpose
Scan A1 activities for naturalness while strictly maintaining vocabulary and grammar constraints per Ukrainian State Standard 2024.

## Critical Constraints

<critical>

**NEVER violate these rules when fixing activities:**

1. **Vocabulary Scope**: Only use words from `curriculum/l2-uk-en/plans/a1/` (module plans) up to current module
2. **Grammar Scope**: Only use grammar constructs introduced by Ukrainian State Standard 2024 up to current module
3. **Pedagogical Focus**: Preserve the grammar point being drilled (e.g., M21 = past tense)
4. **CEFR Level**: Maintain A1 complexity (simple sentences, present tense, basic cases)

</critical>

---

## Pre-Scan Preparation

**Before scanning ANY files:**

1. **Read A1 module plans** from `curriculum/l2-uk-en/plans/a1/`
   - Extract vocabulary hints from each module plan
   - Build cumulative vocabulary map: M01→M{current}
   - Note which grammar points each module introduces

2. **Read Ukrainian State Standard 2024 A1 section**
   - Map grammar progression order
   - Note which cases/tenses/constructs are allowed at each module

3. **Create vocabulary index**
   - Structure: `{module_num: [word1, word2, ...]}`
   - Allows fast lookup: "Is 'обіцяти' allowed in M22?" → NO (introduced M30+)

---

## For Each Activity File (M01→M34 in order)

### Step 1: Load Module Context

```
File: {num}-{slug}.yaml
Module: M{num}
Topic: {extract from curriculum plan}

Allowed vocabulary: M01→M{num} cumulative words
Allowed grammar: {list constructs from State Standard 2024}
```

### Step 2: Extract Prose Activities

**Target activity types:**
- `type: fill-in`
- `type: cloze`
- `type: unjumble`

**Skip:**
- `type: quiz` (comprehension, no prose)
- `type: match-up` (vocabulary pairs)
- `type: group-sort` (categorization)
- `type: true-false` (comprehension)

**Extraction method:**
For each prose activity, reconstruct complete sentences:
- **fill-in**: Substitute `___` with `answer` field value
- **cloze**: Extract first option from `{option1|option2|option3}`
- **unjumble**: Use `answer` field (already ordered)

### Step 3: Naturalness Analysis

**Switch to Ukrainian language mode for this step.**

**Analyze each prose activity for:**

1. **Subject Consistency**
   - ❌ Random shifts: Я читаю. Він говорить. Вона спить. (no context)
   - ✅ Unified context: Я читаю. Мій брат говорить. Моя сестра спить. (family)

2. **Discourse Markers**
   - ❌ Missing: Я прокинувся. Я поснідав. Я пішов.
   - ✅ Present: Спочатку я прокинувся. Потім я поснідав. Нарешті я пішов.

3. **Topic Coherence**
   - ❌ Jumps: Я йду до школи. Кава без цукру будь ласка. (what?)
   - ✅ Logical: Я йду до школи. Школа знаходиться біля парку.

4. **Redundancy**
   - ❌ Pointless repetition: Я завжди снідаю. Я зазвичай снідаю. Я щодня снідаю.
   - ✅ Purposeful variation: Я завжди снідаю вранці. А брат часто пропускає сніданок.

**Score (1-10):**
- **9-10**: Perfect natural discourse, native-like flow
- **8**: Good, coherent, minor roughness acceptable
- **5-7**: Mechanical/drill-like but grammatical, needs connectors
- **1-4**: Random/incoherent, complete rewrite needed

### Step 4: Constraint Validation (for flagged activities)

**Before proposing any fix, validate EVERY word and construct:**

```python
# Pseudo-validation logic
for word in proposed_fix:
    if word not in vocabulary_M01_to_Mcurrent:
        FLAG: "Vocabulary violation: '{word}' not in M01-M{current}"
        CHECK: Which module introduces this word?
        REJECT FIX

for grammar_construct in proposed_fix:
    if grammar_construct not in allowed_grammar_M01_to_Mcurrent:
        FLAG: "Grammar violation: '{construct}' not allowed until M{later}"
        CHECK: State Standard 2024 progression
        REJECT FIX
```

**Common A1 constraints to watch:**

| Module Range | Allowed | NOT Allowed |
|--------------|---------|-------------|
| M01-M10 | Present tense, Nominative, Accusative (basic) | Past/Future tense, all cases |
| M11-M15 | + Accusative (full), Locative | Genitive, Dative, Instrumental |
| M16-M20 | + Genitive (basic) | Dative, Instrumental |
| M21-M25 | + Past tense, Future tense | Aspect distinction |
| M26-M34 | + All basic constructs | Complex subordination, participles |

### Step 5: Fix Proposal (if score < 8)

**Fix template:**

```markdown
## Issue
- Lines: {line_numbers}
- Score: {current_score}/10
- Problem: {specific naturalness issue}

## Current Text
{extract problematic sentences}

## Proposed Fix
{rewritten sentences}

## Validation
✅ Vocabulary: All words from M01-M{current}
✅ Grammar: Only {allowed constructs}
✅ Pedagogy: Preserves {drill focus}
✅ Naturalness: {new_score}/10

## Words Used (verification)
{list all Ukrainian words in fix} → all found in M01-M{current} vocabulary list
```

---

## Output Format

Generate single comprehensive report:

```markdown
# A1 Naturalness Scan Report
Date: {date}
Files scanned: 34
Flagged: {count}

---

## Summary by Status

### ✅ OK (Score >= 8)
- M01-the-cyrillic-code-i.yaml (9/10) - no prose activities
- M02-the-cyrillic-code-ii.yaml (9/10) - simple drills, coherent
- ...

### ⚠️ FLAGGED (Score < 8)
- M08-the-living-verb-ii.yaml (5/10) - random subject shifts
- M21-yesterday-past-tense.yaml (4/10) - disconnected past tense drills
- M22-tomorrow-future-tense.yaml (6/10) - missing connectors
- ...

---

## Detailed Findings

{for each flagged file, use Fix Proposal template}

---

## Previously Fixed Files (Validation)

### M25-my-daily-routine.yaml (FIXED 2026-01-12)
Status: ✅ RE-VALIDATED
- All vocabulary from M01-M25 ✓
- Grammar scope: reflexive verbs (M09) + daily routine vocab (M25) ✓
- Naturalness: 8/10 ✓

{validate all previously committed fixes}

---

## Constraint Violations Found

{if any fixes violated vocabulary/grammar scope, list here}
```

---

## Execution Strategy

1. **Sequential processing**: M01 → M34 (build cumulative knowledge)
2. **Batch validation**: Verify all previously committed fixes first
3. **Single output**: One comprehensive report, not 34 separate messages
4. **Economical**: Group related issues, avoid repetition

---

## Success Criteria

- [ ] All activities score >= 8/10 for naturalness
- [ ] Zero vocabulary violations (100% compliance with curriculum plan)
- [ ] Zero grammar violations (100% compliance with State Standard 2024)
- [ ] Pedagogical focus preserved in all fixes
- [ ] Previously committed fixes validated and re-scored
