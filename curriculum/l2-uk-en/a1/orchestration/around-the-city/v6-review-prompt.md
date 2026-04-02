<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 33: Around the City (A1, A1.5 [Places])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-033
level: A1
sequence: 33
slug: around-the-city
version: '1.2'
title: Around the City
subtitle: Де/куди + directions — navigating in Ukrainian
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Combine Де? (locative) and Куди? (accusative) in real navigation
- Give and follow simple directions
- Describe your neighborhood and daily routes
- Synthesize M28-M32 skills in connected urban communication
dialogue_situations:
- setting: Walking tour of Lviv old town — going from Площа Ринок (f, main square)
    to Оперний театр (m, Opera house) to Високий замок (m, High Castle). Де ми? На
    площі. Куди далі? В театр. Звідки прийшли? З замку.
  speakers:
  - Гід (guide)
  - Туристи
  motivation: Де/Куди/Звідки with площа(f), театр(m), замок(m), парк(m)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Asking for directions: — Вибачте, як дістатися до бібліотеки? —
    Ідіть прямо, потім направо. Бібліотека на розі. — А музей? — Музей далеко. Їдьте
    на метро до центру. Combines directions + transport + city places.'
  - 'Dialogue 2 — Describing your route: — Як ти дістаєшся на роботу? — Спочатку йду
    на зупинку. Потім їду автобусом до центру. — А потім? — Потім іду пішки п''ять
    хвилин. Робота в офісі на площі. Daily route using sequence words + transport
    + places.'
- section: Де і куди разом (Where and Where To Together)
  words: 300
  points:
  - 'Real navigation uses both cases together: Я зараз у парку (де? — locative). Я
    йду в магазин (куди? — accusative). Магазин на вулиці Шевченка (де? — locative).
    Потім їду на роботу (куди? — accusative). The constant switch between де? and
    куди? is natural Ukrainian.'
  - 'Preposition patterns (synthesis): | Situation | Question | Form | | Static |
    Де ти? | в/на + locative | | Direction | Куди йдеш? | в/на + accusative | | By
    transport | Як? Чим? | автобусом / на метро | | Distance | Далеко? | далеко /
    близько / пішки |'
- section: Мій район (My Neighborhood)
  words: 300
  points:
  - 'Describing where you live: Я живу на вулиці Франка. Біля мого дому є парк і магазин.
    Школа далеко — треба їхати автобусом. Аптека близько, можна піти пішки. У моєму
    районі є кафе, ресторан і бібліотека.'
  - 'Useful phrases for city life: пішки (on foot), хвилина (minute) — П''ять хвилин
    пішки. далеко/близько від (far/near from — chunk). У центрі міста / на околиці
    (in the center / on the outskirts).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Urban communication toolkit: Asking: Де...? Як дістатися до...? Directions: прямо,
    направо, наліво. Location: в/на + locative, в/на + accusative. Transport: автобусом,
    на метро, пішки. Self-check: Describe your route from home to work/school.'
vocabulary_hints:
  required:
  - пішки (on foot)
  - хвилина (minute, f)
  - район (neighborhood, m)
  - центр (center, m)
  - вибачте (excuse me)
  recommended:
  - дістатися (to get to)
  - ідіть (go! — imperative, preview)
  - їдьте (go by transport! — imperative, preview)
  - поруч (nearby)
activity_hints:
- type: fill-in
  focus: Give directions using прямо, направо, наліво
  items: 6
  blanks:
  - Ідіть {прямо}, потім {направо}. Бібліотека на розі.
  - Вибачте, як дістатися до музею? — Ідіть {наліво}.
  - Аптека близько. Ідіть {прямо} п'ять хвилин.
  - Потім ідіть {направо}, школа там.
  - Йдіть {прямо}, а потім {наліво}.
  - Ресторан поруч. Ідіть {прямо} і {направо}.
- type: quiz
  focus: Де (locative) or Куди (accusative) in context
  items: 6
  questions:
  - Я зараз... (в парку / в парк)
  - Я йду... (в магазин / в магазині)
  - Магазин на... (вулиці / вулицю)
  - Потім їду на... (роботу / роботі)
  - Ми зараз у... (центрі / центр)
  - Вона йде в... (офіс / офісі)
