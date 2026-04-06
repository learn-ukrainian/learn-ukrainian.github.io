✅ Message sent to Gemini (ID: 28384) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28384...
📨 Message #28384
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-a2-a2-bridge-final
   Time: 2026-04-06T12:44:07.875305+00:00

============================================================

You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: a2, Slug: a2-bridge, Round: final

## Review Rubric (score EACH dimension 1-10, then average)

1. **Factual accuracy** — every claim must have evidence from sources. Vague or unsourced claims → deduct points.
2. **Ukrainian language quality** — check for Russianisms (кон→кін), surzhyk (шо→що), calques (приймати душ→брати душ). Even ONE Russianism = max 7/10.
3. **Decolonization** — is Ukrainian presented on its own terms? Any 'like Russian but...' framing = max 6/10.
4. **Completeness** — does it cover ALL aspects a module writer needs? Missing sections or shallow treatment → deduct.
5. **Actionable guidance** — can a writer actually USE this? Generic advice like 'teach it well' = max 5/10. Must have specific examples, sequences, exercises.

## Rules
- Score each dimension separately, then give weighted average.
- Be honest. If the article is excellent, say so. 10/10 IS possible.
- 9/10 = excellent with minor issues. 8/10 = good. 7/10 = needs work.
- Output a <fixes> block with specific changes. If the article is clean, output <fixes></fixes> (empty).
- Do NOT invent problems. Fabricated issues waste rebuild cycles.

## Fix syntax

Two formats are available:

**1. Replace existing text** (for corrections, rewording):
Use a SHORT anchor (1-2 sentences max) for the old: text. Do NOT paste massive paragraphs — they break exact matching.
```
old: short exact text to find
new: replacement text
```

**2. Insert new content** (for missing sections, added examples):
Use INSERT AFTER with a short anchor from the article, then the new text to add.
```
INSERT AFTER: short anchor text that exists in the article
NEW TEXT: the new content to insert after the anchor
```

Separate multiple fixes with `---`.

## Output format

Dimension scores:
1. Factual: X/10 — [evidence]
2. Language: X/10 — [evidence]
3. Decolonization: X/10 — [evidence]
4. Completeness: X/10 — [evidence]
5. Actionable: X/10 — [evidence]

**Overall: X/10**

<fixes>
old: exact text to find in the article
new: replacement text
---
INSERT AFTER: anchor text in article
NEW TEXT: content to add after the anchor
</fixes>

## Article to review

# Граматика A2: Ласкаво просимо до рівня А2

<!-- wiki-meta
slug: a2-bridge
domain: grammar/a2
tracks: [a2, b1]
sources: [6-klas-ukrmova-betsa-2023_s0092, 6-klas-ukrmova-avramenko-2023_s0096, 6-klas-ukrmova-golub-2023_s0073, 6-klas-ukrmova-golub-2023_s0080, 4-klas-ukrmova-zaharijchuk_s0053, 4-klas-ukrmova-zaharijchuk_s0057, 5-klas-ukrmova-litvinova-2022_s0182, 6-klas-ukrmova-avramenko-2023_s0095, 6-klas-ukrmova-avramenko-2023_s0241, 6-klas-ukrmova-zabolotnyi-2020_s0123, 8-klas-ukrmova-zabolotnyi-2025_s0001, 10-klas-ukrajinska-mova-avramenko-2018_s0115, 10-klas-ukrmova-glazova-2018_s0098, 4-klas-ukrmova-zaharijchuk_s0084, 4-klas-ukrmova-zaharijchuk_s0087, 5-klas-ukrmova-golub-2022_s0088, 5-klas-ukrmova-golub-2022_s0254, 5-klas-ukrmova-litvinova-2022_s0181, 5-klas-ukrmova-litvinova-2022_s0185, 5-klas-ukrmova-litvinova-2022_s0219, 6-klas-ukrmova-avramenko-2023_s0133, 6-klas-ukrmova-betsa-2023_s0124, 6-klas-ukrmova-betsa-2023_s0128, 6-klas-ukrmova-betsa-2023_s0143, 6-klas-ukrmova-golub-2023_s0101, 6-klas-ukrmova-golub-2023_s0142, 6-klas-ukrmova-zabolotnyi-2020_s0094, 7-klas-ukrmova-avramenko-2024_s0006, 7-klas-ukrmova-zabolotnyi-2024_s0001, 8-klas-ukrmova-avramenko-2025_s0105, 9-klas-ukrajinska-mova-voron-2017_s0199, 9-klas-ukrajinska-mova-voron-2017_s0287, 10-klas-ukrajinska-mova-avramenko-2018_s0011, 10-klas-ukrajinska-mova-avramenko-2018_s0031, 10-klas-ukrajinska-mova-avramenko-2018_s0117, 10-klas-ukrmova-glazova-2018_s0110, 10-klas-ukrmova-karaman-2018_s0016, 10-klas-ukrmova-karaman-2018_s0030]
compiled: 2026-04-06
-->

