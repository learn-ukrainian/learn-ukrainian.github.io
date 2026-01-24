# C1-PRO Module Template (AI-Optimized)

> **Full documentation:** `docs/l2-uk-en/templates/c1-pro-module-template.md`
> **Config source of truth:** `scripts/audit/config.py` → `C1-professional`

---

## PHASE 1: BEFORE WRITING

### Step 1.1: Identify Module Phase

```
IF module in M01-15 → Phase PRO.1: Executive Communication
IF module in M16-30 → Phase PRO.2: Academic Publishing
IF module in M31-45 → Phase PRO.3: Industry Specialization
IF module in M46-50 → Phase PRO.4: Mastery & Capstone

Checkpoints: M13-15, M28-30, M44-45, M49-50
```

### Step 1.2: Research Executive/Academic Content

```
⛔ STOP: C1-PRO requires sophisticated professional Ukrainian.
Do NOT generate executive or academic content from memory.

FOR Executive (PRO.1):
1. WebSearch: "[topic] корпоративний звіт зразок"
2. WebSearch: "[topic] стратегічний план приклад"
3. WebFetch: https://kse.ua/... (Kyiv School of Economics)

FOR Academic (PRO.2):
1. WebSearch: "наукова стаття структура ІМРАД українською"
2. WebSearch: "автореферат дисертації зразок"
3. WebFetch: http://nbuv.gov.ua/... (National Library)
```

### Step 1.3: Verify Standards

```
⛔ STOP: Verify against official standards.

REQUIRED verification:
- [ ] ДСТУ 4163:2020 for document formatting
- [ ] ДСТУ 8302:2015 for bibliographic citations (academic)
- [ ] ВАК requirements for academic article structure (PRO.2)
```

---

## PHASE 2: WRITE CONTENT

### Step 2.1: Create Files

```
CREATE 3 files:
1. curriculum/l2-uk-en/c1-pro/{slug}.md        # Prose content
2. curriculum/l2-uk-en/c1-pro/vocabulary/{slug}.yaml  # Vocabulary
3. curriculum/l2-uk-en/c1-pro/activities/{slug}.yaml  # Activities
```

### Step 2.2: Write Markdown Content

**Required sections (in order):**

| Section | Words | Content |
|---------|-------|---------|
| `# Title` + `🎯 Чому це критично важливо?` | 100-150 | Strategic importance |
| `## Концептуальна база` | 500-600 | Theoretical framework |
| `## Поглиблений аналіз` | 600-700 | Case study or document analysis |
| `## Професійне виробництво` | 700-800 | Complex production task with model |
| `## Інтеграція та рефлексія` | 400-500 | Transferable skills, self-assessment |
| `## Підсумок` | 100-150 | Summary |

**Total target: 3000+ words**

### Step 2.3: Case Study Format

```markdown
## Поглиблений аналіз

### Кейс-стаді

**Контекст:**
[High-stakes professional scenario — 100-150 words]

**Матеріал для аналізу:**

> [Complete 400-500 word authentic document:
> - Executive-level complexity
> - Strategic decision-making context
> - Nuanced language patterns
> - Cultural and professional subtleties]

---

### Аналітичні питання

1. **Стратегічний аналіз:** [Strategic implications]
2. **Мовний аналіз:** [Language choices and register]
3. **Культурний контекст:** [Cultural/professional norms]

### Коментар експерта

> [200-word expert analysis of the case]
```

### Step 2.4: Academic Writing Structure (PRO.2)

```markdown
### Структура наукової статті (ВАК)

1. **Постановка проблеми** — problem statement
2. **Аналіз досліджень** — literature review
3. **Мета статті** — article objectives
4. **Виклад матеріалу** — main content
5. **Висновки** — conclusions

**Анотація:**
- Українська: 800-900 знаків
- Англійська: 1800+ знаків (розширена)
- 6-8 ключових слів обома мовами
```

### Step 2.5: Forbidden Patterns

```
DO NOT include:
- ## Vocabulary header (injected from YAML)
- ## Activities header (injected from YAML)
- B2-level scenarios at C1 complexity
- Basic professional vocabulary lists
- Simple document templates
- Ignoring cultural and strategic dimensions
```

---

## PHASE 3: WRITE ACTIVITIES YAML

### Step 3.1: Activity Requirements

```yaml
# activities/{slug}.yaml

# REQUIRED (per config.py C1-professional):
min_activities: 3
max_activities: 9
required_types:
  - reading        # Executive document analysis
  - essay-response # 250-400 word strategic writing
  - critical-analysis  # Deep strategic questions
```

### Step 3.2: Reading Activity Template

