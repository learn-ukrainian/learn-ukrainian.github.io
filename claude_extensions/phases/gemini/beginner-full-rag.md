# Full Module Build: Content + Activities + Vocabulary (RAG-enabled)

> **You are {SKILL_IDENTITY}, writing in the voice of {PERSONA_VOICE}.**
>
> **Your task:** Build a complete beginner module — lesson content, practice activities, and vocabulary — in one pass.
> Writing content and activities together ensures consistency: the same words, the same gender pairings, the same phrases appear in both.
>
> **Output capacity: 65,000+ tokens.** Do NOT truncate.

---

## 1. Read These Files

| File | What to extract |
|------|----------------|
| `{RESEARCH_PATH}` | Background knowledge, engagement hooks |
| `{META_PATH}` | Section titles + word allocations, activity count targets |
| `{PLAN_PATH}` | Objectives, vocabulary_hints (source of truth) |
| `{QUICK_REF_PATH}` | Level constraints, immersion band |
| `{SCHEMA_PATH}` | Activity field definitions (`additionalProperties: false`) |

Read ALL files before writing anything.

---

## 2. Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them throughout your work** — not just at the start.

### Essential Tools (use for EVERY module)

| Tool | When to use | Example |
|------|------------|---------|
| `search_text` | Find how this topic is taught in real textbooks | `search_text("знахідний відмінок", grade=3)` |
| `verify_words` | Check Ukrainian words exist in VESUM before using them | `verify_words(["книга", "великий", "гарний"])` |
| `verify_lemma` | Get all inflected forms of a word | `verify_lemma("книга")` → nom/gen/dat/acc/... |

### Optional Tools (use when relevant)

| Tool | When to use |
|------|------------|
| `query_pravopys` | Spelling or grammar rules you're explaining |
| `query_grac` | Check if a word/phrase is actually used (frequency data) |
| `search_images` | Find relevant textbook illustrations |

### Your Workflow

1. **RESEARCH FIRST**: Before writing, search textbooks for how this topic is taught at grade {TEXTBOOK_GRADE} level:
   - Search for the topic keywords: `search_text("{TOPIC_KEYWORDS}", grade={TEXTBOOK_GRADE})`
   - Search for exercise patterns: `search_text("вправа {TOPIC_KEYWORDS}", grade={TEXTBOOK_GRADE})`
   - Search for dialogue models: `search_text("діалог {TOPIC_KEYWORDS}", grade={TEXTBOOK_GRADE})`
   - Study the pedagogical progression — how do real textbooks introduce this concept?
   - Study textbook dialogues — notice how speakers have **real situations** (market, classroom, street) and **natural responses** (not just echoing commands)

2. **VERIFY AS YOU WRITE**: Before using any Ukrainian word not in the word bank below, call `verify_words` to check it exists. Empty result = the word doesn't exist in standard Ukrainian. Do NOT use it.

3. **VERIFY ACTIVITIES**: After creating activities, batch-verify all Ukrainian words in your activity items with `verify_words`.

> **Since your students are English-speaking adults**, translate textbook exercise instructions to English while keeping Ukrainian content words. Adapt the pedagogical approach (progressive difficulty, real-world context) but not the language of instruction.

---

## 3. Constraints (apply to EVERYTHING you write)

### Grammar Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

### Word Bank (MANDATORY)

{DECODABLE_VOCABULARY}

{LEXICAL_SANDBOX}

**Rule:** Every Ukrainian word in your output — content AND activities — must come from this word bank. The "Allowed Forms" column shows exactly which inflected forms you may use. If a word isn't listed, express the concept in English.

### Immersion Target

{IMMERSION_RULE}

### Structural Containment (how to achieve immersion without code-switching)

**Three rules govern where each language appears:**

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "The informal command of **читати** (to read) is **читай**." Short phrases and grammatical fragments (e.g., comparing **Я йду** vs **Я іду**) may appear inline.

