---
name: grammar-check
description: Use this skill when checking target language text for grammar correctness based on CEFR level constraints. Validates morphology, syntax, and complexity. Triggers when reviewing sentences, examples, or activities in curriculum content.
allowed-tools: Read, Glob, Grep
---

# Grammar Check Skill

You are a language grammar expert specializing in CEFR-aligned instruction. Check target language text for grammar correctness based on the target level.

## When This Skill Activates

- Reviewing target language sentences or examples
- Checking grammar in activity content
- Validating text against level constraints
- Answering questions about grammar rules for a specific language

## Supported Languages

| Language | Grammar Reference |
|----------|-------------------|
| Ukrainian | `docs/l2-uk-en/module-prompt.md` (Section: Grammar Constraints by Level) |

When new languages are added, their grammar constraints will be in `docs/{lang-pair}/module-prompt.md`.

## Validation Workflow

1. **Identify target language** from file path or context
2. **Identify target level** (A1-C2) from frontmatter or context
3. **Read grammar constraints** from the language's module-prompt.md
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

### Quick Reference: Grammar by Level

#### A1 (Modules 1-30)
| Feature | Constraint |
|---------|------------|
| Cases | Nom, Acc (M11+), Loc (M13+), Gen (M16+), Voc |
| Adjectives | Only from M26+ |
| Pronouns | No свій (reflexive possessive) |
| Verbs | Present only (M06+), Past/Future (M21+) |
| Aspect | Imperfective default, don't teach explicitly |
| Syntax | Simple sentences only, no subordinate clauses |

#### A2 (Modules 31-60)
| Feature | Constraint |
|---------|------------|
| Cases | All 7 cases (Dative M31+, Instrumental M36+) |
| Adjectives | All forms allowed |
| Pronouns | свій introduced (M35+) |
| Verbs | Aspect pairs introduced, conditional (M55+) |
| Syntax | Compound sentences, simple subordinate clauses |

#### B1 (Modules 81-140)
| Feature | Constraint |
|---------|------------|
| Cases | All cases with complex prepositions |
| Verbs | Full aspect system, verbal nouns |
| Participles | Active/passive participles |
| Syntax | Complex sentences, reported speech |

#### B2 (Modules 141-180)
| Feature | Constraint |
|---------|------------|
| All features | Near-native grammar allowed |
| Participles | Dієприслівники (adverbial participles) |
| Syntax | Academic/literary structures |

#### C1/C2 (Modules 181-220)
- Full native grammar
- Stylistic variation
- Regional/dialectal awareness

### Common A1 Violations (Ukrainian)

| Issue | Example | Fix |
|-------|---------|-----|
| Wrong case | `Я бачу книжка` | `Я бачу книжку` (Acc) |
| Dative before M31 | `Мені подобається` | Avoid at A1 |
| Instrumental before M36 | `з другом` | Avoid at A1 |
| свій at A1 | `мій свій дім` | Use `мій дім` |
| Perfective verbs | `Я написав` | Use `Я писав` |
| Complex clause | `Книга, яку я читаю` | `Я читаю книгу` |
