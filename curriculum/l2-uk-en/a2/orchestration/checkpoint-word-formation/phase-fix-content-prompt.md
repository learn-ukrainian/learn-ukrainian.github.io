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

**Вітаємо на контрольному етапі!** Ви успішно пройшли шлях вивчення основ українського словотвору. Word formation (словотвір) is one of the most powerful tools in the Ukrainian language. It allows you to expand your vocabulary exponentially by recognizing patterns and logical structures rather than simply memorizing every single word as an isolated lexical unit. At this stage of your A2 journey, mastering these building blocks is what separates a beginner from a confident, independent learner.

Українська мова має надзвичайно розгалужену та логічну систему **словотвору**. Знання того, як корінь, префікс та суфікс взаємодіють між собою, надає вам своєрідний «лінгвістичний рентген» — унікальну здатність бачити внутрішню структуру слова та розуміти його **значення**, навіть якщо ви бачите його вперше. Кожна **морфема** (найменша значуща одиниця мови) несе своє специфічне смислове навантаження. Використовуючи **аналіз** (розкладання складного слова на частини) та **синтез** (творення нових слів з уже відомих елементів), ви зможете впевнено розшифровувати складні тексти та точніше висловлювати власні думки.

У цьому контрольному модулі ми не просто перевіримо ваші знання, а систематизуємо їх, щоб перетворити теоретичне розуміння на активну мовленнєву навичку. Ми зосеведемося на тому, як морфологічні зміни впливають на частину мови та відтінки значень, готуючи вас до переходу на рівень B1.

**Skills tested in this checkpoint:**
1. **Verb Prefixes** - Mastery of direction (при-, ви-, пере-) and aspectual changes.
2. **Noun Suffixes** - Formation of actions (-ння), qualities (-ість), and agents (-ач, -ар).
3. **Adjective Suffixes** - Understanding relational (-ний), material (-овий), and identity (-ський) markers.
4. **Root Families** - Recognizing core meanings and logical shifts across different parts of speech (ход-, пис-, бач-).

---

## Skill 1: Verb Prefixes

**Can you use prefixes to change verb meaning?**

In Ukrainian, a prefix (префікс) is not just a grammatical marker; it is a «semantic compass» that points to the direction or nature of an action. Whether you are arriving at a destination, crossing a boundary, or finishing a task, the prefix tells the listener exactly what is happening before you even name the core action. Understanding these directionals is key to navigating physical space and abstract time.

### Model: Direction and Logic Prefixes

> **при-** = arrival, movement toward: прийти (to arrive)
> **ви-** = exit, movement out of: вийти (to go out)
> **у-/в-** = entering: увійти (to enter)
> **пере-** = crossing or repeating (re-doing): перейти (to cross), переписати (to write again), переробити (to do again)
> **від-** = moving away from or opening: відійти (to step away), відкрити (to open)
> **роз-** = spreading, unfolding, or separating: розійтися (to disperse)
> **на-** = completion of an action: написати (to finish writing)

**Semantic Opposites:**

| Prefix (Toward/In) | Meaning | Prefix (Away/Out) | Meaning |
|-------------------|---------|-------------------|---------|
| **при-** | Arrival | **від-** | Departure |
| **у- / в-** | Entering | **ви-** | Exiting |
| **на-** | Onto | **з-** | Off / Down |

> [!myth-buster]
> **Myth:** Every prefix creates a completely new word with a different meaning.
> **Fact:** While many prefixes change direction (like *вийти* vs *прийти*), some prefixes primarily serve to change the **aspect** of the verb (making it "perfective" or finished) without changing the core action. For example, **писати** (to write) and **написати** (to finish writing) describe the same action, but the prefix **на-** signals completion.

> [!history-bite]
> Did you know that most Ukrainian prefixes actually evolved from prepositions? This is why **в-** (into) looks like the preposition **в** (in), and **на-** (onto) looks like **на** (on). Their spatial logic is preserved in the verb structure!

