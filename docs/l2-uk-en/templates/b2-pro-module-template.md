# B2 Professional Module Template

**Purpose:** Reference template for B2-PRO professional track modules (M01-40: Business Communication, Technical Domains, Media & Public Discourse)

**Based on:** `b2-module-template.md` — inherits all B2 quality standards

**Related Issue:** RFC #409 Curriculum Reorganization

---

## ⚠️ BEFORE WRITING: Research Professional Content First!

**CRITICAL:** Professional content requires authentic terminology and real document formats. Do NOT generate professional vocabulary or document structures from memory.

### Research Strategy

**Step 1: Find Domain-Specific Resources**
```
WebSearch: "[domain] terminology Ukrainian"
WebSearch: "[document type] зразок український"
WebSearch: "діловий лист зразок" OR "службова записка шаблон"
```

**Step 2: Verify Terminology**
```
WebFetch: https://zakon.rada.gov.ua/... (for legal terms)
WebSearch: "[term] визначення українською"
```

### Key Resources by Domain

| Domain | Primary Resources |
|--------|-------------------|
| **Business/General** | zakon.rada.gov.ua, minjust.gov.ua |
| **IT/Technical** | uk.wikipedia.org/wiki/[IT term], dou.ua |
| **Finance** | bank.gov.ua, minfin.gov.ua |
| **Legal** | zakon.rada.gov.ua, minjust.gov.ua |
| **Medical** | moz.gov.ua, umj.com.ua |
| **HR/Recruitment** | dcz.gov.ua, work.ua |
| **Textbooks** | pidruchnyk.com.ua (pre-university level) |

### Official Standards (MUST USE)

