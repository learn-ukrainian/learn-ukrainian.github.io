# B2-PRO Module Template (AI-Optimized)

> **Full documentation:** `docs/l2-uk-en/templates/b2-pro-module-template.md`
> **Config source of truth:** `scripts/audit/config.py` → `B2-professional`

---

## PHASE 1: BEFORE WRITING

### Step 1.1: Identify Module Phase

```
IF module in M01-15 → Phase PRO.1: Business Communication
IF module in M16-30 → Phase PRO.2: Technical & Domain-Specific
IF module in M31-40 → Phase PRO.3: Media & Public Discourse

Checkpoints: M13-15, M28-30, M38-40
```

### Step 1.2: Research Professional Content

```
⛔ STOP: Do NOT generate professional terminology from memory.

DO:
1. WebSearch: "[domain] terminology Ukrainian"
2. WebSearch: "[document type] зразок український"
3. WebSearch: "діловий лист зразок" OR "службова записка шаблон"
4. WebFetch: https://undiasd.archives.gov.ua/doc/DSTU%204163.pdf

DO NOT:
- Invent professional terminology
- Generate document formats from memory
- Use informal register in professional contexts
```

### Step 1.3: Verify Standards

```
⛔ STOP: Professional documents must follow ДСТУ 4163:2020.

REQUIRED verification:
- [ ] Document format matches ДСТУ 4163:2020
- [ ] Formal register markers verified
- [ ] Domain-specific terminology checked against official sources
```

---

## PHASE 2: WRITE CONTENT

### Step 2.1: Create Files

```
CREATE 3 files:
1. curriculum/l2-uk-en/b2-pro/{slug}.md        # Prose content
2. curriculum/l2-uk-en/b2-pro/vocabulary/{slug}.yaml  # Vocabulary
3. curriculum/l2-uk-en/b2-pro/activities/{slug}.yaml  # Activities
```

### Step 2.2: Write Markdown Content

**Required sections (in order):**

| Section | Words | Content |
|---------|-------|---------|
| `# Title` + `🎯 Чому це важливо?` | 100-150 | Practical career value |
| `## Основи` | 200-300 | Key concepts introduction |
| `## Фахова лексика` | 400-500 | Domain vocabulary with examples |
| `## Практичний приклад` | 800-1000 | Complete professional document/scenario |
| `## Завдання` | 400-500 | Practical task with model answer |
| `## Підсумок` | 100-150 | Summary |

**Total target: 3000+ words**

### Step 2.3: Professional Document Format

```markdown
## Практичний приклад

### Зразок документа

**Тип:** [Document type]
**Контекст:** [Professional situation]

---

> [Complete 400-500 word professional document:
> - Correct ДСТУ 4163:2020 structure
> - Appropriate formal register
> - Professional conventions]

---

### Аналіз структури

| Компонент | Приклад | Функція |
|-----------|---------|---------|
| Звертання | Шановний... | Офіційний тон |
| Вступ | Звертаємось... | Мета листа |
| Основна частина | ... | Деталі |
| Завершення | З повагою | Ввічливість |
```

### Step 2.4: Formal Register Markers

```markdown
### Формальний регістр

**Маркери офіційно-ділового стилю:**

1. **Звертання:** Шановний/Шановна, Вельмишановний
2. **Завершення:** З повагою, З найкращими побажаннями
3. **Прохання:** Просимо, Будь ласка, розгляньте
4. **Підтвердження:** Підтверджуємо, Повідомляємо
```

### Step 2.5: Forbidden Patterns

```
DO NOT include:
- ## Vocabulary header (injected from YAML)
- ## Activities header (injected from YAML)
- Informal register in document samples
- Generic exercises without professional context
- Overly academic/theoretical content
```

---

## PHASE 3: WRITE ACTIVITIES YAML

### Step 3.1: Activity Requirements

```yaml
# activities/{slug}.yaml

# REQUIRED (per config.py B2-professional):
min_activities: 3
max_activities: 9
required_types:
  - reading        # Professional document analysis
  - essay-response # 150-300 word professional writing
```

### Step 3.2: Reading Activity Template

