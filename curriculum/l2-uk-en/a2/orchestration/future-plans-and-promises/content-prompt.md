# Module Build: Content + Activities + Vocabulary

## 1. Goal

> **You are Patient & Supportive Ukrainian Tutor, writing in the voice of Encouraging Cultural Guide.**
>
> Build a complete beginner module for English-speaking teens and adults learning Ukrainian at the a2 level. Your job: **search Ukrainian school textbooks using RAG tools**, then **adapt** the pedagogy for L2 learners.
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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/research/future-plans-and-promises-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a2/future-plans-and-promises.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A2.md` | Level constraints, immersion band |
| `schemas/activities-a2.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("imperfective future (буду + infinitive) perfective future (conjugated)", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 15
**Previous module:** The Completed Past

**Cumulative vocabulary (252 words):**
мені, тобі, йому, їй, нам, вам, їм, подобатися, допомагати, дзвонити
здаватися, потрібно, треба, необхідно, цікаво, нудно, весело, сумно, важко, легко
приємно, боляче, холодно, жарко, гарно, називний, займенник, прикметник, давальний, іменник
давати, дякувати, поріг, знахідний, множина, з, із, зі, разом, разом з
поруч з, гуляти, розмовляти, зустрічатися, вітатися, спілкуватися, жити, працювати, грати, дружити
товаришувати, приятелювати, посваритися, помиритися, знайомитися, друг, подруга, приятель, знайомий, сусід
колега, партнер, орудний, одружитися, подружитися, познайомитися, автобус, поїзд, машина, метро
таксі, ручка, олівець, ніж, виделка, ложка, трамвай, тролейбус, літак, комп'ютер
телефон, ножиці, голка, молоток, пензель, око, вухо, рука, голова, користуватися
дістатися, бути, стати, ставати, лікар, лікарка, вчитель, вчителька, програміст, програмістка
айтішник, айтішниця, інженер, інженерка, журналіст, журналістка, юрист, юристка, економіст, економістка
менеджер, менеджерка, спеціаліст, спеціалістка, громадянин, громадянка, директор, директорка, тестувальник, філологиня
в, на, під, над, перед, за, між, до, напроти, біля
коло, поруч, навколо, вздовж, всередині, ззовні, посеред, збоку, поміж, стіл
кімната, шафа, диван, вікно, для, без, через, про, після, о
об, завдяки, протягом, крім, замість, від, щодо, стосовно, внаслідок, заради
всупереч, по, причина, мета, тому що, бо, щоб, здоров'я, хто, що
кого, чого, кому, чому, ким, чим, на кому, на чому, відмінок, родовий
місцевий, кличний, однина, закінчення, відмінювати, прийменник, суддя, свідок, пошта, банк
лист, посилка, бандероль, марка, конверт, адреса, індекс, відправляти, отримувати, гроші
рахунок, картка, готівка, валюта, переказ, знімати, вкладати, обмінювати, курс, замовляти
обмін, долар, євро, правильно, помилка, виправити, перевірити, оцінка, робити / зробити, писати / написати
читати / прочитати, купувати / купити, пити / випити, їсти / з'їсти, ділити / поділити, говорити / сказати, брати / взяти, бачити / побачити, давати / дати, вчити / вивчити
продавати / продати, виходити / вийти, забувати / забути, вид, недоконаний, доконаний, процес, результат, тривалість, завершення
повторення, раптом, щодня, зробив, сказав, написав, прочитав, пішов, прийшов, зрозумів
забув, знайшов

**Grammar already taught (64 topics):**
- dative pronouns
- impersonal constructions
- подобатися
- потрібно
- states
- dative noun endings
- masculine dative (-ові/-у)
- feminine dative (-і)
- neuter dative (-у/-ові)
- plural dative (-ам)
- verbs + dative
- verbs + dative + accusative
- indirect objects
- verb government
- instrumental endings
- preposition з/із/зі
- accompaniment
- social interaction
- instrumental of means
- instrumental without prepositions
- transport
- tools
- бути + instrumental
- стати + instrumental
- працювати + instrumental
- past tense of бути
- prepositions of location
- prepositions of motion
- в/на + locative vs accusative
- під/за/над + instrumental
- prepositions of cause (через)
- prepositions of purpose (для)
- prepositions of time (після, до, о)
- other logical prepositions (про, без, крім)
- noun plural paradigms across all 7 cases
- genitive plural formation (ів/їв, zero ending)
- consonant alternation in Nominative plural
- irregular plural nouns
- animate vs inanimate distinction in Accusative plural
- adjective plural declension (all 7 cases)
- hard group endings (-і, -их, -им, -ими)
- soft group endings (-і, -іх, -ім, -іми)
- noun-adjective agreement in plural
- animate vs inanimate Accusative plural
- all 7 cases review
- case selection logic
- common prepositions
- case endings
- accusative for services (відправити листа)
- numbers 100-1000
- currency and exchange rates
- polite requests (я хочу...)
- case system review
- prepositions review
- case functions
- error correction
- imperfective aspect (process)
- perfective aspect (result)
- aspect pairs
- aspect usage rules
- perfective past tense
- formation of past tense
- narrative sequencing
- result-focused actions

**Coming next (module after this):** prefixes (про-, на-, з-, по-), suffixes (-ва-, -ува-), stem changes
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 25 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- зроблю (I will do/make) — зроблю все можливе, обов'язково зроблю; High frequency result marker
- напишу (I will write) — напишу листа, напишу повідомлення; High frequency for commitments
- скажу (I will say) — скажу правду, скажу завтра; Essential for future speech reporting
- буду (I will be/auxiliary) — буду чекати, буду працювати, буду там; Very high frequency auxiliary for process
- піду (I will go) — піду в кіно, піду додому; High frequency motion verb in simple future
- прочитаю (I will read) — прочитаю книгу до кінця; Focus on completion/result
- побачу (I will see) — побачу тебе завтра; Standard future greeting/observation
- почую (I will hear) — почую новини; Perception of future events
- візьму (I will take) — візьму участь, візьму трубку; Common collocation for participation
- дам (I will give) — дам слово; Directly linked to the cultural value of keeping promises
- прийду (I will come) — прийду вчасно; Essential for punctuality and reliability
- приїду (I will arrive) — приїду поїздом; Standard for travel and arrival plans
- почну (I will begin) — почну нове життя; Marking the inception of a future state
- закінчу (I will finish) — закінчу роботу; Marking the completion of a future state
- зрозумію (I will understand) — зрозумію тебе; Cognitive result in the future

**Recommended** (use in your content to reach the vocabulary target):
- забуду (I will forget) — ніколи не забуду; Often used in emotional promises
- запам'ятаю (I will remember) — запам'ятаю цей день; Used for shared future plans
- знайду (I will find) — знайду вихід; High-frequency problem-solving verb
- вийду (I will exit) — вийду на вулицю; Short-term physical plan
- увійду (I will enter) — увійду в історію; Ambitious goal-setting

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 45-65% Ukrainian.
LANGUAGE ROLES:
- THEORY: English prose for grammar explanations that would be too complex in Ukrainian at this level.
- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.
- HEADERS: Ukrainian with English in parentheses.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence. Ukrainian paragraphs and dialogues carry most content. English appears for grammar theory and in callout boxes.
A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles.







---

## 4. Outline

Write **Future Plans and Promises** for the a2 track.

**Targets:** 2000–3000 words | 4+ callout boxes | **10–15 activities total** (required types + additional types to reach minimum) | 25 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction)` (~325 words)
  - Future tense overview aligned with State Standard §4.2.3.1: distinguishing between the compound form for imperfective verbs (process) and the simple form for perfective verbs (result).
  - Cultural hook: Introduction of the proverb «Обіцянка — цяцянка, а дурневі — радість» (A promise is a toy...) to frame the importance and weight of future commitments in Ukrainian culture.
  - The concept of «тримати слово» (keeping one's word) as a motivator for mastering aspectual precision: why choosing the right verb form is the key to being understood as reliable.
- `## Презентація: Доконаний вид (Presentation: Perfective Future)` (~475 words)
  - Formation of the Simple Future: conjugating perfective verbs (скажу, закричу, поборю) and explaining that the form itself signals future completion without auxiliary verbs.
  - Addressing the 'Aspect Mismatch' error: Detailed correction of the common mistake «Я буду зробити» — explaining why the auxiliary «буду» can never be paired with a perfective infinitive.
  - Semantic power of results: how the perfective future (e.g., «напишу», «прийду») functions as a firm promise or a guarantee of a finished action.
