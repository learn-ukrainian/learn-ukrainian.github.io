---
name: cultural-module-architect
description: Use this skill when creating or reviewing cultural modules (B1-C1). Provides guidance on authentic materials, regional balance, contemporary focus, and reading comprehension activities. Always read the template first.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Cultural Module Architect Skill

Create or review cultural modules using the appropriate level-specific template.

---

## When to Use This Skill

- Creating B1 cultural modules (M71-80): Regions, Music, Cinema, Technology
- Creating C1 cultural modules: Folk culture, sociolinguistics
- Working with authentic Ukrainian materials
- Ensuring cultural accuracy and regional balance

---

## Template Locations

| Level | Template                                                     | Modules |
| ----- | ------------------------------------------------------------ | ------- |
| B1    | `docs/l2-uk-en/templates/b1-cultural-module-template.md`     | M71-80  |
| C1    | `docs/l2-uk-en/templates/c1-folk-culture-module-template.md` | Various |

**CRITICAL:** Read the template BEFORE creating a module.

---

## Language Quality: Use `grammar-check` Skill

**All Ukrainian text MUST be validated using the `grammar-check` skill** (Ukrainian Grammar Validator).

Detects: Russianisms, surzhyk, calques, agreement/case errors.

**Trusted dictionaries:** Словник.UA, Словарь Грінченка, Антоненко-Давидович "Як ми говоримо"

**NOT Trusted:** Google Translate, Russian-Ukrainian dictionaries

---

## Cultural Module Characteristics

| Aspect     | Grammar/Vocab Module | Cultural Module        |
| ---------- | -------------------- | ---------------------- |
| Focus      | Language structure   | Cultural content       |
| Content    | Constructed examples | Authentic materials    |
| Reading    | Short examples       | Extended passages (3+) |
| Activities | All types            | Comprehension emphasis |
| Resources  | Optional             | **MANDATORY**          |

---

## Core Principles

### 1. Contemporary Focus

Focus on modern Ukraine (post-1991, especially 2014-present):

- Eurovision victories
- IT sector achievements
- Contemporary artists and filmmakers
- Current cultural movements

### 2. Regional Balance

Include all regions of Ukraine:

- West (Lviv, Zakarpattia)
- East (Kharkiv, Donetsk)
- South (Odesa, Kherson)
- Center (Kyiv, Poltava)

### 3. Authentic Materials

Use real Ukrainian sources:

- Wikipedia (Ukrainian)
- News articles
- Cultural commentary
- Blogs and interviews

### 4. No Stereotypes

**Avoid:**

- "All Ukrainians love borscht"
- Oversimplified national character
- Soviet-era framing

**Do:**

- Show diversity and complexity
- Name real people and achievements
- Present multiple perspectives

---

## Activity Priorities

| Priority   | Activity Types      | Purpose               |
| ---------- | ------------------- | --------------------- |
| **HIGH**   | quiz (10+)          | Reading comprehension |
| **HIGH**   | true-false (10+)    | Fact verification     |
| **HIGH**   | match-up (12+)      | People/places/terms   |
| **HIGH**   | cloze (14+)         | Extended passage      |
| **MEDIUM** | group-sort (16+)    | Categorization        |
| **MEDIUM** | select (8+)         | Multiple correct      |
| **LOW**    | unjumble, translate | Production            |

---

## CRITICAL: Language Testing, Not Content Recall

<critical>

**The Golden Rule:** "Can the learner answer this without reading the Ukrainian text?"

- **If YES** → Rewrite (tests cultural knowledge)
- **If NO** → Keep (tests Ukrainian comprehension)

</critical>

### Activity Requirements (10-12 total for C1 Folk/Arts)

| Activity Type    | Count | Key Requirement                              |
| ---------------- | ----- | -------------------------------------------- |
| quiz             | 4-5   | MUST start with "Згідно з текстом..."        |
| fill-in/cloze    | 3-4   | Test collocations from cultural vocabulary   |
| error-correction | 2-3   | Fix GRAMMAR errors, NOT factual inaccuracies |
| match-up         | 1-2   | Ukrainian term ↔ Ukrainian definition        |

### Forbidden Patterns

❌ "У якому році [event]?"  
❌ "Хто створив [work]?"  
❌ "Де розташований [place]?"

### Required Patterns

✅ "Згідно з текстом, як автор характеризує..."  
✅ "У тексті модуля автор підкреслює..."  
✅ "Які особливості автор виділяє..."

---

## Quick Checklist

Before submitting a cultural module:

- [ ] **Template read?** — Level-specific template consulted
- [ ] **Word count:** 1500+ words
- [ ] **Reading passages:** 3+ authentic texts (200-300 words each)
- [ ] **Comprehension questions:** 3-5 per passage
- [ ] **Resources section:** 5+ links to authentic Ukrainian materials
- [ ] **Cultural accuracy:** All facts verified
- [ ] **Contemporary focus:** Post-2014 Ukraine prominent
- [ ] **Regional balance:** No region ignored
- [ ] **No stereotypes:** Diverse, nuanced presentation
- [ ] **Activities:** 12+ with comprehension emphasis
- [ ] **Vocabulary:** 25+ items thematically organized
- [ ] **Immersion:** 90-100% Ukrainian

---

## Common Cultural Module Mistakes

1. **Grammar-heavy approach** — Cultural modules focus on content, not grammar rules
2. **Only constructed texts** — Use adapted authentic materials
3. **Missing Resources section** — MANDATORY for cultural modules
4. **Regional bias** — Don't focus only on Kyiv/Lviv
5. **Outdated content** — Show contemporary Ukraine, not just history
6. **Soviet framing** — Use Ukrainian perspective, not imperial lens

---

## Validation

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{module-file}.md
```

---

## Related Documents

- `claude_extensions/quick-ref/{level}.md` — Level constraints
- `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` — Module specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` — Quality standards
