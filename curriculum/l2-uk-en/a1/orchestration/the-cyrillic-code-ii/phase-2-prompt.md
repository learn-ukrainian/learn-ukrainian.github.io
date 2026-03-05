# Beginner Content: Write the Lesson

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of Patient Supportive Tutor.

> **Your task: Write approximately 1200 words of clear, beginner-friendly content.**
> Be concise — students know nothing yet. Short, clear explanations. Every H3 gets {H3_WORD_RANGE} words. The activities do the teaching, not the prose. Do NOT pad with adjectives, motivational filler, or over-explained phonetics.

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## Files to Read

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-cyrillic-code-ii-research.md` | Research notes |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-ii.yaml` | Content outline with section word allocations |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-cyrillic-code-ii.yaml` | Objectives, vocabulary_hints |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries

(No video discoveries available)

### Per-Letter Pronunciation Videos (from plan — MANDATORY embeds)
*Credit: Anna Ohoiko — Ukrainian Lessons*

- **Full Playlist**: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV (link only, do not embed)

**Each letter below MUST get its video embedded in the corresponding H3 section. Use this EXACT markdown link format:**

- **Літера К**: [Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)
- **Літера И**: [Anna Ohoiko — Ukrainian Lessons — И](https://www.youtube.com/watch?v=W-1rCu0indE)
- **Літера І**: [Anna Ohoiko — Ukrainian Lessons — І](https://www.youtube.com/watch?v=Z9TH0H4ShGo)
- **Літера Р**: [Anna Ohoiko — Ukrainian Lessons — Р](https://www.youtube.com/watch?v=fMGsQ5KPQgg)
- **Літера В**: [Anna Ohoiko — Ukrainian Lessons — В](https://www.youtube.com/watch?v=aFcvYfvQ2X4)
- **Літера Т**: [Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)
- **Літера Е**: [Anna Ohoiko — Ukrainian Lessons — Е](https://www.youtube.com/watch?v=KFlsroBW0dk)

## Module Constraints (HARD FAIL if violated)

DECODABILITY (M2 — 14 known letters: А О У М Л Н С + К И І Р В Т Е):
- Reading drills MUST use ONLY these 14 letters (e.g., кіт, молоко, місто, рис, сир, тато, вікно, він)
- Still unknown: Б, Д, П, З, Г, Ґ, Х, Ж, Ш, Ч, Й, Щ, Я, Ю, Є, Ь, Ї, Ц, Ф
- Words needing unknown letters require immediate English translation

GRAMMAR BAN (no verbs exist yet):
- NO imperative forms — ALL BANNED. Use English for instructions.
- NO verb conjugation of any kind
- Allowed: bare nouns, noun phrases using known letters

METALANGUAGE:
- All terminology English-first with Ukrainian in parentheses

DECODABLE VOCABULARY (M2 — only letters: І, А, В, Е, И, К, Л, М, Н, О, Р, С, Т, У):
Use ONLY these words in activities, reading drills, AND prose examples.
Any word with a letter outside this set will FAIL the decodability audit gate.
Video key words from the plan's pronunciation_videos section are exempt
(they are heard, not read), but must NOT appear in prose reading examples.

Available words: кіт, тато, рис, сир, місто, море, метро, ліс, вікно, стіл, молоко, кіно, око, слово, літо, масло, ніс, він, вона, рука, вік

If you need a word not on this list, check that ALL its letters are in the
allowed set above. Words with unknown letters need English translation.

## Textbook Reference Examples (from real Ukrainian буквар)

These are real exercises from Ukrainian 1st-grade primers. Use them as **inspiration for style and difficulty level** — notice how they use simple syllable combinations, short words, and build progressively. Do NOT copy them verbatim, but match their pedagogical approach and simplicity.

**Grade 1, zaharijchuk** — Сторінка 96:
```
94
Бачу Д, д (де). Чую [д], [д'].
д р і * д
д * т е л
дро-ва
две-рі
до-ріж-ка схо-ди
ве-ран-да
л е * і д *
 [ –    =  • –  – ]
 [ = • |  –•  – ]
 [ – • |  =•  =  ]
а
о
у
и
і
Д
да
до
ду
ди
ді
а
о
у
и
і
ад
од
уд
ид
ід
Д
бу-ди-нок
під-ві-кон-ня
дах
ди-мар
Д д
```

**Grade 1, zaharijchuk** — Сторінка 113:
```
111
	 Запиши слова, добираючи до кожного відпо-
відну схему.
   півень          ялинка               джміль
[ – =  = ]            [ =  |–  = ]            [ =  |–  – |–  ]
	 Розглянь малюнки.
	 Запиши слова — назви намальованих пред-
метів за групами: овочі та шкільне приладдя.
	 Розглянь малюнки.
	 Запиши слова — назви намальованих пред-
метів, які відповідають на питання хто?
	 Прочитай текст.
ВЕСНА
Настала весна. Прилетіли птахи. На 
березі шпаки.
	 Випиши речення, яке відповідає схемі.
    
```

**Grade 1, bolshakova** — Сторінка 24:
```
24
ЗВУКИ. ГОЛОСНІ І ПРИГОЛОСНІ
Ти вимовляєш різні звуки: голосні і приголосні. 
Голосні звуки утворюються за допомогою голосу.
Голосні почуєш в пісні,
І у темному у лісі, 
І коли дивуєшся,
І коли милуєшся.
Легко вимовляються, 
Весело співаються! 
Прочитай. Назви букви, які позначають голосні звуки.
ал – ам – ан 
ла – ма – на 
ул – ум – ун
ол – ом – он 
ло – мо – но 
лу – му – ну
 
Приголосні звуки утворюються 
за допомогою голосу і шуму.
Приголосні деренчать
І тихенько шелестять, 
Голосно свистя
```

**Grade 1, zaharijchuk** — Сторінка 78:
```
76
За мотивами казки Е. Мозера
Повторюємо разом
Приголосні звуки: 
тверді та глухі
	 Прочитай імена головних героїнь, чітко ви-
мовляючи перші звуки.
Зося, Сюзі.
	 Чи вони справжні подруги? Як одна з них до-
помогла іншій? Знайди та прочитай про це. 
	 Який із цих звуків вимовляємо дзвінко, з го-
лосом? А який — тільки із шумом? 
	 Перепиши виділене блакитним кольором ре-
чення. Підкресли букви, які позначають при-
голосні звуки. Вимов їх. 
— Так, але я 
сама не зможу.
— Дякую. Ти 
справжня моя 
```

**Grade 1, bolshakova** — Сторінка 79:
```
. . . . . . . . . . . . . . . . . . 44
Т т . . . . . . . . . . . . . . . . . . . . . . . . . . . 45
Тверді і пом’якшені  
приголосні звуки . . . . . . . . . . . . . . 45
Г г . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
Г г . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
Тверді і пом’якшені  
приголосні звуки . . . . . . . . . . . . . . 47
Ґ ґ . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
Ґ ґ . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
Е е  . . . . . .
```

---

## Writing Instructions

Write the lesson prose for **The Cyrillic Code II** (a1 track).

- **Target**: approximately 1200 words
- **Immersion**: TARGET: 5-15% Ukrainian, 85-95% English. ALL explanatory prose in English. ALL grammar explanations in English. ALL callout text in English. Ukrainian appears ONLY in: (1) example words/phrases in bold with stress mark and (English translation), (2) vocabulary items. If you write a paragraph, it MUST be in English. Ukrainian sentences max 10 words.
- **Engagement callouts**: 4+ across sections, at least 3 different types
- **Structure**: Follow the content_outline from `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-ii.yaml` — each section maps to an H2

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
| Вступ — Introduction | 150 |
| Голосні — The Vowels И, І, Е | 350 |
| Приголосні — The Consonants К, Р, В, Т | 350 |
| Перші слова — First Real Words | 250 |
| Підсумок — Summary | 100 |
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
- **Engagement callouts**: 4+
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

> **Why does this matter?**
>
> {2-3 sentences}

## {Section 1}
...

---

# Summary

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