```yaml
- type: reading
  id: b2-pro-XX-reading-01
  title: "Аналіз ділового документа"
  resource:
    type: professional_document
    url: "https://..."  # VERIFY URL EXISTS
    title: "[Document Title]"
  tasks:
    - "Визначте структурні компоненти документа."
    - "Які формальні маркери використано?"
    - "Як би ви адаптували цей документ для іншої ситуації?"
```

### Step 3.3: Essay Activity Template

```yaml
- type: essay-response
  id: b2-pro-XX-essay-01
  title: "Складання [Document Type]"
  prompt: |
    Напишіть [document type] (150-300 слів):
    "[Professional scenario]"

    Вимоги:
    - Використайте офіційно-діловий стиль
    - Дотримуйтесь структури ДСТУ 4163:2020
    - Застосуйте лексику модуля
  rubric:
    - criterion: Регістрова точність
      weight: 40
    - criterion: Структура документа
      weight: 30
    - criterion: Професійна лексика
      weight: 20
    - criterion: Практичність
      weight: 10
```

---

## PHASE 4: WRITE VOCABULARY YAML

### Step 4.1: Vocabulary Requirements

```yaml
# vocabulary/{slug}.yaml

# Per config.py B2-professional:
min_items: 30
format: 3-column (lemma, translation, note)
```

### Step 4.2: Vocabulary Template

```yaml
items:
  - lemma: [Ukrainian term]
    translation: [English]
    note: [professional context/collocation]
```

**Include categories by phase:**

PRO.1 (Business):
- Correspondence terms (лист, звернення, пропозиція)
- Meeting vocabulary (порядок денний, протокол)
- Formal markers (шановний, з повагою)

PRO.2 (Technical):
- IT terms (програмне забезпечення, налаштування)
- Finance terms (баланс, звітність)
- Legal terms (договір, сторона)
- Medical terms (діагноз, лікування)

PRO.3 (Media):
- Journalism terms (стаття, заголовок)
- Public speaking (промова, аргумент)
- Debate terms (теза, контраргумент)

---

## PHASE 5: VALIDATE

### Step 5.1: Pre-Submission Checklist

```
⛔ STOP: Verify ALL before submitting.

CONTENT:
- [ ] 3000+ words (prose only)
- [ ] Complete professional document sample
- [ ] ДСТУ 4163:2020 compliant structure
- [ ] Formal register throughout
- [ ] Practical real-world scenarios
- [ ] No ## Vocabulary or ## Activities headers

ACTIVITIES (in YAML):
- [ ] 3-9 activities total
- [ ] Includes reading activity
- [ ] Includes essay-response (150-300 words)
- [ ] All tasks focus on professional skills

VOCABULARY (in YAML):
- [ ] 30+ items
- [ ] 3-column format (lemma, translation, note)
- [ ] Domain-specific terminology

SOURCES:
- [ ] Document formats verified against ДСТУ 4163:2020
- [ ] Terminology checked against official sources
```

### Step 5.2: Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2-pro/{slug}.md
```

---

## QUICK REFERENCE

### Key Resources by Domain

| Domain | Primary Resources |
|--------|-------------------|
| **Business/General** | zakon.rada.gov.ua, minjust.gov.ua |
| **IT/Technical** | dou.ua |
| **Finance** | bank.gov.ua, minfin.gov.ua |
| **Legal** | zakon.rada.gov.ua, minjust.gov.ua |
| **Medical** | moz.gov.ua, umj.com.ua |
| **HR/Recruitment** | dcz.gov.ua, work.ua |
| **Textbooks** | pidruchnyk.com.ua |

### Official Standards

| Standard | Purpose | URL |
|----------|---------|-----|
| **ДСТУ 4163:2020** | Document formatting | undiasd.archives.gov.ua |
| **NADS Courses** | Business correspondence | pdp.nacs.gov.ua |

### Phase Overview

| Phase | Modules | Focus |
|-------|---------|-------|
| PRO.1 | M01-15 | Business Communication |
| PRO.2 | M16-30 | Technical & Domain-Specific |
| PRO.3 | M31-40 | Media & Public Discourse |

---

**Template version:** 2.0-ai
**Last updated:** 2026-01-24
