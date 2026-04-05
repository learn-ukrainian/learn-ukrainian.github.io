<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 21: Допомагати, дякувати, дзвонити (A2, A2.3 [Dative Case])

## Plan vocabulary to verify

- допомагати (to help)
- дякувати (to thank)
- дзвонити (to call, to phone)
- радити (to advise)
- заважати (to bother, to disturb)
- подобатися (to be pleasing to, to like (reversed syntax))
- відповідати (to answer (someone))
- рік (year)
- роки (years (2-4))
- років (years (5+))
- довіряти (to trust)
- вибачати (to forgive)
- посміхатися (to smile (at someone))
- співчувати (to sympathize (with someone))
- заздрити (to envy)

## Sections to research

- **Дієслова з давальним відмінком (Verbs That Take the Dative)**: Core group of dative-governing verbs: допомагати (to help), дякувати (to thank), дзвонити (to call/phone), радити (to advise), заважати (to bother/disturb), відповідати (to answer someone).; Key insight: in English many of these take direct objects (help someone, call someone), but in Ukrainian the person is in the Dative — допомагати кому?, дякувати кому?; Sentence patterns: Я допомагаю мамі. Він дякує вчителеві. Вона дзвонить подрузі. Ми радимо тобі. Вони заважають нам.
- **Мені подобається: Давальний відмінок досвідника (The Experiencer Dative with подобатися)**: подобатися has reversed syntax: the experiencer (who likes) is in the Dative, the thing liked is in the Nominative and controls the verb — Мені подобається ця книжка. Тобі подобаються ці фільми.; Conjugation: подобається (singular subject) vs. подобаються (plural subject). The verb agrees with the Nominative thing, NOT the Dative person.; Compare with English "I like this book" (I = subject) vs. Ukrainian "Мені подобається ця книжка" (книжка = grammatical subject).
- **Скільки тобі років? Вік у давальному відмінку (Age in the Dative)**: Age construction: Dative + number + рік/роки/років. Мені двадцять п'ять років. Дідусеві вісімдесят. Дитині три роки.; Question pattern: Скільки тобі років? Скільки їй років?; Number agreement: один рік, два/три/чотири роки, п'ять і більше років.
- **Давальний чи знахідний? Порівняння (Dative vs. Accusative with Verbs)**: Verbs with Accusative (direct object): бачити, знати, любити, чекати — кого? що?; Verbs with Dative (indirect/experiencer): допомагати, дякувати, дзвонити, радити — кому?; Some verbs take both: давати КОМУ (Dat.) ЩО (Acc.), розповідати КОМУ (Dat.) ПРО ЩО (Acc.).

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Search textbooks for each section topic

For each section title above, call `search_text` with the Ukrainian keywords.

Report the most relevant textbook excerpt for each section (author, grade, key quote).

### Task 3: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 4: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 5: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A2).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Textbook Excerpts
### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

### Section: [title]
> [relevant textbook quote]
> Source: [author, grade]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>
