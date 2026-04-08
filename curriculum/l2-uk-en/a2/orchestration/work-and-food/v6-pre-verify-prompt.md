<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 30: Професії та кулінарія (A2, A2.4 [Instrumental Case])

## Plan vocabulary to verify

- готувати (to cook, to prepare)
- різати (to cut)
- мішати (to stir, to mix)
- посипати (to sprinkle)
- подавати (to serve)
- вареники (varenyky, dumplings)
- картопля (potato)
- помідор (tomato)
- огірок (cucumber)
- сіль (salt)
- олія (oil)
- виделка (fork)
- рецепт (recipe)
- інгредієнт (ingredient)
- нарада (meeting)
- колега (colleague)
- начальник (boss)

## Sections to research

- **Розмова про професії (Talking About Professions)**: Task scenario: You meet someone new at a gathering. Ask about their profession, interests, and what they are passionate about.; Key question chains: Хто ти за фахом? → Я працюю програмістом. Чим ти захоплюєшся? → Захоплююся фотографією. Ким ти хотів/хотіла стати в дитинстві? → Я мріяв/мріяла стати лікарем.; Extended dialogue: Two people at a party — one is a cook, the other is a teacher. They discuss their jobs, what they like about them, and what they do in their free time.
- **На кухні: Готуємо разом (In the Kitchen: Cooking Together)**: Task scenario: Describe how to make a simple Ukrainian dish (e.g., вареники з картоплею, салат з овочами, бутерброд з маслом і сиром).; Tool Instrumental: різати ножем, мішати ложкою, смажити на сковорідці (Locative — contrast!), посипати сіллю, поливати олією.; Ingredient Instrumental with з: борщ зі сметаною, вареники з картоплею, салат з помідорами і огірками, чай з медом.
- **Мій робочий день (My Workday)**: Task: Describe a full workday using all Instrumental functions — Вранці я їду на роботу автобусом. Працюю за комп'ютером (Instrumental — tool). Обідаю з колегами (accompaniment). Перед обідом маю нараду.; Combining prepositions: перед роботою (before work), між нарадами (between meetings), за розкладом (according to schedule), з моїм начальником (with my boss).; Dialogue: A vlog-style monologue where someone describes their typical day — uses all Instrumental patterns naturally.
- **Практика: Розкажи про себе (Practice: Tell About Yourself)**: Integrated production task: Write 8-10 sentences about yourself — your profession, interests, daily routine, favorite food — using as many Instrumental constructions as possible.; Self-check: identify which Instrumental function each sentence uses (accompaniment, tool, profession, spatial, temporal).; Peer dialogue simulation: Practice a full getting-to-know-you conversation that touches on work, hobbies, food preferences, and daily schedule.

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
