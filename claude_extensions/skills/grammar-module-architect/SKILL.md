---
name: grammar-module-architect
description: Use this skill when creating or reviewing grammar-focused modules (B1-B2). Provides pedagogical guidance for TTT/PPP structure, aspect teaching, motion verbs, and complex sentences. Always read the level-specific template first.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

> **PERSONA:** Embody the Ukrainian linguist & historian. See `claude_extensions/skills/_shared/persona.md`

# Grammar Module Architect Skill

Create or review grammar-focused modules using the appropriate level-specific template.

---

## When to Use This Skill

- Creating B1/B2 grammar modules (aspect, motion verbs, participles, passive voice)
- Reviewing grammar module structure and pedagogy
- Ensuring TTT/PPP pedagogical approach is correctly applied

---

## Template Locations

| Level | Template | Modules |
|-------|----------|---------|
| B1 | `docs/l2-uk-en/templates/b1-grammar-module-template.md` | M06-50 |
| B2 | `docs/l2-uk-en/templates/b2-grammar-module-template.md` | M01-25 |

**CRITICAL:** Read the template BEFORE creating a module. The template is authoritative.

---

## Language Quality: Use `grammar-check` Skill

**All Ukrainian text MUST be validated using the `grammar-check` skill.**

This skill integrates the Ukrainian Grammar Validator (adapted from "Ukrainian Tutor" Gem) which detects:
- **Russianisms** (кушать → їсти, кто → хто)
- **Surzhyk** (mixed Ukrainian-Russian grammar)
- **Calques** (English loan translations: "робити сенс" → "мати сенс")
- **Agreement errors, case errors, morphology errors**

**Trusted Ukrainian Dictionaries:**
- **Словник.UA** (slovnyk.ua) - standard spelling
- **Словарь Грінченка** - authentic Ukrainian forms
- **Антоненко-Давидович "Як ми говоримо"** - Russianisms vs authentic Ukrainian

**NOT Trusted:** Google Translate, Russian-Ukrainian dictionaries

---

## Core Pedagogy

### TTT (Test-Teach-Test) Structure

| Phase | Purpose | Content |
|-------|---------|---------|
| **Test** | Diagnostic discovery | Present contrast without explanation |
| **Teach** | Systematic explanation | Grammar rules in Ukrainian metalanguage |
| **Test** | Application practice | Activities testing understanding |

### PPP (Presentation-Practice-Production) Structure

| Phase | Purpose | Content |
|-------|---------|---------|
| **Presentation** | Introduce grammar | Examples with explanation |
| **Practice** | Controlled activities | Fill-in, match-up, cloze |
| **Production** | Free application | Dialogues, translation |

---

## Grammar-Specific Guidelines

### B1 Grammar Focus Areas

| Phase | Modules | Grammar Focus |
|-------|---------|---------------|
| B1.1 | M01-05 | Metalanguage, grammar review |
| B1.2 | M06-15 | **Aspect system** (НДВ/ДВ) |
| B1.3 | M16-25 | **Motion verbs** (definite/indefinite) |
| B1.4 | M26-40 | **Complex sentences** (subordinate clauses) |
| B1.5 | M41-50 | **Participles** (active/passive) |

### B2 Grammar Focus Areas

| Phase | Modules | Grammar Focus |
|-------|---------|---------------|
| B2.1 | M01-10 | **Passive voice** (full system) |
| B2.2 | M11-25 | **Adverbial participles** (дієприслівники) |

---

## Quick Checklist

Before submitting a grammar module:

- [ ] **Template read?** — Level-specific template consulted
- [ ] **Word count:** 1500+ words (core prose)
- [ ] **Vocabulary:** 25+ items in correct format (5-column for B1, 3-column for B2)
- [ ] **Activities:** 12+ with all types represented
- [ ] **Quiz questions:** 12-20 words each (complex, context-rich)
- [ ] **Unjumble:** 12-16 words per sentence
- [ ] **Cloze:** 14+ blanks per passage
- [ ] **Error-correction:** All 4 callouts required
- [ ] **Engagement boxes:** 5+ boxes
- [ ] **Immersion:** 90-100% Ukrainian
- [ ] **Pedagogy:** TTT or PPP structure clear

---

## Common Grammar Module Mistakes

1. **Grammar explained in English** — Use Ukrainian metalanguage (вид, доконаний, etc.)
2. **Quiz questions too short** — Must be 12-20 words with subordinate clauses
3. **Unjumble sentences too simple** — Must be 12-16 words with complex syntax
4. **Missing error-correction callouts** — All 4 required: `[!error]`, `[!answer]`, `[!options]`, `[!explanation]`
5. **No decision framework** — Include "Як обрати?" section for grammar choices

---

## Validation

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{module-file}.md
```

---

## Related Documents

- `claude_extensions/quick-ref/{level}.md` — Level constraints
- `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` — Module plans
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` — Quality standards
