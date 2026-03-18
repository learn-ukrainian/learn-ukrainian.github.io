You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
**Curriculum context:** This is Module 17 of the A1 track (Ukrainian for English speakers). Title: "Reflexive Verbs (-ся)" — Actions Directed at Oneself. Phase: A1.2 [Verbs & Sentences]. Previous module: The Living Verb Ii. Next module: Questions And Negation.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/reflexive-verbs-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/reflexive-verbs.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Reflexive particle -ся/-сь Conjugation of reflexive verbs", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 16
**Previous module:** The Living Verb II

**Cumulative vocabulary (202 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, ніс, мак, сік, стіл, тут, там, привіт, дякую, це
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, сало, хліб
зуб, дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок
сіль, люди, суп, вода, цибуля, люк, Львів, кінь, осінь, м'ясо
п'ять, сім'я, м'яч, цукор, час, чай, черепаха, що, щастя, факт
джерело, бджола, дзвін, склад, голосний, приголосний, перенесення, сестра, вікно, ґудзик
пальці, книга, вулиця, автобус, брат, море, ніч, земля, серце, сонце
машина, ім'я, артефакт, зона, укриття, добрий ранок, добрий день, добрий вечір, до побачення, будь ласка
вибачте, перепрошую, дуже приємно, пане, пані, бувай, здрастуйте, ласкаво просимо, на все добре, добраніч
ти, ви, як справи, я, він, вона, воно, ми, вони, хто
студент, студентка, українець, українка, вчитель, вчителька, звати, ось, друзі, цей
ця, ці, той, та, те, ті, телефон, кімната, стілець, ліжко
лампа, шафа, двері, ніж, ложка, крісло, диван, новий, старий, гарний
великий, малий, добрий, поганий, цікавий, синій, червоний, молодий, дорогий, дешевий
смачний, зелений, рідний, білий, чорний, жовтий, сорочка, штани, сукня, куртка
светр, плаття, джинси, окуляри, вишиванка, колір, одяг, прапор, бордо, одні
дитина, людина, гроші, очі, ножиці, маленький, говорити, робити, бачити, любити
їсти, пити, ходити, просити, сидіти, стояти, платити, вчити, дивитися, борщ
парк, школа

**Grammar already taught (56 topics):**
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
- T-V distinction
- Imperative forms in politeness expressions
- Personal pronouns
- Zero copula construction
- Demonstrative це
- Demonstratives цей/ця/це/ці (this)
- Demonstratives той/та/те/ті (that)
- Gender agreement with demonstratives
- Adjective endings for gender (m/f/n)
- Hard stem adjectives (-ий/-а/-е/-і)
- Soft stem adjectives (-ій/-я/-є/-і)
- Color adjectives with agreement
- Clothing vocabulary
- Adjective + noun gender agreement with clothing items
- Noun plural formation
- Vowel alternation (і → о/е)
- Adjective plural agreement
- Cyrillic alphabet (all 33 letters)
- Noun gender (m/f/n)
- Adjective-noun agreement
- Plural formation
- First Conjugation pattern (-ати → -аю, -аєш...)
- Personal verb endings
- Imperfective aspect introduction
- Second Conjugation pattern (-ити → -у, -иш...)
- Consonant mutation patterns
- Irregular verbs

**Coming next (module after this):** Yes/no questions with чи, Question words, Negation with не
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- дивитися (to watch/look) — дивитися телевізор, дивитися на мене, дивитися у вікно; High Frequency (Top 100)
- сміятися (to laugh) — сміятися голосно, сміятися з жарту (Standard Ukrainian), сміятися до сліз; Medium-High frequency
- вмиватися (to wash oneself) — вмиватися холодною водою, вмиватися вранці; Medium frequency (Routine)
- одягатися (to dress oneself) — одягатися тепло, одягатися стильно, швидко одягатися; Medium frequency (Routine)
- називатися (to be called) — як це називається?, вулиця називається...; High Frequency (Identification)
- вчитися (to study) — вчитися в школі, вчитися добре, вчитися грати на гітарі; High Frequency (Academic)
- займатися (to do/engage in) — займатися спортом, займатися йогою, займатися бізнесом; Medium-High frequency
- повертатися (to return) — повертатися додому, повертатися з роботи пізно; High Frequency (Motion)

**Recommended** (use in your content to reach the vocabulary target):
- голитися (to shave) — routine context
- зупинятися (to stop) — physical motion
- знайомитися (to get acquainted) — reciprocal interaction
- цікавитися (to be interested) — psychological state; usually takes Instrumental case

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
Ukrainian sentences max 10 words. Mix container types.

### Videos
- **ULP 3-109 На побаченні – On a date in Ukrainian + Reflexive verbs** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=a27-PA_CQdw
  Score: 0.9 -- The video explicitly teaches about 'зворотні дієслова' (reflexive verbs) and specifically mentions 'дієслова які закінчуються на ся', which is the core topic of the module. It provides direct instructional content on the subject.
  Suggested placement: After Презентація: Форми та відмінювання (Presentation: Forms and Conjugation) -- The video serves as a direct instructional segment on the forms and concept of reflexive verbs, perfectly complementing the presentation section.
  Key excerpt: сьогодні ми поговоримо більше про так звані зворотні дієслова Це дієслова які закінчуються на ся.


### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S3 Ep109: On a date in Ukrainian + Reflexive verbs**
  URL: https://www.ukrainianlessons.com/episode109/
  Relevance: 0.6
  Topics: grammar, verbs, phrases, introductions, listening

- **ULP S1 Ep14: Likes and dislikes — common verbs in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode14/
  Relevance: 0.5
  Topics: grammar, verbs

### Blog Articles & Guides
- **Dobra Forma: Present Tense of -ся Verbs (First Conjugation)** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/23-1/
  Relevance: 0.6
  Topics: reflexive, verbs, conjugation, grammar

- **Dobra Forma: Present Tense of -ся Verbs (Second Conjugation)** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/23-2/
  Relevance: 0.6
  Topics: reflexive, verbs, conjugation, grammar

- **Dobra Forma: Past Tense of -ся Verbs** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/24-2/
  Relevance: 0.6
  Topics: past tense, reflexive, verbs, grammar


### Textbook References
- **Grade 4, Сторінка 190**
  Змінювання дієслів минулого часу
за родами (в однині) й числами......................................................146
Теперішній час. Змінювання дієслів теперішнього часу 
за особами й числами........

- **Grade 10, Сторінка 176**
  Дієслова із суфіксом -ся(-сь), які 
виражають зворотну дію, нази-
ваються зворотними: навчатися, 
закохатися. Сучасний дієслівний суфікс 
-ся(-сь) — це давня коротка фор-
ма зворотного займенника себе...

- **Grade 6, Сторінка 5**
  . . . . . . . . . . . . . . . . . . . 256
Присвійні займенники . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 259
Зворотний займенник себе. . . . ....

- **Grade 10, Сторінка 270**
  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 176
§ 71 Дві основи дієслова. Поділ дієслів на діє відміни. Словозміна діє...

- **Grade 11, Сторінка 221**
  . . . . . . . 33
§ 8 
Дієслово. Дієслівні форми  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 37
§ 9 
Паралельні форми вираже...






---

## 4. Outline

Write **Reflexive Verbs (-ся)** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ: Дзеркало дії (Introduction: Mirroring Action)` (~250 words)
  - Suffix -ся turns action back onto subject (мити → митися) — use the 'mirror' analogy to explain -ся (action reflecting back) per research notes.
  - -ся is short for 'себе' (self) — historically a separate word, now a bound morpheme that signals the action stays with the agent.
  - Cultural Hook: The 'Apology' Logic — contrast 'Вибачаюсь' (I excuse myself, implying self-forgiveness) vs correct 'Вибачте' (Excuse me, asking another) to show the semantic logic of -ся.
  - Learner error: The 'Myself' Redundancy — address the common mistake of saying 'Я мию себе' instead of the natural 'Я миюся'.
- `## Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)` (~350 words)
  - Phonetic Rule: Two forms based on the preceding sound — -ся (after consonants like 'миється') and -сь (after vowels like 'миюсь').
  - State Standard §4.2.4.1 alignment: Focus on present tense conjugation patterns using 'дивитися' (дивлюся, дивишся, дивиться, дивимося, дивитеся, дивляться).
  - Morphological Note: Mention past tense forms per Standard examples (сміявся, сміялася, сміялося, сміялися) to show the suffix persists across tenses.
  - Shibboleth Pronunciation: Mastering the long soft [ц':а] for '-ться' is a critical phonetic marker of Ukrainian identity, distinct from the hard Russian [ца].
- `## Семантичні групи (Semantic Groups)` (~300 words)
  - Type 1 — True Reflexive: Focus on daily routine (вмиватися, одягатися) — collocations: вмиватися холодною водою, одягатися стильно.
  - Type 2 — Reciprocal: Actions between two people (зустрічатися, вітатися, цілуватися) — emphasize that -ся here means 'each other'.
  - Type 3 — Lexicalized: Verbs that are always reflexive (сміятися, подобатися) — both 'сміятися з когось' and 'сміятися над кимось' are standard Ukrainian with slightly different nuances (з = laughing at/about, над = mocking/ridiculing).
  - Agent Confusion: Explicitly contrast 'називати' (to name something) with high-frequency 'називатися' (to be called/identified).
- `## Практика та застосування (Practice and Application)` (~300 words)
  - Transitive ↔ Reflexive Contrast: Drill pairs like 'мити тарілку' (washing a plate) vs 'митися' (washing oneself) to reinforce the 'mirror' concept.
  - Daily Routine Integration: Heavy application in routine contexts (вчитися в школі, повертатися додому, займатися спортом) preparing for module a1-25.
  - Conjugation Drills: Focus on the High-frequency verbs 'дивитися' and 'вчитися' to ensure automaticity in the present tense.
  - Social Interaction: Using 'знайомитися' and 'вітатися' in short dialogues to build confidence in reciprocal forms.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ: Дзеркало дії (Introduction: Mirroring Action) | 250+ |
| Презентація: Форми та відмінювання (Presentation: Forms and Conjugation) | 350+ |
| Семантичні групи (Semantic Groups) | 300+ |
| Практика та застосування (Practice and Application) | 300+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Reflexive particle -ся/-сь Conjugation of reflexive verbs", grade=3-5)` — find how textbooks teach this
2. **Write content** following the outline and lesson arc below
3. **Verify as you write**: `verify_words` on any Ukrainian word you're unsure about
4. **Create activities** from your content
5. **Verify activities**: batch `verify_words` on all activity items

### Beginner Lesson Arc

1. **WELCOME** — warm greeting, set context
2. **PREVIEW** — "By the end of this module, you'll be able to..."
3. **PRESENT** — the main content sections
4. **PRACTICE** — examples, dialogues, reading practice
5. **CELEBRATE** — in the final `## Підсумок` section, tell learners what they can now do

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
**Required types:** fill-in, fill-in, match-up, fill-in

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

GRAMMAR CONSTRAINTS (A1.2 — Verbs & Sentences):
Present tense verbs are fully available. Simple sentences.

ALLOWED:
- Present tense (я читаю, він іде, вони мають)
- Basic imperatives (читай/читайте, слухай/слухайте, дивись/дивіться)
- Infinitives in simple contexts (можна читати, треба слухати)
- Simple questions and answers

BANNED (too complex for A1.2):
- Past tense, future tense, conditionals
- Participles, passive voice
- Complex subordinate clauses

- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No colonial framing**: never define Ukrainian by comparing it to Russian. Don't say "unlike Russian..." or "not found in Russian." Present Ukrainian on its own terms
- **No IPA or Latin transliteration** — stress marks (´) only
- **Ukrainian quotes** in content: «...» | **YAML values**: plain text or single quotes (never «»)
- **Euphony** (у/в, і/й alternation): follow rules in the shared content rules section below — audit flags violations
- **YAML colon values**: quote with single quotes: `'text: with colon'`
- H2 titles must match the outline EXACTLY. You MAY add H3 sub-headings within H2 sections (e.g., for individual letters, grammar sub-topics)
- **MUST end with `## Підсумок`** with self-check questions

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


FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.

</prompt>

## The Plan

<plan>
module: a1-017
level: A1
sequence: 17
slug: reflexive-verbs
version: '2.0'
title: Reflexive Verbs (-ся)
subtitle: Actions Directed at Oneself
focus: grammar
pedagogy: PPP
phase: A1.2 [Verbs & Sentences]
word_target: 1200
objectives:
- Learner can identify reflexive verbs ending in -ся
- Learner can conjugate reflexive verbs in present tense
- Learner can explain difference between transitive and reflexive verbs
- Learner can use common reflexive verbs like дивитися, сміятися
content_outline:
- section: 'Вступ: Дзеркало дії (Introduction: Mirroring Action)'
  words: 250
  points:
  - Suffix -ся turns action back onto subject (мити → митися) — use the 'mirror' analogy to explain -ся (action reflecting
    back) per research notes.
  - -ся is short for 'себе' (self) — historically a separate word, now a bound morpheme that signals the action stays with
    the agent.
  - 'Cultural Hook: The ''Apology'' Logic — contrast ''Вибачаюсь'' (I excuse myself, implying self-forgiveness) vs correct
    ''Вибачте'' (Excuse me, asking another) to show the semantic logic of -ся.'
  - 'Learner error: The ''Myself'' Redundancy — address the common mistake of saying ''Я мию себе'' instead of the natural
    ''Я миюся''.'
- section: 'Презентація: Форми та відмінювання (Presentation: Forms and Conjugation)'
  words: 350
  points:
  - 'Phonetic Rule: Two forms based on the preceding sound — -ся (after consonants like ''миється'') and -сь (after vowels
    like ''миюсь'').'
  - 'State Standard §4.2.4.1 alignment: Focus on present tense conjugation patterns using ''дивитися'' (дивлюся, дивишся,
    дивиться, дивимося, дивитеся, дивляться).'
  - 'Morphological Note: Mention past tense forms per Standard examples (сміявся, сміялася, сміялося, сміялися) to show the
    suffix persists across tenses.'
  - 'Shibboleth Pronunciation: Mastering the long soft [ц'':а] for ''-ться'' is a critical phonetic marker of Ukrainian identity,
    distinct from the hard Russian [ца].'
