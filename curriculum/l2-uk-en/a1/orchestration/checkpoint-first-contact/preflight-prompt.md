You are about to build a module using the prompt below. This prompt has been carefully engineered to produce content that passes all audit gates. Your job is to confirm it is ready.

**Default answer: PASS.** This prompt is designed to work. Only report issues if something will genuinely cause an audit gate to FAIL.

## The Prompt

<prompt>
# Beginner Checkpoint: Synthesis & Review

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of Patient Supportive Tutor.

> **Your task: Write approximately 1200 words that REVIEW and SYNTHESIZE prior material — NOT teach new concepts.**
> Keep explanations clear and direct. Every H3 gets {H3_WORD_RANGE} words. Avoid verbose prose — students are beginners. Focus on practical examples over theory.

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## CHECKPOINT IDENTITY — READ THIS FIRST

**This is a CHECKPOINT module.** Checkpoints are fundamentally different from teaching modules:

| Teaching Module | Checkpoint Module |
|----------------|-------------------|
| Introduces new grammar/vocabulary | Reviews grammar/vocabulary from prior modules |
| Explains concepts for the first time | Creates new CONTEXTS that combine prior concepts |
| Learning objectives | Synthesis objectives |
| "Here's how it works" | "Show me you can use it" |
| Feels like a lecture | Feels like a celebration of progress |

**The golden rule: If the learner hasn't seen it in a prior module, it does NOT belong here.**

### What Checkpoints Do

1. **Reuse ALL vocabulary and grammar from the preceding block** — no new teaching
2. **Create new contexts** that force combining multiple skills learned separately
3. **Feel like a reward/celebration**, not a test — the learner should feel proud of how far they've come
4. **Synthesis over explanation** — show how pieces fit together, don't re-explain them
5. **Self-assessment** — help learners identify gaps before moving forward

### What Checkpoints Do NOT Do

- Introduce new grammar rules or patterns
- Teach new vocabulary (only reuse from prior modules)
- Explain concepts in detail (brief reminders only, not full explanations)
- Present theory-heavy sections

---

## Files to Read

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/checkpoint-first-contact-research.md` | Research notes |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/checkpoint-first-contact.yaml` | Content outline, section word allocations, vocabulary_hints |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries

### Videos
- **Ukrainian podcast #10 Traveling to Lviv - Подорож до Льова. SLOW UKRAINIAN** (Speak Ukrainian)
  URL: https://www.youtube.com/watch?v=1_vO60OkkrY
  Score: 0.7 -- The video describes Lviv, specifically mentioning 'кафе' as a feature of the city. This directly reinforces the 'Культурний контекст: Кафе' section of the module by providing real-world context and vocabulary usage.
  Suggested placement: After Культурний контекст: Кафе -- the video provides an authentic cultural context for cafes in Ukraine, directly linking to the module's cultural section.
  Key excerpt: Сьогодні Львів має площу 155 км. кв. з безліччю громадських будинків, кафе, магазинів, готелів та банків у стилі ХІХ-ХХ ст. Львів — єдине в Україні місто, у якому збереглися архітектурні споруди часів Ренесансу.


### Blog Articles & Guides
- **Ukrainian Alphabet: Full Guide with Examples and Pronunciation** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ukrainian-alphabet/
  Relevance: 0.8


### Textbook References
- **Grade 2, Сторінка 3**
  ДОРОГІ ДІТИ!
Ви тримаєте в руках новий підручник, який допоможе вам 
навчитися швидко і вдумливо читати. Уміти читати — це не 
лише утворювати слова зі складів, а й розуміти зміст, відчу­
вати красу м...

- **Grade 1, Сторінка 3**
  3
Дорогий друже!
Ти хочеш учитися читати?
Ти прагнеш спілкуватися?
Ти любиш фантазувати?
Тоді ця книга саме для тебе! 
Вона допоможе тобі навчитися читати, 
висловлювати думки й почуття, спілкуватися....

