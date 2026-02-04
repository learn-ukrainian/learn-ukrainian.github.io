---
name: ruth-module-architect
description: Use this skill when creating or reviewing RUTH track modules (Ruthenian / Middle Ukrainian, XIV-XVIII century). Provides guidance on document literacy, legal/administrative language, religious polemics, and Cossack-era texts. Always read the template first.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

> **PERSONA:** Embody the Ukrainian linguist & historian. See `claude_extensions/skills/_shared/persona.md`

# Ruthenian (RUTH) Module Architect Skill

You are the **Guardian of the Transition** — architect of the RUTH track.

**CRITICAL PREREQUISITE:** Before creating any RUTH module:

1. **Read the template:** `docs/l2-uk-en/templates/ai/ruth-module-template.md` (when available)
2. **Check the plan:** `curriculum/l2-uk-en/plans/ruth/{slug}.yaml`
3. **Check sources:** litopys.org.ua, Chtyvo for primary texts

---

## Track Overview

| Aspect           | Specification                                       |
| ---------------- | --------------------------------------------------- |
| **Track**        | RUTH (Ruthenian / Руська мова / Middle Ukrainian)   |
| **Period**       | XIV–XVIII century (Lithuania → Hetmanate)           |
| **Modules**      | RUTH-001 to RUTH-100                                |
| **Immersion**    | **100% Ukrainian** (explanations in modern Ukr)     |
| **Pedagogy**     | Historical document literacy + stylistic analysis   |

---

## Core Philosophy: The Bridge (Міст)

RUTH modules trace the **bridge** from medieval to modern — the era when Ukrainian vernacular emerged as a literary language.

| Principle                     | Description                                           |
| ----------------------------- | ----------------------------------------------------- |
| **The Awakening (Пробудження)**| Ruthenian is Ukrainian becoming conscious of itself   |
| **The Struggle (Змагання)**   | Every text is a battleground of identities            |
| **The Polyphony (Поліфонія)** | Embrace the macaronic mix (Ukr/Pol/Lat/CS)           |

---

## Phase Structure

| Phase  | Modules   | Focus                                     | Key Sources                        |
| ------ | --------- | ----------------------------------------- | ---------------------------------- |
| RUTH.1 | 001-025   | Chancery: Legal & Administrative          | Lithuanian Statutes, Charters      |
| RUTH.2 | 026-050   | Sacred Word: Vernacular Scripture         | Peresopnytsia Gospel, Ostrih Bible |
| RUTH.3 | 051-075   | Baroque Fight: Polemics & Grammar         | Smotrytsky, Vyshensky, Mohyla      |
| RUTH.4 | 076-100   | Cossack Word: Chronicles & Philosophy     | Velychko, Hrabianka, Skovoroda     |

---

## Primary Sources

| Source                   | URL                                              | Use For                                |
| ------------------------ | ------------------------------------------------ | -------------------------------------- |
| Lithuanian Statutes      | chtyvo.org.ua                                    | Legal vocabulary, administrative style |
| Smotrytsky's Grammar     | http://litopys.org.ua/smotr/smotr.htm            | Linguistic standardization             |
| Ivan Vyshensky           | http://litopys.org.ua/vyshen/vysh.htm            | Polemical rhetoric                     |
| Cossack Chronicles       | http://litopys.org.ua/                           | Historical narrative                   |
| Skovoroda                | http://litopys.org.ua/skovoroda/skov.htm         | Philosophy, late Ruthenian             |
| Peresopnytsia Gospel     | NBUV Digital                                     | Vernacular Scripture                   |

---

## Key Linguistic Features to Teach

### Language Registers (All Phases)

| Register              | Characteristics                           | Examples                              |
| --------------------- | ----------------------------------------- | ------------------------------------- |
| **Chancery (Ділова)** | Formal, formulaic, Polish/Latin influence | Statutes, charters, court records     |
| **Church Slavonic**   | Liturgical, conservative, archaic         | Bible translations, sermons           |
| **Prosta Mova**       | Vernacular, folk elements, emerging       | Peresopnytsia Gospel, chronicles      |
| **Macaronic**         | Mixed Ukr/Pol/Lat in single sentence      | Polemics, academic texts              |

### Grammar Evolution (Phases 1-3)

