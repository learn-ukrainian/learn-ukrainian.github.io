You are about to build a module using the prompt below. This prompt has been carefully engineered to produce content that passes all audit gates. Your job is to confirm it is ready.

**Default answer: PASS.** This prompt is designed to work. Only report issues if something will genuinely cause an audit gate to FAIL.

## The Prompt

<prompt>
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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-living-verb-ii-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-living-verb-ii.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Second Conjugation pattern (-ити → -у, -иш...) Consonant mutation patterns", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 15
**Previous module:** The Living Verb I

**Cumulative vocabulary (236 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, хліб
зуб, дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок
сіль, люди, вода, люк, Львів, м'ясо, п'ять, сім'я, цукор, час
що, джерело, дзвін, осінь, м'яч, щастя, факт, бджола, дзеркало, черепаха
цибуля, кінь, сестра, дерево, вулиця, автобус, бібліотека, університет, склад, переніс
голосний, приголосний, острів, ґудзик, кава, чай, замок, писати, школа, добрий
далеко, наголос, інтонація, питання, відповідь, хата, книжка, дорога, кафе, він
вона, воно, книга, слово, мова, вікно, брат, ніч, море, сонце
земля, Добрий день, Добрий ранок, Добрий вечір, Привіт, До побачення, Па-па, Дякую, Будь ласка, Вибачте
Перепрошую, Так, Ні, Як справи?, Добре, Погано, Нормально, Чудово, Смачного, На здоров'я
Добраніч, це, я, ти, ми, ви, вони, хто, студент, студентка
українець, українка, вчитель, вчителька, ось, мене звати, особовий займенник, займенник, граматичний рід, рід
телефон, дуже приємно, давай на ти, удома, на роботі, підручник, паспорт, цей, ця, ці
той, та, те, ті, кімната, стілець, ліжко, лампа, шафа, двері
квартира, новий, старий, гарний, великий, малий, поганий, цікавий, синій, червоний
молодий, дорогий, дешевий, смачний, зелений, який, множина, білий, чорний, жовтий
бордо, беж, хакі, колір, сорочка, штани, сукня, плаття, куртка, светр
джинси, окуляри, носити, одягати, розмір, дієслово, друг, музей, машина, пісня
хлопець, зошит, ручка, словник, читати, говорити, знати, розуміти, питати, відповідати
перевіряти, де, рахунок, смачного, працювати, слухати, грати, чекати, думати, вивчати
відпочивати, лист, повідомлення, новини, музика, радіо

**Grammar already taught (53 topics):**
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

**Coming next (module after this):** Reflexive particle -ся/-сь, Conjugation of reflexive verbs, Transitive vs reflexive pairs
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- говорити (to speak) — говорити українською, говорити правду; High Frequency (Top 100). Part of the 'Hospitality Triad'.
- робити (to do) — робити домашнє завдання, робити покупки, робити вибір; High Frequency (Top 50). Note labial mutation: 'я роблю'.
- бачити (to see) — я бачу, радий бачити, бачити на власні очі; High Frequency (Top 200). Focus on result/faculty.
- любити (to love) — я люблю тебе, любити природу, любити читати; shares PIE root with 'люди' (people). Note labial mutation: 'я люблю'.
- їсти (to eat) — хотіти їсти, смачно їсти; Irregular: 'я їм', 'ти їси', 'він їсть'. Learner error: avoid 'я їджу'.
- пити (to drink) — пити каву, пити воду; High Frequency. Essential for cultural hospitality contexts.
- ходити (to walk) — ходити в парк, ходити до школи; involves mutation 'я ходжу' (д→дж).
- просити (to ask) — просити допомоги; involves mutation 'я прошу' (с→ш).

**Recommended** (use in your content to reach the vocabulary target):
- сидіти (to sit) — State Standard example for consonant mutation (я сиджу).
- стояти (to stand) — high frequency positional verb; note 'вони стоять' ending.
- платити (to pay) — useful for practical scenarios; involves mutation 'я плачу' (т→ч).
- вчити (to teach/learn) — вчити мову; frequent 2nd conjugation verb with 'и' stem.

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

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

### Videos
- **ULP 3-94 У піцерії – At the pizzeria + Sound changes between imperfective and perfective verbs in...** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=zVdb0g7KDC0
  Score: 0.9 -- The video explicitly discusses 'доконаний і недоконаний вид дієслів' (perfective and imperfective verbs) and 'чергування зміни' (sound changes/alternations), which directly corresponds to the module's 'Презентація: Моделі та мутації' section on verb paradigms and their transformations.
  Suggested placement: After Презентація: Моделі та мутації
  Key excerpt: сьогодні а тоді поговоримо ще трохи про доконаний і недоконаний вид дієслів а саме про чергування зміни які відбуваються при утворенні доконаного виду

- **ULP 1-34 | Going to the movies in Ukraine – Perfective verbs in Ukrainian** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=0sWUV72QiSU
  Score: 0.9 -- This video introduces the concept of 'perfective and imperfective verbs', which is a fundamental grammatical aspect directly related to the 'Paradigms and Mutations' of verbs, central to 'The Living Verb II' module.
  Suggested placement: After Презентація: Моделі та мутації (as a complementary resource to other aspect-focused videos)
  Key excerpt: to introduce to the concept of perfective and imperfective verbs

- **Ukrainian for beginners: Where are u from? Countries, languages | Genitive case,  Verb conjugations** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=xGrdJHym-9E
  Score: 0.9 -- The video explicitly states it teaches 'how to conjugate verbs of the first conjugation type'. Verb conjugation is a core concept for understanding 'Paradigms and Mutations' within 'The Living Verb II' module.
  Suggested placement: After Презентація: Моделі та мутації
  Key excerpt: how to conjugate verbs of the first conjugation type.

- **Ukrainian for beginners: Hobbies | Ukrainian music | Palatalization, Verb + infinitive, Noun cases** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=A49aZdwMz6k
  Score: 0.7 -- The video discusses 'verb plus infinitive construction'. While not as broad as aspect or conjugation, it covers a specific usage pattern of verbs, which is relevant to 'Practice: Errors and Automation' or 'Продукування та культурний контекст' for verb application.
  Suggested placement: After Практика: Помилки та автоматизація
  Key excerpt: verb plus infinitive construction

- **Cooking verbs in Ukrainian. Дієслова для готування.** (Bright Kids Ukrainian)
  URL: https://www.youtube.com/watch?v=_lvdp6hRm1U
  Score: 0.5 -- The video focuses on 'cooking verbs', which is a thematic vocabulary set. While it addresses 'дієслова', its specific focus does not directly align with the grammatical topics (e.g., paradigms, mutations, hospitality triad) of the module 'The Living Verb II'.
  Suggested placement: Not recommended for direct embedding within the current module structure due to thematic mismatch. Could be a supplementary resource if there's a section on thematic verb groups.
  Key excerpt: [музика] cooking [музика] мити чистити [музика] різати розбивати


### Blog Articles & Guides
- **Verb Aspect in Ukrainian** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/verb-aspect-in-ukrainian-differences/
  Relevance: 0.8

- **Ukrainian Verb Prefixes** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ukrainian-verb-prefixes/
  Relevance: 0.7


### Textbook References
- **Grade 4, Сторінка 134**
  134
282. 1. Спиши слова. До яких частин мови вони належать? 
Що в них спільного?
2. З одним словом (на вибір) склади і запиши речення.
283. 1. Розгляньте таблицю змінювання дієслів теперіш-
нього і ма...

- **Grade 4, Сторінка 152**
  Випишіть дієслова минулого часу 3-ї особи однини.
•  Випишіть дієслова неозначеної форми. Утворіть від них 
дієслова майбутнього часу. Поставте їх у формі 1-ї особи 
однини й множини. Наприклад: не за...

- **Grade 4, Сторінка 133**
  133
5. Від записаних тобою дієслів утвори форму майбутнього 
часу, яка відповідає на питання що буду робити? Зверни 
увагу, як змінюються такі дієслова.
Якщо форма дієслова майбутнього часу складаєтьс...

- **Grade 8, Сторінка 61**
  ІІ. Складіть два речення, використавши слова майструвати, виконувати, отримати 
(на вибір) як частини складених дієслівних присудків. ІІІ. Доберіть синоніми до виділених слів....

- **Grade 7, Сторінка 58**
  55
§ 25. Вид  дієслова
Перемагати, крутити, зігнути, пекти, зіграти, дати, ловити, виховати, 
говорити, брати, назвати, зібрати, шукати, смикати, зігріти, вивертати. 4. Виконайте завдання в тестовій ф...






---

## 4. Outline

Write **The Living Verb II** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ: Тріада гостинності (Introduction: The Triad of Hospitality)` (~250 words)
  - Introduction to Second Conjugation verbs (-ити): establishing this family as the second pillar of Ukrainian verbal action, focusing on ongoing and habitual meanings.
  - Cultural Motivator - The Triad of Hospitality: Establishing the verbs 'їсти' (to eat), 'пити' (to drink), and 'говорити' (to speak) as the core of Ukrainian social interaction, where connection is built through feeding and conversation.
  - Concept check: reviewing the difference between 'doing' (imperfective) and 'completing', anchoring the module in the learner's existing understanding of present tense from Module 06.
- `## Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)` (~375 words)
  - Systematic introduction of endings: -ити → -ю, -иш, -ить, -имо, -ите, -ять. Side-by-side comparison with First Conjugation (читати vs говорити) to highlight the critical vowel difference (е/є vs и/і).
  - State Standard competency (§4.2.4.1): Using 'сидіти' (я сиджу) as the primary model for consonant mutation (д→дж) in the first person singular.
  - Phonetic framing of the 'Labial L' in 'люблю' and 'роблю': teaching the epenthetic 'l' not just as a rule, but as a physical aid to separate labial consonants (б, п, в, м, ф) from the 'ю' sound.
  - The irregularity of 'їсти' (to eat): explicitly teaching the correct 'я їм' form and contrasting it with the common learner error 'я їджу' or 'я їстю'.
  - Distinction between 'бачити' (to see - result/faculty) and 'дивитися' (to watch - process) to prevent semantic confusion in early sentence building.
- `## Практика: Помилки та автоматизація (Practice: Errors and Automation)` (~300 words)
  - Contrastive drills to prevent Conjugation Mixing: identifying and correcting the habit of applying 1st conjugation endings to 2nd conjugation verbs (e.g., 'ти робиш' vs incorrect 'ти робеш').
  - Mutation Mastery: intensive 'Я'-form drills with verbs like 'ходити' (ходжу), 'сидіти' (сиджу), and 'платити' (плачу) to eliminate omission errors like 'я ходю' or 'я сидю'.
  - Sorting exercises: categorization of 1st and 2nd conjugation verbs to build structural intuition for vowel patterns in endings.
- `## Продукування та культурний контекст (Production and Cultural Context)` (~275 words)
  - Contextual Production: describing daily routines and interests using high-frequency collocations such as 'робити домашнє завдання', 'любити природу', and 'говорити українською'.
  - Deep Culture - The Etymology of 'Любити': exploring the PIE root (*lewdh-) shared with 'люди' (people) and 'людство' (humanity), illustrating how love is intrinsically linked to community belonging.
  - Social Ethics of Hospitality: discussing the weight of 'їсти' and 'пити' in hosting, noting that refusing a meal ('не їсти') can be perceived as a rejection of the host's goodwill.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ: Тріада гостинності (Introduction: The Triad of Hospitality) | 250+ |
| Презентація: Моделі та мутації (Presentation: Paradigms and Mutations) | 375+ |
| Практика: Помилки та автоматизація (Practice: Errors and Automation) | 300+ |
| Продукування та культурний контекст (Production and Cultural Context) | 275+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Second Conjugation pattern (-ити → -у, -иш...) Consonant mutation patterns", grade=3-5)` — find how textbooks teach this
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
**Required types:** fill-in, match-up, fill-in

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