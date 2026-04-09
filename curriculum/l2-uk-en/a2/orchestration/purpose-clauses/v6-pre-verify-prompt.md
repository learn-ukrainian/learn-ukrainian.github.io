<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 48: Щоб зрозуміти... (A2, A2.7 [Complex Sentences and Conditionals])

## Plan vocabulary to verify

- щоб (in order to, so that)
- мета (goal, purpose)
- сказати (to say, to tell)
- відповісти (to answer, to reply)
- пояснити (to explain)
- запитати (to ask)
- повідомлення (message)
- зрозуміти (to understand)
- непряма мова (indirect/reported speech)
- додати (to add)
- навіщо (what for, why)
- передати (to pass on, to relay)
- попросити (to ask, to request)
- пряма мова (direct speech)

## Sections to research

- **Щоб + інфінітив: для чого? (In Order To: What For?)**: Introducing purpose clauses: the question Для чого? Навіщо? (What for?) and the answer щоб + infinitive. Я вчу українську, щоб розуміти друзів.; Same-subject rule: when the subject of both clauses is the same, use щоб + infinitive. Він прийшов, щоб допомогти. Ми поїхали в Київ, щоб побачити місто.; Different-subject construction: when subjects differ, use щоб + past tense form (looks like past tense but functions as subjunctive). Я зателефонував, щоб вона знала. Вчитель пояснив, щоб учні зрозуміли.
- **Базова непряма мова: він сказав, що... (Basic Reported Speech: He Said That...)**: A2 scope: basic reported speech with що and чи only. Sequence of tenses, якби-constructions, and complex transformations are B1. Here we learn the high-frequency relay pattern: він сказав, що...; Introducing reported speech with що: transforming direct speech into indirect. "Я прийду завтра" -> Він сказав, що прийде завтра.; Reporting verbs: сказати, відповісти, пояснити, запитати, додати. Each takes що + reported clause. Вона пояснила, що не може прийти.
- **Мета і повідомлення в житті (Purpose and Messages in Daily Life)**: Combining purpose and reported speech in real situations: Мама зателефонувала, щоб я купив хліб. Колега сказав, що зустріч перенесли.; Writing short messages and notes using щоб and що: SMS, voice messages, notes on the fridge. "Зателефонуй мамі, вона сказала, що чекає."; Common conversational patterns: Мені сказали, що... / Я чув, що... / Вони попросили, щоб... — high-frequency frames for everyday communication.

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 3: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 4: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
