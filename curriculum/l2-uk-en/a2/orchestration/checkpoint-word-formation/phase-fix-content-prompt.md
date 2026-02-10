# Phase Fix-Content: Content-Only Fixes

> **You are Gemini, executing a targeted content fix.**
> **Your ONLY task: Fix the CONTENT file based on the review's Fix Plan.**
> **Do NOT output activities or vocabulary — only the fixed content.**

## Your Input

Read these files from disk:

**Review with Fix Plan** (your instructions — follow EVERY fix listed):
```
# Рецензія: Checkpoint: Word Formation

**Level:** A2 | **Module:** 44
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-10

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Plan hints used; Ukrainian terms appear in unjumble]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Clear structure, but marred by Latin typo and ambiguous activities. |
| 2 | Coherence | 9/10 | <7 | Logical flow from prefixes to suffixes to roots. |
| 3 | Relevance | 9/10 | <7 | Highly relevant for A2 expansion. |
| 4 | Educational | 8/10 | <7 | Good explanations, but "Mark the words" activity is pedagogically broken. |
| 5 | Language | 7/10 | <8 | Latin typo "napisав", clumsy tautology "словотвору слів", punctuation missing in unjumble. |
| 6 | Pedagogy | 6/10 | <7 | Activity count mismatches; Mark-the-words asks for morphemes but tool likely selects words. |
| 7 | Immersion | 8/10 | <6 | Good mix, though headings are English (standard for A2). |
| 8 | Activities | 6/10 | <7 | Technical failures (cloze typo, mark-words logic), count mismatches. |
| 9 | Richness | 9/10 | <6 | Content is dense and valuable. |
| 10 | Beginner Safety | 8/10 | <7 | Clear, not overwhelming despite the meta-topic. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural, but some robotic definitions in unjumble. |
| 12 | Linguistic Accuracy | 6/10 | <9 | "napisав", wrong POS/IPA for "читати". |

**Weighted Overall:** 7.5/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] (Typo "napisав", Cloze duplication, Mark-the-words logic)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Latin Script / Typo
- **Location**: Activities YAML / `mark-the-words` / `text`
- **Original**: "Український письменник napisав музичну п'єсу..."
- **Problem**: The word `napisав` mixes Latin `napis` with Cyrillic `ав` (or is fully Latin `napis` plus separate `ав`?). This is a critical text generation failure.
- **Fix**: Change to `написав`.

### Issue 2: Broken "Mark the Words" Logic
- **Location**: Activities YAML / `mark-the-words`
- **Original**: Answers: `при`, `ви`, `Читач`, `читання`, ... / Text: "Він прийшов..."
- **Problem**: The instruction asks to find "Word Parts" (prefixes/roots), but `mark-the-words` activities typically select **whole words**. You cannot click just the `при` in `прийшов` in most web interfaces. If the user clicks `прийшов` and the key is `при`, it will likely mark it wrong.
- **Fix**: Change activity type to `fill-in` or change instruction to "Click the **words** that contain prefixes/suffixes" and update answers to full words (`прийшов`, `вийшов`).

### Issue 3: Cloze Prefix Duplication
- **Location**: Activities YAML / `cloze` / Item "Зробити ще раз"
- **Original**: "Зробити ще раз = пере{переписати|написати|дописати}"
- **Problem**: The text before the brace is `пере`. If the correct answer is `переписати`, the result reads `перепереписати`.
- **Fix**: Change to "Зробити ще раз = {переписати|написати|дописати}" OR "Зробити ще раз = пере{писати|робити|читати}".

### Issue 4: Vocabulary Metadata Errors
- **Location**: Vocabulary YAML / Item `читати`
- **Original**: `pos: noun`, `gender: f`, `ipa: /t͡ʃɪtˈa/`
- **Problem**: `читати` is a VERB (infinitive), not a noun. It has no gender. IPA is missing the final syllable `/t͡ʃɪtˈatɪ/`.
- **Fix**: `pos: verb`, remove `gender`, fix IPA to `/t͡ʃɪtˈatɪ/`.

### Issue 5: Missing Activity Items
- **Location**: Activities YAML
- **Problem**: Plan requires 12 items for `fill-in`, 8 for `error-correction`, 8 for `unjumble`.
- **Actual**: `fill-in` (8), `error-correction` (6), `unjumble` (6).
- **Fix**: Add missing items to meet the quota.

### Issue 6: Unjumble Grammar & Tautology
- **Location**: Activities YAML / `unjumble`
- **Original**: "Українська мова має дуже багату систему словотвору слів"
- **Problem**: "словотвору слів" is redundant (word-formation of words). Also missing punctuation in other items (`...слів щоб...`).
- **Fix**: Remove `слів` -> "...систему словотвору". Add commas: "...корені слів, щоб...".

### Issue 7: Ambiguous Fill-in
- **Location**: Activities YAML / `fill-in` / Item 1
- **Original**: "Він [___] до класу вчасно." (Options: прийшов, вийшов, увійшов...)
- **Problem**: Without the English cue "(arrived)" used in the content, `увійшов` (entered) is also semantically correct.
- **Fix**: Add English context to the sentence: "Він [___] до класу вчасно. (arrived)" or ensure the prompt explicitly asks for "arrival".

## Strengths
- Excellent conceptual breakdown of word formation (Theory-First).
- "Myth Buster" about prefixes is engaging and culturally relevant.
- Clear distinction between `при-`/`ви-` and root families.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 6/10 → 9/10
**What to fix:**
1. Activities YAML `mark-the-words`: Fix `napisав` → `написав`.
2. Vocabulary YAML: Fix `читати` POS to `verb`, remove gender, fix IPA.
3. Activities YAML `cloze`: Fix `пере{переписати}` → `пере{писати}` or `{переписати}`.

### Activities: 6/10 → 9/10
**What to fix:**
1. `fill-in`: Add 4 items (Total 12). Add English cues to existing items to resolve ambiguity.
2. `error-correction`: Add 2 items (Total 8).
3. `unjumble`: Add 2 items (Total 8). Fix punctuation in answers (add commas/periods).
4. `mark-the-words`: Change strategy. Either ask to click WHOLE words (`answers: [прийшов, вийшов...]`) or change to a different activity type (e.g., `drag-text` to drag prefixes to roots).

### Language: 7/10 → 9/10
**What to fix:**
1. Activities YAML `unjumble`: Change "систему словотвору слів" → "систему словотвору".
2. Ensure unjumble target sentences have proper punctuation (commas before `що`, `яка`).

### Projected Overall After Fixes
(8+9+9+8+9+9+8+9+9+8+8+9) / 12 ≈ **8.6/10** (Wait, let's re-calc: 7.5 base. Fixing Activity/Lang/Acc -> ~9.0).
Weighted: (8*1.5 + 9 + 9 + 8*1.2 + 9*1.1 + 9*1.2 + 8 + 9*1.3 + 9*0.9 + 8*1.3 + 8 + 9*1.5) / 14 = **8.85**.
Close enough to pass, as mostly technical errors.

## Verification Summary
- Content lines read: 180
- Activity items checked: 60+
- Ukrainian sentences verified: 30+
- IPA transcriptions checked: 5
- Issues found: 7 (3 Critical)
- Naturalness score recommendation: 8/10

## Verdict
**FAIL**

Blocking issues:
1.  **Latin script typo** in Ukrainian text (`napisав`).
2.  **Pedagogically broken activity** (`mark-the-words` asking for substrings).
3.  **Vocabulary metadata error** (verb labeled as noun).
4.  **Activity count mismatches** against plan.
```

