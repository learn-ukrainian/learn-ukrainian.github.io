<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 10: Кольори (A1, A1.2 [Мій світ])

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
- карий (brown-eyed; mainly for eyes)
- русявий (fair-haired, light-brown/blondish)
- сивий (grey-haired)
- прапор (flag, m)

## Sections to research

- **Діалоги**: Діалог 1 — Вибір букета на квітковому ринку (за мотивами вірша про кольори з підручника Большакової для 2 класу, с. 38): — Які гарні троянди! Якого вони кольору? — Червоні. А ось ці лілії — білі. — Мені подобаються жовті соняшники. — Добре, загорнути букет? Кольори входять через реалістичне запитання `Якого кольору?` і коротку відповідь. Примітка: `Мені подобаються` тут працює як готовий вираз; детальне пояснення давального відмінка відкладаємо.; Діалог 2 — Опис кімнати й людини для впізнавання (продовження модуля №8–9): — Якого кольору твоя кімната? — Біла. — А стіл? — Стіл коричневий. А крісло — сіре. — Як я впізнаю Олю? — У неї карі очі й русяве волосся. Повторення: узгодження за родами + нова лексика кольорів + кілька природних словосполучень для зовнішності.
- **Кольори**: 12 базових кольорів, поділених за типами прикметників: Тверда група (-ий/-а/-е — такий самий патерн, як у модулі №9): червоний/червона/червоне, жовтий/жовта/жовте, зелений/зелена/зелене, чорний/чорна/чорне, білий/біла/біле, сірий/сіра/сіре.; М'яка група (-ій/-я/-є — НОВИЙ патерн): синій/синя/синє. Вашуленко, 3 клас, с. 130: прикметники поділяються на тверду групу (-ий) та м'яку групу (-ій). Лише слово "синій" належить до м'якої групи серед базових кольорів — зараз варто вивчити його як окремий виняток. Порівняйте: великий стіл → синій стіл, велика книга → синя книга, велике вікно → синє вікно.; Мовленнєва рамка: `Якого кольору...?` + коротка відповідь одним прикметником (`Червоний`, `Червона`, `Червоне`, `Червоні`). Лише потім переходити до повного речення (`Сукня червона`).
- **Синій ≠ блакитний**: В українській мові для A1 активно вчимо пару синій = темно-/глибоко-синій (море, чорнило) і блакитний = світло-/небесно-синій (ясне небо). Прапор України — синьо-жовтий (Кравцова, 2 клас, с. 22: Синє — небо, жовте — жито). Writer note: не називайте `голубий` русизмом; якщо слово трапиться поза модулем, досить пасивного впізнавання як словникового синоніма до `блакитний`.; Інші кольори для опису речей: коричневий, рожевий, помаранчевий, фіолетовий. Усі вони належать до твердої групи (-ий/-а/-е). Складні кольори: темно-зелений, світло-синій.; Усталені словосполучення для зовнішності: `карі очі`, `русяве волосся`, `сиве волосся`. Їх варто подавати як готові чанки, а не як просте механічне перенесення базової палітри на людину.
- **Підсумок**: Узгодження кольорів за правилами модуль №9: Тверда група: червоний стіл, червона книга, червоне вікно. М'яка група: синій стіл, синя книга, синє вікно. Самоперевірка: поставте 3 запитання з формулою `Якого кольору?`, опишіть 3 речі у вашій кімнаті, а також дайте природний опис `карі очі` / `русяве волосся` / `сиве волосся`. УВАГА до автора: форми `зеленіший`, `синіший` свідомо не вводимо; це межа A2, не ціль цього модуля.

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
