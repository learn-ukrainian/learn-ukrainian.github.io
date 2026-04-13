

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **34: З друзями, для дітей** (A2, A2.5 [Case Synthesis and Plurals]).

**Target: 2000–3000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 2000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 55-75% Ukrainian — Ukrainian dominates. English for abstract grammar only.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 2000–3000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the plan's `activity_hints` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_hints` entry from the plan:

```
<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->
```

Rules:
- Use the EXACT `id` from the plan's `activity_hints` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the plan has 4 activity hints, you should place 4 markers in your prose

### Example

If the plan says:
```yaml
activity_hints:
  - id: quiz-sounds-vs-letters
    type: quiz
    focus: "Distinguish звук from літера"
  - id: match-false-friends
    type: match-up
    focus: "Match false friend Cyrillic letters to real sounds"
```

Your prose should contain (after the relevant sections):
```
[...prose about sounds and letters...]

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

[...prose about false friend letters...]

<!-- INJECT_ACTIVITY: match-false-friends -->
```

### What NOT to Do

- Do NOT write `:::quiz`, `:::fill-in`, `:::match-up`, or any DSL exercise blocks
- Do NOT write exercise questions, answers, or options — the ACTIVITIES step handles all of this
- Do NOT invent marker IDs — use only IDs from the plan's `activity_hints`

---

## Plan

<plan_content>
module: a2-034
level: A2
sequence: 34
slug: plural-other-cases
version: '1.0'
title: З друзями, для дітей
subtitle: Давальний, орудний та місцевий відмінки множини
focus: grammar
pedagogy: PPP
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
- Learner can form the Dative plural for nouns of all declension classes using the endings -ам/-ям.
- Learner can form the Instrumental plural using -ами/-ями and recognize the common alternation pattern.
- Learner can form the Locative plural using -ах/-ях and use it correctly with prepositions (у/в, на,
  по).
- Learner can use all three plural cases in practical sentences about doing things with friends, giving
  things to people, and describing locations.
dialogue_situations:
- setting: 'Organizing a school trip — all cases in plural: Розкажіть дітям (dat pl) план. Їдемо автобусами
    (inst pl). Зупинимося в готелях (loc pl). Купимо подарунки для батьків (gen pl).'
  speakers:
  - Вчитель
  - Учні
  motivation: 'All plural cases: дітям, автобусами, готелях, батьків'
content_outline:
- section: 'Давальний множини: Кому? (Dative Plural: To Whom?)'
  words: 550
  points:
  - 'Universal pattern: all nouns take -ам (hard) or -ям (soft) in Dat.Pl. студентам, друзям, дітям, містам,
    ночам.'
  - This is the most regular plural case — ONE rule covers almost everything. Compare with the complexity
    of Gen.Pl.
  - 'Common verbs requiring Dative: давати, допомагати, пояснювати, телефонувати, дякувати, радити.'
  - 'Practice: Я даю подарунки друзям. Вчитель пояснює правила студентам. Батьки допомагають дітям.'
- section: 'Орудний множини: З ким? Чим? (Instrumental Plural: With Whom? With What?)'
  words: 600
  points:
  - 'Universal pattern: -ами (hard) or -ями (soft). студентами, друзями, дітьми (irregular), містами,
    ночами.'
  - 'Key irregular forms: діти → дітьми, люди → людьми, коні → кіньми, гості → гістьми (or гостями). These
    are high-frequency — learn them.'
  - 'Preposition з/із + Instr.Pl.: Я зустрівся з друзями. Ми розмовляли з учителями. Вона прийшла з дітьми.'
  - 'Instrumental without preposition (means/tool): писати олівцями, їсти паличками, прикрасити квітами.'
  - 'Practice dialogues: planning activities with friends, describing how things are done.'
- section: 'Місцевий множини: Де? На чому? (Locative Plural: Where? On What?)'
  words: 500
  points:
  - 'Universal pattern: -ах (hard) or -ях (soft). у містах, на столах, у книжках, на заняттях, у ночах.'
  - 'Prepositions: у/в + Loc.Pl. (location), на + Loc.Pl. (surface/event), по + Loc.Pl. (distribution/across).'
  - 'Examples: Діти грають у парках. Книжки лежать на полицях. По вулицях ходять люди. На заняттях ми
    багато говоримо.'
  - 'Compare Dat. and Loc. plural — same stems, different endings: друзям (Dat.) vs. на друзях (Loc. —
    rare but demonstrates the pattern).'