**Current content** (the file you are fixing):
```
# Checkpoint - Word Formation

## Огляд

**Вітаємо на контрольному етапі!** Ви успішно пройшли шлях вивчення основ словотвору. Word formation (словотвір) is one of the most powerful tools in Ukrainian. It allows you to expand your vocabulary exponentially by recognizing patterns rather than memorizing every single word as a unique entity.

Українська мова має дуже багату та логічну систему словотвору. Знання того, як корінь, префікс та суфікс взаємодіють між собою, дає вам "лінгвістичний рентген" — здатність бачити структуру слова та розуміти його значення, навіть якщо ви бачите його вперше.

**Skills tested in this checkpoint:**
1. **Verb Prefixes** - Mastery of direction (при-, ви-, пере-) and aspectual changes.
2. **Noun Suffixes** - Formation of actions (-ння), qualities (-ість), and agents (-ач, -ар).
3. **Adjective Suffixes** - Understanding relational (-ний), material (-овий), and nationality (-ський) markers.
4. **Root Families** - Recognizing core meanings across different parts of speech (ход-, пис-, бач-).

> У цьому модулі ми систематизуємо ваші знання та підготуємо вас до активного використання цих інструментів у мовленні.

---

## Skill 1: Verb Prefixes

**Can you use prefixes to change verb meaning?**

In Ukrainian, a prefix (префікс) is not just a grammatical marker; it is a "semantic compass" that points to the direction or nature of an action.

### Model: Direction and Logic Prefixes

> **при-** = arrival, movement toward: прийти (to arrive)
> **ви-** = exit, movement out of: вийти (to go out)
> **у-/в-** = entering: увійти (to enter)
> **пере-** = crossing or repeating: перейти (to cross), переписати (to rewrite)
> **від-** = moving away from or opening: відійти (to step away), відкрити (to open)
> **роз-** = spreading, unfolding, or separating: розійтися (to disperse)

**Detailed patterns:**

| Prefix | Primary Meaning | Example | Context |
|--------|-----------------|---------|---------|
| **при-** | Arrival / Attachment | прийти, приїхати | Coming home or to class |
| **ви-** | Exit / Outward | вийти, винести | Leaving a room or taking out trash |
| **у-/в-** | Entering / Into | увійти, в'їхати | Entering a building or a city |
| **пере-** | Across / Re-doing | перейти, переробити | Crossing a street or fixing a mistake |
| **від-** | Away / Detachment | відійти, відсунути | Stepping back or moving something away |
| **на-** | Onto / Accumulation | написати, наклеїти | Writing something down or sticking a label |
| **з-/с-** | Down / Together | зійти, скласти | Coming down or putting things together |

### Practice: Choose the Right Prefix

1. Він **при**йшов до класу вчасно. (arrived)
> [!solution] Перевірити
> **прийшов** — arrival = при-

2. Вона **ви**йшла з кімнати дуже швидко. (exited)
> [!solution] Перевірити
> **вийшла** — exit = ви-

3. Я **пере**писав цей текст ще раз. (rewrote/redid)
> [!solution] Перевірити
> **переписав** — re-do = пере-

4. Ми **пере**йшли через старий міст. (crossed)
> [!solution] Перевірити
> **перейшли** — across = пере-

5. Сонце **зі**йшло рано вранці. (rose/came up)
> [!solution] Перевірити
> **зійшло** — movement up/out = з- (with euphonic і)

6. Ми **в**війшли до музею. (entered)
> [!solution] Перевірити
> **ввійшли** — entering = в- (variant of у-)

7. Він **від**ійшов від вікна. (stepped away)
> [!solution] Перевірити
> **відійшов** — movement away = від-

8. Студент **на**писав емейл професору. (wrote down/wrote)
> [!solution] Перевірити
> **написав** — completion of writing = на-

### Self-Check

- Do you distinguish between **при-** (arrival) and **ви-** (exit)?
- Can you use **пере-** for both «across» and «re-do»?
- Do you understand that **від-** implies moving away or opening a boundary?

> [!myth-buster] 🔍 Myth Buster
>
> **Myth:** «Ukrainian prefixes are just like those in other Slavic languages.»
>
> **Truth:** While Slavic languages share a common heritage, Ukrainian has unique prefixal nuances and phonological rules. For example, the Ukrainian **від-** (away) preserves the ancient dental 'д', and forms like **відійти** showcase the authentic Ukrainian "soft і" (ікавізм), which is a hallmark of the language's development since the 12th century.

> [!history-bite] 📜 History Bite
>
> **Prefixes as a tool of resilience!** During the 19th century, when the Ukrainian language faced severe restrictions under the Ems Ukaz, writers used word formation to create new terms and preserve the language's richness. Ivan Franko, a giant of Ukrainian literature, was a master of prefixation, using combinations like **роз-**, **пере-**, and **від-** to convey complex philosophical and emotional states that were uniquely Ukrainian.

---

## Skill 2: Noun Suffixes

**Can you form nouns from verbs and adjectives?**

Suffixes (суфікси) in Ukrainian often determine the "category" of a noun—whether it is an action, a quality, or a person who performs a task.

### Model: Suffixes That Create Nouns

> **-ння** = verbal noun (action): читати → **читання** (reading/the act of reading)
> **-ість** = abstract noun (quality): сміливий → **сміливість** (boldness/courage)
> **-ач / -ник / -ар** = agent noun (person): читати → **читач** (reader)

**Productive Patterns:**

| Suffix | Function | Example | Base Word |
|--------|----------|---------|-----------|
| **-ння** | Action/Result | писання, навчання | писати, вчити |
| **-ість** | Quality/State | важливість, радість | важливий, радий |
| **-ач** | Person (agent) | викладач, слухач | викладати, слухати |
| **-ар / -яр** | Profession/Skill | лікар, школяр, кухар | ліки, школа, кухня |
| **-тель** | Person (doer) | вчитель, вихователь | вчити, виховувати |

### Practice: Form the Noun

1. говорити (to speak) → **говоріння** (speaking)
> [!solution] Перевірити
> **говоріння** — verb + -ння = verbal noun (action)

2. сміливий (brave) → **сміливість** (bravery)
> [!solution] Перевірити
> **сміливість** — adjective + -ість = abstract quality

3. слухати (to listen) → **слухач** (listener)
> [!solution] Перевірити
> **слухач** — verb + -ач = agent noun (person)

4. лікувати (to treat/heal) → **лікар** (doctor)
> [!solution] Перевірити
> **лікар** — root + -ар = professional agent

5. малювати (to draw) → **малювання** (drawing)
> [!solution] Перевірити
> **малювання** — verb + -ння = verbal noun (action)

6. чесний (honest) → **чесність** (honesty)
> [!solution] Перевірити
> **чесність** — adjective + -ість = abstract quality

7. вчити (to teach) → **вчитель** (teacher)
> [!solution] Перевірити
> **вчитель** — verb + -тель = person (doer)

8. кухня (kitchen) → **кухар** (cook)
> [!solution] Перевірити
> **кухар** — noun + -ар = professional agent

### Self-Check

- Can you form neuter verbal nouns with **-ння**? (навчання, малювання)
- Can you form feminine abstract nouns with **-ість**? (можливість, чесність)
- Do you know that **-ач** and **-ар** suffixes create masculine nouns for people?

> [!tip] 🎯 Pro Tip: Suffix-Gender Link
>
> Memorizing a suffix also means memorizing the gender!
> - **-ння** = always **neuter** (воно)
> - **-ість** = always **feminine** (вона)
> - **-ач / -ар** = always **masculine** (він)
>
> This shortcut will help you with case endings later!

---

## Skill 3: Adjective Suffixes

**Can you form adjectives from nouns?**

### Model: Suffixes That Create Adjectives

> **-ний** = general relationship: музика → **музичний** (musical)
> **-овий / -евий** = material, type, or possession: слово → **словниковий** (vocabulary-related)
> **-ський** = origin, nationality, or place: Україна → **український** (Ukrainian)

**Key Suffixes:**

| Suffix | Meaning | Examples |
|--------|---------|----------|
| **-ний** | General relation | цікавий, корисний, музичний |
| **-овий** | Material / Character | кольоровий, паперовий, лісовий |
| **-ський** | Place / Identity | київський, студентський, морський |

### Practice: Form the Adjective

1. Київ → **київський**
> [!solution] Перевірити
> **київський** — place + -ський

2. музика → **музичний**
> [!solution] Перевірити
> **музичний** — noun + -ний

3. колір → **кольоровий**
> [!solution] Перевірити
> **кольоровий** — noun + -овий

4. Європа → **європейський**
> [!solution] Перевірити
> **європейський** — place + -ський

5. студент → **студентський**
> [!solution] Перевірити
> **студентський** — person + -ський

6. ліс → **лісовий**
> [!solution] Перевірити
> **лісовий** — noun + -овий

7. папір → **паперовий**
> [!solution] Перевірити
> **паперовий** — material + -овий

8. море → **морський**
> [!solution] Перевірити
> **морський** — place + -ський

### Self-Check

- Can you form nationality/place adjectives with **-ський**?
- Do you use **-ний** for general abstract or functional relations?
- Do you recognize **-овий** as a marker for material or specific types?

> [!note] 📝 Word Formation Memory Aid
>
> Remember: **-ський** is your "location and identity" suffix. If it belongs to a city, a country, or a group of people (like students), use **-ський**.
> - Львів → львівський
> - Польща → польський
> - Студент → студентський

---

## Skill 4: Root Families

**Can you recognize related words from the same root?**

The root (корінь) is the semantic heart of the word. Once you identify the root, you can decipher dozens of related words across different parts of speech.

### Model: Root = Core Meaning

> **Root ход- / хід-** (walk / go / movement):
> вхід (entrance), вихід (exit), перехід (crossing), пішохід (pedestrian), ходити (to walk), прийти (to arrive).

> **Root пис-** (write):
> писати (to write), написати (to write down), письменник (writer), писання (writing), переписати (to rewrite).

> **Root бач-** (see):
> бачити (to see), побачення (a date/meeting), передбачити (to foresee), бачення (vision).

**Common Root Families:**

| Root | Core Meaning | Family Words |
|------|--------------|--------------|
| **ход-** | movement | вхід, вихід, поїзд, хід |
| **пис-** | writing | писати, письменник, лист |
| **бач-** | vision | бачити, побачення, бачення |
| **слух-** | hearing | слухати, слухач, послуга |
| **мов-** | speech | мова, розмова, промовець |
| **чит-** | reading | читати, читач, читанка |

### Practice: Identify the Core Meaning

1. вхід, вихід, перехід — what is the shared concept?
> [!solution] Перевірити
> **ход- / хід-** — All relate to the act of walking or moving through a space.

2. письменник, писання, переписати — what is the shared concept?
> [!solution] Перевірити
> **пис-** — All relate to the act of writing or creating text.

3. слухач, слухати, послухати — what is the shared concept?
> [!solution] Перевірити
> **слух-** — All relate to the sense of hearing or listening.

4. Український письменник написав цікаву книгу. — which words share a root?
> [!solution] Перевірити
> **письменник** and **написав** — both share the root **пис-**.

5. мова, розмова, перемовини — what is the shared concept?
> [!solution] Перевірити
> **мов-** — All relate to speech or language.

6. читати, читанка, читач — what is the shared concept?
> [!solution] Перевірити
> **чит-** — All relate to reading.

### Self-Check

- Can you strip away prefixes and suffixes to find the root?
- Do you recognize vowel shifts (like **о/і** in **ход-/хід-**)?
- Can you guess the meaning of a new compound word if you know its root?

> [!note] 📝 Root Family Practice Strategy
>
> When you encounter a long word, follow these steps:
> 1. **Identify the prefix:** Is there a direction marker (при-, ви-, пере-)?
> 2. **Identify the suffix:** Does it tell you the category (person, action, quality)?
> 3. **Find the root:** What is the core syllable? Does it remind you of a verb or noun you already know?
>
> *Example:* **Передбачення** = перед (before) + бач (see) + ення (action) = Foreseeing/Prediction.

---

## Integration Challenge

Analyze these complex words by breaking them into their logical parts (Prefix + Root + Suffix):

1. **передбачити** (to foresee)
> [!solution] Перевірити
> **перед** (prefix: before) + **бач** (root: see) + **ити** (infinitive suffix)

2. **письменник** (writer)
> [!solution] Перевірити
> **пис** (root: write) + **мен** (inter-suffix) + **ник** (agent suffix)

3. **важливість** (importance)
> [!solution] Перевірити
> **важлив** (base: important) + **ість** (suffix: quality)

4. **український** (Ukrainian)
> [!solution] Перевірити
> **україн** (root/base: Ukraine) + **ський** (suffix: identity/nationality)

5. **читання** (reading)
> [!solution] Перевірити
> **чит** (root: read) + **ання** (suffix: action)

6. **перехід** (crossing)
> [!solution] Перевірити
> **пере** (prefix: across) + **хід** (root: walk/move)

7. **приїзд** (arrival)
> [!solution] Перевірити
> **при** (prefix: arrival) + **їзд** (root: travel/drive)

8. **робітник** (worker)
> [!solution] Перевірити
> **робіт** (root: work) + **ник** (suffix: agent)

9. **безкоштовний** (free of charge)
> [!solution] Перевірити
> **без** (prefix: without) + **кошт** (root: cost) + **овний** (adjective suffix)

10. **неможливий** (impossible)
> [!solution] Перевірити
> **не** (prefix: negation) + **мож** (root: can/able) + **ливий** (adjective suffix)

11. **вихід** (exit)
> [!solution] Перевірити
> **ви** (prefix: out) + **хід** (root: walk/move)

12. **школяр** (schoolboy)
> [!solution] Перевірити
> **школ** (root: school) + **яр** (suffix: person/agent)

> [!warning] ⚠️ Common Mistake
>
> Watch out for vowel shifts! The root **ход-** often changes to **хід-** in nouns (хід, вхід, вихід), but stays **ход-** in verbs (ходити, переходити). This is a natural phonetic feature of Ukrainian called "чергування" (alternation).

---

# Підсумок

| Skill | Pattern / Marker | Function | Example |
|-------|------------------|----------|---------|
| **Prefixes** | при-, ви-, пере- | Change direction/nature | прийти, вийти |
| **Noun Suffixes** | -ння, -ість, -ач | Define category (action/quality) | читання, радість |
| **Adj Suffixes** | -ний, -овий, -ський | Define relationship/origin | музичний, київський |
| **Roots** | пис-, ход-, бач- | Provide core meaning | письменник, вихід |

> 💡 **Лінгвістичний Інсайт**
>
> Словотвір — це "конструктор" мови. Якщо ви знаєте 50 коренів та 10 префіксів/суфіксів, ви потенційно знаєте 5000 слів!
> *Word formation is the "Lego set" of language. If you know 50 roots and 10 prefixes/suffixes, you potentially know 5000 words!*

---

## Need More Practice?

Щоб закріпити знання, спробуйте знайти 5 нових слів у словнику та проаналізуйте їхню структуру. Використовуйте слова зі списку (vocabulary sidecar) для створення власних речень, звертаючи увагу на те, як суфікси змінюють значення слова.
```