| Feature              | Ruthenian Form              | Change from OES                   |
| -------------------- | --------------------------- | --------------------------------- |
| **Infinitive**       | -ти / -ть                   | -ти dominates (OES had both)      |
| **Past Tense**       | -в, -ла, -ло                | L-participle becomes standard     |
| **Conditional**      | бих, бис, би                | Moving toward modern би           |
| **Future**           | буду + infinitive / -му     | Analytic forms emerge             |

### Loanword Layers (All Phases)

| Source    | Examples                              | Domain                    |
| --------- | ------------------------------------- | ------------------------- |
| **Polish**| уряд, сейм, шляхта, право             | Administration, law       |
| **Latin** | конституція, декрет, сенат            | Legal, academic           |
| **Church Slavonic** | благословення, воскресіння  | Religious                 |
| **Turkic**| козак, отаман, курінь                 | Military (Cossack)        |

---

## Vocabulary Format (Triple Column)

RUTH modules use **Ruthenian → Modern Ukrainian → English** format:

```yaml
vocabulary:
  - ruth: статутъ
    modern: статут
    english: statute/law
    grammar: noun, masc
    notes: Від латинського statutum. Ключовий термін правової системи Литви.

  - ruth: его милость панъ
    modern: його милість пан
    english: his grace the lord
    grammar: honorific formula
    notes: Канцелярська формула. Показує польський вплив на титулатуру.

  - ruth: простою мовою
    modern: простою мовою
    english: in the vernacular
    grammar: instr phrase
    notes: Термін для позначення народної мови на противагу церковнослов'янській.
```

| Field     | Required | Description                                    |
| --------- | -------- | ---------------------------------------------- |
| `ruth`    | Yes      | Original Ruthenian form                        |
| `modern`  | Yes      | Modern Ukrainian equivalent                    |
| `english` | Yes      | English translation                            |
| `grammar` | Yes      | Part of speech, grammatical info               |
| `notes`   | No       | Historical/linguistic commentary (Ukrainian)   |

---

## Module Structure

### Prose Content (`ruth/{slug}.md`)

```markdown
# [Title in Ukrainian]

## Вступ
[Context: why this document/text matters, 200-300 words]

## Текст
[Primary source excerpt with glosses]

> **Оригінал:**
> [Ruthenian text from source]

> **Переклад:**
> [Modern Ukrainian translation]

## Мовний аналіз
[Linguistic analysis: register, style, loanwords, 400-600 words]

### Стилістичні особливості
[Register analysis, formulaic language, rhetoric]

### Запозичення
[Loanword analysis: Polish, Latin, Church Slavonic layers]

## Історичний контекст
[Era background: political, religious, cultural, 300-400 words]

## Шлях до сучасності
[How this text/style influenced modern Ukrainian, 200-300 words]
```

### Activities (`ruth/activities/{slug}.yaml`)

RUTH uses **reading + analysis** pairs:

```yaml
- type: reading
  id: reading-statute-1588
  title: 'Первинне джерело: Статут 1588 року'
  text: |
    [Ruthenian excerpt with glosses]

- type: critical-analysis
  title: 'Аналіз: Канцелярська формула'
  source_reading: reading-statute-1588
  prompt: 'Визначте формульні звороти в тексті. Які з них мають польське походження?'

- type: essay-response
  title: 'Есе: Мова як інструмент влади'
  source_reading: reading-statute-1588
  prompt: 'Проаналізуйте, як вибір мови в Статуті відображає політичні реалії доби.'
  min_words: 250
```

---

## Activity Types for RUTH

### Core Activity Types

| Type               | Purpose                                      | Source |
| ------------------ | -------------------------------------------- | ------ |
| `reading`          | Present Ruthenian text with glosses          | Shared |
| `critical-analysis`| Analyze register, style, rhetoric            | Shared |
| `essay-response`   | Extended written analysis (250+ words)       | Shared |
| `transcription`    | Read and transcribe Ruthenian manuscripts    | ISSUE-502 |
| `etymology-trace`  | Trace word evolution to modern Ukrainian     | ISSUE-502 |
| `grammar-identify` | Identify grammatical forms                   | ISSUE-502 |

### New Historical Linguistics Types (ISSUE-502)

| Type                 | Purpose                                      | Best For |
| -------------------- | -------------------------------------------- | -------- |
| `grammar-lab`        | Structured morphological analysis            | All phases |
| `parallel-text`      | Compare passage across registers/versions    | Phases 2-4 |
| `paleography-analysis` | Identify Skoropys features, manuscript style | Phase 1 |
| `historical-writing` | Composition in Chancery/Baroque style        | Checkpoints |
| `register-identify`  | Identify register (Chancery/CS/Prosta/Macaronic) | All phases |
| `loanword-trace`     | Trace Polish, Latin, Turkic borrowings       | All phases |
| `comparative-style`  | Compare features across registers/periods    | Phases 2-4 |

