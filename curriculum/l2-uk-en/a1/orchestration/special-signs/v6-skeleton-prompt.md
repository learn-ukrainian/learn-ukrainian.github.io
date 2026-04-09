<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **3: Special Signs** (A1, A1.1 [Sounds, Letters, and First Contact]).

**Word target: 1200 words** of prose. Your skeleton must budget every word.

---

## Plan

<plan_content>
module: a1-003
level: A1
sequence: 3
slug: special-signs
version: '1.3'
title: Special Signs
subtitle: Ь, apostrophe, and the voice of consonants
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Understand what the soft sign (Ь) does to consonants
- Read words with apostrophe correctly (сім'я, м'ясо)
- Distinguish voiced and voiceless consonant pairs
- Pronounce the tricky Ukrainian sounds И, Г, Р
content_outline:
- section: М'який знак (The Soft Sign — Ь)
  words: 250
  points:
  - 'Ь has no sound. Its job: soften the consonant before it. Three-way distinction
    (Авраменко Grade 5 p.75, Большакова Grade 2 p.46): м''які приголосні (truly soft,
    9 pairs: Д/Д'', Т/Т'', З/З'', С/С'', Ц/Ц'', Л/Л'', Н/Н'', Р/Р'', ДЗ/ДЗ'' + Й),
    пом''якшені (partially softened: губні, шиплячі, задньоязикові — Ь never after
    these), тверді (hard). Захарійчук Grade 1 p.15 notation: hard = [–], soft = [=].'
  - 'Літвінова Grade 5 mnemonic: «ДЗіДЗьо, Де Ти З''їСи Ці ЛиНи» — exactly
    the 9 consonants Ь can soften. Common patterns: -нь (день, кінь, осінь),
    -ль (сіль, біль), -ть (мить), -зь (мазь). Practice: учитель, батько, маленький.'
- section: Апостроф (The Apostrophe)
  words: 250
  points:
  - 'Захарійчук Grade 1 p.97: Apostrophe comes after б, п, в, м, ф, р before я, ю,
    є, ї. It keeps the consonant HARD and gives the vowel its full [й] + vowel sound.'
  - 'Without apostrophe: consonant softens (пісня — Н is soft). With apostrophe: consonant
    stays hard + vowel = two sounds. сім''я [сім-йа] (family), м''ясо [м-йасо] (meat),
    п''ять [п-йать] (five), комп''ютер [комп-йутер] (computer). Reading practice:
    п''ять, дев''ять, м''який, м''яч, об''єкт. IMPORTANT: Only use apostrophe words
    where apostrophe follows the labial rule (б,п,в,м,ф,р + я,ю,є,ї). Do NOT include
    під''їзд or з''їзд — these follow the prefix rule (під-/з- + їзд) which is A2+.
    Also: тварь is a RUSSIAN form — do NOT use it. Ukrainian has тварина (animal).'
- section: Дзвінкі і глухі (Voiced and Voiceless)
  words: 250
  points:
  - 'Consonants come in voiced-voiceless pairs. Hand on throat test: vibration = voiced.
    Pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.'
  - 'Ukrainian pronounces voiced consonants clearly at word end — дуб is [дуб], мороз is
    [мороз]. Voiced consonants переважно (mostly) keep their sound. Exception: легко
    [лехко]. This is a defining feature of Ukrainian phonetics.'
  - 'Minimal pairs for ear training: балка (beam) vs палка (stick), коза (goat) vs
    коса (braid).'
- section: Вимова українських звуків (Pronouncing Ukrainian Sounds)
  words: 250
  points:
  - 'И [и] — a unique Ukrainian vowel. It is NOT the same as І [і]. Minimal pairs to hear
    the difference: бик (bull) vs бік (side), дим (smoke) vs дім (house), лист (letter/leaf)
    vs ліс (forest), кит (whale) vs кіт (cat). Practice with Anna Ohoiko''s И video.'
  - 'Г [ɦ] vs Ґ [g] — two different letters, two different sounds. Г is a voiced
    fricative (air flows through narrowed throat): гарно, гора, голова. Its voiceless
    partner is Х — say Х then add voice to get Г. Ґ is a voiced stop (full throat
    closure then release): ґанок, ґудзик. Its voiceless partner is К. Ґ is uniquely
    Ukrainian — an important part of Ukrainian phonetic identity. DO NOT call Г "soft"
    — in Ukrainian phonetics "м''який" means palatalized, which Г is not.'
  - 'Р [р] — the Ukrainian rolled/trilled Р. Practice with Anna Ohoiko''s video: рука, робота,
    ранок, риба. An imperfect Р is always understood — focus on getting comfortable, not perfect.'