## Як це пояснюють у школі (How Schools Teach This)

The transition to A2 in the Ukrainian school system signifies a shift from recognizing grammatical categories to systematically applying them. While younger grades (4-5) introduce the seven cases (відмінки) and their questions (Source 5, 29), the middle grades (6-7) focus on mastering the declension patterns for nouns and adjectives, and understanding their function within a sentence (Source 8, 31).

The core concepts solidified at this stage are:

1.  **The Seven-Case System:** Ukrainian has seven cases: Називний, Родовий, Давальний, Знахідний, Орудний, Місцевий, and Кличний (Source 1). The Nominative (Називний) is considered the "direct" case and the initial form of a noun, while all others are "indirect" (Source 8, 29). Each case answers specific questions (`кого? чого?`, `кому? чому?`, etc.) which are used as a primary pedagogical tool (Source 3, 11).

2.  **The Vocative Case (Кличний відмінок):** This is consistently highlighted as a unique and expressive feature of the Ukrainian language. Unlike other cases, it does not have a corresponding question and is used exclusively for direct address (Source 3, 27). School curricula emphasize its correct use in both formal and informal communication (Source 30, 32).

3.  **Adjective-Noun Agreement:** The principle that an adjective's form depends entirely on the noun it modifies is central. The rule is simple: "to determine the case of an adjective, one must first find the case of the noun it depends on" (Source 15). Curricula build on this by introducing hard (`тверда група`) and soft (`м'яка група`) adjective declensions (Source 24).

4.  **Euphony (Милозвучність):** This is not treated as an optional stylistic choice but as a codified set of rules governing pronunciation and, consequently, orthography. The alternations of `у-в`, `і-й`, and `з-із-зі` are explicitly taught to avoid difficult-to-pronounce clusters of vowels or consonants (Source 12, 13, 16, 21). This is presented as a fundamental characteristic of the Ukrainian language (Source 21).

5.  **Comparative and Superlative Adjectives:** At the A2/B1 threshold, students learn to form degrees of comparison, including recognizing irregular forms like `гарний -> кращий` (Source 23).

By the end of this phase, a student is expected to decline common nouns and adjectives through all seven cases and apply euphonic rules automatically.

## Повна парадигма (Full Paradigm)

The A2 level requires mastery of noun and adjective declensions.

### Noun Declension (Відмінювання іменників)

Ukrainian nouns change their endings based on case, number, and declension class. Here is a consolidated paradigm based on examples from the sources.

| Відмінок | Питання | Однина (Singular) | Множина (Plural) |
| :--- | :--- | :--- | :--- |
| **Н.** (Nom) | хто? що? | син, річк**а**, пол**е** | син**и**, річк**и**, пол**я** |
| **Р.** (Gen) | кого? чого? | син**а**, річк**и**, пол**я** | син**ів**, річ**ок**, пол**ів** |
| **Д.** (Dat) | кому? чому? | син**ові**/**у**, річ**ці**, пол**ю** | син**ам**, річк**ам**, пол**ям** |
| **Зн.** (Acc) | кого? що? | син**а**, річк**у**, пол**е** | син**ів**, річк**и**, пол**я** |
| **Ор.** (Inst) | ким? чим? | син**ом**, річк**ою**, пол**ем** | син**ами**, річк**ами**, пол**ями** |
| **М.** (Loc) | (на) кому/чому? | (на) син**ові**/**і**, (на) річ**ці**, (на) пол**і** | (на) син**ах**, (на) річк**ах**, (на) пол**ях** |
| **Кл.** (Voc) | - | син**у**, річк**о**, пол**е** | син**и**, річк**и**, пол**я** |
*(Based on paradigms in Sources 1, 5, 8, 9, 11)*

### Adjective Declension (Відмінювання прикметників)

Adjectives agree with the noun in gender, number, and case. There are two main groups: hard stem and soft stem.

**Hard Stem Adjectives (Тверда група): `новий`**
| Відмінок | Чоловічий рід (Masc.) | Жіночий рід (Fem.) | Середній рід (Neut.) | Множина (Plural) |
| :--- | :--- | :--- | :--- | :--- |
| **Н.** | нов**ий** | нов**а** | нов**е** | нов**і** |
| **Р.** | нов**ого** | нов**ої** | нов**ого** | нов**их** |
| **Д.** | нов**ому** | нов**ій** | нов**ому** | нов**им** |
| **Зн.** | Н. or Р. | нов**у** | нов**е** | Н. or Р. |
| **Ор.** | нов**им** | нов**ою** | нов**им** | нов**ими** |
| **М.** | (на) нов**ому** / -**ім** | (у) нов**ій** | (на) нов**ому** / -**ім** | (на) нов**их** |
*(Based on `довгий` paradigm in Source 14 and `чистий` in Source 9)*

**Soft Stem Adjectives (М'яка група): `літній`**
| Відмінок | Чоловічий рід (Masc.) | Жіночий рід (Fem.) | Середній рід (Neut.) | Множина (Plural) |
| :--- | :--- | :--- | :--- | :--- |
| **Н.** | літн**ій** | літн**я** | літн**є** | літн**і** |
| **Р.** | літн**ього** | літн**ьої** | літн**ього** | літн**іх** |
| **Д.** | літн**ьому** | літн**ій** | літн**ьому** | літн**ім** |
| **Зн.** | Н. or Р. | літн**ю** | літн**є** | Н. or Р. |
| **Ор.** | літн**ім** | літн**ьою** | літн**ім** | літн**іми** |
| **М.** | (на) літн**ьому** / -**ім** | (у) літн**ій** | (на) літн**ьому** / -**ім** | (на) літн**іх** |
*(Based on classification in Source 24 and general rules)*

### Euphony Rules (Правила милозвучності)

| Rule | Use | When | Example | Source |
| :--- | :--- | :--- | :--- | :--- |
| **`у` / `в`**| `у` | Between consonants | Зустрінемось **у** школі. | 13 |
| | `в` | Between a vowel and consonant | Ольга **в** салоні. | 37 |
| | `у` | Before `в, ф, св, хв` etc. | Вона **у** вагоні. | 37 |
| **`і` / `й`** | `і` | Between consonants | Сергій **і** Надія. | 13 |
| | `й` | After a vowel, before a consonant | Діти **й** дорослі. | 18 |
| | `і` | Before `й, я, ю, є, ї` | Цікавий **і** яскравий фільм. | 18 |
| **`з` / `із` / `зі`** | `з` | Before a vowel or most consonants | **З** однокласницями. | 7 |
| | `із` | Between consonants (often for flow) | Максим **із** Семеном. | 7 |
| | `зі` | Before consonant clusters (esp. `з, с, ш, щ`) | **Зі** святом, **зі** мною. | 7, 22 |

## Частотність і пріоритети

For an A2 learner, not all forms are equally important. The curriculum should prioritize based on communicative frequency.

1.  **Core Cases (High Priority):**
    *   **Називний (Nominative):** Essential for identifying the subject. Already mastered at A1.
    *   **Знахідний (Accusative):** Essential for the direct object (`що?`). For masculine animate nouns (`кого?`), it's identical to the Genitive, a crucial pattern to master (Source 4, 11).
    *   **Родовий (Genitive):** Extremely high frequency. Used for possession (of whom/what?), negation (`немає чого?`), quantities (`багато чого?`), and after many prepositions. The `-у`/`-а` ending for masculine nouns is a key A2 challenge.
    *   **Місцевий (Locative):** The primary case for location (`де?`), always used with a preposition (Source 8).

2.  **Connective & Address Cases (Medium Priority):**
    *   **Кличний (Vocative):** While grammatically simple, its usage is a marker of fluency. Prioritize common names and forms of address: `мамо`, `друже`, `пане`, `Олю` (Source 3, 30).
    *   **Орудний (Instrumental):** The "with/by means of" case (`ким? чим?`). Essential for expressing instrumentality (`писати ручкою`) and accompaniment (`з другом`) (Source 8, 29).

3.  **The "Recipient" Case (Lower Priority for early A2):**
    *   **Давальний (Dative):** The case of the indirect object ("to/for whom/what"). While important, its functional load can initially be covered by simpler constructions. Key uses like age (`мені Х років`) are often learned as set phrases.

4.  **Adjective Agreement:** The priority is mastering agreement in the Nominative, Accusative, and Genitive cases, as they cover the vast majority of simple sentence structures (subject, object, possession).

5.  **Preposition Mapping (Crucial for A2):** Cases in A2 are rarely used in isolation; they must be taught alongside their triggering prepositions.
    *   **Genitive:** `до` (to), `з/із/зі` (from/out of), `після` (after), `біля` (near).
    *   **Accusative:** `про` (about), `через` (through/across), `в/у` + `на` (direction/into).
    *   **Locative:** `в/у` (location in), `на` (location on), `по` (along).
    *   **Instrumental:** `з/із/зі` (together with), `над` (above), `під` (under), `перед` (before).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Добрий день, Анна!` | `Добрий день, Анно!` | **Failure to use the Vocative case.** English uses the same form for subject and address. Ukrainian requires the distinct Vocative case (`Кличний відмінок`) for direct address. The rules for its endings must be learned (Source 3, 27, 30). |
