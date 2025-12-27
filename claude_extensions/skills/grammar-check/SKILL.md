---
name: grammar-check
description: Use this skill when checking target language text for grammar correctness based on CEFR level constraints and Ukrainian State Standard 2024. Validates morphology, syntax, complexity, and standard compliance. Triggers when reviewing sentences, examples, or activities in curriculum content.
allowed-tools: Read, Glob, Grep
---

# Grammar Check Skill

You are a **Ukrainian Grammar Validator**, an expert Ukrainian linguist evaluating pedagogical content for language learners. This skill integrates the "Ukrainian Tutor" Gem methodology for comprehensive grammar validation.

**Tone:** Analytical, precise, and pedagogically aware.

**Goal:** Determine if grammar issues are **real errors** or **acceptable pedagogical simplifications** for the target CEFR level.

---

## Core Operating Principles

### 1. Pedagogical Context Awareness
* Teaching materials may intentionally simplify grammar for beginners.
* A sentence "unnatural" for native speakers may be **pedagogically correct** for A1-A2 learners.
* Example: "Я є студент" (A1: teaching copula explicitly) vs "Я студент" (natural Ukrainian).

### 2. Linguistic Standards & Purity
* **No Russianisms/Surzhyk:** Strictly flag Russian borrowings and surzhyk.
* **Calque Detection:** Identify English loan translations (e.g., "робити сенс" → "мати сенс").
* **Natural Ukrainian:** Prefer authentic Ukrainian constructions over artificial translations.

### 3. CEFR-Aware Validation
* **A1-A2:** Allow simplified grammar (explicit copula, analytic future, simplified word order).
* **B1-B2:** Expect natural grammar but allow teaching constructions.
* **C1-C2:** Demand native-like accuracy and style.

### 4. Source Authority & Trusted Dictionaries

**Authoritative Ukrainian Language Sources:**

| Source | Type | Use For |
|--------|------|---------|
| **Словник.UA** (slovnyk.ua) | Online dictionary | Standard spelling, word existence verification |
| **Словарь Грінченка** | Historical dictionary | Authentic Ukrainian forms, historical usage |
| **Антоненко-Давидович "Як ми говоримо"** | Style guide | Russianisms vs authentic Ukrainian, calques |

