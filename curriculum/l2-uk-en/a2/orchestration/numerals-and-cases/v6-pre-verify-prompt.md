<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 55: Числа у відмінках (A2, A2.8 [Refinement and Graduation])

## Plan vocabulary to verify

- числівник (numeral)
- порядковий (ordinal)
- кількісний (cardinal)
- перший (first)
- третій (third)
- один (one)
- скільки (how many)
- кілограм (kilogram)
- коштувати (to cost)
- вік (age)
- обидва (both, m.)
- обидві (both, f.)
- десяток (a ten, a dozen)
- пів (half)

## Sections to research

- **Порядкові числівники: -ий та -ій (Ordinal Numerals: -ий and -ій)**: Two patterns: -ий ordinals decline like hard adjectives (п'ятий → п'ятого, п'ятому, п'ятим). -ій ordinals decline like soft adjectives (третій → третього, третьому, третім).; Which ordinals use -ій: третій (3rd) — the main one. Also перший (1st) has mixed pattern. All others use -ий.; Practice with dates: двадцять першого березня, другого квітня, п'ятнадцятого серпня. Ordinals in the Genitive for dates.
- **Один/одна/одне у відмінках (One in All Cases)**: Full declension of один (m.), одна (f.), одне (n.) in all seven cases. Key forms: одного, одному, одним (m./n.); однієї/одної, одній, однією (f.).; Usage beyond counting: один means "a certain" (один чоловік сказав...), "alone" (я один/одна), "the same" (ми з одного міста).; Practice sentences using один in different cases and meanings.
- **Скільки чого? Числівник + іменник (How Many? Numeral + Noun Agreement)**: The agreement cycle: 1 + Nom.Sg. (один студент, одна книга), 2-4 + Nom.Pl. (два студенти, три книги), 5-20 + Gen.Pl. (п'ять студентів, десять книг).; After 20, the cycle restarts based on the last digit: 21 студент, 22 студенти, 25 студентів.; Gender matters for два/дві and обидва/обидві: два брати but дві сестри.
- **Числа навколо нас (Numbers Around Us)**: Dialogue: at the market — asking prices, discussing quantities, bargaining (Скільки коштує? Дайте, будь ласка, три кілограми).; Reading practice: a short text about Ukrainian holidays with dates, ages of historical figures, distances between cities.; Address format: вулиця Хрещатик, будинок 22, квартира 5.

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