- `## Презентація: Недоконаний вид (Presentation: Imperfective Future)` (~400 words)
  - Formation of the Compound Future: Mastery of the «буду + infinitive» structure (буду боротися, буду читати) to emphasize duration and ongoing processes.
  - The 'Process vs. Result' distinction: Contrasting marker words like «буду читати» (spending time reading) versus «прочитаю» (finishing the book/result) to clarify intent.
  - Pedagogical warning against the 'Overuse of Буду': Encouraging learners to move beyond the auxiliary shortcut and embrace perfective conjugations for specific promises.
- `## Практика та діалоги (Practice and Dialogues)` (~475 words)
  - Situational exchange: Planning a weekend versus making a solemn promise, using high-frequency collocations like «піду в кіно» and «зроблю все можливе».
  - Cultural nuance: Integrating the proverb «Обіцяного три роки ждуть» (One waits three years for what is promised) to discuss expectations and the reality of delayed fulfillment.
  - Drill on commitment signals: Transforming process-oriented plans (буду писати) into result-oriented promises (напишу) based on different conversational contexts.
- `## Висновок та застосування (Conclusion and Application)` (~325 words)
  - Summary of structural differences: 'I will do' (result = one word: зроблю) vs 'I will be doing' (process = two words: буду робити).
  - Production task: Drafting a response to a friend's invitation, making at least three specific promises using perfective future verbs (прийду, принесу, допоможу).
  - Final reflection on linguistic elegance: how the choice of aspect in the future tense reflects the speaker's agency and reliability.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ (Introduction) | 325+ |
