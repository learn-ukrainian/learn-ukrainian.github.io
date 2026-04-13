<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 36: Компас відмінків (A2, A2.5 [Case Synthesis and Plurals])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-036
level: A2
sequence: 36
slug: which-case-when
version: '1.0'
title: Компас відмінків
subtitle: Як обрати правильний відмінок за дієсловом, прийменником та контекстом
focus: grammar
pedagogy: PPP
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
  - Learner can select the correct case for a noun based on the governing verb 
    (e.g., допомагати + Dat., бачити + Acc., користуватися + Instr.).
  - Learner can select the correct case after common prepositions, including 
    prepositions that govern different cases depending on meaning (на + Acc. for
    direction vs. на + Loc. for location).
  - Learner can use Accusative for time expressions (у четвер, у середу), with 
    про (думати про майбутнє), and recognize Locative for characteristics 
    (хлопець у червоному светрі), path (бігати по кімнаті), and years (у 2014 
    році).
  - Learner can apply a systematic decision process (verb/preposition → case → 
    ending) to determine the correct form of any noun in context.
dialogue_situations:
  - setting: 'Grammar detective game — reading a Ukrainian newspaper article and identifying
      which case is used and why: Президент (nom) зустрівся з прем''єром (inst). Для
      журналістів (gen) підготували зал (acc).'
    speakers:
      - Вчитель
      - Студенти
    motivation: 'Case identification: nom, gen, dat, acc, inst, loc in real text'
content_outline:
  - section: 'Дієслово вирішує: Який відмінок після дієслова? (The Verb Decides: Which
      Case After a Verb?)'
    words: 550
    points:
      - 'Accusative verbs (most transitive): бачити, знати, любити, читати, купити,
        шукати + Acc. Я читаю книгу. Ми шукаємо ключі.'
      - 'Dative verbs: допомагати, телефонувати, дякувати, радити, заважати + Dat.
        Я допомагаю сестрі. Ми дякуємо вчителям.'
      - 'Instrumental verbs: користуватися, цікавитися, займатися, керувати + Instr.
        Він користується комп''ютером. Вона цікавиться історією.'
      - 'Genitive verbs/constructions: немає + Gen., боятися + Gen., потребувати +
        Gen. У мене немає часу. Вона боїться темряви.'
      - 'Thinking about + Acc.: думати про + Acc. (думати про майбутнє, мріяти про
        подорож).'
  - section: 'Прийменник вирішує: Один прийменник — різні відмінки (The Preposition
      Decides: One Preposition, Different Cases)'
    words: 550
    points:
      - 'на + Acc. (direction/goal): Я йду на роботу. Поклади книгу на стіл. на +
        Loc. (location): Я на роботі. Книга лежить на столі.'
      - 'у/в + Acc. (direction): Я йду в магазин. Acc. for time: у четвер, у середу,
        у п''ятницю. у/в + Loc. (location): Я в магазині. Loc. for years: у 2014 році,
        у минулому році.'
      - 'по + Loc. (path/surface): бігати по кімнаті, ходити по вулиці, подорожувати
        по Україні.'
      - 'з/із + Gen. (from/out of): вийти з дому, приїхати з Києва. з/із + Instr.
        (together with): піти з другом, кава з молоком.'
      - 'за + Acc. (in exchange/for): дякувати за допомогу, платити за квитки. за
        + Instr. (behind/after): за столом, бігти за автобусом.'
  - section: 'Особливі випадки: Час, характеристика, шлях (Special Uses: Time, Characteristics,
      Path)'
    words: 500
    points:
      - 'Acc. for days and time periods: у четвер, у середу, у п''ятницю. Цю неділю
        я відпочиваю. Наступного тижня (Gen. for next/last).'
      - 'Loc. for characteristics/description: хлопець у червоному светрі, дівчина
        в окулярах, жінка у білому пальті. Pattern: noun + у/в + Loc. describes what
        someone is wearing or looks like.'
      - 'Loc. for years and time contexts: у 2014 році, у двадцять першому столітті,
        у дитинстві.'
      - 'Loc. for path with по: бігати по кімнаті, гуляти по парку, їздити по місту.'
  - section: 'Алгоритм вибору відмінка (The Case Selection Algorithm)'
    words: 400
    points:
      - 'Step 1: Is there a preposition? → Check which case(s) it governs. Step 2:
        No preposition? → Check which case the verb requires. Step 3: Still unsure?
        → Ask the case question (Кого? Що? Кому? Ким? etc.).'
      - 'Decision tree visual: Preposition → Case. Verb → Case. Neither → Default
        Nom. (subject) or context-dependent.'
      - 'Common pitfalls: confusing на + Acc. (direction) with на + Loc. (location);
        forgetting that думати takes про + Acc., not Loc.; using Gen. instead of Dat.
        after допомагати.'
      - 'Practice: mixed sentences where learner must identify the trigger (verb or
        preposition) and choose the correct case.'
vocabulary_hints:
  required:
    - відмінок (grammatical case)
    - прийменник (preposition)
    - дієслово (verb)
    - напрямок (direction)
    - місце (place, location)
    - час (time)
    - характеристика (characteristic, description)
    - думати (to think)
    - боятися (to be afraid)
    - користуватися (to use)
  recommended:
    - алгоритм (algorithm)
    - контекст (context)
    - керувати (to manage, drive)
    - майбутнє (future)