- section: Підсумок — Summary
  words: 200
  points:
  - 'Self-check: What does Ь do? After which letters does apostrophe appear? Name
    3 voiced-voiceless pairs. How is Ukrainian Г different from Ґ? Read these words:
    сім''я, день, п''ять, гарно.'
vocabulary_hints:
  required:
  - сім'я (family) — apostrophe word
  - день (day) — soft sign after Н
  - сіль (salt) — soft sign after Л
  - м'ясо (meat) — apostrophe after М
  - п'ять (five) — apostrophe after П
  - гарно (nicely, beautifully) — Г [ɦ] practice
  - риба (fish) — Р and И practice
  recommended:
  - батько (father, formal) — soft sign
  - учитель (teacher) — soft sign at end
  - дев'ять (nine) — apostrophe
  - комп'ютер (computer) — apostrophe in cognate
  - м'який (soft) — apostrophe only (NO soft sign! Й is inherently soft)
activity_hints:
- type: odd-one-out
  section: "М'який знак"
  focus: 'Which consonant does NOT have a soft pair? (Ь can''t soften it)'
  items: 6
- type: fill-in
  section: "Апостроф"
  focus: 'Add the missing Ь or apostrophe: сім_я, ден_, п_ять'
  items: 6
- type: error-correction
  section: "Апостроф"
  focus: 'Find missing apostrophes in words like м''ясо, сім''я, п''ять'
  items: 6
- type: group-sort
  section: "Апостроф"
  focus: 'Sort words into: has Ь / has apostrophe / neither'
  items: 18
- type: match-up
  section: "Дзвінкі і глухі"
  focus: 'Match voiced-voiceless pairs: Б↔П, Д↔Т, Г↔Х, Ґ↔К, etc.'
  items: 8
- type: true-false
  section: "Дзвінкі і глухі"
  focus: 'Statements about voiced/voiceless rules and non-devoicing'
  items: 6
- type: quiz
  section: "Вимова українських звуків"
  focus: 'Г vs Ґ: choose the correct letter for each word'
  items: 6
connects_to:
- a1-004 (Stress and Melody)
prerequisites:
- a1-002 (Reading Ukrainian)
grammar:
- 'Soft sign (Ь) — softens preceding consonant, no sound. Only after 9 consonants:
  Д, Т, З, С, Ц, Л, Н, Р, ДЗ (mnemonic: ДЗіДЗьо, Де Ти З''їСи Ці ЛиНи)'
- 'Three-way distinction: м''які (truly soft, 9+Й), пом''якшені (partially softened
  губні/шиплячі/задньоязикові), тверді (hard)'
- 'Apostrophe — after б,п,в,м,ф,р before я,ю,є,ї (Захарійчук rule). NO prefix
  apostrophe examples (під''їзд, з''їзд) at A1.'
- 'Voiced/voiceless pairs (8): Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.
  Сонорні (В,Л,М,Н,Й,Р) are NEITHER voiced nor voiceless.'
- 'Non-devoicing: voiced consonants переважно keep sound at word end. Exception: легко [лехко].'
- 'Г [ɦ] voiced fricative (NOT "soft") vs Ґ [g] voiced stop'
register: розмовний
references:
- title: Захарійчук Grade 1 (NUS 2025), p.97
  notes: 'Apostrophe rule: after б,п,в,м,ф,р before я,ю,є,ї.'
- title: Захарійчук Grade 1 (NUS 2025), p.15
  notes: Hard [–] vs soft [=] consonant notation.
- title: Большакова Grade 1, p.45-47
  notes: Тверді і пом'якшені приголосні звуки.

</plan_content>

---

## Wiki Teaching Brief

Skim this for the key concepts, paradigms, and examples you must cover. Reference specific examples from the article that you plan to use in each paragraph.

