---
name: history-module-architect
description: Use this skill when creating or reviewing history modules (B2) and biography modules (C1). Provides guidance on historical narrative, primary sources, decolonization perspective, and era-appropriate vocabulary. Always read the template first.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# History & Biography Module Architect Skill

Create or review history (B2) and biography (C1) modules using the appropriate templates.

---

## When to Use This Skill

- Creating B2 history modules (M71-131): Ukrainian history from Origins to Present
- Creating B2 synthesis modules (M83, M107, M119, M125, M131): Cross-era analysis
- Creating C1 biography modules (M36-100): 65 Ukrainian historical & cultural figures
- Working with primary sources and historical documents
- Ensuring decolonization perspective and historical accuracy

---

## Template Locations

| Level        | Template                                                          | Modules                     |
| ------------ | ----------------------------------------------------------------- | --------------------------- |
| B2 History   | `docs/l2-uk-en/templates/b2-history-module-template.md`           | M71-131 (excl. synthesis)   |
| B2 Synthesis | `docs/l2-uk-en/templates/b2-history-synthesis-module-template.md` | M83, M108, M119, M125, M131 |
| C1 Biography | `docs/l2-uk-en/templates/c1-biography-module-template.md`         | M36-100                     |

**CRITICAL:** Read the template BEFORE creating a module.

> **Note:** Synthesis modules replace traditional checkpoints in B2.3 History. They test cross-era analysis and historical argumentation, not recall. See GitHub issue #332.

---

## Language Quality: Use `grammar-check` Skill

**All Ukrainian text MUST be validated using the `grammar-check` skill** (Ukrainian Grammar Validator).

Detects: Russianisms, surzhyk, calques, agreement/case errors.

**Trusted dictionaries:** Словник.UA, Словарь Грінченка, Антоненко-Давидович "Як ми говоримо"

**NOT Trusted:** Google Translate, Russian-Ukrainian dictionaries

---

## Core Principles

### 1. Ukrainian Perspective (Decolonization)

| Colonial Myth               | Ukrainian Reality                           |
| --------------------------- | ------------------------------------------- |
| Shevchenko = "Russian poet" | Ukrainian poet persecuted by Russian Empire |
| Mazepa = "traitor"          | Defender of Ukrainian autonomy              |
| Hrushevsky = "nationalist"  | Historian documenting Ukrainian statehood   |

### 2. Historical Terminology

| Before 1721                                                | After 1721        |
| ---------------------------------------------------------- | ----------------- |
| Московське царство                                         | Російська імперія |
| **Never use:** Malorossiya, Little Russia, Russian framing |

### 3. Primary Sources

Include authentic historical documents:

- Quotes from letters and speeches
- Excerpts from treaties and declarations
- Literary passages

### 4. Era Context

Every historical/biographical module must include:

- Political situation of the era
- Cultural movements
- Language situation (Russification, national revival, etc.)

---

## B2 History Focus Areas

| Phase | Modules  | Era                                                    |
| ----- | -------- | ------------------------------------------------------ |
| B2.3a | M71-83   | Origins → Commonwealth (Trypillia to Lithuania)        |
| B2.3b | M84-107  | Cossack Era & Empire (Sich to 1920s)                   |
| B2.3c | M108-119 | Trauma & Resistance (Executed Renaissance to Diaspora) |
| B2.3d | M120-125 | Independence Era (1991-2013)                           |
| B2.3e | M126-131 | Revolution & War (2014-present)                        |

**Synthesis Modules:** M83, M108, M119, M125, M131 — cross-era thematic analysis (NOT quiz-style checkpoints)

---

## CRITICAL: Language Testing, Not Content Recall

<critical>

**The Golden Rule:** "Can the learner answer this without reading the Ukrainian text?"

- **If YES** → Rewrite (tests history knowledge)
- **If NO** → Keep (tests Ukrainian comprehension)

</critical>

### Activity Requirements (10-12 total)