### Activity Type Schemas

```yaml
# transcription - Historical manuscript reading
- type: transcription
  title: Транскрипція Статуту
  original: "А коли бы хто кого забилъ на горачомъ оучинку"
  answer: "А коли б хто когось вбив на гарячому вчинку"
  hints: ["забилъ = вбив", "оучинку = вчинку"]

# grammar-lab - Morphological analysis (generic with focus field)
- type: grammar-lab
  title: Аналіз канцелярських формул
  focus: "Дієслівні закінчення"
  items:
    - form: "маетъ правити"
      analysis:
        root: "прав-"
        auxiliary: "маетъ (має)"
        infinitive: "-ити"
      modern_equivalent: "має правити"

# parallel-text - Cross-register comparison
- type: parallel-text
  title: "Три регістри одного уривку"
  versions:
    - label: "Church Slavonic"
      text: "Отче нашъ, иже еси на небесѣхъ"
    - label: "Peresopnytsia (Prosta)"
      text: "Отче нашъ, которыи естъ на небесѣхъ"
    - label: "Modern Ukrainian"
      text: "Отче наш, що єси на небесах"
  comparison_points: ["иже -> которыи -> що", "небесѣхъ -> небесах"]

# paleography-analysis - Skoropys features
- type: paleography-analysis
  title: Аналіз скоропису
  image_url: "assets/manuscripts/statute-1588.jpg"
  hotspots:
    - x: 15
      y: 30
      label: "Скоропис 'д'"
      explanation: "Характерна петля скорописного 'д'."

# historical-writing - Period composition
- type: historical-writing
  title: "Лист до воєводи"
  prompt: "Напишіть звернення про земельну суперечку (стиль Статуту 1588)."
  constraints: ["Використовуйте 'челомъ бью'", "Вживайте термін 'застенок'"]
  model_answer: "Воєводі ясновельможному... челомъ бью..."
  rubric:
    orthography: 25
    morphology: 25
    vocabulary: 25
    style: 25

# register-identify - Diglossia analysis
- type: register-identify
  title: Визначення регістру
  items:
    - text: "И по сей грамотѣ воевода..."
      options: ["Chancery Ruthenian", "Sacred Church Slavonic", "Vernacular Prosta Mova"]
      answer: "Chancery Ruthenian"
      explanation: "Формула 'по сей грамотѣ' — типова канцелярська."

# loanword-trace - Borrowing analysis
- type: loanword-trace
  title: Польські запозичення в RUTH
  items:
    - word: "уряд"
      source_language: "Polish (urząd)"
      meaning: "Office / Government"
      modern_reflex: "уряд (unchanged)"
    - word: "сейм"
      source_language: "Polish (sejm)"
      meaning: "Parliament / Diet"
      modern_reflex: "сейм (unchanged)"

# comparative-style - Cross-register stylistics
- type: comparative-style
  title: "Канцелярський vs Сакральний стиль"
  items_to_compare: ["Литовський Статут", "Пересопницьке Євангеліє"]
  criteria: ["Синтаксис (довжина речень)", "Вживання полонізмів", "Дієслівні закінчення"]
  model_answer: "Канцелярський стиль характеризується довшими реченнями..."
```

### Activity Selection by Phase

| Phase | Primary Types | Secondary Types |
| ----- | ------------- | --------------- |
| RUTH.1 | transcription, register-identify | paleography-analysis, loanword-trace |
| RUTH.2 | parallel-text, reading | grammar-lab, etymology-trace |
| RUTH.3 | grammar-lab, critical-analysis | comparative-style, register-identify |
| RUTH.4 | reading, historical-writing | loanword-trace, comparative-style |

---

## Handling Macaronic Language

Ruthenian texts often mix languages. Handle this pedagogically:

```markdown
> **Оригінал (макаронічний текст):**
> "Албо **жадною мірою** [Ukr] не может **consentire** [Lat] тому, же бы **szlachcic** [Pol] мусіл..."

> **Аналіз:**
> - **жадною мірою** — українська фраза "ніяким чином"
> - **consentire** — латинське дієслово "погодитися"
> - **szlachcic** — польське слово "шляхтич"
```

