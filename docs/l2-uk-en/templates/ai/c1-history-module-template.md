# C1-HIST Module Template (AI-Optimized)

> **Full documentation:** `docs/l2-uk-en/templates/c1-history-module-template.md`
> **Config source of truth:** `scripts/audit/config.py` → `C1-history`

---

## PHASE 1: BEFORE WRITING

### Step 1.1: Confirm Track

```
⛔ STOP: C1-HIST is NOT about historical facts (that's B2-HIST).
C1-HIST is about HOW we know history — sources, methods, historiography.

IF you need factual narrative → USE b2-history-module-template.md
IF you need source analysis, methodology, competing narratives → CONTINUE
```

### Step 1.2: Research Historiographical Content

```
⛔ STOP: Do NOT generate historiographical debates from memory.

DO:
1. WebSearch: "[topic] historiography Ukrainian"
2. WebSearch: "[historian name] праці"
3. WebSearch: "[primary source name] аналіз джерела"
4. WebFetch: http://resource.history.org.ua/...
5. WebFetch: http://nbuv.gov.ua/...

DO NOT:
- Invent historiographical debates
- Generate primary source text from memory
- Attribute views to historians without verification
- Use Wikipedia as primary source (information warfare risk)
```

### Step 1.3: Verify Sources

```
⛔ STOP: Verify before proceeding.

REQUIRED sources found:
- [ ] Academic historiographical source (history.org.ua, nbuv.gov.ua)
- [ ] Primary source from litopys.org.ua or similar
- [ ] Different interpretations (Ukrainian vs Russian vs Western)

IF missing sources → WebSearch again or mark [NEEDS VERIFICATION]
```

---

## PHASE 2: WRITE CONTENT

### Step 2.1: Create Files

```
CREATE 3 files:
1. curriculum/l2-uk-en/c1-hist/{slug}.md        # Prose content
2. curriculum/l2-uk-en/c1-hist/vocabulary/{slug}.yaml  # Vocabulary
3. curriculum/l2-uk-en/c1-hist/activities/{slug}.yaml  # Activities
```

### Step 2.2: Write Markdown Content

**Required sections (in order):**

| Section | Words | Content |
|---------|-------|---------|
| `# Title` + `🎯 Чому це важливо?` | 100-150 | Methodological significance |
| `## Методологічний вступ` | 400-500 | Historiographical concept/method |
| `## Аналіз джерела` | 800-1000 | Primary source with glosses, source criticism |
| `## Порівняльна історіографія` | 400-500 | Ukrainian vs Russian vs Western interpretations |
| `## Застосування методу` | 300-400 | Practice applying the method |
| `## Підсумок` | 100-150 | Summary |

**Total target: 3500+ words**

### Step 2.3: Primary Source Format

```markdown
### Джерело: [Source Title]

**Контекст створення:**
[When, where, why — 100-150 words]

**Оригінал (з глосами):**

> [Primary source excerpt — 200-300 words]
>
> *— Джерело: [Full attribution]*

**Глоси:**
| Архаїзм | Сучасне значення |
|---------|------------------|
| [archaic] | [modern] |

### Критика джерела

**Авторство:** [Who wrote it]
**Мета:** [Why written, for whom]
**Упередження:** [Detectable biases]
**Достовірність:** [Reliability assessment]
```

### Step 2.4: Historiographical Comparison

```markdown
## Порівняльна історіографія

### Українська інтерпретація
[Hrushevsky, modern Ukrainian scholars — 150-200 words]

### Російська/імперська інтерпретація
[Russian/imperial framing — 150-200 words]

> ⚠️ **Деколонізація**
> [Why imperial narrative is problematic]

### Західна історіографія
[Western scholars' approach — 100-150 words]

### Синтез
[What we conclude from comparison — 100-150 words]
```

### Step 2.5: Forbidden Patterns

```
DO NOT include:
- ## Vocabulary header (injected from YAML)
- ## Activities header (injected from YAML)
- Factual drills (this is NOT B2-HIST)
- Quiz on dates/events
- Dialogs (historiography is analytical)
```

---

## PHASE 3: WRITE ACTIVITIES YAML

### Step 3.1: Activity Requirements

```yaml
# activities/{slug}.yaml

# REQUIRED (per config.py C1-history):
min_activities: 3
max_activities: 9
required_types:
  - reading        # Primary source analysis
  - essay-response # 250-500 word analytical essay
  - critical-analysis  # Methodology questions
```

### Step 3.2: Reading Activity Template

