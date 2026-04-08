<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 35: Чим ти захоплюєшся? Дозвілля та хобі (A2, A2.5 [Case Synthesis and Plurals])

## Plan vocabulary to verify

- дозвілля (leisure, free time)
- хобі (hobby)
- захоплюватися (to be passionate about)
- займатися (to engage in, to do)
- спорт (sport)
- розвага (entertainment)
- вільний (free)
- плавання (swimming)
- музика (music)
- виставка (exhibition)
- вподобання (preferences, interests)
- прогулянка (walk, stroll)
- змагання (competition)
- малювання (drawing, painting)
- кіно (cinema, movies)

## Sections to research

- **Хобі та вподобання (Hobbies and Preferences)**: Key verbs: захоплюватися + instrumental (to be passionate about), займатися + instrumental (to engage in, do), любити + infinitive (to love doing), цікавитися + instrumental (to be interested in).; Hobby vocabulary: плавання, малювання, читання, танці, фотографія, кулінарія, садівництво, програмування, вишивання.; Sports: футбол, баскетбол, теніс, волейбол, біг, плавання, йога. Грати в/у + accusative (грати у футбол). Займатися + instrumental (займатися йогою).
- **Куди йдемо? Де ми? (Where Are We Going? Where Are We?)**: Case practice through leisure: going TO = accusative (йти в кіно, на виставку, у басейн, на стадіон). Being AT = locative (бути в кіно, на виставці, у басейні, на стадіоні).; Verbs of leisure movement: ходити (regularly), піти (one-time, pf), йти (going now). Ходити в театр (I go to the theater regularly) vs. Піду в театр (I'll go to the theater).; Practice pairs: Ми йдемо на прогулянку → Ми на прогулянці. Вона їде на змагання → Вона на змаганні.
- **Плани на вихідні (Weekend Plans)**: Making suggestions: Ходімо в кіно! Може, підемо на прогулянку? Хочеш піти на концерт? Давай пограємо в теніс!; Accepting: З задоволенням! Чудова ідея! Так, давай! Я — за!; Declining politely: На жаль, не можу. Я зайнятий/зайнята. Може, іншим разом? У мене вже є плани.
- **Що мені подобається найбільше (What I Like Most)**: Expressing preferences: Мені подобається (I like), мені найбільше подобається (I like most), я обожнюю (I adore), мені не подобається (I don't like).; Combining: Я захоплююся малюванням, але найбільше люблю ходити в гори. У вільний час я зазвичай читаю або граю на гітарі.; Cultural note: popular Ukrainian leisure — going to the Carpathians, visiting castles, attending folk festivals, berry picking (збирати ягоди), mushroom hunting (збирати гриби).

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
