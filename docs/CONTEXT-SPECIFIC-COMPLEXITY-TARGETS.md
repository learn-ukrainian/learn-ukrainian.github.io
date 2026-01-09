# Context-Specific Complexity Targets (B1 & B2)

> **Philosophy:** Quality over quantity. Different module types have different pedagogical needs.

## Rationale

Uniform complexity targets across all module types create unnecessary friction:

- **History/Biography modules:** Factual questions are naturally shorter ("Where was X born?" vs. artificial elaboration)
- **Cultural modules:** Authentic materials (song lyrics, proverbs) may be shorter than arbitrary word counts
- **Vocabulary modules:** Testing vocabulary recognition can be more direct

**Solution:** Context-specific complexity targets that match pedagogical reality while maintaining rigor.

---

## B2 Context-Specific Targets

### Standard B2 (Grammar/Vocabulary M01-70)

| Activity | Minimum | Maximum |
|----------|---------|---------|
| Quiz | 10 words | 25 words |
| Fill-in | 10 words | 16 words |
| Unjumble | 10 words | 18 words |
| Error-correction | 10 words | 20 words |
| True-false | 10 words | 22 words |
| Mark-the-words | 12 words | 22 words |
| Select | 10 words | 18 words |
| Translate | 10 words | 18 words |
| **Activities** | **13+** | - |

### B2-History / B2-Biography (M71-131)

| Activity | Minimum | Maximum | Rationale |
|----------|---------|---------|-----------|
| Quiz | **6 words** | **20 words** | Biographical facts are naturally shorter |
| Fill-in | **7 words** | **14 words** | Historical facts can be concise |
| Unjumble | **7 words** | **15 words** | Allows authentic historical quotes |
| Error-correction | **7 words** | **18 words** | Historical errors in shorter sentences |
| True-false | **7 words** | **20 words** | Historical facts can be shorter |
| Mark-the-words | **10 words** | **20 words** | Historical passages can be shorter |
| Select | **8 words** | **16 words** | Historical selection can be direct |
| Translate | **7 words** | **16 words** | Historical translation can be shorter |
| **Activities** | **10-12** | - | Content-heavy modules (not 13+) |

**Examples of naturally short historical questions:**
- ✅ "Де народився Тарас Шевченко?" (4 words - acceptable)
- ✅ "У якому році відбулася Помаранчева революція?" (6 words - acceptable)
- ❌ "У якому місті, що знаходиться на території сучасної Київської області, народився майбутній великий національний поет України Тарас Григорович Шевченко?" (20 words - artificial elaboration)

---

## B1 Context-Specific Targets

### Standard B1 (Grammar M06-51)

| Activity | Minimum | Maximum |
|----------|---------|---------|
| Quiz | 12 words | 20 words |
| Fill-in | 10 words | 14 words |
| Unjumble | 12 words | 16 words |
| Error-correction | 10 words | 16 words |
| True-false | 10 words | 18 words |
| Mark-the-words | 12 words | 18 words |
| Select | 10 words | 14 words |
| Translate | 8 words | 14 words |
| **Activities** | **12+** | - |

### B1-Vocab (M52-71)

| Activity | Minimum | Maximum | Rationale |
|----------|---------|---------|-----------|
| Quiz | **10 words** | **18 words** | Vocabulary testing can be more direct |
| Fill-in | **8 words** | **12 words** | Vocabulary practice can be concise |
| Unjumble | **10 words** | **14 words** | Vocabulary sentences can be simpler |
| Error-correction | **8 words** | **14 words** | Vocabulary errors in shorter sentences |
| True-false | **8 words** | **16 words** | Vocabulary facts can be concise |
| Mark-the-words | **10 words** | **16 words** | Vocabulary marking in shorter passages |
| Select | **8 words** | **12 words** | Vocabulary selection can be direct |
| Translate | **6 words** | **12 words** | Vocabulary translation can be brief |
| **Activities** | **12+** | - | Standard count |

### B1-Cultural (M72-81)

| Activity | Minimum | Maximum | Rationale |
|----------|---------|---------|-----------|
| Quiz | **8 words** | **18 words** | Cultural facts can be concise |
| Fill-in | **8 words** | **12 words** | Cultural context can be briefer |
| Unjumble | **10 words** | **14 words** | Cultural sentences can be shorter |
| Error-correction | **8 words** | **14 words** | Cultural errors in shorter sentences |
| True-false | **8 words** | **16 words** | Cultural facts can be concise |
| Mark-the-words | **10 words** | **16 words** | Cultural marking in shorter passages |
| Select | **8 words** | **12 words** | Cultural selection can be direct |
| Translate | **6 words** | **12 words** | Cultural translation can be brief |
| **Activities** | **10-12** | - | Content-heavy modules (not 12+) |

---

## Implementation

### Audit Script

The audit script (`scripts/audit/config.py`) now supports context-specific complexity lookup:

1. **Primary lookup:** `{level}-{focus}` (e.g., `B2-history`, `B1-cultural`)
2. **Fallback:** `{level}` (e.g., `B2`, `B1`)

### Module Detection

Module focus is detected from YAML frontmatter or LEVEL_CONFIG keys:
- `B2-history` (M71-131)
- `B2-biography` (M71-131)
- `B1-vocab` (M52-71)
- `B1-cultural` (M72-81)
- `B1-grammar` (M06-51) - uses standard B1 targets

### Backward Compatibility

All existing modules continue to work with standard targets. Context-specific targets are opt-in via module focus classification.

---

## Testing

### Sample Module Testing

Test the new targets on representative modules:

**B2:**
- M100 (Shevchenko biography) - should pass with 6-20 word quiz questions
- M110 (Holodomor history) - should pass with authentic historical quotes

**B1:**
- M60 (Abstract vocabulary) - should pass with 8-12 word fill-ins
- M75 (Ukrainian music culture) - should pass with shorter cultural facts

### Migration Path

1. ✅ Config updated with context-specific entries
2. ⏳ Documentation updated (this file)
3. ⏳ Quick-ref files updated for B1/B2
4. ⏳ Re-audit B2 M100-105 to validate
5. ⏳ Spot-check B1 M52-81 for improvements

---

## Benefits

1. **Reduced Artificial Elaboration:** No more padding short biographical facts
2. **Authentic Materials:** Historical quotes and song lyrics can remain authentic
3. **Pedagogical Alignment:** Complexity targets match learning objectives
4. **Maintained Rigor:** Grammar modules keep strict standards

**Quality over quantity.**
