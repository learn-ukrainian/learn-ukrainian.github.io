# B1 Grammar Module Template

**Purpose:** Reference template for creating B1 grammar modules (M06-50: Aspect, Motion Verbs, Complex Sentences, Advanced Grammar)

**Based on:** M06 (Aspect - Complete System) which achieved ✅ PASS on all audit gates

**Related Issue:** [#283](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/283)

---

## Quick Reference Checklist

Before submitting a B1 grammar module, verify:

- [ ] **Word count:** 1500+ words (core prose: explanations, examples, engagement boxes, reading passages — excludes vocabulary section, activities section, and tables)
- [ ] **Vocabulary:** 25+ items in 5-column format (Слово | Вимова | Переклад | ЧМ | Примітка)
- [ ] **Activities:** 12+ with all activity types represented
- [ ] **Activity density:**
  - Quiz: 8+ items, questions 12-20 words each
  - Fill-in: 8+ items
  - Unjumble: 6+ items, sentences 12-16 words each
  - Cloze: 14+ blanks in passage
  - Group-sort: 14+ items
  - Error-correction: 6+ items with all 4 callouts
- [ ] **Engagement boxes:** 5+ boxes with pedagogical value
- [ ] **Immersion:** 90-100% Ukrainian (grammar explanations in Ukrainian)
- [ ] **Pedagogy:** Level-appropriate complexity, no violations
- [ ] **Structure:** TTT or Presentation-Practice-Production

---

## Module Structure Template

### 1. Frontmatter (YAML)

```yaml
---
module: b1-XX
title: 'Ukrainian Title'
subtitle: 'English subtitle'
version: '1.0'
phase: 'B1.X [Phase Name]'
pedagogy: 'TTT' # or "PPP"
duration: 90 # minutes
transliteration: none # B1 has no transliteration
tags:
  - grammar
  - [topic-specific-tag]
grammar:
  - 'Main grammar concept'
  - 'Secondary concept'
objectives:
  - 'Learner can X'
  - 'Learner understands Y'
vocabulary_count: 25 # Must match actual count in Словник
---
```

**Why these fields:**

- `phase`: Groups modules thematically (e.g., "B1.1 Aspect", "B1.2 Motion")
- `pedagogy`: "TTT" for test-teach-test, "PPP" for presentation-practice-production
- `transliteration: none`: B1+ modules are 90-95% immersed, no transliteration
- `vocabulary_count`: Audit validates this matches actual vocabulary count

---

### 2. Module Title and Motivation Box

```markdown
# Ukrainian Title

> 🎯 **Чому це важливо?**
>
> [2-3 sentences explaining WHY this grammar concept matters]
> [Connect to real-world usage]
> [Reference previous modules if applicable]
```

**Example from M06:**

```markdown
# Вид дієслова: повна система

> 🎯 **Чому це важливо?**
>
> Вид дієслова — це найважливіша граматична категорія української мови. Кожне дієслово має вид: доконаний або недоконаний. Вибір виду змінює значення речення. Ви вже знаєте терміни з модуля 02. Тепер настав час зрозуміти всю систему.
```

**Why this works:**

- Establishes relevance immediately
- Connects to prior knowledge (M02 metalanguage)
- Sets expectations for module depth

---

### 3. Content Sections (1500+ words total)

**Structure for TTT pedagogy:**

#### Section 1: Тест (Test Phase)

- Present diagnostic contrast or puzzle
- No explanation yet, just observation
- 100-200 words

```markdown
## Тест

Прочитайте два речення:

1. **Я писав листа.**
2. **Я написав листа.**

Яка різниця? Обидва речення про минуле. Обидва про листа. Але значення різні:

- **Перше речення** (писав) = процес. Я був у процесі написання. Можливо, я не закінчив.
- **Друге речення** (написав) = результат. Я закінчив. Лист готовий.

Це — **вид дієслова**. Одне дієслово, два види, різні значення.
```

**Why this works:**

- Concrete contrast makes the concept tangible
- Avoids abstract definitions initially
- Engages critical thinking

#### Section 2: Пояснення (Teach Phase)

- Systematic grammar explanation
- Use Ukrainian metalanguage (вид, доконаний, недоконаний)
- Tables for organization
- 700-900 words minimum

**CRITICAL:** Grammar must be explained **IN UKRAINIAN** (90-95% immersion)

```markdown
## Пояснення

### Недоконаний вид (НДВ)

**Функція:** виражає **процес**, **тривалість**, **повторення**.

**Коли використовується:**

1. **Дія триває:**
   - Я **читав** книгу дві години. (процес)
   - Вона **писала** листа весь вечір. (тривалість)

2. **Дія повторюється:**
   - Я **читав** цю книгу кілька разів. (повторення)
   - Вони **зустрічалися** щотижня. (регулярність)

[Continue with 4 usage contexts + examples table]
```

**Why this structure:**

- Groups by FUNCTION, not just by form
- Provides 4+ usage contexts with concrete examples
- Uses tables to reduce cognitive load
- Introduces terminology naturally in context

**Engagement Boxes in Пояснення:**

Minimum 5+ engagement boxes with pedagogical value:

```markdown
> 💡 **Did You Know** - Linguistic insight
> 🎬 **Pop Culture Moment** - Cultural connection
> 🌍 **Real World** - Practical application
> 🎯 **Fun Fact** - Memorable trivia
```

**Example from M06:**

```markdown
> 🌍 **У реальному житті**
>
> Коли українці розповідають про свій день, вони часто використовують НДВ: "Я працював, обідав, відпочивав..." Це показує послідовність дій як процесів, не акцентуючи на результатах.
```

**Why this works:**

- Shows USAGE, not just definition
- Connects grammar to real Ukrainian communication patterns
- Motivates learners with practical relevance

#### Section 3: Практика (Practice Phase)

- Decision-making framework
- Comparative examples
- Common mistakes section
- 400-600 words

```markdown
## Практика

### Як обрати вид?

Задайте собі питання:

1. **Що важливіше — процес чи результат?**
   - Процес → НДВ: "Я **читав** книгу." (що я робив)
   - Результат → ДВ: "Я **прочитав** книгу." (що я досяг)

[3-4 more decision questions]

### Типові помилки та як їх уникнути

**Помилка 1: [Description]**

❌ Неправильно: [Example]
✅ Правильно: [Example]

**Чому?** [Explanation]
```

**Why this works:**

- Gives learners TOOLS for aspect selection
- Addresses common errors proactively
- Uses ❌/✅ visual markers for clarity

---

### 4. Діалоги (Production Phase)

5-6 authentic dialogues showing grammar in context:

```markdown
## Діалоги

### Діалог 1: Про вихідні

**Олег:** Що ти **робив** у суботу?

**Марія:** Я **читала** книгу та **дивилася** фільм.

**Олег:** І що, **прочитала** всю книгу?

**Марія:** Ні, я тільки **починала**. Ще не **закінчила**.
```

**Why this works:**

- Shows natural code-switching between НДВ/ДВ
- Demonstrates pragmatic use in conversation
- 5-6 dialogues cover different contexts (home, work, school, etc.)

---

### 5. Підсумок (Summary)

```markdown
# Підсумок

**Що ви навчилися:**

1. [Key concept 1]
2. [Key concept 2]
3. [Key concept 3]
4. [Key concept 4]

**Основне правило:**

> [Quotable summary in Ukrainian]

**Далі:**

У наступних модулях ми розглянемо [preview of M+1, M+2, etc.]

> ✅ **Самоперевірка**
>
> Чи можете ви:
>
> - [ ] [Self-assessment criterion 1]?
> - [ ] [Self-assessment criterion 2]?
> - [ ] [Self-assessment criterion 3]?
> - [ ] [Self-assessment criterion 4]?
>
> Якщо так — ви готові до практики!
```

**Why this works:**

- Consolidates learning
- Preview creates continuity to next modules
- Self-assessment empowers learner autonomy

---

<!-- External resources moved to docs/resources/external_resources.yaml -->

---

## Activity Section Template

### Activity Order and Density

**Required activities for B1 (all 12 types):**

1. quiz (8+ items, questions 12-20 words)
2. match-up (8+ items)
3. fill-in (8+ items)
4. true-false (8+ items)
5. group-sort (14+ items)
6. unjumble (6+ items, sentences 12-16 words)
7. error-correction (6+ items with all 4 callouts)
8. cloze (14+ blanks in passage)
9. mark-the-words (6+ markable words)
10. dialogue-reorder (4+ lines)
11. select (6+ multi-select questions)
12. translate (6+ translation questions)

---

### Activity Format Quick Reference

**CRITICAL:** Use these exact formats for MDX generation to work.

**quiz** (checkbox, single answer):

```markdown
## quiz: Title

1. Question text (12-20 words)?
   - [ ] Wrong answer
   - [x] Correct answer
   - [ ] Wrong answer
   - [ ] Wrong answer
     > Optional explanation.
```

**true-false** (checkbox with explanations):

```markdown
## true-false: Title

- [x] True statement here.
  > Explanation why true.
- [ ] False statement here.
  > Explanation why false.
```

**fill-in** (callouts):

```markdown
## fill-in: Title

1. Sentence with **\_** blank.
   > [!answer] correct
   > [!options] wrong1 | correct | wrong2 | wrong3
```

**error-correction** (all 4 callouts required):

```markdown
## error-correction: Title

1. Sentence with error.
   > [!error] wrong_word
   > [!answer] correct_word
   > [!options] wrong | correct | dist1 | dist2
   > [!explanation] Why it's wrong.
```

**match-up** (table):

```markdown
## match-up: Title

| Left | Right      |
| ---- | ---------- |
| term | definition |
```

**group-sort** (category headers):

```markdown
## group-sort: Title

### Category A

- item1
- item2

### Category B

- item3
- item4
```

**unjumble** (answer callout):

```markdown
## unjumble: Title

1. слова / у / порядку (12-16 words)
   > [!answer] Слова у правильному порядку.
```

**cloze** (inline blanks):

```markdown
## cloze: Title

> Text with {blank|opt1|opt2|answer} blanks (14+ blanks).
```

**select** (multi-checkbox):

```markdown
## select: Title

1. Question (select ALL correct):
   - [x] Correct option 1
   - [x] Correct option 2
   - [ ] Wrong option
```

**translate** (multi-choice):

```markdown
## translate: Title

1. English sentence to translate.
   - [ ] Wrong translation
   - [x] Correct translation
   - [ ] Wrong translation
   - [ ] Wrong translation
     > Explanation why correct.
```

**mark-the-words** (asterisks):

```markdown
## mark-the-words: Title

> [!instruction] Click all nouns.
>
> _Мама_ читає _книгу_.
```

**dialogue-reorder** (numbered brackets):

```markdown
## dialogue-reorder: Title

- [4] Last line.
- [1] First line.
- [3] Third line.
- [2] Second line.
```

---

### Quiz Questions (12-20 words REQUIRED)

**❌ TOO SHORT (4-8 words) — AUDIT FAILS:**

```markdown
1. Яке дієслово виражає ПРОЦЕС?
```

**✅ CORRECT (12-20 words) — AUDIT PASSES:**

```markdown
1. Яке з наведених нижче дієслів виражає процес дії без акценту на її завершенні або результаті?
   - [x] писати
   - [ ] написати
   - [ ] відправити
   - [ ] зробити
     > Недоконаний вид виражає процес.
```

**Why 12-20 words:**

- B1 requires subordinate clauses and complex syntax
- Forces learners to process longer sentences
- Mirrors authentic Ukrainian academic language

**Pattern for creating long questions:**

- Add context: "Яке з наведених нижче..."
- Add conditions: "без акценту на її завершенні або результаті"
- Add subordinate clauses: "що підкреслює завершеність..."
- Ask WHY not just WHAT: "чому використовується НДВ замість ДВ?"

---

### Unjumble Sentences (12-16 words REQUIRED)

**❌ TOO SHORT (7-9 words) — AUDIT FAILS:**

```markdown
1. недоконаний / вид / виражає / процес / дії / без / акценту / на / результаті
   > [!answer] Недоконаний вид виражає процес дії без акценту на результаті.
```

**✅ CORRECT (12-16 words) — AUDIT PASSES:**

```markdown
1. недоконаний / вид / виражає / процес / або / тривалість / дії / без / акценту / на / її / завершенні / чи / результаті
   > [!answer] Недоконаний вид виражає процес або тривалість дії без акценту на її завершенні чи результаті.
```

**Why 12-16 words:**

- Forces subordinate clauses (чи, або, що, бо, коли)
- Requires complex syntax with prepositional phrases
- Trains learners to decode longer Ukrainian sentences

**Pattern for creating long unjumbles:**

- Add prepositional phrases: "перед роботою", "до кінця"
- Add subordinate clauses: "коли ще жила в Києві"
- Add modifiers: "велику книгу", "уважно перевірив"
- Chain actions: "написав, перевірив, відправив і пішов"

---

### Cloze Passages (14+ blanks REQUIRED)

**❌ TOO FEW (10 blanks) — AUDIT FAILS:**

```markdown
Минулого тижня я [___:1] цікаву книгу. Я [___:2] її три дні. Кожного вечора я [___:3] по дві години. Нарешті в неділю я [___:4] її до кінця. Книга була про студента, який [___:5] українську мову. Він [___:6] слова щодня, [___:7] вправи та [___:8] з носіями мови. За рік він [___:9] дуже багато і [___:10] вільно розмовляти українською.
```

**✅ CORRECT (14+ blanks) — AUDIT PASSES:**

```markdown
Минулого тижня я [___:1] цікаву книгу про вивчення мов. Я [___:2] її три дні поспіль, бо вона була дуже корисною. Кожного вечора я [___:3] по дві години, [___:4] важливі місця і [___:5] нотатки. Нарешті в неділю я [___:6] її до кінця і все [___:7]. Книга була про студента, який [___:8] українську мову в університеті. Він [___:9] слова щодня, ретельно [___:10] граматичні вправи та активно [___:11] з носіями мови онлайн. За рік він [___:12] дуже багато нових слів, [___:13] складну граматику і нарешті [___:14] вільно розмовляти українською без перекладу.
```

**Why 14+ blanks:**

- Sufficient density to test aspect comprehension throughout
- Allows testing both НДВ and ДВ in varied contexts
- Mimics authentic reading with distributed grammar focus

**Pattern for creating dense cloze:**

- Add parallel actions: "я читав, підкреслював і робив нотатки"
- Expand with adverbs: "ретельно", "активно", "дуже"
- Add result clauses: "і нарешті зміг"

---

### Error-Correction (ALL 4 callouts REQUIRED)

**❌ INCOMPLETE (missing callouts) — AUDIT FAILS:**

```markdown
1. Я прочитав книгу дві години.
   > [!error] прочитав
   > [!answer] читав
```

**✅ CORRECT (all 4 callouts) — AUDIT PASSES:**

```markdown
1. Я прочитав книгу дві години.
   > [!error] прочитав
   > [!answer] читав
   > [!options] прочитав | читав | читаю | буду читати
   > [!explanation] Тривалість (дві години) вимагає НДВ: читав.
```

**Why all 4 callouts:**

- `[!error]`: Identifies the wrong word
- `[!answer]`: Provides the correction
- `[!options]`: Gives multiple-choice options (includes correct + wrong + distractors)
- `[!explanation]`: Explains WHY it's wrong (pedagogical value)

---

## Vocabulary Section Template (25+ items, 5 columns)

**❌ WRONG FORMAT (3 columns, no IPA) — AUDIT FAILS:**

```markdown
| Слово   | Переклад | Примітки                      |
| ------- | -------- | ----------------------------- |
| **вид** | aspect   | граматична категорія дієслова |
```

**✅ CORRECT FORMAT (5 columns with IPA) — AUDIT PASSES:**

```markdown
| Слово           | Вимова         | Переклад     | ЧМ         | Примітка                      |
| --------------- | -------------- | ------------ | ---------- | ----------------------------- |
| **вид**         | /wid/          | aspect       | ім. (ч.р.) | граматична категорія дієслова |
| **доконаний**   | /dɔˈkɔnɑnɪj/   | perfective   | прикм.     | вид, що виражає результат     |
| **недоконаний** | /nɛdɔˈkɔnɑnɪj/ | imperfective | прикм.     | вид, що виражає процес        |
| **процес**      | /prɔˈt͡sɛs/     | process      | ім. (ч.р.) | тривалість дії                |
| **результат**   | /rɛzulʲˈtɑt/   | result       | ім. (ч.р.) | завершення з наслідком        |

[... 20 more entries for total of 25+]
```

**Column specifications:**

1. **Слово**: Ukrainian word in bold
2. **Вимова**: IPA pronunciation (use [ipa.typeit.org](https://ipa.typeit.org))
3. **Переклад**: English translation
4. **ЧМ** (частина мови): Part of speech
   - `ім. (ч.р.)` = noun (masculine)
   - `ім. (ж.р.)` = noun (feminine)
   - `ім. (с.р.)` = noun (neuter)
   - `прикм.` = adjective
   - `дієсл. (ДВ)` = verb (perfective)
   - `дієсл. (НДВ)` = verb (imperfective)
5. **Примітка**: Usage note or context

**Why 5 columns with IPA:**

- B1 learners need pronunciation guidance
- Part of speech helps grammatical understanding
- Notes provide contextual depth
- Audit validates this exact format for B1+

---

## Common Pitfalls to Avoid

### 1. **Insufficient Word Count**

- ❌ Problem: Module has 897 words (need 1500+)
- ✅ Solution: Expand Пояснення section with more examples, cultural context, decision frameworks, common mistakes

### 2. **Quiz Questions Too Short**

- ❌ Problem: Questions 4-8 words (need 12-20)
- ✅ Solution: Add context ("Яке з наведених нижче..."), conditions, subordinate clauses

### 3. **Unjumble Sentences Too Simple**

- ❌ Problem: Sentences 7-9 words (need 12-16)
- ✅ Solution: Add subordinate clauses (коли, що, бо), prepositional phrases, adverbs

### 4. **Cloze Passage Too Sparse**

- ❌ Problem: 10 blanks (need 14+)
- ✅ Solution: Expand passage with parallel actions, result clauses, more context

### 5. **Wrong Vocabulary Format**

- ❌ Problem: 3 columns without IPA (need 5 columns with IPA)
- ✅ Solution: Add Вимова and ЧМ columns, use proper IPA notation

### 6. **Insufficient Engagement Boxes**

- ❌ Problem: 3 boxes (need 5+)
- ✅ Solution: Add 💡 Did You Know, 🎬 Pop Culture, 🌍 Real World, 🎯 Fun Fact

### 7. **Low Immersion**

- ❌ Problem: Grammar explained in English (85% Ukrainian)
- ✅ Solution: Use Ukrainian metalanguage for grammar explanations (90-95% target)

### 8. **Missing Error-Correction Callouts**

- ❌ Problem: Only `[!error]` and `[!answer]` provided
- ✅ Solution: Add `[!options]` and `[!explanation]` for every error-correction item

---

## Audit Validation

Before submitting, run:

```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/XX-your-module.md
```

**Target output:**

```
✅ Words: 1500+/1500
✅ Activities: 12/12
✅ Density: All > minimums
✅ Vocab: 25/25
✅ Pedagogy: Level-appropriate
✅ Immersion: 90-100%
✅ AUDIT PASSED.
```

---

## Example: M06 as Reference Implementation

See `curriculum/l2-uk-en/b1/06-aspect-complete-system.md` for a complete example that passes all audit gates.

**M06 Audit Results:**

- ✅ Words: 1516/1500
- ✅ Activities: 12/12 (all types)
- ✅ Density: Quiz 14 items, Cloze 14 blanks, Unjumble 8 items
- ✅ Vocab: 25/25 in correct 5-column format
- ✅ Engagement: 10 boxes
- ✅ Immersion: 97.2%
- ✅ Pedagogy: No violations

---

## Related Documents

- [B1 Curriculum Plan](../B1-CURRICULUM-PLAN.md) - Full B1 module specifications
- [Module Richness Guidelines](../MODULE-RICHNESS-GUIDELINES-v2.md) - Quality standards
- [Quick Reference: B1](claude_extensions/quick-ref/b1.md) - B1 requirements summary
- [Activity Markdown Reference](../ACTIVITY-MARKDOWN-REFERENCE.md) - Activity syntax patterns

---

**Last Updated:** 2025-12-22
**Based on:** M06 (Aspect - Complete System)
**Status:** ✅ Production Ready
