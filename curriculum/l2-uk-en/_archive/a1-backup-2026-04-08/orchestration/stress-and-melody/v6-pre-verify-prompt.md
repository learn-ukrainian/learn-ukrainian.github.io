<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 4: Stress and Melody (A1, A1.1 [Sounds, Letters, and First Contact])

## Plan vocabulary to verify

- наголос (stress/accent) — metalanguage word
- замок (castle) — stress pair (first syllable)
- замок (lock) — stress pair (second syllable)
- кава (coffee) — first-syllable stress
- вода (water) — second-syllable stress
- столиця (capital) — Київ — столиця України
- мука (flour) — stress pair with мука (torment)
- ранок (morning) — first-syllable stress
- метро (metro) — last-syllable stress
- фотографія (photograph) — long word practice

## Sections to research

- **Наголос (Stress)**: Заболотний Grade 5 p.73: Ukrainian has 38 sounds, and stress (наголос) determines which syllable is louder and longer. Stress is FREE — it can fall on any syllable, and it MOVES between forms of the same word. This is unlike French (always last) or Czech (always first).; Stress changes meaning — real pairs learners will encounter: замок (castle) vs замок (lock), мука (torment) vs мука (flour), атлас (atlas) vs атлас (satin). Wrong stress = wrong word. This is why stress marks matter.; In writing, stress marks (') appear in textbooks and dictionaries but NOT in everyday Ukrainian text. As a learner, always check goroh.pp.ua for stress when unsure.
- **Інтонація (Intonation)**: Ukrainian uses intonation (melody) to distinguish sentence types. Same words, different melody, different meaning. Statement: Це кава. ↘ (falling — telling) Question: Це кава? ↗ (rising on last stressed syllable — asking) Exclamation: Як гарно! ↘↘ (strong fall — expressing emotion); Question words (хто, що, де, коли) make questions WITHOUT rising: Що це? ↘ (falling — the question word does the work). Де метро? ↘ (falling). But yes/no questions always rise: Це метро? ↗; Ukrainian classifies sentences by purpose: розповідні (declarative), питальні (interrogative), спонукальні (imperative). Any of these can also be окличні (exclamatory) — a separate dimension. For A1: focus on the three punctuation patterns: . for statements, ? for questions, ! for exclamations/commands.
- **Читаємо вголос (Reading Aloud)**: Multisyllable reading with correct stress: у-кра-їн-ська (Ukrainian — stress on ї), фо-то-гра-фі-я (photograph — stress on third а: фотографія), ві-дпо-чи-нок (rest — stress on и). Method: break → find stressed syllable → read at natural speed.; Word stress reading practice — read aloud with correct наголос: Ки-їв, мо-ло-ко, ран-ок, ка-ва, во-да, зи-ма, у-кра-їн-ська. Find the stressed syllable, then read the whole word at natural speed.; Dialogue practice using greetings from M01: — Привіт! ↘ (statement/greeting) — Привіт! Як справи? ↗ (yes/no question) — Добре! А у тебе? ↗ — Добре! ↘ Apply intonation patterns to the greetings already learned.
- **Підсумок — Summary**: Self-check: What is наголос? Can it change word meaning? Give an example. What intonation do you use for a yes/no question? For a statement? Read this aloud: Це аптека? Так, це аптека. Як гарно!

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