| `Він був в Львові.` | `Він був у Львові.` | **Ignoring euphony (милозвучність).** A sequence of consonants like `в-в-л-в` is difficult to pronounce and violates the euphonic rules of Ukrainian. `у` is used between consonants (Source 13, 16). |
| `Я бачу *наш новий вчитель.` | `Я бачу нашого нового вчителя.` | **Failure to decline for animate Accusative.** In the Accusative case, masculine animate nouns (and the adjectives/pronouns that modify them) take the same form as the Genitive case (Source 4, 11, 14). |
| `Це книга *мій сестра.` | `Це книга моєї сестри.` | **Using Nominative for possession.** English uses `'s` or "of". Ukrainian uses the Genitive case (`кого? чого?`) to show possession. `сестра` (Nom) -> `сестри` (Gen) (Source 5, 8). |
| `Я розмовляю *з мій друг.` | `Я розмовляю з моїм другом.` | **Incorrect preposition + case combination.** The preposition `з` ("with") requires the Instrumental case (`Орудний`), not the Nominative. `друг` (Nom) -> `другом` (Inst) (Source 8). |
| `Це *більш кращий варіант.` | `Це кращий варіант.` | **Redundant comparative form.** The synthetic comparative (`кращий`) cannot be combined with the analytic comparative marker `більш`. This is a common error noted in school exercises (Source 23). |