- section: 'Три відмінки разом: Практика (All Three Together: Practice)'
  words: 350
  points:
  - 'Combined sentences using Dat., Instr., and Loc. plurals: Ми подарували квіти вчителям (Dat.) і сфотографувалися
    з ними (Instr.) у класах (Loc.).'
  - 'Short dialogue: organizing a trip — who to invite (Dat.), what to bring (Instr.), where to go (Loc.).'
  - 'Summary table: Dat. -ам/-ям, Instr. -ами/-ями, Loc. -ах/-ях — the most regular set of plural endings
    in Ukrainian.'
vocabulary_hints:
  required:
  - давальний відмінок (dative case)
  - орудний відмінок (instrumental case)
  - місцевий відмінок (locative case)
  - допомагати (to help)
  - дякувати (to thank)
  - подарунок (gift)
  - квіти (flowers)
  - діти (children)
  - люди (people)
  - заняття (class, lesson)
  recommended:
  - радити (to advise)
  - пояснювати (to explain)
  - полиця (shelf)
  - прикрашати (to decorate)
activity_hints:
- type: fill-in
  focus: Put the noun into the correct plural case (Dat., Instr., or Loc.) based on the preposition or
    verb in the sentence
  items: 8
- type: match-up
  focus: Match plural noun forms with the correct case label (Dat., Instr., Loc.)
  items: 8
- type: quiz
  focus: Choose the correct preposition + plural case combination to complete a sentence
  items: 8
- type: error-correction
  focus: Fix incorrect case endings in sentences
  items: 6
references:
- title: Заболотний Grade 6, §§63-65
  notes: Dat., Instr., Loc. plural endings with exercises
- title: Кравцова Grade 4, с. 46-48
  notes: Distinguishing Dative and Locative — simple exercises for recognizing case by question words

</plan_content>

---

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification
- Confirmed: давальний, орудний, місцевий, відмінок, допомагати, дякувати, подарунок, квіти, діти, люди, заняття, радити, пояснювати, полиця, прикрашати.
- Irregular forms confirmed: дітьми, людьми, кіньми, гістьми.
- Not found: None.

## Grammar Rules
- Dative Plural: Ending -ам (hard), -ям (soft). Universal for all nouns. (Pravopys §92/95/98/101 - confirmed via Textbook Grade 6 Golub p.79).
- Instrumental Plural: Ending -ами (hard), -ями (soft). Irregulars: дітьми, людьми, гістьми, кіньми. (Textbook Grade 4 Varzatska p.71).
- Locative Plural: Ending -ах (hard), -ях (soft). Used with prepositions у/в, на, по. (Textbook Grade 4 Ponomarova p.60).
- Preposition "по" + Locative: In Ukrainian, "по" takes the Locative plural (-ах, -ях), unlike Russian which uses Dative. (Textbook Grade 4 Varzatska p.71 — "Не плутай!").

## Calque Warnings
- по вулицях: OK (Locative Plural) — avoid Russianism "по вулицям" (Dative).
- дякувати друзям: OK (Dative) — Ukrainian "дякувати" always takes Dative, unlike Russian "благодарить" + Accusative.
- на заняттях: OK (Locative Plural) — standard way to express "at/during classes".

## CEFR Check
- допомагати: A2 — (Confirmed: Grade 4 textbooks).
- дякувати: A1 — (Confirmed: High-frequency basic verb).
- подарунок: A2 — (Confirmed: Grade 4 textbooks).
- заняття: A2/B1 — (Confirmed: Grade 6 textbooks, appropriate for late A2).
- прикрашати: A2 — (Confirmed: Grade 4 textbooks).
- полиця: A2 — (Confirmed: Grade 4 textbooks).
</pre_verified_facts>


## Wiki Teaching Brief — Your Authoritative Source

**This is your primary teaching material.** The wiki article below was compiled from real Ukrainian school textbooks, literary sources, and verified references. It contains the correct terminology, paradigm tables, teaching sequences, and examples for this module. Your job is to TRANSFORM this into engaging, level-appropriate content — not to copy it verbatim.

