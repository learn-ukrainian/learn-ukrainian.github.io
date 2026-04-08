<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 10: Для кого? Без чого? Біля чого? (A2, A2.2 [Genitive Case Complete])

## Plan vocabulary to verify

- призначення (purpose, destination)
- відпочинок (rest, relaxation)
- допомога (help, assistance)
- сумнів (doubt)
- будинок (building, house)
- зупинка (stop (bus/tram))
- бібліотека (library)
- лікарня (hospital)
- площа (square (city))
- станція (station)
- навчання (studying, education)
- церква (church)
- вокзал (train station)
- річка (river)

## Sections to research

- **Для кого це? Для + родовий (Who Is It For? Для + Genitive)**: Purpose: для здоров'я (for health), для роботи (for work), для навчання (for studying).; Recipient: для мами (for mom), для друга (for a friend), для дітей (for children).; Practice with all genders: для брата (hard masc.), для вчителя (soft masc. -тель group), для сестри (hard fem.), для Марії (-ія fem.), для щастя (-тя neuter).
- **Без чого? Без + родовий (Without What? Без + Genitive)**: Core meaning: кава без цукру (coffee without sugar), чай без молока (tea without milk), день без дощу (a day without rain).; Abstract uses: без сумніву (without doubt), без проблем (no problem), без допомоги (without help).; Hard vs. soft stems after без: без хліба (hard masc.), без олівця (soft masc.), без води (hard fem.), без солі (soft fem.), без вікна (hard neuter), без моря (soft neuter).
- **Де це? Біля, навпроти, коло + родовий (Where Is It? Біля, навпроти, коло + Genitive)**: Біля (near, next to): біля школи, біля будинку, біля річки. The most common 'near' preposition.; Навпроти (opposite, across from): навпроти парку, навпроти вокзалу, навпроти церкви. Used for objects facing each other.; Коло (near, by — slightly literary): коло хати, коло дороги. Less common in spoken Ukrainian than біля, but appears in literature and songs.

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
