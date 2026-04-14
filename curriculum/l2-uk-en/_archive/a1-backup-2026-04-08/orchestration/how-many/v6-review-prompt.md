<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 11: How Many? (A1, A1.2 [My World])
**Writer:** Claude
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-011
level: A1
sequence: 11
slug: how-many
version: '1.2'
title: How Many?
subtitle: Один, два, три — numbers through prices, ages, and phones
focus: vocabulary
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Count from 1 to 100 in Ukrainian
- Say prices using гривня and round numbers up to 1000
- Give age using Мені ... років (as memorized chunk — NO case grammar)
- Read and say Ukrainian phone numbers
dialogue_situations:
- setting: 'At a bakery — ordering bread, pastries, and cakes for a family gathering.
    Count: один хліб (m, bread), одна булочка (f, bun), одне тістечко (n, pastry). Prices in гривні.
    Ask: Скільки коштує торт? А три булочки?'
  speakers:
  - Покупець
  - Пекар (baker)
  motivation: Скільки коштує? with торт(m), булочка(f), тістечко(n), хліб(m)
- setting: Counting items in a school backpack before class — ручка (f, pen), олівець
    (m, pencil), зошит (m, notebook), підручник (m, textbook).
  speakers:
  - Учень (student)
  - Мама
  motivation: 'Numbers with school supplies: один олівець, дві ручки, п''ять зошитів'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At a market stall: — Скільки коштує сумка? — Двісті гривень.
    — А маленька? — Сто п''ятдесят. — Добре, дякую!
    Numbers emerge through real shopping context. Uses only vocabulary from M08-M10
    (gender, adjectives, colors). Demonstratives (ця/та) come in M12.'
  - 'Dialogue 2 — Meeting someone new (extending M05): — Скільки тобі років? — Мені
    двадцять п''ять. А тобі? — Мені тридцять два. А твоя сестра? — Їй вісімнадцять.
    Age formula as chunk: Мені/тобі/їй + number + років/роки/рік.'
- section: Числа 1-20 (Numbers 1-20)
  words: 300
  points:
  - '1-10: один, два, три, чотири, п''ять, шість, сім, вісім, дев''ять, десять. Pronunciation
    focus: п''ять (apostrophe!), сім (not ''сем''), дев''ять (apostrophe!). Practice:
    counting objects from M08 — один стіл, два стільці, три книги. Note: the noun
    changes after numbers, but we learn the PATTERNS as chunks, not the grammar rule.'
  - '11-20: одинадцять, дванадцять, тринадцять, чотирнадцять, п''ятнадцять, шістнадцять,
    сімнадцять, вісімнадцять, дев''ятнадцять, двадцять. Pattern: base + -надцять (like
    English ''-teen''). Watch the stress: одинáдцять, дванáдцять — stress always falls
    on the syllable ''на'' in -надцять.'
- section: Десятки і сотні (Tens and Hundreds)
  words: 300
  points:
  - 'Tens: двадцять, тридцять, сорок (!), п''ятдесят, шістдесят, сімдесят, вісімдесят,
    дев''яносто (!), сто. Two irregulars: сорок (40 — not ''чотиридесят'') and дев''яносто
    (90 — not ''дев''ятдесят''). Combined: двадцять один, тридцять п''ять, сорок сім
    — just add the unit.'
  - 'Hundreds for prices: сто (100), двісті (200), триста (300), чотириста (400),
    п''ятсот (500), тисяча (1000). Гривня: одна гривня, дві гривні, п''ять гривень.
    These noun changes are memorized patterns — grammar comes in A2. ULP Ep9: Anna
    teaches numbers through real prices.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three practical uses of numbers: 1. Prices: Скільки коштує? — Двісті гривень.
    Сто п''ятдесят гривень. 2. Age: Скільки тобі років? — Мені двадцять три (роки).
    3. Phone: Мій номер — нуль дев''яносто сім, три два один, сорок п''ять, шістдесят
    сім. Self-check: Say your age in Ukrainian. Say a price (250 hryvnias). Read a
    phone number.'
vocabulary_hints:
  required:
  - один, два, три, чотири, п'ять (1-5)
  - шість, сім, вісім, дев'ять, десять (6-10)
  - двадцять, тридцять, сорок (20, 30, 40)
  - сто, тисяча (100, 1000)
  - скільки (how many/how much)
  - коштує (costs — from коштувати)
  - гривня (hryvnia — Ukrainian currency)
  - рік, роки, років (year/years — age chunks)
  recommended:
  - п'ятдесят, шістдесят, сімдесят (50, 60, 70)
  - вісімдесят, дев'яносто (80, 90)
  - двісті, триста, п'ятсот (200, 300, 500)
  - копійка (kopek)
  - номер (number — phone/room)
  - нуль (zero)
