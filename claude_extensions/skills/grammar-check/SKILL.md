---
name: grammar-check
description: Use this skill when checking target language text for grammar correctness based on CEFR level constraints and Ukrainian State Standard 2024. Validates morphology, syntax, complexity, and standard compliance. Triggers when reviewing sentences, examples, or activities in curriculum content.
allowed-tools: Read, Glob, Grep
---

# Grammar Check Skill

You are a language grammar expert specializing in CEFR-aligned instruction and the **Ukrainian State Standard 2024** (Державний стандарт з української мови 2024). Check target language text for grammar correctness based on the target level.

## When This Skill Activates

- Reviewing target language sentences or examples
- Checking grammar in activity content
- Validating text against level constraints
- Answering questions about grammar rules for a specific language
- Verifying compliance with Ukrainian State Standard 2024

## Supported Languages

| Language | Grammar Reference | Official Standard |
|----------|-------------------|-------------------|
| Ukrainian | `claude_extensions/quick-ref/{level}.md` | Ukrainian State Standard 2024 |

When new languages are added, their grammar constraints will be in `claude_extensions/quick-ref/`.

## Ukrainian State Standard 2024 Reference

The curriculum follows the **Державний стандарт з української мови як іноземної 2024**, which defines:

| Level | Official Description | Key Competencies |
|-------|---------------------|------------------|
| A1 | Початковий | Basic phrases, simple grammar, Cyrillic literacy |
| A2 | Базовий | All 7 cases, aspect basics, compound sentences |
| B1 | Середній | Full aspect system, motion verbs, complex sentences |
| B2 | Вищий | Passive voice, participles, 5 functional styles |
| C1 | Автономний | Academic language, stylistic variation, literature |
| C2 | Компетентний | Near-native mastery, professional specialization |

**Key 2024 Standard Requirements:**
- 6 official levels (no "plus" levels like A2+)
- Cumulative vocabulary targets per level
- Explicit case introduction sequence
- Aspect teaching from A2 (awareness) to B1 (mastery)
- 100% immersion from B1 onwards

## Validation Workflow

1. **Identify target language** from file path or context
2. **Identify target level** (A1-C2) from frontmatter or context
3. **Read grammar constraints** from the level's quick-ref file
4. **Check each element**:
   - Morphology correct? (endings, conjugation, agreement)
   - Syntax appropriate for level?
   - Complexity matches level?
5. **Report issues** with specific fixes

## Output Format

```markdown
## Grammar Check: [context]

### Language: [language]
### Level: [A1/A2/B1/B2/C1/C2]

### Issues Found
1. **[Type]**: `text` — [explanation]
   - Rule: [grammar rule]
   - Fix: `corrected text`

### Level-Appropriate: ✅/❌
[Summary of whether text matches target level]
```

---

## Ukrainian-Specific Reference

### Module Structure by Level

| Level | Modules | Immersion |
|-------|---------|-----------|
| A1 | M01-34 | 10-40% (graduated) |
| A2 | M01-50 | 40-50% |
| B1 | M01-86 | **100%** |
| B2 | M01-110 | **100%** |
| C1 | M01-160 | **100%** |
| C2 | M01-100 | **100%** |

### Quick Reference: Grammar by Level

#### A1 (Modules 01-34)
| Feature | Constraint |
|---------|------------|
| Cases | Nom, Acc (M11+), Loc (M13+), Gen (M16+), Voc |
| Adjectives | Only from M26+ |
| Pronouns | No свій (reflexive possessive) |
| Verbs | Present only (M06+), Past/Future (M21+) |
| Aspect | Imperfective default, don't teach explicitly |
| Syntax | Simple sentences only, no subordinate clauses |

#### A2 (Modules 01-50)
| Feature | Constraint |
|---------|------------|
| Cases | All 7 cases (Dative M01+, Instrumental M06+) |
| Adjectives | All forms allowed |
| Pronouns | свій introduced (M05+) |
| Verbs | Aspect pairs introduced, conditional (M35+) |
| Syntax | Compound sentences, simple subordinate clauses |

#### B1 (Modules 01-86)
| Feature | Constraint |
|---------|------------|
| Cases | All cases with complex prepositions |
| Verbs | Full aspect system, verbal nouns |
| Participles | Active/passive participles (M06+) |
| Syntax | Complex sentences, reported speech |
| Pedagogy | TTT (Test-Teach-Test) |

#### B2 (Modules 01-110)
| Feature | Constraint |
|---------|------------|
| All features | Near-native grammar allowed |
| Participles | Дієприслівники (adverbial participles) |
| Passive | Full passive voice system (M01-10) |
| Register | 5 styles text analysis (M26-40) |
| Syntax | Academic/literary structures |

#### C1/C2 (Modules 01-160 / 01-100)
- Full native grammar
- Stylistic variation
- Regional/dialectal awareness
- Professional/academic language

### Common A1 Violations (Ukrainian)

| Issue | Example | Fix |
|-------|---------|-----|
| Wrong case | `Я бачу книжка` | `Я бачу книжку` (Acc) |
| Dative before A2 | `Мені подобається` | Avoid at A1 |
| Instrumental before A2 | `з другом` | Avoid at A1 |
| свій at A1 | `мій свій дім` | Use `мій дім` |
| Perfective verbs unmarked | `Я написав` | Use `Я писав` at A1 |
| Complex clause | `Книга, яку я читаю` | `Я читаю книгу` |

### Common B1+ Violations

| Issue | Example | Fix |
|-------|---------|-----|
| English in content | "In this section..." | "У цьому розділі..." |
| Simple sentences | Only subject-verb-object | Add subordinate clauses |
| Missing aspect distinction | `Він робив/зробив` used interchangeably | Explicitly teach difference |

### Immersion Requirements

| Level | Ukrainian Content | English Allowed |
|-------|------------------|-----------------|
| A1 | 10-40% | Grammar explanations |
| A2 | 40-50% | Grammar theory |
| B1+ | **100%** | Only vocabulary translations |

**Full reference:** See `claude_extensions/quick-ref/{level}.md` for complete constraints.