- section: Семантичні групи (Semantic Groups)
  words: 300
  points:
  - 'Type 1 — True Reflexive: Focus on daily routine (вмиватися, одягатися) — collocations: вмиватися холодною водою, одягатися
    стильно.'
  - 'Type 2 — Reciprocal: Actions between two people (зустрічатися, вітатися, цілуватися) — emphasize that -ся here means
    ''each other''.'
  - 'Type 3 — Lexicalized: Verbs that are always reflexive (сміятися, подобатися) — both ''сміятися з когось'' and ''сміятися
    над кимось'' are standard Ukrainian with slightly different nuances (з = laughing at/about, над = mocking/ridiculing).'
  - 'Agent Confusion: Explicitly contrast ''називати'' (to name something) with high-frequency ''називатися'' (to be called/identified).'
- section: Практика та застосування (Practice and Application)
  words: 300
  points:
  - 'Transitive ↔ Reflexive Contrast: Drill pairs like ''мити тарілку'' (washing a plate) vs ''митися'' (washing oneself)
    to reinforce the ''mirror'' concept.'
  - 'Daily Routine Integration: Heavy application in routine contexts (вчитися в школі, повертатися додому, займатися спортом)
    preparing for module a1-25.'
  - 'Conjugation Drills: Focus on the High-frequency verbs ''дивитися'' and ''вчитися'' to ensure automaticity in the present
    tense.'
  - 'Social Interaction: Using ''знайомитися'' and ''вітатися'' in short dialogues to build confidence in reciprocal forms.'