activity_hints:
- type: fill-in
  focus: 'Write the number in words: 15 → п''ятнадцять, 47 → сорок сім'
  items: 10
- type: quiz
  focus: Скільки коштує? Match price tags to spoken prices.
  items: 8
- type: quiz
  focus: Скільки років? Match ages to descriptions.
  items: 6
- type: fill-in
  focus: Complete the phone number dictation
  items: 4
connects_to:
- a1-012 (This and That)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- Cardinal numbers 1-1000 (vocabulary, not morphology)
- Скільки коштує? question pattern
- 'Age chunk: Мені + number + років/роки/рік (memorized, not analyzed)'
- 'Irregular tens: сорок (40), дев''яносто (90)'
register: розмовний
references:
- title: ULP Season 1, Episode 5
  url: https://www.ukrainianlessons.com/episode5/
  notes: Numbers 1-10 pronunciation.
- title: ULP Season 1, Episode 9
  url: https://www.ukrainianlessons.com/episode9/
  notes: Numbers 11-100 and prices.
- title: Авраменко Grade 6, p.152
  notes: Числівники кількісні vs порядкові — basic classification.

</plan_content>

## Generated Content

<generated_module_content>
## Діало́ги (Dialogues)
> — **Покупе́ць:** До́брий день! Скі́льки ко́шту́є торт? *(Good day! How much does the cake cost?)*
> — **Пекар:** Дві́сті гри́вень. *(Two hundred hryvnias.)*
> — **Покупець:** А хліб? *(And the bread?)*
> — **Пекар:** П'ятна́дцять гривень. *(Fifteen hryvnias.)*
> — **Покупець:** А три бу́лочки? *(And three buns?)*
> — **Пекар:** Соро́к п'ять гривень. *(Forty-five hryvnias.)*
> — **Покупець:** А одне́ ті́стечко? *(And one pastry?)*
> — **Пекар:** Два́дцять гривень. *(Twenty hryvnias.)*
> — **Покупець:** До́бре. Дякую, до поба́чення! *(Okay. Thank you, goodbye!)*

