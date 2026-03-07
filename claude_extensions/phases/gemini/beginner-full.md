# Full Module Build: Content + Activities + Vocabulary

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

## 2. Constraints (apply to EVERYTHING you write)

### Grammar Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

### Word Bank (MANDATORY)

{DECODABLE_VOCABULARY}

{LEXICAL_SANDBOX}

**Rule:** Every Ukrainian word in your output — content AND activities — must come from this word bank. The "Allowed Forms" column shows exactly which inflected forms you may use. If a word isn't listed, express the concept in English.

### Level Rules

- **Immersion**: {IMMERSION_RULE}
- **How to achieve immersion through STRUCTURE** (ordered best → weakest):
  1. **Tables** (BEST) — conjugation paradigms, vocabulary groups, gender sorting. Every cell is Ukrainian = highest immersion density with zero readability cost
  2. **Pattern boxes** — `Наприклад: читати → читай → читайте` — show transformations clearly
  3. **Inline bold** — weave Ukrainian INTO English prose: "The word **книга** (book) belongs to the feminine group." This is the DEFAULT for body paragraphs.
  4. **Mini-dialogues** — 2-4 lines, labeled speakers (— Мама: / — Син:), with English gloss per line
  5. **Example sentences** (USE SPARINGLY) — 2-4 per grammar point, each on its own line with English translation. Only for illustrating a rule AFTER explaining it in English.
- **BANNED PATTERNS** (these cause automatic rewrites):
  - **Bilingual ping-pong**: alternating bold Ukrainian sentence → italic English translation, line after line. This is NOT teaching — it's a parallel text dump.
  - **Paragraph dump**: 5+ Ukrainian sentences followed by block English translation.

  ```markdown
  BAD (bilingual ping-pong — BANNED):
  **Ми використовуємо наказовий спосіб.**
  *We use the imperative mood.*

  **Є дві форми.**
  *There are two forms.*

  GOOD (inline bold — DEFAULT for body text):
  We use the imperative mood (**наказовий спосіб**). There are two forms: informal for **ти** and formal for **ви**.

  GOOD (table — BEST for paradigms):
  | Infinitive | ти-command | ви-command |
  |---|---|---|
  | читати | читай | читайте |
  ```
- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No IPA or phonetic brackets**
- **Quotes**: Use «...» not "..."

---

## 3. Write the Lesson Content

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

**Do:**
- Write body paragraphs in ENGLISH with Ukrainian words **bolded inline**: "The informal command of **читати** (to read) is **читай**."
- Use tables for conjugation paradigms, vocabulary groups, and comparisons
- Use pattern boxes to show transformations: `читати → читай → читайте`
- Put example sentences AFTER the English explanation, not instead of it
- Short paragraphs (3-5 sentences), plenty of callout boxes
- Vary your immersion patterns — tables, inline bold, dialogues, pattern boxes

**Don't:**
- Bilingual ping-pong (see BANNED PATTERNS above)
- Use grammar terminology (іменник, дієслово, голосний) — they don't know these
- Use words outside the word bank
- Write IPA or Latin transliteration
- Create sentences if constraints forbid them

**Deliberate errors (showing common mistakes):**
When showing a wrong pattern to avoid, use strikethrough: ~~великий книга~~ → велика книга. This tells the validator the error is intentional. In activities, wrong forms in `options` arrays are always fine (they're distractors) — no special marking needed.

{SHARED_CONTENT_RULES}

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

{TEXTBOOK_EXAMPLES}

{CHECKPOINT_GUIDANCE}

---

## 4. Create Activities (from YOUR content above)

After writing the content, create activities that practice the Ukrainian you just taught. This is why we do both in one pass — you know exactly which words, phrases, and gender pairings you used.

**Targets:**
- {ACTIVITY_MIN}–{ACTIVITY_MAX} activities
- Required types: {REQUIRED_TYPES}
- {VOCAB_COUNT_TARGET} vocabulary items

### Item Minimums (HARD FAIL if under)

{ITEM_MINIMUMS_TABLE}

{TEXTBOOK_ACTIVITY_EXAMPLES}

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

## 5. Self-Audit Before Output

{SELF_AUDIT_SNIPPET}

### Content Checks
- [ ] Word count ≥ {WORD_TARGET}?
- [ ] Every plan section has prose?
- [ ] {ENGAGEMENT_MIN}+ callout boxes?
- [ ] No words outside the word bank?
- [ ] No Russianisms, Russian characters, IPA?
- [ ] No bilingual ping-pong? (Scan for bold Ukrainian sentence → italic English on next line. If you find 3+ instances, rewrite those paragraphs using inline bold instead.)

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

---

## 6. Output Format

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
===FRICTION_END===
```