### Practice: Choose the Right Prefix

1. Він **прийшов** до класу вчасно. (arrived)
> [!solution] Перевірити
> **прийшов** — arrival = при-

2. Вона **вийшла** з кімнати дуже швидко. (exited)
> [!solution] Перевірити
> **вийшла** — exit = ви-

3. Я **переписав** цей текст ще раз. (rewrote)
> [!solution] Перевірити
> **переписав** — re-do = пере- (Зверніть увагу: ми використовуємо корінь -писати, а не «пере-переписати»).

4. Ми **перейшли** через старий міст. (crossed)
> [!solution] Перевірити
> **перейшли** — across = пере-

5. Сонце **зійшло** рано вранці. (rose)
> [!solution] Перевірити
> **зійшло** — movement up/out = з- (with euphonic vowel і)

6. Ми **увійшли** до музею. (entered)
> [!solution] Перевірити
> **увійшли** — entering = у- (variant of в-)

7. Він **відійшов** від вікна. (stepped away)
> [!solution] Перевірити
> **відійшов** — movement away = від-

8. Студент **написав** емейл професору. (finished writing)
> [!solution] Перевірити
> **написав** — completion of writing = на-

9. Ми **зайшли** до кафе на каву. (dropped in)
> [!solution] Перевірити
> **зайшли** — short stop / drop-in = за-

10. Автобус **від'їхав** від зупинки. (drove away)
> [!solution] Перевірити
> **від'їхав** — departure / away = від-

11. Він **зійшов** зі сходів дуже обережно. (came down)
> [!solution] Перевірити
> **зійшов** — movement down = з- (with euphonic і)

12. Птах **вилетів** з вікна. (flew out)
> [!solution] Перевірити
> **вилетів** — outward movement = ви-

13. Він **переробив** домашнє завдання ще раз. (redid)
> [!solution] Перевірити
> **переробив** — prefix пере- denotes repetition of the action.

14. Я **перечитав** статтю, щоб краще її зрозуміти. (read again)
> [!solution] Перевірити
> **перечитав** — repetition of reading. (Зверніть увагу на кому перед «що» або «щоб»!).

---

## Skill 2: Noun Suffixes

**Can you form nouns from verbs and adjectives?**

Suffixes (суфікси) in Ukrainian often determine the «category» of a noun—whether it is an action, a quality, or a person who performs a task. By learning just one root and a few suffixes, you can unlock a whole family of words.

### Model: Suffixes That Create Nouns

> **-ння** = verbal noun (action): читати (verb) → **читання** (reading, noun)
> **-ість** = abstract noun (quality): сміливий → **сміливість** (bravery)
> **-ач / -ник / -ар** = agent noun (person): читати → **читач** (reader)

**Productive Patterns:**

| Suffix | Function | Example | Base Word |
|--------|----------|---------|-----------|
| **-ння** | Action/Result (Neuter) | писання, навчання | писати, вчити |
| **-ість** | Quality/State (Feminine) | важливість, радість | важливий, радий |
| **-ач** | Person / Agent (Masculine) | викладач, слухач | викладати, слухати |
| **-ар / -яр** | Profession / Skill | лікар, кухар, школяр | ліки, кухня, школа |
| **-тель** | Person / Instructor | вчитель, вихователь | вчити, виховувати |

> [!cultural]
> **Diminutives and Warmth**
> Ukrainian is famous for its productive diminutive suffixes like **-ик** (for masculine) and **-к-** (for feminine). While they can mean "small" (e.g., *стіл* → *столик*), they are most often used to express warmth, politeness, and hospitality. Calling a coffee *кавуся* or a friend *Оленка* creates a friendly atmosphere (*затишок*) that is central to Ukrainian social interaction.

### Subsection: Diminutives (Пестливі слова)

In Ukrainian, diminutive suffixes are highly productive. They shift the emotional register of a word, making it "softer" or more affectionate.