**Plan file** (source of truth for scope — check if fixes align):
```
module: a2-44
level: A2
sequence: 44
slug: checkpoint-word-formation
version: '2.0'
title: 'Checkpoint: Word Formation'
subtitle: Review and Mastery Assessment
content_outline:
- section: Огляд
  words: 95
  points:
  - Skills overview
  - Checkpoint goals
- section: 'Skill 1: Verb Prefixes'
  words: 234
  points:
  - Direction prefixes
  - Practice exercises
  - Myth Buster and History
- section: 'Skill 2: Noun Suffixes'
  words: 156
  points:
  - Verbal noun -ння
  - Abstract noun -ість
  - Agent noun -ач
- section: 'Skill 3: Adjective Suffixes'
  words: 117
  points:
  - General relation -ний
  - Material/type -овий
  - Place/nation -ський
- section: 'Skill 4: Root Families'
  words: 256
  points:
  - Core root meaning
  - Root recognition practice
  - Extended root families
- section: Integration Challenge
  words: 95
  points:
  - Word analysis practice
  - Common mistakes
- section: Підсумок
  words: 50
  points:
  - Summary table
  - Linguistic insight
word_target: 1000
vocabulary_hints:
  required:
  - корінь (root)
  - префікс (prefix)
  - суфікс (suffix)
  - слово (word)
  - утворення (formation)
  - значення (meaning)
  - помилка (error)
  - правильний (correct)
  recommended:
  - морфема (morpheme)
  - аналіз (analysis)
  - синтез (synthesis)
  - похідний (derivative)
activity_hints:
- type: quiz
  focus: Word formation comprehensive
  items: 12
- type: fill-in
  focus: Create correct forms
  items: 12
- type: error-correction
  focus: Fix formation errors
  items: 8
- type: match-up
  focus: Root families and meanings
  items: 12
- type: group-sort
  focus: Sort by suffix types
  items: 12
- type: cloze
  focus: Word formation in context
  items: 12
- type: unjumble
  focus: Word formation sentences
  items: 8
- type: translate
  focus: Form equivalents
  items: 8
focus: checkpoint
pedagogy: TTT
prerequisites:
- a2-43 (WF Mastery)
connects_to:
- a2-45 (Food and Cooking)
objectives:
- Demonstrate confidence in identifying root families
- Deduce meaning using morphological clues
- Form words using correct prefixes and suffixes
- Correct common word formation errors
grammar:
- Word formation comprehensive review
- Root families review
- Prefix/suffix application
register: розмовний
phase: A2.4 [Word Formation]

```