- **Grade 4, Сторінка 51**
  140.1. Прочитай слова.
Голка, гілка, подруга, сніжинка, усмішка, ложка, берег, Ма­
рійка, бібліотека, іволга, вільха.
2. Зміни подані слова так, щоб відбувалося чергування приголо­
сних звуків. Запиши...

- **Grade 1, Сторінка 3**
  3
Дорогий друже!
Ти продовжуєш подорож чудовим сві-
том рідної мови. Адже ти любиш читати, 
спілкуватися, фантазувати. 
Ця книга допоможе тобі навчитися 
читати, висловлювати думки й почуття, 
спілкув...

- **Grade 4, Сторінка 4**
  4
ЧИТАЄМО Й РОЗПОВІДАЄМО 
ЧИТАЄМО Й РОЗПОВІДАЄМО 
ПРО СВОЇ ЗАХОПЛЕННЯ
ПРО СВОЇ ЗАХОПЛЕННЯ
 
Ознайомтеся з новим підручником. Знайдіть у змісті 
перший розділ. Які твори вміщені в ньому? Які автори тво...


### Pronunciation Videos (from plan — MANDATORY embeds)
*Credit: Anna Ohoiko — Ukrainian Lessons*

- **Overview**: [Anna Ohoiko — Ukrainian Lessons — Overview](https://www.youtube.com/watch?v=ksXIXj7CXwc)
- **Full Playlist**: [Anna Ohoiko — Ukrainian Lessons — Playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)

**Embed the overview video in the introduction section and reference the playlist for students who want per-letter videos.**

## Module Constraints (HARD FAIL if violated)

GRAMMAR CONSTRAINTS (A1.1 — First Contact):
Keep grammar simple — this is the learner's first exposure to Ukrainian.

ALLOWED:
- Це + noun: «Це кіт», «Це мама»
- Simple present tense (я читаю, я бачу)
- Basic imperatives (читай, слухай, дивись)
- Question words: «Хто це?», «Що це?», «Де?»
- Так/Ні answers
- Adj + noun: «великий дім», «нова книга»

BANNED (too complex for first contact):
- Past tense, future tense, conditionals
- Participles, passive voice, gerunds
- Compound/complex sentences — max 1 clause per sentence (no і/а/але joining clauses)
- Do not explicitly teach cases — use nouns in natural contexts

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)'
- Section headings MUST be bilingual (e.g., '## Голосні — Vowels')
- Explanatory prose in English, Ukrainian for examples and dialogues



**Target vocabulary** (from the plan — these are REVIEW words from prior modules, not new vocabulary):

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- великий (big) — великий стіл, великий дім; Review from M11
- новий (new) — нова книга, нове місто; Review from M11
- гарний (beautiful/nice) — гарна книга, гарне місто; Review from M11
- червоний (red) — червона сукня, червоний светр; Review from M12
- хто (who) — Хто це?; Interrogative focus
- що (what) — Що це?; Interrogative focus
- де (where) — Де кафе?; Interrogative focus
- так/ні (yes/no) — базові ствердні та заперечні відповіді

**Recommended** (use in your content to reach the vocabulary target):
- синій (blue) — сині штани, синій светр; Review from M12
- білий (white) — біла сорочка, білий сніг; Review from M12
- кава (coffee) — чорна кава, кава з молоком; Cultural hook: Lviv tradition
- Смачного! (Bon appetit) — Essential cultural phrase for dining
- маленький (small) — маленький кіт, маленька книга; Adjective practice

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

**Rules:**
- Every word listed above was taught in a prior module. Use them in NEW combinations and contexts.
- Do NOT explain these words as if seeing them for the first time — the learner already knows them.
- Create fresh example sentences that combine vocabulary from different prior modules.
- Match the syntactic complexity of the prior modules — do not escalate difficulty.

## Textbook Reference Examples (from real Ukrainian буквар)