*   **-ик / -ок** (Masculine): *кіт* → *котик*, *дім* → *будинок* (house), *стіл* → *столик*.
*   **-к- / -иц-** (Feminine): *книга* → *книжка*, *вода* → *водичка*, *сестра* → *сестричка*.
*   **-ц- / -чк-** (Neuter): *вікно* → *віконце*, *сонце* → *сонечко*.

> [!history-bite]
> Many Ukrainian surnames are living examples of word formation! Suffixes like **-енко** (meaning "son of", like *Шевченко*) and **-ук** or **-юк** (common in Western Ukraine, like *Бондарчук*) tell the story of a person's ancestry through these productive suffixes.

### Practice: Form the Noun

1. говорити (to speak) → **говоріння** (speaking)
> [!solution] Перевірити
> **говоріння** — verb + -ння (Note: all -ння nouns are Neuter).

2. сміливий (brave) → **сміливий** (brave) → **сміливість** (bravery)
> [!solution] Перевірити
> **сміливість** — adjective + -ість (Note: all -ість nouns are Feminine).

3. слухати (to listen) → **слухач** (listener)
> [!solution] Перевірити
> **слухач** — verb + -ач.

4. лікувати (to treat/heal) → **лікар** (doctor)
> [!solution] Перевірити
> **лікар** — root + -ар.

5. малювати (to draw) → **малювання** (drawing)
> [!solution] Перевірити
> **малювання** — verb + -ння.

6. чесний (honest) → **чесність** (honesty)
> [!solution] Перевірити
> **чесність** — adjective + -ість.

7. вчити (to teach) → **вчитель** (teacher)
> [!solution] Перевірити
> **вчитель** — verb + -тель.

8. кухня (kitchen) → **кухар** (cook)
> [!solution] Перевірити
> **кухар** — noun + -ар.

9. знати (to know) → **знання** (knowledge)
> [!solution] Перевірити
> **знання** — verb + -ння.

10. викладати (to lecture/teach) → **викладач** (lecturer)
> [!solution] Перевірити
> **викладач** — verb + -ач.

11. мудрий (wise) → **мудрість** (wisdom)
> [!solution] Перевірити
> **мудрість** — adjective + -ість.

12. писати (to write) → **писання** (the act of writing)
> [!solution] Перевірити
> **писання** — verb + -ння.

13. працювати (to work) → **працівник** (worker / employee)
> [!solution] Перевірити
> **працівник** — verb + -ник.

14. радіти (to rejoice) → **радість** (joy)
> [!solution] Перевірити
> **радість** — verb-related root + -ість. (Note: all nouns in -ість are Feminine).

---

## Skill 3: Adjective Suffixes

**Can you form adjectives from nouns?**

### Model: Suffixes That Create Adjectives

Ukrainian adjectives are formed using specific suffixes that indicate a relationship to a noun, a material, or an origin.

> **-ний** = general relationship: музика → **музичний** (musical)
> **-овий / -евий** = material or type: слово → **словниковий** (vocabulary-related)
> **-ський** = origin, identity, or place: Україна → **український** (Ukrainian)

**Common Patterns:**

| Suffix | Function | Example | Base Word |
|--------|----------|---------|-----------|
| **-ний** | General relation | нічний, залізний | ніч, залізо |
| **-овий** | Material / Type | кольоровий, лісовий | колір, ліс |
| **-ський** | Place / Origin | київський, одеський | Київ, Одеса |
| **-яний** | Material (Special) | дерев'яний, скляний | дерево, скло |

### Practice: Form the Adjective