<knowledge_packet>
# Knowledge Packet: Special Signs
**Module:** special-signs | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/special-signs.md

# Педагогіка A1: Special Signs



## Методичний підхід (Methodological Approach)

The two "special signs" in Ukrainian orthography, the **soft sign (м’який знак `ь`)** and the **apostrophe (апостроф `’`)**, are fundamental for correct pronunciation and are best taught through contrast. They perform opposite functions. Ukrainian pedagogy for native children introduces them visually and functionally, a method that is highly effective for L2 learners as well.

1.  **The Soft Sign (`ь`) as a "Softener"**: This sign has no sound of its own. Its only job is to indicate that the preceding consonant is soft (palatalized). Ukrainian textbooks introduce this concept by showing how the `ь` changes the quality of a consonant (Source 32: `5-klas-ukrmova-avramenko-2022_s0127`). For an English speaker, this is a new phonetic skill that requires focused practice on the tongue's position.

2.  **The Apostrophe (`'`) as a "Separator" or "Wall"**: The apostrophe signals a hard break. It indicates that the preceding consonant remains **hard** and the following iotated vowel (`я, ю, є, ї`) is pronounced as two distinct sounds: `[йа]`, `[йу]`, `[йе]`, `[йі]` (Source 19: `2-klas-ukrmova-bolshakova-2019-1_s0058`). Большакова's Grade 2 textbook explicitly states the apostrophe's function is to show the preceding consonant is hard and the following iotated vowel represents two sounds. This "wall" analogy is a powerful pedagogical tool.

3.  **Teaching through Minimal Pairs**: The core of the native method is contrasting words that differ only by the presence of a soft sign, an apostrophe, or neither. For example, `[р'а]` (in `зоря`) vs. `[рйа]` (in `подвір’я`) (Source 19). This forces the learner to hear and produce the phonetic difference, linking it directly to the written sign.

## Послідовність введення (Introduction Sequence)

For A1 learners, these signs should be introduced after the basic alphabet and the concept of iotated vowels (`я, ю, є, ї`) have been presented.

1.  **Step 1: Introduce the Soft Sign (`ь`)**.
    *   Start with word-final position, as it's the clearest example of its function. Use high-frequency words like `день`, `кінь`, `сіль`.
    *   Introduce the mnemonic "Де ти з’їси ці лини?" (`д, т, з, с, ц, л, н`) as the core group of consonants that can be followed by `ь` at the end of a word (Source 47: `7-klas-ukrmova-avramenko-2024_s0044`).
    *   Practice contrasting hard/soft pairs: `брат` vs. `брать` (to take), `став` vs. `ставь` (put). Even if the grammar is advanced, the phonetic contrast is the goal.

2.  **Step 2: Introduce the Apostrophe (`'`)**.
    *   Present it as the "anti-soft-sign." Its job is to *prevent* softening.
    *   Introduce the core rule: the apostrophe is written after the "lip" consonants `б, п, в, м, ф` and the consonant `р` before `я, ю, є, ї` (Source 49: `3-klas-ukrainska-mova-vashulenko-2020-1_s0088`). The mnemonic "Мавпочка Буф грає в чужі шахи" is used in later grades but the core letters `б, п, в, м, ф, р` are the A1 focus.
    *   Use simple, high-frequency words: `сім'я`, `м'ясо`, `п'ять`, `ім'я`, `комп'ютер`.
    *   Explicitly model the two-sound pronunciation: `м'я` = `[м] + [йа]`.

