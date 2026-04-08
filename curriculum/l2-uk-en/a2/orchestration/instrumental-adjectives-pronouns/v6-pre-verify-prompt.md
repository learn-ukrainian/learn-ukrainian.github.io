<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 29: З моїм найкращим другом (A2, A2.4 [Instrumental Case])

## Plan vocabulary to verify

- мій (my)
- твій (your (informal))
- наш (our)
- ваш (your (formal/plural))
- цей (this)
- той (that)
- новий (new)
- старий (old)
- великий (big, large)
- гарний (nice, beautiful)
- найкращий (the best)
- сусід (neighbor (male))
- домашній (home (adj.), domestic)
- синій (blue)
- сусідка (neighbor (female))
- тим часом (meanwhile)
- цим вечором (this evening)

## Sections to research

- **Прикметники в орудному відмінку (Adjectives in the Instrumental Case)**: Hard group adjective endings in Instrumental singular: masculine/neuter -им (новим, гарним, великим, старим), feminine -ою (новою, гарною, великою, старою).; Soft group adjective endings in Instrumental singular: masculine/neuter -ім (синім, літнім, домашнім), feminine -ьою (синьою, літньою, домашньою).; Reference chart from Захарійчук Grade 4, с. 92: full declension table for hard and soft adjective groups.
- **Присвійні та вказівні займенники (Possessive and Demonstrative Pronouns)**: Possessive pronouns in Instrumental singular: мій → моїм/моєю, твій → твоїм/ твоєю, наш → нашим/нашою, ваш → вашим/вашою. його/її/їхній do not change (його is invariable, їхній declines like an adjective).; Demonstrative pronouns: цей → цим/цією, той → тим/тією. Цим автобусом (by this bus), за тією стіною (behind that wall).; Building full phrases: з моїм старим другом, за нашим новим будинком, під цією великою ялинкою.
- **Повні словосполучення в орудному відмінку (Full Instrumental Phrases)**: Three-word agreement chains: з моїм найкращим другом (prep + poss.pron. + adj. + noun), за нашим великим будинком, між тією старою школою і новою бібліотекою.; Comparing masculine and feminine chains: з моїм новим сусідом vs. з моєю новою сусідкою — every word changes.; Common real-life phrases: з моєю найкращою подругою, за вашим будинком, цим вечором (this evening — temporal), тим часом (meanwhile).
- **Практика: Опиши свій день (Practice: Describe Your Day)**: Production exercise: describe your day using full Instrumental phrases — З ким ти снідаєш? З моєю сім'єю. Чим ти їдеш на роботу? Нашим старим автобусом.; Dialogue: Two friends catching up — asking about family, new neighbors, daily routine. Practice with possessive + adjective + noun chains.; Error correction drill: spot and fix agreement mistakes in Instrumental phrases (e.g., *з моїм новою другом → з моїм новим другом).

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