**Research notes** (reference for factual accuracy):
```
# Research Notes: A2 M44 Checkpoint - Word Formation

**Track**: l2-uk-en
**Module**: checkpoint-word-formation
**Level**: A2
**Researched**: 2026-02-08

## 1. Grammar: State Standard 2024 Reference

According to the **Державний стандарт української мови як іноземної (2024)**, word formation (Словотвір) requirements for Level A2 are outlined in **Catalog V (Зміст мовної компетентності), Section 4.3**:

> **4.3. Словотвір.**
> 4.3.1. Ступені порівняння якісних прикметників: проста форма вищого ступеня: солодший, важливіший; проста форма найвищого ступеня: найсолодший, найважливіший...
> 4.3.2. Видові пари дієслів: робити – зробити, ділити – поділити, писати – написати, виходити – вийти, забувати – забути.

*Note: While the standard formally places noun/adjective/adverb formation suffixes in Level B1 (§4.3.3–4.3.7), this curriculum introduces them in A2 to build a richer vocabulary through pattern recognition, reflecting the "Theory-First" approach.*

## 2. Vocabulary Frequency

At the A2 level, focus is on high-frequency roots and productive patterns that expand communicative range without overwhelming the student.

### High-Frequency Bases and Derivatives
- **Verbs of Motion (Prefixation):**
  - **іти/їхати** → *прийти/приїхати* (arrival), *вийти/виїхати* (exit), *перейти/переїхати* (cross).
- **Agent/Occupation Suffixes:**
  - **-ар/-яр:** *лікар* (doctor), *школяр* (schoolboy), *кухар* (cook).
  - **-ач:** *викладач* (teacher), *читач* (reader).
  - **-тель:** *вчитель* (teacher).
- **Diminutive Suffixes (Highly Productive):**
  - **-ик/-ок:** *стіл → столик*, *дім → будинок*.
  - **-к(а):** *рука → ручка*, *книга → книжка*, *вода → водічка*.
- **Abstract/Action Nouns:**
  - **-ння/-ття:** *читання* (reading), *навчання* (studying), *життя* (life).

### Common Collocations
- *робити запис* (to make a record/note)
- *дати відповідь* (to give an answer — from *відповідати*)
- *місце навчання* (place of study)

## 3. Cultural Hook

1. **Diminutives as Emotional Language:** In Ukrainian, diminutives (*пестливі слова*) are not just for children or "small" things. They are a vital tool for expressing intimacy, politeness, and affection (*ласкавість*). Calling someone "Оленка" or asking for "кавуся" (coffee) creates a warm, hospitable atmosphere. This is a distinctive feature of the Ukrainian "soul" and linguistic etiquette.
2. **Surnames and Identity:** Many Ukrainian surnames are living examples of word formation patterns. Suffixes like **-енко** (son of, e.g., Шевченко) and **-ук/-юк** (Western Ukrainian origin, e.g., Бондарчук) reflect the historical development of the language and family structures.

## 4. Pedagogical Notes

- **Root Identification:** Students often struggle with vowel shifts in the root (*чергування*) during word formation (e.g., *стіл* → *столик*, *кіт* → *котик*). It is helpful to present these as "logical shifts" for ease of pronunciation.
- **Gender Consistency:** Nouns formed with specific suffixes often have a fixed gender. For example, all nouns ending in **-ння** (derived from verbs) are neuter. Teaching the suffix and the gender as a package reduces errors.
- **Prefix Meaning vs. Aspect:** Students should distinguish between prefixes that purely change aspect (*писати* → *написати*) and those that add lexical meaning (*писати* → *виписати* - to write out/extract).
- **Comparison with English:** English often uses separate words or adjectives (e.g., "little table"), whereas Ukrainian internalizes the meaning into the word structure (*столик*).

## 5. Scope Boundaries

### In Scope
- **Cases:** All 6 main cases (Nominative, Accusative, Locative, Genitive, Dative, Instrumental) and the **Vocative** (*Кличний відмінок*).
- **Aspect:** Basic imperfective/perfective pairs.
- **Prefixes:** Primary motion verb prefixes (*при-, ви-, пере-, за-, по-, в-, з-*) and aspectual prefixes (*на-, з-, по-*).
- **Suffixes:** Basic agentive (-ар, -ач), diminutive (-ик, -к-), and deverbal (-ння).
- **Adjectives:** Comparative and Superlative forms.

### Out of Scope
- **Participles & Gerunds:** Forms like *читаючий* or *прочитавши* are B1/B2 level.
- **Complex Suffixes:** Collective nouns (*-ство*, e.g., *козацтво*) or specialized scientific suffixes.
- **Passive Voice:** Complex passive constructions (though simple reflexive forms like *відчиняється* may be familiar).
- **Archaic/Poetic Word Formation:** Rare suffixes used in folklore but not in daily life.

```

