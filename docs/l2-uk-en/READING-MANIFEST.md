# Module Architect: Required Reading Manifest

> **Purpose:** This file ensures AI agents read and understand all required documentation before creating or reviewing modules. It extracts the **MOST VIOLATED RULES** from each document.

---

## ⛔ ABSOLUTE RULES (Zero Tolerance)

Before reading ANY other document, internalize these:

| Rule | Violation Example | Correct |
|------|-------------------|---------|
| **No Latin transliteration at A2+** | `привіт (pryvit)` | `привіт` only |
| **Vocabulary = Markdown table at END** | Vocab in YAML frontmatter | `## Vocabulary` section with `\| Ukrainian \| IPA \| ...` |
| **Section headers lowercase** | `## Warm-Up:` | `## warm-up` |
| **"Kyiv" never "Kiev"** | Kiev | Kyiv |
| **"Ukraine" never "The Ukraine"** | The Ukraine | Ukraine |
| **Placeholders = `___`** | `_____` or `(blank)` | `___` (3 underscores) |

---

## 📚 Document Reading Order

### Document 1: Level Curriculum Plan (REQUIRED FIRST)
**Path:** `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`

**What it contains:**
- Module list with titles, vocabulary, grammar per module
- **Каталог В** - The grammar allowed at each module
- Cross-module dependencies

**KEY RULE:**
> ⚠️ Grammar is strictly scoped by module number. 
> Example: Dative case is NOT allowed until M31 (A2).
> Do NOT use grammar from modules the learner hasn't completed.

**VERIFICATION:** Before using any grammar, check Каталог В in the Curriculum Plan.

---

### Document 2: Module Richness Guidelines (REQUIRED)
**Path:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

**What it contains:**
- Word count targets by level
- Activity count requirements
- Sentence complexity by level
- IPA/Audio requirements

**KEY RULES:**

| Level | Core Words | Activities | Items/Activity | Transliteration |
|-------|------------|------------|----------------|-----------------|
| A1 | 300/500/750* | 8+ | 12+ | ALLOWED (first-occurrence) |
| A2 | 1000+ | 10+ | 12+ | ⛔ FORBIDDEN |
| B1 | 1250+ | 12+ | 14+ | ⛔ FORBIDDEN |
| B2 | 1500+ | 14+ | 16+ | ⛔ FORBIDDEN |
| C1 | 1750+ | 16+ | 18+ | ⛔ FORBIDDEN |
| C2 | 2000+ | 16+ | 18+ | ⛔ FORBIDDEN |

*A1 Core Word Count Graduated: M01-05 (300+), M06-10 (500+), M11-34 (750+)

**VERIFICATION:** Run `python3 scripts/audit_module.py {file}` to verify word count.

---

### Document 3: Linguistic Purity Guide (REQUIRED)
**Path:** `docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md`

**What it contains:**
- Anti-Surzhyk (Russification) corrections
- Grammar fidelity rules (Vocative, Aspect, etc.)

**KEY RULES (Surzhyk = INSTANT FAIL):**

| ❌ FORBIDDEN | ✅ USE THIS |
|--------------|-------------|
| Приймати участь | Брати участь |
| Самий кращий | Найкращий |
| Давай підемо | Ходімо |
| Вірний (correct) | Правильний |
| Відкривати (door) | Відчиняти |
| Білет (transport) | Квиток |

**VERIFICATION:** Search module for "самий", "давай", "відкривати".

---

### Document 4: Markdown Format Specification (REQUIRED)
**Path:** `docs/MARKDOWN-FORMAT.md`

**What it contains:**
- Activity syntax (fill-in, match-up, quiz, etc.)
- Callout types (`> [!answer]`, `> [!options]`)
- Vocabulary table format

**KEY RULES:**