These are real exercises from Ukrainian 1st-grade primers. Use them as **inspiration for style and difficulty level** — notice how they use simple syllable combinations, short words, and build progressively. Do NOT copy them verbatim, but match their pedagogical approach and simplicity.

**Grade 1, zaharijchuk** — Сторінка 92:
```
90
Е е
Бачу Е, е. Чую е.
О-ле-сик  і  та-то  по-ві-си-ли на  гіл-
ку  кле-на 
. 
 У 
 на-си-па-ли 
, 
 і 
 .
При-ле-ті-ли 
, 
, 
.
ле- 
         ле-
      
    ве- 
     ек-
ле- 
         ле-
      
    ве- 
     ек-
* е р е * а
к л е н
  –•  |  –• |  – •
м
н
с
л
р
Е
ем
ен
ес
ел
ер
м
н
с
л
р
ме
не
се
ле
ре
Е
е * е л * в
с
*
е
  –  –•  –
```

**Grade 1, zaharijchuk** — Сторінка 6:
```
Юю
Аа
Оо
Уу
Ии
Мм
Мм
Іі
Нн
Нн
Вв
Вв
Лл
Сс
Кк
Пп
Рр
Тт
Ее
Дд
Зз
ь
Бб
Аа
```

**Grade 1, zaharijchuk** — Сторінка 105:
```
103
	 Тобі сподобався Чижик-Пижик? Він уперше 
полетів. Що ти хотів би / хотіла б йому поба-
жати?
Читаємо разом
Слова — назви дій
 
Слова — назви дій предмета відпо-
відають на питання що робити? що 
робить? що роб­лять? 
	 Розглянь малюнки. 
1
5
3
7
2
6
4
	 Прочитай слова — назви дій.
Поливає, снідає, читає, ідуть, навча-
ються, малює, чистить зуби.
Pidruchnyk.com.ua
```

**Grade 1, bolshakova** — Сторінка 3:
```
3
Дорогий друже!
Ти хочеш учитися читати?
Ти прагнеш спілкуватися?
Ти любиш фантазувати?
Тоді ця книга саме для тебе! 
Вона допоможе тобі навчитися читати, 
висловлювати думки й почуття, спілкуватися.
Умовні позначення:
 
 — слухаю 
 
— досліджую мовлення
 
 — читаю 
 — обговорюю малюнок
 
 — спілкуюся 
 
— мислю критично
```

**Grade 1, zaharijchuk** — Сторінка 34:
```
32
	
Визнач предмети, у назвах яких є звук г; 
у якому є звук ґ; два звуки ш.
	
Знайди «загублений» склад у словах — на-
звах намальованих предметів. 
	
Визнач, якому слову — назві зображеного 
предмета відповідає кожна схема.
___ -ба-ба	
кул-,	
куль-,	
буль-
бе- ____ -за	
-ра-,	
-ри-,	
-ре-
че-ре- ___ -ха	 -ре-,	
-па-,	
-ба-
   = •   =   |  – •
   – • |  – • |  – • 
   – • | – • 
Мої навчальні досягнення. Я вмію, можу
   – • –  | – • |  = •
Pidruchnyk.com.ua
```

**Grade 1, zaharijchuk** — Сторінка 112:
```
110
Повторюємо разом
Текст
 
Як­що два й біль­ше ре­чень поєдна­ні 
за зміс­том, — це текст. Текст має 
заголовок.
	 Розглянь схему тексту. З виділених слів тек-
сту створи речення, які б відповідали схемам. 
Добери заголовок до створеного тексту.
.
.
.
.
.
	 Розкажи, що ти знаєш про персонажів про-
читаних казок. 
	 Назви свого улюбленого персонажа. 
Pidruchnyk.com.ua
```

NOTE: The textbook examples above are provided as INSPIRATION for the pedagogical approach, NOT as content to copy. For modules M15+, focus on the communicative patterns, not the letter/syllable exercises.


---

## Writing Instructions

Write the checkpoint content for **Checkpoint: First Contact** (a1 track).