## Your Task

1. Read the review file completely — focus on:
   - **"Critical Issues Found"** section
   - **"Fix Plan to Reach 9/10"** section
   - **"Ukrainian Language Issues"** table
2. Apply ONLY content-related fixes (ignore activity/vocabulary fixes)
3. Output the COMPLETE fixed content file

### Rules

1. **Apply EVERY content fix** from the Fix Plan — do not skip any
2. **Scope your changes** — change/add ONLY what the Fix Plan specifies for content
3. **Adding content IS expected** — if the Fix Plan says "add a table", "add examples", "expand section", you MUST do it
4. **Preserve structure** — keep the same H2/H3 headings
5. **Preserve voice** — do not change the writing style of unflagged content
6. **If a fix is ambiguous**, choose the option that matches the plan file
7. **Never output "no changes needed"** — if the Fix Plan lists content fixes, there ARE changes to make

### What NOT to Do

- Do NOT output activities or vocabulary — this phase is CONTENT ONLY
- Do NOT rewrite the entire file — only change what the Fix Plan says
- Do NOT add engagement boxes unless the Fix Plan says to
- Do NOT request skills, delegate to Claude, or skip fixes
- Do NOT add commentary — just output the fixed content

## Output Format

**CRITICAL: Output the COMPLETE fixed content between these delimiter lines.**

===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===

**After the content, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. Line {N}: {what changed} — {which review issue this addresses}
2. Section "{name}": {what changed} — {which review issue}

## Fixes NOT Applied (explain why)

- {If any content fix was unclear or contradictory, explain here}
===CHANGES_END===

## Boundaries

- Do NOT output activities or vocabulary sections
- Do NOT fabricate fixes — only apply what the review specified
- Do NOT change the module's pedagogical approach or structure
- If you cannot apply a fix, explain why in the "Fixes NOT Applied" section
