---
name: integration-module-architect
description: Use this skill when creating or reviewing integration modules (B1-B2). Integration modules review and consolidate all skills from a level, combining grammar, vocabulary, and cultural content. Always read the template first.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Integration Module Architect Skill

Create or review integration modules that consolidate all skills from a level.

---

## When to Use This Skill

- Creating B1 integration modules (M81-86): Skills review, capstone
- Creating B2 integration modules (M106-110): Final consolidation
- Designing comprehensive review activities
- Ensuring all prior learning is tested

---

## Template Locations

| Level | Template | Modules |
|-------|----------|---------|
| B1 | `docs/l2-uk-en/templates/b1-integration-module-template.md` | M81-86 |
| B2 | `docs/l2-uk-en/templates/b2-integration-module-template.md` | M106-110 |

**CRITICAL:** Read the template BEFORE creating a module.

---

## Integration vs Checkpoint

| Aspect | Checkpoint | Integration |
|--------|------------|-------------|
| Scope | One phase | Entire level |
| Pedagogy | TTT | Review + Production |
| New content | None | None |
| Activities | 16+ | 14+ |
| Length | 1200+ words | 1500+ words |

---

## Integration Module Types

### Skills Integration (M81-83)

Focus on combining skills from different domains:
- Grammar + Vocabulary in context
- Reading + Listening comprehension
- Speaking + Writing production

### Level Review (M84-85)

Comprehensive review of all grammar and vocabulary:
- All tenses and aspects
- All cases and prepositions
- All vocabulary themes

### Capstone (M86/M110)

Final production module:
- Extended writing tasks
- Complex translation
- Portfolio preparation

---

## Core Principles

### 1. No New Content

Integration modules ONLY review existing knowledge. Never introduce:
- New grammar rules
- New vocabulary
- New cultural topics

### 2. Skill Combination

Activities should combine multiple skills:
- Grammar + vocabulary in same activity
- Reading + speaking (dialogue after passage)
- Listening + writing (dictation, summaries)

### 3. Authentic Application

Show how skills work together in real contexts:
- Extended dialogues
- Authentic texts
- Real-world scenarios

### 4. Self-Assessment

Include comprehensive "Чи можете ви..." checklists covering all level objectives.

---

## Activity Priorities

| Priority | Activity Types | Purpose |
|----------|---------------|---------|
| **HIGH** | cloze (16+) | Extended passage combining grammar |
| **HIGH** | translate (10+) | Productive skill test |
| **HIGH** | error-correction (10+) | All error types from level |
| **HIGH** | quiz (12+) | Comprehensive review |
| **MEDIUM** | dialogue-reorder (8+) | Discourse competence |
| **MEDIUM** | unjumble (8+) | Complex sentences |
| **LOW** | match-up, group-sort | Quick review |

---

## Quick Checklist

Before submitting an integration module:

- [ ] **Template read?** — Level-specific template consulted
- [ ] **Word count:** 1500+ words
- [ ] **No new content:** Only reviews existing knowledge
- [ ] **Skill coverage:** All major grammar and vocabulary areas
- [ ] **Activity count:** 14+ activities
- [ ] **Cloze density:** 16+ blanks (higher than regular)
- [ ] **Error-correction:** All error types from level
- [ ] **Self-assessment:** Comprehensive "Чи можете ви..." checklist
- [ ] **Authentic contexts:** Real-world application scenarios
- [ ] **Vocabulary review:** Items from ALL prior modules
- [ ] **Immersion:** 90-100% Ukrainian

---

## Common Integration Module Mistakes

1. **Introducing new grammar** — Integration is REVIEW only
2. **Too narrow focus** — Must cover entire level, not one phase
3. **Low activity density** — Need 14+ activities
4. **Missing self-assessment** — Required at end of integration modules
5. **Isolated skills** — Activities should combine grammar + vocabulary
6. **No authentic context** — Show real-world application

---

## Validation

```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/{level}/{module-file}.md
```

---

## Related Documents

- `claude_extensions/quick-ref/{level}.md` — Level constraints
- `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` — Module specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` — Quality standards
- `docs/l2-uk-en/templates/{level}-checkpoint-module-template.md` — Checkpoint comparison
