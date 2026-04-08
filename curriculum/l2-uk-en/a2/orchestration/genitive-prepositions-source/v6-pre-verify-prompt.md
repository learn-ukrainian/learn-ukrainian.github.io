<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 9: Звідки ти? З чого це зроблено? (A2, A2.2 [Genitive Case Complete])

## Plan vocabulary to verify

- прийменник (preposition)
- джерело (source)
- походження (origin)
- матеріал (material)
- далеко (far)
- недалеко (not far, nearby)
- подарунок (gift)
- сніданок (breakfast)
- вечеря (dinner, supper)
- канікули (vacation, holidays)
- дитинство (childhood)
- шовк (silk)
- парасолька (umbrella)
- сусід (neighbor)

## Sections to research

- **Звідки? З/із/зі + родовий (Where From? З/із/зі + Genitive)**: Origin and source: з Києва, з України, зі Львова, зі Швеції. The core meaning is 'from' a place, person, or source.; Phonetic variants: з before vowels and single consonants (з Одеси, з університету); із before single sibilants [з], [с], [ц], [ж], [ч], [ш] (із золота, із села) and between two consonants (лист із Бразилії); зі before clusters starting with з-, с-, ш- (зі Львова, зі школи, зі стола). General principle: euphony (милозвучність) — choose the variant that's easier to pronounce.; Material and composition: склянка з молока (a glass of milk), сік з яблук (apple juice), сукня з шовку (a dress made of silk).
- **Від кого? Від + родовий (From Whom? Від + Genitive)**: From a person: лист від мами (a letter from mom), подарунок від друга (a gift from a friend), новини від сусіда (news from a neighbor).; Contrast з vs. від: з Києва (from Kyiv — place) vs. від Олени (from Olena — person). З = source/origin, від = from a specific person or entity.; Distance from: далеко від центру (far from the center), недалеко від вокзалу (not far from the station).
- **Що було потім? Після + родовий (What Happened Next? Після + Genitive)**: After an event or period: після уроку (after the lesson), після обіду (after lunch), після роботи (after work), після канікул (after vacation).; Genitive forms after після with both hard and soft nouns: після екзамену (hard masc.), після дня (soft masc.), після лекції (-ія fem.), після свята (hard neuter -о).; Common daily routine sequences: після сніданку йду на роботу, після роботи готую вечерю, після вечері дивлюся фільм.

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