| Activity Type         | Count | Key Requirement                                                  |
| --------------------- | ----- | ---------------------------------------------------------------- |
| quiz                  | 4-5   | MUST start with "Згідно з текстом..."                            |
| fill-in/cloze         | 3-4   | Test collocations (чинити спротив, відіграти роль, брати участь) |
| error-correction      | 2-3   | Fix GRAMMAR errors, NOT factual inaccuracies                     |
| match-up              | 1-2   | Ukrainian term ↔ Ukrainian definition                            |
| select/mark-the-words | 1-2   | Find grammatical features in text                                |

### Forbidden Patterns

❌ "У якому році [event]?"  
❌ "Хто був [person]?"  
❌ "Скільки [number]?"  
❌ "Що символізує [symbol]?" (without "як автор тлумачить")

### Required Patterns

✅ "Згідно з текстом, як автор пояснює причини..."  
✅ "У тексті модуля автор характеризує..."  
✅ "Яку функцію автор підкреслює..."  
✅ "Який аргумент автор наводить..."

### Self-Check Before Delivering

For EVERY quiz question:

1. Can learner answer without reading Ukrainian module text?
2. If YES → You're testing history. STOP and rewrite.
3. If NO → You're testing Ukrainian. Proceed.

### Synthesis Module Structure (Different from Regular History)

| Section                    | Purpose                                           |
| -------------------------- | ------------------------------------------------- |
| **Узагальнення епохи**     | 500+ word synthesis connecting all modules in era |
| **Хронологія**             | Timeline reconstruction activity (12+ events)     |
| **Словник епохи**          | Era vocabulary REVIEW (not new vocab)             |
| **Есе-аналіз**             | 250-400 word analytical essay with model answer   |
| **Зв'язок із сьогоденням** | Connection to modern Ukraine                      |

See `b2-history-synthesis-module-template.md` for full structure and example essay prompts

---

## C1 Biography Distribution

| Era           | Modules | Count |
| ------------- | ------- | ----- |
| Pre-modern    | M36-45  | 10    |
| Cossack       | M46-55  | 10    |
| Imperial      | M56-70  | 15    |
| Revolutionary | M71-78  | 8     |
| Soviet        | M79-88  | 10    |
| Independence  | M89-100 | 12    |

**Gender balance:** Minimum 30% women (20+ modules)

---

## Biography Structure

1. **Hook & Context** — Why this figure matters (300-400 words)
2. **Біографія** — Main narrative (800-1000 words)
   - Ранні роки (Early years)
   - Шлях до визнання (Rise to prominence)
   - Головні досягнення (Major achievements)
   - Спадщина (Legacy)
3. **Історичний контекст** — Era background (300-400 words)
4. **Порівняльний аналіз** — Comparison with contemporaries (300-400 words)

---

## Quick Checklist

Before submitting a history/biography module:

- [ ] **Template read?** — Level-specific template consulted
- [ ] **Word count:** 2000+ words (biography), 1500+ words (history)
- [ ] **Primary sources:** Quotes, letters, or speeches included
- [ ] **Historical context:** Era's political/cultural situation explained
- [ ] **Decolonization:** Ukrainian perspective, not Russian framing
- [ ] **Legacy section:** Connection to modern Ukraine
- [ ] **Vocabulary:** 35+ items for biography, 25+ for history
- [ ] **Activities:** 12+ with comprehension emphasis
- [ ] **Era categorization:** Figures correctly placed in historical periods
- [ ] **Engagement boxes:** Include 📜 Primary Source, ⚠️ Decolonization
- [ ] **Immersion:** 100% Ukrainian

---

## Common History/Biography Mistakes

1. **Russian framing** — Use "Російська імперія", not "Russia" for empire
2. **Missing primary sources** — Always include quotes or documents
3. **Ahistorical language** — Use period-appropriate terminology
4. **No legacy connection** — Always link to modern Ukraine
5. **Gender imbalance** — Ensure 30%+ women across biography modules
6. **Victimhood narrative** — Emphasize Ukrainian agency and resistance

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