- type: fill-in
  focus: Describe route with transport (автобусом, пішки, на метро)
  items: 6
  blanks:
  - Я їду в центр {на метро}.
  - Потім іду {пішки} п'ять хвилин.
  - Вона їде на роботу {автобусом}.
  - Школа далеко, треба їхати {на метро}.
  - Парк близько, ми йдемо {пішки}.
  - Ми їдемо в ресторан {автобусом}.
- type: match-up
  focus: Match question to logical response for navigation
  items: 6
  pairs:
  - Вибачте, як дістатися до бібліотеки?: Ідіть прямо, потім направо.
  - Де музей?: Він у центрі.
  - Як ти дістаєшся на роботу?: Їду автобусом.
  - Школа далеко?: Ні, близько. П'ять хвилин пішки.
  - Куди ви йдете?: У магазин.
  - Де ти живеш?: На вулиці Франка.
connects_to:
- a1-034 (Where From?)
prerequisites:
- a1-032 (Transport)
grammar:
- 'Synthesis: Де? (locative) + Куди? (accusative) in real navigation'
- Direction + transport + location combined
- 'Imperative preview: ідіть, їдьте (formal commands)'
register: розмовний
references:
- title: Synthesis of M28-M32 skills
  notes: Applied communication — no new grammar, just integration.

</plan_content>

## Generated Content

<generated_module_content>
## Діало́ги (Dialogues)

Navigating a Ukrainian city means juggling two questions at once: **де?** (where?) for your current location and **куди́?** (where to?) for your destination. You also need to ask for directions and describe how you travel. Two real situations show this in action — a stranger asking for help on a Lviv street, and a friend describing their morning commute.

### Діало́г 1 — Asking for Directions

> — **Тури́ст:** Ви́бачте, як діста́тися до бібліоте́ки? *(Excuse me, how do I get to the library?)*
> — **Перехо́жий:** Іді́ть пря́мо, по́тім напра́во. Бібліоте́ка на ро́зі. *(Go straight, then right. The library is at the corner.)*
> — **Турист:** А музе́й? *(And the museum?)*
> — **Перехожий:** Музей дале́ко. Ї́дьте на метро́ до це́нтру. *(The museum is far. Take the metro to the center.)*
> — **Турист:** Дякую! *(Thank you!)*

The tourist opens with **вибачте** (excuse me) — the standard polite formula for addressing a stranger. The full question **як дістатися до...?** (how to get to...?) is a survival phrase — memorize it as one chunk. You will study the verb **дістатися** (to get to) properly at B1; for now, just use the whole phrase.

Notice the two commands: **ідіть** (go — on foot) and **їдьте** (go — by vehicle). Both are formal imperatives, a preview of grammar you will learn later. The difference is simple: **ідіть** means walking, **їдьте** means riding. The phrase **на розі** (at the corner) is a locative chunk — learn it as a fixed unit.

### Діалог 2 — Describing Your Route

> — **Оле́на:** Як ти дістає́шся на робо́ту? *(How do you get to work?)*
> — **Тара́с:** Споча́тку йду на зупи́нку. Потім ї́ду авто́бусом до центру. *(First I walk to the stop. Then I ride the bus to the center.)*
> — **Олена:** А потім? *(And then?)*
> — **Тарас:** Потім іду́ пі́шки п'ять хвили́н. Робо́та в о́фісі на пло́щі. *(Then I walk five minutes. Work is in an office on the square.)*

Tарас uses sequence words to structure his route: **спочатку** (first) → **потім** (then) → **а потім** (and then). This is how Ukrainians naturally describe any multi-step journey. Notice the transport contrast: **їду автобусом** (I ride by bus — instrumental case, taught as a chunk) versus **іду пішки** (I walk — literally "go on foot"). The destination uses accusative: **на зупинку** (to the stop), **до центру** (to the center). His current location uses locative: **в офісі** (in the office), **на площі** (on the square).