vocabulary_hints:
  required:
  - дивитися (to watch/look) — дивитися телевізор, дивитися на мене, дивитися у вікно; High Frequency (Top 100)
  - сміятися (to laugh) — сміятися голосно, сміятися з жарту (Standard Ukrainian), сміятися до сліз; Medium-High frequency
  - вмиватися (to wash oneself) — вмиватися холодною водою, вмиватися вранці; Medium frequency (Routine)
  - одягатися (to dress oneself) — одягатися тепло, одягатися стильно, швидко одягатися; Medium frequency (Routine)
  - називатися (to be called) — як це називається?, вулиця називається...; High Frequency (Identification)
  - вчитися (to study) — вчитися в школі, вчитися добре, вчитися грати на гітарі; High Frequency (Academic)
  - займатися (to do/engage in) — займатися спортом, займатися йогою, займатися бізнесом; Medium-High frequency
  - повертатися (to return) — повертатися додому, повертатися з роботи пізно; High Frequency (Motion)
  recommended:
  - голитися (to shave) — routine context
  - зупинятися (to stop) — physical motion
  - знайомитися (to get acquainted) — reciprocal interaction
  - цікавитися (to be interested) — psychological state; usually takes Instrumental case
activity_hints:
- type: fill-in
  focus: Conjugate reflexive verbs
  items: 25
