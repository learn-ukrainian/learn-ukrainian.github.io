# l2-uk-direct Curriculum Plan

> Last updated: 2026-02-26
> State standard reference: `docs/l2-uk-en/state-standard-2024-mapping.yaml`
> Gap analysis: `docs/l2-uk-direct/A1-GAP-ANALYSIS.md`
> GH Issues: Infrastructure [#661](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/661) | Content [#662](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/662) | Textbooks [#663](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/663) | Scripts [#664](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/664)

---

## Design Principles

1. **Slower start, faster later** — 3 pre-literacy modules before any word recognition. Pays off at module 4+ when learner reads fluently.
2. **Communicative competence first** — greetings, self-introduction, and politeness formulas come before any grammar analysis. A learner can say "Добрий день" and "Мене звати..." before learning what nominative case means.
3. **Cases introduced strictly by state standard schedule** — accusative ≥ module 17, locative ≥ module 20.
4. **Grammar via question words only** — never "nominative case", always "ХТО?/ЩО?"
5. **Each module builds on all previous** — vocabulary from prior modules used in examples.
6. **Checkpoints every ~15 modules** — consolidation and assessment, no new grammar.
7. **Textbook activities embedded** — riddles, proverbs, tongue twisters from school books used throughout. See `docs/l2-uk-direct/textbook-map.yaml` for sources.
8. **L1-agnostic** — zero assumptions about learner's first language. Ukrainian explained purely through Ukrainian.
9. **All 4 speech activities** — listening, reading, writing, and speaking practiced throughout (not just recognition).
10. **All 12 thematic areas** — every State Standard Catalogue B theme has dedicated coverage.
11. **All 17 communicative intentions** — every Catalogue A intention is taught and practiced.

---

## Textbook Reading Schedule

*When to read each book before building the corresponding modules.*

| Book | Status | Read before building... |
|------|--------|------------------------|
| Grade 1 Буквар Part 1 (Bolshakova 2025) | ✅ read | Module 1–3 (done) |
| Grade 1 Буквар Part 2 (Bolshakova 2025) | ✅ read | Module 1–3 (done) |
| Grade 2 Part 1 (Tsepova 2025) | ✅ read | Modules 4–15 (done) |
| Grade 2 Part 2 (Tsepova 2025) | ✅ read | Modules 4–15 (done) |
| Grade 3 Part 1 (Vashulenko 2020) | ✅ read | Modules 1–15 (done) |
| **Grade 3 Part 2** | 🔲 **read before module 27** | Daily life vocabulary → Modules 27–33 |
| Grade 4 Part 1 (Varzatska 2021) | 🔲 read before A2 | A2 planning only |
| Grades 5–7 (Litvinova) | 🔲 low priority | B1+ content |

---

## A1 — Full Module Sequence (44 modules)

---

### Phase 0: Script (Modules 1–3)
*Goal: learner can read Ukrainian text aloud. Activities: pre-literacy only.*
*Textbook source: Grade 1 Буквар (both parts).*

---

#### Module 1: `abetka`
**Focus**: Ukrainian alphabet — 33 letters, sounds, letter groups
**Type**: `script_foundation`
**Status**: ✅ Draft (abetka.yaml complete, validator passes)
**State standard**: §4.1.1 (alphabet), §4.1.2 (apostrophe), §4.1.4 (vowels/consonants)

**Letters section** (33 letters):
All letters with: `upper`, `lower`, `sound_type`, `key_word`, `emoji`, `pronunciation_video` (Anna Ohoiko YouTube).

Special entries:
- Apostrophe (ʼ) — not a letter, a separator (б'ю, п'ять, м'яч)
- Soft sign (Ь) — softens preceding consonant (НЬ, ЛЬ, ТЬ); never starts a word

Letter groups taught:
- Vowels (10): А Е И І О У Є Ї Ю Я
- Consonants (23): Б В Г Ґ Д Ж З Й К Л М Н П Р С Т Ф Х Ц Ч Ш Щ + Ь
- Digraphs flagged: ДЖ, ДЗ (single sounds, two letters)

Tricky pairs to emphasize:
- Г (voiced fricative, like Arabic غ) vs Ґ (plosive, like English G)
- И (central vowel) vs І (front vowel) vs Ї (always /ji/)
- Р is trilled — not English R
- Щ = /ʃtʃ/ — two sounds fused

**Activities** (pre-literacy only — no reading required):

1. `watch_and_repeat` — Anna Ohoiko pronunciation videos, one per letter group (vowels, then consonant groups)
2. `watch_and_repeat` — special sounds (Г/Ґ, Ш/Щ/Ч, Р trill)
3. `image_to_letter` — 30+ emoji → tap the first letter (see abetka.yaml for full list)
4. `classify` — sort letters into vowels (•) vs consonants (—)
5. `classify` — soft vs hard consonants (using • = soft, ─ = hard symbols)

**Images**: 0/33 sourced — one per letter key_word (Pixabay candidates needed; see issue [#664](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/664))

---

#### Module 2: `sklad`
**Focus**: Syllables, stress mark, reading syllables aloud
**Type**: `script_foundation`
**Status**: 🔲 Not built
**State standard**: §4.1.5 (stress), §4.1.4 (vowel–consonant combinations), §4.1.6 (syllable)

**Content**:
- Rule: every syllable has **exactly one vowel**. Syllable = minimal unit of pronunciation.
- Reading CV syllables: МА МО МУ МИ МЕ МІ | БА БО БУ БИ... (all consonants × 6 vowels)
- Reading VC syllables: АМ ОМ УМ ИМ АН ОН...
- Stress mark (´) — always on a vowel, changes meaning (з`амок vs замо`к)
- Soft syllables: НЬ→НЯ, ЛЬ→ЛЯ, ТЬ→ТЯ (Ь softens, Я/Ю/Є/Ї carry the softening vowel)
- Apostrophe separates hard consonant from soft vowel: б'є, п'ять, м'яч

**Vocabulary focus** (20 common 2-syllable words with stress marked):
ма`ма, та`то, ди`тина, ко`тик, со`нце, кни`жка, сто`лик, ша`фа, ві`кно, ді`м, ча`й, во`да, мо`локо, яблу`ко, дере`во, кві`тка, пта`шка, рі`чка, мі`сяць, не`бо

**Activities** (pre-literacy — no reading required):

1. `watch_and_repeat` — video of syllable chains: МА-МА, БА-БА-КА, СО-НЦЕ (teacher clapping rhythm)
2. `classify` — sort 20 emoji images into 1-syllable vs 2-syllable bins (кіт=1, мама=2, яблуко=3)
3. `watch_and_repeat` — stress demonstration: `за'мок` (castle) vs `замо'к` (padlock) — same letters, different meaning
4. `image_to_letter` variant (pre-literacy safe): show image, tap the syllable count (1, 2, or 3 tiles)

---

#### Module 3: `naholos`
**Focus**: Stress patterns, fluent reading of short words
**Type**: `script_foundation`
**Status**: 🔲 Not built
**State standard**: §4.1.5 (stress), §4.1.8 (basic intonation)

**Content**:
- Stress can fall on any syllable: дру`г, дру`зі, дру`жба (all differ)
- Stress shifts in forms: ру`ка → ру`ки → рука`м (awareness only, no rules yet)
- Unstressed vowels: [е]→[и] and [и]→[е] in rapid speech — don't correct, just be aware
- Intonation: rising at the end for questions (Це кіт↗?) vs falling for statements (Це кіт↘.)
- Double stress: за`вжді / завжді` (both acceptable — Grade 3 p.68 confirmed)

**30 practice words with stress marked** (spread across syllable positions):
- Stress on first: `со`нце, `мама`, `осінь`, `місто`, `дерево`, `олень`, `новий`, `читання`
- Stress on second: `весна`, `зима`, `вода`, `земля`, `читáти`, `писáти`, `живемó`, `нести`
- Stress on third: `Украı̈на`, `телефо`н, `сантиме`тр, `листопа`д, `беремо`

**Activities** (first module requiring reading):

1. `pattern_drill` — prompt: «На якому складі наголос?» | given: слово (printed) | answer: 1/2/3
2. `true_false` — «Наголос на першому складі: ВО-ДА» → false (second syllable: во-ДА)
3. `build_sentence` — arrange 5 word tiles into statement; stress marks visible on each tile
4. `tongue_twister` — vowel rhythm drill: «Сáни везуть Сáню; Лáни зеленіють лáнами» (first-syllable stress chain)
5. `pattern_drill` — intonation: same sentence tiles, mark ? or . ending

---

### Phase 1: First Words (Modules 4–9)
*Goal: learner names things and actions, greets people, introduces self.*
*Communicative competence before grammar analysis — greetings first, then naming, then verbs.*

---

#### Module 4: `pryvit` 🆕
**Focus**: Greetings, farewells, politeness formulas, basic social interaction
**Type**: `communicative`
**Status**: 🔲 Not built
**State standard**: Catalogue A items 1–8 (attract attention, introduce, greet, farewell, thank, apologize, congratulate, wish)

**This is the FIRST content module.** Before any grammar, the learner needs to be able to interact socially.

**Vocabulary** (25 expressions — memorize as fixed phrases):

| Function | Phrases |
|---|---|
| Attract attention | Вибачте. Скажіть, будь ласка. |
| Greet | Привіт! Добрий ранок. Добрий день. Добрий вечір. |
| Farewell | До побачення. Бувай! Бувайте! На добраніч. До зустрічі. |
| Thank | Дякую. Дуже дякую. Будь ласка (= you're welcome). |
| Apologize | Вибачте. Пробачте. Вибач (informal). |
| Congratulate | Вітаю! |
| Wish | Бажаю здоров'я! Бажаю щастя! Щасти! |
| Respond to greetings | Добрий день! (echo). Привіт! (echo). Дякую, добре! |
| Agreement | Так. Ні. Добре. Гаразд. |

**Register awareness**: Ти-form (Привіт, Бувай, Вибач) vs Ви-form (Добрий день, Бувайте, Вибачте). Teach as two sets: «з друзями» vs «з незнайомими».

**Textbook enrichment**:
- Proverb: «Ввічливе слово — золотий ключик»

**Activities**:

1. `classify` — sort 15 phrases into: привітання (greetings) vs прощання (farewells) vs подяка (thanks) vs вибачення (apologies)
2. `match_sound` — audio greeting → correct written phrase (6 pairs)
3. `pattern_drill` — situation → correct phrase: «Ви зустрічаєте друга вранці» → «Привіт! Добрий ранок!»
4. `build_sentence` — dialogue completion: Speaker A says [greeting], Speaker B responds
5. `true_false` — «"Бувай" — це привітання» → false (це прощання)
6. `proverb_drill` — «Ввічливе слово — золотий ключик.»
7. `reading` — mini dialogue (4 exchanges): Two people meet on the street, greet, ask «Як справи?», answer «Добре, дякую!», say goodbye. | question: Як справи у друга?

---

#### Module 5: `tse`
**Focus**: Це... — naming things and people. ХТО? ЩО?
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Nominative (ХТО? ЩО?)
**State standard**: §4.2.3.1 (nominative), §4.3.1 (simple sentences)

**Vocabulary** (20 words across three categories):

| Category | Words |
|---|---|
| People (ХТО?) | мама, тато, дитина, друг, вчитель, лікар |
| Animals (ХТО?) | кіт, пес, птах, кінь, риба |
| Objects (ЩО?) | стіл, стілець, книга, сумка, телефон, олівець, вода, хліб |

Key vocabulary notes:
- кіт = male cat, кішка = female cat; пес = dog (more affectionate than собака)
- Diminutives available but teach in Module 34: котик, песик, книжечка

**Sentences**:
- Це мама. / Це кіт. / Це книга.
- Хто це? — Це друг. / Що це? — Це стіл.
- Це не кіт. — Це пес. (negation preview — taught fully in Module 11)

**Key pattern**: Це + [noun in nominative]

**Activities**:

1. `classify` — sort 20 emoji images: ХТО? (living) vs ЩО? (inanimate). Bins labeled with question words.
2. `build_sentence` — arrange tiles: Це + noun (5 sentences)
3. `true_false` — «Це кіт» [shows image of dog] → false
4. `riddle` (**Загадка** — Grade 3 p.63):
   - clues: ["Хоч не солодкий, та дуже смачний. / Щодня він на столі у нас. / Без нього важко буде нам"]
   - answer: ХЛІБ
   - answer_emoji: 🍞
5. `reading` — short passage (2 sentences): «Це мій стіл. На столі є книга і олівець.» — comprehension: Що є на столі?
6. `proverb_drill` — «Без хліба нема обіду» | fill_gap: нема [ХЛІБА] обіду | meaning: «Хліб — основна їжа»

---

#### Module 6: `ya` 🆕
**Focus**: Self-introduction — name, nationality, country, language, age, profession
**Type**: `communicative` + `vocabulary`
**Status**: 🔲 Not built
**State standard**: Catalogue A #2 (introduce self/others), Catalogue B #1 (людина: name, nationality, language, profession, age)

**Core phrases** (fixed patterns — memorize as chunks):

| Pattern | Example |
|---|---|
| Name | Мене звати Олена. / Як тебе звати? / Як Вас звати? |
| Nationality | Я українець / українка. Він японець. Вона іспанка. |
| Country | Я з України. Він з Японії. Вона з Іспанії. |
| Language | Я говорю українською. Вона говорить англійською. |
| Age | Мені двадцять п'ять років. Скільки тобі / Вам років? |
| Profession | Я студент / студентка. Він лікар. Вона вчителька. |

**Vocabulary** (25 words):

Nationalities (m/f pairs): українець/українка, американець/американка, німець/німкеня, японець/японка, іспанець/іспанка, поляк/полька, француз/француженка

Countries: Україна, США, Німеччина, Японія, Іспанія, Польща, Франція, Великобританія

Languages: українською, англійською, німецькою, японською, іспанською

Professions: студент, лікар, вчитель/вчителька, інженер, програміст, водій, продавець, кухар, бухгалтер, музикант

**Note**: «Я з України» uses genitive (з + gen) — teach as a FIXED PHRASE. Don't explain genitive case. The learner memorizes «з України, з Японії, з Німеччини» as chunks.

**Textbook enrichment**:
- Synonyms drill (Grade 3): Батьківщина / Рідний край / Вітчизна / Україна — four ways to say "homeland"

**Activities**:

1. `pattern_drill` — prompt: «Ти з Японії. Як ти скажеш?» | answer: «Я японець/японка. Я з Японії. Я говорю японською.»
2. `build_sentence` — self-introduction from tiles: Мене + звати + [name]. Я + [profession]. Я + з + [country].
3. `classify` — sort words: країна (country) vs національність (nationality) vs мова (language) vs професія (profession)
4. `true_false` — «Українець — це людина з Польщі» → false (з України)
5. `pattern_drill` — homeland synonyms: «Батьківщина, Рідний край, Вітчизна, Україна — це слова з одним значенням» → true
6. `reading` — two self-introductions (3 sentences each): «Мене звати Олена. Я з України. Я вчителька. Мені тридцять років.» | «Мене звати Такеші. Він з Японії. Він інженер.» | questions: Звідки Олена? Яка її професія?
7. `pattern_drill` — introducing others: «Це Марко. Він з Італії. Він говорить італійською.»

---

#### Module 7: `shcho-robyt`
**Focus**: Actions — ЩО РОБИТЬ? Present tense, 3rd person singular
**Type**: `vocabulary` + `grammar`
**Status**: 🔲 Not built
**Grammar**: ЩО РОБИТЬ? (3rd person sg. present)
**State standard**: §4.2.4.1 (indicative present), §4.3.1

**Vocabulary** (15 core verbs):

| Verb (infinitive) | 3sg present | Gloss |
|---|---|---|
| іти | іде | to go (on foot) |
| бігти | біжить | to run |
| сидіти | сидить | to sit |
| стояти | стоїть | to stand |
| лежати | лежить | to lie down |
| їсти | їсть | to eat |
| пити | п'є | to drink |
| спати | спить | to sleep |
| читати | читає | to read |
| писати | пише | to write |
| говорити | говорить | to speak |
| слухати | слухає | to listen |
| дивитися | дивиться | to look/watch |
| малювати | малює | to draw |
| грати | грає | to play |

Conjugation note (teach as patterns, not rules):
- -ає/-яє type: читає, слухає, малює, грає (Conjugation I)
- -ить type: говорить, сидить, стоїть, лежить (Conjugation II)
- Irregular: іде, біжить, їсть, п'є, пише (show explicitly)

**Sentences**:
- Кіт спить. / Мама читає. / Дитина грає.
- Пес біжить. / Птах летить. (introduced naturally)

**Key pattern**: [хто?] + [verb 3sg present] — draws on answer to ЩО РОБИТЬ?

**Activities**:

1. `match_sound` — pairs: image of action + written verb → match them (e.g., 🏃 ↔ БІЖИТЬ)
2. `build_sentence` — tiles: subject (Кіт / Мама / Дитина) + verb (спить / читає / грає)
3. `pattern_drill` — prompt: «ЩО РОБИТЬ кіт? (спати)» | answer: «Кіт спить»
4. `true_false` — «Мама пише» [image shows мама читає] → false (перевір: ЩО РОБИТЬ мама?)
5. `tongue_twister` (**Grade 3 p.81** — adapted for verb sounds):
   - text: «Говорить горобець горобцеві: — Гарно говориш!»
   - focus: Г/Ґ distinction; говорить vs горить
6. `reading` — 3-sentence passage: «Це Оля. Оля читає книгу. Поряд сидить кіт. Кіт спить.» | question: «Що робить Оля?»

---

#### Module 8: `yakyi`
**Focus**: Descriptions — ЯКИЙ? ЯКА? ЯКЕ? Gender agreement
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Adjective gender agreement (nominative only)
**State standard**: §4.2.1.2 (adjective nominative), §4.2.2 (gender)

**Core principle**: In Ukrainian every noun has grammatical gender. Adjectives must match.
- Masculine nouns → ЯКИЙ? → adjective ends in -ий/-ій: великий стіл
- Feminine nouns → ЯКА? → adjective ends in -а/-я: велика книга
- Neuter nouns → ЯКЕ? → adjective ends in -е/-є: велике вікно

**Note on КРАСНИЙ**: красний = гарний/вродливий (beautiful). NOT червоний (red). This is a common false friend for many learners — teach explicitly. (Source: Grade 3 p.96–97)

**Vocabulary** (15 adjective–noun pairs):

| Adjective | Masc | Fem | Neut |
|---|---|---|---|
| big | великий стіл | велика книга | велике вікно |
| small | маленький кіт | маленька сумка | маленьке яблуко |
| beautiful | гарний птах | гарна мама | гарне місто |
| old | старий дідусь | стара школа | старе дерево |
| new | новий телефон | нова куртка | нове слово |
| red | червоний олівець | червона квітка | червоне яблуко |
| blue | синій олівець | синя куртка | синє небо |
| white | білий сніг | біла сорочка | біле молоко |
| black | чорний кіт | чорна ніч | чорне пальто |
| green | зелений ліс | зелена трава | зелене дерево |

**Activities**:

1. `classify` — sort 15 nouns into masculine / feminine / neuter bins (using ХТО?/ЩО? question → ЯКИЙ?/ЯКА?/ЯКЕ? answer)
2. `pattern_drill` — prompt: «ЯКИЙ? великий → ЯКА?» | answer: «велика» (12 adjectives × 3 genders)
3. `build_sentence` — tiles: [adjective] + [noun] — learner must choose the correct adjective form
4. `true_false` — «Великий книга» → false (book is feminine: велика книга)
5. `riddle` (**Grade 3 p.76**):
   - clues: ["Довга шия, як драбина, / В чорних плямах жовта спина"]
   - answer: ЖИРАФ
   - answer_emoji: 🦒
6. `tongue_twister` — vowel agreement drill: «Синій кит, синя хвиля, синє небо» (same adjective, 3 genders)

---

#### Module 9: `mnozh` 🆕
**Focus**: Plural formation — nouns and adjectives
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Nominative plural formation, vowel alternation
**State standard**: §4.2.1.1 (plural formation: -и/-і/-ї, vowel alternation), §4.2.1.2 (adjective plural)

**Noun plural patterns**:

| Pattern | Singular | Plural | Rule |
|---|---|---|---|
| Masc + -и | стіл | столи | consonant + -и |
| Masc + -і | лікар | лікарі | soft consonant + -і |
| Masc + -ї | музей | музеї | й → ї |
| Fem -а → -и | книга | книги | -а → -и |
| Fem -я → -і | земля | землі | -я → -і |
| Neuter -о → -а | вікно | вікна | -о → -а |
| Neuter -е → -я | море | моря | -е → -я |

**Vowel alternation** (чергування голосних — Grade 3 p.105):

| Singular | Plural | What changes |
|---|---|---|
| рік | роки | і → о |
| ніж | ножі | і → о |
| палець | пальці | е drops |
| будинок | будинки | о drops |
| річ | речі | і → е |

**Adjective plurals** (one form for all genders):
- великий/велика/велике → великі (always -і)
- синій/синя/синє → сині (always -і)
- новий/нова/нове → нові (always -і)

**Special nouns** (only-plural, only-singular — Grade 3 p.117):
- Only plural: двері, ножиці, окуляри, сани, гроші, радощі, канікули, штани
- Only singular: молоко, здоров'я, дружба, птаство, дітвора

**Textbook enrichment**:
- Riddle ВІТЕР (Grade 3 p.112): «Без крил і двигуна летить, без ніг, а біжить»

**Activities**:

1. `pattern_drill` — singular → plural: «стіл →» answer: «столи» (20 nouns, all patterns)
2. `classify` — sort 15 nouns by plural ending: -и / -і / -а / -я
3. `true_false` — «Множина слова "ніж" — "ніжі"» → false (ножі — vowel changes)
4. `pattern_drill` — adjective + noun plural: «великий стіл → великі столи» (10 pairs)
5. `classify` — тільки множина (двері, ножиці...) vs тільки однина (молоко, здоров'я...)
6. `riddle` — «Без крил і двигуна летить, без ніг, а біжить» → вітер (source: Grade 3 p.112)
7. `build_sentence` — «Тут є один стіл. А там є три...» → «столи»

---

### Phase 2: Sentences (Modules 10–16)
*Goal: learner makes full sentences, asks all types of questions, expresses preferences.*

---

#### Module 10: `ya-ty-vin`
**Focus**: Personal pronouns + verb conjugation I/II
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: я/ти/він/вона/ми/ви/вони + present tense conjugation
**State standard**: §4.2.1.4 (personal pronouns nominative), §4.2.4.1 (conjugation I/II)

**Pronoun paradigm**:

| Pronoun | Person | Gloss |
|---|---|---|
| я | 1sg | I |
| ти | 2sg | you (familiar) |
| він / вона / воно | 3sg | he / she / it |
| ми | 1pl | we |
| ви | 2pl / formal 2sg | you (pl / polite) |
| вони | 3pl | they |

Note on Ви: Ви (capital V) for formal address to one person; ви (lowercase) for plural. Teach as social register, not grammar rule.

**Two core conjugation patterns** (teach as rhythm, not rule):

Conjugation I (читати type — most -ати verbs):
| | Sing | Plur |
|---|---|---|
| 1 | читаю | читаємо |
| 2 | читаєш | читаєте |
| 3 | читає | читають |

Conjugation II (говорити type — most -ити/-іти verbs):
| | Sing | Plur |
|---|---|---|
| 1 | говорю | говоримо |
| 2 | говориш | говорите |
| 3 | говорить | говорять |

**10 core verbs in both paradigms**: читати, писати, слухати, знати, мати, жити, любити, говорити, робити, іти

**Textbook enrichment**:
- Proverb: «Вчення — світ, а невчення — тьма» (Grade 3)

**Activities**:

1. `pattern_drill` — prompt: «читати: ТИ?» | answer: «ти читаєш» (full paradigm drill, 10 verbs)
2. `pattern_drill` — prompt: «говорити: МИ?» | answer: «ми говоримо»
3. `build_sentence` — tiles: [pronoun] + [verb form] + [object or complement]
4. `classify` — Conjugation I (читаю-type) vs Conjugation II (говорю-type) endings: sort 10 verb forms
5. `true_false` — «Вони читає» → false (3pl needs читають); «Ми говоримо» → true
6. `proverb_drill` — «Вчення — світ, а невчення — тьма.»
7. `reading` — 4-sentence passage with all pronoun forms: «Я читаю. Ти пишеш. Він говорить. Ми всі вчимо українську мову.» | true_false: «Вони вчать?» → false (ми = we, not they)

---

#### Module 11: `rechennia`
**Focus**: Building sentences — SVO anatomy, questions, negation
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: SVO sentence structure, question word order, negation (не + verb, ні)
**State standard**: §4.3.1 (simple sentences: declarative, interrogative, negative)

**Content**:

Sentence anatomy (taught with question words, not labels):
- ХТО?/ЩО? → subject (підмет) — single underline in Ukrainian school books
- ЩО РОБИТЬ? → verb (присудок) — double underline
- ЩО? / КОГО? / ДЕ? → everything else (деталі)

Statement vs question word order:
- Statement: Мама читає книгу.
- Yes/no question (intonation): Мама читає книгу? (rising intonation)
- Question word: Що мама читає? / Хто читає книгу?
- Negation: Мама не читає книгу. / Ні, мама не читає.

**Textbook enrichment**:
- Proverb: «Менше говори — більше почуєш» (Grade 3)

**Activities**:

1. `build_sentence` — 8 sentences from shuffled tiles (include statement + question variants)
2. `pattern_drill` — prompt: «Зроби запитання: Мама читає книгу.» | answer: «Що мама читає?»
3. `pattern_drill` — prompt: «Зроби заперечення: Я знаю.» | answer: «Я не знаю.»
4. `true_false` — «"Мама читає книгу" — це запитання» → false (це речення/statement)
5. `proverb_drill` — «Менше говори — більше почуєш.»
6. `reading` — 4-sentence passage: «Це Олена. Вона читає книгу. Хто читає? Олена читає. Що вона читає? Книгу.» | comprehension questions

---

#### Module 12: `spoluchnyky` 🆕
**Focus**: Connectors and compound sentences — і/й, а, але, тому що, бо, Чи-questions
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Connectors і/а/але/тому що/бо, Чи-questions, compound sentences
**State standard**: §4.3.1 (Чи-questions), §4.3.2 (complex sentences: і/й, але, тому що, бо)

**Content**:

**Connectors**:
- і / й — and (і before consonant, й after vowel: мама і тато, кіт й пес — preview of Module 43 euphony)
- а — but/and (contrast): Кіт спить, а пес грає.
- але — but (stronger contrast): Вона хоче спати, але не може.
- **тому що** — because (formal): Він не гуляє, тому що холодно.
- **бо** — because (informal): Ми не гуляємо, бо йде дощ.

**Чи-questions** (formal yes/no):
- Чи студент читає? Чи це наш автобус?
- Answer: Так, студент читає. / Ні, студент не читає.

**Textbook enrichment**:
- Proverb: «Чим темніша ніч, тим ясніші зорі» (Grade 3 — contrastive, perfect for але/а)

**Activities**:

1. `pattern_drill` — prompt: «Зроби Чи-запитання: Студент читає.» | answer: «Чи студент читає?»
2. `build_sentence` — combine two clauses with connector: «Я хочу гуляти» + «йде дощ» + [але/бо/тому що] → «Я хочу гуляти, але йде дощ.»
3. `classify` — sort 10 connectors by function: додавання (і/й) vs протиставлення (а/але) vs причина (бо/тому що)
4. `pattern_drill` — choose correct connector: «Мама працює, ___ тато відпочиває.» → а
5. `proverb_drill` — «Чим темніша ніч, тим ясніші зорі.»
6. `reading` — 5-sentence passage with all connectors: «Це Максим. Він читає книгу, бо він любить читати. Поряд є кішка, але вона не читає — вона спить. Максим читає, а кішка спить, тому що вона втомилася.»

---

#### Module 13: `zapytuyu`
**Focus**: Questions and negation — full question system
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: All question words (хто? що? де? коли? як? скільки? чому? який? **звідки? куди?**), не/ні
**State standard**: §4.3.1 (questions, negation)

**Complete question word system**:

| Question word | What it asks | Example |
|---|---|---|
| Хто? | person/animal | Хто це? — Це мама. |
| Що? | object/concept | Що це? — Це книга. |
| Де? | location | Де кішка? — Тут. |
| **Звідки?** | origin | Звідки ти? — Я з України. |
| **Куди?** | direction | Куди ти йдеш? — В школу. |
| Коли? | time | Коли ти читаєш? — Вранці. |
| Як? | manner / how | Як справи? — Добре. |
| Скільки? | quantity | Скільки книг? — Три. |
| Чому? | reason | Чому ти не спиш? — Бо я читаю. |
| Який?/Яка?/Яке? | description | Який кіт? — Чорний. |

**Negation system**:
- не — negates verbs: Я не знаю. / Він не читає.
- ні — short negative answer: Ти читаєш? — Ні, не читаю.
- ніхто — nobody: Тут ніхто не сидить.
- ніщо — nothing: Нічого не сталося. (preview — teach formally at A2)

**Spatial adverbs** (pairs with question words):
- Де? → тут, там, далеко, близько, праворуч, ліворуч, прямо
- Звідки? → звідти, з міста, з дому
- Куди? → туди, в місто, додому

**Activities**:

1. `build_sentence` — make a question from statement tiles: [Де? / Коли? / Як? / Звідки? / Куди?] + [verb phrase]
2. `pattern_drill` — prompt: «Зроби запитання до слова: Мама читає ВРАНЦІ» | answer: «Коли читає мама?»
3. `true_false` — «Де? запитує про час» → false (де запитує про місце)
4. `classify` — sort question words: ХТО?/ЩО? (предмет) vs ДЕ? (місце) vs КОЛИ? (час) vs ЗВІДКИ? (походження) vs КУДИ? (напрямок) vs ЯК? (спосіб) vs СКІЛЬКИ? (кількість)
5. `proverb_drill` — «Вчення — світ, а невчення — тьма.»
   - type: true_false about meaning
   - items: [«Навчання освітлює шлях» → true, «Краще не вчитися» → false]
6. `reading` — short interview dialogue (A asks questions, B answers): 6 exchanges covering all question words including Звідки? and Куди?

---

#### Module 14: `chysla`
**Focus**: Numbers 1–100, time expressions, quantities
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Cardinals in nominative only; genitive plural as fixed phrases
**State standard**: §4.2.1.3 (cardinal numerals)

**Number vocabulary**:
- 1–20: один, два, три, чотири, п'ять, шість, сім, вісім, дев'ять, десять, одинадцять... двадцять
- Tens: тридцять, сорок, п'ятдесят, шістдесят, сімдесят, вісімдесят, дев'яносто, сто
- Compounds: двадцять один, тридцять два...

Agreement note (teach as fixed phrases, not rules):
- один/одна + nominative singular: один кіт, одна книга
- два/дві, три, чотири + nominative plural: два коти, три книги (uses plurals from module 9!)
- п'ять–двадцять + genitive plural: п'ять книг, десять котів — teach as «magic formula», not full genitive case

Fixed phrases (memorize as chunks):
- Мені 20 років. (20 years old — connects to module 6 self-intro)
- Зараз дев'ята година. (It's 9 o'clock)
- Тут є три кішки.

**Activities**:

1. `classify` — sort numbers into groups: одиниці (1–9), десятки (10–19, 20, 30...), сотні (100+)
2. `pattern_drill` — counting sequences: «один, два, три...» + reverse «десять, дев'ять...»
3. `pattern_drill` — prompt: «Скільки? (3 кішки)» | answer: «Три кішки»
4. `build_sentence` — «Скільки книг на столі?» — use image with 1–10 items
5. `true_false` — «Два + один = чотири» → false (= три)
6. `riddle` — number riddle:
   - clues: ["Я не великий і не малий. / Я між сімома і дев'ятьма."]
   - answer: ВІСІМ
   - answer_emoji: 8️⃣

---

#### Module 15: `podobається` 🆕
**Focus**: Expressing preferences — likes, dislikes, wants
**Type**: `communicative` + `grammar`
**Status**: 🔲 Not built
**Grammar**: Мені подобається / не подобається, Я люблю / не люблю, Я хочу
**State standard**: Catalogue A #13 (express likes/dislikes)

**Core patterns**:

| Pattern | Example | Note |
|---|---|---|
| Мені подобається + noun (nom) | Мені подобається музика. | Impersonal: "To me it pleases" |
| Мені подобається + infinitive | Мені подобається читати. | "I like to read" |
| Мені не подобається | Мені не подобається дощ. | Negation |
| Я люблю + noun (acc) | Я люблю книги. | "I love" — more personal |
| Я не люблю | Я не люблю каву. | |
| Я хочу + infinitive | Я хочу читати. | "I want to" |
| Я хочу + noun (acc) | Я хочу каву. | "I want" a thing |

**The подобається construction**: Teach as a fixed pattern. «Мені» is dative but DON'T teach dative — just memorize: Мені/Тобі/Йому/Їй/Нам/Вам/Їм подобається.

| Person | Form |
|---|---|
| Мені | I like |
| Тобі | You like |
| Йому | He likes |
| Їй | She likes |
| Нам | We like |
| Вам | You (pl/formal) like |
| Їм | They like |

**Vocabulary** (interests/hobbies preview):
музика, спорт, кіно, книги, футбол, плавання, малювання, танці, подорожі, готування

**Textbook enrichment**:
- Riddle ЗНАННЯ (Grade 3 p.98): «На базарі їх не купиш, у крамниці не знайдеш»

**Activities**:

1. `pattern_drill` — «ти + подобається + музика» → «Тобі подобається музика»
2. `classify` — sort 12 phrases: подобається (✓) vs не подобається (✗)
3. `build_sentence` — express preferences: tiles for «Мені / Тобі / Їй» + «подобається / не подобається» + «[topic]»
4. `true_false` — «"Мені подобається" = "Я не люблю"» → false
5. `pattern_drill` — contrast: подобається vs люблю vs хочу: «Мені подобається читати. Я люблю книги. Я хочу нову книгу.»
6. `riddle` — «На базарі їх не купиш, у крамниці не знайдеш» → знання (source: Grade 3 p.98)
7. `reading` — dialogue about hobbies: «Що тобі подобається? — Мені подобається музика і спорт. А тобі? — Я люблю кіно. Мені не подобається спорт.» | question: Що подобається другові?

---

#### Module 16: `zovnishnist` 🆕
**Focus**: Describing people — appearance, physical features
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Adjective + noun (nominative), review of gender agreement
**State standard**: Catalogue B #1 (людина: зовнішність)

**Vocabulary** (20 appearance words):

| Category | Words |
|---|---|
| Height | високий/висока, низький/низька, середнього зросту |
| Build | худий/худа, повний/повна, спортивний/спортивна |
| Hair | довге волосся, коротке волосся, темноволосий/а, світловолосий/а, рудий/руда, кучерявий/кучерява |
| Eyes | карі очі, блакитні очі, зелені очі, сірі очі |
| Age | молодий/молода, старий/стара, дорослий/доросла |
| General | гарний/гарна, красивий/красива, симпатичний/симпатична |

**Description pattern**: Він/Вона + [adjective matching gender]. Волосся + [neuter adj]. Очі + [plural adj].

**Example descriptions**:
- Це Олена. Вона висока. Олена має довге темне волосся і карі очі. Вона молода і гарна.
- Це Назар. Він середнього зросту. У нього коротке світле волосся і блакитні очі.

**Activities**:

1. `classify` — sort 15 adjectives: зріст (height) vs будова тіла (build) vs волосся (hair) vs очі (eyes)
2. `pattern_drill` — prompt: «Олена (високий)» | answer: «Олена висока» (gender agreement)
3. `build_sentence` — describe a person from an image: «Він/Вона + [зріст] + [волосся] + [очі]»
4. `true_false` — «Людина з довгим волоссям завжди жіночої статі» → false
5. `reading` — "wanted poster" style descriptions: 3 short people descriptions, match to image
6. `pattern_drill` — asking about appearance: «Який він? — Він високий і темноволосий.»

---

### Checkpoint 1 (Module 17) 🆕

#### Module 17: `checkpoint-1`
**Focus**: Review and assessment of modules 4–16
**Type**: `checkpoint`
**Status**: 🔲 Not built
**State standard**: All §§ covered in modules 4–16

**Assessment scope**:

| Skill | What's tested | Source modules |
|---|---|---|
| Greetings/politeness | Correct phrase for situation | 4 |
| Self-introduction | Name, nationality, profession | 6 |
| Vocabulary | Recognition of ~120 taught words | 5–9, 13–15 |
| Gender | ЯКИЙ?/ЯКА?/ЯКЕ? agreement | 8 |
| Plurals | Singular → plural, vowel alternation | 9 |
| Conjugation | Both patterns, all persons | 10 |
| Sentence building | SVO, questions, negation, connectors | 11–12 |
| Numbers | 1–100, counting, Скільки? | 13 |
| Preferences | Подобається / люблю / хочу | 14 |
| Appearance | Describing people | 15 |

**Structure**: Mixed activities — `true_false` × 10, `pattern_drill` × 6, `build_sentence` × 4, `reading` × 2, `classify` × 2

**Pass threshold**: 70% overall.

---

### Phase 3: Accusative (Modules 18–20)
*Goal: learner says what they do/want/see — direct object.*

---

#### Module 18: `znavidminnyk-i`
**Focus**: Accusative — inanimate objects (ЩО?)
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Accusative inanimate
**State standard**: §4.2.3.2 (accusative)

**The key question**: When something IS the object of an action (verb acts ON it), the noun changes form.
Taught as: ЩО? (asking about a subject) → ЩО БАЧИТЬ? / ЩО ЧИТАЄ? (asking about object)

**Accusative patterns for inanimate nouns**:

| Gender | Nominative | Accusative | Pattern |
|---|---|---|---|
| Feminine -а | книга | книгу | -а → -у |
| Feminine -я | земля | землю | -я → -ю |
| Masculine inanimate | стіл | стіл | no change |
| Neuter | вікно | вікно | no change |

**Key verbs that govern accusative**: читати, писати, мати, любити, бачити, купувати, їсти, пити, хотіти, знати, розуміти

**Example sentences**:
- Я читаю кни**гу**.
- Вона має сумк**у**.
- Ми їмо піц**у**.

**Activities**:

1. `pattern_drill` — prompt: «книга → (я читаю...)» | answer: «книгу» (15 feminine nouns → accusative)
2. `build_sentence` — «Я читаю [книга/книгу]» — choose correct form
3. `true_false` — «Я люблю мамо» → false (should be маму)
4. `classify` — changes form (fem) vs stays same (masc inanimate / neuter)
5. `riddle` (**Grade 3 p.76**):
   - clues: ["Влітку медом ласував, / По малину в ліс ходив. / А як впав глибокий сніг, / Позіхнув і спати ліг."]
   - answer: ВЕДМІДЬ
   - answer_emoji: 🐻
6. `reading` — 5-sentence shopping scene: «Тарас іде в магазин. Він хоче купити хліб і молоко. Він бачить гарну книгу. Тарас купує книгу і хліб.» | question: Що купує Тарас?

---

#### Module 19: `znavidminnyk-ii`
**Focus**: Accusative — animate (КОГО?)
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Accusative animate (masculine -а/-я)
**State standard**: §4.2.3.2 (accusative animate)

**The animate distinction**: When the direct object is a person or animal, masculine nouns also change.

| | Nominative (ХТО?) | Accusative (КОГО?) |
|---|---|---|
| Masculine animate | брат | брата |
| Masculine animate | друг | друга |
| Masculine animate | кіт | кота |
| Masculine animate | лікар | лікаря |
| Feminine animate | мама | маму (same as inanimate fem) |

**Example sentences**:
- Я бачу мам**у**. / Я люблю тат**а**.
- Я чекаю друг**а**.
- Ти знаєш лікар**я**?

**Activities**:

1. `pattern_drill` — prompt: «брат → (я бачу...)» | answer: «брата» (12 animate masc nouns)
2. `classify` — inanimate acc (no change for masc) vs animate acc (changes)
3. `build_sentence` — Я люблю [мама/маму/кіт/кота/стіл/стіл]
4. `true_false` — «Я чекаю друг» → false (animate: друга)
5. `pattern_drill` — contrast drill: «стіл» (no change: стіл) vs «кіт» (animate: кота)
6. `proverb_drill` — «Без сім'ї нема щастя на землі.»
   - type: fill_gap
   - gap_word: сім'ї
   - options: [«сім'ї», «землі», «щастя», «нема»]

---

#### Module 20: `znavidminnyk-priymennyky` 🆕
**Focus**: Accusative with prepositions — direction, time, topic
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Accusative with в/у, на, за, через, про; days of week in accusative
**State standard**: §4.2.3.2.2 (acc with prepositions: в/у, на for direction; у(в) for days; про with думати/мріяти)

**Preposition patterns**:

| Preposition | Use | Example |
|---|---|---|
| в / у + acc | direction (going to) | Я іду **в школу**. Степан заходить **у кімнату**. |
| на + acc | direction (onto/to event) | Я кладу книжку **на стіл**. Іду **на зупинку**. |
| у (в) + acc | days of the week | **У понеділок** я працюю. **В середу** буде сонце. **У суботу** офіс не працює. |
| про + acc | about (with думати, мріяти) | Думати **про відпочинок**. Мріяти **про вечірку**. |
| за + acc | for / during | Дякую **за допомогу**. **За годину** я прийду. |
| через + acc | because of / across | **Через дощ** ми не гуляємо. Іти **через парк**. |

**Days of the week** (taught here, consolidating with module 13 numbers):
понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя

**Key contrast**: Direction (КУДИ? + accusative) vs Position (ДЕ? + locative, taught in module 20)
- КУДИ? Я іду **в школу**. (accusative)
- ДЕ? Я **в школі**. (locative — next phase)

**Activities**:

1. `pattern_drill` — direction: «школа → я іду в...» → «в школу» (12 places)
2. `classify` — sort prepositions: в/у (direction) vs на (surface/event) vs про (about) vs за (for) vs через (because)
3. `build_sentence` — weekly schedule: «У понеділок я працюю. У вівторок я відпочиваю...»
4. `true_false` — «Я думаю за книгу» → false (should be: про книгу)
5. `pattern_drill` — reason: «Чому ти не гуляєш?» → «Через дощ я не гуляю.»
6. `reading` — week plan passage: «У понеділок Оля іде в школу. У середу вона йде на тренування. У п'ятницю вона мріє про вихідні. У суботу вона піде в парк.» | questions: Коли Оля іде в школу? Про що мріє Оля?

---

### Phase 4: Location (Modules 21–23)
*Goal: learner says where things are.*

---

#### Module 21: `mistse`
**Focus**: Locative case — where things are (ДЕ?)
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Locative singular with в/у, на
**State standard**: §4.2.3.3 (locative)

**The locative** answers ДЕ? after prepositions в/у (inside) and на (on/at).

| Gender | Nominative | Locative | Pattern |
|---|---|---|---|
| Masc ending in consonant | стіл | на столі | + -і |
| Masc ending in -к | парк | у парку | -к → -ку |
| Fem -а | кімната | у кімнаті | -а → -і |
| Fem -я | земля | на землі | -я → -і |
| Neuter -о | місто | у місті | -о → -і |
| Neuter -е | місце | на місці | -е → -і |

**Preposition choice** в/у vs на:
- в/у: enclosed spaces (у кімнаті, в місті, у школі, у лісі)
- на: surfaces, open spaces, events (на столі, на вулиці, на зупинці, на святі)
- Teach as vocabulary — don't give rules, give examples and let pattern emerge

**Locative for TIME** (months):
- у + місяць (locative): **у січні**, **у лютому**, **у березні**, **у квітні**, **у травні**, **у червні**, **у липні**, **у серпні**, **у вересні**, **у жовтні**, **у листопаді**, **у грудні**
- Коли? — У травні. Марія народилася у травні.

**Key contrast** (connecting to module 19):
- Direction: Я іду в школ**у**. (КУДИ? → accusative)
- Position: Я в школ**і**. (ДЕ? → locative)

**Activities**:

1. `classify` — в/у (enclosed) vs на (surface/open) — 20 location images
2. `pattern_drill` — prompt: «стіл → (книга на...)» | answer: «на столі»
3. `build_sentence` — locative sentences from image prompts
4. `true_false` — «Кіт є на лісі» → false (should be у лісі)
5. `pattern_drill` — accusative vs locative contrast: «Я іду в школу» vs «Я є в школі»
6. `pattern_drill` — months: «Коли? (травень)» → «У травні»

---

#### Module 22: `misto`
**Focus**: The city — location vocabulary + locative + **city transport**
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Locative (consolidation), direction (accusative with в/на) vs position (locative)
**State standard**: Catalogue B #3 (місто: institutions, transport, city organization)

**Vocabulary** (30 city words):

| Category | Words |
|---|---|
| Education | школа, інститут, університет |
| Culture | театр, кінотеатр, музей, бібліотека |
| Religious | церква, мечеть, синагога |
| Public | ресторан, кафе, ринок, перукарня, готель, лікарня, банк, пошта, пункт обміну валют |
| **Transport** | автобус, трамвай, тролейбус, метро, маршрутка, таксі, зупинка, квиток, станція |
| Urban space | вулиця, парк, площа, проспект |

**Transport phrases** (fixed phrases):
- Де зупинка автобуса? — Where is the bus stop?
- Один квиток, будь ласка. — One ticket, please.
- Скільки коштує квиток? — How much is a ticket?
- Мені потрібно метро. — I need the metro.

| Place | Locative (ДЕ?) | Direction (КУДИ?) |
|---|---|---|
| банк | у банку | в банк |
| ринок | на ринку | на ринок |
| магазин | у магазині | в магазин |
| аптека | в аптеці | в аптеку |
| лікарня | у лікарні | в лікарню |
| зупинка | на зупинці | на зупинку |
| університет | в університеті | в університет |

**Activities**:

1. `classify` — в/у (indoor) vs на (outdoor/platform) — city places
2. `build_sentence` — «Де ти зараз?» — choose place + correct locative form
3. `true_false` — «Книги є в бібліотека» → false (has wrong ending)
4. `pattern_drill` — position vs direction contrast: «магазин → я в [?]» vs «я іду в [?]»
5. `reading` — mini city tour: «Це Київ. У Києві є великий парк. На площі стоїть пам'ятник. У музеї є старі картини. На зупинці чекає автобус.» | 3 comprehension questions
6. `classify` — sort transport: наземний (bus, tram, trolleybus) vs підземний (metro) vs індивідуальний (taxi)

---

#### Module 23: `dim`
**Focus**: Home and rooms — locative practice in domestic context
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Locative (consolidation), possessives (мій/моя/моє/наш/наша/наше)
**State standard**: Catalogue B #2 (дім), §4.2.2 (possessive pronouns)

**Vocabulary** (22 home words):

Rooms: кімната, вітальня, кухня, спальня, ванна кімната, туалет, балкон, коридор

Furniture/objects: стіл, стілець, ліжко, шафа, диван, полиця, вікно, двері, лампа, килим, дзеркало, холодильник

Housing types: квартира, будинок (приватний будинок)

**Possessives** (nominative — other cases at A2):

| | Masc | Fem | Neut | Plural |
|---|---|---|---|---|
| my | мій | моя | моє | мої |
| your (familiar) | твій | твоя | твоє | твої |
| our | наш | наша | наше | наші |
| your (formal/pl) | ваш | ваша | ваше | ваші |
| his/her/their | його / її / їхній | його / її / їхня | його / її / їхнє | його / її / їхні |

**Activities**:

1. `classify` — sort 20 images into rooms: вітальня / кухня / спальня / ванна
2. `build_sentence` — «Де є [що]?» — place furniture in rooms using locative
3. `pattern_drill` — possessives: «стіл — МОЄ?» → false (masc → мій стіл)
4. `true_false` — «Ліжко є у вітальні» [image shows ліжко in bedroom] → false
5. `reading` — home description: «Це наш дім. У нас є три кімнати. У вітальні є великий диван і телевізор. У спальні є моє ліжко. На кухні мама готує їжу.» | questions: Скільки кімнат? Де є диван?
6. `riddle` — home object riddle:
   - clues: ["Я стою у вітальні або спальні. / У мені є сорочки і штани. / Я не холодильник, але я зберігаю речі."]
   - answer: ШАФА
   - answer_emoji: 🚪

---

### Phase 5: Pronoun & Adjective Forms (Modules 24–26) 🆕
*Goal: learner correctly uses pronoun and adjective forms in accusative/locative.*

---

#### Module 24: `mene-tobi` 🆕
**Focus**: Personal pronoun declension — oblique case forms
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Personal pronouns in accusative and dative-like forms (as fixed phrases)
**State standard**: §4.2.1.4 (personal pronoun declension: я→мене/мені, ти→тебе/тобі, ми→нас/нам, ви→вас/вам)

**Pronoun forms** (State Standard explicitly requires these):

| Nominative | Accusative (КОГО?) | Dative-like (КОМУ? — as fixed phrases) |
|---|---|---|
| я | мене | мені |
| ти | тебе | тобі |
| він | його (нього) | йому |
| вона | її (неї) | їй |
| ми | нас | нам |
| ви | вас | вам |
| вони | їх (них) | їм |

**Note**: The Standard lists мене/мені, тебе/тобі, нас/нам, вас/вам explicitly for A1. We teach the full set, but the him/her/them forms are taught as recognition vocabulary (not active production).

**Usage patterns** (teach through sentences, not paradigm tables):
- Accusative: Він бачить **мене**. Я чекаю **тебе**. Вони знають **нас**.
- Dative-like: Дайте **мені** воду. Я скажу **тобі**. Це подобається **нам**.
- After prepositions: для **мене**, про **нас**, з **нами** (instrumental preview as fixed phrase only)

**Connecting to module 15**: Мені подобається / Тобі подобається — now the learner understands WHY it's «мені» not «я».

**Textbook enrichment**:
- Riddle ОБЛИЧЧЯ (Grade 3 p.141): «Густий ліс, чисте поле, два дзеркальця, кривий жолоб, два самограйки»

**Activities**:

1. `pattern_drill` — «я → (він бачить...)» → «мене» (all 7 pronouns)
2. `pattern_drill` — «ти → (я скажу...)» → «тобі» (dative forms)
3. `build_sentence` — replace noun with pronoun: «Він бачить маму» → «Він бачить її»
4. `true_false` — «Він бачить я» → false (should be: мене)
5. `classify` — sort pronoun forms: ХТО? (nominative) vs КОГО? (accusative) vs КОМУ? (dative)
6. `riddle` — «Густий ліс, чисте поле, два дзеркальця, кривий жолоб, два самограйки» → обличчя (source: Grade 3 p.141)
7. `reading` — short story using pronoun forms: «Мама любить мене. Я люблю її. Тато дає нам подарунки. Ми дякуємо йому.» | questions: Кого любить мама? Кому вони дякують?

---

#### Module 25: `tsej-toj` 🆕
**Focus**: Demonstrative pronouns — цей/ця/це, той/та/те + plurals
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Demonstrative pronoun gender/number forms
**State standard**: §4.2.2 (demonstrative pronouns: цей/ця/це, той/та/те, ці/ті)

**Demonstrative paradigm**:

| | Masc | Fem | Neut | Plural |
|---|---|---|---|---|
| this | цей | ця | це | ці |
| that | той | та | те | ті |

**Usage**:
- Цей стіл великий. (This table is big — masc)
- Ця книга нова. (This book is new — fem)
- Це вікно відчинене. (This window is open — neut)
- Ці люди працюють. (These people work — plural)
- Той будинок старий. (That building is old)
- Ті книги на полиці. (Those books are on the shelf)

**Key contrast**: Цей (close, this) vs Той (distant, that) — taught through spatial comparison.

**Connecting possessives** (review from module 23): мій/моя/моє/мої, твій/твоя/твоє/твої, наш/наша/наше/наші — plurals now explicitly practiced.

**Textbook enrichment**:
- Proverb: «Кожному мила своя сторона» (Grade 3)

**Activities**:

1. `pattern_drill` — gender match: «стіл (цей/ця/це?)» → «цей стіл» (15 nouns)
2. `classify` — sort 20 noun phrases: цей/ця/це (singular) vs ці (plural)
3. `build_sentence` — «[цей/ця/це/ці] + [noun] + [adjective]» — triple agreement
4. `true_false` — «Це книга нова» → false (should be: Ця книга нова — feminine, not neuter)
5. `pattern_drill` — close vs far: «стіл (близько)» → «цей стіл» / «(далеко)» → «той стіл»
6. `proverb_drill` — «Кожному мила своя сторона.»
7. `reading` — room description using demonstratives: «У цій кімнаті стоїть великий стіл. Цей стіл новий. На тому столі лежать книги. Ці книги старі, а ті — нові.» | comprehension questions

---

#### Module 26: `prykmetnyk-vidminky` 🆕
**Focus**: Adjective forms in accusative and locative
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Adjective declension in accusative and locative (all genders)
**State standard**: §4.2.1.2 (adjective acc/loc forms for -ий/-а/-е and -ій/-я/-є groups)

**Adjective forms** (hard group: -ий/-а/-е):

| Gender | Nom | Acc | Loc |
|---|---|---|---|
| Masc (inanimate) | великий | великий | великому |
| Masc (animate) | великий | великого | великому |
| Fem | велика | велику | великій |
| Neut | велике | велике | великому |

**Adjective forms** (soft group: -ій/-я/-є):

| Gender | Nom | Acc | Loc |
|---|---|---|---|
| Masc (inanimate) | домашній | домашній | домашньому |
| Masc (animate) | домашній | домашнього | домашньому |
| Fem | домашня | домашню | домашній |
| Neut | домашнє | домашнє | домашньому |

**Key insight for learner**: The adjective form matches both the gender AND the case of the noun.
- Nom: велик**а** книга → Acc: велик**у** книгу → Loc: у велик**ій** книзі
- Nom: нов**ий** телефон → Acc: нов**ий** телефон (inanimate = same) → Loc: у нов**ому** телефоні

**Example sentences**:
- Я читаю цікав**у** книж**ку**. (acc fem)
- Він бачить нов**ого** друг**а**. (acc masc animate)
- Ми живемо у велик**ому** міст**і**. (loc neut)
- Студент працює в нов**ій** лабораторі**ї**. (loc fem)

**Textbook enrichment**:
- Riddle КАШТАН (Grade 3 p.136): «Товстий стовбур, пишні віти, восени знайдеш під ними колючу кулю»

**Activities**:

1. `pattern_drill` — «нова книга → (я читаю...)» → «нову книгу» (10 adj+noun pairs)
2. `pattern_drill` — «великий будинок → (ми живемо в...)» → «у великому будинку»
3. `build_sentence` — full adj+noun in correct case: «Я бачу [старий/старого] [друг/друга]»
4. `true_false` — «Я живу в великий місто» → false (should be: у великому місті)
5. `classify` — sort adj forms: ХТО?/ЩО? vs КОГО?/ЩО? (accusative) vs ДЕ?/В ЧОМУ? (locative)
6. `riddle` — «Товстий стовбур, пишні віти, восени знайдеш під ними колючу кулю» → каштан (source: Grade 3 p.136)
7. `reading` — passage with mixed adjective forms: «Олена живе у великому місті. Вона працює в новій лабораторії. Вона любить свою цікаву роботу. У маленькій кімнаті стоїть старий комп'ютер.» | questions

---

### Phase 6: Time & Daily Life (Modules 27–33)
*Goal: learner describes routine, needs, feelings, leisure activities.*

---

#### Module 27: `chas`
**Focus**: Time — clock time, days, months, future tense
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Ordinal numerals in time expressions, analytical future (буду + infinitive), locative for months
**State standard**: §4.2.1.3 (ordinal numerals in time), §4.2.4.1 (future tense), §4.2.3.3 (locative for months)

**Clock time** (teach ordinals in fixed time phrases):
- Котра година? — Перша/Друга/Третя... година (1st, 2nd, 3rd... o'clock)
- О котрій? — О першій / О другій / О третій... годині (at 1, 2, 3... o'clock)

**Days of the week** (consolidation from module 19):
понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя

**Months** (taught with locative from module 20):
- січень → у січні, лютий → у лютому, березень → у березні, квітень → у квітні, травень → у травні, червень → у червні, липень → у липні, серпень → у серпні, вересень → у вересні, жовтень → у жовтні, листопад → у листопаді, грудень → у грудні

**Seasons**: зима, весна, літо, осінь → взимку, навесні, влітку, восени

**Time adverbs**: сьогодні, завтра, вчора, зараз, потім, скоро, вранці, вдень, ввечері, вночі, завжди, ніколи, іноді

**Analytical future tense** (буду + infinitive):
- буду / будеш / буде / будемо / будете / будуть + infinitive
- Завтра я **буду читати**. / Ми **будемо відпочивати**.

**Activities**:

1. `pattern_drill` — time telling: «Котра година? (3:00)» → «Третя година»
2. `pattern_drill` — future tense paradigm: «я буду читати → ти?» → «ти будеш читати»
3. `build_sentence` — schedule sentences: «Завтра о третій я буду в школі.»
4. `classify` — sort 15 time expressions: вчора (минуле) / зараз (теперішнє) / завтра (майбутнє)
5. `riddle` (**Grade 3 p.81**):
   - clues: ["Срібні дзвоники лунають, / Білим пилом замітають"]
   - answer: ЗИМА
   - answer_emoji: ❄️
6. `true_false` — «Вчора я буду грати» → false (вчора = past; буду = future)

---

#### Module 28: `den`
**Focus**: Daily routine — sequence of actions, reflexive verbs (present tense only)
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Present tense consolidation, reflexive verbs (-ся/-сь)
**State standard**: §4.2.4.1 (reflexive verbs)

**Vocabulary** (20 daily routine words — present tense forms only):

| Infinitive | Gloss | 1sg present |
|---|---|---|
| вставати | to get up | встаю |
| вмиватися | to wash up | вмиваюся |
| одягатися | to get dressed | одягаюся |
| снідати | to have breakfast | снідаю |
| іти | to go | іду |
| працювати | to work | працюю |
| обідати | to have lunch | обідаю |
| відпочивати | to rest | відпочиваю |
| вечеряти | to have dinner | вечеряю |
| лягати спати | to go to bed | лягаю спати |

**Reflexive verbs** (-ся = self / each other):
вмиватися, одягатися, сміятися, зустрічатися, дивитися

**Textbook enrichment**:
- Proverb: «Без роботи день роком стає.» (Grade 3)

**Activities**:

1. `build_sentence` — daily routine sequence (morning → evening), 8 sentences with temporal adverbs (вранці, потім, після обіду, ввечері)
2. `pattern_drill` — reflexive conjugation: «вмиватися → я» → «я вмиваюся» / «ти» → «ти вмиваєшся»
3. `classify` — sort 12 verbs: reflexive (-ся) vs non-reflexive
4. `true_false` — «Ми вмиваємося вранці» → true / «Ми снідаємося» → false (снідати — not reflexive)
5. `proverb_drill` — «Без роботи день роком стає.»
   - type: true_false
   - items: [«Без роботи час іде швидко» → false, «Без роботи день здається дуже довгим» → true]
6. `reading` — routine narration (present tense only): «Сьогодні понеділок. Я встаю о сьомій годині. Я вмиваюся і одягаюся. Потім я снідаю. О дев'ятій я іду на роботу.» | 4 comprehension questions

---

#### Module 29: `mynule` 🆕
**Focus**: Past tense — formation, gender agreement, present↔past contrast
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Past tense formation (-в/-ла/-ло/-ли), gender agreement in past tense
**State standard**: §4.2.4.1 (past tense)

**Content**:

**Past tense formation** (uses routine vocabulary from Module 28 as drill material):
- Stem + -в (masc sg): він читав, він вставав, кіт спав
- Stem + -ла (fem sg): вона читала, вона вставала, кішка спала
- Stem + -ло (neut sg): воно читало, сонце світило
- Stem + -ли (all plural): вони читали, ми вставали

**Past tense of routine verbs** (builds on Module 28):

| Infinitive | він | вона | вони |
|---|---|---|---|
| вставати | вставав | вставала | вставали |
| вмиватися | вмивався | вмивалася | вмивалися |
| снідати | снідав | снідала | снідали |
| працювати | працював | працювала | працювали |
| іти | йшов | йшла | йшли |

**Present↔past contrast**:
- Зараз я читаю. → Вчора я читав/читала.
- Зараз він працює. → Учора він працював.

**Textbook enrichment**:
- Riddle ДЕНЬ/НІЧ: «Чорна корова всіх людей поборола, / а білий віл усіх підвів» (Grade 3 p.57 — antonyms, time theme)
- Proverb: «Краще на п'ять хвилин раніше, ніж на одну пізніше» (Grade 3)

**Activities**:

1. `pattern_drill` — past tense formation: «читати → він» → «він читав» / «вона» → «вона читала» (10 verbs × 4 forms)
2. `pattern_drill` — present → past contrast: «Зараз я читаю.» → «Вчора я читав/читала.»
3. `build_sentence` — 6 past-tense sentences from shuffled tiles with temporal markers (вчора, позавчора, минулого тижня)
4. `true_false` — «Вчора Оля снідала о дев'ятій» [with story context]
5. `riddle` — «Чорна корова всіх людей поборола, а білий віл усіх підвів» → день і ніч
6. `reading` — diary entry (mixed present/past/future): «Сьогодні я встала о сьомій годині. Я вмилася і снідала. Потім я йшла до школи. Зараз я вдома і читаю книгу. Завтра я буду відпочивати.» | 4 comprehension questions

---

#### Module 30: `yizha`
**Focus**: Food vocabulary — eating, ordering, tableware
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Accusative consolidation (їсти/пити + object), imperative 2sg basics
**State standard**: Catalogue B #8 (купівля: groceries), Catalogue B #9 (ресторан: dishes, drinks, **tableware**)

**Vocabulary** (35 food + tableware items):

| Category | Words |
|---|---|
| Staples | хліб, рис, картопля, макарони, яйце |
| Meat/fish | м'ясо, курка, риба, сосиска, ковбаса |
| Dairy | молоко, сир, масло, сметана, йогурт |
| Vegetables | помідор, морква, огірок, цибуля, капуста |
| Fruit | яблуко, банан, апельсин, виноград, полуниця |
| Drinks | вода, сік, чай, кава, компот |
| Prepared | суп, борщ, піца, салат, каша |
| **Tableware** | **тарілка, чашка, виделка, ніж, ложка, склянка** |

**Taste adjectives**: смачний/а/е (tasty), солодкий (sweet), гіркий (bitter), гострий (spicy), солоний (salty), свіжий (fresh), кислий (sour)

**Imperative 2sg/2pl** (5 core polite phrases):
- Дайте, будь ласка, + accusative: Дайте, будь ласка, каву.
- Принесіть, будь ласка... (waiter/service context)
- Візьміть (take), Спробуйте (try)

**Activities**:

1. `classify` — sort 20 food images: їжа (solid food) vs напої (drinks)
2. `classify` — sort by meal: сніданок / обід / вечеря
3. `build_sentence` — «Я хочу [їжу в акузативі].» — 8 sentences
4. `true_false` — «Борщ є напій» → false (борщ — суп, не напій)
5. `reading` — café menu scene (6 exchanges): Customer orders, waiter responds. Uses: Дайте, будь ласка... / Що ви хочете? / У нас є... | comprehension: Що замовив клієнт?
6. `riddle` — food riddle:
   - clues: ["Я жовтий зовні і білий всередині. / Мене привозять з далеких країн. / Мавпи дуже мене люблять."]
   - answer: БАНАН
   - answer_emoji: 🍌

---

#### Module 31: `kupuvatysia`
**Focus**: Shopping — buying things, prices, hygiene products
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Accusative + скільки + numbers, imperative 2sg
**State standard**: Catalogue B #8 (купівля: shops, groceries, **hygiene, office supplies, weight/volume, money**)

**Vocabulary** (30 shopping words):

| Category | Words |
|---|---|
| Shops | магазин, крамниця, ринок, супермаркет, аптека, кіоск |
| Shopping actions | купувати, продавати, платити, коштувати, давати, брати, вибирати |
| Money | гривня (₴), копійка, ціна, знижка, решта (change), чек (receipt) |
| Descriptors | дорогий, дешевий, безкоштовний |
| **Hygiene** | **мило, шампунь, зубна паста, зубна щітка, рушник, туалетний папір** |
| **Office supplies** | **ручка, олівець, зошит, папір, ножиці, клей** |
| **Weight/volume** | **кілограм, грам, літр, пляшка, пакет** |
| Polite forms | дайте, скажіть, покажіть |

**Price expressions**:
- Скільки коштує? — How much does it cost?
- Це коштує 50 гривень.
- Два кілограми яблук, будь ласка.
- Одну пляшку води, будь ласка.

**Activities**:

1. `build_sentence` — price dialogues: «Скільки коштує [товар]?» / «[Товар] коштує [ціна] гривень.»
2. `pattern_drill` — imperative: «дати → ви (наказ)» → «дайте»
3. `true_false` — «Дорогий магазин — там дешеві ціни» → false
4. `classify` — категорії товарів: їжа / гігієна / канцелярія
5. `reading` — market dialogue (8 exchanges): customer and vendor. Uses: Скільки коштує...? / Дайте, будь ласка, два кілограми... / Ось ваша решта. | comprehension: Що купила людина? Скільки заплатила?
6. `proverb_drill` — «Не все те золото, що блищить.»
   - type: match_meaning
   - options: ["Золото дуже цінне", "Зовнішній вигляд не завжди відповідає цінності", "Треба купувати дороге"]
   - answer: option 2

---

#### Module 32: `zdorovia`
**Focus**: Body and health
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: У мене болить... (teach as fixed phrase), locative in context
**State standard**: Catalogue B #10 (здоров'я: body parts, well-being, illness, pharmacy)

**Vocabulary** (25 body/health words):

Body parts: голова, очі (pl), вуха (pl), ніс, рот, зуби (pl), шия, плечі (pl), рука, нога, спина, живіт, серце, горло

Health words: боліти, хворіти, кашляти, чхати, температура, ліки, таблетки, лікар, аптека, рецепт

Fixed phrases:
- У мене болить голова. (I have a headache)
- У мене болять зуби. (my teeth hurt — plural: болять)
- Я хворію. (I'm sick)
- Вам треба взяти ліки. (You should take medicine)
- Викличте лікаря! (Call a doctor! — imperative)
- Мені потрібна швидка допомога! (I need an ambulance!)

**Activities**:

1. `classify` — body parts by region: голова / тулуб (torso) / руки / ноги
2. `build_sentence` — «У мене болить [частина тіла].» — 10 sentences
3. `pattern_drill` — болить (singular) vs болять (plural): «голова → болить» vs «очі → болять»
4. `true_false` — «У мене болить очі» → false (plural: болять очі)
5. `reading` — doctor's appointment dialogue (6 exchanges): Що у вас болить? / Яка у вас температура? / Вам треба взяти ці ліки. | comprehension
6. `riddle` — body riddle:
   - clues: ["Я є у кожної людини. / Без мене ти не можеш бачити. / У тебе є два — один зліва, один справа."]
   - answer: ОКО
   - answer_emoji: 👁️

---

#### Module 33: `dozvillia` 🆕
**Focus**: Leisure, hobbies, sports, sports venues
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Consolidation — подобається/люблю + leisure activities, present tense
**State standard**: Catalogue B #6 (дозвілля: hobbies, sports, sports venues), Catalogue B #5 (діяльність: working day, day off)

**Vocabulary** (25 leisure words):

| Category | Words |
|---|---|
| Hobbies | малювання, читання, музика, танці, фотографія, готування, шахи, садівництво |
| Sports | футбол, баскетбол, плавання, біг, теніс, гімнастика, велоспорт, йога |
| Venues | стадіон, спортзал, басейн, парк, спортивний майданчик |
| Work/free time | робочий день, вихідний, обідня перерва, канікули, відпустка |
| Actions | займатися (чимось), тренуватися, грати в..., кататися на... |

**Key patterns**:
- Мені подобається + infinitive: Мені подобається плавати.
- Я займаюся + instrumental (fixed phrases): Я займаюся спортом / музикою / танцями.
- Я граю в + accusative: Я граю в футбол / шахи / теніс.

**Work/life vocabulary** (Theme 5 coverage):
- Робочий день починається о дев'ятій. (The workday starts at 9.)
- Обідня перерва — з першої до другої. (Lunch break — from 1 to 2.)
- У вихідні я відпочиваю. (On weekends I rest.)

**Textbook enrichment**:
- Proverb: «Хто працює — не бідує» (Grade 3)

**Activities**:

1. `classify` — sort 20 activities: спорт vs хобі vs робота
2. `build_sentence` — «У вільний час я люблю [hobby].» — 8 sentences
3. `pattern_drill` — «футбол → я граю в...» → «Я граю в футбол.»
4. `true_false` — «Басейн — це місце для футболу» → false (для плавання)
5. `proverb_drill` — «Хто працює — не бідує.»
6. `reading` — two people describe their weekends differently: one active (sport, swimming), one relaxed (reading, music, cooking). | questions: Хто займається спортом? Що робить інша людина?
7. `pattern_drill` — work schedule: «Коли починається робочий день?» → «О дев'ятій годині.»

---

### Checkpoint 2 (Module 34) 🆕

#### Module 34: `checkpoint-2`
**Focus**: Review and assessment of modules 18–33
**Type**: `checkpoint`
**Status**: 🔲 Not built

**Assessment scope**:

| Skill | Source modules |
|---|---|
| Accusative (inanimate + animate + prepositions) | 17–19 |
| Locative (place + time/months) | 20–22 |
| Personal pronoun declension | 23 |
| Demonstrative pronouns | 24 |
| Adjective acc/loc forms | 25 |
| Future tense (буду + inf) | 26 |
| Past tense (-в/-ла/-ло/-ли) | 27 |
| Reflexive verbs | 27 |
| Food/shopping/health/leisure vocabulary | 28–31 |

**Structure**: Mixed activities — `true_false` × 10, `pattern_drill` × 8, `build_sentence` × 4, `reading` × 3, `classify` × 2

**Pass threshold**: 70% overall.

---

### Phase 7: World (Modules 35–38)
*Goal: learner describes nature, family, traditions, and can handle travel situations.*

---

#### Module 35: `pryroda`
**Focus**: Nature and weather
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Nominative + locative consolidation
**State standard**: Catalogue B #11 (природа: weather, plants, animals, natural objects)

**Vocabulary** (28 nature words):

Seasons: зима, весна, літо, осінь
Weather: сонце, дощ, сніг, вітер, хмара, грім, блискавка, туман, мороз
Nature places: ліс, річка, море, озеро, гора, поле, берег, острів
Plants/animals: дерево, квітка, трава, кущ, кіт, собака, птах, риба, метелик

Temperature vocabulary: гарячий, теплий, прохолодний, холодний, морозний
Weather verbs: іде (дощ/сніг іде), світить (сонце світить), дує (вітер дує)

Fixed weather phrases:
- Надворі холодно / тепло / гарно.
- Іде дощ. / Падає сніг.
- Зараз зима.

**Activities**:

1. `classify` — sort 20 nature images by season: зима / весна / літо / осінь
2. `build_sentence` — weather descriptions: «Зараз [сезон]. Надворі [прикметник]. [Явище].»
3. `true_false` — «Влітку іде сніг» → false (normally)
4. `pattern_drill` — weather verbs: «дощ → ЩО РОБИТЬ?» → «іде» / «сонце» → «світить»
5. `reading` — season description (2 paragraphs): «Зараз літо. Надворі тепло і сонячно. Діти грають у парку. Але ввечері іде дощ...»
6. `riddle` — season riddle:
   - clues: ["Я приходжу після зими. / Я приношу тепло і квіти. / Птахи повертаються і співають."]
   - answer: ВЕСНА
   - answer_emoji: 🌸

---

#### Module 36: `sim-ya`
**Focus**: Family, relationships, vocative, extended appearance
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Nominative, accusative, vocative (address forms)
**State standard**: Catalogue B #1 (людина: family, relatives, status), §4.2.3.4 (vocative)

**Vocabulary** (25 family + relationship words):

Nuclear: мама, тато, дитина, дочка, син, бабуся, дідусь
Siblings: брат, сестра
Extended: тітка, дядько, племінник, племінниця
Spouses: дружина, чоловік
Status: друг/подруга, колега, сусід/сусідка

**Diminutives** (teach for recognition):
| Base | Common diminutives |
|---|---|
| мама | матуся, мамочка |
| тато | татусь, татко |
| бабуся | бабусенька, бабця |
| дідусь | дідусенько |

**Vocative case** (address forms):
| Base | Vocative |
|---|---|
| мама | мамо |
| тато | тату |
| бабуся | бабусю |
| дідусь | дідусю |
| Оля | Олю |
| Іван | Іване |
| пан | пане |
| пані | пані (no change) |

**Activities**:

1. `classify` — family tree position: батьки / дідусі-бабусі / брати-сестри / інші
2. `build_sentence` — describe family: «Це моя [родич]. Її/Його звати [ім'я].»
3. `true_false` — family relationships: «Мама моєї мами — це моя тітка» → false (бабуся)
4. `pattern_drill` — vocative: «мама → звертання» → «мамо» / «тато» → «тату» / «Іван» → «Іване»
5. `proverb_drill` — «Без сім'ї нема щастя на землі.»
6. `reading` — family introduction (6 sentences): «Мене звати Назар. У мене є велика сім'я. Моя мама — вчителька. Мій тато — лікар. У мене є сестра Оля і брат Тарас. Ми живемо в Харкові.» | questions

---

#### Module 37: `sviatky`
**Focus**: Holidays, traditions, birthday, wedding, gifts
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Locative (на святі), consolidation
**State standard**: Catalogue B #12 (традиції: state/religious holidays, **birthday, wedding, gifts**)

**Vocabulary** (25 holiday/tradition words):

Major holidays: Різдво, Новий рік, Великдень, День незалежності (24 серпня), Покров, Івана Купала
Tradition words: свято, традиція, звичай, обряд, вишиванка, вінок, паска

**Birthday**: день народження, подарунок, торт, свічки, вітаю!, З днем народження!, гості, вечірка
**Wedding**: весілля, наречений, наречена, кільце, букет
**Gifts**: подарунок, дарувати, отримувати, листівка, квіти

Greeting expressions:
- Із святом! / З святом!
- З Новим роком! / Щасливого Нового року!
- З днем народження!
- Христос Воскрес! / Воістину Воскрес!
- Слава Україні!

**Activities**:

1. `classify` — sort holidays by season: зима / весна / літо / осінь
2. `build_sentence` — greeting situations: choose correct greeting for context
3. `true_false` — «День незалежності — це 24 серпня» → true
4. `classify` — holidays: державні vs релігійні vs народні
5. `reading` — birthday description: «Сьогодні день народження Олі. Їй двадцять п'ять років. Прийшли друзі і принесли подарунки. Мама спекла великий торт. Оля дуже рада!» | comprehension
6. `pattern_drill` — giving/receiving: «Що ти даруєш? — Я дарую [подарунок].» / «Що ти отримав? — Я отримав [подарунок].»

---

#### Module 38: `podorozhi` 🆕
**Focus**: Travel — station, airport, directions, world regions, sightseeing
**Type**: `vocabulary`
**Status**: 🔲 Not built
**Grammar**: Direction (КУДИ? + accusative), location (ДЕ? + locative), imperative for instructions
**State standard**: Catalogue B #7 (подорожі: station, airport, border, movement verbs, world regions, sightseeing)

**Vocabulary** (30 travel words):

| Category | Words |
|---|---|
| Transport hubs | вокзал, автовокзал, аеропорт (летовище), станція, платформа |
| Border/customs | кордон, митний контроль, паспорт, віза, митниця |
| Movement | іти, їхати, летіти, приїхати, виїхати, пересідати |
| Directions | прямо, ліворуч, праворуч, назад, через, навпроти |
| World regions | Європа, Азія, Африка, Америка, Австралія; північ, південь, захід, схід |
| Sightseeing | визначне місце, пам'ятник, екскурсія, фотографувати, карта, путівник |
| Practical | валіза, рюкзак, квиток, розклад, інформація, затримка |

**Key phrases** (fixed patterns):
- Вибачте, де вокзал? — Ідіть прямо, потім ліворуч.
- Один квиток до Львова, будь ласка.
- О котрій відходить поїзд? — О шостій годині.
- Де знаходиться зупинка автобуса?
- Мені потрібно пересісти?

**Direction instructions** (Catalogue A #16: spatial meanings, connecting to #15: prohibitions):
- Ідіть прямо. Поверніть ліворуч. Це навпроти банку.
- Не входьте! Вхід заборонено.

**Activities**:

1. `classify` — sort 15 words: транспортні вузли vs рух vs напрямки vs країнознавство
2. `build_sentence` — asking for directions: «Вибачте, де [місце]?» → «Ідіть [напрямок].»
3. `pattern_drill` — buying tickets: «До Львова, один квиток» → «Один квиток до Львова, будь ласка.»
4. `true_false` — «Аеропорт — це місце для поїздів» → false (для літаків)
5. `reading` — travel dialogue (8 exchanges): tourist at train station asks for directions, buys ticket, asks about platform. | comprehension: Куди їде турист? О котрій відходить поїзд?
6. `classify` — sort countries by world region: Європа / Азія / Африка / Америка

---

### Phase 8: Real-World Skills (Modules 39–42) 🆕
*Goal: learner handles real-world Ukrainian — commands, signs, writing.*

---

#### Module 39: `nakazy` 🆕
**Focus**: Imperative — commands, requests, polite forms
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Imperative 2sg/2pl (all 8 State Standard verbs), polite requests (будь ласка)
**State standard**: §4.2.4.2 (imperative 2sg/2pl: 8 specific verbs), Catalogue A #14 (requests)

**Imperative forms** (all 8 verbs from State Standard):

| Infinitive | 2sg | 2pl | Gloss |
|---|---|---|---|
| читати | читай | читайте | read |
| прочитати | прочитай | прочитайте | read (complete) |
| сказати | скажи | скажіть | say/tell |
| дати | дай | дайте | give |
| писати | пиши | пишіть | write |
| написати | напиши | напишіть | write (complete) |
| сідати | сідай | сідайте | sit down |
| сидіти | сиди | сидіть | stay seated |

**Polite requests** (будь ласка):
- Дайте, будь ласка, хліб.
- Скажіть, будь ласка, де вокзал?
- Прочитайте, будь ласка, цей текст.

**Textbook enrichment**:
- Proverb: «Добрій пораді ціни немає» (Grade 3)

**Activities**:

1. `pattern_drill` — form imperatives: «читати → ти» → «читай» / «ви» → «читайте» (8 verbs × 2 forms)
2. `build_sentence` — polite requests: «[verb imperative] + будь ласка + [object]» (6 items)
3. `classify` — sort 10 phrases: прохання (polite request) vs наказ (command)
4. `pattern_drill` — ти vs ви: «Скажіть, будь ласка...» (formal) vs «Скажи...» (informal)
5. `proverb_drill` — «Добрій пораді ціни немає.»
6. `reading` — classroom scene: teacher gives 6 commands using all imperative forms. Students follow or ask questions. | comprehension: Що треба зробити?

---

#### Module 40: `zaborony-dokonane` 🆕
**Focus**: Prohibitions, perfective vs imperfective contrast, perfective future preview
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Prohibitions (не + infinitive), perfective vs imperfective contrast (читай vs прочитай), perfective future preview
**State standard**: Catalogue A #15 (prohibitions), §4.2.4.1 (perfective future: зможу, скажете, прочитають)

**Prohibitions** (Catalogue A #15):
- Не курити! / Не палити! (No smoking!)
- Не входити! (Do not enter!)
- Не бігати! (No running!)
- Тихо! (Quiet!)
- Заборонено! (Forbidden!)

**Perfective vs imperfective** (key distinction):
- читай (do it — ongoing/habitual) vs прочитай (finish reading it — complete the action)
- пиши (write — process) vs напиши (write and finish — result)
- сідай (sit down — start) vs сиди (stay seated — state)

**Perfective future** (preview — 3 forms from Standard):
- зможу (I will be able to) — from могти
- скажете (you will tell) — from сказати
- прочитають (they will read through) — from прочитати

**НЕ з дієсловами** (Grade 3 pp.154–157): НЕ always written separately from verbs.

**Textbook enrichment**:
- Proverb: «Не все те золото, що блищить» (prohibition/negation theme)

**Activities**:

1. `classify` — sort 12 phrases: наказ (command) vs заборона (prohibition) vs прохання (request)
2. `true_false` — «"Прочитай" і "читай" — це одне й те саме» → false (perfective vs imperfective)
3. `pattern_drill` — perfective future: «могти → я (майбутнє)» → «зможу» / «сказати → ви» → «скажете»
4. `pattern_drill` — choose правильно: «___ цю книгу до завтра» → прочитай (complete) vs читай (ongoing)
5. `proverb_drill` — «Не все те золото, що блищить.»
6. `reading` — signs and rules passage: «У школі є правила. Не бігати! Не кричати! Сидіть тихо. Прочитайте розклад. Скажіть «Добрий день» учителю.» | comprehension: Що заборонено в школі?

---

#### Module 41: `znaky-ta-napysy` 🆕
**Focus**: Signs, real-world reading — schedules, tickets, receipts, forms, menus
**Type**: `reading`
**Status**: 🔲 Not built
**Grammar**: Consolidation — reading comprehension of authentic text types
**State standard**: §1.2 (reading: signs, schedules, forms, tickets, menus, SMS, postcards, email)

**Text types covered**:

1. **Signs and notices**: Не курити! Не палити! Увага! Відчинено! Зачинено! Вхід. Вихід. Розклад руху поїздів. Обережно! Небезпечно!
2. **Schedule** (розклад): Train/bus departure times — read time, destination, platform
3. **Ticket** (квиток): From/to, date, time, seat number, price
4. **Receipt** (чек): Items, prices, total
5. **Menu** (меню): Categories (перші страви, другі страви, напої, десерти), items, prices
6. **Form** (анкета): Fields — ім'я, прізвище, дата народження, країна, адреса, телефон, email, підпис

**Vocabulary** (15 sign/form words):
відчинено, зачинено, вхід, вихід, увага, небезпечно, заборонено, безкоштовно, розклад, прізвище, адреса, підпис, номер телефону, електронна пошта, громадянство

**Textbook enrichment**:
- Riddle ПАЛЬЦІ (Grade 3 p.141): «У двох матерів по п'ять синків, одне ім'я всім»

**Activities**:

1. `reading` — image of 5 Ukrainian signs: match each sign to its meaning
2. `reading` — train schedule image: «О котрій відходить поїзд до Одеси?» → find in table
3. `reading` — receipt: «Скільки коштує хліб? Скільки всього?» → find in receipt
4. `reading` — restaurant menu: «Скільки коштує борщ? Які напої є?» → find in menu
5. `pattern_drill` — form filling: given information (name, country, etc.) → write in correct field
6. `true_false` — «"Зачинено" означає, що магазин працює» → false (зачинено = closed)
7. `riddle` — «У двох матерів по п'ять синків, одне ім'я всім» → пальці (source: Grade 3 p.141)

---

#### Module 42: `lystuvannia` 🆕
**Focus**: Writing practice — postcards, SMS, self-description, forms, envelope
**Type**: `writing`
**Status**: 🔲 Not built
**Grammar**: Consolidation — writing production using all A1 grammar
**State standard**: §1.3 (writing: name, address, nationality, postcards, SMS, forms, self-description, describe others, address envelope)

**Writing tasks** (State Standard §1.3.1.1 checklist):

1. **Self-description**: Write 5 sentences about yourself — name, nationality, country, age, profession, one hobby
2. **Describe a friend/family member**: Short phrases — Це мій друг. Його звати... Він студент. Він високий.
3. **Describe objects/rooms/weather**: Кімната велика. Стіл новий. Сьогодні холодна погода.
4. **Postcard/SMS**: Привіт з Києва! / Вітаю зі святом! / Бажаю щастя!
5. **Form (анкета)**: Fill in: ім'я, прізвище, країна, дата народження, адреса, телефон
6. **Envelope**: Адресат → Кому: Іваненко О. П., Куди: м. Київ, вул. Хрещатик, 15, кв. 3

**Address vocabulary**: місто (м.), вулиця (вул.), будинок (буд.), корпус (корп.), квартира (кв.), індекс

**Activities**:

1. `build_sentence` — write 5 sentences about yourself from prompts (name, country, age, profession, hobby)
2. `build_sentence` — write a postcard: choose correct greeting + 2 sentences + farewell
3. `pattern_drill` — form fields: given «Олена Іваненко, 25 років, Київ, вул. Шевченка 10» → place each item in correct form field
4. `build_sentence` — describe a photo: person image → 3 sentences about them
5. `true_false` — «На конверті пишуть ім'я, місто, вулицю, номер» → true
6. `reading` — sample SMS conversation between friends (6 messages): planning to meet. | question: Де вони зустрінуться? О котрій?

---

### Phase 9: Polish & Assessment (Modules 43–44)

---

#### Module 43: `eufoniia`
**Focus**: Euphony — у/в, і/й, з/із/зі alternation
**Type**: `grammar`
**Status**: 🔲 Not built
**Grammar**: Phonetic alternation rules
**State standard**: §4.1.7 (euphony devices)

**Content** (rules + patterns — Grade 3 pp.77–80):

**у/в** (preposition alternation):
- у — after consonant or pause, before consonant: Я **у** школі. / **У** кімнаті.
- в — after vowel, before consonant: Вона **в** школі. / Іди **в** парк.
- Before vowel: always в: **в** Одесі, **в** Україні

**і/й** (conjunction alternation):
- і — between consonants: брат **і** сестра
- й — after vowel: вона **й** він, школа **й** парк

**з/із/зі** (preposition alternation):
- з — before vowel or single consonant: **з** Одеси, **з** другом
- із — before consonant cluster: **із** школи
- зі — for ease: **зі** мною, **зі** столу

**Activities**:

1. `pattern_drill` — у/в choice: 10 items with consonant/vowel context
2. `pattern_drill` — і/й choice: 10 items
3. `build_sentence` — 5 sentences with all three alternation types
4. `true_false` — «Вона у Одесі» → false (before vowel: в Одесі)
5. `tongue_twister` (**Grade 3 p.81**):
   - text: «Гусак гусаці дав гарбуза, / Ґава ґавенятам — ґудзика.»
6. `reading` — passage with all alternation types: «Оля і Назар ідуть у школу. Вони вчаться в університеті й у школі. Оля із Харкова, а Назар із Львова.»

---

#### Module 44: `checkpoint-a1`
**Focus**: Final A1 comprehensive assessment — all skills, no new content
**Type**: `checkpoint`
**Status**: 🔲 Not built
**State standard**: Full A1 scope — all 4 Catalogues

**Assessment scope**:

| Skill | What's tested | Target |
|---|---|---|
| **Communicative** | Greetings, introductions, politeness, preferences | 80% |
| Vocabulary | Recognition of 400+ taught words | 70% |
| Nominative | ХТО?/ЩО? identification and use | 80% |
| Accusative | Inanimate + animate + prepositions (в/у, на, за, через, про) | 70% |
| Locative | в/у + на + locative endings + time (months) | 70% |
| Vocative | Address forms (мамо, тату, Олю, Іване, пане) | 70% |
| Present tense | All persons, both conjugations | 75% |
| Past tense | -в/-ла/-ло/-ли forms | 70% |
| Future tense | Буду + infinitive + perfective preview | 70% |
| Imperative | 2sg/2pl forms (8 verbs from Standard) | 70% |
| Pronouns | Personal (мене/мені...), possessive (мій/моя...), demonstrative (цей/ця...) | 70% |
| Adjective forms | Nominative + accusative + locative | 70% |
| Plurals | Noun + adjective plural formation | 70% |
| Question system | хто/що/де/коли/як/скільки/звідки/куди/чому/Чи | 80% |
| Connectors | і/й, а, але, тому що, бо | 70% |
| Euphony | у/в, і/й, з/із/зі | 70% |
| Reading | Real-world texts (signs, menu, form, schedule, passages) | 70% |
| Writing | Self-description, postcard, form filling | 70% |
| **Themes** | All 12 thematic areas represented | 70% |

**Structure**:
1. `true_false` × 3 sections — broad vocabulary + grammar review (10 items each)
2. `pattern_drill` × 5 — one per case/tense + imperative + pronouns
3. `build_sentence` × 3 — complex multi-clause sentences with connectors
4. `classify` × 2 — vocabulary categories
5. `reading` × 4 — passages of increasing length (2, 4, 6, 8 sentences) including one real-world text
6. `riddle` × 2 — using vocabulary from all modules
7. `proverb_drill` × 1 — consolidation

**Pass threshold**: 70% overall — each major section must reach threshold.

---

## A1 Grammar Progression Summary

| Module | Grammar introduced | State standard ref |
|---|---|---|
| 1–3 | Script only (alphabet, syllables, stress, intonation) | §4.1.1–§4.1.6, §4.1.8 |
| 4 | Communicative phrases (greetings, farewells, politeness) | Catalogue A #1–8 |
| 5 | Nominative (ХТО? ЩО?) | §4.2.3.1 |
| 6 | Self-introduction patterns (name, nationality, profession) | Catalogue A #2, B #1 |
| 7 | Present tense 3sg (ЩО РОБИТЬ?) | §4.2.4.1 |
| 8 | Adjective gender nominative (ЯКИЙ? ЯКА? ЯКЕ?) | §4.2.1.2 (nom) |
| 9 | **Plural formation** (nouns + adjectives, vowel alternation) | §4.2.1.1 (plural) |
| 10 | Personal pronouns + full conjugation I/II | §4.2.1.4 (nom), §4.2.4.1 |
| 11 | SVO sentences, questions, negation | §4.3.1 |
| 12 | **Connectors і/а/але/тому що/бо, Чи-questions** | §4.3.1, §4.3.2 |
| 13 | All question words incl. **звідки, куди** | §4.3.1 |
| 14 | Cardinal numerals (nominative) | §4.2.1.3 |
| 15 | **Подобається / люблю / хочу** (likes/dislikes) | Catalogue A #13 |
| 16 | **Appearance vocabulary** (зовнішність) | Catalogue B #1 |
| 17 | *Checkpoint 1* | — |
| **18** | **Accusative inanimate** | **§4.2.3.2** |
| 19 | Accusative animate | §4.2.3.2 |
| 20 | **Accusative with prepositions (в/у, на, за, через, про, days)** | §4.2.3.2.2 |
| **21** | **Locative (place + time/months)** | **§4.2.3.3** |
| 22 | Locative consolidation + **transport vocabulary** | §4.2.3.3, B #3 |
| 23 | Possessive pronouns (мій/твій/наш/ваш) | §4.2.2 |
| 24 | **Personal pronoun declension (мене/мені, тебе/тобі...)** | §4.2.1.4 |
| 25 | **Demonstrative pronouns (цей/ця/це, той/та/те, ці/ті)** | §4.2.2 |
| 26 | **Adjective acc/loc declension** | §4.2.1.2 (acc, loc) |
| 27 | Ordinal numerals (time), **future tense (буду + inf)**, loc for months | §4.2.1.3, §4.2.4.1 |
| 28 | Reflexive verbs (-ся), daily routine (present tense) | §4.2.4.1 |
| 29 | **Past tense (-в/-ла/-ло/-ли)**, present↔past contrast | §4.2.4.1 |
| 30–33 | Accusative + locative consolidation, vocabulary themes | B #5–6, #8–10 |
| 34 | *Checkpoint 2* | — |
| 35–37 | Nature, family, vocative, traditions | B #1, #11–12, §4.2.3.4 |
| 38 | **Travel vocabulary** | B #7 |
| 39 | **Imperative 2sg/2pl (8 verbs), polite requests** | §4.2.4.2, A #14 |
| 40 | **Prohibitions, perfective vs imperfective, perfective future** | A #15, §4.2.4.1 |
| 41 | **Real-world reading (signs, forms, menus, schedules)** | §1.2 text types |
| 42 | **Writing (postcards, SMS, forms, self-description)** | §1.3 |
| 43 | Euphony (у/в, і/й, з/із/зі) | §4.1.7 |
| 44 | *Final A1 checkpoint* | All §§ |

---

## A1 State Standard Coverage Checklist

### Catalogue A — Communicative Intentions (17/17 ✅)

| # | Intention | Module |
|---|---|---|
| 1 | Attract attention | 4 (`pryvit`) |
| 2 | Introduce self/others | 6 (`ya`) |
| 3 | Greet | 4 (`pryvit`) |
| 4 | Say goodbye | 4 (`pryvit`) |
| 5 | Thank | 4 (`pryvit`) |
| 6 | Apologize | 4 (`pryvit`) |
| 7 | Congratulate | 37 (`sviatky`) |
| 8 | Wish | 37 (`sviatky`) |
| 9 | Ask simple questions | 13 (`zapytuyu`) |
| 10 | Answer simple questions | 13 (`zapytuyu`) |
| 11 | Request information | 31 (`kupuvatysia`), 38 (`podorozhi`) |
| 12 | Confirm/deny | 11 (`rechennia`) |
| 13 | Express likes/dislikes | 15 (`podobається`) |
| 14 | Request action | 30 (`yizha`), 39 (`nakazy`) |
| 15 | Prohibit | 40 (`zaborony-dokonane`), 41 (`znaky-ta-napysy`) |
| 16 | Express spatial meanings | 21–22 (`mistse`, `misto`), 38 (`podorozhi`) |
| 17 | Express temporal concepts | 27 (`chas`), 28 (`den`) |

### Catalogue B — Thematic Catalogue (12/12 ✅)

| # | Theme | Module(s) |
|---|---|---|
| 1 | Людина | 6 (`ya`), 16 (`zovnishnist`), 36 (`sim-ya`) |
| 2 | Дім | 23 (`dim`) |
| 3 | Місто | 22 (`misto`) |
| 4 | Побут | 27 (`chas`), 28 (`den`) |
| 5 | Діяльність | 28 (`den`), 33 (`dozvillia`) |
| 6 | Дозвілля | 33 (`dozvillia`) |
| 7 | Подорожі | 38 (`podorozhi`) |
| 8 | Купівля | 31 (`kupuvatysia`) |
| 9 | Ресторан | 30 (`yizha`) |
| 10 | Здоров'я | 32 (`zdorovia`) |
| 11 | Природа | 35 (`pryroda`) |
| 12 | Традиції | 37 (`sviatky`) |

### Catalogue C — Linguistic Competence (all covered ✅)

| Requirement | Module |
|---|---|
| §4.1 Phonetics (all 8 subsections) | 1–3, 43 |
| §4.2.1.1 Noun declension (gender, plural, cases) | 5, 8, 9, 18–19, 21 |
| §4.2.1.2 Adjective declension (nom, acc, loc) | 8, 26 |
| §4.2.1.3 Ordinal numerals | 14, 27 |
| §4.2.1.4 Personal pronoun declension | 10, 24 |
| §4.2.2 Possessive/demonstrative pronouns | 23, 25 |
| §4.2.3.1 Nominative | 5 |
| §4.2.3.2 Accusative (object + prepositions) | 18–20 |
| §4.2.3.3 Locative (place + time) | 21–22, 27 |
| §4.2.3.4 Vocative | 36 |
| §4.2.4.1 Indicative (present, past, future, reflexive, perfective) | 7, 10, 27–29, 40 |
| §4.2.4.2 Imperative 2nd person (8 verbs) | 39 |
| §4.3.1 Simple sentences (declarative, Чи-questions, wh-questions, imperative, negation) | 11–13 |
| §4.3.2 Complex sentences (і/й, але, тому що, бо) | 12 |

---

## A1 Vocabulary Targets

| Phase | Modules | New words | Cumulative |
|---|---|---|---|
| Script | 1–3 | ~30 (key words only) | 30 |
| First Words | 4–9 | ~135 (greetings, nouns, verbs, adj, intro, plurals) | 165 |
| Sentences | 10–16 | ~90 (pronouns, connectors, numbers, preferences, appearance) | 255 |
| Accusative | 18–20 | ~40 (case forms, prepositions, days) | 295 |
| Location | 21–23 | ~75 (city, transport, home, possessives) | 370 |
| Pronoun/Adj Forms | 24–26 | ~25 (forms of existing words + demonstratives) | 395 |
| Daily Life | 27–33 | ~145 (time, routine, past tense, food, shopping, health, leisure) | 540 |
| World | 35–38 | ~110 (nature, family, holidays, travel) | 650 |
| Real-World Skills | 39–42 | ~35 (imperatives, prohibitions, signs, writing vocab) | 685 |
| Euphony | 43 | ~5 | 690 |

**Active production**: ~690 words
**Receptive** (through reading passages, dialogues, signs, menus): ~750+
**State Standard A1 target**: 750 words (receptive) ✅

---

## A2 — Outline (to be detailed)

A2 introduces:
- Dative case — §4.2.2.3
- Instrumental case — §4.2.2.5
- Genitive case full paradigm — §4.2.2.2
- Aspect pairs (доконаний/недоконаний) — §4.2.3.1
- Motion verbs (їхати/ходити) — §4.2.3.1
- Past tense expanded (aspect pairs: читав vs прочитав) — §4.2.4.1
- Future tense expanded (perfective future: прочитаю) — §4.2.4.1
- Expanded phonetics (consonant assimilation)
- Complex sentences expanded

A2 modules (~30): aspect-pairs, motion, genitive, dative, instrumental, city-life, travel-expanded, media, culture, relationships, work, health-expanded, environment, checkpoint-a2.

---

## Notes on Bükvар Influence

The Ukrainian Буквар (Bolshakova, 2025) influenced:
- Pre-literacy concept sequence (3 modules before any reading activities)
- Question-word grammar categories (ХТО?/ЩО?/ЩО РОБИТЬ?)
- Symbol-based activities (• = vowel, — = consonant) before letter recognition
- Image-first meaning (every word has a visual anchor)
- Правда чи неправда? activity type (directly borrowed)

The Bükvар is designed for 6-year-old L1 Ukrainian speakers learning to read. Adaptation for adult L2 learners:
- Skip L1 phonological awareness (adults already have it)
- Accelerate syllable reading (adults learn faster)
- Add vocabulary categories adults need (not children's topics)
- Maintain the image-anchored, question-word approach

## Textbook Activity Sources

All riddles, tongue twisters, and proverbs embedded in modules are sourced from:
- Болшакова (2025) Grade 1 Буквар — riddles and скоромовки
- Цепова (2025) Grade 2 — прислів'я
- Вашуленко (2020) Grade 3 Parts 1–2 — riddles (pp.76, 81), tongue twisters (p.81), прислів'я

Full index: `docs/l2-uk-direct/textbook-map.yaml`
