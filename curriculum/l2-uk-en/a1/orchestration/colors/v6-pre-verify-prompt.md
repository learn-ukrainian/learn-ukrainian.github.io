<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 10: Colors (A1, A1.2 [My World])

## Plan vocabulary to verify

- червоний (red)
- жовтий (yellow)
- зелений (green)
- синій (dark blue — soft-stem!)
- блакитний (light blue, sky blue)
- білий (white)
- чорний (black)
- сірий (grey)
- колір (color, m)
- якого кольору? (what color?)
- коричневий (brown)
- рожевий (pink)
- помаранчевий (orange)
- фіолетовий (purple)
- {'темний (dark — as prefix': 'темно-)'}
- {'світлий (light — as prefix': 'світло-)'}
- прапор (flag, m)

## Sections to research

- **Діалоги (Dialogues)**: Dialogue 1 — Choosing a gift (Большакова Grade 2 p.38 colors poem as inspiration): — Яка гарна сумка! Якого вона кольору? — Червона. А є ще синя і зелена. — Мені подобається синя. — А мені — жовта! Colors emerge naturally through shopping scenario. Note: Мені подобається is a memorized chunk (like У мене є) — dative grammar is A2.; Dialogue 2 — Describing your room (extending M08-M09): — Якого кольору твоя кімната? — Біла. — А стіл? — Стіл коричневий. А крісло — сіре. Review: gender agreement + new color vocabulary.
- **Кольори (Colors)**: 12 basic colors organized by adjective type: Hard-stem (-ий/-а/-е — same pattern as M09): червоний/червона/червоне (red) жовтий/жовта/жовте (yellow) зелений/зелена/зелене (green) чорний/чорна/чорне (black) білий/біла/біле (white) сірий/сіра/сіре (grey); Soft-stem (-ій/-я/-є — NEW pattern): синій/синя/синє (dark blue) Вашуленко Grade 3 p.130: adjectives divide into тверда група (-ий) and м'яка група (-ій). Only синій is soft-stem among basic colors — learn it as a special case now. Compare: великий стіл → синій стіл, велика книга → синя книга, велике вікно → синє вікно.
- **Синій ≠ блакитний (Blue ≠ Blue)**: Ukrainian has TWO blues — English has one: синій = dark blue, deep blue (the sea, the night sky, ink) блакитний = light blue, sky blue (a clear daytime sky, baby blue) Прапор України — синьо-жовтий (Кравцова Grade 2 p.22: Синьо-жовтий прапор маєм: синє — небо, жовте — жито). Cultural note: 'голубий' is a Russian-influenced word for light blue — use блакитний.; More colors for describing things: коричневий (brown), рожевий (pink), помаранчевий (orange), фіолетовий (purple). These are all hard-stem (-ий/-а/-е). Compound colors: темно-зелений (dark green), світло-синій (light blue-ish). Cultural hook: вишиванка — traditional embroidered shirt, typically червоний і чорний (Полісся) or червоний і синій (Полтавщина).
- **Підсумок — Summary**: Color agreement follows the same rules as M09: Hard-stem: червоний стіл, червона книга, червоне вікно. Soft-stem: синій стіл, синя книга, синє вікно. Self-check: What color is the Ukrainian flag? (синьо-жовтий) Describe 3 things in your room using colors. What's the difference between синій and блакитний?

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

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (A1).

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