1. Київ (Kyiv) → **київський** (Kyivan / from Kyiv)
2. музика (music) → **музичний** (musical)
3. колір (color) → **кольоровий** (colored / colorful)
4. Європа (Europe) → **європейський** (European)
5. студент (student) → **студентський** (student-related)
6. ліс (forest) → **лісовий** (forest-related)
7. папір (paper) → **паперовий** (paper / made of paper)
8. море (sea) → **морський** (marine / sea-related)
9. дерево (wood/tree) → **дерев'яний** (wooden)
10. сонце (sun) → **сонячний** (sunny) (Зверніть увагу на чергування **ц / ч**).
11. ніч (night) → **нічний** (nightly / at night)
12. Одеса (Odesa) → **одеський** (Odesan / from Odesa)
13. літо (summer) → **літній** (summer / summery)
14. зима (winter) → **зимовий** (winter / wintery)

---

## Skill 4: Root Families

**Can you recognize related words from the same root?**

The root (**корінь**) is the semantic heart of the word. Identifying it allows you to decipher the core meaning of related words across different parts of speech, even if they have different prefixes or suffixes.

### Model: The "Word Tree" (Root = Core Meaning)

Consider the root **ход- / хід-** (related to movement on foot). From this one core, we can build a massive "family" of words:

*   **ход**ити (verb: to walk)
*   **вхід** (noun: entrance)
*   **вихід** (noun: exit)
*   **перехід** (noun: crossing)
*   **прихід** (noun: arrival)
*   **захід** (noun: sunset / the West)

> [!tip]
> **Whole-Word Recognition**
> Коли ви аналізуєте текст, зосередьтеся на ідентифікації **цілого слова**, яке містить конкретний корінь або префікс. Зверніть увагу на чергування голосних **о / і** у корені (**ход-** стає **хід-**). Це дуже поширене явище в українському словотворі для полегшення вимови у закритих складах.

### Practice: Identify Word Families

1. Визначте **цілі слова**, що мають спільний корінь **ход- / хід-**: (вхід, вихід, перехід, поїзд).
> [!solution] Перевірити
> **вхід, вихід, перехід** relate to movement. Note the vowel shift (о/і).

2. Визначте **цілі слова**, що мають спільний корінь **пис-**: (письменник, писання, переписати, папір).
> [!solution] Перевірити
> **письменник, писання, переписати** relate to writing.

3. Яке поняття об'єднує слова **слухач, слухати, послухати**?
> [!solution] Перевірити
> Слух (the sense of hearing).

4. Визначте **цілі слова** зі спільним коренем у реченні: «Український письменник написав музичну п'єсу».
> [!solution] Перевірити
> **письменник** та **написав** (корінь **пис-**).

5. Який корінь мають слова **читати, читанка, читач**?
> [!solution] Перевірити
> Корінь **чит-** (reading).

6. Визначте слова з коренем **мов-** у списку: (мова, розмова, море, мовець).
> [!solution] Перевірити
> **мова, розмова, мовець**.

7. Яке слово має корінь **бач-**? (бачити, побачення, будівля)
> [!solution] Перевірити
> **бачити, побачення**.

8. Визначте префікс у слові **перехід**.
> [!solution] Перевірити
> **пере-** (meaning «across»).

9. Які слова мають корені **чит-** та **зна-** у реченні: «Студент, який багато читає, має гарні знання»?
> [!solution] Перевірити
> **читає** та **знання**. (Зверніть увагу на кому перед «який»!).

10. Визначте words з коренями **клад-** та **важ-** у реченні: «Викладач розповів про важливість мови».
> [!solution] Перевірити
> **викладач** (клад-) та **важливість** (важ-).

