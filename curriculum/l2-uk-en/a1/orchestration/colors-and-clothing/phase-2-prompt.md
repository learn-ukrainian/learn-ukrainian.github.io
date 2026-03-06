# Beginner Content: Write the Lesson

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of Patient Supportive Tutor.

> **Your task: Write approximately 1200 words of clear, beginner-friendly content.**
> Keep explanations clear and direct. Every H3 gets {H3_WORD_RANGE} words. Avoid verbose prose — students are beginners. Focus on practical examples over theory.

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## Files to Read

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/colors-and-clothing-research.md` | Research notes |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/colors-and-clothing.yaml` | Content outline with section word allocations |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/colors-and-clothing.yaml` | Objectives, vocabulary_hints |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries

(No video discoveries available)



## Module Constraints (HARD FAIL if violated)

SEQUENCE CONSTRAINTS (M11-14 — Adjectives & Plurals):
Student knows: alphabet, gender, greetings, Це/Я/Мене звати, basic nouns.
Learning: adjective agreement (M11), colors (M12), plurals (M13), checkpoint (M14).

GRAMMAR STATUS:
- AVAILABLE: nouns (nom. sg & pl from M13), adjective+noun agreement (from M11), Це/Я sentences, memorized phrases
- FORBIDDEN: verb conjugation (starts M15), imperatives (M47), cases beyond nominative (accusative starts M25)
- Use English for classroom instructions

METALANGUAGE: English-first, Ukrainian in parentheses



## Textbook Reference Examples (from real Ukrainian буквар)

These are real exercises from Ukrainian 1st-grade primers. Use them as **inspiration for style and difficulty level** — notice how they use simple syllable combinations, short words, and build progressively. Do NOT copy them verbatim, but match their pedagogical approach and simplicity.

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

**Grade 1, bolshakova** — Сторінка 3:
```
3
Дорогий друже!
Ти продовжуєш подорож чудовим сві-
том рідної мови. Адже ти любиш читати, 
спілкуватися, фантазувати. 
Ця книга допоможе тобі навчитися 
читати, висловлювати думки й почуття, 
спілкуватися.
Умовні позначення:
	
	 — читаю
	
	 — обговорюю малюнок
	
	 — досліджую мовлення
	
	 — мислю критично
```

**Grade 1, zaharijchuk** — Сторінка 48:
```
46
Бачу М, м (ем).  Чую [м].
м а *
а
*
*
м и * о
* о м а * * а
	
Визнач, яка схема відповідає намальовано-
му предмету. 
а
о
у
и
М
ма
мо
му
ми
а
о
у
и
ам
ом
ум
им
М
ма     
ма  
мо
ма
ми
му
ма-     
мо-     
му-     
[ –• | – •]
[ –•| – •– | – •]
М м
```

**Grade 1, zaharijchuk** — Сторінка 28:
```
26
Жовтий жук купив жилет,
Джемпер, джинси та 
жакет (Л. Мовчун).
,
	
Розгадай ребуси.
	
Прочитай скоромовку повільно, швидко, ще 
швидше.
	
Прочитай слова, які «заховалися» в словах.
ніжка	
	
   журавлик		
ведмежа
стежка		
   невже	
	
жолоб
жа
ба
бка
жо
вте
вток
жи
то
тло
	 Прочитай слова кожної колонки. Вилучи 
«зай­ве» слово.
жоржина	
жайворонок	
журнал
жасмин	
журавель	
журналіст
журавлина	
стриж	
інженер
кожух	
гараж	
режисер
	 нога — ніжка	
книга — книжка 
	 смуга — смужка	
ріг — ріжок 
Pi
```

**Grade 1, zaharijchuk** — Сторінка 29:
```
27
	 Створи речення до кожного малюнка (усно).