**How to use the wiki article:**
1. **Adopt the Ukrainian terminology.** If the article says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Follow the teaching sequence.** If the article shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Use the article's examples as your foundation.** Authentic examples from textbooks beat invented ones. Use the article's examples and expand with your own that follow the same patterns.
4. **Synthesize and teach, don't summarize.** You are a teacher, not a summarizer. Take the facts from the article and weave them into engaging explanations with dialogues, situations, and practice. The article tells you WHAT to teach — you decide HOW to teach it for the target level.
5. **Your pre-training is contaminated by Russian and English linguistics.** When the article contradicts your instinct, the article wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
6. **Do NOT copy paragraphs verbatim.** The article is reference material. Your output must be original teaching prose at the correct CEFR level, not a rephrased version of the article.

<knowledge_packet>
# Knowledge Packet: З друзями, для дітей
**Module:** plural-other-cases | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/plural-other-cases.md

# Граматика A2: З друзями, для дітей



## Як це пояснюють у школі (How Schools Teach This)

Ukrainian schools introduce noun declension (змінювання за відмінками) early, typically by Grade 3 or 4. The approach is foundational and builds iteratively.

1.  **Core Concept (Grades 3-4)**: The initial introduction focuses on the concept that nouns change their endings to connect with other words in a sentence (Source 13, 32). This is taught through questions. Each of the seven cases is paired with specific questions (`хто? що?`, `кого? чого?`, etc.). Mnemonics are sometimes used to help students remember the order of the cases, such as "Нашого Ромчика Дивує Зебра — Оця Маленька Красуня" (Source 8).

2.  **Systematization (Grades 4-6)**: Instruction moves from simple question-answer pairs to systematic tables. Students learn to identify the case of a noun in a sentence by asking the correct question and observing its ending and any associated prepositions (Source 12, 19, 22). The distinction between direct (Називний) and indirect (усі інші) cases is established (Source 13, 35). Plural endings for Instrumental (`-ами`/`-ями`) and Locative (`-ах`/`-ях`) are explicitly taught (Source 20, 28).

3.  **Distinguishing Similar Cases (Grade 4 onwards)**: Textbooks provide specific strategies for distinguishing cases that have similar forms or questions.
    *   **Dative vs. Locative**: Though endings can be identical in the singular (e.g., `(на) білочці`), they are differentiated by meaning and prepositions. The Dative case often indicates the recipient of an action and is usually used without a preposition, while the Locative case indicates location and *always* requires a preposition (`у`, `на`, `по`) (Source 9, 37).
    *   **Nominative vs. Accusative**: For inanimate nouns, these cases can look identical. The key differentiator is the noun's function in the sentence: a noun in the Nominative case is the subject, whereas in the Accusative case it is a direct object (Source 30, 42).

