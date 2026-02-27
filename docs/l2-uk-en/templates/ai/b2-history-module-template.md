# HIST Module Template (AI-Optimized)

> **Full documentation:** `docs/l2-uk-en/templates/history-module-template.md`
> **Config source of truth:** `scripts/audit/config.py` → `history`

---

## PHASE 1: BEFORE WRITING

### Step 1.1: Identify Module Type

```
IF module in [M83, M107, M119, M125, M131]
  → USE b2-synthesis-module-template.md INSTEAD
  → STOP HERE

ELSE
  → CONTINUE with this template
```

### Step 1.2: Research Topic

```
⛔ STOP: Do NOT write from memory. Research first.

DO:
1. WebSearch: "[topic] site:history.org.ua"
2. WebSearch: "[topic] site:esu.com.ua"
3. WebSearch: "[topic] site:memory.gov.ua" (for 20th c.)
4. WebFetch: [URLs found above]

DO NOT:
- Use Wikipedia as primary source (information warfare risk)
- Invent dates, names, events
- Generate quotes from memory
```

### Step 1.3: Verify Sources

```
⛔ STOP: Verify before proceeding.

REQUIRED sources found:
- [ ] At least 1 academic source (.gov.ua or history.org.ua)
- [ ] At least 2 primary source excerpts (from litopys.org.ua or similar)
- [ ] Decolonization perspective available

IF missing sources → WebSearch again or mark [NEEDS VERIFICATION]
```

---

## PHASE 2: WRITE CONTENT

### Step 2.1: Create Files

```
CREATE 3 files:
1. curriculum/l2-uk-en/hist/{slug}.md        # Prose content
2. curriculum/l2-uk-en/hist/vocabulary/{slug}.yaml  # Vocabulary
3. curriculum/l2-uk-en/hist/activities/{slug}.yaml  # Activities
```

### Step 2.2: Write Markdown Content

**Required sections (in order):**

| Section | Words | Content |
|---------|-------|---------|
| `# Title` + `🎯 Чому це важливо?` | 50-100 | Hook, modern relevance |
| `## Вступ` | 150-200 | Dramatic opening, context |
| `## [Event Name]` | 800-1000 | Main narrative with embedded vocab |
| `## Первинні джерела` | 200-300 | ≥2 document excerpts with `[!quote]` |
| `## Деколонізаційний погляд` | 200-300 | Myth vs reality, Ukrainian perspective |
| `## Підсумок` | 100-150 | Summary |

**Total target: 4000+ words**

### Step 2.3: Primary Sources Format

```markdown
## Первинні джерела

### Документ 1: [Title]

**Контекст:** [1-2 sentences]

> [100-200 word excerpt in Ukrainian]
> _— Джерело: [Full attribution]_

**Лінгвістичний аналіз:**
- [Question about register/style]
- [Question about vocabulary]
- [Question about grammar patterns]
```

```
⚠️ CRITICAL: Questions must test LANGUAGE, not history knowledge.

✅ GOOD: "Знайдіть три приклади пасивного стану."
❌ BAD:  "Чому Хмельницький прийняв це рішення?"
```

### Step 2.4: Forbidden Patterns

```
DO NOT include:
- ## Vocabulary header (injected from YAML)
- ## Activities header (injected from YAML)
- ## Есе section (essay goes in activities YAML only)
- Conversational dialogs (history is reading-centric)
- Wikipedia-sourced claims without .gov.ua verification
```

---

## PHASE 3: WRITE ACTIVITIES YAML

### Step 3.1: Activity Requirements

```yaml
# activities/{slug}.yaml

# REQUIRED (per config.py):
min_activities: 3
max_activities: 9
required_types:
  - reading      # External reading task
  - essay-response  # 150-250 word essay
```

### Step 3.2: Reading Activity Template

```yaml
- type: reading
  id: hist-XX-reading-01
  title: "Аналіз первинного джерела"
  resource:
    type: primary_source
    url: "https://litopys.org.ua/..."  # VERIFY URL EXISTS
    title: "[Document title]"
  tasks:
    - "Знайдіть три приклади офіційного регістру."
    - "Які дієслова використовує автор?"
    - "Порівняйте синтаксис із сучасною мовою."
```

### Step 3.3: Essay Activity Template

```yaml
- type: essay-response
  id: hist-XX-essay-01
  title: "Есе: [Topic]"
  prompt: |
    Напишіть есе (150-250 слів) на тему: "[Topic]"

    Вимоги:
    - Використайте лексику модуля
    - Застосуйте деколонізаційний підхід
    - Наведіть приклади з первинних джерел
  rubric:
    - criterion: Мовна якість
      weight: 40
    - criterion: Використання матеріалу
      weight: 30
    - criterion: Структура
      weight: 20
    - criterion: Деколонізаційний підхід
      weight: 10
```

---

## PHASE 4: WRITE VOCABULARY YAML

### Step 4.1: Vocabulary Requirements

```yaml
# vocabulary/{slug}.yaml

# Per config.py history:
min_items: 25
format: 3-column (lemma, translation, note)
```

### Step 4.2: Vocabulary Template

```yaml
items:
  - lemma: [Ukrainian word]
    translation: [English]
    note: [context/collocation]
```

**Include categories:**
- Political/military terms
- Historiographical terms (джерело, свідчення)
- Decolonization terms (русифікація, колоніальний)
- Era-specific vocabulary

---

## PHASE 5: VALIDATE

### Step 5.1: Pre-Submission Checklist

```
⛔ STOP: Verify ALL before submitting.

CONTENT:
- [ ] 4000+ words (prose only, excluding vocab/activities)
- [ ] ≥2 primary source excerpts with [!quote] callouts
- [ ] Decolonization section present
- [ ] No dialogs (reading-centric only)
- [ ] No ## Vocabulary or ## Activities headers

ACTIVITIES (in YAML):
- [ ] 3-9 activities total
- [ ] Includes reading activity
- [ ] Includes essay-response (150-250 words)
- [ ] All URLs verified with WebFetch

VOCABULARY (in YAML):
- [ ] 25+ items
- [ ] 3-column format (lemma, translation, note)

SOURCES:
- [ ] No unverified Wikipedia claims
- [ ] Primary sources have full attribution
- [ ] Academic sources cited
```

### Step 5.2: Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/hist/{slug}.md
```

---

## QUICK REFERENCE

### Era-Specific Resources

| Era | Search |
|-----|--------|
| Ancient/Medieval | `site:history.org.ua`, `site:litopys.org.ua` |
| Cossack | `site:litopys.org.ua` (chronicles) |
| Imperial | `site:esu.com.ua` |
| Soviet/20th c. | `site:memory.gov.ua`, `site:uinp.gov.ua` |
| Independence | `site:ukrinform.ua` |

### Decolonization Vocabulary

| Use | Instead of |
|-----|------------|
| Московське царство | Росія (pre-1721) |
| Російська імперія | Росія (1721-1917) |
| Русифікація | "cultural integration" |
| Колоніальний наратив | "Russian perspective" |

### Common Errors

| Error | Fix |
|-------|-----|
| Essay in markdown | Move to activities YAML |
| Dialog sections | Remove, use primary sources instead |
| Wikipedia-only source | Add .gov.ua verification |
| Dates from memory | WebSearch to verify |
| ## Vocabulary header | Remove, YAML injection handles this |

---

**Template version:** 2.0-ai
**Last updated:** 2026-01-24