| Презентація: Доконаний вид (Presentation: Perfective Future) | 475+ |
| Презентація: Недоконаний вид (Presentation: Imperfective Future) | 400+ |
| Практика та діалоги (Practice and Dialogues) | 475+ |
| Висновок та застосування (Conclusion and Application) | 325+ |
| **Total** | **2000+ (aim for ~2400)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("imperfective future (буду + infinitive) perfective future (conjugated)", grade=3-5)` — find how textbooks teach this
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
- Read `schemas/activities-a2.schema.json` for full field definitions.

**Allowed types:** quiz, true-false, fill-in, match-up, unjumble, mark-the-words, cloze, error-correction, group-sort, watch-and-repeat, classify, image-to-letter
**Forbidden types:** anagram, essay-response, critical-analysis, comparative-study, authorial-intent
**Required types:** fill-in, fill-in, quiz, fill-in, quiz

| Module range | Use these | Avoid these |
|-------------|-----------|-------------|
| M1-M4 (alphabet) | quiz, match-up, group-sort, anagram, true-false, fill-in, watch-and-repeat, image-to-letter, classify | unjumble, cloze, translate |
| M5-M10 | + unjumble, fill-in with sentences | cloze, translate |
| M11+ | all types including translate | cloze (needs 14+ blanks) |

### Item Minimums (HARD FAIL if under)

| Type | Minimum |
|------|--------|
| quiz | ≥8 items |
| true-false | ≥8 items |
| fill-in | ≥8 items |
| match-up | ≥8 pairs |
| unjumble | ≥6 items |
| mark-the-words | ≥6 items |
| error-correction | ≥6 items |
| group-sort | ≥8 items |

### Vocabulary YAML

Object with `items:` wrapper. Each entry: `lemma` (dictionary form), `translation`, `pos`. Optional: `gender`, `notes`, `usage`, `example`. No `ipa` field.

---

## 6. Hard Constraints



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