4.  **Complexities (Grades 6-8)**: Older grades delve into the finer points, such as the declension patterns of different noun groups (тверда, м'яка, мішана) (Source 39, 40), the complexities of the Genitive plural endings (Source 39), and the declension of nouns that only exist in the plural (*pluralia tantum*) like `Карпати`, `окуляри`, `гроші` (Source 23, 24). The concept of syntactic government (керування), where a verb or preposition dictates the case of a noun, is also formally introduced (Source 15, 25).

The overall pedagogy is structured and consistent: introduce the concept with questions, provide clear tables, practice with sentence analysis and transformation exercises, and then address exceptions and similar-looking forms with targeted rules.

## Повна парадигма (Full Paradigm)

Ukrainian nouns change their endings in the plural according to their case. The patterns depend on the noun's gender and declension group. Here are the most common paradigms for A2/B1 learners.

### І & ІІ Відміна (1st & 2nd Declensions): Most Common Nouns

These tables cover the vast majority of masculine, feminine, and neuter nouns.

| Відмінок (Case) | Питання (Questions) | Друзі (m, an.) | Коні (m, an.) | Річки (f, inan.) | Міста (n, inan.) | Моря (n, inan.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Н.** (Nom.) | хто? що? | друзі | коні | річки | міста | моря |
| **Р.** (Gen.) | кого? чого? | друз**ів** | кон**ей** | річ**ок** | міст | мор**ів** |
| **Д.** (Dat.) | кому? чому? | друз**ям** | кон**ям** | річк**ам** | міст**ам** | мор**ям** |
| **Зн.** (Acc.) | кого? що? | друз**ів** | кон**ей** / коні | річки | міста | моря |
| **Ор.** (Instr.) | ким? чим? | друз**ями** | **кіньми** | річк**ами** | міст**ами** | мор**ями** |
| **М.** (Loc.) | на/у кому? чому? | на/у друз**ях** | на/у кон**ях** | на/у річк**ах** | по/у міст**ах** | у/на мор**ях** |
| **Кл.** (Voc.) | (звертання) | друзі | коні | річки | міста | моря |

*(Paradigms compiled from Sources 35, 39, 41, and 33)*

**Key Observations:**
*   **Genitive Plural (`-ів`, `-ей`, `-ок`)**: This is the most complex case. Common endings are `-ів` (for many masculine/neuter nouns like `друзів`, `морів`), `-ей` (for some like `коней`, `гостей`), or a **zero-ending** (`-ø`), often with a vowel change (`річка` -> `річок`, `нога` -> `ніг`) (Source 39).
*   **Dative (`-ам`, `-ям`)**: Very regular. Ends in `-ам` after a hard consonant and `-ям` after a soft one (Source 39).
*   **Accusative (Animate vs. Inanimate)**: For inanimate nouns (`річки`, `міста`), the form is identical to the Nominative. For animate nouns (`друзі`, `коні`), the form is identical to the Genitive (Source 30, 41).
*   **Instrumental (`-ами`, `-ями`, `-ми`)**: Mostly regular with `-ами`/`-ями`. However, a small but common group of masculine nouns uses the ending `-ми` (e.g., `кіньми`, `гістьми`, `чобітьми`). The form `дверима` (doors) is also common (Source 24, 41).
*   **Locative (`-ах`, `-ях`)**: Very regular. Always used with a preposition (`на`, `у`, `по`) (Source 28, 37).
*   **Vocative**: In the plural, the Vocative is almost always identical to the Nominative (Source 22, 35).

### Pluralia Tantum (Іменники, що мають лише форму множини)
A number of common nouns exist only in the plural. They follow similar declension patterns.

| Відмінок (Case) | Питання (Questions) | Карпати (гори) | Окуляри (очі) | Гроші (кошти) |
| :--- | :--- | :--- | :--- | :--- |
| **Н.** (Nom.) | що? | Карпати | окуляри | гроші |
| **Р.** (Gen.) | чого? | Карпат | окуляр**ів** | грош**ей** |
| **Д.** (Dat.) | чому? | Карпат**ам** | окуляр**ам** | грош**ам** |
| **Зн.** (Acc.) | що? | Карпати | окуляри | гроші |
| **Ор.** (Instr.) | чим? | Карпат**ами** | окуляр**ами** | **грішми** / грошима |
| **М.** (Loc.) | на/у чому? | в/на Карпат**ах** | в окуляр**ах** | у грош**ах** |
| **Кл.** (Voc.) | (звертання) | Карпати | окуляри | гроші |

*(Examples and forms from Sources 3, 23, 24, 39)*

## Частотність і пріоритети

For A2 learners, not all cases are used with equal frequency in plural forms. The goal is communication, so focus should be on the most common patterns.

1.  **Priority 1: Locative & Instrumental**
    *   **Locative (`-ах`/`-ях`)**: Essential for talking about location. Phrases like `в Карпатах` (Source 3), `на канікулах` (Source 11), `у містах` (Source 1) are extremely common. The pattern is highly regular and provides a high return on investment.
    *   **Instrumental (`-ами`/`-ями`)**: Crucial for expressing "with...". The phrase `з друзями` (with friends) is ubiquitous in texts about social activities (Source 1, 6). The pattern is also very regular.

2.  **Priority 2: Genitive & Accusative (Animate)**
    *   **Genitive Plural (`-ів`, zero ending)**: Necessary for expressing absence (`немає друзів`, `немає проблем`), quantity (`багато друзів`, `кілька місяців`), and belonging (`свято для дітей`). The zero-ending with vowel changes (`книжка` -> `книжок`) is challenging but frequent. The `-ів` ending is very common for masculine nouns.
    *   **Accusative Plural (Animate)**: Since this form matches the Genitive for animate nouns (`Я люблю своїх друзів`), mastering the Genitive helps master this as well. It's vital for any sentence where the direct object is a group of people or animals.

3.  **Priority 3: Dative**
    *   **Dative Plural (`-ам`/`-ям`)**: While grammatically simple, its usage in the plural is less frequent in basic A2 conversation than other cases. It's used for giving something *to* multiple people (`дякувати друзям`) or for age (`дітям п'ять років`), but many of these constructions can be worked around at a lower level. It becomes more important at B1.

## Типові помилки L2 (Common L2 Errors)

English speakers often struggle with cases in general. Here are specific pitfalls related to plural nouns.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| Я був в **Карпати**. | Я був в **Карпатах**. | This is a direct transfer from English syntax, which does not change the noun form after a preposition like "in". The Locative case (`-ах`/`-ях`) is mandatory after prepositions of location like `в` and `на` (Source 3, 37). |
| Я не маю **книги**. | Я не маю **книжок** / **книг**. | The Genitive plural is often a zero-ending, frequently requiring a vowel insertion (`книжка -> книжок`) for ease of pronunciation. Simply using the Genitive singular form is a common error (Source 39). |
| Я бачу мої **друзі**. | Я бачу моїх **друзів**. | Learners forget that the Accusative case for animate nouns is identical to the Genitive case, not the Nominative. `Друзі` is "who/what" (subject), but `друзів` is "whom/what" (object) (Source 39, 41). |
| Ми говорили **з друзі**. | Ми говорили **з друзями**. | Forgetting to apply the Instrumental case ending `-ами`/`-ями` after the preposition `з` ("with") is a typical mistake. The noun must change to show its role in the phrase (Source 1, 35). |
| Ми їхали по **полям**. | Ми їхали по **полях**. | This is a classic Russism. In Russian, the Dative plural (`по полям`) is used after `по`. In Ukrainian, the Locative plural (`по полях`) is correct for movement across a surface (Source 20). |

## Деколонізаційні застереження (Decolonization Notes)

It is critical to teach Ukrainian grammar on its own terms, not as a variant of Russian. The two languages, while related, have followed different evolutionary paths from Proto-Slavic, resulting in significant structural differences.

1.  **The `по` + Locative Rule**: The most common L2 error influenced by Russian is the use of the preposition `по`. In Ukrainian, when `по` indicates movement across a surface or distribution, it requires the **Locative** case: `ходити по магазинах`, `гуляти по полях`. In Russian, this construction uses the Dative case (`ходить по магазинам`). Explicitly teaching `по + М.в.` as the Ukrainian standard is a crucial decolonization point (Source 20).

2.  **Instrumental Plural `-ми`**: Ukrainian has preserved an archaic Instrumental plural ending `-ми` for a specific group of nouns (mostly 2nd and 4th declension), such as `кіньми`, `гістьми`, `дверима`, `грошима`. While parallel forms with `-ами`/`-ями` (`грошима`) sometimes exist, the `-ми` form is distinctly Ukrainian and should be presented as a normal, living feature of the language, not a strange exception (Source 41, 24). In modern Russian, this ending is largely considered archaic or poetic.

3.  **Genitive Plural Variations**: The formation of the Genitive plural in Ukrainian, with its complex system of vowel alternations (`нога` -> `ніг`), inserted vowels (`земля` -> `земель`), and varied endings (`-ів`, `-ей`, zero), is a unique feature. It should not be simplified or taught using Russian models, which have their own (different) set of complexities. The Ukrainian system must be learned from Ukrainian examples.

4.  **Vocabulary Choice**: Use authentically Ukrainian vocabulary in examples. Avoid words that are calques or direct loans from Russian when a native Ukrainian equivalent exists. For instance, in social contexts, use `зустрічатися з друзями` (Source 1) rather than constructions that might mirror Russian phrasing.

Presenting Ukrainian as a self-contained system with its own logic is the core of a decolonized pedagogical approach.

## Природні приклади (Natural Examples)

These examples are taken from authentic Ukrainian sources and demonstrate the natural use of plural cases in context.

**Group 1: Locative (`-ах`/`-ях`) - Talking about location**
*   "Взимку в Києві дуже багато [цікавих подій], наприклад, в **театрах** і **операх** є багато вистав." (In winter in Kyiv there are many [interesting events], for example, in the theaters and operas there are many shows.) (Source 1)
*   "В українських **селах** на Різдво ставили не ялинку, а дідух." (In Ukrainian villages at Christmas, they used to put up not a Christmas tree, but a didukh.) (Source 10)
*   "...а ще в **горах** ми збирали гриби." (...and also in the mountains we gathered mushrooms.) (Source 3)

**Group 2: Instrumental (`-ами`/`-ями`) - Doing things "with" people or things**
*   "Зустрічайтеся частіше з **друзями**, ходіть в гості." (Meet more often with friends, visit each other.) (Source 1)
*   "Він [дельфін] пригадав, як грався з **друзями** — дельфінами, як ми разом супроводжували кораблі." (He [the dolphin] remembered how he played with his friends—dolphins, how we accompanied ships together.) (Source 6)
*   "Поїдь зі своїми **полками** поблизу мого полку." (Ride with your regiments near my regiment.) (Source 5)

**Group 3: Genitive (`-ів`, `-ей`, `-ø`) - Expressing quantity or absence**
*   "Для **дітей** ти просто диво!" (For children, you are simply a miracle!) (Source 6)
*   "Зараз у нас немає домашніх **тварин**." (Right now we don't have any pets.) (Source 7)
*   "У нас є багато **видів** чаю." (We have many kinds of tea.) (Source 1)

**Group 4: Accusative (Animate) - Direct objects that are alive**
*   "Взимку ми підгодовуємо **птахів**." (In winter, we feed the birds.) (Source 30)
*   "Я знаю, що ти зі своїми **друзями** завжди поспішаєш **людям** на допомогу." (I know that you and your friends always hurry to help people.) (Source 6) <!-- Note: Here 'людям' is Dative, but 'друзями' is Instrumental, showing case interplay -->

**Group 5: Dative (`-ам`/`-ям`) - Giving or helping people**
*   "А ми, люди, чим віддячуємо **дельфінам** за їхню любов і відданість?" (And what about us, people, how do we thank the dolphins for their love and devotion?) (Source 6)
*   "Моїм **батькам** дуже цікаво познайомитися з іноземцями." (It's very interesting for my parents to meet foreigners.) (Source 7)

## Рекомендації для вправ (Activity Concepts)

A phased approach is best for internalizing plural cases.

*   **Phase 1: Recognition & Identification (Input)**
    *   **Drill 1 (Case Matching)**: Given a list of plural nouns (`друзям`, `в горах`, `коней`, `книгами`), students match them to the correct case name and question (`Кому? Чому? -> Давальний`).
    *   **Drill 2 (Sentence Highlighting)**: Provide a short text (like a dialogue from Source 3). Students must find and highlight all plural nouns and identify their case.

*   **Phase 2: Controlled Production (Practice)**
    *   **Drill 3 (Fill-in-the-Blank)**: Provide sentences with a noun in the Nominative plural in parentheses. Students must write the correct form.
        *   `Я люблю гуляти з (мої друзі) ___________.` -> `моїми друзями`
        *   `У нас немає (домашні тварини) ___________.` -> `домашніх тварин`
        *   `Ми живемо в (Карпати) ___________.` -> `Карпатах`
    *   **Drill 4 (Transformation)**: Give a simple sentence in the singular and prompt students to create a plural version.
        *   `Я дав книгу другу.` -> `Я дав книги (друзі) ___________.` -> `друзям`
        *   `Кінь стоїть у полі.` -> `(Коні) ___________ стоять у полях.` -> `Коні`

*   **Phase 3: Communicative Production (Output)**
    *   **Activity 5 (Question & Answer)**: Ask open-ended questions that require plural cases in the answer.
        *   `Що ви робили з друзями минулих вихідних?` (Requires Instrumental)
        *   `В яких містах України ви були?` (Requires Locative)
        *   `Скільки у вас є українських книжок?` (Requires Genitive)
    *   **Activity 6 (Picture Description)**: Show a picture of a busy place (a market, a park) and have students describe it using plural nouns. `Я бачу багато людей. Вони розмовляють з друзями. Діти граються з собаками.`

## Зв'язки з іншими темами

*   **Prerequisites**: This topic directly builds on an understanding of **Nominative Plural** forms and the concept of **Cases in the Singular**. Without knowing how to form a basic plural (`друг` -> `друзі`), declining it is impossible.
*   **Adjective Agreement**: This is the immediate next step. Once a learner can form `з друзями`, they can learn to add adjectives that agree in case, number, and gender: `з **хорошими** друзями`. Teaching adjective declension without a solid foundation in noun declension is ineffective.
*   **Prepositions**: This topic reinforces the function of many prepositions (`з`, `в`, `на`, `про`, `для`, `без`), showing how they "govern" or require a specific case.

## Пов'язані статті

*   grammar/a1/noun-cases-singular
*   grammar/a1/nominative-plural
*   grammar/a2/adjective-declension-plural
*   grammar/a1/prepositions-and-cases
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Давальний множини: Кому? (Dative Plural: To Whom?)` (~550 words)
- `## Орудний множини: З ким? Чим? (Instrumental Plural: With Whom? With What?)` (~600 words)
- `## Місцевий множини: Де? На чому? (Locative Plural: Where? On What?)` (~500 words)
- `## Три відмінки разом: Практика (All Three Together: Practice)` (~350 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 2000 words minimum.

---

## Content Rules

TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.

GRAMMAR RULES:
- Max 15 words per Ukrainian sentence
- Max 2 clauses per sentence
- All cases allowed
- Simple subordinate clauses allowed (який/що/коли)
- Aspect pairs introduced but not complex
- No participles

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce)
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Zero paronyms**: тактична≠тактовна, ефектний≠ефективний — use the right word, not a similar-sounding one
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

**Authority hierarchy (if uncertain about a word, check in this order):**
VESUM (does word exist?) → Правопис 2019 (spelling) → Горох (stress) → Антоненко-Давидович (style) → Грінченко (etymology).

**Online fallbacks:** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) — at least 3 per module (mnemonics, common mistakes, cultural notes). Space them throughout the module, not clustered.
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- **Dialogues must sound like real people talking.** Test: would two Ukrainians actually say this to each other? If the dialogue sounds like a textbook drill ("Це кінь? — Так, це кінь."), rewrite it. Good dialogues have context, reactions, and personality:

  BAD (interrogation): "Це сім'я? — Так, це сім'я. — А де м'ясо? — М'ясо там."
  GOOD (natural): "Це твоя сім'я на фото? — Так! Нас п'ять. — А що ви їсте? М'ясо? — Так, дуже смачне!"

  BAD (labeling objects): "Це дуб. — А там коза. — Ні, це коса."
  GOOD (real reaction): "Дивись, який великий дуб! — Так, старий. А під ним — коза! — Смішна коза."

  Use the knowledge packet's textbook excerpts for dialogue patterns. Adapt real situations, don't invent drills.
- **DIALOGUE VARIETY — CRITICAL.** Each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules.

  **Module-specific dialogue settings (from plan):**
  1. **Organizing a school trip — all cases in plural: Розкажіть дітям (dat pl) план. Їдемо автобусами (inst pl). Зупинимося в готелях (loc pl). Купимо подарунки для батьків (gen pl).**
     Speakers: Вчитель, Учні
     Why: All plural cases: дітям, автобусами, готелях, батьків

  Use these settings. Do NOT substitute with a room description or generic greeting.
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.



### Vocabulary

**Required:** давальний відмінок (dative case), орудний відмінок (instrumental case), місцевий відмінок (locative case), допомагати (to help), дякувати (to thank), подарунок (gift), квіти (flowers), діти (children), люди (people), заняття (class, lesson)
**Recommended:** радити (to advise), пояснювати (to explain), полиця (shelf), прикрашати (to decorate)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*



---

## Skeleton — Follow This Structure Exactly

A detailed paragraph-level skeleton was generated for this module. You MUST follow it precisely:
- Write every paragraph listed, in the order listed
- Hit each paragraph's word budget (+-10%)
- Place exercises exactly where the skeleton says
- Use the specific examples named in the skeleton
- Do NOT skip paragraphs, reorder sections, or add unplanned content

The skeleton replaces Step 1 (Pacing Plan) — do NOT output a <pacing_plan> block. Start writing immediately from the first section.

<skeleton>
## Давальний множини: Кому? (Dative Plural: To Whom?) (~550 words total)
- P1 (~120 words): [Introductory dialogue: A teacher organizing a school trip. "Слухайте, діти! Я розповім студентам і учням план нашої подорожі. Ми подякуємо батькам за допомогу." Highlights Dative plural use for recipients and high-frequency verbs.]
- P2 (~150 words): [Grammar explanation: The universal pattern for Dative Plural. All nouns (masculine, feminine, and neuter) typically take -ам for hard stems and -ям for soft stems. Examples: студентам, містам, книжкам, друзям, морям, пісням.]
- P3 (~100 words): [Pedagogical comparison: Contrast the simplicity of the Dative plural (one rule fits almost all) with the complexity of the Genitive plural (zero endings, -ів, -ей). Explain that this regularity makes it one of the easiest cases to master in the plural.]
- P4 (~100 words): [Verbs governing the Dative: Focus on common communicative verbs like давати (to give), допомагати (to help), дякувати (to thank), телефонувати (to call), and пояснювати (to explain). Examples: "Я телефоную друзям," "Вона допомагає дітям."]
- P5 (~80 words): [Special focus on pluralia tantum in the Dative: nouns that only exist in plural. Examples: Карпатам, грошам, окулярам, штанам. Explain that they follow the same -ам/-ям rule.]
- <!-- INJECT_ACTIVITY: match-up-plural-cases --> [match-up, focus: Match plural noun forms with the correct case labels (Nom, Gen, Dat), 8 items]

## Орудний множини: З ким? Чим? (Instrumental Plural) (~600 words total)
- P1 (~150 words): [Grammar explanation: Forming the Instrumental plural with -ами (hard) and -ями (soft). Cover all genders: братами, жінками, вікнами vs. вчителями, вулицями, обличчями. Emphasize the semantic role of "with" or "by means of".]
- P2 (~150 words): [Irregular/Archaic forms: Deep dive into the -ми ending preserved in high-frequency nouns. Essential list for A2: дітьми, людьми, кіньми, гістьми, чобітьми, and the common variant грішми/грошима. Explain that these are standard, living forms in Ukrainian.]
- P3 (~150 words): [The preposition з/із + Instrumental Plural: Practical social context. Examples: "зустрічатися з друзями," "розмовляти з колегами," "гратися з котами." Explain the vowel harmony for з vs із before clusters.]
- P4 (~150 words): [Instrumental as a tool (without preposition): Describing actions and means. Examples: "писати олівцями," "їсти паличками," "прикрашати квітами," "їхати автобусами." Use the school trip context: "Ми їдемо великими автобусами."]
- <!-- INJECT_ACTIVITY: fill-in-plural-forms --> [fill-in, focus: Put the noun in parentheses into the correct plural case (Dat or Instr) based on context, 8 items]

## Місцевий множини: Де? На чому? (Locative Plural) (~500 words total)
- P1 (~150 words): [Grammar explanation: The Locative plural endings -ах (hard) and -ях (soft). Explain that like the singular, the Locative plural *always* requires a preposition. Examples: у театрах, на полицях, у листах, на заняттях.]
- P2 (~150 words): [Decolonization & Precision: The 'по' + Locative plural rule. Explain that movement across a surface or distribution in Ukrainian uses the Locative (unlike Russian's Dative). Examples: "гуляти по парках," "ходити по магазинах," "подорожувати по країнах."]
- P3 (~100 words): [Location idioms and fixed phrases: Focus on common A2 expressions. Examples: "в Карпатах" (in the Carpathians), "на канікулах" (on holidays), "у вихідних" (on weekends), "на сторінках" (on the pages).]
- P4 (~100 words): [Formal distinction: Distinguishing Dative (-ам) from Locative (-ах) through questions (Кому? vs На чому?). Use the example "друзям" (to friends) vs "на друзях" (on/about friends) to show the stem consistency.]
- <!-- INJECT_ACTIVITY: quiz-preposition-case --> [quiz, focus: Choose the correct preposition and plural case ending to complete the sentence, 8 items]

## Три відмінки разом: Практика (Synthesis) (~350 words total)
- P1 (~150 words): [Narrative synthesis: A short story about children preparing for a festival. "Ми купуємо подарунки дітям (Dat). Ми прикрашаємо залу квітами (Instr). Свято буде у школах (Loc)." Demonstrates shifting between cases to convey different relations.]
- P2 (~100 words): [Practical dialogue: Two friends discussing a birthday party. Uses questions like "Кому ми даруємо це?", "З ким ти йдеш?", and "В яких кафе ми можемо сісти?". Covers Dat, Instr, and Loc plural forms in natural flow.]
- P3 (~100 words): [Summary Table & Recap: A quick-reference look at the endings: Dat (-ам/-ям), Instr (-ами/-ями), Loc (-ах/-ях). Reiterate that these are the most regular plural endings in the language.]
- <!-- INJECT_ACTIVITY: error-correction-plural --> [error-correction, focus: Identify and fix incorrect plural case endings in a short text about a trip, 6 items]

## Підсумок (~150 words)
- P1 (~150 words): [Summary of key takeaways: 1. Dative plural is the recipient (-ам/-ям). 2. Instrumental plural is for 'with' or 'by means' (-ами/-ями, with -ми exceptions). 3. Locative plural is for location and always has a preposition (-ах/-ях). Self-check questions: Як сказати "with friends"? (з друзями). Яке закінчення у місцевому відмінку множини? (-ах/-ях). Коли ми використовуємо "дітьми"? (в орудному відмінку).]

Grand total: ~2150 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

Begin writing now. Start with the first section heading.
