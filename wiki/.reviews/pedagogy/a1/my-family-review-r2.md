✅ Message sent to Gemini (ID: 28169) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28169...
📨 Message #28169
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-a1-my-family-r2
   Time: 2026-04-05T22:16:12.661605+00:00

============================================================

You are a HARSH adversarial reviewer of a A1 pedagogical brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: a1, Slug: my-family, Round: 2

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

# Педагогіка A1: My Family

<!-- wiki-meta
slug: my-family
domain: pedagogy/a1
tracks: [a1, a2]
sources: [5-klas-ukrmova-uhor-2022-1_s0052, 5-klas-ukrmova-uhor-2022-1_s0059, 5-klas-ukrmova-uhor-2022-1_s0234, 5-klas-ukrmova-uhor-2022-1_s0061, 11-klas-ukrajinska-mova-avramenko-2019_s0103, 2-klas-ukrmova-kravcova-2019-2_s0034, 2-klas-ukrmova-kravcova-2019-2_s0035, 7-klas-ukrmova-zabolotnyi-2024_s0269, 9-klas-ukrajinska-mova-voron-2017_s0161, 10-klas-ukrajinska-mova-avramenko-2018_s0115, 11-klas-ukrajinska-mova-avramenko-2019_s0020, 11-klas-ukrajinska-mova-voron-2019_s0349, 2-klas-ukrmova-bolshakova-2019-1_s0061, 2-klas-ukrmova-kravcova-2019-2_s0031, 4-klas-ukrmova-zaharijchuk_s0119, 5-klas-ukrmova-golub-2022_s0198, 5-klas-ukrmova-litvinova-2022_s0223, 5-klas-ukrmova-zabolotnyi-2023_s0108, 6-klas-ukrmova-golub-2023_s0247, 6-klas-ukrmova-litvinova-2023_s0259, 8-klas-ukrmova-zabolotnyi-2025_s0243, 10-klas-ukrmova-karaman-2018_s0415, 1-klas-bukvar-zaharijchuk-2025-2_s0097, 2-klas-ukrmova-bolshakova-2019-1_s0080, 2-klas-ukrmova-bolshakova-2019-1_s0090, 2-klas-ukrmova-kravcova-2019-2_s0005, 2-klas-ukrmova-kravcova-2019-2_s0028, 2-klas-ukrmova-kravcova-2019-2_s0033, 2-klas-ukrmova-kravcova-2019-2_s0082, 2-klas-ukrmova-vashulenko-2019-2_s0008, 4-klas-ukrmova-zaharijchuk_s0050, 5-klas-ukrmova-avramenko-2022_s0178, 5-klas-ukrmova-golub-2022_s0206, 5-klas-ukrmova-uhor-2022-1_s0060, 5-klas-ukrmova-uhor-2022-1_s0095, 5-klas-ukrmova-uhor-2022-1_s0099, 5-klas-ukrmova-uhor-2022-1_s0108, 6-klas-ukrmova-avramenko-2023_s0096, 6-klas-ukrmova-avramenko-2023_s0209, 6-klas-ukrmova-avramenko-2023_s0214, ext-article-0, ext-article-1, ext-article-2, ext-article-3, ext-article-4, ext-article-5, ext-article-6, ext-article-7, ext-video-8]
compiled: 2026-04-06
-->

## Методичний підхід (Methodological Approach)

