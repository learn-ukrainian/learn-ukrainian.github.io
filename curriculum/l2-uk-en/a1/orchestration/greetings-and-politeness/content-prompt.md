# Module Build: Content + Activities + Vocabulary

## 1. Goal

> **You are Patient & Supportive Ukrainian Tutor, writing in the voice of Patient Supportive Tutor.**
>
> Build a complete beginner module for English-speaking teens and adults learning Ukrainian at the a1 level. Your job: **search Ukrainian school textbooks using RAG tools**, then **adapt** the pedagogy for L2 learners.
>
> **Output capacity: 65,000+ tokens.** Do NOT truncate.

**What L2 learners need** (that L1 textbooks assume):
1. Explicit grammar rules in English (L1 learners know intuitively)
2. Level-appropriate vocabulary only
3. Setting/purpose for dialogues (L1 assumes shared cultural context)

## 2. Scoring Dimensions

Your content will be scored on these 7 dimensions (see GEMINI.md for details):
1. **Experience Quality** — would the learner continue?
2. **Language Accuracy** — correct Ukrainian, no Russianisms
3. **Pedagogy** — clear progression, quick wins
4. **Activities** — variety, appropriate difficulty
5. **Beginner Safety** — warm tone, not overwhelming
6. **LLM Fingerprint** — natural voice, not robotic
7. **Linguistic Accuracy** — factual correctness

---

## 3. Context

### Input Files (read ALL before writing)

| File | What to extract |
|------|----------------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/greetings-and-politeness-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/greetings-and-politeness.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("T-V distinction Imperative forms in politeness expressions", grade=1-2)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 7
**Previous module:** The Gender Code

