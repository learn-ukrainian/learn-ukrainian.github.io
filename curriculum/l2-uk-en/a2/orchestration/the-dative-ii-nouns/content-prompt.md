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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/research/the-dative-ii-nouns-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a2/the-dative-ii-nouns.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A2.md` | Level constraints, immersion band |
| `schemas/activities-a2.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("dative noun endings masculine dative (-ові/-у)", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 1
**Previous module:** The Dative I — Pronouns

**Cumulative vocabulary (35 words):**
мені, тобі, йому, їй, нам, вам, їм, подобатися, допомагати, дзвонити
здаватися, потрібно, треба, необхідно, цікаво, нудно, весело, сумно, важко, легко
приємно, боляче, холодно, жарко, гарно, називний, займенник, прикметник, давальний, іменник
давати, дякувати, поріг, знахідний, множина

**Grammar already taught (5 topics):**
- dative pronouns
- impersonal constructions
- подобатися
- потрібно
- states

**Coming next (module after this):** verbs + dative, verbs + dative + accusative, indirect objects
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 25 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- давати (to give) — collocations: «давати пораду» (give advice), «давати відповідь» (give answer); core verb
- дарувати (to gift) — collocations: «дарувати квіти» (odd number!), «дарувати радість»; High frequency
- допомагати (to help) — collocations: «допомагати мамі», «допомагати у навчанні»; REQUIRES DATIVE (not Accusative)
- телефонувати (to call) — collocations: «телефонувати лікарю», «телефонувати подрузі»; REQUIRES DATIVE; distinct from «кликати»
- відповідати (to answer) — «відповідати вчителю», «відповідати на питання»; High frequency (Core)
- пояснювати (to explain) — «пояснювати правила», «пояснювати дорогу»
- розповідати (to tell) — telling a story or news to a recipient
- надсилати (to send) — digital/post: «надсилати листа», «надсилати повідомлення»
- личити (to suit) — «ця сукня тобі личить»; Medium frequency; used for clothing/style
- підходити (to suit) — something being suitable for someone
- заважати (to bother) — bothering or hindering someone
- вистачати (to be enough) — being sufficient for someone
- бракувати (to lack) — something missing/lacking for someone

**Recommended** (use in your content to reach the vocabulary target):
- радити (to advise) — giving advice to someone; High frequency in social contexts
- довіряти (to trust) — trusting someone; requires dative
- вірити (to believe) — believing someone; requires dative
- дозволяти (to allow) — allowing/permitting someone
- шкодити (to harm) — causing harm to someone/something; Standard §4.2.2.3 context
- показувати (to show) — showing a gift or the way

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

Write **The Dative II — Nouns** for the a2 track.

**Targets:** 2000–3000 words | 4+ callout boxes | **10–15 activities total** (required types + additional types to reach minimum) | 25 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction: The Recipient Concept)` (~325 words)
  - Building on dative pronouns from M01 — review «мені/тобі» as foundational examples and link to A1-09 (Nominative Plural) logic for dative plural foundations
  - Define the Dative case as the 'To/For' case for indirect objects — frame as the beneficiary or sufferer of an action per Standard §4.2.2.3 (на користь чи на шкоду)
  - Introduce the Dative for age expressions as a primary function — contextualize with the example «Дідусеві вісімдесят років» to establish the subject of a quantitative age trait
- `## Презентація: Чоловічий та середній рід (Presentation: Masculine and Neuter)` (~475 words)
  - Masculine endings (-ові/-еві vs -у) — emphasize -ові/-еві for animate nouns as more 'Ukrainian' and euphonious; contrast «студентові» and «братові»
  - Learner error: Masc Confusion — drill the distinction between Dative -у and Genitive -а/-у endings to prevent accidental case mixing in common sentences
  - Neuter endings (-у/-ові) — explain the use of -у as the primary ending, while noting the parallel with masculine patterns for certain noun types
  - Drill the 'Call' Trap — focus on «телефонувати лікарю» (Dat) vs. the English-influenced error «телефонувати директора» (Acc)
- `## Презентація: Жіночий рід та множина (Presentation: Feminine and Plural)` (~475 words)
  - Feminine endings (-і) and critical phonetic shifts — drill 'Consonant Shift Amnesia' focusing on velar shifts: г-з (нога-нозі), к-ц (рука-руці), х-с (муха-мусі)
  - Learner error: Mixing gender endings — address the tendency to apply masculine -у to feminine nouns (e.g., incorrect «маму» instead of «мамі»)
  - Plural endings (-ам/-ям) — emphasize the consistency of the -ам ending for plurals, building on established A1 Nominative Plural stems
  - Drill the 'Help' Trap — contrast the correct «допомагати мамі» (Dat) with the high-frequency error «допомагати маму» (Acc)
- `## Практика: Дієслова та етикет (Practice: Verbs and Etiquette)` (~400 words)
  - Dative-hungry verbs — focus on high-frequency social verbs: «дарувати» (gift), «відповідати» (answer), «пояснювати» (explain), and «радити» (advise)
  - Integrated Practice: Sentence transformation using gift-giving contexts — focus on typical dative recipients like «батькам», «вчителю», or «подрузі»
  - Practice the verb «личити» (Medium frequency) in descriptive contexts — use clothing and style examples: «ця сукня тобі личить»
  - Drill collocations for «давати» — including «давати пораду» (give advice) and «давати відповідь» (give an answer) to show abstract recipients
- `## Діалоги та культура (Dialogues and Culture)` (~325 words)
  - Cultural Hook: Flower Etiquette — simulate dialogues for buying flowers where characters insist on an odd number (1, 3, 5) for the living, noting that even numbers are for funerals
  - Cultural Hook: Taboo Gifts — roleplay 'buying' a gift like a knife or watch for a 5-kopiyok coin to neutralize the omen of severing ties or running out of time
  - Name Day (День Ангела) — mini-dialogue celebrating a 'Name Day' as a significant event; use the essential greeting «З Днем ангела!» for the «іменинник»
  - Summary: Review of recipient-verb pairs — reinforcing the social function of the dative in Ukrainian daily interaction
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ (Introduction: The Recipient Concept) | 325+ |
| Презентація: Чоловічий та середній рід (Presentation: Masculine and Neuter) | 475+ |
| Презентація: Жіночий рід та множина (Presentation: Feminine and Plural) | 475+ |
| Практика: Дієслова та етикет (Practice: Verbs and Etiquette) | 400+ |
| Діалоги та культура (Dialogues and Culture) | 325+ |
| **Total** | **2000+ (aim for ~2400)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("dative noun endings masculine dative (-ові/-у)", grade=3-5)` — find how textbooks teach this
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
**Required types:** fill-in, quiz, match-up, fill-in, quiz

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