The topic of "My Family" (Моя сім'я / Моя родина) is a cornerstone of A1, serving as a highly motivating and immediately practical domain for beginners. The approach in Ukrainian textbooks (e.g., Большакова, Вашуленко, Кравцова for grades 1-2) is consistently communicative, context-driven, and centered on the learner's personal experience.

1.  **Narrative and Personalization:** The core method is to start with a model and then immediately ask the learner to apply it to themselves. A text like "Сім’я Оксани" (Source 4) presents a simple family structure, their names, and p

## Instructions
1. Read the critique carefully.
2. Identify which SPECIFIC sections need rewriting to address the critique.
3. Output the COMPLETE article with those sections rewritten.
4. Do NOT remove or degrade sections that scored well.
5. Do NOT add commentary — output ONLY the article markdown.

## Current article

```markdown
# Педагогіка A1: My Family

<!-- wiki-meta
slug: my-family
domain: pedagogy/a1
tracks: [a1, a2]
sources: [5-klas-ukrmova-uhor-2022-1_s0052, 5-klas-ukrmova-uhor-2022-1_s0059, 5-klas-ukrmova-uhor-2022-1_s0234, 5-klas-ukrmova-uhor-2022-1_s0061, 11-klas-ukrajinska-mova-avramenko-2019_s0103, 2-klas-ukrmova-kravcova-2019-2_s0034, 2-klas-ukrmova-kravcova-2019-2_s0035, 7-klas-ukrmova-zabolotnyi-2024_s0269, 9-klas-ukrajinska-mova-voron-2017_s0161, 10-klas-ukrajinska-mova-avramenko-2018_s0115, 11-klas-ukrajinska-mova-avramenko-2019_s0020, 11-klas-ukrajinska-mova-voron-2019_s0349, 2-klas-ukrmova-bolshakova-2019-1_s0061, 2-klas-ukrmova-kravcova-2019-2_s0031, 4-klas-ukrmova-zaharijchuk_s0119, 5-klas-ukrmova-golub-2022_s0198, 5-klas-ukrmova-litvinova-2022_s0223, 5-klas-ukrmova-zabolotnyi-2023_s0108, 6-klas-ukrmova-golub-2023_s0247, 6-klas-ukrmova-litvinova-2023_s0259, 8-klas-ukrmova-zabolotnyi-2025_s0243, 10-klas-ukrmova-karaman-2018_s0415, 1-klas-bukvar-zaharijchuk-2025-2_s0097, 2-klas-ukrmova-bolshakova-2019-1_s0080, 2-klas-ukrmova-bolshakova-2019-1_s0090, 2-klas-ukrmova-kravcova-2019-2_s0005, 2-klas-ukrmova-kravcova-2019-2_s0028, 2-klas-ukrmova-kravcova-2019-2_s0033, 2-klas-ukrmova-kravcova-2019-2_s0082, 2-klas-ukrmova-vashulenko-2019-2_s0008, 4-klas-ukrmova-zaharijchuk_s0050, 5-klas-ukrmova-avramenko-2022_s0178, 5-klas-ukrmova-golub-2022_s0206, 5-klas-ukrmova-uhor-2022-1_s0060, 5-klas-ukrmova-uhor-2022-1_s0095, 5-klas-ukrmova-uhor-2022-1_s0099, 5-klas-ukrmova-uhor-2022-1_s0108, 6-klas-ukrmova-avramenko-2023_s0096, 6-klas-ukrmova-avramenko-2023_s0209, 6-klas-ukrmova-avramenko-2023_s0214, ext-article-0, ext-article-1, ext-article-2, ext-article-3, ext-article-4, ext-article-5, ext-article-6, ext-article-7, ext-video-8]
compiled: 2026-04-06
-->

## Методичний підхід (Methodological Approach)

The topic of "My Family" (Моя сім'я / Моя родина) is a cornerstone of A1, serving as a highly motivating and immediately practical domain for beginners. The approach in Ukrainian textbooks (e.g., Большакова, Вашуленко, Кравцова for grades 1-2) is consistently communicative, context-driven, and centered on the learner's personal experience.

1.  **Narrative and Personalization:** The core method is to start with a model and then immediately ask the learner to apply it to themselves. A text like "Сім’я Оксани" (Source 4) presents a simple family structure, their names, and professions. The immediate follow-up task is always "Напишіть про свою сім’ю" (Write about your family) (Source 4, exercise 127). This personal investment is key. Stories like the one where a little girl, Ліля, counts her family members (including the cat, Муся) to get to the "seven" in "СІМ-Я" (Source 6, 7) provide a memorable and emotional anchor for the vocabulary.

2.  **Integrated Grammar:** Grammar is not taught in isolation. The topic of family is the vehicle for introducing several fundamental concepts:
    *   **Possessive Pronouns:** Introduced immediately with family nouns to force gender agreement (`мій тато`, `моя мама`).
    *   **Basic Verb Conjugation:** Presenting family members is linked to what they do, introducing 3rd person singular forms like `працює`, `вчиться`, `живе`.
    *   **Case Usage:** The construction `У мене є...` (I have...) is taught organically to express having siblings, parents, etc., providing a natural first exposure to the Genitive case.
    *   **Sentence Structure:** Simple `Subject-Predicate` sentences (`Оксана грає`) and equational sentences (`Київ — столиця України`, `Він — вчитель`) are modeled extensively (Source 2, 4).

3.  **Role-Playing and Dialogue:** Dialogues are used heavily to activate the vocabulary. Learners are encouraged to role-play scenarios like introducing family members, asking about a friend's family, or creating simple conversations (Source 8, 34). This moves the knowledge from passive to active.

4.  **Spiral Learning:** Concepts are revisited. A learner might first learn to say "Це мій брат". Later, they add his profession "Мій брат — студент". Later still, they describe him "Мій старший брат — високий". This layering reinforces vocabulary and grammar over time.

## Послідовність введення (Introduction Sequence)

The introduction of "Family" elements should follow a logical, scaffolded progression.

1.  **Core Vocabulary (Хто?):** Begin with the most immediate family members.
    *   `мама` (mom), `тато` (dad)
    *   `брат` (brother), `сестра` (sister)
    *   *Then expand to:* `дідусь` (grandfather), `бабуся` (grandmother), `син` (son), `донька` (daughter).

2.  **Simple Identification (`Це...`):** The first structure is simple pointing and naming.
    *   `Це мама.` (This is mom.)
    *   `Це мій тато.` (This is my dad.)

3.  **Possessive Pronouns (`Мій/Твій`):** Introduce `мій / моя / моє` and `твій / твоя / твоє` immediately to link family to the learner. This is the primary mechanism for teaching noun gender agreement. The exercise pattern from Uhor (Source 1) — `Бабуся → твоя бабуся` — is extremely effective and should be used.

4.  **"To Have" Construction (`У мене є...`):** Introduce the genitive construction for possession.
    *   `У мене є брат.` (I have a brother.)
    *   `У тебе є сестра?` (Do you have a sister?)
    *   Explicitly contrast this with the English "I have".

5.  **Personal Pronouns & Simple Verbs:** Link family members to actions.
    *   Introduce `він` (he) and `вона` (she).
    *   Model sentences: `Це мій тато. Він працює.` `Це моя мама. Вона вчиться.` (Source 4).
    *   Introduce 3rd person verbs: `живе` (lives), `працює` (works), `любить` (loves).

6.  **Professions and Places:** Broaden the context by linking family to work.
    *   `Мій тато — лікар. Він працює в лікарні.` (My dad is a doctor. He works in a hospital.) (Source 2, 34).

7.  **Names and Patronymics:** Introduce full names as a cultural element.
    *   Explain the concept of *по батькові* (patronymic).
    *   Model the structure: `Іван Петрович` (Ivan, son of Petro), `Марія Василівна` (Maria, daughter of Vasyl). Explain the endings `-ович` for men and `-івна` for women (Source 4).

8.  **Descriptive Adjectives:** Begin to add descriptions.
    *   `молодший брат` (younger brother), `старша сестра` (older sister).
    *   `дружна сім'я` (friendly family).

## Типові помилки L2 (Common L2 Errors)

Learners from an English background will face predictable challenges. The curriculum must preempt these.

1.  **Gender Agreement:** This is the single biggest hurdle. English has no grammatical gender for nouns.
    *   **Error:** *`моя брат` or *`мій сестра`.
    *   **Prevention:** From the very first lesson, every noun must be presented with a gendered modifier (like a possessive pronoun). Drills like the `твій, твоя, твоє` exercise (Source 1) are not optional; they are essential muscle-memory builders. Use color-coding or icons for genders.

2.  **Possession: `У мене є` vs. `Я маю`:** This is a fundamental structural difference.
    *   **Error:** Learners will default to a direct translation of "I have" and say *`Я маю брат`*.
    *   **Prevention:** Explicitly teach `У [genitive pronoun] є [nominative noun]` as the standard formula for possessing things/people. Explain that `я маю` is used more for abstract ideas ("I have an idea") or obligations. Provide many examples and drills.

3.  **Reflexive Possessive `Свій`:** This concept is alien to English.
    *   **Error:** Confusion when seeing `Я люблю свою маму` vs. `Я люблю мою маму`.
    *   **Prevention:** For A1, it's sufficient to *mostly* use `мій/твій`. However, the writer must introduce `свій` passively. Explain it as a special pronoun that means "one's own" and refers back to the subject. Acknowledge that `Я люблю мою маму` is understandable, but `Я люблю свою маму` is more natural Ukrainian. Do not over-test this at A1, but expose learners to it (see Source 43).

4.  **Case on Pronouns:** English pronouns change, but not as systematically.
    *   **Error:** *`Дай я` instead of `Дай мені`.
    *   **Prevention:** Introduce cases in chunks based on function. For "Family", the key cases are:
        *   Nominative (for the subject): `я, ти, він, вона`
        *   Genitive (for possession): `у мене, у тебе`
        *   Accusative (for the object, as in "My name is..."): `Мене звати...`

5.  **The Zero Copula ("to be"):** English speakers expect a "to be" verb in every sentence.
    *   **Error:** *`Мій тато є лікар.`
    *   **Prevention:** Teach that the verb "to be" (`є`) is dropped in the present tense for simple identification. Model `Він — лікар` (with an em-dash in writing for clarity) and `Він лікар` (in speech). Show that `є` is only used for existence, as in `У мене є брат`.

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian from a decolonized perspective is a core project principle.

1.  **No Russian Comparisons:** Under no circumstances should Ukrainian be taught "through" Russian. Avoid phrases like "it's like the Russian 'X' but..." This frames Ukrainian as a derivative, which is historically and linguistically false. Teach Ukrainian on its own terms. The pronunciation, grammar, and vocabulary should be presented as a self-contained system.

2.  **Сім'я and Родина:** Both words mean "family," but `родина` carries a deeper sense of ancestry, kin, and belonging to the nation (`рід` = kin/lineage). `Сім'я` is closer to the immediate "household." Use both words. Introduce proverbs like `Нашому роду нема переводу` (Our kin will never end) (Source 14) to subtly embed this cultural concept.

3.  **Patronymics (По батькові):** Emphasize the Ukrainian formation: `-ович` (masculine) and `-івна` (feminine). Pointedly use only Ukrainian examples and forms, such as `Васильович`/`Василівна` (Source 4), to distinguish from the Russian feminine form `-овна`.

4.  **Vocabulary Purity:** Ensure all vocabulary is authentically Ukrainian and free of common Russisms (Surzhyk). Check words against authoritative sources if there is any doubt. For instance, `дякую` (thank you), not `спасибі` (which, while used, has a contested history and is less purely Ukrainian in formal contexts).

5.  **Cultural Anchors:** Ground the language in Ukrainian culture from day one. Instead of generic examples, use culturally significant ones. Mentioning Taras Shevchenko's family (Source 9), Lesya Ukrainka's, or family traditions around `вишивка` (embroidery) (Source 14) reinforces the language's deep connection to a unique and resilient national identity.

## Словниковий мінімум (Vocabulary Boundaries)

The following vocabulary is appropriate for an A1 module on "My Family".

**Nouns (Family):**
*   `сім'я` (family, household)
*   `родина` (family, kin)
*   `мама` (mom), `тато` (dad)
*   `батьки` (parents)
*   `брат` (brother), `сестра` (sister)
*   `син` (son), `донька` (daughter)
*   `діти` (children)
*   `дідусь` (grandfather), `бабуся` (grandmother)
*   `чоловік` (husband), `дружина` (wife)

**Nouns (Other):**
*   `школа`, `лікарня`, `дім` (house), `квартира` (apartment)
*   `робота` (work), `професія` (profession)
*   `лікар` (doctor), `вчитель` (teacher), `студент` (student)

**Pronouns:**
*   **Personal:** `я, ти, він, вона, ми, ви, вони`
*   **Possessive:** `мій, моя, моє, мої`, `твій, твоя, твоє, твої`

**Verbs:**
*   `бути` (to be - mainly in `є` for `У мене є`)
*   `звати` (to be called, e.g., `Мене звати...`)
*   `жити` (to live)
*   `працювати` (to work)
*   `любити` (to love)
*   `вчитись` (to study)

**Adjectives:**
*   `старший` (older), `молодший` (younger)
*   `великий` (big), `маленький` (small)
*   `дружна` (friendly - used for `сім'я`)

## Приклади з підручників (Textbook Examples)

The writer should model activities directly on these effective examples from Ukrainian textbooks.

*   **Substitution Drill (Gender/Possessives):**
    *   "Утворіть словосполучення. Доберіть до поданих слів відповідний займенник *твій, твоя, твоє, твої*."
    *   **Зразок:** `Бабуся → твоя бабуся.`
    *   `Бабуся, дідусь, мама, тато, брат, сестра...` (Source 1)
    *   **Pedagogy:** This simple exercise is a powerhouse for drilling gender agreement.

*   **Model Text and Personalization:**
    *   Provide a short, simple text like "Це сім’я. Це тато Іван Петрович. Він вчител

============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18309 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a A1 pedagogical brief for the Ukrainian language curri...
Dimension scores:
1. Factual: 5/10 — Massive failure on basic linguistic facts. You claim `спасибі` has a "contested history" and is "less purely Ukrainian". This is a popular pseudo-patriotic myth; it is a native Old East Slavic formation used extensively in classic Ukrainian literature. Secondly, you give `Дай мені` (Dative) as an example of a common error, but then instruct the writer to teach Nominative, Genitive, and Accusative to fix it, completely ignoring the Dative case you just highlighted.
2. Language: 8/10 — The Ukrainian text provided is generally accurate and natural, but the document literally cuts off mid-word at the very end (`Він вчител`).
3. Decolonization: 5/10 — You fell into the trap of linguistic hyper-purism. Banning or marginalizing authentic Ukrainian words like `спасибі` because they share a root with Russian (`спасибо`) is doing the colonizer's work for them by artificially shrinking the Ukrainian vocabulary. Decolonization means reclaiming our heritage, not amputating it.
4. Completeness: 7/10 — The document is missing its ending. It cuts off in the middle of a sentence in the "Textbook Examples" section, rendering the final pedagogical example incomplete.
5. Actionable: 6/10 — Referencing "(Source 43)" or "(Source 4)" is useless to a human writer or LLM looking at a flat array of 49 slugs in the frontmatter. They cannot easily resolve those indices without counting manually. You should cite the textbook name directly. Furthermore, the truncated final example is not actionable.

**Overall: 6.2/10**

<fixes>
old: *   **Error:** *`Дай я` instead of `Дай мені`.
    *   **Prevention:** Introduce cases in chunks based on function. For "Family", the key cases are:
new: *   **Error:** Using Nominative instead of Accusative for objects (e.g., *`Він любить я` instead of `Він любить мене`).
    *   **Prevention:** Introduce cases in chunks based on function. For "Family", the key cases are:
---
old: 4.  **Vocabulary Purity:** Ensure all vocabulary is authentically Ukrainian and free of common Russisms (Surzhyk). Check words against authoritative sources if there is any doubt. For instance, `дякую` (thank you), not `спасибі` (which, while used, has a contested history and is less purely Ukrainian in formal contexts).
new: 4.  **Vocabulary Purity:** Ensure all vocabulary is authentically Ukrainian and free of Surzhyk. However, avoid pseudo-linguistic purism. For example, `спасибі` is a native, historically rooted Ukrainian word (used heavily by Shevchenko, Franko, etc.), not a Russism. Decolonization means reclaiming our full vocabulary, not rejecting words just because they share an etymological root with Russian.
---
old: *   Provide a short, simple text like "Це сім’я. Це тато Іван Петрович. Він вчител
new: *   Provide a short, simple text like "Це сім’я. Це тато Іван Петрович. Він вчитель. Це мама Олена Василівна. Вона лікар."
    *   Follow up immediately with a production task: "Напишіть про свою сім'ю." (Write about your family).
    *   **Pedagogy:** This bridges receptive reading with immediate, personalized production.
</fixes>


────────────────────────────────────────
✅ Gemini finished (3110 chars)
✅ Message sent to Claude (ID: 28170)
✓ Message 28170 acknowledged
   Auto-acknowledged reply #28170 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-a1-my-family-r2' — skipping GH posting (review saved to orchestration/)
✓ Message 28169 acknowledged