```yaml
- type: reading
  id: c1-hist-XX-reading-01
  title: "Аналіз первинного джерела"
  resource:
    type: primary_source
    url: "https://litopys.org.ua/..."  # VERIFY URL EXISTS
    title: "[Source Title]"
  tasks:
    - "Визначте регістр та стиль джерела. Наведіть приклади."
    - "Знайдіть три приклади архаїчної лексики."
    - "Які упередження автора можна виявити з тексту?"
```

### Step 3.3: Essay Activity Template

```yaml
- type: essay-response
  id: c1-hist-XX-essay-01
  title: "Історіографічний аналіз"
  prompt: |
    Напишіть порівняльний аналіз (250-500 слів):
    "[Topic]: Українська та російська інтерпретації"

    Вимоги:
    - Використайте академічну лексику модуля
    - Цитуйте первинне джерело
    - Обґрунтуйте, чому одна інтерпретація переконливіша
  rubric:
    - criterion: Академічна мова
      weight: 40
    - criterion: Критика джерел
      weight: 30
    - criterion: Порівняльний аналіз
      weight: 20
    - criterion: Аргументація
      weight: 10
```

### Step 3.4: Critical Analysis Template

```yaml
- type: critical-analysis
  id: c1-hist-XX-analysis-01
  title: "Методологічна рефлексія"
  questions:
    - "Як застосувати цей метод критики джерел до інших періодів?"
    - "Які обмеження має цей тип джерела?"
    - "Як сучасна деколонізація змінює інтерпретацію цього періоду?"
```

---

## PHASE 4: WRITE VOCABULARY YAML

### Step 4.1: Vocabulary Requirements

```yaml
# vocabulary/{slug}.yaml

# Per config.py C1-history:
min_items: 30
format: 3-column (lemma, translation, note)
```

### Step 4.2: Vocabulary Template

```yaml
items:
  - lemma: [Ukrainian word]
    translation: [English]
    note: [historiographical context]
```

**Include categories:**
- Historiographical terms (джерелознавство, верифікація)
- Source criticism vocabulary (достовірність, упередження)
- Academic discourse markers (згідно з, на думку)
- Decolonization terms (русифікація, імперський наратив)

---

## PHASE 5: VALIDATE

### Step 5.1: Pre-Submission Checklist

```
⛔ STOP: Verify ALL before submitting.

CONTENT:
- [ ] 3500+ words (prose only)
- [ ] Primary source with glosses
- [ ] Source criticism (authorship, purpose, bias)
- [ ] Comparative historiography section
- [ ] No factual drills
- [ ] No ## Vocabulary or ## Activities headers

ACTIVITIES (in YAML):
- [ ] 3-9 activities total
- [ ] Includes reading activity
- [ ] Includes essay-response (250-500 words)
- [ ] Includes critical-analysis
- [ ] All URLs verified with WebFetch

VOCABULARY (in YAML):
- [ ] 30+ items
- [ ] 3-column format (lemma, translation, note)

SOURCES:
- [ ] No Wikipedia-only claims
- [ ] Primary sources from litopys.org.ua or similar
- [ ] Historiographical debates verified (not invented)
```

### Step 5.2: Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1-hist/{slug}.md
```

---

## QUICK REFERENCE

### Key Academic Resources

| Resource | URL | Use For |
|----------|-----|---------|
| Litopys.org.ua | litopys.org.ua | Primary sources |
| Institute of History NANU | history.org.ua | Scholarly articles |
| National Library | nbuv.gov.ua | Academic journals |
| Hrushevsky Digital | hrushevsky.nbuv.gov.ua | Foundational historiography |
| ЕСУ | esu.com.ua | Conceptual articles |
| UINP | memory.gov.ua | 20th century, decolonization |

### Anti-Hallucination Rules

| Rule | Action |
|------|--------|
| Never invent debates | Verify which historians actually disagree |
| Never generate sources | Always verify from litopys.org.ua |
| Never attribute views | Check actual arguments first |
| When in doubt | Mark [NEEDS VERIFICATION] |

### C1-HIST vs B2-HIST

| Aspect | B2-HIST | C1-HIST |
|--------|---------|---------|
| Focus | Historical facts | Historiographical analysis |
| Questions | What happened? | How do we know? |
| Sources | Context for narrative | Objects of analysis |
| Activities | Reading + essay | Reading + essay + critical-analysis |

---

**Template version:** 2.0-ai
**Last updated:** 2026-01-24