3.  **Step 3: Contrast `ь`, `'`, and nothing.**
    *   This is the most critical step. Use a three-column table with minimal pairs.
    | No Sign (softening vowel) | Soft Sign `ь` (soft consonant + `о`) | Apostrophe `'` (hard consonant + `й` + vowel) |
    | :--- | :--- | :--- |
    | `буряк` [р'а] | `бульйон` [л'о] | `бур'ян` [рйа] |
    | `свято` [с'в'а] | `сьогодні` [с'о] | `здоров'я` [вйа] |
    | `ряд` [р'ад] | `трьох` [р'ох] | `подвір'я` [рйа] |
    *   This direct comparison solidifies the distinct function of each orthographic rule (Source 40: `5-klas-ukrmova-uhor-2022-1_s0186`).

4.  **Step 4: Apostrophe after Prefixes.**
    *   Introduce this as a simple, logical rule. When a prefix ends in a hard consonant, an apostrophe is used before `я, ю, є, ї` to maintain the hard separation.
    *   Examples: `з'явитися`, `об'єднати`, `від'їзд` (Source 31: `3-klas-ukrainska-mova-vashulenko-2020-1_s0090`).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково (Incorrectly) | ✅ Правильно (Correctly) | Чому (Why) |
| :--- | :--- | :--- |
| Writing `сімя`, `пят`, `здоровя`. | `сім'я`, `п'ять`, `здоров'я`. | Forgetting the apostrophe. English has no equivalent concept of a "separator" sign, so learners often omit it. The apostrophe is mandatory to show the consonant is hard and the vowel is iotated (`[йа]`). (Source 49) |
| Pronouncing `м'ясо` as [`мьасо`] (soft m). | Pronouncing `м'ясо` as [`мйасо`] (hard m + ya). | The apostrophe's primary function is to signal the preceding consonant is **hard**. Learners often see the `я` and automatically soften the `м`. The apostrophe is a "wall" that prevents this. (Source 19) |
| Using `'` after other consonants, e.g., `*кать'я`. | Not using an apostrophe there. | The main apostrophe rule applies to a specific set of consonants (`б, п, в, м, ф, р`). Learners may overgeneralize the rule to other consonants. (Source 50) |
| Writing `льожка` or `тьохкає`. | `ложка` (hard л), `тьохкає` (soft т). | Confusing the soft sign (`ь`) with palatalization rules. The soft sign is not used before all vowels, and the combination `ьо` is used to represent `[ьо]`, but `ло` is simply `[ло]`. (Source 42: `6-klas-ukrmova-betsa-2023_s0032`) |
| Writing `компютер` or `інтервю`. | `комп'ютер`, `інтерв'ю`. | Forgetting the apostrophe in common loanwords. This is a very frequent error. The rule applies consistently to these words. (Source 24) |
| Treating `ь` as a silent letter like in English "debt". | Treating `ь` as a command to modify the previous consonant. | English orthography has no direct parallel. The soft sign has zero sound value itself but carries a critical instruction for the consonant before it. (Source 32) |

## Деколонізаційні застереження (Decolonization Notes)

This is a critical area where Russian influence can mislead learners. Ukrainian orthography must be taught on its own terms.

1.  **The Apostrophe is NOT a Hard Sign**: The Ukrainian apostrophe (`'`) is a unique feature. It is **not** a replacement for or equivalent to the Russian hard sign (`ъ`). The Russian hard sign also serves a separating function, but their historical development and usage rules are different. The writer must avoid any comparison, as it creates a false equivalency and frames Ukrainian as a derivative of Russian. The Ukrainian apostrophe was standardized in the early 20th century to solve a phonetic challenge using the tools available in a standard typeset, distinct from the Cyrillic-specific `ъ` (Source 22: `ext-istoria_movy-52`).

2.  **Teach Ukrainian Phonetics Natively**: Do not explain the soft sign `ь` as being "like the Russian soft sign." While functionally similar, the degree and quality of palatalization can differ. The learner's reference point must be native Ukrainian audio and phonetic descriptions, not another Slavic language.

3.  **No Russian Examples**: All example words, phrases, and texts must be Ukrainian. Using Russian examples (e.g., to show a cognate) implicitly centers Russian as the default Slavic language and should be strictly avoided.

4.  **Historical Context**: Ukrainian writers in the 19th century used various systems to represent these sounds before the modern apostrophe was standardized (Source 22). This shows a living language evolving its own writing system, not borrowing one. This context is for the writer's understanding, not necessarily for the A1 lesson itself, but it informs a decolonized approach.

## Словниковий мінімум (Vocabulary Boundaries)

### Words with Apostrophe (`'`)
*   ★★★ (Essential): `сім'я`, `м'ясо`, `п'ять`, `дев'ять`, `ім'я`, `здоров'я`, `комп'ютер`, `подвір'я`, `пам'ять`.
*   ★★ (Useful): `в'язати` (to knit), `бур'ян` (weed), `пір'я` (feathers), `черв'як` (worm), `об'єкт` (object).
*   ★ (Can wait): `торф'яний` (peat), `міжгір'я` (intermountain), `Лук'ян` (name).

### Words with Soft Sign (`ь`)
*   ★★★ (Essential): `день`, `вчитель`, `батько`, `Львів`, `кінь`, `осінь`, `сіль`, `сьогодні`, `польський`, `український`, `-ський` (in general).
*   ★★ (Useful): `лялька` (doll), `тінь` (shadow), `палець` (finger), `хлопець` (boy), `щось`, `десь`.
*   ★ (Can wait): `мільйон`, `бульйон`, `різьбяр` (carver), `женьшень` (ginseng).

## Приклади з підручників (Textbook Examples)

These exercise formats are taken directly from Ukrainian elementary school textbooks and are perfect for A1 learners.

1.  **Contrastive Choice (from Source 19)**
    *   *Мета: Навчити розрізняти м'яку вимову (`ря`) і роздільну вимову (`р'я`).*
    *   **Вправа:** Прочитай слова. Поясни, де `я` позначає один звук, а де два.
        *   `зоря` — `сузір'я`
        *   `буряк` — `бур'ян`
        *   `Різдво` — `різдв'яний`

2.  **Fill in the `ь` or `'` (from Sources 24, 47)**
    *   *Мета: Застосувати правила вживання апострофа і м'якого знака.*
    *   **Вправа:** Вставте, де потрібно, `ь` або `'`.
        *   `здоров..я`
        *   `пол..ський`
        *   `комп..ютер`
        *   `учител..`
        *   `п..ятниця`
        *   `Л..вів`
        *   `сім..я`
        *   `пал..то`

3.  **Categorization (from Source 47)**
    *   *Мета: Перевірити розуміння правил для обох знаків.*
    *   **Вправа:** Розподіліть слова на три колонки: 1) з апострофом, 2) з м'яким знаком, 3) без знаків.
    *   *Слова:* `Свято`, `Дев'ять`, `Різдво`, `Морква`, `Батько`, `Подвір'я`, `Тінь`, `П'ятниця`, `Український`, `М'яч`.