```yaml
- type: reading
  id: c1-pro-XX-reading-01
  title: "Аналіз виконавчого документа"
  resource:
    type: executive_document
    url: "https://..."  # VERIFY URL EXISTS
    title: "[Document Title]"
  tasks:
    - "Визначте стратегічні цілі документа."
    - "Які нюанси регістру використано для різних стейкхолдерів?"
    - "Як культурний контекст впливає на структуру?"
```

### Step 3.3: Essay Activity Template

```yaml
- type: essay-response
  id: c1-pro-XX-essay-01
  title: "[Strategic Communication Type]"
  prompt: |
    Напишіть [document type] (250-400 слів):
    "[Complex professional scenario with multiple stakeholders]"

    Стратегічний контекст:
    - [Stakeholder 1]: [Interests]
    - [Stakeholder 2]: [Interests]
    - [Key constraint or opportunity]

    Вимоги:
    - Демонструйте стратегічну глибину
    - Використайте бездоганний формальний стиль
    - Враховуйте українські професійні норми
  rubric:
    - criterion: Стратегічна глибина
      weight: 30
    - criterion: Регістрова досконалість
      weight: 30
    - criterion: Переконливість
      weight: 25
    - criterion: Культурна компетентність
      weight: 15
```

### Step 3.4: Critical Analysis Template

```yaml
- type: critical-analysis
  id: c1-pro-XX-analysis-01
  title: "Стратегічна рефлексія"
  questions:
    - "Як ці навички застосовуються в різних контекстах?"
    - "Які критичні помилки можуть підірвати комунікацію на цьому рівні?"
    - "Як адаптувати підхід для міжнародного контексту?"
```

---

## PHASE 4: WRITE VOCABULARY YAML

### Step 4.1: Vocabulary Requirements

```yaml
# vocabulary/{slug}.yaml

# Per config.py C1-professional:
min_items: 35
format: 3-column (lemma, translation, note)
```

### Step 4.2: Vocabulary Template

```yaml
items:
  - lemma: [Ukrainian term]
    translation: [English]
    note: [strategic context/collocation]
```

**Include categories by phase:**

PRO.1 (Executive):
- Strategic vocabulary (стратегія, візія, місія)
- Stakeholder terms (стейкхолдер, партнер)
- Crisis communication (криза, управління ризиками)

PRO.2 (Academic):
- Research terms (методологія, гіпотеза)
- Citation vocabulary (посилання, джерело)
- Publication terms (рецензія, редколегія)

PRO.3 (Industry):
- Domain-specific advanced terms
- Cross-cultural terms (міжкультурний, локалізація)

---

## PHASE 5: VALIDATE

### Step 5.1: Pre-Submission Checklist

```
⛔ STOP: Verify ALL before submitting.

CONTENT:
- [ ] 3000+ words (prose only)
- [ ] Executive-level complexity
- [ ] Strategic thinking embedded in content
- [ ] Nuanced register control
- [ ] Cross-cultural professional competence
- [ ] No ## Vocabulary or ## Activities headers

ACTIVITIES (in YAML):
- [ ] 3-9 activities total
- [ ] Includes reading activity
- [ ] Includes essay-response (250-400 words)
- [ ] Includes critical-analysis
- [ ] All tasks test mastery-level skills

VOCABULARY (in YAML):
- [ ] 35+ items
- [ ] 3-column format (lemma, translation, note)
- [ ] Advanced domain-specific terminology

QUALITY CHECK:
- [ ] Would a Ukrainian executive find this authentic?
- [ ] Appropriate complexity for C1 mastery?
```

### Step 5.2: Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1-pro/{slug}.md
```

---

## QUICK REFERENCE

### Key Resources by Phase

| Phase | Resources |
|-------|-----------|
| **PRO.1 Executive** | kse.ua, cases.media, forbes.ua |
| **PRO.2 Academic** | nbuv.gov.ua, nas.gov.ua, ukrmova.com |
| **PRO.3 Industry** | Domain-specific (see B2-PRO resources) |

### Official Standards

| Standard | Purpose |
|----------|---------|
| **ДСТУ 4163:2020** | Document formatting |
| **ДСТУ 8302:2015** | Bibliographic citations |
| **ВАК вимоги** | Academic article structure |

### Phase Overview

| Phase | Modules | Focus |
|-------|---------|-------|
| PRO.1 | M01-15 | Executive Communication |
| PRO.2 | M16-30 | Academic Publishing |
| PRO.3 | M31-45 | Industry Specialization |
| PRO.4 | M46-50 | Mastery & Capstone |

### B2-PRO vs C1-PRO

| Aspect | B2-PRO | C1-PRO |
|--------|--------|--------|
| Level | Practical professional | Executive/expert |
| Complexity | Standard documents | Strategic documents |
| Register | Formal | Nuanced formal |
| Scenarios | Common workplace | High-stakes, multi-stakeholder |

---

**Template version:** 2.0-ai
**Last updated:** 2026-01-24
