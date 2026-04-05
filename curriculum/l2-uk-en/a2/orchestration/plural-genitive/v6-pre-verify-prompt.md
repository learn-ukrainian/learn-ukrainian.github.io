<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 33: Скільки? (A2, A2.5 [Case Synthesis and Plurals])

## Plan vocabulary to verify

- родовий відмінок (genitive case)
- нульове закінчення (zero ending)
- кількість (quantity, amount)
- багато (a lot, many)
- мало (few, little)
- кілька (a few, several)
- декілька (a few, several)
- скільки (how many, how much)
- гроші (money)
- гривня (hryvnia)
- вставний голосний (fleeting vowel)
- виняток (exception)
- десяток (a dozen, ten-unit)

## Sections to research

- **Чому родовий множини такий складний? (Why Is the Genitive Plural So Hard?)**: Overview: Gen.Pl. has THREE possible endings — zero (нульове закінчення), -ів/-їв, -ей — plus fleeting vowels. No single rule covers all nouns.; Why it matters: Gen.Pl. appears after numbers 5+, after багато/мало/кілька/скільки, and in many prepositional phrases. It is the most common plural case.; Strategy: learn by відміна and gender, with the most frequent words first.
- **I відміна: нульове закінчення (First Declension: Zero Ending)**: Most I відміна nouns (feminine -а/-я) take zero ending: книга → книг, зірка → зірок, вишня → вишень.; Fleeting vowels appear when consonant clusters form: сестра → сестер, земля → земель, пісня → пісень, казка → казок.; Exceptions with -ів or -ей: суддя → суддів, сім'я → сімей, стаття → статей.
- **II відміна: -ів, нульове, -ей (Second Declension: Three Patterns)**: Masculine hard stems: -ів (столів, братів, учнів, днів).; Masculine soft stems: -ів or -ей (учителів, but гостей, коней).; Neuter -о: zero ending, often with fleeting vowels (вікон, слів, but міст — no fleeting vowel).
- **Скільки чого? Кількість у житті (How Much of What? Quantity in Daily Life)**: Pattern: скільки/багато/мало/кілька/декілька + Gen.Pl. — Скільки студентів? Багато книжок. Мало грошей. Кілька друзів.; Numbers 5+ take Gen.Pl.: п'ять яблук, десять студентів, двадцять гривень.; Contrast with 2-4 (Nom.Pl.): два студенти vs. п'ять студентів; три книжки vs. сім книжок.

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