4.  **Word Puzzle / Riddle (from Source 19)**
    *   *Мета: Закріпити написання слів з апострофом у контексті.*
    *   **Вправа:** Прочитай опис і запиши слово-відгадку.
        *   "П'ятий день тижня." (Відповідь: `п'ятниця`)
        *   "Тато, мама і я — це дружна..." (Відповідь: `сім'я`)
        *   "Його їдять. Воно не риба і не овоч." (Відповідь: `м'ясо`)

## Пов'язані статті (Related Articles)
- `pedagogy/a1/iotated-vowels`
- `pedagogy/a1/consonants-hard-soft`
- `phonetics/palatalization`
- `orthography/history-of-the-apostrophe`

---

### Вікі: pedagogy/a1/this-and-that.md

# Педагогіка A1: This And That



## Методичний підхід (Methodological Approach)

The core pedagogical principle for teaching demonstratives (`цей`, `той`) in Ukrainian is to tightly integrate them with the concept of noun gender. Ukrainian elementary school textbooks do not teach these words in isolation; they are presented as a fundamental tool for identifying and reinforcing a noun's gender from the very beginning (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`).

The primary method is **substitution and association**. Learners are taught to associate a noun with a chain of gender-agreeing words. For a masculine noun like `стіл` (table), the chain is `стіл` → `він` (he) → `мій` (my) → `цей` (this) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`). This creates a powerful mental link between the noun and its grammatical gender, making adjective agreement (e.g., `цей червоний стіл`) intuitive later on.

The unchangeable pronoun `це` ("this/that is") is introduced first as a simple identifier. It is the most frequent and simplest form, used in basic sentence patterns like "**Це** + [іменник]" (e.g., "**Це** стіл," "**Це** книга."). This allows learners to start building sentences before tackling gender agreement (Джерело: `ext-video-4`, `5-klas-ukrmova-uhor-2022-1_s0081`).

Only after `цей/ця/це` are mastered as pointers for "close" objects is the "far" equivalent `той/та/те` introduced, often through direct contrastive exercises (`цю книгу чи ту книгу?` — "this book or that book?") (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`).

