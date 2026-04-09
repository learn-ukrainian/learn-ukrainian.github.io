<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Pre-Write Verification — Tool-Forced Fact Checking

You MUST verify facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

## Module

**Module:** 29: Where Is It? (A1, A1.5 [Places])

## Plan vocabulary to verify

- школа → в школі (school)
- робота → на роботі (work)
- банк → у банку (bank)
- магазин → у/в магазині (shop)
- вулиця → на вулиці (street)
- місто → у/в місті (city)
- парк → у/в парку (park)
- лікарня → у/в лікарні (hospital)
- кафе → у/в кафе (café — indeclinable)
- площа → на площі (square)
- вокзал → на вокзалі (train station)
- пошта → на пошті (post office)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Where is everyone? (ULP Ep17 pattern): — Де Олена? — Вона в школі. — А Тарас? — Він на роботі. — А діти? — Вони в парку. — А кішка? — Вона на дивані! Locative case emerges naturally from answering 'Де?'; Dialogue 2 — Describing locations: — Де ти живеш? — Я живу в Києві, на вулиці Хрещатик. — А де ти працюєш? — В офісі, на другому поверсі. City + street + building locations.
- **Місцевий відмінок (The Locative Case)**: Grade 4 case system: helper word method (Захарійчук Gr4 p.74): М. = місцевий відмінок: на/у кому? на/у чому? The locative ALWAYS needs a preposition — в/у or на. В/у = inside: в школі, у банку, в магазині, у лікарні. На = on/at: на роботі, на вулиці, на площі, на уроці.; Basic locative endings (most common patterns): Masculine: -і or -у — в парку, у банку, в офісі, на уроці. Feminine: -і — в школі, на роботі, у лікарні, на вулиці. Neuter: -і — в місті, на морі. Note: endings depend on the noun's declension — learn the common places as fixed phrases for now.
- **В чи на? (В or На?)**: General guide: В/у = enclosed spaces: в школі, в магазині, у банку, в лікарні, в кафе. На = open spaces, surfaces, events: на вулиці, на площі, на роботі, на концерті. Some are conventional: на пошті (not в пошті), на вокзалі (not в вокзалі). Learn each place with its preposition — like English 'at school' vs 'in the office'.; Country/city rule: В/у + country/city: в Україні, у Києві, у Львові, в Одесі. На + some special cases: на Хрещатику (on Khreshchatyk street). Remember: NEVER 'на Україні' — it's ЗАВЖДИ 'в Україні'. This is not just grammar — it's a matter of respect and sovereignty.
- **Підсумок — Summary**: Locative case = where something IS (static location). Де? → в/у + locative (inside) or на + locative (on/at). Helper word: М. (на, у) — на/у кому? на/у чому? Common places: в школі, на роботі, у банку, в парку, на вулиці. Self-check: Where are you right now? Where do you work? Where do you live?

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