1. **Answers:** Use `> [!answer]` callout, NEVER `**Answer:**`
2. **Options:** Use `> [!options]` callout for fill-in
3. **Vocabulary table:** MUST be at END of file, NEVER in YAML
4. **Activity headers:** `## type: Title` (e.g., `## fill-in: Case Practice`)

**VERIFICATION:** Check that no activities use YAML blocks or bold answers.

---

### Document 5: Module Skeleton (FOR CREATION)
**Path:** `docs/l2-uk-en/MODULE-SKELETON.md`

**What it contains:**
- Template structure for PPP, TTT, and Narrative modules
- Section requirements with word counts

**KEY RULE:**
> Copy the skeleton and FILL EVERY SECTION.
> Never delete sections. Expand them until word count is met.

---

### Document 6: Ukrainian State Standard (REFERENCE)
**Path:** `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`
**Index:** `docs/l2-uk-en/UKRAINIAN-STANDARD-INDEX.md`

**What it contains:**
- Official Ukrainian competency requirements by level
- Grammar/vocabulary aligned to CEFR

**KEY RULE:**
> Modules must cover AT LEAST the Standard's competencies.
> Check the Index for which Standard sections apply to your module.

---

## ✅ Pre-Work Verification Checkpoint

Before starting ANY module work, you MUST be able to answer:

### For ALL Levels:
1. What is the Core Word Count target for this level? ____
2. How many activities are required? ____
3. Is Latin transliteration allowed at this level? ____

### For This Specific Module:
4. What grammar is allowed at this module number? (Check Каталог В)
5. What vocabulary should this module teach? (Check Curriculum Plan)

### Format Check:
6. Where does the vocabulary table go? → **END of file, as Markdown table**
7. How do I format answers? → **`> [!answer]` callout**

---

## 🔄 Post-Work Verification

After completing module work, run these checks:

```bash
# 1. Audit the module
python3 scripts/audit_module.py {file_path}

# 2. Generate HTML/JSON
npm run generate l2-uk-en {level} {module_num}

# 3. Verify output
# Check output/html/l2-uk-en/{level}/module-XX.html
```

### Manual Checks:
- [ ] No Latin transliteration (A2+)
- [ ] Vocabulary table at END of file
- [ ] All section headers lowercase
- [ ] No Surzhyk terms (самий, давай, відкривати)
- [ ] Activity items count ≥ 12

---

## Level Quick Reference

### A1 (Modules 01-34)
- **Word Count:** Graduated (M01-05: 300+, M06-10: 500+, M11-34: 750+)
- **Transliteration:** ALLOWED (first-occurrence only, phases out by M20)
- **Immersion:** 10-40% Ukrainian (graduated by module)
- **Pedagogy:** PPP (Present-Practice-Produce)
- **Cases:** Nom, Acc (M11+), Loc (M13+), Gen (M16+)
- **Verbs:** Present (M06+), Past/Future (M21+)

### A2 (Modules 01-50)
- **Transliteration:** ⛔ FORBIDDEN
- **Immersion:** 40% Ukrainian
- **Pedagogy:** PPP transitioning to TTT
- **Cases:** All 7 (Dat M31+, Instr M36+)
- **Aspect:** Pairs introduced

### B1 (Modules 01-80)
- **Transliteration:** ⛔ FORBIDDEN
- **Immersion:** 60% Ukrainian
- **Pedagogy:** TTT / Narrative
- **Full aspect system, motion verbs, participles**

### B2 (Modules 01-125)
- **Transliteration:** ⛔ FORBIDDEN
- **Immersion:** 80% Ukrainian
- **Pedagogy:** TTT / Narrative / CLIL
- **Passive voice, phraseology, history**

### C1 (Modules 01-115)
- **Transliteration:** ⛔ FORBIDDEN
- **Immersion:** 95% Ukrainian
- **Academic/Professional focus**

### C2 (Modules 01-80)
- **Transliteration:** ⛔ FORBIDDEN
- **Immersion:** 100% Ukrainian
- **Native mastery, literary style**