Finally, demonstratives are presented as a key tool for creating cohesive text by avoiding noun repetition. Textbooks show how words like `цей`, `ця`, `він`, `вона` connect sentences and make writing flow more naturally (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`). At the A1 level, the focus is purely on the nominative (subject) case. Full declension is a B1 topic (<!-- VERIFY -->).

## Послідовність введення (Introduction Sequence)

The introduction must be methodical and layered, building from the simplest concept to the more complex.

- **Step 1: The Universal Identifier `Це`**
  - **What:** Introduce the word `це` as the universal, gender-neutral way to say "This is..." or "That is...". It answers the question `Що це?` (What is this?).
  - **Why:** This is the highest frequency demonstrative and requires zero knowledge of gender. It allows learners to immediately start identifying objects. For example: `Що це? - Це стіл.` `Що це? - Це книга.` (Джерело: `ext-video-4`). It functions like "It is" in English.

- **Step 2: The Gender Pointers `Цей`, `Ця`, `Це`**
  - **What:** Introduce the three gendered forms of "this": `цей` (masculine), `ця` (feminine), and `це` (neuter). Explicitly link them to the gender pronouns `він`, `вона`, `воно` and possessives `мій`, `моя`, `моє`.
  - **Why:** This directly reinforces noun gender. The teaching pattern is: see a noun (`стіл`), recall its gender pronoun (`він`), and then select the corresponding demonstrative (`цей стіл`) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`). This builds the grammatical reflex for agreement.

- **Step 3: The Plural Pointer `Ці`**
  - **What:** Introduce the plural form `ці` ("these") for all genders.
  - **Why:** After mastering the three singular forms, the single plural form is a simple next step. It shows how gender distinctions disappear in the plural for demonstratives. Example: `ці столи`, `ці книги`, `ці вікна`. (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`).

- **Step 4: Distinguishing "This" vs. "That" (`Той`, `Та`, `Те`, `Ті`)**
  - **What:** Introduce the "far" pointers `той` (m), `та` (f), `те` (n), and `ті` (pl) to contrast with the "near" pointers (`цей`, `ця`, `це`, `ці`).
  - **Why:** This concept of proximity is familiar to English speakers ("this/that"). It should be taught with contrastive examples, physically pointing to near and far objects. For example: `Цей стілець тут, а той стілець там.` (This chair is here, and that chair is there). `Мені, будь ласка, це/те тістечко` (Source 3) is a perfect textbook example of this choice.

- **Step 5: Demonstratives for Text Cohesion**
  - **What:** Show how `цей`, `він`, `вона` etc., are used to refer back to a previously mentioned noun to avoid clumsy repetition.
  - **Why:** This moves learners from single sentences to basic text construction. It's a key feature of natural Ukrainian writing style. (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`, `4-klas-ukrmova-zaharijchuk_s0014`). For example: "Славко купив букет квітів... **Він** також узяв книжку." (Slavko bought a bouquet... **He** also took a book).

## Типові помилки L2 (Common L2 Errors)

English-speaking learners often make predictable errors when learning Ukrainian demonstratives due to interference from English grammar.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Що цей?` | `Що це?` | Learners mistakenly use the gendered `цей` for the general question "What is this?". The correct form for identification is always the neutral, unchangeable `це`. (Джерело: `ext-video-4`) |
| `Ця стіл великий.` | `Цей стіл великий.` | This is a direct gender agreement error. The learner has not yet internalized that `стіл` is masculine and requires the masculine demonstrative `цей`. This is the most common error and is why linking demonstratives to gender is so critical. (Джерело: `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`) |
| `Це стіл є новий.` | `Цей стіл новий.` or `Це новий стіл.` | Learners overuse the verb `є` (is/are), translating directly from English. In simple descriptive sentences in Ukrainian, the verb "to be" is usually omitted in the present tense. The first correct option uses the demonstrative as a pointer, while the second uses `це` as an identifier. |
| `Це столи.` | `Ці столи.` | The learner incorrectly uses the singular identifier `це` when pointing to multiple items. The correct plural demonstrative is `ці` for "these". (Джерело: `ext-ulp_youtube-261`) |
| `Мені подобається цей дівчина.` | `Мені подобається ця дівчина.` | Another gender agreement error, but with a feminine noun. The learner applies the default/masculine form `цей` to the feminine noun `дівчина`. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`) |
| `Я живу в цей будинок.` | `Я живу в цьому будинку.` | This is a case error. While full declension is not an A1 topic, learners will encounter prepositions. They often incorrectly use the nominative form (`цей`) after a preposition instead of the required locative (`цьому`). This should be taught as a fixed chunk (`в цьому будинку`) at A1, with the grammatical explanation delayed. (<!-- VERIFY -->) |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian requires a conscious effort to de-link it from Russian and establish its own phonetic and grammatical foundation in the learner's mind.