- **Target**: 1200–1800 words (below 1200 = FAIL)
- **Engagement callouts**: **3+ MANDATORY** — spread across sections, at least 3 different types
- **Structure**: Use the EXACT H2 section titles listed below. Missing or renamed sections fail validation.

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Огляд (Overview)` (~180 words)
  - Привітання від господаря хостелу (Friendly Hostel Host) — пояснення мети контрольної точки: консолідація фонології (§4.1.1), морфології (§4.2.1.1, §4.2.4.1) та синтаксису (§4.3.1) рівня A1.1
  - Практичний підхід до перевірки знань — стратегія 'Test-Teach-Test' (TTT) для виявлення прогалин перед переходом до знахідного відмінка (a1-11)
- `## Навичка 1: Читання та Рід (Skill 1: Reading and Gender)` (~300 words)
  - Фонологічний виклик: розрізнення звуків И /ɪ/ (bit) та І /i/ (bee) — вправи на мінімальні пари та читання слів зі стандарту (§4.1.1: Київ, київський, Україна, українець, Олена, олівець)
  - Класифікація іменників за родом (§4.2.1.1) — фокус на 'тато' (чоловічий рід), який часто помилково вважають середнім через закінчення -о, на відміну від слова 'місто'
  - Швидка перевірка вміння впізнавати всі 33 літери українського алфавіту без використання транслітерації
- `## Навичка 2: Прикметники та Множина (Skill 2: Adjectives and Plurals)` (~300 words)
  - Узгодження прикметників з іменниками за родом (M11 review): великий стіл (M), нова книга (F), гарне місто (N). Drill на правильні закінчення -ий/-а/-е.
  - Утворення множини (M13 review): стіл → столи, книга → книги, місто → міста. Чергування приголосних та голосних у множині.
  - Кольори + одяг (M12 review): червона сукня, сині штани, білий светр. Поєднання прикметників з іменниками одягу.
- `## Культурний контекст: Кафе (Cultural Context: Cafe)` (~240 words)
  - Львівська культура кави — історична довідка про Юрія Кульчицького та віденську кав'ярню «Під синьою пляшкою» (1683), що пов'язує Україну з європейською традицією
  - Етикет замовлення їжі (§3.9) — обов'язкове вживання фрази «Смачного!» (Bon appetit) та ввічливих форм запиту: «Дайте, будь ласка...», «Можна рахунок?»
- `## Інтеграційне завдання (Integration Task)` (~180 words)
  - Інтеграція навичок: опис кафе та меню через Це + adj + noun (Це чорна кава, Це великий торт, Це нове кафе). Визначення роду іменників та правильне узгодження.
  - Самооцінка готовності до переходу на рівень A1.2 — підбиття підсумків засвоєння модулів M1-M13
- `## Підсумок — Summary` (~150 words) — recap + 3-4 self-check questions

### Checkpoint Writing Style

**Tone: Celebratory and encouraging.** The learner has completed a block of lessons. This is a victory lap, not an exam.

- Open with acknowledgment of progress: "You've learned X, Y, and Z — now let's see how they work together!"
- Use warm, encouraging language throughout
- Frame challenges as "puzzles" or "adventures", not "tests"
- End with a clear signal of readiness for the next phase

**Structure each skill-review section as:**
1. **Brief reminder** (1-2 sentences max) of what the skill is — NOT a full re-explanation
2. **New context** that exercises the skill — a scenario, dialogue, or situation the learner hasn't seen
3. **Integration challenge** that combines this skill with others from the same block
4. **Reinforcement callout** (tip, culture note, or encouragement)

**Integration sections must:**
- Combine 2+ skills from different prior modules in a single task
- Use a realistic scenario (ordering food, describing a room, introducing family)
- Show how grammar and vocabulary work together in natural speech

### Immersion Target

TARGET: 25-40% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences (3+ words with a verb) go in tables, bulleted example lists, or pattern boxes. Never write a Ukrainian sentence followed by its English translation in a prose paragraph.
Ukrainian sentences max 10 words. Mix container types — don't use tables for everything.