11. Який корінь має слово **побачення** у реченні: «Ми чекаємо на побачення, що змінить наше життя»?
> [!solution] Перевірити
> Корінь **бач-**. (Кома перед «що» обов'язкова!).

12. Визначте слова з коренями **лік-** та **пис-** у реченні: «Досвідчений лікар написав рецепт».
> [!solution] Перевірити
> **лікар** (лік-) та **написав** (пис-).

13. Яке слово має корінь **слов-** у реченні: «Ми вивчаємо словотвір, щоб розуміти структуру мови»?
> [!solution] Перевірити
> **словотвір**. (Кома перед «щоб»!).

14. Я знаю, що цей префікс змінює значення. (I know that this prefix changes the meaning.)
> [!solution] Перевірити
> Корені **зна-** (знаю) та **знач-** (значення). (Кома перед «що»!).

15. Я бачу письменника, який написав цю книгу. (I see the writer who wrote this book.)
> [!solution] Перевірити
> Корінь **пис-** (письменник, написав). (Кома перед «який»!).

---

## Practice: Common Word Formation Errors

**Can you spot and fix incorrect word forms?**

Analyze these sentences and fix the word formation error based on the English context provided.

1. Вчора я **вийшов** до школи вчасно. (arrived)
> [!solution] Перевірити
> **прийшов** (arrival = при-).

2. Мені подобається це **читач**. (the act of reading)
> [!solution] Перевірити
> **читання** (-ння for action).

3. Він хороший **читання**. (person who reads)
> [!solution] Перевірити
> **читач** (-ач for person).

4. Я **перейшов** з кімнати дуже швидко. (exited)
> [!solution] Перевірити
> **вийшов** (exit = ви-).

5. Це цікавий **музикальний** інструмент. (musical)
> [!solution] Перевірити
> **музичний** (standard adjective for music-related objects).

6. Ми **написали** через старий міст. (crossed / walked across)
> [!solution] Перевірити
> **перейшли** (across = пере- + movement).

7. Він **відійшов** до музею вранці. (entered)
> [!solution] Перевірити
> **увійшов** (entering = у-).

8. Вона **вийшла** від вікна дуже повільно. (stepped away)
> [!solution] Перевірити
> **відійшла** (away = від-).

9. Я **перечитала** до кімнати. (entered / walked in)
> [!solution] Перевірити
> **увійшла** (entering = у-).

10. Ця людина має велику **чесна**. (honesty - noun)
> [!solution] Перевірити
> **чесність** (іменник жіночого роду на -ість).

11. Ця **мудрий** дуже важлива. (wisdom)
> [!solution] Перевірити
> **мудрість** (іменник жіночого роду на -ість).

12. Я **перейшла** статтю ще раз. (read again)
> [!solution] Перевірити
> **перечитала** (префікс пере- для повторної дії з текстом).

13. Ця подія має велику **важливий**. (importance - noun)
> [!solution] Перевірити
> **важливість** (іменник на -ість).

14. Я **увійшов** від вікна. (stepped away)
> [!solution] Перевірити
> **відійшов** (префікс від- для руху від чогось).

---

## Integration Challenge

Analyze these complex words by breaking them into their logical parts (Prefix + Root + Suffix).

1. **передбачити** (to foresee) -> **перед** (prefix) + **бач** (root) + **ити** (suffix).
2. **письменник** (writer) -> **пис** (root) + **мен** (inter-suffix) + **ник** (agent suffix).
3. **важливість** (importance) -> **важ** (root) + **лив** (suffix) + **ість** (suffix).
4. **український** (Ukrainian) -> **україн** (base) + **ський** (suffix).
5. **читання** (reading) -> **чит** (root) + **ання** (suffix).
6. **безкоштовний** (free) -> **без** (prefix) + **кошт** (root) + **овний** (suffix).
7. **неможливий** (impossible) -> **не** (prefix) + **мож** (root) + **ливий** (suffix).
8. **робітник** (worker) -> **робіт** (root) + **ник** (suffix).
9. **вихід** (exit) -> **ви** (prefix) + **хід** (root).
10. **школяр** (schoolboy) -> **школ** (root) + **яр** (suffix).
11. **необхідність** (necessity) -> **не** (prefix) + **об** (prefix) + **хід** (root) + **н** (suffix) + **ість** (suffix).
12. **переможець** (winner) -> **пере** (prefix) + **мож** (root) + **ець** (suffix).
13. **побачення** (date / meeting) -> **по** (prefix) + **бач** (root) + **ення** (suffix).
14. **викладач** (lecturer) -> **ви** (prefix) + **клад** (root) + **ач** (suffix).
15. **словниковий** (vocabulary-related) -> **слов** (root) + **ник** (suffix) + **овий** (suffix).

---

## Sentence Building (Unjumble Challenge)

Try to assemble these sentences correctly. Pay attention to word order and punctuation!

1. **Українська мова має надзвичайно багату систему словотвору.** (Ukrainian language has an extremely rich system of word formation.)
2. **Кожна морфема несе своє специфічне смислове навантаження.** (Every morpheme carries its specific semantic load.)
3. **Ми вивчаємо корені слів, щоб розуміти структуру мови.** (We study word roots to understand the structure of the language.)
4. **Я знаю письменника, який написав цю музичну п'єсу.** (I know the writer who wrote this musical play.)
5. **Викладач розповів студентам про важливість правильного утворення слів.** (The lecturer told the students about the importance of correct word formation.)
6. **Слово «перехід» має префікс пере-, що означає рух через щось.** (The word "perekhid" has the prefix pere-, which means movement across something.)
7. **Я бачу, що ви добре розумієте логіку українського словотвору.** (I see that you understand the logic of Ukrainian word formation well.)
8. **Розуміння кореня допомагає нам вивчати нові слова набагато швидше.** (Understanding the root helps us study new words much faster.)

---

# Підсумок

Словотвір — це процес **утворення** нових слів за допомогою морфологічних засобів.

| Element | Pattern / Marker | Function | Example |
|---------|------------------|----------|---------|
| **Prefixes** | при-, ви-, пере-, у-, від- | Direction / Aspect | прийти, вийти, переписати |
| **Noun Suffixes** | -ння, -ість, -ач, -ар | Action / Quality / Person | читання, радість, слухач, лікар |
| **Adj Suffixes** | -ний, -овий, -ський | Relationship / Origin | музичний, кольоровий, київський |
| **Roots** | пис-, ход-, бач-, мов- | Core Meaning | написав, перехід, побачення, розмова |

> [!important]
> **Linguistic Insight**
>
> Словотвір — це логічна система, яка перетворює вивчення мови на захопливий процес відкриттів. Розуміння структури слова дозволяє вам не просто знати мову, а відчувати її логіку. 
> 
> **Уникайте помилок:**
> 1. **Надлишковість (Tautology):** Уникайте виразів на зразок «словотвір слів». Оскільки термін *словотвір* уже містить основу *слово-* та корінь *-твір-*, додавання слова «слів» створює смислову надлишковість. Це робить ваше мовлення більш природним та професійним.
> 2. **Пунктуація:** Пам'ятайте, що у складних реченнях перед сполучниками **що**, **щоб**, **як**, **де** або **який** (яка, яке, які, яку) майже завжди ставиться кома. Вона відокремлює частини речення для ясності.
> 
> *Наприклад:*
> - «Я знаю письменника, **який** написав цю музичну п'єсу.»
> - «Я бачу, **що** ви добре розумієте систему словотвору.»

---

## Need More Practice?

Щоб закріпити знання на практиці, спробуйте знайти 5 нових слів у будь-якому тексті та проаналізуйте їхню морфологічну структуру. Переконайтеся, що ваш вибір префікса **правильний**, щоб уникнути **помилок** у значенні (наприклад, не плутайте *прийти* та *відійти*). Зверніть особливу увагу на дієслово **читати** (to read, verb, /t͡ʃɪtˈatɪ/) та його численні похідні, такі як **читач** (reader) або **читання** (reading). Пам'ятайте, що розуміння навіть однієї нової морфеми може відкрити вам шлях до розуміння цілого ряду нових слів! Для глибшого занурення зверніть увагу на «пестливі слова» (diminutives), які роблять українську мову такою мелодійною та теплою.
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