**Cumulative vocabulary (83 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, сестра
дерево, вулиця, автобус, бібліотека, університет, склад, переніс, голосний, приголосний, острів
сім'я, ґудзик, вода, кава, чай, замок, рука, писати, школа, добрий
далеко, наголос, інтонація, питання, відповідь, хата, книжка, дорога, кафе, він
вона, воно, книга, слово, мова, дім, вікно, брат, ніч, час
море, сонце, земля

**Grammar already taught (29 topics):**
- Full alphabet overview (33 letters)
- Sound-letter correspondence (букви vs звуки)
- Vowel vs consonant classification
- Basic syllable blending and word reading
- Base vowel pronunciation (А О У Е И І)
- Iotated vowels dual function (Я Ю Є Ї)
- И vs І distinction
- Word stress basics (наголос)
- Vowel purity rule (no reduction)
- Sonorant consonants (Л М Н Р В)
- Voiced/voiceless consonant pairs
- No final devoicing rule
- Hard/soft consonant distinction
- Г vs Ґ distinction
- Soft sign palatalization (Ь)
- Apostrophe function and rules
- Affricates (Ц, Ч, Щ)
- Digraphs (ДЖ, ДЗ)
- Ф — rare native, common in borrowings
- Full alphabet mastery
- Syllable structure
- Open and closed syllables
- Word division rules
- Word stress
- Stress mobility
- Intonation patterns
- Three-gender system
- Declension families overview
- Gender prediction rules

**Coming next (module after this):** Personal pronouns, Zero copula construction, Demonstrative це
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- привіт (hello, informal) — Top 200 word; the universal casual greeting among friends and peers
- добрий ранок (good morning) — formal morning greeting; collocations: Добрий ранок, пане/пані!
- добрий день (good afternoon) — formal daytime greeting; the safest default greeting; Top 100 collocation
- добрий вечір (good evening) — formal evening greeting; used after approximately 18:00
- до побачення (goodbye) — formal farewell; literally 'until seeing'; Top 300 collocation
- дякую (thank you) — Top 100 word; collocations: дуже дякую, щиро дякую
- будь ласка (please/you're welcome) — Top 100 collocation; dual function as request marker and response to thanks
- вибачте (excuse me, formal) — Top 500 word; used to get attention or apologize politely
- перепрошую (I apologize) — formal apology; more sincere than вибачте
- дуже приємно (pleased to meet you) — introduction formula; literally 'very pleasant'

**Recommended** (use in your content to reach the vocabulary target):
- бувай/бувайте (bye, informal/formal plural) — casual farewell; literally 'be well'
- здрастуйте (hello, formal) — alternative formal greeting; slightly old-fashioned but still used
- ласкаво просимо (welcome) — used when receiving guests; collocations: Ласкаво просимо до України!
- на все добре (all the best) — warm farewell formula; used in both formal and semi-formal contexts

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 15-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.
- UKRAINIAN CONTENT: Words and phrases inline bolded. Short example sentences in bulleted lists or tables — each with English gloss on the same line.
- TABLES: Word families, vocabulary groups, simple paradigm tables.
- PATTERN BOXES: Show transformations: `слово → слова` (word → words).
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian vocabulary. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
Ukrainian sentences max 10 words.

### Videos
- **Start learning UKRAINIAN: Greetings! How are you? What is your name? Personal pronouns in Ukrainian** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=3zZWCCS7igw
  Score: 1.0 -- This video comprehensively covers greetings, politeness phrases, and introductions, aligning perfectly with multiple sections of the module including Вітання, Ввічливість, and Знайомство.
  Suggested placement: After Знайомство (Introductions) - as it covers an extensive range of module topics.
  Key excerpt: Today we will learn personal pronouns, phrases of politess, how to say how are you and answer to it and keep a small talk conversation and also how to introduce yourself. Here we have greetings in the first column.

- **FMU 1-50 | Greetings in Ukrainian: informal, formal and fun! | 5 Minute Ukrainian** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=dtufctJhBrY
  Score: 0.9 -- Directly covers informal and formal greetings, which is highly relevant to the Вітання and potentially the Ти і Ви sections of the module.
  Suggested placement: After Вітання (Greetings) - as it explicitly discusses various ways to greet.
  Key excerpt: How to greet Someone in Ukrainian Привітик це Анна і новий епізод подкасту 5 хвилин української Today we will Talk more about thatвіtic and Other Ways To greet Someone вітатися to greet It Will Be formal informal and Some Fun Ways

- **Greetings & Farewell + Words of Politeness 💙💛 #ukrainianlanguage #ukrainianlessons** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=yXoHXF7Q6x8
  Score: 0.9 -- Provides a good overview of common greetings and politeness words, directly relevant to the Вітання and Ввічливість sections.
  Suggested placement: After Ввічливість (Politeness) - as it clearly lists phrases for greetings and politeness.
  Key excerpt: Добрий день. Good afternoon. Добрий вечір. Good evening. Доброго ранку. Good morning. Привіт. Hello. Будь ласка. Please or you welcome. Прошу. Here you go.

- **ULP 2-63 | Вітання зі святами | Ukrainian Holiday Greetings** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=cQQB8GX3zxM
  Score: 0.5 -- The video focuses on holiday-specific greetings, which is a sub-category of greetings, but not the primary focus of general greetings and politeness in this module.
  Suggested placement: After Вітання (Greetings) - as an extension covering specific greeting contexts.
  Key excerpt: я хочу вас навчити Як вітати зі святами українською щоб ви могли написати комусь повідомлення електронний лист чи надіслати листівку українцям тому якщо вам цікаво як українці вітають зі святами слухайте Цей урок


### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S1 Ep1: Informal Greetings in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode1/
  Relevance: 0.5
  Topics: phrases, greetings

- **ULP S1 Ep2: Formal Greetings and Saying Goodbye in Ukrainian + Pronouns**
  URL: https://www.ukrainianlessons.com/episode2/
  Relevance: 0.5
  Topics: grammar, pronouns, phrases, greetings, goodbyes

- **ULP S2 Ep63: Ukrainian Holiday Greetings**
  URL: https://www.ukrainianlessons.com/episode63/
  Relevance: 0.5
  Topics: grammar, cases, genitive, instrumental, culture

### Blog Articles & Guides
- **Talk Ukrainian: Greetings in Ukrainian** (talkukrainian)
  URL: https://talkukrainian.com/greetings/
  Relevance: 0.7
  Topics: greetings, hello, привіт, introductions

- **Polite Phrases in Ukrainian** (verba.school)
  URL: https://www.verba.school/post/polite-phrases-in-ukrainian
  Relevance: 0.6
  Topics: vocabulary, phrases, greetings, politeness


### Textbook References
- **Grade 1, Сторінка 97**
  95
—	 Доб-ро-го ран-ку! — мов-лю за 
зви-ча-єм. 
—	 Доб-ро-го ран-ку! — кож-но-му 
зи-чу  я. 
—	 Доб-ро-го  дня! — лю-дям ба-
жа-ю.
—	 Ве-чо-ра  доб-ро-го! — стріч-
них  ві-та-ю.
І  ус-мі-ха-ють-ся   ...

- **Grade 4, Сторінка 176**
  Довідка: доброзичливо, щиро, обов’язково, зацікав­
лено, шанобливо, мало, тактовно, привітно, небагато, 
приязно, спокійно, уважно, увічливо, удумливо, виразно, 
делікатно.
•  Порівняйте тексти вправ ...

- **Grade 11, Сторінка 217**
  Вибір вітального слова залежить від різних обставин. Уранці ми вико-
ристовуємо такі слова, як Добри± ранок або Доброго ранку Нині 
набу ває поширення остання ôорма, яка виражає побажання людин...

- **Grade 7, Сторінка 243**
  240
Етикетні формули прощання
До побачення… 
На все добре… 
До нових зустрічей… 
До зустрічі…
До завтра… 
Усього найкращого… 
Добраніч… 
Дозвольте попрощатися…
Етикетні формули побажання
Хай вам щасти...

- **Grade 7, Сторінка 9**
  РОЗВИТОК
МОВЛЕННЯ
6
1.	Прочитайте діалог «У громадському транспорті» та виконайте завдання. 
— Жінко в червоній сукні, ви виходите на наступній зупинці? 
— Ні, проходьте, будь ласка.
А.	 Хто з пасажир...






---

## 4. Outline

Write **Greetings and Politeness** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вітання (Greetings)` (~200 words)
  - Informal greeting: Привіт — used with friends, peers, and children; the universal casual hello
  - Formal time-based greetings: Добрий ранок (morning, until ~12:00), Добрий день (afternoon, ~12:00-18:00), Добрий вечір (evening, after ~18:00) — used with strangers, elders, and in professional settings
  - Goodbyes: До побачення (formal goodbye, literally 'until seeing'), Бувай/Бувайте (informal goodbye, literally 'be well'), На все добре (all the best)
  - When to use which: matching the greeting to the social context and time of day — using Добрий день as the safe default when unsure
- `## Ти і Ви (T-V distinction)` (~250 words)
  - Ти = singular informal: used with one person you know well — friends, family members, children, peers of your age
  - Ви = singular formal OR plural: used with one person you respect (stranger, teacher, elder, boss) OR with any group of two or more people
  - The safety rule: always start with Ви until explicitly invited to switch — the phrase 'Давай на ти?' (Shall we switch to ти?) signals the transition
  - Cultural importance: using Ти with a stranger or elder is considered rude and disrespectful in Ukrainian culture; this is more strictly observed than in many Western European cultures
- `## Ввічливість (Politeness)` (~250 words)
  - Дякую (thank you) — the universal expression of gratitude; can be intensified with Дуже дякую (thank you very much) or Щиро дякую (sincerely thank you)
  - Будь ласка (please/you're welcome) — dual function: used both when requesting something and when responding to thanks
  - Вибачте (excuse me, formal) vs Вибач (excuse me, informal) — used to get attention, apologize for a minor inconvenience, or interrupt politely
  - Перепрошую (I apologize) — a more formal and sincere apology than Вибачте; used when you have genuinely inconvenienced someone
  - Usage contexts: ordering at a cafe (Будь ласка, каву), bumping into someone (Вибачте!), receiving a gift (Дуже дякую!)
- `## Знайомство (Introductions)` (~250 words)
  - Asking names: Як вас звати? (formal) vs Як тебе звати? (informal) — literally 'How do they call you?'
  - Responding: Мене звати... (My name is...) — the standard self-introduction formula from State Standard §4.2.3.1
  - Pleased to meet you: Дуже приємно (very pleasant) or Приємно познайомитись (pleasant to meet) — said after exchanging names
  - Formal vs informal introductions: meeting a professor (Добрий день. Як вас звати? Мене звати... Дуже приємно.) vs meeting a classmate (Привіт! Як тебе звати? Я... Приємно!)
- `## Діалоги (Dialogues)` (~250 words)
  - Dialogue 1 — Meeting someone for the first time (formal): full greeting-introduction-farewell sequence using Ви, Добрий день, Як вас звати, До побачення
  - Dialogue 2 — Greeting a friend (informal): using Привіт, Як справи? (How are things?), Бувай with casual register
  - Dialogue 3 — Asking for something politely: using Вибачте to get attention, Будь ласка when requesting, Дякую when receiving
  - Dialogue 4 — Thanking and saying goodbye: combining gratitude expressions with appropriate farewell formulas for formal and informal contexts
- `## Підсумок — Summary` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вітання (Greetings) | 200+ |
| Ти і Ви (T-V distinction) | 250+ |
| Ввічливість (Politeness) | 250+ |
| Знайомство (Introductions) | 250+ |
| Діалоги (Dialogues) | 250+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("T-V distinction Imperative forms in politeness expressions", grade=1-2)` — find how textbooks teach this
2. **Write content** following the outline and lesson arc below
3. **Verify as you write**: `verify_words` on any Ukrainian word you're unsure about
4. **Create activities** from your content
5. **Verify activities**: batch `verify_words` on all activity items

### Beginner Lesson Arc

1. **WELCOME** — warm greeting, set context
2. **PREVIEW** — "By the end of this module, you'll be able to..."
3. **PRESENT** — the main content sections
4. **PRACTICE** — examples, dialogues, reading practice
5. **CELEBRATE** — in the final `## Підсумок — Summary` section, tell learners what they can now do

### Emotional Safety (scored — Beginner Safety dimension)

Use direct address ("you", "your") at least 15 times throughout the module. Include encouragement ("Great job!", "You're doing well", "Don't worry"), quick wins (learner reads their first word early), and reassurance ("This is normal", "Take your time"). The learner should feel supported, not overwhelmed.

### Writing Style

English explains; Ukrainian is what they're learning. In each section:
1. **Explain** the concept in English (with Ukrainian vocabulary **bolded inline**). Short Ukrainian phrases are fine inline.
2. **Show** with **5-10 Ukrainian examples** per grammar point using bulleted lists, dialogues, and pattern boxes.
3. **Reinforce** with a callout box (`[!tip]`, `[!warning]`, `[!note]`, `[!culture]`, `[!challenge]`, `[!practice]`)

Tables contribute zero to immersion. Use **dialogues** and **bulleted examples** for Ukrainian content.

**MANDATORY for A2+:** Reading Practice blocks after each major section (5-8 Ukrainian sentences + English translation).

**Grammar terminology by level:**
- A1 M1-M10: English terms in prose, bilingual section headings with em-dash: `## Голосні — Vowels`
- A1 M11+: Introduce Ukrainian terms with gloss: **іменник** (noun)
- A2+: Ukrainian terms freely after first gloss

### Dialogue Quality

**No echo drills.** For M5+: every dialogue MUST start with `> **(Location / Місце)**`, have a real situation, 4-6 dialogues, 4-8 lines each.

**Alphabet modules (M1-M10):** Include 4-5 micro-dialogues using decodable words + sight words. Keep them short (2-4 lines each) and conversationally natural. Good patterns:
- Greeting: `— Привіт! — Привіт!`
- Identification: `— Це кіт? — Так, це кіт.`
- Location: `— Молоко тут? — Ні, молоко там.`
- Combined: `— Мама тут? — Так, мама тут. А тато там.`

Every line must make conversational sense. Do NOT pair unrelated speech acts (e.g., "Це мама?" → "Дякую!" makes no sense). Use `search_text` to find real dialogue patterns from Grade 1 textbooks (Заhaрійчук, Большакова) and adapt them to the available letter set.

**Cite textbook adaptations:** `<!-- adapted from: {author}, Grade {N} -->`

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


### Activity Rules

- Activity **answers** must use words from your content. **Distractors** may use other level-appropriate words.
- Follow schemas exactly — `additionalProperties: false` means any unlisted field = FAIL.
- Read `schemas/activities-a1.schema.json` for full field definitions.

**Allowed types:** quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter
**Forbidden types:** cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent
**Required types:** match-up, quiz, fill-in, unjumble

| Module range | Use these | Avoid these |
|-------------|-----------|-------------|
| M1-M4 (alphabet) | quiz, match-up, group-sort, anagram, true-false, fill-in, watch-and-repeat, image-to-letter, classify | unjumble, cloze, translate |
| M5-M10 | + unjumble, fill-in with sentences | cloze, translate |
| M11+ | all types including translate | cloze (needs 14+ blanks) |

### Item Minimums (HARD FAIL if under)

| Type | Minimum |
|------|--------|
| quiz | ≥6 items |
| true-false | ≥6 items |
| fill-in | ≥6 items |
| match-up | ≥6 pairs |
| anagram | ≥6 items |
| unjumble | ≥6 items |
| group-sort | ≥8 items |
| watch-and-repeat | ≥1 items |
| classify | ≥1 items |
| image-to-letter | ≥5 items |

### Vocabulary YAML

Object with `items:` wrapper. Each entry: `lemma` (dictionary form), `translation`, `pos`. Optional: `gender`, `notes`, `usage`, `example`. No `ipa` field.

---

## 6. Hard Constraints

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

- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No colonial framing**: never define Ukrainian by comparing it to Russian. Don't say "unlike Russian..." or "not found in Russian." Present Ukrainian on its own terms
- **No IPA or Latin transliteration** — stress marks (´) only
- **Ukrainian quotes** in content: «...» | **YAML values**: plain text or single quotes (never «»)
- **Euphony** (у/в, і/й alternation): follow rules in the shared content rules section below — audit flags violations
- **YAML colon values**: quote with single quotes: `'text: with colon'`
- H2 titles must match the outline EXACTLY. You MAY add H3 sub-headings within H2 sections (e.g., for individual letters, grammar sub-topics)
- **MUST end with `## Підсумок — Summary`** with self-check questions

### Common Irregular Imperatives

If your module uses imperative verbs:
- взяти → **візьми/візьміть** (NOT ~~взяй~~)
- стояти → **стій/стійте** (NOT ~~стояй~~)
- сісти → **сядь/сядьте** (NOT ~~сісь~~)
- їсти → **їж/їжте** (NOT ~~їсь~~)

The Russian conjunction **"и"** (meaning "and") is forbidden. Use Ukrainian conjunctions **і**, **й** (after vowels), or **та**.

---

## 7. Output Format

> **Content outside delimiters is automatically discarded.**

Output FIVE blocks in this exact order (plus optional friction report):

**Block 1: Content** — `===CONTENT_START===` ... `===CONTENT_END===`
**Block 2: Word Counts** — `===WORD_COUNTS_START===` ... `===WORD_COUNTS_END===`
**Block 3: Activities** — `===ACTIVITIES_START===` ... `===ACTIVITIES_END===` (bare list, no wrapper)
**Block 4: Vocabulary** — `===VOCABULARY_START===` ... `===VOCABULARY_END===` (object with `items:`)
**Block 5: Builder Notes** — `===BUILDER_NOTES_START===` ... `===BUILDER_NOTES_END===`

### Builder Notes (MANDATORY)

```
===BUILDER_NOTES_START===
phase: CONTENT
status: SUCCESS | PARTIAL | BLOCKED
word_count: {actual}
deviations:
  - section: "{section}"
    reason: "{why}"
frictions:
  - type: TEMPLATE_CONSTRAINT | SCHEMA_MISMATCH | PLAN_GAP | RAG_FAILURE
    description: "{what went wrong}"
    proposed_fix: "{fix}"
research_gaps:
  - "{what you couldn't find}"
unverified_terms:
  - "{words you couldn't verify}"
review_focus:
  - "{what reviewer should check}"
rag_tools_used:
  - "{tool}: {query} → {result}"
===BUILDER_NOTES_END===
```

### Friction Report (OPTIONAL — only if you hit pipeline/schema issues)

```
===FRICTION_START===
**Phase**: Full Build
**Friction Type**: YAML_SCHEMA_VIOLATION | PLAN_GAP | CONTRADICTION
**Problem**: {what went wrong}
**Proposed Fix**: {how to fix the template/pipeline}
===FRICTION_END===
```