### Structural Containment (how to achieve immersion without code-switching)

**Three rules govern where each language appears:**

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "Remember **книга** (book)? Now combine it with the adjective **нова** to get **нова книга**."

2. **Full Ukrainian sentences = prefer structural containers.** Ukrainian sentences (3+ words with a verb) work best in containers, but short inline Ukrainian is fine in explanatory context (e.g., "Remember how **Це нова книга** uses the adjective before the noun?"):
   - **Tables** — paradigms, vocabulary groups, gender sorting (tables count ZERO for immersion — use for structure/explanation only)
   - **Bulleted example lists** — Ukrainian line + English gloss: `- **Читай книгу!** — Read the book!`
   - **Blockquote dialogues** — mini-conversations with labeled speakers
   - **Pattern boxes** — transformations: `читати → читай → читайте`

3. **Vary containers.** Never use the same container type twice in a row.

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Огляд (Overview) | 180+ |
| Навичка 1: Читання та Рід (Skill 1: Reading and Gender) | 300+ |
| Навичка 2: Прикметники та Множина (Skill 2: Adjectives and Plurals) | 300+ |
| Культурний контекст: Кафе (Cultural Context: Cafe) | 240+ |
| Інтеграційне завдання (Integration Task) | 180+ |
| **Total** | **1200+ (aim for ~1440)** |

### Callout Types to Use

- `[!tip]` — practical reminders for learners
- `[!warning]` — common mistakes to watch for (review traps)
- `[!did-you-know]` — fun facts about Ukrainian
- `[!culture]` — cultural connections that make the language come alive

### Audit Gates (your content will be checked for)

- **Word count**: minimum 1200 words
- **Russianisms**: banned (кушати, получати, etc.)
- **Russian characters**: ы, э, ё, ъ must NEVER appear
- **Euphony**: і/й, у/в alternation
- **Engagement callouts**: 3+
- **IPA/phonetic brackets**: BANNED
- **New grammar/vocabulary**: BANNED — checkpoint reviews only

## Language Quality Rules (Beginner Tier)

### Russian Characters (HARD FAIL)

**ы, э, ё, ъ** must NEVER appear in Ukrainian text. These are Russian-only characters.

### Stress Mark Typography

Use lowercase letters with a combining acute accent (´) on the stressed vowel:
- Correct: ма́ма, анана́с, оса́, сосна́
- Wrong: мА́ма, ананА́с, осА́, соснА́ (do NOT capitalize the stressed vowel)

### IPA and Latin Transliteration (BANNED at ALL levels)

Never include IPA symbols (ɑ, ɛ, ʃ, etc.) or bracketed pronunciation guides like `[ma-ma]`, `[a-na-nas]`, `[ˈmɑmɑ]`. The ONLY pronunciation aid is the stress mark (´) on the vowel.

Latin transliterations are BANNED: never use kh, sh, ch, zh, ts, ya, yu, ye, shch.

```markdown
❌ WRONG: "мама [ˈmɑmɑ]" or "хліб (khlib)"
✅ RIGHT: "**ма́ма** (mom)" or "**Х**, like the «ch» in Scottish «loch»"
```

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Base content vocabulary on the plan's `vocabulary_hints`. Function words (pronouns, conjunctions, particles, question words) are always allowed

### No Word Salad (HARD FAIL)

Every paragraph must have ONE clear point and logical flow between sentences. Do NOT string together unrelated observations.

### LLM Writing Patterns to Avoid

1. **Grandiose openers** — don't inflate every topic
2. **Stacked identical callouts** — same title max twice, vary types
3. **"In this lesson, we will..."** — ALWAYS banned (formulaic opener)


---

## Pre-Submission Checks

