<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 24: З другом (A2, A2.4 [Instrumental Case])

## Plan vocabulary to verify

- орудний відмінок (instrumental case)
- з (with)
- із (with — before consonant clusters)
- зі (with — before з-, с-, ш-)
- друг (friend (male))
- подруга (friend (female))
- лимон (lemon)
- молоко (milk)
- масло (butter)
- мед (honey)
- сметана (sour cream)
- супутник (companion)
- разом (together)
- компанія (company, group of friends)
- гриби (mushrooms)

## Sections to research

- **Орудний відмінок: Знайомство (The Instrumental Case: Introduction)**: Introducing the Instrumental case (Орудний відмінок), answering the questions 'Ким? Чим?' — the seventh Ukrainian case in our curriculum journey.; Its core meaning: the "tool" or "companion" of an action. Today we focus on companionship — doing something WITH someone or something.; Quick overview of all Instrumental functions (accompaniment, tool, profession, spatial) — to be covered across M21-M25.
- **Закінчення орудного відмінка однини (Instrumental Singular Endings)**: Masculine nouns: -ом for hard stems (другом, столом, братом), -ем for soft stems and sibilants (вчителем, ножем, товаришем), -єм for stems in [й] (чаєм, трамваєм).; Feminine nouns: -ою for hard stems (сестрою, мамою, книгою), -ею for soft stems and sibilants (землею, душею), -єю for stems in [й] (мрією, надією).; Neuter nouns: -ом for -о stems (вікном, молоком, маслом), -ем/-ям for -е/-я stems (морем, ім'ям).
- **З/із/зі + орудний відмінок (Z/iz/zi + Instrumental)**: The preposition з (with) + Instrumental expresses two meanings: (1) accompaniment — Я гуляю з другом, Вона живе з батьками; (2) attribute — чай з лимоном, хліб з маслом, борщ зі сметаною.; Phonetic variants: з before vowels and most consonants (з другом, з молоком), із before consonant clusters (із сестрою), зі before з-, с-, ш- initial words (зі мною, зі сметаною).; Common collocations: каша з маслом, кава з молоком, піца з грибами, салат з овочами — food descriptions that learners can use immediately.
- **Практика: З ким? З чим? (Practice: With Whom? With What?)**: Practice answering questions: З ким ти живеш? — Я живу з мамою. З ким ти ходиш у кіно? — З другом. Чай з чим? — З лимоном.; Dialogue: Two friends meeting at a cafe, ordering drinks and snacks, describing what they want (Мені, будь ласка, каву з молоком. А мені чай з медом).; Transformation drill from Nominative to Instrumental in context sentences.

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