## Деколонізаційні застереження (Decolonization Notes)

It is critical to teach Ukrainian on its own terms, not as a dialect or derivative of Russian.

1.  **The Vocative Case is Alive and Well:** The `Кличний відмінок` is a standard, fully productive case in modern Ukrainian, used in all registers from formal address (`пане Президенте`) to informal chats (`Олю`, `друже`). This contrasts sharply with modern Russian, where it is largely archaic. Presenting the Vocative as a core, vibrant feature of Ukrainian is essential (Source 3, 27, 30).
2.  **Euphony is a System, Not a Suggestion:** The principles of `милозвучність` (`у/в`, `і/й` alternation) are fundamental to the rhythm and sound of Ukrainian. They are codified rules, not stylistic suggestions. This systemic approach to avoiding consonant and vowel clusters is a defining characteristic of the language's phonology (Source 12, 13, 40).
3.  **The Sound `Ґ`:** Ukrainian has two distinct letters and sounds: `г` (a voiced glottal fricative, [ɦ]) and `ґ` (a voiced velar plosive, [ɡ]), as in `грати` (to play) vs. `ґрати` (bars). This distinction, absent in Russian, must be taught explicitly as a core part of the phonetic system (Source 40).
4.  **Consonant Mutations are Regular:** The sound changes in Dative and Locative cases (e.g., `нога` -> `нозі`, `рука` -> `руці`) are not random exceptions. They are ancient, regular, and predictable sound laws (`г/к/х` -> `з/ц/с` before `і`) inherited from Proto-Slavic and preserved in Ukrainian. They should be presented as a logical system (Source 1).
5.  **Lexical and Grammatical Purity:** Avoid Russianisms and grammatical calques. For example, `слідуючий` is not just a loanword; it is an active participle calque from Russian ("следующий") which violates Ukrainian morphological rules. Always use `наступний` or `такий`. Similarly, use `відсоток` instead of `процент`. The teaching goal is to promote standard, natural Ukrainian morphology and vocabulary (Source 36).