.
.
.
.
.
.
Речення
.
.
.
```

---

## Writing Instructions

Write the lesson prose for **Colors & Clothing** (a1 track).

- **Target**: approximately 1200 words
- **Immersion**: TARGET: 25-40% Ukrainian, 60-75% English. Write cultural notes, practical sections, observations, and drill instructions in Ukrainian first (2-3 sentence paragraphs, max 10 words per sentence), then add English translation below. CRITICAL: NEVER mix languages within a sentence. Each sentence is 100% Ukrainian OR 100% English. Grammar RULES stay in English. Provide 3-4 Ukrainian examples per grammar point. Some callout/tip text in Ukrainian. A1 register only — simple concrete vocabulary.
- **Engagement callouts**: **3+ MANDATORY** — spread across sections, at least 3 different types. Content with fewer than 3 callout boxes (> [!tip], > [!warning], etc.) FAILS validation.
- **Structure**: Follow the content_outline from `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/colors-and-clothing.yaml` — each section maps to an H2. **Write ALL sections. Do not skip any section, even short ones like Summary.** Missing sections fail validation.

### Beginner Writing Style

Write for someone seeing Ukrainian for the first time. English is the scaffolding language — use it for explanations, instructions, and context. Ukrainian is the target content — letters, words, phrases being taught.

**Do this:**
- Introduce each new letter/word clearly with its sound and meaning
- Use tables to show letter-sound mappings
- Give real Ukrainian words as examples (from the decodable vocabulary only)
- Keep paragraphs short (3-5 sentences)
- Use callout boxes for tips, fun facts, and warnings about visual traps

**Do NOT do this:**
- Use Ukrainian grammar terminology (іменник, дієслово, голосний, приголосний) — students don't know these yet
- Write long paragraphs of linguistic analysis
- Include IPA transcriptions or phonetic brackets
- Use vocabulary from future modules
- Create practice sentences if the constraints say "no sentences"
- Repeat the same Ukrainian phrase pattern more than twice (e.g. don't write "Це склад", "Це слово", "Це правило" in every paragraph — vary your immersion: use contextual labels like "Наприклад — For example", section bridges like "А тепер — And now", vocabulary callouts, or short dialogue snippets)

### Example of Good A1 Content (letter introduction)

```markdown
## Meet the Letters

### А — The Familiar One

The first letter is easy: **А** looks exactly like English A and makes the same sound — /a/ as in "father."

You'll find А in some of the first words you learn:

| Word | Meaning |
|------|---------|
| **мА́ма** | mom |
| **сУ́ма** | sum, amount |

[!tip]
> А is one of the "true friends" — letters that look AND sound the same in both alphabets. Enjoy these while they last!

### Н — The First Visual Trap

Here's where it gets interesting: **Н** looks like English H, but it's actually the /n/ sound.

This is a "visual trap" — your brain sees H and wants to say "h", but in Ukrainian it's always /n/.

