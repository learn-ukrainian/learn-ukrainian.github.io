<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 28: Euphony (A1, A1.5 [Places])

## Plan vocabulary to verify

- у/в (in/at — alternating preposition)
- і/й (and — alternating conjunction)
- з/із/зі (with/from — alternating preposition)
- Київ (Kyiv)
- Львів (Lviv)
- офіс (office, m)
- парк (park, m)
- театр (theater, m)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Describing where things are: — Де ти живеш? — Я живу в Києві. А ти? — Я живу у Львові. — У Львові гарно! Note: в Києві (before К=consonant after vowel) vs у Львові (before Л after consonant). Euphony rules make sentences flow naturally.; Dialogue 2 — Making plans: — Ти й Олена йдете в кіно? — Ні, я і Максим йдемо в парк. — А Олена й Тарас? — Вони йдуть у театр. Note: й between vowels (ти й Олена), і between consonants (я і Максим).
- **У чи В? (У or В?)**: Авраменко Grade 5 p.117: Чергування у–в забезпечує милозвучність мови. Core rule: avoid consonant clusters. В after a vowel before a consonant: живу в Києві, працюю в офісі. У after a consonant before a consonant: Тарас у Львові, Максим у банку. This applies to both the preposition (в/у) and the prefix (вже/уже).; Exceptions to know: At the start of a sentence: У мене є... (always У). After a pause or comma: Так, у нас є... (У after pause). Don't overthink it — native speakers use euphony instinctively. The goal: sentences that SOUND smooth, not rigid rule application.
- **І чи Й? З, із, чи зі?**: Літвінова Grade 5 p.176: і/й чергування: І between consonants: брат і сестра, Тарас і Максим. Й between vowels: мама й тато, вона й він. At sentence start: І він прийшов (always І).; Літвінова Grade 5 p.177: з/із/зі чергування: З before vowels and most consonants: з Одеси, з другом. Із between consonants (avoiding cluster): Максим із Семеном. Зі before з, с, ш, щ or consonant clusters: зі мною, зі святом, зі школи. This is a smaller rule than у/в but important for natural speech.
- **Підсумок — Summary**: Three euphony pairs: у/в — avoid consonant+consonant: у Львові, в Києві. і/й — avoid vowel+vowel: брат і сестра, мама й тато. з/із/зі — before difficult clusters: з другом, із сестрою, зі мною. Self-check: Which is correct? Я живу (в/у) Києві. Мама (і/й) тато. Practice: read your sentences aloud — do they flow smoothly?

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