## Природні приклади (Natural Examples)

These examples are drawn from or inspired by the provided source texts.

**Group 1: Basic Case Usage in Sentences**
*   `Сестра допомагає мамі готувати вечерю.` (Dative, Accusative) (Inspired by Source 2)
*   `Баба з воза — кобилі легше.` (Genitive, Dative) (Source 8)
*   `Боятися вовка — у ліс не ходити.` (Genitive) (Source 8)

**Group 2: The Vocative Case in Address**
*   `Ой не шуми, луже, з дібровою дуже.` (Vocative) (Source 29)
*   `Дорогий Віталію, вітаю тебе з днем народження!` (Corrected version from Source 30)
*   `Олю, з великим задоволенням запрошую тебе...` (Vocative) (Source 2)

**Group 3: Adjective Agreement**
*   `На широкому письмовому столі лежали книги та зошити.` (Locative) (Source 26)
*   `Які широкі дунайські степи.` (Nominative Plural) (Source 2)
*   `Стелеться степом битий шлях.` (Instrumental, Nominative) (Source 2)

**Group 4: Euphony in Action**
*   `Син і донька.` (Consonant + `і` + Consonant) (Source 18)
*   `Вона йде.` (Vowel + `й` + Vowel) (Source 18)
*   `Приїхали зі Львова.` (Preposition `зі` before cluster) (Inspired by Source 22)

## Рекомендації для вправ (Activity Concepts)

The learning process should be scaffolded from recognition to production.

*   **Phase 1: Recognition and Identification (Drills)**
    *   **Case Spotting:** Provide a short text (like the story of Іван Сірко from Source 29). Ask learners to highlight all nouns in the Genitive case, or all adjectives in the Instrumental case.
    *   **Error Correction:** Give sentences with common L2 errors (from the list above) and have learners identify and correct them, 

============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18306 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum w...
1. Factual: 8/10 — The phonetic analysis of `Вона йде` incorrectly labels the `й` + `д` cluster as "й + Vowel", when `д` is clearly a consonant. Furthermore, the proverb is misquoted; the standard idiom uses the plural Genitive `Вовків боятися`, not the singular `Боятися вовка`.
2. Language: 9/10 — Very high quality, natural examples, and excellent explanations of euphony. The misquoted proverb is the only minor blemish on naturalness.
3. Decolonization: 10/10 — Outstanding. Explicitly tackles the Vocative case's vibrancy compared to Russian, addresses the letter `Ґ`, and correctly identifies `слідуючий` as a morphological calque.
4. Completeness: 8/10 — The document cuts off mid-sentence at the very end (`...identify and correct them, `), completely omitting the production phase of the activities.
5. Actionable: 8/10 — The pedagogical prioritization and typical error lists are highly actionable, but the broken, incomplete activity section severely undermines the final practical guidance.

**Overall: 8.6/10**

<fixes>
old: `Боятися вовка — у ліс не ходити.` (Genitive)
new: `Вовків боятися — в ліс не ходити.` (Genitive)
---
old: `Вона йде.` (Vowel + й + Vowel)
new: `Вона йде.` (Vowel + й + Consonant)
---
old: *   **Error Correction:** Give sentences with common L2 errors (from the list above) and have learners identify and correct them, 
new: *   **Error Correction:** Give sentences with common L2 errors (from the list above) and have learners identify and correct them, explaining the grammatical rule they violated.
*   **Phase 2: Production (Application)**
    *   **Cloze Exercises:** Fill in the blanks with the correct form of the noun or adjective in brackets.
    *   **Translation:** Translate simple sentences from English that force the use of specific cases (e.g., possession for Genitive).
    *   **Communicative Tasks:** Short dialogues where students must use the Vocative case to address each other and basic prepositions to describe their location.
</fixes>


────────────────────────────────────────
✅ Gemini finished (1998 chars)
✅ Message sent to Claude (ID: 28385)
✓ Message 28385 acknowledged
   Auto-acknowledged reply #28385 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-a2-a2-bridge-final' — skipping GH posting (review saved to orchestration/)
✓ Message 28384 acknowledged