| Word | Meaning |
|------|---------|
| **нам** | to us |
| **луна́** | echo |
```

### Section Word Budgets

| Section | Target |
|---------|--------|
| Вступ та культурний контекст (Introduction & Cultural Context) | 200 |
| Кольори та узгодження (Colors & Grammar of Agreement) | 300 |
| Лексика одягу (Clothing Vocabulary) | 300 |
| Практика: Дієслово «носити» та покупки (Practice: The Verb 'To Wear' & Shopping) | 250 |
| Підсумок (Summary) | 150 |
| **Total** | **1200** |

### Callout Types to Use

- `[!tip]` — practical advice for learners
- `[!warning]` — visual traps, common mistakes
- `[!did-you-know]` — fun facts about Ukrainian
- `[!culture]` — cultural connections

### Audit Gates (your content will be checked for)

- **Word count**: minimum 1200 words
- **Russianisms**: banned (кушати, получати, etc.)
- **Russian characters**: ы, э, ё, ъ must NEVER appear
- **Euphony**: і/й, у/в alternation
- **Engagement callouts**: 3+
- **IPA/phonetic brackets**: BANNED

## Language Quality Rules (All Tiers)

### Russianisms (HARD FAIL if found)

Scan your ENTIRE output for these. They cause automatic audit failure:

| Russicism | Correct Ukrainian |
|-----------|-------------------|
| кушати | їсти |
| приймати участь | брати участь |
| получати | отримувати |
| самий кращий | найкращий |
| відноситися | стосуватися |
| слідуючий | наступний |
| любий (= будь-який) | будь-який |
| на то, що | на те, що |
| красивий | гарний |
| прекрасне / прекрасний | чудовий / чудове |

Also scan for Russian characters: **ы, э, ё, ъ** — these must NEVER appear in Ukrainian text.

### Euphony / Милозвучність (WARNING if violated)

Ukrainian prose must follow euphony rules:

| Rule | Avoid (Bad) | Use (Good) |
|------|-------------|------------|
| і → й between vowels | вона і Олена | вона й Олена |
| й → і after consonant | він й Олена | він і Олена |
| у → в before vowel | у Одесі | в Одесі |
| в → у before в, ф | в вікні | у вікні |
| в → у before consonant cluster | в зграї | у зграї |
| з → із/зі before з, с, ш, ч | з зброєю | із зброєю (або зі) |
| Vary conjunctions | він і вона і Іван | він і вона та Іван |

Key: й can ONLY follow a vowel. After a consonant, always use і — even before a vowel.

### Stress Mark Typography

Use lowercase letters with a combining acute accent (´) on the stressed vowel:
- Correct: ма́ма, анана́с, оса́, сосна́
- Wrong: мА́ма, ананА́с, осА́, соснА́ (do NOT capitalize the stressed vowel)

### Non-Decodable Ukrainian in Beginner Modules (M1-M6)

In Cyrillic primer modules, the learner can only read letters taught so far. Any Ukrainian phrase using letters outside the cumulative charset MUST include an English translation in parentheses immediately after. No exceptions — the learner literally cannot read it otherwise.

- Correct: "Все буде добре (Everything will be fine)."
- Wrong: "Все буде добре." (no translation — learner cannot read Б or Д at M2)

### IPA and Latin Transliteration (BANNED at ALL levels)

Never include IPA symbols (ɑ, ɛ, ʃ, etc.) or bracketed pronunciation guides like `[ma-ma]`, `[a-na-nas]`, `[ˈmɑmɑ]`. The ONLY pronunciation aid is the stress mark (´) on the vowel.

Latin transliterations are BANNED: never use kh, sh, ch, zh, ts, ya, yu, ye, shch.

```markdown
❌ WRONG: "мама [ˈmɑmɑ]" or "хліб (khlib)"
✅ RIGHT: "**ма́ма** (mom)" or "**Х**, like the «ch» in Scottish «loch»"
```

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Use ONLY vocabulary from the plan's `vocabulary_hints` — do NOT invent new terms

### No Word Salad (HARD FAIL)

Every paragraph must have ONE clear point and logical flow between sentences. Do NOT string together unrelated observations.

### LLM Writing Patterns to Avoid

1. **"Це не просто X, а Y"** — max ONE in entire module
2. **Grandiose openers** — don't inflate every topic
3. **Purple prose** — no "багатогранний діамант", "хірургічного аналізу"
4. **Duplicate greetings** — "Ласкаво просимо" ONCE (intro only)
5. **Stacked identical callouts** — same title max twice, vary types
6. **"In this lesson, we will..."** — ALWAYS banned (formulaic opener)
7. **Repetitive transitions** — "It's worth noting...", «Варто зазначити...», «Давайте розглянемо...» flagged at 2+ occurrences

### Anti-Robotic Writing

- No 3+ sentences starting with the same phrase
- Vary sentence openers across sections
- No mechanical transitions («Далі ми побачимо...», «Тепер розглянемо...»)
- Each section should have its own narrative arc

### Active Voice Preference

Ukrainian strongly prefers active constructions. Use passive only when the agent is truly unknown.

Avoid: «Це може бути використано...», «Правило застосовується...»
Prefer: «Ви можете використати...», «Ми застосовуємо правило...»


---

## Pre-Submission Checks

1. **Plan compliance**: Does every point in the content_outline have dedicated prose?
2. **Word count**: Does the total meet 1200?
3. **Language scan**: No Russianisms, no Russian characters, no IPA, no Latin transliteration?
4. **Decodable vocabulary**: Does every Ukrainian word use only the allowed letter set?

---

## Output Format

```
===CONTENT_START===

<!-- SCOPE
Covers: {what this module teaches}
Not covered:
  - {related topic} → {slug}
-->

# {Title}

> **Чому це важливо? — Why does this matter?**
>
> {2-3 sentences}

## {Section 1}
...

---

# Підсумок — Summary

{Summary + 3-4 self-check questions}

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
**Phase**: Beginner Content
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities or vocabulary tables (separate phase)
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Do NOT skip sections from the content_outline
- Do NOT write fewer than 1200 words
- Do NOT use straight quotes "..." — always «...»