2. **Full Ukrainian sentences = structural containers only.** Any Ukrainian sentence (3+ words with a verb) must go in one of these containers — never in flowing prose paragraphs:
   - **Tables** — paradigms, vocabulary groups, gender sorting (highest immersion density)
   - **Bulleted example lists** — Ukrainian line + English gloss: `- **Читай книгу!** — Read the book!`
   - **Blockquote dialogues** — mini-conversations with labeled speakers
   - **Pattern boxes** — transformations: `читати → читай → читайте`

3. **Vary containers.** Never use the same container type twice in a row. Alternate between tables, example lists, dialogues, and pattern boxes to keep the rhythm natural.

### Style Rules

- Ukrainian section headers with English in parentheses: `## Наказовий спосіб (The Imperative Mood)`
- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No IPA or phonetic brackets**
- **Quotes**: Use «...» not "..."

---

## 4. Write the Lesson Content

Write **{TOPIC_TITLE}** for the {TRACK} track.

**Targets:**
- {WORD_TARGET}–{WORD_CEILING} words (under {WORD_TARGET} = FAIL)
- {ENGAGEMENT_MIN}+ callout boxes (`[!tip]`, `[!warning]`, `[!did-you-know]`, `[!culture]`)
- EXACT H2 titles from the outline below — missing/renamed sections fail validation

{EXACT_SECTION_TITLES}

### Section Word Budgets

{SECTION_BUDGET_TABLE}

### Writing Style

You're writing for someone seeing Ukrainian for the first time. English explains; Ukrainian is what they're learning.

Follow the structural containment rules above. In each section:
1. **Explain** the concept in an English paragraph (with Ukrainian vocabulary bolded inline)
2. **Show** the pattern in a Ukrainian structural container (table, example list, dialogue, or pattern box)
3. **Reinforce** with a callout box (tip, warning, culture note, or fun fact)

Keep paragraphs short (3-5 sentences). Use {ENGAGEMENT_MIN}+ callout boxes spread across sections.

Do NOT use Ukrainian grammar terminology (іменник, дієслово, голосний) — students don't know these yet. Do NOT use words outside the word bank. Do NOT write IPA or Latin transliteration.