activity_hints:
  - type: quiz
    focus: Given a sentence with a blank, choose the correct case form based on 
      the governing verb or preposition
    items: 8
  - type: group-sort
    focus: Sort prepositions by which case(s) they govern (Acc., Gen., Instr., 
      Loc.)
    items: 8
  - type: fill-in
    focus: Complete sentences with the correct noun form — mixed cases triggered
      by different prepositions and verbs, including time expressions (у 
      четвер), characteristics (у червоному светрі), and path (по кімнаті)
    items: 8
  - type: true-false
    focus: Judge whether the case used in a sentence is correct or incorrect, 
      including tricky pairs like на роботу (Acc.) vs. на роботі (Loc.)
    items: 8
references:
  - title: Заболотний Grade 6, §§59-67
    notes: Complete case system overview — when each case is used, with 
      preposition tables
  - title: Заболотний Grade 10, §§44-45
    notes: Advanced case usage — Loc. for characteristics, time expressions with
      cases
  - title: "ULP: Ukrainian Cases Overview"
    url: "https://www.ukrainianlessons.com/ukrainian-cases/"
    notes: Practical summary of all 7 cases with usage examples

</plan_content>

## Generated Content

<generated_module_content>
## Дієслово вирішує: Який відмінок після дієслова? (~600 words)

Сьогодні ми граємо в граматичних детективів. Ми читаємо українську газету і шукаємо кожен **відмінок** (grammatical case). Такий спосіб аналізу спирається на шкільні підручники Заболотного та огляд ULP: спочатку визначаємо слово, яке керує формою, а потім обираємо закінчення.

> — **Вчитель:** Читаємо перший текст. «Президент зустрівся з прем'єром. Для журналістів підготували зал». Які відмінки ви вже бачите? *(Let's read the first text. "The president met with the prime minister. They prepared a hall for the journalists". Which cases can you already see?)*
> — **Студенти:** «Президент» — це називний, бо це суб'єкт. «З прем'єром» — орудний, бо тут прийменник «з». *("President" is the nominative because it is the subject. "With the prime minister" is instrumental because of the preposition "з".)*
> — **Вчитель:** Добре. А як пояснити «для журналістів» і «зал»? *(Good. And how do we explain "for the journalists" and "hall"?)*
> — **Студенти:** «Для журналістів» — це родовий після прийменника «для», а «зал» — знахідний, бо це об'єкт дії «підготували». *("For the journalists" is genitive after the preposition "для", and "hall" is accusative because it is the object of the action "prepared".)*

When an action passes directly onto an object, the Ukrainian language uses the Accusative case. Most transitive verbs require this case, and mastering them is your first big step in sentence building.

Коли ви хочете щось купити, знайти або прочитати, вам потрібен знахідний відмінок. Такі слова як «бачити», «знати», «любити», «читати», «купити» та «шукати» завжди вимагають об'єкта. Я читаю книгу. Ми шукаємо ключі. Вона знає цього хлопця. Кожне **дієслово** (verb) тут напряму впливає на об'єкт.

> *When you want to buy, find, or read something, you need the accusative case. Words like "to see", "to know", "to love", "to read", "to buy", and "to look for" always require an object. I am reading a book. We are looking for the keys. She knows this guy. Every verb here directly affects the object.*

Some actions are directed *towards* a recipient rather than done *to* an object. In Ukrainian, you do these actions *to* or *for* someone, which means you must use the Dative case.

Ми даємо допомогу або пораду комусь. Тому слова «допомагати», «телефонувати», «дякувати», «радити» та «заважати» вимагають давального відмінка. Я допомагаю сестрі. Ми щиро дякуємо вчителям. Він телефонує батькам. Це дуже важливе правило.

> *We give help or advice to someone. Therefore, words like "to help", "to call", "to thank", "to advise", and "to bother" require the dative case. I help my sister. We sincerely thank the teachers. He calls his parents. This is a very important rule.*

:::info
**Grammar box**
Always remember: you thank *to* someone (`дякувати комусь`), help *to* someone (`допомагати комусь`), and bother *to* someone (`заважати комусь`). Using the Accusative here is a very common mistake!
:::

Another specific group of verbs describes what tool you use, what you manage, or what you are interested in. These concepts are expressed using the Instrumental case, completely without prepositions.

Якщо ви хочете чимось **користуватися** (to use), вам потрібен орудний відмінок. Він користується новим комп'ютером. Вона цікавиться історією. Мій друг займається спортом. Директор керує великою компанією. Іменник показує інструмент дії або сферу вашого інтересу.

> *If you want to use something, you need the instrumental case. He uses a new computer. She is interested in history. My friend does sports. The director manages a large company. The noun shows the tool of the action or the area of your interest.*

Verbs expressing fear, need, or a lack of something strictly require the Genitive case.

Найпопулярніше слово для цього відмінка — «немає». У мене немає часу. Але ми також маємо дієслова. Якщо ви хочете чогось **боятися** (to be afraid) або потребувати, використовуйте родовий відмінок. Вона боїться темряви. Проєкт потребує інвестицій.

> *The most popular word for this case is "there is no". I have no time. But we also have verbs. If you want to be afraid of something or require something, use the genitive case. She is afraid of the dark. The project requires investments.*

Finally, some verbs require a specific preposition, which dictates the case. A classic example is when you **думати** (to think) about something. The preposition «про» always takes the Accusative.

Коли ви мрієте або думаєте про щось, ви використовуєте прийменник «про» і знахідний відмінок. Я часто думаю про майбутнє. Вони мріють про подорож. Ми думаємо про новий план.

> *When you dream or think about something, you use the preposition "про" and the accusative case. I often think about the future. They dream about a trip. We are thinking about a new plan.*

<!-- INJECT_ACTIVITY: true-false-case-pairs -->
</generated_module_content>

**PIPELINE NOTE — Word count: 732 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
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

Verified: 165 words | Not found: 0 words

All 165 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
