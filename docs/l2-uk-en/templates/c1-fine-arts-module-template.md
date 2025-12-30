# C1 Fine Arts Module Template

**Purpose:** Reference template for C1 fine arts modules covering Classical Music, Opera, Visual Arts, Ballet, Theater, and Architecture

**Based on:** `c1-module-template.md` — inherits all C1 quality standards

**Related Issue:** [#306](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/306)

**Proposed Modules:** See `C1-REVIEW-PROPOSAL.md` for the comprehensive arts expansion plan

---

## Quick Reference Checklist

Before submitting a C1 fine arts module, verify all items from `c1-module-template.md` PLUS:

### Fine Arts-Specific Requirements
- [ ] **CBI pedagogy:** Content-Based Instruction (arts content drives language learning)
- [ ] **Authentic materials:** Excerpts from reviews, librettos, exhibition catalogs, program notes
- [ ] **Art-specific terminology:** музичний термін, сценічна мова, мистецтвознавство
- [ ] **Historical context:** European context AND Ukrainian national significance
- [ ] **Ukrainian contribution:** Emphasize Ukrainian artists' role in world culture
- [ ] **Register:** Mix of науковий (academic) and публіцистичний (arts journalism)
- [ ] **Modern relevance:** Contemporary Ukrainian artists continuing traditions

---

## Module Types

### Classical Music (3 modules)

| Module | Focus | Key Figures & Works |
|--------|-------|---------------------|
| M141 | Baroque & Early Classical | Бортнянський, Березовський, Ведель |
| M142 | National School (19th-early 20th c.) | Лисенко, Леонтович, Стеценко, Левіцький |
| M143 | Modern Ukrainian Classical | Лятошинський, Сильвестров, Скорик, Станкович |

### Opera & Vocal Arts (2 modules)

| Module | Focus | Key Works |
|--------|-------|-----------|
| M144 | Ukrainian Opera Tradition | Запорожець за Дунаєм, Наталка Полтавка, Тарас Бульба |
| M145 | Art Song & Choral Music | Українська пісня, хорова традиція, Щедрик |

### Visual Arts (2 modules)

| Module | Focus | Key Figures |
|--------|-------|-------------|
| M146 | Icons to Avant-Garde | Боровиковський, Федотов, Бойчук, Казимир Малевич |
| M147 | Modern Ukrainian Visual Arts | Шишко, Ройтбурд, сучасне мистецтво |

### Ballet & Dance (1 module)

| Module | Focus | Key Figures |
|--------|-------|-------------|
| M148 | Ukrainian Ballet | Серж Лифар, Надія Павлова, Національний балет |

### Theater (2 modules)

| Module | Focus | Key Figures |
|--------|-------|-------------|
| M149 | Historical Ukrainian Theater | Лесь Курбас, Березіль, Гнат Юра |
| M150 | Contemporary Ukrainian Theater | Сучасні театри, режисери, драматурги |

### Architecture (1 module)

| Module | Focus | Key Sites |
|--------|-------|-----------|
| M151 | Ukrainian Architecture | Бароко, модерн, конструктивізм, сучасна архітектура |

---

## Module Structure (Fine Arts-Specific)

### 1. Frontmatter

```yaml
---
module: c1-1XX
title: "[Fine Arts Topic]: Ukrainian Title"
phase: "C1.5 [Fine Arts & High Culture]"
pedagogy: "CBI"  # Content-Based Instruction
register: "науковий/публіцистичний"
tags:
  - fine-arts
  - [domain: classical-music, opera, visual-arts, ballet, theater, architecture]
  - [era: baroque, romantic, modern, contemporary]
grammar:
  - "Art criticism vocabulary"
  - "Aesthetic terminology"
vocabulary_focus:
  - "Мистецька термінологія"
  - "Критика та аналіз"
---
```

### 2. Fine Arts Content Structure

#### Section 1: Artistic Introduction — 400-500 words

```markdown
# [Fine Arts Topic]

> **Чому це важливо?**
>
> [Explain artistic/cultural significance]
> [Connection to world culture AND Ukrainian identity]
> [Why C1 learners should know this]

## Вступ

[Engaging introduction to the art form — 200-250 words]

[Historical context — origins, development, Ukrainian contribution]

> **Світовий контекст**
>
> [How this art form developed in Europe and Ukraine's role]

### Ключова термінологія

| Термін | Значення | Приклад |
|--------|----------|---------|
| [Term 1] | [Meaning] | [Example usage] |
| [Term 2] | [Meaning] | [Example usage] |
| [Term 3] | [Meaning] | [Example usage] |
```

#### Section 2: Deep Artistic Content — 800-1000 words

```markdown
## [Main Artistic Content]

### [Era/Movement/Figure 1]: [Title]

[Detailed exploration — 300-400 words]

**Ключова постать: [Name]** (роки життя)

> [Biographical sketch — 100-150 words]
>
> **Головні твори:**
> - [Work 1] (рік) — [significance]
> - [Work 2] (рік) — [significance]
> - [Work 3] (рік) — [significance]

**Автентичний текст:**

> [Excerpt from review, libretto, exhibition catalog, or program notes — 100-200 words]
>
> **Ключові терміни:**
> - [Term]: [explanation]
> - [Term]: [explanation]

> **Мистецький аналіз**
>
> [Critical analysis of style, technique, significance]

---

### [Era/Movement/Figure 2]: [Title]

[Continue pattern — 300-400 words]

**Порівняння з європейським контекстом:**

| Аспект | Українська школа | Європейська традиція |
|--------|------------------|----------------------|
| Стиль | [Ukrainian style] | [European equivalent] |
| Вплив | [Ukrainian influence] | [European influence] |
| Особливість | [Ukrainian distinction] | [European norm] |

---

### [Era/Movement/Figure 3]: [Title]

[Continue pattern — 300-400 words]

> **Культурне значення**
>
> [Why this matters for Ukrainian cultural identity]
```

#### Section 3: Technical Analysis — 300-400 words

```markdown
## Технічний аналіз

### [Technique/Style/Form]

[Detailed explanation of artistic technique — 150-200 words]

**Приклад аналізу:**

[Analyze a specific work in detail — 100-150 words]

| Елемент | Характеристика | Значення |
|---------|----------------|----------|
| [Element 1] | [Characteristic] | [Significance] |
| [Element 2] | [Characteristic] | [Significance] |
| [Element 3] | [Characteristic] | [Significance] |

### Критичне мислення

**Питання для роздуму:**
1. Як українські митці поєднували національне та європейське?
2. Яку роль відіграло мистецтво у формуванні національної ідентичності?
3. Як радянський період вплинув на розвиток цього мистецтва?
4. Які сучасні митці продовжують традицію?
```

#### Section 4: Modern Context — 200-300 words

```markdown
## Сучасна Україна

### Сучасні майстри

[Contemporary artists continuing the tradition — 100-150 words]

**Провідні митці:**
- [Contemporary figure 1] — [contribution]
- [Contemporary figure 2] — [contribution]
- [Contemporary figure 3] — [contribution]

### Де побачити/почути

| Місце | Тип | Репертуар/Колекція |
|-------|-----|-------------------|
| [Venue 1] | [Type] | [Specialty] |
| [Venue 2] | [Type] | [Specialty] |
| [Festival/event] | [Type] | [Specialty] |

> **Де знайти**
>
> [Recordings, streaming, museums, concert halls, YouTube channels]
```

---

## Fine Arts-Specific Activities

### CRITICAL: Language Practice, Not Content Testing

<critical>

**Activities test LANGUAGE SKILLS, not arts knowledge recall.**

The lesson teaches both Ukrainian AND fine arts content. Activities practice only Ukrainian using artistic content as context.

**CORRECT:** "Згідно з текстом, як автор характеризує стиль Лисенка?" (requires reading Ukrainian)
**WRONG:** "У якому році була написана опера 'Запорожець за Дунаєм'?" (tests factual recall, not language)

**Key Test:** Can the learner answer without reading the Ukrainian text? If yes, rewrite.

| Component | Purpose |
|-----------|---------|
| **Lesson Content** | Teaches BOTH Ukrainian language AND fine arts knowledge |
| **Activities** | Practice ONLY Ukrainian language skills using arts content as context |

**Activity Types and Their Language Focus:**
- **quiz**: Test reading comprehension — "Згідно з текстом модуля..."
- **cloze**: Test vocabulary in arts context (reviews, program notes)
- **match-up**: Test vocabulary — Ukrainian arts terms <-> Ukrainian definitions
- **fill-in**: Test vocabulary/collocations from module
- **group-sort**: Test categorization using module vocabulary (eras, styles, genres)
- **mark-the-words**: Test grammar recognition in authentic arts text
- **error-correction**: Test grammar in arts sentences, NOT factual accuracy

</critical>

---

### Activity Format Quick Reference

**CRITICAL:** Use these exact formats for MDX generation to work correctly.

| Activity | Format |
|----------|--------|
| **quiz** | `- [ ] wrong` / `- [x] correct` with optional `> explanation` |
| **true-false** | `- [x] True.` with `> explanation` / `- [ ] False.` with `> explanation` |
| **fill-in** | `> [!answer] correct` + `> [!options] a \| b \| c \| d` |
| **error-correction** | ALL 4 required: `> [!error]` + `> [!answer]` + `> [!options]` + `> [!explanation]` |
| **match-up** | Table: `\| Left \| Right \|` |
| **group-sort** | `### Category` headers with `- items` underneath |
| **unjumble** | `> [!answer] Correct sentence here.` |
| **cloze** | Inline: `{blank\|opt1\|opt2\|answer}` |
| **select** | Multiple `- [x]` for all correct options |
| **translate** | Multi-choice: `- [x] Correct translation.` with `> explanation` |
| **mark-the-words** | `*marked*` words in blockquote passage |
| **dialogue-reorder** | `- [N]` numbered lines (N = correct order) |

---

### Arts Terminology Matching

```markdown
## match-up: Музична термінологія

| Термін | Значення |
|--------|----------|
| опера | сценічний жанр, що поєднує музику, спів і драму |
| симфонія | великий оркестровий твір у кількох частинах |
| кантата | вокально-інструментальний твір для солістів і хору |
| увертюра | оркестровий вступ до опери чи балету |
| арія | сольний вокальний номер в опері |
| лібрето | текст опери чи музичного твору |
| партитура | нотний запис усіх голосів оркестру |
| диригент | музикант, який керує оркестром |
| прем'єра | перше публічне виконання твору |
| репертуар | сукупність творів, які виконує театр чи музикант |

[14+ fine arts terminology matches per module]
```

### Era/Style Classification

```markdown
## group-sort: Музичні епохи

Розподіліть композиторів за епохами:

- group: Бароко та класицизм
  - Дмитро Бортнянський
  - Максим Березовський
  - Артемій Ведель

- group: Романтизм / Національна школа
  - Микола Лисенко
  - Семен Гулак-Артемовський
  - Кирило Стеценко

- group: Модернізм (XX століття)
  - Борис Лятошинський
  - Левко Ревуцький
  - Мирослав Скорик

- group: Сучасність
  - Валентин Сильвестров
  - Євген Станкович
  - Вікторія Полєвá

[20+ items across 3-4 categories]
```

### Reading Comprehension (Language-Focused)

```markdown
## quiz: Розуміння тексту

> **Instruction:** Відповідайте на питання на основі прочитаного тексту модуля.

1. Згідно з текстом, як автор характеризує внесок Миколи Лисенка в українську музику?
   - [ ] Автор зазначає, що Лисенко лише обробляв народні пісні
   - [x] Автор виділяє Лисенка як засновника української національної музичної школи
   - [ ] Автор пише, що творчість Лисенка не мала впливу на наступні покоління
   - [ ] Автор не згадує Лисенка в тексті
   > У тексті чітко формулюється роль Лисенка в розділі про національну школу.

2. Як у тексті модуля описано значення опери "Запорожець за Дунаєм"?
   - [ ] Текст зосереджується лише на музичних аспектах
   - [ ] Автор називає оперу невдалою спробою
   - [x] Автор підкреслює, що це перша українська опера, яка мала світовий успіх
   - [ ] У тексті не згадується ця опера
   > У розділі про українську оперу автор детально пояснює історичне значення твору.

[All questions must begin with "Згідно з текстом" — tests READING COMPREHENSION, not arts knowledge recall]
```

### Arts Review Cloze

```markdown
## cloze: Мистецька рецензія

Заповніть пропуски у рецензії:

> Вчорашня {прем'єра|виставка|концерт|прем'єра} опери "Наталка Полтавка" у {Національній|Київській|Харківській|Національній} опері стала справжньою подією сезону. {Диригент|Режисер|Композитор|Диригент} майстерно {інтерпретував|написав|переклав|інтерпретував} партитуру Лисенка, надаючи їй сучасного {звучання|вигляду|змісту|звучання}. Особливо вразила {арія|сцена|п'єса|арія} головної героїні у другому {акті|дії|розділі|акті}.

[15+ blanks in authentic arts review context]
```

---

## Engagement Boxes for Fine Arts Modules

```markdown
> **Світовий контекст**
>
> [How Ukrainian art fits into world culture]

> **Чи знали ви?**
>
> [Surprising fact about the artist or work]

> **Мистецький аналіз**
>
> [Technical or aesthetic insight]

> **Культурне значення**
>
> [Why this matters for Ukrainian identity]

> **Де послухати/подивитися**
>
> [Recordings, performances, exhibitions, YouTube, streaming]

> **Сучасна спадщина**
>
> [How contemporary artists continue the tradition]
```

---

## Vocabulary Section for Fine Arts Modules

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| **опера** | opera | сценічний музично-драматичний жанр |
| **симфонія** | symphony | великий оркестровий твір |
| **диригент** | conductor | керівник оркестру |
| **лібрето** | libretto | текст опери |
| **партитура** | score | нотний запис для всіх інструментів |
| **прем'єра** | premiere | перше виконання |
| **репертуар** | repertoire | сукупність виконуваних творів |
| **композитор** | composer | автор музичних творів |
| **виконавець** | performer | музикант, співак |
| **ансамбль** | ensemble | група виконавців |
| **соліст** | soloist | виконавець сольних партій |
| **хор** | choir, chorus | колектив співаків |
| **оркестр** | orchestra | колектив музикантів |
| **арія** | aria | сольний номер в опері |
| **увертюра** | overture | вступ до опери |
| [35+ fine arts terms per module] | | |
```

---

## Domain-Specific Vocabulary by Module Type

### Classical Music Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| камерна музика | chamber music | для невеликого ансамблю |
| хоровий концерт | choral concerto | жанр бароко (Бортнянський) |
| симфонічна поема | symphonic poem | програмний оркестровий твір |
| етюд | etude | навчальна п'єса |
| ноктюрн | nocturne | "нічна" п'єса |
| прелюдія | prelude | вступна п'єса |

### Opera Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| тенор | tenor | високий чоловічий голос |
| сопрано | soprano | високий жіночий голос |
| бас | bass | низький чоловічий голос |
| речитатив | recitative | мелодекламація в опері |
| дует | duet | номер для двох співаків |
| фінал | finale | заключна частина акту |

### Visual Arts Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| полотно | canvas | основа для живопису |
| олія | oil (paint) | олійні фарби |
| акварель | watercolor | водяні фарби |
| графіка | graphic art | мистецтво малюнка |
| скульптура | sculpture | просторове мистецтво |
| авангард | avant-garde | експериментальне мистецтво |
| іконопис | icon painting | церковний живопис |

### Theater Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| режисер | director | постановник вистави |
| актор | actor | виконавець ролі |
| сцена | stage | місце дії |
| декорації | set design | оформлення сцени |
| драматург | playwright | автор п'єси |
| вистава | performance | театральне дійство |
| антракт | intermission | перерва між актами |

### Ballet Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| балерина | ballerina | танцівниця балету |
| хореограф | choreographer | автор танців |
| пуанти | pointe shoes | балетне взуття |
| па-де-де | pas de deux | танець удвох |
| кордебалет | corps de ballet | ансамбль танцівників |
| прима | prima ballerina | провідна балерина |

### Architecture Vocabulary

| Термін | Переклад | Примітки |
|--------|----------|----------|
| фасад | facade | зовнішня стіна будівлі |
| купол | dome | склепінне перекриття |
| дзвіниця | bell tower | вежа з дзвонами |
| бароко | baroque | архітектурний стиль XVII-XVIII ст. |
| модерн | art nouveau | стиль кінця XIX — поч. XX ст. |
| конструктивізм | constructivism | авангардний стиль 1920-х |

---

## Key Ukrainian Figures by Domain

### Classical Music

| Постать | Роки | Внесок |
|---------|------|--------|
| Дмитро Бортнянський | 1751-1825 | Хорові концерти, директор Придворної капели |
| Максим Березовський | 1745-1777 | Перший український оперний композитор |
| Артемій Ведель | 1767-1808 | Духовна хорова музика |
| Микола Лисенко | 1842-1912 | "Батько української музики", опери, романси |
| Микола Леонтович | 1877-1921 | "Щедрик" (Carol of the Bells) |
| Борис Лятошинський | 1895-1968 | Українська симфонічна школа |
| Валентин Сильвестров | 1937- | Постмодерна класична музика |

### Opera & Vocal

| Постать | Роки | Внесок |
|---------|------|--------|
| Семен Гулак-Артемовський | 1813-1873 | "Запорожець за Дунаєм" |
| Соломія Крушельницька | 1872-1952 | Світова оперна зірка |
| Іван Козловський | 1900-1993 | Тенор світового рівня |
| Анатолій Солов'яненко | 1932-1999 | Тенор, народний артист СРСР |

### Visual Arts

| Постать | Роки | Внесок |
|---------|------|--------|
| Володимир Боровиковський | 1757-1825 | Портретист, класицизм |
| Тарас Шевченко | 1814-1861 | Художник і поет |
| Михайло Бойчук | 1882-1937 | Монументалізм, бойчукісти |
| Казимір Малевич | 1879-1935 | Супрематизм |
| Олександр Архипенко | 1887-1964 | Скульптура модернізму |

### Ballet

| Постать | Роки | Внесок |
|---------|------|--------|
| Серж Лифар | 1905-1986 | Балетмейстер Паризької опери |
| Надія Павлова | 1956- | Прима-балерина Великого театру |

### Theater

| Постать | Роки | Внесок |
|---------|------|--------|
| Лесь Курбас | 1887-1937 | Режисер-реформатор, театр "Березіль" |
| Гнат Юра | 1888-1966 | Актор, засновник театру ім. Франка |
| Марія Заньковецька | 1854-1934 | Легендарна актриса |

### Architecture

| Постать | Роки | Внесок |
|---------|------|--------|
| Іван Григорович-Барський | 1713-1791 | Українське бароко |
| Владислав Городецький | 1863-1930 | Київський модерн |
| Віктор Кричевський | 1872-1952 | Український модерн |

---

## Related Documentation

- **Base template:** `docs/l2-uk-en/templates/c1-module-template.md`
- **Folk culture template:** `docs/l2-uk-en/templates/c1-folk-culture-module-template.md`
- **C1 Curriculum Plan:** `docs/l2-uk-en/C1-CURRICULUM-PLAN.md`
- **Arts Expansion Proposal:** `docs/l2-uk-en/C1-REVIEW-PROPOSAL.md`
- **Activity Reference:** `docs/ACTIVITY-MARKDOWN-REFERENCE.md`

---

**Last Updated:** 2025-12-29
**Template Version:** 1.0