1.  **Independent Phonetics:** The sound `[ц]` must be taught as a native Ukrainian phoneme. Do not describe it as "like the Russian ц". Use examples from within Ukrainian, like `цукор` (sugar), `палець` (finger), `кінець` (end). The learner's reference point must be Ukrainian itself.

2.  **No Russian Cognates as a Crutch:** Avoid teaching `цей` by comparing it to Russian `этот` or `той` to `тот`. While they are cognates from a common Slavic root, using Russian as the bridge reinforces a colonial linguistic dependency. Teach `цей` and `той` through their function and context within Ukrainian only.

3.  **Emphasize Native Etymology:** Briefly explain that `цей` comes from an older Ukrainian form `отъ + сей` ("lo, this"), which evolved into `отсей` and then was re-analyzed as `о-цей`, eventually yielding the standalone `цей` (Джерело: `ext-istoria_movy-103`). This demonstrates a clear, internal path of development for the word within the Ukrainian language itself, countering any false narrative of it being a Russian import or derivative.

4.  **Ukrainian Sentence Structure:** Stress that the omission of "to be" (`є`) in sentences like `Цей стіл червоний` is a standard feature of Ukrainian grammar. It is not an "informal" version of a structure that "should" have a verb like in Russian (`Этот стол есть красный`). This validates Ukrainian grammar on its own terms.

5.  **Stylistic Norms:** The use of demonstratives and personal pronouns (`цей`, `він`, `вона`) to avoid repeating nouns is a characteristic of good Ukrainian style, as taught in Ukrainian schools (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `2-klas-ukrmova-bolshakova-2019-2_s0044`). It should be presented as a native stylistic device, not a calque from another language.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for A1 learners when practicing demonstratives. It focuses on concrete, point-able objects found in a classroom or home.

**Іменники (Nouns):**
- ★★★ `стіл` (table) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `стілець` (chair) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `книга` (book)
- ★★★ `ручка` (pen) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)
- ★★★ `вікно` (window) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `будинок` (house, building) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `кімната` (room) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `двері` (door - *plural only*) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `олівець` (pencil) (Джерело: `3-klas-ukrainska-mova-savchenko-2020-2_s0009`)
- ★★☆ `шафа` (wardrobe, cabinet) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `ліжко` (bed) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `поле` (field) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)

**Прикметники (Adjectives):**
- ★★★ `новий` (new) (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0065`)
- ★★★ `старий` (old) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★★ `великий` (big)
- ★★★ `малий` (small)
- ★★☆ `червоний` (red) (Джерело: `10-klas-ukrajinska-mova-avramenko-2018_s0186`)
- ★★☆ `синій` (blue) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `жовтий` (yellow) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `зелений` (green) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `гарний` (good, beautiful) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)

**Дієслова (Verbs):**
- ★★★ `бути` (to be)
- ★★★ `мати` (to have)
- ★★★ `бачити` (to see)
- ★★☆ `жити` (to live) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)
- ★★☆ `хотіти` (to want)

## Приклади з підручників (Textbook Examples)

These exercises, adapted from Ukrainian school materials, provide a gold standard for practice activities.

1.  **Gender Sorting with Demonstratives (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`)**
    - **Format:** Sorting task. Provide a list of nouns and three columns.
    - **Prompt:** "Розподіли іменники за родами. Запиши назви в потрібний рядок." (Distribute the nouns by gender. Write the names in the correct row.)
    - **Task:**
        - **Він, мій, цей:** `стіл`, `олівець`, `будинок`
        - **Вона, моя, ця:** `книга`, `ручка`, `шафа`
        - **Воно, моє, це:** `вікно`, `ліжко`, `поле`

