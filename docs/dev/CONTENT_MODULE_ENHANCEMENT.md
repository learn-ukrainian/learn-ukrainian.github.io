# Content Module Enhancement Strategy

**Date:** 2026-01-03
**Scope:** B2 History, C1 Literature, C1 Biography, C1 Folk Culture, C1 Fine Arts
**Goal:** Enhance reading/writing components while maintaining language-first pedagogy

---

## Core Principle (CRITICAL)

<critical>

**These are LANGUAGE lessons that use content as context, NOT content lessons taught in Ukrainian.**

### The Golden Rule

**✅ GOOD:** "Згідно з текстом, як автор описує роль Січі?"
→ Tests reading comprehension of Ukrainian
→ Answer requires understanding the Ukrainian text

**❌ BAD:** "У якому році заснована Запорозька Січ?"
→ Tests historical knowledge
→ Can be answered from memory without reading Ukrainian

### Test for Every Activity

**"Can the learner answer this without reading the Ukrainian text?"**

- **If YES** → Rewrite (it's testing content recall, not language)
- **If NO** → Keep (it's testing Ukrainian comprehension)

</critical>

---

## What We're Borrowing from LIT

### 1. Reading Tasks (External Assignments)

**Add 2-3 `type: reading` activities per content module:**

```yaml
- type: reading
  id: b2-75-reading-01
  title: "Аналіз первинного джерела"
  resource:
    type: primary_source
    url: "https://..."
    title: "Універсал Богдана Хмельницького"
  tasks:
    - "Знайдіть у тексті три приклади офіційного регістру"
    - "Які дієслова використовує автор для опису своїх дій?"
    - "Порівняйте синтаксис цього документа із сучасною публіцистикою"
```

**Key:** Questions test LINGUISTIC analysis, not historical interpretation.

### 2. Enhanced Writing Tasks

**Standardize essay components:**

| Module Type | Essay Requirement |
|-------------|-------------------|
| B2 History | 400+ words: Деколонізаційний аналіз (linguistic + historical perspective) |
| C1 Literature | 400+ words: Літературознавчий аналіз (stylistic analysis) |
| C1 Biography | 400+ words: Порівняльний есе (comparative analysis) |
| C1 Folk/Arts | 400+ words: Культурний аналіз (cultural significance) |

**All include:**
- Model answer demonstrating C1/B2 language use
- Clear rubric focusing on LANGUAGE quality, not content accuracy

### 3. Primary Source Focus

**Make primary source analysis more systematic:**

- Dedicated section in module (already exists)
- **Linguistic analysis questions** (not content interpretation)
- Questions focus on: register, vocabulary, syntax, style

**Example (GOOD):**
> **Аналіз джерела:**
> - Який регістр використовує автор? Наведіть приклади.
> - Знайдіть три приклади пасивного стану. Чому автор їх використовує?
> - Порівняйте лексику цього тексту з лексикою модуля. Які слова застаріли?

**Example (BAD):**
> - Що автор думає про Московське царство? ← Tests interpretation
> - Чому Хмельницький прийняв це рішення? ← Tests historical knowledge

---

## What We're KEEPING (Language Practice)

### Standard Activities Remain Essential

**B2/C1 core modules are still LANGUAGE LEARNING.**

Learners need to practice:
- Reading comprehension of complex Ukrainian
- Vocabulary in authentic contexts
- Grammar in historical/literary registers
- Collocations and fixed expressions

**Activity count:** 10-12 (down from 14+, but NOT eliminated)

### Refined Activity Mix

| Activity Type | Count | Purpose | Example (History) |
|---------------|-------|---------|-------------------|
| **quiz** | 4-5 | Reading comprehension | "Згідно з текстом, як автор характеризує роль козацтва?" |
| **fill-in / cloze** | 3-4 | Vocabulary in context | "Козаки [___] спротив польському пануванню" → чинили |
| **error-correction** | 2-3 | Grammar practice | Fix case errors in historical sentences |
| **match-up** | 1-2 | Terminology | Ukrainian term ↔ Ukrainian definition |
| **select / mark-the-words** | 1-2 | Analytical | Find passive voice in primary source |

**Total:** 10-12 activities

---

## Examples: GOOD vs BAD Activities

### B2 History Module

#### ❌ BAD (Tests Historical Knowledge)

```markdown
## quiz: Історія козацтва

1. У якому році заснована Запорозька Січ?
   - [ ] 1550
   - [x] 1552
   - [ ] 1560
   - [ ] 1570

2. Хто був першим гетьманом?
   - [x] Дмитро Вишневецький
   - [ ] Богдан Хмельницький
   - [ ] Петро Сагайдачний
   - [ ] Іван Мазепа
```

**Problem:** Tests date/name recall. Can be answered without reading Ukrainian text.

#### ✅ GOOD (Tests Ukrainian Language)

```markdown
## quiz: Розуміння тексту

> **Інструкція:** Відповідайте на питання на основі прочитаного тексту модуля.

1. Згідно з текстом, як автор пояснює причини виникнення козацтва?
   - [ ] Автор зазначає лише економічні фактори
   - [x] Автор виділяє поєднання соціальних, економічних та військових факторів
   - [ ] Автор пише, що козацтво виникло випадково
   - [ ] Автор не пояснює причин
   > У тексті автор детально аналізує múльтіфакторну природу козацтва.

2. Яку функцію Січі автор підкреслює в тексті?
   - [ ] Виключно військову
   - [ ] Тільки економічну
   - [x] Політичну, військову та культурну разом
   - [ ] Релігійну
   > Текст описує Січ як "осередок козацької демократії" з múльтіплікатівними функціями.
```

**Why GOOD:**
- Requires reading the Ukrainian module text
- Tests comprehension of Ukrainian explanations
- Answer depends on HOW author describes, not WHAT happened

### C1 Literature Module

#### ❌ BAD (Tests Literary Facts)

```markdown
## quiz: Шевченко

1. У якому році написаний "Заповіт"?
   - [ ] 1843
   - [x] 1845
   - [ ] 1847
   - [ ] 1850

2. Що символізує образ Дніпра в поезії Шевченка?
   - [ ] Природу
   - [x] Волю України
   - [ ] Смуток
   - [ ] Кохання
```

**Problem:** Tests literary knowledge. Students can answer from prior knowledge.

#### ✅ GOOD (Tests Ukrainian Language)

```markdown
## quiz: Аналіз тексту модуля

> **Інструкція:** Відповідайте на питання на основі літературознавчого аналізу в модулі.

1. Згідно з аналізом у модулі, який стилістичний засіб автор виділяє в рядку "Реве та стогне Дніпр широкий"?
   - [ ] Автор класифікує це як метафору
   - [x] Автор визначає це як персоніфікацію
   - [ ] Автор називає це гіперболою
   - [ ] Автор не аналізує цей рядок
   > У тексті модуля чітко зазначено: "Дніпр наділяється людськими якостями."

2. Як у тексті модуля інтерпретується образ каменярів у Франка?
   - [ ] Текст описує буквальних будівельників
   - [x] Автор тлумачить каменярів як символ інтелектуальної праці
   - [ ] Автор не згадує цей образ
   - [ ] Текст дає суперечливі тлумачення
   > У розділі аналізу автор формулює: "Каменярі — це метафора…"
```

**Why GOOD:**
- Tests reading comprehension of the MODULE'S ANALYSIS
- Requires understanding Ukrainian literary terminology
- Answer is in the Ukrainian text students read

### C1 Biography Module

#### ❌ BAD (Tests Biographical Facts)

```markdown
## fill-in: Життя Шевченка

1. Шевченко народився в [___] році.
   > [!answer] 1814
   > [!options] 1812 | 1814 | 1816 | 1818

2. Його викупили з кріпацтва у [___] році.
   > [!answer] 1838
   > [!options] 1835 | 1838 | 1840 | 1842
```

**Problem:** Tests dates. No language learning.

#### ✅ GOOD (Tests Ukrainian Collocations)

```markdown
## fill-in: Біографічна лексика в контексті

1. Згідно з текстом, Шевченко [___] визначну роль у розвитку української літератури.
   > [!answer] відіграв
   > [!options] відіграв | зробив | мав | дав
   > Fixed collocation: відіграти роль = to play a role.

2. Його творча [___] охоплює понад 20 років.
   > [!answer] спадщина
   > [!options] спадщина | робота | діяльність | праця
   > Спадщина = legacy (used for cultural/intellectual inheritance).

3. Він [___] участь у національно-визвольному русі.
   > [!answer] брав
   > [!options] брав | робив | мав | давав
   > Fixed expression: брати участь = to participate.
```

**Why GOOD:**
- Tests Ukrainian collocations (відіграти роль, творча спадщина, брати участь)
- Requires understanding how these expressions work in Ukrainian
- Language-focused, not fact-focused

---

## Implementation Checklist

### For Each Content-Heavy Module Template:

- [ ] **Add "Reading Tasks" section** with 2-3 external reading assignments
- [ ] **Enhance essay requirements** (400+ words, model answer, rubric)
- [ ] **Strengthen "CRITICAL" warning** about language vs. content testing
- [ ] **Reduce activity count** from 14+ to 10-12
- [ ] **Add more "Згідно з текстом" examples** in quiz activities
- [ ] **Emphasize linguistic analysis** in primary source sections
- [ ] **Add bad vs. good activity examples** for clarity

### Templates to Update:

1. `b2-history-module-template.md`
2. `c1-literature-module-template.md`
3. `c1-biography-module-template.md`
4. `c1-folk-culture-module-template.md`
5. `c1-fine-arts-module-template.md`

---

## Key Phrases for Activities

### Reading Comprehension (quiz, select)

**Always start with:**
- "Згідно з текстом…"
- "У тексті модуля автор…"
- "Як автор описує/характеризує/пояснює…"
- "Який аргумент автор наводить…"

**Never ask:**
- "У якому році…"
- "Хто був…"
- "Що символізує…" (unless asking "як автор інтерпретує символіку")
- "Чому [historical figure] прийняв це рішення…"

### Vocabulary (fill-in, cloze)

**Focus on:**
- Collocations (відіграти роль, чинити спротив, брати участь)
- Register-appropriate vocabulary
- Fixed expressions from module vocabulary
- Words used in specific Ukrainian contexts

**Avoid:**
- Simple translation exercises
- Vocabulary not in module text
- Trivial gaps (articles, obvious words)

### Grammar (error-correction)

**Test:**
- Case agreement in historical/literary sentences
- Aspect choice in narrative contexts
- Passive voice in formal registers
- Complex sentence structures

**Don't test:**
- Factual accuracy ("Шевченко народився в Києві" → wrong city, but tests history)
- Content correctness (focus on grammar only)

---

## Success Metrics

**After implementation, modules should:**

✅ Use content to create authentic Ukrainian reading contexts
✅ Test learners' Ukrainian language skills comprehensively
✅ Provide reading/writing tasks like LIT track
✅ Include 10-12 language-focused activities

❌ NOT test historical/literary/cultural knowledge recall
❌ NOT require memorizing dates, names, or facts
❌ NOT turn into content exams taught in Ukrainian

---

## Related Documentation

- **LIT Migration Strategy:** `docs/dev/LIT_MIGRATION_STRATEGY.md`
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`
- **Module Richness Guidelines:** `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

---

**Last Updated:** 2026-01-03
**Status:** Proposal (awaiting implementation)