1. **Plan compliance**: Does every point in the content_outline have dedicated prose?
2. **Word count**: Does the total meet 1200?
3. **Language scan**: No Russianisms, no Russian characters, no IPA, no Latin transliteration?
4. **Decodable vocabulary**: Does every Ukrainian word use only the allowed letter set?
5. **Synthesis check**: Does every section COMBINE skills rather than re-teach them individually?
6. **No new material**: Have you avoided introducing any grammar or vocabulary not from prior modules?



---

## Output Format

```
===CONTENT_START===

<!-- SCOPE
Covers: Review and synthesis of {prior modules}
Not covered:
  - New grammar or vocabulary
  - {next phase topic} → {next-slug}
-->

# {Title}

> **Чому це важливо? — Why does this matter?**
>
> {2-3 celebratory sentences acknowledging progress}

## {Section 1}
...

---

# Підсумок — Summary

{Summary + 3-4 self-check questions. Each question MUST include an English translation if the question is in Ukrainian. Format: "Який? (Which?) — answer / відповідь"}

---

===CONTENT_END===
```

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: 1200)
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Beginner Checkpoint Content
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities or vocabulary tables (separate phase)
- Do NOT introduce new vocabulary or grammar not from prior modules
- **VOCABULARY COVERAGE RULE:** All words from `vocabulary_hints` in the plan MUST appear at least once in the module content.
- Do NOT skip sections from the content_outline
- Do NOT write fewer than 1200 words
- Do NOT use straight quotes "..." — always «...»
- Do NOT re-explain concepts in detail — brief reminders only, then synthesize

</prompt>

## Audit Gates (what your content will be checked against)

## Audit Gates (your content will be checked against these)

Level: A1
Word target: 1200
Word ceiling: ~1800 (exceeding = FAIL)
Min activities: 8
Min engagement boxes: 3
Min activity types: 4

### Immersion
Target range: defined in the prompt's Immersion Target section (varies by module).
Tables count ZERO for immersion — only blockquotes, bulleted lists, and pattern boxes count.

### Grammar constraints
Max words per Ukrainian sentence: 10
Participles allowed: False
Max clauses: 1

### Structure
MUST have a Summary/Підсумок section (structure gate FAILS without it).

### Pedagogy
Sentences exceeding word limit = COMPLEXITY violation.
Participles before B1 = GRAMMAR violation.
Euphony (у/в alternation) errors are flagged.

## Scoring Dimensions (7 — Beginner Tier)
Your content will be scored on these dimensions (9-10 = PASS):
1. Language Quality — no Russianisms, correct Ukrainian, natural phrasing
2. Engagement — would the learner continue reading? Hook in first 50 words
3. Writing Quality — clarity, pacing, no word salad, logical flow
4. Immersion — % Ukrainian must hit target range (tables = ZERO)
5. Structure — lesson arc: WELCOME → PREVIEW → PRESENT → PRACTICE → CELEBRATE
6. Emotional Safety — ≥15 direct address, encouragement, quick wins
7. Lesson Quality — does it feel like a patient, encouraging tutor?

## Instructions

Read the prompt carefully. If you can build a module that passes all audit gates using this prompt, return PASS.

Only report an issue if:
- Two instructions **directly contradict** each other AND following one will FAIL a named gate
- A target is **mathematically impossible** to reach given the constraints
- A required gate has **zero guidance** in the prompt (not "could be clearer" — literally missing)

Do NOT report: style preferences, wording suggestions, minor ambiguities, things that "could be improved." Focus on issues that would prevent you from building excellent content.

**Gate names** (only these matter): Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion.

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # or MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, UNCLEAR
      location: "Section 4, line about tables"
      problem: "Template says tables have highest density but audit strips tables from immersion"
      suggested_fix: "Remove 'highest density' claim, add warning that tables = zero immersion"
      severity: HIGH  # or MEDIUM, LOW
```

If there are no issues, return:
```yaml
prompt_preflight:
  status: PASS
  issues: []
```

Be SPECIFIC. Cite exact text from the prompt. Focus on issues that will cause audit FAILURES, not style preferences.