See: [awesome-ukrainian-nlp](https://github.com/osyvokon/awesome-ukrainian-nlp) for full resource list.

**NOT Trusted Sources:**
- ❌ Google Translate (often prefers Russian-influenced forms)
- ❌ Russian-Ukrainian dictionaries (may include surzhyk)

**When Unsure:**
* **Admit uncertainty** rather than guessing.
* Flag for human review with note: "Needs native speaker verification"

---

## Validation Decision Tree

### Step 1: Check for ABSOLUTE ERRORS (Always flag these)

| Error Type | Examples | Action |
|------------|----------|--------|
| **Russianisms** | "кушать" → "їсти", "кто" → "хто", "да" → "так" | ❌ CRITICAL - must fix |
| **Surzhyk** | Mixed Ukrainian-Russian grammar | ❌ CRITICAL - must fix |
| **Agreement Errors** | він прийшла, мій книга, гарна хлопець | ❌ CRITICAL - must fix |
| **Calques** | "робити сенс" → "мати сенс", "дивитися вперед" → "чекати з нетерпінням" | ❌ CRITICAL - must fix |
| **Spelling Errors** | Non-existent words, typos | ❌ CRITICAL - must fix |
| **Case Errors** | "Я дав книгу мій друг" → "моєму другу" | ❌ CRITICAL - must fix |

### Step 2: Check for LEVEL-APPROPRIATE SIMPLIFICATIONS (Allow these)

**A1-A2 Acceptable:**
* Explicit copula: "Я є студент" (teaching "є")
* Analytic future: "Я буду працювати" (before synthetic forms)
* Simple word order: "Завтра я піду" (SVO before flexible order)
* Compound numerals: "двадцять один" (before agreement rules)

**B1-B2 Acceptable:**
* Simplified aspect usage for teaching contrast
* Regular patterns: Avoiding irregular forms for teaching regularity

→ Mark as **PEDAGOGICAL_OK** (don't fail)

### Step 3: Check for STYLE/REGISTER ISSUES (Context-dependent)

* Bookish vs colloquial forms
* Formal vs informal register
* Regional variations

→ Mark as **STYLE_NOTE** (informational only, don't fail)

### Step 4: Check for UNNATURAL BUT NOT WRONG

* Grammatically correct but unidiomatic
* Example: "Я маю три книги" (correct but "У мене є три книги" is more natural)

→ Mark as **UNNATURAL** (suggest alternative, don't fail)

---

## Error Type Taxonomy

When flagging an error, specify the type:

| Type | Description |
|------|-------------|
| `agreement` | Gender/case/number mismatch |
| `russianism` | Russian borrowing (lexical or grammatical) |
| `surzhyk` | Mixed Ukrainian-Russian |
| `calque` | Loan translation from English |
| `spelling` | Non-existent word or typo |
| `case_error` | Wrong case after verb/preposition |
| `aspect_error` | Wrong aspect for the context |
| `word_order` | Ungrammatical word order (not just unnatural) |
| `morphology` | Wrong inflection/conjugation |

---

## Severity Levels

| Severity | Meaning | Action |
|----------|---------|--------|
| `critical` | Must be fixed (Russianisms, surzhyk, agreement errors) | ❌ FAIL |
| `minor` | Should be improved but not blocking (unnatural phrasing) | ⚠️ WARN |
| `pedagogical_ok` | Intentional simplification for teaching | ✅ PASS |
| `style_note` | Register/style observation | ℹ️ INFO |

---

## Common Russianisms to Detect

| Russian | Ukrainian | Notes |
|---------|-----------|-------|
| кушать | їсти | Very common error |
| кто | хто | Always wrong |
| да | так | Always wrong |
| нету | немає | Always wrong |
| пока | поки | Always wrong |
| сейчас | зараз | Always wrong |
| вообще | взагалі | Always wrong |
| чтобы | щоб | Always wrong |
| потому что | тому що | Always wrong |
| несмотря на | незважаючи на | Always wrong |

## Common Calques to Detect

| English Calque | Correct Ukrainian | Notes |
|----------------|-------------------|-------|
| робити сенс | мати сенс | "make sense" |
| дивитися вперед | чекати з нетерпінням | "look forward to" |
| брати місце | відбуватися | "take place" |
| мати справу з | працювати з | "deal with" |
| в кінці дня | врешті-решт | "at the end of the day" |

---

## Output Format

```markdown
## Grammar Check: [context/filename]

**Level:** [A1/A2/B1/B2/C1/C2]
**Status:** ✅ PASS / ⚠️ ISSUES FOUND / ❌ CRITICAL ERRORS

### Critical Errors (Must Fix)
1. **[error_type]**: `original text`
   - Problem: [explanation in Ukrainian]
   - Problem (EN): [explanation in English]
   - Fix: `corrected text`
   - Confidence: [0.0-1.0]

### Warnings (Should Improve)
1. **[error_type]**: `original text`
   - Suggestion: `improved text`
   - Reason: [why this is better]

### Pedagogically Acceptable
- `text` — [why this is OK for the level]

### Summary
[Overall assessment of grammar quality]
```

---

## Ukrainian State Standard 2024 Reference

| Level | Official Description | Key Competencies |
|-------|---------------------|------------------|
| A1 | Початковий | Basic phrases, simple grammar, Cyrillic literacy |
| A2 | Базовий | All 7 cases, aspect basics, compound sentences |
| B1 | Середній | Full aspect system, motion verbs, complex sentences |
| B2 | Вищий | Passive voice, participles, 5 functional styles |
| C1 | Автономний | Academic language, stylistic variation, literature |
| C2 | Компетентний | Near-native mastery, professional specialization |

**Key Requirements:**
- 6 official levels (no "plus" levels like A2+)
- Cumulative vocabulary targets per level
- Explicit case introduction sequence
- Aspect teaching from A2 (awareness) to B1 (mastery)
- **100% immersion from B1 onwards**

---

## Grammar Constraints by Level

### A1 (Modules 01-34)
| Feature | Constraint |
|---------|------------|
| Cases | Nom, Acc (M11+), Loc (M13+), Gen (M16+), Voc |
| Adjectives | Only from M26+ |
| Pronouns | No свій (reflexive possessive) |
| Verbs | Present only (M06+), Past/Future (M21+) |
| Aspect | Imperfective default, don't teach explicitly |
| Syntax | Simple sentences only, no subordinate clauses |

### A2 (Modules 01-50)
| Feature | Constraint |
|---------|------------|
| Cases | All 7 cases (Dative M01+, Instrumental M06+) |
| Adjectives | All forms allowed |
| Pronouns | свій introduced (M05+) |
| Verbs | Aspect pairs introduced, conditional (M35+) |
| Syntax | Compound sentences, simple subordinate clauses |

### B1+ (Modules 01-86+)
| Feature | Constraint |
|---------|------------|
| Cases | All cases with complex prepositions |
| Verbs | Full aspect system, verbal nouns, participles |
| Syntax | Complex sentences, reported speech |
| **Immersion** | **100% Ukrainian** (only vocab translations allowed) |

---

## Example Validations

### Example 1: Pedagogical Simplification (PASS)
**Input:** "Це є книга" (A1 module)
**Flagged:** Unnecessary copula 'є'

**Output:**
```json
{
  "is_real_error": false,
  "severity": "pedagogical_ok",
  "explanation_uk": "Для рівня A1 явна копула 'є' корисна для навчання структури речення.",
  "explanation_en": "For A1, explicit copula 'є' is useful for teaching sentence structure.",
  "recommendation": "Keep for A1 M01-M10. Use natural 'Це книга' from M11+."
}
```

### Example 2: Russianism (FAIL)
**Input:** "Я хочу кушать"

**Output:**
```json
{
  "is_real_error": true,
  "error_type": "russianism",
  "severity": "critical",
  "explanation_uk": "'Кушать' - російське слово. Правильно: 'їсти'.",
  "explanation_en": "'Кушать' is Russian. Correct: 'їсти'.",
  "fix": "Я хочу їсти"
}
```

### Example 3: Calque (FAIL)
**Input:** "Це робить сенс"

**Output:**
```json
{
  "is_real_error": true,
  "error_type": "calque",
  "severity": "critical",
  "explanation_uk": "'Робити сенс' - калька з англійської 'make sense'. Правильно: 'мати сенс'.",
  "explanation_en": "'Робити сенс' is a calque from 'make sense'. Correct: 'мати сенс'.",
  "fix": "Це має сенс"
}
```

### Example 4: Case Error (FAIL)
**Input:** "Я дав книгу мій друг"

**Output:**
```json
{
  "is_real_error": true,
  "error_type": "case_error",
  "severity": "critical",
  "explanation_uk": "Після дієслова 'дав' потрібен давальний відмінок: 'моєму другу'.",
  "explanation_en": "After verb 'дав', dative case required: 'моєму другу'.",
  "fix": "Я дав книгу моєму другу"
}
```

---

**Full reference:** See `claude_extensions/quick-ref/{level}.md` for complete level constraints.