- type: fill-in
  focus: Choose -ся or -сь
  items: 15
- type: match-up
  focus: Transitive ↔ reflexive pairs
  items: 12
- type: fill-in
  focus: Daily routine conversations
  items: 6
connects_to:
- 'a1-14 (Checkpoint: First Contact)'
- a1-38 (My Daily Routine)
prerequisites:
- a1-16 (The Living Verb II)
persona:
  voice: Patient Supportive Tutor
  role: Yoga Instructor
grammar:
- Reflexive particle -ся/-сь
- Conjugation of reflexive verbs
- Transitive vs reflexive pairs
register: розмовний

</plan>

## Audit Gates

## Audit Gates (your content will be checked against these)

Level: A1
Word target: 1200
Word ceiling: ~1800 (exceeding = FAIL)
Min activities: 0
Min engagement boxes: 3
Min activity types: 0

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

## Check 1: Prompt Feasibility

Only report if:
- Two instructions **directly contradict** each other AND following one will FAIL a named gate
- A target is **mathematically impossible** to reach given the constraints
- A required gate has **zero guidance** in the prompt (literally missing, not "could be clearer")

**Gate names**: Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion.

## Check 2: Semantic False Friends (Russianisms)

These Ukrainian words exist in BOTH Ukrainian and Russian but have DIFFERENT meanings:

- **лук**: Russian meaning = onion, цибуля, onions; Ukrainian meaning = bow (weapon). Correct word for 'onion, цибуля, onions' → **цибуля**
- **город**: Russian meaning = city, місто, town; Ukrainian meaning = garden, vegetable patch. Correct word for 'city, місто, town' → **місто**
- **неділя**: Russian meaning = week, тиждень; Ukrainian meaning = Sunday. Correct word for 'week, тиждень' → **тиждень**
- **річ**: Russian meaning = speech; Ukrainian meaning = thing, item. Correct word for 'speech' → **промова**
- **шар**: Russian meaning = ball, sphere; Ukrainian meaning = layer. Correct word for 'ball, sphere' → **куля**
- **мешкати**: Russian meaning = to dawdle, to delay, dawdle; Ukrainian meaning = to live, to dwell. Correct word for 'to dawdle, to delay, dawdle' → **баритися**
- **лічити**: Russian meaning = to treat, to heal, treatment; Ukrainian meaning = to count. Correct word for 'to treat, to heal, treatment' → **лікувати**
- **наглий**: Russian meaning = arrogant, impudent, insolent; Ukrainian meaning = sudden, unexpected. Correct word for 'arrogant, impudent, insolent' → **зухвалий**
- **лаяти**: Russian meaning = to bark, bark, barking; Ukrainian meaning = to scold, to swear at. Correct word for 'to bark, bark, barking' → **гавкати**
- **палиця**: Russian meaning = finger; Ukrainian meaning = stick, cane. Correct word for 'finger' → **палець**
- **сварка**: Russian meaning = welding; Ukrainian meaning = quarrel, argument. Correct word for 'welding' → **зварювання**

**Only flag if the prompt USES or DEFINES a word with the Russian meaning.** Do NOT flag:
- Warnings about the false friend (e.g., "неділя ≠ week")
- Discussions explaining the difference
- Correct Ukrainian usage

## Check 3: Plan-Prompt Coherence

Compare the plan (above) to the rendered prompt. Check:
1. **Section coverage**: Every plan `content_outline` section has a matching section in the prompt
2. **Word target**: Plan's `word_target` matches the prompt's word budget
3. **Vocabulary**: All `vocabulary_hints.required` items appear in the prompt
4. **Objectives**: The prompt's instructions would achieve all plan `objectives`

Only flag if a plan section is **completely missing**, the word target **differs**, or required vocabulary is **absent**. Do NOT flag rewordings or extra scaffolding.

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, RUSSICISM, MISSING_PLAN_SECTION, PLAN_CONTRADICTION, WORD_TARGET_MISMATCH
      location: "where in the prompt"
      problem: "what's wrong"
      suggested_fix: "how to fix it"
      severity: HIGH  # or MEDIUM, LOW
```

If no issues: `prompt_preflight: {status: PASS, issues: []}`

Be SPECIFIC. Cite exact text.