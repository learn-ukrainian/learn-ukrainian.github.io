---
name: history-module-architect
description: Use this skill when creating or reviewing history modules (B2) and biography modules (C1). Provides guidance on historical narrative, primary sources, decolonization perspective, and era-appropriate vocabulary. Always read the template first.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# History & Biography Module Architect Skill

Create or review history (B2) and biography (C1) modules using the appropriate templates.

---

## When to Use This Skill

- Creating B2 history modules (M26-40): Ukrainian history from Kyivan Rus to present
- Creating C1 biography modules (M36-100): 65 Ukrainian historical & cultural figures
- Working with primary sources and historical documents
- Ensuring decolonization perspective and historical accuracy

---

## Template Locations

| Level | Template | Modules |
|-------|----------|---------|
| B2 | `docs/l2-uk-en/templates/b2-history-module-template.md` | M26-40 |
| C1 | `docs/l2-uk-en/templates/c1-biography-module-template.md` | M36-100 |

**CRITICAL:** Read the template BEFORE creating a module.

---

## Core Principles

### 1. Ukrainian Perspective (Decolonization)

| Colonial Myth | Ukrainian Reality |
|---------------|-------------------|
| Shevchenko = "Russian poet" | Ukrainian poet persecuted by Russian Empire |
| Mazepa = "traitor" | Defender of Ukrainian autonomy |
| Hrushevsky = "nationalist" | Historian documenting Ukrainian statehood |

### 2. Historical Terminology

| Before 1721 | After 1721 |
|-------------|------------|
| Московське царство | Російська імперія |
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

| Phase | Modules | Era |
|-------|---------|-----|
| B2.3 | M26-30 | Kyivan Rus and medieval Ukraine |
| B2.3 | M31-35 | Cossack era (Hetmanate) |
| B2.3 | M36-40 | Imperial era to independence |

---

## C1 Biography Distribution

| Era | Modules | Count |
|-----|---------|-------|
| Pre-modern | M36-45 | 10 |
| Cossack | M46-55 | 10 |
| Imperial | M56-70 | 15 |
| Revolutionary | M71-78 | 8 |
| Soviet | M79-88 | 10 |
| Independence | M89-100 | 12 |

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
python3 scripts/audit_module.py curriculum/l2-uk-en/{level}/{module-file}.md
```

---

## Related Documents

- `claude_extensions/quick-ref/{level}.md` — Level constraints
- `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` — Module specifications
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` — Quality standards