Notice the question **Скільки коштує?** (How much does it cost?) — this is the single most useful phrase for shopping in Ukraine. The three nouns in this dialogue are recycled vocabulary from earlier modules: **торт** (cake) is masculine, **бу́лочка** (bun) is feminine, and **тістечко** (pastry) is neuter. You might see that the noun endings change after different numbers — **одне тістечко** but **три булочки**, **п'ятнадцять гривень** but **двісті гривень**. These changes follow a pattern you will memorize as chunks now. The grammar behind them arrives in A2.
> — **Оле́нка:** Приві́т, Тара́се! Скільки тобі́ ро́кі́в? *(Hi, Taras! How old are you?)*
> — **Тара́с:** Ме́ні двадцять п'ять. А тобі? *(I'm twenty-five. And you?)*
> — **Оленка:** Мені три́дцять два. А твоя́ сестра́ моло́дша? *(I'm thirty-two. Is your sister younger?)*
> — **Тарас:** Так, їй вісімна́дцять. *(Yes, she's eighteen.)*
> — **Оленка:** А твій брат? *(And your brother?)*
> — **Тарас:** Йому одина́дцять. *(He's eleven.)*

The age formula in Ukrainian works like a fixed chunk: **Мені** (I am), **тобі** (you are), **йому** (he is), **їй** (she is) + a number + **років**. Ukrainian uses three different words for "year(s)" depending on the number: **рік** (year) after 1, **ро́ки́** (years) after 2–4, and **років** (years) after 5 and above. At A1, memorize these as a pattern — one **рік**, twenty-two **роки**, five **років**. Notice in the dialogue: **двадцять п'ять** (25) and **тридцять два** (32) — these combined numbers are just the tens word plus the unit, with no connector. No case analysis needed.
<!-- INJECT_ACTIVITY: quiz-age -->
## Чи́сла 1-20 (Numbers 1-20)
The first ten numbers in Ukrainian are: **оди́н** (1), **два** (2), **три** (3), **чоти́ри** (4), **п'ять** (5), **шість** (6), **сім** (7), **ві́сім** (8), **де́в'ять** (9), **де́сять** (10). Three of these need extra attention when you say them aloud. First, **п'ять** has an apostrophe — the letter **п** is followed by **'ять**, giving it a "p-yat" sound. Second, **сім** is the Ukrainian word for seven — it is NOT "сем," which is a Russian ghost form. Third, **дев'ять** also carries an apostrophe, making it two syllables: "dev-yat." Try counting objects from earlier modules: **один стіл** (one table), **два стільці́** (two chairs), **три кни́ги** (three books), **чотири ручки** (four pens), **п'ять зо́шитів** (five notebooks). The number always comes first, and the nouns are words you already know.
Numbers 11–20 follow a clear pattern. Ukrainian textbooks (Vashulenko, Grade 3) list them as a family built from a base number plus the suffix **-на́дцять**, parallel to the English "-teen": **одинадцять** (11), **двана́дцять** (12), **трина́дцять** (13), **чотирна́дцять** (14), **п'ятнадцять** (15), **шістна́дцять** (16), **сімна́дцять** (17), **вісімнадцять** (18), **дев'ятна́дцять** (19), **двадцять** (20). The stress rule is consistent and simple: stress ALWAYS falls on the **-на-** syllable within **-надцять**. So it is одинáдцять, дванáдцять, тринáдцять, and so on through дев'ятнáдцять. One spelling trap: **шістнадцять** is written without a soft sign before **н** — not "шістьнадцять." A counting rhyme by Ле́ся Возню́к (in Kravcova, Grade 2, p. 92) puts numbers 1–10 into context: «Один і два — росла́ трава́, три, чотири — покоси́ли, п'ять — на со́нечку суши́ли, шість — в копи́чку посклада́ли, сім — корі́вку годува́ли, вісім — молочко́ дава́ла, дев'ять — ді́ток напува́ла, десять — привела́ теля́тко. Почина́ймо все споча́тку!» Reading this aloud is excellent pronunciation practice for all ten base numbers.
With numbers 1–20 in hand, you can already do two practical things. First, count real objects around you: **скільки стільці́в у кімна́ті?** (how many chairs in the room?) **скільки книжо́к на столі́?** (how many books on the table?) Second, answer age questions from the dialogue above: **Мені** + number + **років**. Say your own age, a sibling's age, a friend's age — all using numbers from this section. Combined numbers like **двадцять один** (21) and **тридцять п'ять** (35) come in the next section.
<!-- INJECT_ACTIVITY: fill-in-numbers -->
## Деся́тки і со́тні (Tens and Hundreds)
The tens from 20 to 100 follow a predictable pattern — with two famous exceptions. Here is the full list: **двадцять** (20), **тридцять** (30), **сорок** (40), **п'ятдеся́т** (50), **шістдеся́т** (60), **сімдеся́т** (70), **вісімдеся́т** (80), **дев'яно́сто** (90), **сто** (100). Most tens are built from a base number plus a suffix: п'ять → **п'ятдесят**, шість → **шістдесят**. But **сорок** (40) is completely irregular — there is no "чотиридесят" in Ukrainian. Historically, **сорок** referred to a bundle of forty animal pelts used as a trading unit (Го́луб, Grade 6). And **дев'яносто** (90) breaks the pattern too — it is not "дев'ятдеся́т." Memorize both as standalone words. To make combined numbers, place the tens word before the unit with no connector: **двадцять один** (21), **тридцять п'ять** (35), **сорок сім** (47), **вісімдесят дев'ять** (89). Practice examples: **двадцять три студе́нти** (23 students), **сорок вісім гривень** (48 hryvnias), **дев'яносто дві копійки́** (92 kopeks).
For prices above 100, you need the hundreds: **сто** (100), **двісті** (200), **три́ста** (300), **чоти́риста** (400), **п'ятсо́т** (500), **шістсо́т** (600), **сімсо́т** (700), **вісімсо́т** (800), **дев'ятсо́т** (900), **ти́сяча** (1000). Notice the pattern shift: at 200 the form is **двісті** (not "двасто"), at 300–400 it is **триста** and **чотириста**, and from 500 onward the suffix is **-сот**. The Ukrainian currency is **гри́вня** (hryvnia), and it changes form after numbers just like "year" does: **одна́ гривня** (1), **дві гри́вні** (2–4), **п'ять гривень** (5+). Important: the currency word is **гривня**, not **гри́вна** — that is a different word meaning a neck ornament. Memorize three price chunks from the bakery dialogue: **п'ятнадцять гривень** (15₴), **сорок п'ять гривень** (45₴), **двісті гривень** (200₴). The noun changes гривня/гривні/гривень are price chunks for now — case grammar arrives in A2.
Ukrainian mobile numbers follow the format 0XX-XXX-XX-XX. Break them into groups for easier reading: **нуль дев'яносто сім** (097) — pause — **три два один** (321) — pause — **сорок п'ять** (45) — pause — **шістдесят сім** (67). Each group is read as a mini-number. A full example: **Мій но́мер** (my number) — **нуль дев'яносто сім, три два один, сорок п'ять, шістдесят сім**.
<!-- INJECT_ACTIVITY: quiz-prices -->
<!-- INJECT_ACTIVITY: fill-in-phone -->
## Підсумок — Summary
This module built three number systems. First, cardinal numbers 1–20: the base ten (**один** through **десять**), then the **-надцять** teens with stress always on **-на-** (одинáдцять, дванáдцять...). Two apostrophe words to remember: **п'ять** and **дев'ять**. Second, the tens from 20 to 100, with two irregulars that must simply be memorized: **сорок** (40) and **дев'яносто** (90). Third, the hundreds from **сто** to **тисяча**, where the pattern shifts at **двісті** (200) and again at **п'ятсот** (500). Combined numbers never need a connector word — just say the tens then the unit: **двадцять три** (23), **сто сорок п'ять** (145).
**Prices.** The question is **Скільки коштує?** and the answer is a number plus the right form of **гривня**: **одна гривня** (1₴), **дві гривні** (2–4₴), **п'ять гривень** (5+₴). Three memorized frames: **п'ятнадцять гривень** (bread), **сорок п'ять гривень** (three buns), **двісті гривень** (a cake). You can now ask and answer any price up to **тисяча гривень** (1000₴).
**Age.** The question is **Скільки тобі років?** and the answer follows the formula: **Мені/Йому/Їй** + number + **рік/роки/років**. Three memorized frames: **Мені двадцять п'ять років** (25), **Йому двадцять два роки** (22), **Їй тридцять п'ять років** (35). The switch between рік, роки, and років is a chunk — feel it through repetition, do not analyze it.
**Phone numbers.** Read Ukrainian mobile numbers in groups of 3–3–2–2. Practice with three sample numbers: (a) 097-321-45-67, (b) 050-112-33-99, (c) 073-456-78-10. Read each one aloud in Ukrainian. The bakery could call you when your cake is ready — just say **Мій номер телефо́ну...** and dictate it.
Self-check — answer these in Ukrainian:
- Як сказа́ти 17? → **сімнадцять**
- Як сказати 40? → **сорок** (not "чотиридесят"!)
- Як сказати 90? → **дев'яносто** (not "дев'ятдесят"!)
- Торт коштує 250₴. Як сказати? → **Двісті п'ятдесят гривень.**
- Скажі́ть своє́ ім'я́ і вік: **Ме́не зва́ти ___, мені ___ років.**
- Продикту́йте свій номер телефону по-украї́нськи.

**Deterministic word count: 1384 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 108 words | Not found: 78 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Возню — NOT IN VESUM
  ✗ Деся — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ П'ятна — NOT IN VESUM
  ✗ Приві — NOT IN VESUM
  ✗ Продикту — NOT IN VESUM
  ✗ Скажі — NOT IN VESUM
  ✗ Скі — NOT IN VESUM
  ✗ Соро — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ в'ять — NOT IN VESUM
  ✗ вень — NOT IN VESUM
  ✗ вку — NOT IN VESUM
  ✗ вна — NOT IN VESUM
  ✗ вня — NOT IN VESUM
  ✗ вні — NOT IN VESUM
  ✗ вісімдеся — NOT IN VESUM
  ✗ вісімна — NOT IN VESUM
  ✗ вісімсо — NOT IN VESUM
  ✗ годува — NOT IN VESUM
  ✗ двана — NOT IN VESUM
  ✗ двасто — NOT IN VESUM
  ✗ дев' — NOT IN VESUM
  ✗ дев'яно — NOT IN VESUM
  ✗ дев'ятдеся — NOT IN VESUM
  ✗ дев'ятна — NOT IN VESUM
  ✗ дев'ятсо — NOT IN VESUM
  ✗ дцять — NOT IN VESUM
  ✗ дша — NOT IN VESUM
  ✗ зва — NOT IN VESUM
  ✗ ймо — NOT IN VESUM
  ✗ йте — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ книжо — NOT IN VESUM
  ✗ кімна — NOT IN VESUM
  ✗ лочка — NOT IN VESUM
  ✗ лочки — NOT IN VESUM
  ✗ льки — NOT IN VESUM
  ✗ моло — NOT IN VESUM
  ✗ нечку — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нськи — NOT IN VESUM
  ✗ нти — NOT IN VESUM
  ✗ одина — NOT IN VESUM
  ✗ п'ятдеся — NOT IN VESUM
  ✗ п'ятсо — NOT IN VESUM
  ✗ поба — NOT IN VESUM
  ✗ риста — NOT IN VESUM
  ✗ сказа — NOT IN VESUM

All 108 other words are confirmed to exist in VESUM.

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
