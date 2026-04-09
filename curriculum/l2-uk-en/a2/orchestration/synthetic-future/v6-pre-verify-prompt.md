<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 41: Я напишу! (A2, A2.6 [Aspect, Tenses, and Motion])

## Plan vocabulary to verify

- майбутній час (future tense)
- простий (simple, synthetic)
- складений (compound, analytical)
- сказати / скажу (to say/tell — pf. future)
- написати / напишу (to write — pf. future)
- зробити / зроблю (to do — pf. future)
- буду (I will — auxiliary)
- прочитати (to read through — pf.)
- подзвонити (to call — pf.)
- купити (to buy — pf.)
- приїхати (to arrive — pf.)
- обіцяти (to promise)
- планувати (to plan)
- прибирати / прибрати (to clean up — impf./pf.)

## Sections to research

- **Два майбутніх часи (Two Futures in Ukrainian)**: Ukrainian has two ways to talk about the future, and the choice depends on aspect — not on formality or style.; Perfective future (простий майбутній час): use the conjugated present-tense forms of perfective verbs. Since perfective verbs cannot describe an action happening right now, their present forms point to the future: скажу = I will say, напишу = I will write, зроблю = I will do.; Imperfective future (складений майбутній час): буду + imperfective infinitive. Буду говорити = I will be speaking, буду читати = I will be reading.
- **Простий майбутній час (Perfective/Synthetic Future)**: Formation: conjugate the perfective verb exactly like a present tense verb. The forms look like present tense but mean future: я скажу, ти скажеш, він/вона скаже, ми скажемо, ви скажете, вони скажуть.; More examples: написати → напишу, напишеш, напише...; зробити → зроблю, зробиш, зробить...; прочитати → прочитаю, прочитаєш, прочитає...; When to use: a single, completed action in the future. Я напишу листа (I will write the letter — and finish it). Він прочитає книгу (He will read the book — all of it).
- **Складений майбутній час (Imperfective/Analytical Future)**: Formation: conjugate буду (я буду, ти будеш, він/вона буде, ми будемо, ви будете, вони будуть) + imperfective infinitive.; Examples: Я буду читати (I will be reading). Ми будемо працювати (We will be working). Вони будуть вивчати українську (They will be studying Ukrainian).; When to use: an ongoing, repeated, or general action in the future. Завтра я буду працювати весь день (Tomorrow I will be working all day). Влітку вони будуть подорожувати (In summer they will be traveling).
- **Як обрати вид для майбутнього (Choosing Aspect for the Future)**: Decision guide: Will the action be completed with a result? → Perfective (synthetic). Will it be ongoing, repeated, or is duration important? → Imperfective (analytical).; Contrastive examples: Я подзвоню тобі ввечері (I will call you — single call) vs. Я буду дзвонити тобі щодня (I will call you every day — repeated). Він прочитає статтю (He will read the article — finish it) vs. Він буде читати статтю (He will be reading the article — process).; Practical dialogues: making plans, promises, predictions — all require choosing aspect. Що ти будеш робити завтра? — Я прибиратиму квартиру, а потім приготую вечерю.

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