<!-- INJECT_ACTIVITY: fill-in-directions -->

## Де і куди ра́зом (Where and Where To Together)

Real Ukrainian navigation constantly switches between two questions. When you say where you are, you use **де?** with locative case. When you say where you are heading, you use **куди?** with accusative case. A single journey might alternate between these several times:

- **Я за́раз у парку.** (I'm in the park now.) — де? → locative: у парку
- **Я йду в магази́н.** (I'm going to the store.) — куди? → accusative: в магазин
- **Магазин на ву́лиці Шевче́нка.** (The store is on Shevchenko Street.) — де? → locative: на вулиці
- **Потім їду на роботу.** (Then I ride to work.) — куди? → accusative: на роботу

The pattern is consistent: **question → preposition → case**. Static location = locative. Motion toward = accusative.

Here is the full navigation toolkit in one table:

| Ситуа́ція | Пита́ння | Фо́рма | Приклад |
|---|---|---|---|
| Static location | Де? | в/на + locative | Я в офісі. На площі. |
| Motion toward | Куди? | в/на + accusative | Іду в теа́тр. На роботу. |
| Transport mode | Як? Чим? | автобусом / на метро / пішки | Їду автобусом. |
| Distance | Далеко? | далеко / бли́зько / хвилин пішки | П'ять хвилин пішки. |

:::tip
Streets, avenues, and squares always use **на**: **на вулиці Франка́**, **на площі**, **на проспе́кті**. Buildings you enter use **в/у**: **в магази́ні**, **в офісі**, **у теа́трі**. Metro always stays with **на**: **на метро** — both for location and transport.
:::

Now see how all four rows work together in connected speech. **Марі́я** lives in Lviv and is heading to the theater:

**Марія живе́ у Льво́ві** (де? — locative). **Сього́дні вона́ йде в театр** (куди? — accusative). **Театр на площі** (де? — locative). **Потім вона ї́де на метро до центру** (куди? — accusative). **Центр далеко** — п'ять хвилин на метро, а потім **іде́ пішки** три хвили́ни. The question type shifts six times in this short passage — and that is completely natural.

<!-- INJECT_ACTIVITY: quiz-de-kudy -->

## Мій райо́н (My Neighborhood)

Every learner needs to describe where they live. Here is a model paragraph you can adapt with your own details:

**Я живу́ на вулиці Франка.** **Бі́ля мого до́му є парк і мале́нький магазин.** **Шко́ла далеко** — тре́ба ї́хати автобусом де́сять хвилин. **Апте́ка близько**, мо́жна піти **пішки**. **У моє́му райо́ні є кафе́, два рестора́ни і бібліотека.**

Key structures to notice: **біля мого дому** (near my house) is a genitive chunk — learn it as a fixed unit. The construction **є** + noun list means "there is / there are." Two modal chunks appear: **треба їхати** (must go by vehicle) and **можна піти** (can go on foot).

Now put the required vocabulary into full sentences:

- **пішки** (on foot) → Аптека близько — іду **пішки**.
- **хвили́на** (minute) → П'ять **хвилин** пішки від зупи́нки.
- **далеко від** / **близько від** (far from / near) → Школа **далеко від** дому. Парк **близько від** робо́ти.
- **у це́нтрі мі́ста** (in the city center) → Готе́ль **у центрі міста**.
- **на око́лиці** (on the outskirts) → Я живу **на околиці**, не в центрі.

:::note
The chunks **далеко від** and **близько від** are followed by genitive case. At this stage, memorize them as fixed phrases with common nouns: далеко від дому, близько від роботи, далеко від зупинки.
:::

Now try building your own description using these sentence frames:

1. **Я живу** [де — ву́лиця / мі́сто]. **Біля мого дому є** [що].
2. [Мі́сце] [далеко / близько]. **Треба їхати** [чим] / **Можна піти пішки.**
3. **У моєму районі є** [list 3 places].

Three example outputs for different situations:

- City center: **Я живу на вулиці Хреща́тик. Біля мого дому є метро. Парк близько — п'ять хвилин пішки. У моєму районі є театр, музей і кафе.**
- Suburb: **Я живу на околиці. Біля мого дому є зупи́нка. Центр далеко — треба їхати автобусом. У моєму районі є школа, магазин і аптека.**
- Small town: **Я живу у мале́нькому мі́сті. Біля мого дому є парк. Магазин близько — три хвилини пішки. У моєму районі є бібліотека, кафе і школа.**

The sentence frames stay identical — only the details change.

<!-- INJECT_ACTIVITY: fill-in-transport -->

## Підсумок — Summary

Here is your urban communication toolkit — a reference card for navigating any Ukrainian city:

**Запита́ти доро́гу** (asking for directions):
- Вибачте, як дістатися до [місця́]?
- Де є [місце]?

**На́прямок** (direction):
- **прямо** (straight) → **направо** (right) → **налі́во** (left) → **на розі** (at the corner)

**Де?** (locative — static):
- в/на + locative: **у парку**, **в театрі**, **на вулиці**, **на площі**

**Куди?** (accusative — motion):
- в/на + accusative: **у парк**, **в театр**, **на ву́лицю**, **на пло́щу**

**Транспорт** (transport):
- **автобусом** / **на метро** / **пішки** — П'ять **хвилин** пішки.

### Self-Check

Answer these five prompts mentally or aloud, then check your answers:

1. You are standing on a street. A stranger asks how to get to the library. The library: straight, then left. What do you say? — *Ідіть прямо, потім наліво. Бібліотека там.*

2. Describe your morning route in three sentences using **спочатку... потім... а потім...** — *(Free production — use your real route.)*

3. Choose the correct form: Я зараз — **в театрі** чи **в театр**? Я йду — **в театрі** чи **в театр**? — *В театрі (static, де?) / В театр (motion, куди?).*

4. How do you say "five minutes on foot"? — *П'ять хвилин пішки.*

5. Where do you live? What is near your house? Say it in two sentences. — *(Free production using Я живу на... Біля мого дому є...)*

<!-- INJECT_ACTIVITY: match-navigation -->

**Deterministic word count: 1281 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 125 words | Not found: 54 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іді — NOT IN VESUM
  ✗ Апте — NOT IN VESUM
  ✗ Бібліоте — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Льво — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Перехо — NOT IN VESUM
  ✗ Ситуа — NOT IN VESUM
  ✗ Споча — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Хреща — NOT IN VESUM
  ✗ Шко — NOT IN VESUM
  ✗ бли — NOT IN VESUM
  ✗ бібліоте — NOT IN VESUM
  ✗ доро — NOT IN VESUM
  ✗ дьте — NOT IN VESUM
  ✗ діста — NOT IN VESUM
  ✗ жий — NOT IN VESUM
  ✗ жна — NOT IN VESUM
  ✗ зом — NOT IN VESUM
  ✗ зько — NOT IN VESUM
  ✗ кті — NOT IN VESUM
  ✗ магази — NOT IN VESUM
  ✗ музе — NOT IN VESUM
  ✗ налі — NOT IN VESUM
  ✗ напра — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нки — NOT IN VESUM
  ✗ нку — NOT IN VESUM
  ✗ ння — NOT IN VESUM
  ✗ нтру — NOT IN VESUM
  ✗ нтрі — NOT IN VESUM
  ✗ нький — NOT IN VESUM
  ✗ нькому — NOT IN VESUM
  ✗ пло — NOT IN VESUM
  ✗ проспе — NOT IN VESUM
  ✗ прямок — NOT IN VESUM
  ✗ райо — NOT IN VESUM
  ✗ рестора — NOT IN VESUM
  ✗ рма — NOT IN VESUM
  ✗ сті — NOT IN VESUM
  ✗ сце — NOT IN VESUM
  ✗ сять — NOT IN VESUM
  ✗ теа — NOT IN VESUM
  ✗ тися — NOT IN VESUM
  ✗ тку — NOT IN VESUM
  ✗ трі — NOT IN VESUM
  ✗ фісі — NOT IN VESUM

All 125 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
