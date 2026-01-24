---
name: vocab-module-architect
description: Use this skill when creating or reviewing vocabulary expansion modules (B1). Provides guidance on thematic vocabulary presentation, collocations, synonymy, and register differentiation. Always read the template first.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

> **PERSONA:** Embody the Ukrainian linguist & historian. See `claude_extensions/skills/_shared/persona.md`

# Vocabulary Module Architect Skill

Create or review vocabulary-focused modules using the B1 vocabulary template.

---

## When to Use This Skill

- Creating B1 vocabulary expansion modules (M51-70)
- Teaching abstract concepts, opinions, discourse markers
- Working with collocations, synonymy, and register
- Creating thematic vocabulary presentations

---

## Template Location

| Level | Template                                              | Modules |
| ----- | ----------------------------------------------------- | ------- |
| B1    | `docs/l2-uk-en/templates/b1-vocab-module-template.md` | M51-70  |

**CRITICAL:** Read the template BEFORE creating a module.

---

## Language Quality: Use `grammar-check` Skill

**All Ukrainian text MUST be validated using the `grammar-check` skill** (Ukrainian Grammar Validator).

Detects: Russianisms, surzhyk, calques, agreement/case errors.

**Trusted dictionaries:** Словник.UA, Словарь Грінченка, Антоненко-Давидович "Як ми говоримо"

**NOT Trusted:** Google Translate, Russian-Ukrainian dictionaries

---

## Vocabulary Module Characteristics

| Aspect     | Grammar Module    | Vocabulary Module                        |
| ---------- | ----------------- | ---------------------------------------- |
| Focus      | Grammar rules     | Word usage & context                     |
| Pedagogy   | TTT               | PPP                                      |
| Activities | All types         | Emphasis on match-up, group-sort, select |
| Tables     | Grammar paradigms | Collocation tables                       |
| Reading    | Examples          | Authentic passages (2-3)                 |

---

## Core Principles

### 1. Teach Collocations, Not Isolated Words

```markdown
| Слово     | Типові колокації              | Приклад         |
| --------- | ----------------------------- | --------------- |
| **ідея**  | мати ідею, цікава ідея        | У мене є ідея.  |
| **думка** | на мою думку, висловити думку | На мою думку... |
```

### 2. Differentiate Synonyms by Usage

- **ідея** → concrete proposal, creative suggestion
- **думка** → opinion, personal view
- **концепція** → theoretical framework (formal)

### 3. Mark Register Differences

- **Розмовна:** У мене є ідея!
- **Формальна:** Висуваю гіпотезу, що...

### 4. Organize by Semantic Field

Group vocabulary thematically:

- Ідеї та думки (Ideas and Thoughts)
- Проблеми та виклики (Problems and Challenges)
- Рішення та підходи (Solutions and Approaches)

---

## Activity Priorities

| Priority   | Activity Types             | Purpose                       |
| ---------- | -------------------------- | ----------------------------- |
| **HIGH**   | match-up (12+)             | Collocation practice          |
| **HIGH**   | group-sort (16+)           | Semantic categorization       |
| **HIGH**   | select (8+)                | Multiple correct collocations |
| **HIGH**   | fill-in (12+)              | Contextual usage              |
| **MEDIUM** | cloze (14+)                | Extended passage              |
| **MEDIUM** | quiz (8+)                  | Comprehension                 |
| **LOW**    | unjumble, error-correction | Production                    |

---

## Quick Checklist

Before submitting a vocabulary module:

- [ ] **Template read?** — `b1-vocab-module-template.md` consulted
- [ ] **Word count:** 1500+ words
- [ ] **Vocabulary:** 25-30 items in YAML Sidecar
- [ ] **Thematic groups:** Vocabulary organized by semantic field
- [ ] **Collocations:** Explicitly taught in tables and activities
- [ ] **Synonymy:** Similar words differentiated by usage
- [ ] **Register:** Formal vs informal marked
- [ ] **Reading passages:** 2-3 authentic texts
- [ ] **Activities:** 12+ with emphasis on match-up, group-sort, select
- [ ] **Engagement boxes:** 5+ focusing on usage
- [ ] **Immersion:** 90-100% Ukrainian

---

## Common Vocabulary Module Mistakes

1. **Words in isolation** — Always teach collocations
2. **No register marking** — Distinguish formal/informal
3. **Synonyms treated as identical** — Show usage differences
4. **Alphabetical organization** — Use semantic groups
5. **Too few match-up/select activities** — Prioritize collocation practice
6. **No authentic reading** — Include 2-3 real passages

---

## Validation

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/{module-file}.md
```

---

## Related Documents

- `claude_extensions/quick-ref/b1.md` — B1 constraints
- `docs/l2-uk-en/B1-CURRICULUM-PLAN.md` — M51-70 specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` — Quality standards