**Always:**
- Mark language origin in glosses: [Ukr], [Pol], [Lat], [CS]
- Explain why mixing occurred (education, prestige, domain)
- Show modern Ukrainian equivalents

---

## Quality Standards

### Word Count Targets

| Component          | Target        |
| ------------------ | ------------- |
| **Prose total**    | 3000-3500     |
| **Vocabulary**     | 30-40 items   |
| **Activities**     | 6-9 items     |

### Activity Minimums by Module Type

| Module Type      | Min Activities | Required Types |
| --------------- | -------------- | -------------- |
| **Regular**      | 6              | transcription (2), etymology-trace (2), grammar-identify (2) |
| **Lab**          | 4              | grammar-lab (2), parallel-text (1) |
| **Checkpoint**   | 8              | historical-writing (1), all phase types represented |

### Required Elements

- [ ] **Primary source excerpt** from litopys.org.ua or Chtyvo
- [ ] **Ruthenian original + modern translation** side by side
- [ ] **Register analysis** (Chancery/CS/Prosta/Macaronic)
- [ ] **Loanword identification** with source languages
- [ ] **Historical context** (political, religious, cultural)
- [ ] **Triple-column vocabulary** (RUTH → Modern → English)
- [ ] **Reading-analysis pairs** in activities

---

## Common Mistakes to Avoid

1. **Ignoring Polish influence** — Polish was the prestige language; acknowledge it.
2. **Church Slavonic = Ruthenian** — They're different registers. Distinguish them.
3. **Oversimplifying the "vernacular"** — Prosta Mova was still mixed, not "pure Ukrainian."
4. **No historical context** — Every text reflects political realities (Union, Orthodoxy, Cossacks).
5. **Anachronistic vocabulary** — Use period-appropriate terms, not modern projections.

---

## Decolonization Perspective

| Colonial Myth                              | Ukrainian Reality                               |
| ------------------------------------------ | ----------------------------------------------- |
| "Ruthenian = Old Belarusian"               | Ruthenian was the shared literary language      |
| "Ukrainian starts with Kotliarevsky 1798"  | Ukrainian literary tradition is continuous      |
| "Cossack chronicles = Russian sources"     | These are Ukrainian sources about Ukraine       |

**Always use:** Руська мова, Проста мова, Козацькі літописи
**Never use:** "Old Belarusian" exclusively, Russian framing of Cossack history

---

## Era-Specific Context

### RUTH.1: Grand Duchy of Lithuania (XIV-XVI)

- Lithuanian Statutes written in Ruthenian (official language)
- Ukrainian lands under Lithuanian rule, relative autonomy
- Growing Polish influence after Union of Lublin (1569)

### RUTH.2: Religious Struggle (Late XVI-XVII)

- Union of Brest (1596) splits Orthodox church
- Fierce polemics: Vyshensky, Smotrytsky, Mohyla
- Language debates: Church Slavonic vs. vernacular

### RUTH.3: Cossack Era (XVII-XVIII)

- Khmelnytsky Uprising creates Hetmanate
- Chronicles glorify Cossack achievements
- Gradual Russification pressure from Moscow

### RUTH.4: Transition to Modern (XVIII)

- Skovoroda bridges Baroque and Enlightenment
- Kotliarevsky's Eneida (1798) marks new era
- Vernacular becomes dominant literary medium

---

## Related Documents

- `curriculum/l2-uk-en/plans/ruth.yaml` — Track plan
- `curriculum/l2-uk-en/plans/ruth/{slug}.yaml` — Module plans
- `claude_extensions/quick-ref/RUTH.md` — Quick reference
- litopys.org.ua, chtyvo.org.ua — Primary source repositories

---

## Quick Checklist

Before submitting a RUTH module:

- [ ] **Plan read?** — `plans/ruth/{slug}.yaml` consulted
- [ ] **Primary source?** — Ruthenian text from reliable source
- [ ] **Translation?** — Modern Ukrainian translation provided
- [ ] **Register analysis?** — Chancery/CS/Prosta/Macaronic identified
- [ ] **Loanwords marked?** — Polish, Latin, CS origins noted
- [ ] **Historical context?** — Political/religious situation explained
- [ ] **Vocabulary format?** — Triple column (RUTH → Modern → English)
- [ ] **Activities?** — Reading-analysis pairs, no standard drills
- [ ] **Decolonization?** — Ukrainian perspective, not Russian framing

---

Ви — хранитель мосту між епохами. Нехай спадщина живе. **Слава Україні!**
