# Beginner Content: Write the Lesson

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of Patient Supportive Tutor.

> **Your task: Write approximately 1200 words of clear, beginner-friendly content.**
> Be concise — students know nothing yet. Short, clear explanations. Every H3 gets {H3_WORD_RANGE} words. The activities do the teaching, not the prose. Do NOT pad with adjectives, motivational filler, or over-explained phonetics.

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## Files to Read

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-cyrillic-code-iv-research.md` | Research notes |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-iv.yaml` | Content outline with section word allocations |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-cyrillic-code-iv.yaml` | Objectives, vocabulary_hints |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries

(No video discoveries available)

### Per-Letter Pronunciation Videos (from plan — MANDATORY embeds)
*Credit: Anna Ohoiko — Ukrainian Lessons*

- **Full Playlist**: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV (link only, do not embed)

**Each letter below MUST get its video embedded in the corresponding H3 section. Use this EXACT markdown link format:**

- **Літера Й**: [Anna Ohoiko — Ukrainian Lessons — Й](https://www.youtube.com/watch?v=aq0cjB90s3w)
- **Літера Щ**: [Anna Ohoiko — Ukrainian Lessons — Щ](https://www.youtube.com/watch?v=QmBLieIuf6Q)
- **Літера Я**: [Anna Ohoiko — Ukrainian Lessons — Я](https://www.youtube.com/watch?v=yhSAf41LX8I)
- **Літера Ю**: [Anna Ohoiko — Ukrainian Lessons — Ю](https://www.youtube.com/watch?v=9JdIBYCTWGw)
- **Літера Є**: [Anna Ohoiko — Ukrainian Lessons — Є](https://www.youtube.com/watch?v=O0bwRyyBQSc)
- **Літера Ь**: [Anna Ohoiko — Ukrainian Lessons — Ь](https://www.youtube.com/watch?v=cJlal8XKBxo)
- **Літера Ї**: [Anna Ohoiko — Ukrainian Lessons — Ї](https://www.youtube.com/watch?v=UcjdjQXhAY8)
- **Літера Ц**: [Anna Ohoiko — Ukrainian Lessons — Ц](https://www.youtube.com/watch?v=u44eCjR2Oz8)
- **Літера Ф**: [Anna Ohoiko — Ukrainian Lessons — Ф](https://www.youtube.com/watch?v=haHRsFFZRQI)
- **Літера Ґ**: [Anna Ohoiko — Ukrainian Lessons — Ґ](https://www.youtube.com/watch?v=gNjHqjTW9WQ)

## Module Constraints (HARD FAIL if violated)

DECODABILITY (M4 — full 33-letter alphabet now complete):
- No letter restrictions — all Ukrainian words are decodable after this module.

GRAMMAR BAN (no verbs exist yet):
- NO imperative forms — BANNED. English for instructions.
- NO verb conjugation
- Allowed: bare nouns, noun phrases, Це + noun (preview)

METALANGUAGE: English-first, Ukrainian in parentheses



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

**Grade 1, zaharijchuk** — Сторінка 113:
```
111
	 Відшукай предмети, у назвах яких букв біль-
ше, ніж звуків.  Запиши їх.
	Прочитай склади. Відшукай слова із цими 
складами. Запиши їх.
	
-ріл-	
	
космос		
	
	
зірка
	
-зор	
	
тарілка		
	
	
міст
	
-мос 	
	
телевізор	 	
	
друзі
	 Відшукай предмети, у назвах яких є звук [з′], 
звук [д′], два звуки [е]. Обведи.
	 Перепиши слово разом зі схемою, яка йому 
відповідає.
	
 біла 	
коник	   зірка 	    сльози
 [–  =  |–  ] 	       [=  | –  ]       [–  |–  –] 	     [=  –| –  ]
```

**Grade 1, zaharijchuk** — Сторінка 69:
```
67
Прочитай виділені слова в тексті. Які звуки ти чуєш на 
початку слів? Які букви позначають звуки [дз], [дз′]? 
Прочитай усі слова, у яких є буквосполучення дз. 
Джмелик запропонував дружбу метелику, дзвіночку 
чи бджілці? Який джмелик: увічливий, мовчазний 
чи насуплений?
Скільки разів буквосполучення дз ужито в тексті?  
У якому слові — назві намальованого
предмета букв більше, ніж звуків? 
Дзінь-дзінь, дзень-дзень! — це дзві-
ночок запрошує до себе джмелика.
—	Який барвистий луг! Тут так ба
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

---

## Writing Instructions

Write the lesson prose for **The Cyrillic Code IV** (a1 track).

- **Target**: approximately 1200 words
- **Immersion**: TARGET: 10-25% Ukrainian, 75-90% English. ALL explanatory prose in English. Grammar explained in English. Ukrainian in examples and short phrases only — always with English translations. Callout text in English. Ukrainian sentences max 10 words.
- **Engagement callouts**: **3+ MANDATORY** — spread across sections, at least 3 different types. Content with fewer than 3 callout boxes (> [!tip], > [!warning], etc.) FAILS validation.
- **Structure**: Follow the content_outline from `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-iv.yaml` — each section maps to an H2. **Write ALL sections. Do not skip any section, even short ones like Summary.** Missing sections fail validation.

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
| Злиті звуки та рідкісні букви — Affricates, Digraphs & Ґ | 300 |
| Йотовані голосні — Iotated Vowels Я, Ю, Є, Ї, Й | 350 |
| М'який знак та апостроф — Soft Sign & Apostrophe | 250 |
| Підсумок: Весь алфавіт — The Full Alphabet | 150 |
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