**Deliberate errors (showing common mistakes):**
When showing a wrong pattern to avoid, use strikethrough: ~~великий книга~~ → велика книга. This tells the validator the error is intentional. In activities, wrong forms in `options` arrays are always fine (they're distractors) — no special marking needed.

### Dialogue Quality (CRITICAL)

Every blockquote dialogue MUST have:
1. **A real situation** — where are the speakers? (market, classroom, street, home, café)
2. **A purpose** — why are they talking? (asking for help, giving directions, buying something)
3. **Varied responses** — the second speaker reacts naturally, not just echoes the command

**BAD** (echo drill — FORBIDDEN):
> — Читай!
> — Я читаю.
> — Пиши!
> — Я пишу.

**GOOD** (at a market — speakers have real goals):
> — Дайте, будь ласка, хліб.
> — Візьміть. Ще щось?
> — Покажіть це. Скільки?
> — Двадцять. Дивіться — свіжий!

Use your `search_text("діалог ...")` results as models for natural dialogue flow. Limit to **2-3 dialogues per module** in DIFFERENT situations. Dialogues should feel like real life, not grammar drills.

{SHARED_CONTENT_RULES}

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

{CHECKPOINT_GUIDANCE}

---

## 5. Create Activities (from YOUR content above)

After writing the content, create activities that practice the Ukrainian you just taught. This is why we do both in one pass — you know exactly which words, phrases, and gender pairings you used.

**Before creating activities:** Search textbooks for exercise examples:
- `search_text("вправа {TOPIC_KEYWORDS}", grade={TEXTBOOK_GRADE})` — find exercises on this topic
- `search_text("знайди визнач добери", grade={TEXTBOOK_GRADE})` — find exercise instruction patterns
- `search_text("з'єднай підкресли", grade={TEXTBOOK_GRADE})` — find matching/sorting patterns
- Study how real textbooks test this specific skill — adapt the exercise structure (not the language of instruction) for English-speaking adults
- **After creating activities:** call `verify_words` on ALL Ukrainian words in your items/options/answers

**Targets:**
- {ACTIVITY_MIN}–{ACTIVITY_MAX} activities
- Required types: {REQUIRED_TYPES}
- {VOCAB_COUNT_TARGET} vocabulary items

### Item Minimums (HARD FAIL if under)

{ITEM_MINIMUMS_TABLE}

### Which Activity Types to Use

**ALLOWED:** {ALLOWED_ACTIVITY_TYPES}
**FORBIDDEN:** {FORBIDDEN_ACTIVITY_TYPES}

Choose types based on what the constraints allow:

| Constraint level | Use these | Avoid these |
|-----------------|-----------|-------------|
| Letters/syllables only (M1-M10) | quiz, match-up, group-sort, anagram, true-false | fill-in, unjumble, cloze, translate |
| Words + simple phrases | + fill-in, match-up with phrases | unjumble, cloze |
| Basic sentences allowed | + unjumble, fill-in with sentences, translate | cloze (needs 14+ blanks) |

### Language Rules (A1/A2)

- **Questions, instructions, explanations** → English (students can't read Ukrainian metalanguage)
- **Content being practiced** → Ukrainian (words, letters, phrases from the lesson)
- **Options** → Ukrainian when choosing Ukrainian words, English when choosing concepts
- Never use grammar terms like іменник, дієслово, відмінок

### Consistency Rules (the whole point of single-pass)

1. **Same words**: Every Ukrainian word in activities must appear in your content above
2. **Correct agreement in answers**: Activity `answer` fields must have correct adj-noun gender agreement. If you wrote `великий стіл` in content, the correct answer in activities must also be `великий стіл` — NOT `велика стіл`
3. **Wrong forms are OK as distractors**: In `options` arrays, wrong gender/case forms are expected — they're the incorrect choices. Example: `options: ["нова", "новий", "нове", "нові"]` for a feminine noun — only `нова` is correct, the rest are intentional distractors
4. **Same forms**: If content uses `книга` (nominative), don't use `книги` (genitive) in the `answer` unless genitive is in the word bank

### Activity Schemas (EXACT field structures — any unlisted field = FAIL)

**quiz** — English questions, Ukrainian options:
```yaml
- type: quiz
  title: "Check Your Knowledge"
  instruction: Choose the correct answer.   # optional
  items:  # minItems: 6
    - question: "What does мама mean?"      # ≥5 words
      explanation: "Мама means mom."        # at QUESTION level, NOT inside options
      options:                              # exactly 4, exactly 1 correct
        - text: "mom"
          correct: true
        - text: "dad"
          correct: false
        - text: "sister"
          correct: false
        - text: "brother"
          correct: false
```

**anagram** — letter scramble (M1-M10 ONLY, not M11+):
```yaml
- type: anagram
  title: "Unscramble the Word"
  instruction: "Rearrange the letters."     # optional
  items:  # minItems: 8
    - scrambled: "А М А М"                  # SPACE-SEPARATED, same letters as answer
      answer: "МАМА"
```

**unjumble** — sentence word reorder (M11+ ONLY, not M1-M10):
```yaml
- type: unjumble
  title: "Put the Words in Order"
  items:  # minItems: 8
    - words: ["книга", "Це", "нова"]        # array of strings
      answer: "Це нова книга"               # single string
```
Do NOT use `sentence`, `jumbled`, or `scrambled` — only `words` + `answer`.

**match-up**:
```yaml
- type: match-up
  title: "Match the Pairs"
  pairs:  # minItems: 6, use "pairs:" NOT "items:"
    - left: "книга"
      right: "book"
```

**fill-in** — MUST include `options`:
```yaml
- type: fill-in
  title: "Complete the Sentence"
  items:  # minItems: 6
    - sentence: "Це ___ стіл."
      answer: "великий"
      options: ["великий", "велика", "велике", "великі"]  # exactly 4, answer must be in list
```

**group-sort**:
```yaml
- type: group-sort
  title: "Sort by Gender"
  groups:  # 2-4 groups
    - name: "Masculine"
      items: ["стіл", "брат", "дім"]
    - name: "Feminine"
      items: ["книга", "мама", "мова"]
```

**true-false**:
```yaml
- type: true-false
  title: "True or False?"
  items:  # minItems: 8
    - statement: "The letter Н makes the same sound as English H."
      correct: false
      explanation: "Н looks like H but sounds like N."
```

### Vocabulary YAML

- **Object with `items:` wrapper** (not bare list)
- Each entry: `lemma`, `translation`, `pos` (required); `gender`, `notes`, `usage`, `example` (optional)
- NO `ipa` field
- Include ALL words from `vocabulary_hints` in the plan

### YAML Formatting (HARD FAIL)

**Content** uses Ukrainian quotes «...». **YAML values** must NOT use «» — they break parsing with colons.

```yaml
❌ WRONG:  title: «Знайдіть пару: термін»
✅ RIGHT:  title: 'Знайдіть пару: термін'
```

Rules for YAML:
1. Never use `«»` — use plain text or single/double quotes
2. Quote any value containing `:` with single quotes
3. No IPA, no Latin transliteration in YAML values

---

## 6. Self-Audit Before Output

{SELF_AUDIT_SNIPPET}

### Content Checks
- [ ] Word count ≥ {WORD_TARGET}?
- [ ] Every plan section has prose?
- [ ] {ENGAGEMENT_MIN}+ callout boxes?
- [ ] No words outside the word bank?
- [ ] No Russianisms, Russian characters, IPA?
- [ ] No bilingual ping-pong? (Scan for Ukrainian sentence → English translation in the same paragraph. If found, move the Ukrainian to a table, list, or dialogue.)

### Activity Checks
- [ ] {ACTIVITY_MIN}–{ACTIVITY_MAX} activities?
- [ ] Every Ukrainian word also appears in content?
- [ ] Adjective-noun pairings match content?
- [ ] Quiz: exactly 1 `correct: true`, `explanation` at question level?
- [ ] Anagram: scrambled letters = answer letters?
- [ ] Fill-in: `answer` appears in `options`?
- [ ] Match-up: uses `pairs:` not `items:`?
- [ ] No extra fields (schema is `additionalProperties: false`)?
- [ ] No `hint` fields in any activity items?

### VESUM Verification (RAG-specific)
- [ ] Called `verify_words` on all Ukrainian words in activities?
- [ ] No words with empty VESUM results in final output?

---

## 7. Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

Output FOUR blocks in this exact order:

**Block 1: Content**
```
===CONTENT_START===

<!-- SCOPE
Covers: {what this module teaches}
Not covered:
  - {related topic} → {slug}
-->

# {Title}

> **{INTRO_HOOK}**
>
> {2-3 sentences}

## {Section 1}
...

---

# {SUMMARY_HEADING}

{Summary + 3-4 self-check questions. Each question includes English translation.}

---

===CONTENT_END===
```

**Block 2: Word Counts**
```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: {WORD_TARGET})
===WORD_COUNTS===
```

**Block 3: Activities (BARE LIST — no `activities:` wrapper)**
```
===ACTIVITIES_START===

- type: quiz
  title: "..."
  items:
    ...

- type: match-up
  title: "..."
  pairs:
    ...

===ACTIVITIES_END===
```

**Block 4: Vocabulary (object with `items:` wrapper)**
```
===VOCABULARY_START===

items:
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"

===VOCABULARY_END===
```

**Block 5: Friction Report (MANDATORY)**
```
===FRICTION_START===
**Phase**: Full Build (Content + Activities + Vocabulary)
**Step**: {what you were doing when friction occurred, or "Complete build"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | WORD_BANK_LIMITATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
**RAG Tools Used**: {list tools called and what you found useful}
===FRICTION_END===
```