| Standard | Purpose | URL |
|----------|---------|-----|
| **ДСТУ 4163:2020** | Document formatting | [undiasd.archives.gov.ua](https://undiasd.archives.gov.ua/doc/DSTU%204163.pdf) |
| **NADS Courses** | Business correspondence | [pdp.nacs.gov.ua](https://pdp.nacs.gov.ua/courses/business-correspondence) |

### Reference Textbooks (Use, Don't Copy!)

| Source | Use For |
|--------|---------|
| Шевчук С.В. "Ділове мовлення: Модульний курс" | Business speech patterns, correspondence |
| "Сучасне діловодство: зразки документів" | Document samples, business etiquette |
| pidruchnyk.com.ua textbooks | Accessible business Ukrainian for B2 level |

**⚠️ ANTI-PLAGIARISM RULES:**
1. **SYNTHESIZE, don't copy** — use textbooks for patterns, write original examples
2. **Cite standards** — reference ДСТУ when discussing document formats
3. **Adapt for language learning** — textbooks teach procedures, we teach language

### Anti-Hallucination Rules

1. **NEVER invent professional terminology** — verify real Ukrainian business terms
2. **NEVER generate document formats from memory** — check ДСТУ 4163:2020
3. **Use official government portals** — zakon.rada.gov.ua has legal document standards
4. **Verify formulas and conventions** — formal Ukrainian varies by domain
5. **When in doubt, mark as [NEEDS VERIFICATION]** — flag for review

> 💡 **Tip:** The [ДСТУ 4163:2020 PDF](https://undiasd.archives.gov.ua/doc/DSTU%204163.pdf) contains official document samples in Appendix B.

---

<!--
TEMPLATE_METADATA:
  required_sections:
  - Вступ|Контекст
  - Професійний контекст
  - Практика
  - Підсумок
  - Потрібно більше практики?
  pedagogy: ESP
  min_word_count: 3000
  required_callouts: []
  description: B2-PRO professional track modules for career-focused Ukrainian
-->

---

## Quick Reference Checklist

Before submitting a B2-PRO professional module, verify all items from `b2-module-template.md` PLUS:

### Professional-Specific Requirements (Seminar Style)
- [ ] **Seminar pedagogy:** Production-focused, not drill-focused
- [ ] **Activities:** 3-9 production activities (reading, essay-response, critical-analysis)
- [ ] **Essay requirements:** 150-300 words per essay (with Model Answer)
- [ ] **Practical focus:** Real-world professional scenarios and documents
- [ ] **Professional immersion:** 100% Ukrainian in professional contexts
- [ ] **Document templates:** At least one professional document format
- [ ] **Domain vocabulary:** 30+ domain-specific terms
- [ ] **Transferable skills:** Focus on skills applicable across professional contexts

---

## Module Types in B2-PRO

### Phase PRO.1: Business Communication (M01-15)

| Modules | Focus | Skills |
|---------|-------|--------|
| M01-03 | Business Correspondence | Emails, formal letters, proposals |
| M04-07 | Reports & Meetings | Report writing, meeting participation |
| M08-09 | Presentations | Structure, delivery, Q&A |
| M10-12 | Negotiations & Networking | Negotiation tactics, relationship building |
| M13-15 | Checkpoints & Integration | Assessment and combined practice |

### Phase PRO.2: Technical & Domain-Specific (M16-30)

| Modules | Focus | Skills |
|---------|-------|--------|
| M16-18 | IT Vocabulary & Documentation | Hardware, software, technical docs |
| M19-20 | Finance | Banking, financial reporting |
| M21-22 | Legal | Contracts, legal terminology |
| M23-24 | Medical | Healthcare vocabulary, consultations |
| M25-27 | HR & Scientific | Recruitment, research writing |
| M28-30 | Checkpoints & Integration | Assessment and combined practice |

### Phase PRO.3: Media & Public Discourse (M31-40)

| Modules | Focus | Skills |
|---------|-------|--------|
| M31-32 | News Analysis | Critical reading, source evaluation |
| M33 | Journalism Writing | Article structure, headlines |
| M34-35 | Public Speaking | Speech structure, persuasion |
| M36-37 | Debate & Interview | Formal debate, interview skills |
| M38-40 | Checkpoints & Capstone | Final assessment |

---

## Naturalness Quality Checklist

**Run this check during Stage 4 (Review & Fix) on prose activities.**

Before finalizing the module, verify prose activities (cloze, fill-in, unjumble with 5+ sentences) achieve:

- [ ] **Subject consistency** - Clear subjects maintained throughout passages
- [ ] **Discourse markers** - At least 2-3 connectors per 10-sentence passage (а, але, потім, тому, також, спочатку, нарешті)
- [ ] **Topic coherence** - All sentences contribute to unified narrative/theme, no random topic jumps
- [ ] **No template repetition** - Varied sentence structures across activities within the module
- [ ] **Moderate intensifiers** - Maximum 2-3 "дуже" per module, 0-1 "надзвичайно/справжній"
- [ ] **No double superlatives** - Use one precise descriptor instead of redundant pairs
- [ ] **Natural transitions** - Avoid robotic "і це", "тому що... тому" patterns

**Target score:** 8/10 for content modules, 7/10 for checkpoints

---

## Module Structure (Professional-Specific)

### 1. Frontmatter

```yaml
---
module: b2-pro-XX
title: "[Professional Topic]: Ukrainian Title"
phase: "B2-PRO.X"
pedagogy: "ESP"
register: "офіційно-діловий"
tags:
  - professional
  - [business, technical, media]
  - [domain if applicable]
grammar:
  - "Professional vocabulary"
  - "Formal register markers"
vocabulary_focus:
  - "Domain-specific terminology"
  - "Formal correspondence"
---
```

### 2. Professional Content Structure

#### Section 1: Professional Context — 400-500 words

```markdown
# [Topic]: Професійний контекст

> 🎯 **Чому це важливо?**
>
> [Explain practical career value]
> [How this skill applies in Ukrainian workplaces]
> [Why B2 learners need this for professional success]

## Основи

### Ключові поняття

[Introduction to professional domain — 200-300 words]

**Практичне застосування:**

| Ситуація | Приклад |
|----------|---------|
| [Context 1] | [Example] |
| [Context 2] | [Example] |
| [Context 3] | [Example] |

> 💼 **Професійна порада**
>
> [Practical workplace advice]
```

#### Section 2: Domain Vocabulary — 400-500 words

```markdown
## Фахова лексика

### Ключові терміни

| Термін | Переклад | Приклад вживання |
|--------|----------|------------------|
| [term] | [translation] | [example sentence] |
| [term] | [translation] | [example sentence] |
| [term] | [translation] | [example sentence] |

### Формальний регістр

**Маркери офіційно-ділового стилю:**

1. **Звертання:** Шановний/Шановна, Вельмишановний
2. **Завершення:** З повагою, З найкращими побажаннями
3. **Прохання:** Просимо, Будь ласка, розгляньте
4. **Підтвердження:** Підтверджуємо, Повідомляємо

> 📝 **Регістрова точність**
>
> [Formal vs. informal professional language guidance]
```

#### Section 3: Professional Document/Scenario — 800-1000 words

```markdown
## Практичний приклад

### Зразок документа / Сценарій

**Тип:** [Document type / Scenario type]
**Контекст:** [Professional situation]

---

> [Complete 400-500 word professional document or dialogue:
> - Correct structure and format
> - Appropriate register
> - Professional conventions
> - Authentic language patterns]

---

### Аналіз структури

| Компонент | Приклад | Функція |
|-----------|---------|---------|
| [Element] | [Example] | [Purpose] |
| [Element] | [Example] | [Purpose] |

### Шаблон

```
[Blank template with placeholders]
```

> 💡 **Порада**
>
> [Tips for successful document/communication]
```

#### Section 4: Application & Practice — 400-500 words

```markdown
## Завдання

### Практичне завдання

**Ситуація:**
[Professional scenario — 100-150 words]

**Вимоги:**
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

**Зразок відповіді:**

> [Complete model answer — 200+ words]

**Коментар:**
> [Explanation of key elements and conventions]
```

---

## Activity Format Quick Reference

**CRITICAL:** Activities must be defined in `activities/{slug}.yaml`. Do NOT embed activities in Markdown.

See [ACTIVITY-YAML-REFERENCE.md](../../ACTIVITY-YAML-REFERENCE.md) for schemas and examples.

**Example `activities/b2-pro-01-business-email.yaml`:**

```yaml
- type: fill-in
  title: Ділове листування
  instruction: Виберіть правильний вираз для формального листа.
  items:
    - sentence: "[___], пане директоре, звертаємось до Вас з пропозицією."
      answer: Шановний
      options:
        - Шановний
        - Дорогий
        - Любий
```

---

## Engagement Boxes for Professional Modules

```markdown
> 💼 **Професійна порада**
>
> [Practical workplace advice]

> 📝 **Регістрова точність**
>
> [Formal register guidance]

> 🤝 **Культура спілкування**
>
> [Ukrainian professional communication norms]

> 📋 **Шаблон**
>
> [Document template for reference]

> 💡 **Практичний приклад**
>
> [Real-world application example]

> ⚠️ **Типові помилки**
>
> [Common mistakes to avoid]
```

---

## Content Structure Note

### Vocabulary & Activities
**CRITICAL:** Do NOT add `## Vocabulary` or `## Activities` headers. These sections are injected automatically from:
- `vocabulary/{slug}.yaml`
- `activities/{slug}.yaml`

The build system will inject these sections at build time.

---

## Key Principle: Practical Professional Skills

### What B2-PRO Teaches

✅ **Correct approach:**
- Real workplace scenarios
- Authentic document formats
- Practical vocabulary for immediate use
- Transferable professional communication skills

❌ **Incorrect approach:**
- Overly academic or theoretical content
- Vocabulary without practical context
- Generic exercises without professional scenarios

### Rationale

B2-PRO prepares learners for actual Ukrainian workplaces. Every module should answer: "How will this help me in my career?" Content should be immediately applicable to business emails, reports, presentations, and professional interactions.

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/b2-module-template.md`
- **B2-PRO Curriculum Plan:** `docs/l2-uk-en/B2-PRO-CURRICULUM-PLAN.md`
- **Quick Reference:** `claude_extensions/quick-ref/b2-pro.md`
- **Activity Reference:** `docs/ACTIVITY-YAML-REFERENCE.md`

---

**Last Updated:** 2026-01-17
**Template Version:** 1.0