2.  **Forced Choice: This vs. That (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`)**
    - **Format:** Multiple choice within a sentence.
    - **Prompt:** "Прочитайте речення, обираючи правильний займенник." (Read the sentences, choosing the correct pronoun.)
    - **Task:**
        - 1. Привал буде за (цією / тією) горою. (The stop will be behind *this* / *that* mountain.)
        - 2. Мені, будь ласка, (це / те) тістечко. (For me, please, *this* / *that* pastry.)
        - 3. Візьміть (цю / ту) книгу, не пошкодуєте. (Take *this* / *that* book, you won't regret it.)

3.  **Adjective and Demonstrative Agreement (Джерело: `6-klas-ukrmova-betsa-2023_s0113`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)**
    - **Format:** Fill-in-the-blanks for endings.
    - **Prompt:** "Оберіть правильний варіант закінчення." (Choose the correct ending.)
    - **Task:**
        - Який? (m): `Нов__ стіл`, `цікав__ фільм`, `цей хорош__ друг` → (`-ий`, `-ий`, `-ій`)
        - Яка? (f): `Ця нов__ сукня`, `цікав__ казка` → (`-а`, `-а`)
        - Яке? (n): `Це нов__ крісло`, `цікав__ оповідання` → (`-е`, `-е`)

4.  **Text Cohesion via Pronoun Substitution (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`)**
    - **Format:** Text rewriting.
    - **Prompt:** "Спишіть текст, уникаючи повторів виділених слів. Підкресліть слова, які зв’язують речення в тексті." (Rewrite the text, avoiding repetition of the highlighted words. Underline the words that connect the sentences in the text.)
    - **Original Text:** "Марусі... подарували маленький рожевий ноутбук. **Ноутбук** став для Марусі найкращим другом. **Ноутбук** зберігав маленькі таємниці дівчинки..."
    - **Expected Output:** "Марусі... подарували маленький рожевий ноутбук. **Він** став для Марусі найкращим другом. **Цей комп'ютер** зберігав маленькі таємниці дівчинки..."

## Пов'язані статті (Related Articles)

- `pedagogy/a1/noun-gender`
- `pedagogy/a1/adjective-agreement`
- `pedagogy/a1/personal-pronouns`
- `pedagogy/a2/introduction-to-cases`
- `grammar/nouns/pluralization`
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Output format

Output a single `<skeleton>` block. For each section from the plan's `content_outline`, list every paragraph and exercise with its word budget and content focus.

Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."

```
<skeleton>
## Section Title (~XXX words total)
- P1 (~XX words): [specific content — what concept, what examples, what comparison]
- P2 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type from activity_hints, focus, number of items]
- P3 (~XX words): [specific content]
...

## Section Title (~XXX words total)
- P1 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type, focus]
...

## Summary (~150 words)
- P1 (~150 words): [Follow the plan's points for this section EXACTLY. If the plan says "Self-check questions", output a bulleted Q&A list — NOT prose. If the plan says "recap", write a brief recap.]

Grand total: ~1200 words
</skeleton>
```

## Rules

1. **Every paragraph has ONE clear purpose.** If you can't describe it in one sentence, split it.
2. **Word budgets must sum to 1200+.** Aim for ~10% overshoot (1320 words) — writers tend to undershoot.
3. **Section budgets must match the plan's `content_outline` word allocations** (±10%).
4. **Place exercise injection markers in the correct section.** Each activity hint in the plan may have a `section:` field that tells you which section it belongs in. Place `<!-- INJECT_ACTIVITY: descriptive-id -->` AFTER the teaching content of that section, never before. Use a descriptive kebab-case id (e.g., `fill-in-genitive`, `quiz-aspect-choice`). If no `section:` is specified, place the marker after the most relevant teaching point. **CRITICAL: An exercise must ONLY test concepts already taught above it. Never test a concept from a later section. Every plan `activity_hints` entry MUST have a corresponding `<!-- INJECT_ACTIVITY: id -->` marker in the skeleton.**
5. **Name specific Ukrainian examples** you plan to use in each paragraph. This prevents vague skeletons that produce vague content.
6. **Dialogues count as paragraphs.** Budget 80-120 words per multi-turn dialogue.
7. **No meta-commentary.** Output only the `<skeleton>` block, nothing else.
