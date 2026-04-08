

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **18: Студентові, сестрі, дитині** (A2, A2.3 [Dative Case]).

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

1. **IMMERSION TARGET: 45-65% Ukrainian — nearly half in Ukrainian. English for grammar theory only.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
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
module: a2-018
level: A2
sequence: 18
slug: dative-nouns
version: '1.0'
title: Студентові, сестрі, дитині
subtitle: Закінчення давального відмінка іменників усіх родів
focus: grammar
pedagogy: PPP
phase: A2.3 [Dative Case]
word_target: 2000
objectives:
  - Learner can form dative singular endings for masculine nouns using the 
    correct variant (-ові/-еві/-єві vs. -у/-ю).
  - Learner can form dative singular endings for feminine nouns (-і/-ї for 
    hard/soft stems, -ці/-зі after velars with consonant alternation).
  - Learner can form dative singular endings for neuter nouns (-у/-ю).
  - Learner can use dative nouns as indirect objects with verbs like подарувати,
    показати, розповісти, написати.
dialogue_situations:
  - setting: 'At a post office — addressing packages to different people: Студентові
      Петренку — підручник (m, textbook). Сестрі Олені — листівка (f, postcard). Дитині
      — іграшка (f, toy).'
    speakers:
      - Відправник (sender)
      - Працівник пошти
    motivation: 'Dative nouns: студент→студентові, сестра→сестрі, дитина→дитині'
content_outline:
  - section: 'Давальний відмінок іменників чоловічого роду (Dative of Masculine Nouns)'
    words: 650
    points:
      - 'II declension masculine nouns have parallel endings: -ові/-еві/-єві and -у/-ю.
        Both are correct: братові = брату, лікареві = лікарю.'
      - '-ові for hard stems (студентові, другові, батькові), -еві for soft stems
        and sibilants (вчителеві, товаришеві), -єві after vowels (героєві).'
      - 'Style rule from Заболотний: when multiple dative nouns appear together, alternate
        endings to avoid monotony — подякувати сусідові Данилу.'
      - 'I declension masculine nouns (Дмитро, батько): follow their declension pattern
        — Дмитрові, батькові.'
      - Practice with common masculine nouns learners already know from A1-A2.
  - section: 'Давальний відмінок іменників жіночого роду (Dative of Feminine Nouns)'
    words: 500
    points:
      - 'I declension: hard stems take -і (мамі, подрузі, сестрі), soft stems take
        -і (землі, пісні), stems in -ія take -ії (станції).'
      - 'Consonant alternations before -і: к→ц (подруга→подрузі), г→з (книга→книзі),
        х→с (свекруха→свекрусі).'
      - 'III declension feminine nouns: -і (ночі, матері, любові, радості).'
      - Practice sentences using indirect object pattern (подарувати квіти мамі,
        написати листа подрузі).
  - section: 'Давальний відмінок іменників середнього роду (Dative of Neuter Nouns)'
    words: 350
    points:
      - 'II declension neuter: -у for hard stems (місту, слову, вікну), -ю for soft
        stems (морю, серцю).'
      - 'IV declension (nouns in -а/-ят-): -аті/-яті (немовляті, курчаті).'
      - Examples with neuter nouns in real contexts (дати назву місту, радіти 
        сонцю).
  - section: 'Давальний відмінок у реченні (Dative Nouns in Sentences)'
    words: 500
    points:
      - 'Two-object verb pattern: Subject + Verb + Dative (recipient) + Accusative
        (thing). Тетяна подарувала братові книгу. Вчитель показав студентам карту.'
      - 'Common verbs with indirect objects: подарувати, показати, дати, розповісти,
        написати, пояснити, відповісти.'
      - Dialogue practice — giving gifts, explaining things, writing to someone.
      - Contrast with Genitive constructions (дати братові vs. немає брата) to 
        reinforce case discrimination.
vocabulary_hints:
  required:
    - студентові (to the student (dat.))
    - сестрі (to the sister (dat.))
    - другові (to the friend (dat.))
    - подарувати (to give as a gift)
    - показати (to show)
    - написати (to write)
    - розповісти (to tell, to narrate)
    - пояснити (to explain)
    - відповісти (to answer, to reply)
    - закінчення (ending (grammar))
  recommended:
    - відміна (declension)
    - чергування (alternation (grammar))
    - одержувач (recipient)
    - немовля (baby, infant)
activity_hints:
  - type: fill-in
    focus: Put the noun in brackets into the dative case (e.g., подарувати 
      [брат] → братові)
    items: 8
  - type: group-sort
    focus: Sort dative nouns by gender (masculine -ові/-у, feminine -і, neuter 
      -у/-ю)
    items: 8
  - type: quiz
    focus: Choose the correct dative ending for nouns with consonant alternation
      (подруга→подрузі vs. *подругі)
    items: 8
  - type: match-up
    focus: Match verb + dative noun phrases to their English meanings
    items: 8
  - type: unjumble
    focus: Reorder words to form correct dative constructions with indirect 
      objects (e.g., подарувати братові книгу)
    items: 6
references:
  - title: "Заболотний Grade 10, §157"
    notes: "Dative endings for II declension masculine nouns with parallel -ові/-еві/-єві
      and -у/-ю, style rule for alternating"
  - title: "Глазова Grade 10, §194"
    notes: "Dative singular endings for masculine nouns by declension group (hard,
      soft, mixed)"
  - title: "Кравцова Grade 4, §135"
    notes: "Distinguishing dative and locative case — shared endings, different functions"

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
- Confirmed: студентові, сестрі, другові, подарувати, показати, написати, розповісти, пояснити, відповісти, закінчення, відміна, чергування, одержувач, немовля.
- Not found: None. All 14 words are confirmed.

## Grammar Rules
- Dative of Masculine Nouns: Іменники чоловічого роду в давальному відмінку однини мають паралельні закінчення -ові, -еві (-єві) та -у (-ю). (e.g., братові/брату). Style rule: alternate endings to avoid monotony (e.g., "подякувати сусідові Данилу"). (Grade 10 Zabolotnyi, Grade 4 Ponomarova).
- Dative of Feminine Nouns: Consonant alternations before -і: к→ц (білочка → білочці), г→з (книга → книзі, Прага → Празі), х→с (муха → мусі). (Grade 4 Kravtsova, Grade 5 Uhor).
- Dative of Neuter Nouns: II declension takes -у/-ю (вікну, місту/містові), IV declension (nouns in -а/-ят-) takes -аті/-яті (немовляті, курчаті). (Grade 4 Kravtsova, Grade 6 Zabolotnyi).
- Sentence Pattern: Verb + Dative (Recipient) + Accusative (Object). (Grade 4 Kravtsova).

## Calque Warnings
- приймати участь: Calque — use **брати участь**.
- давати відповідь: OK, but **відповісти** is often more natural for single actions.
- одержувач: OK (Term for "recipient"), confirmed in VESUM.

## CEFR Check
- студент: A1 — OK
- сестра: A1 — OK
- друг: A1 — OK
- подарувати: A2 — OK
- немовля: A2 (appears in Grade 1 Bukvar and Grade 3 textbooks) — OK
- одержувач: B1/Technical — OK as a grammar label for "Recipient" in the context of Dative case.
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
# Knowledge Packet: Студентові, сестрі, дитині
**Module:** dative-nouns | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/dative-nouns.md

# Граматика A2: Студентові, сестрі, дитині



## Як це пояснюють у школі (How Schools Teach This)

Давальний відмінок (the Dative case) в українській шкільній програмі вводиться поступово, починаючи з початкових класів. Основна функція відмінка пояснюється через питання **«кому? чому?»** (Source 11: 4-klas-ukrmova-zaharijchuk_s0082) і його назву, що походить від дієслова «давати» — дія, спрямована на отримувача (Source 42: ext-ulp_youtube-252).

Ключові концепції та послідовність викладання:

1.  **Основна функція (4 клас):** Учні знайомляться з давальним відмінком як з відмінком, що позначає адресата дії. Наприклад, у конструкціях "подарувати (кому?) сестрі", "написати (кому?) другові" (Source 31: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0045).

2.  **Ключові правила для іменників І відміни (4 клас):** Одним з перших правил є чергування приголосних **[г], [к], [х]** на **[з'], [ц'], [с']** в іменниках жіночого роду перед закінченням `-і`. Це правило є спільним для давального і місцевого відмінків.
    *   *доро**г**а* → *доро**з**і*
    *   *ру**к**а* → *ру**ц**і*
    *   *му**х**а* → *му**с**і*
    (Джерело: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0046, 4-klas-ukrayinska-mova-ponomarova-2021-1_s0049)

3.  **Паралельні форми для іменників ІІ відміни (4-6 класи):** Учні дізнаються, що іменники чоловічого роду в давальному відмінку однини можуть мати паралельні закінчення: **-ові, -еві (-єві)** або **-у (-ю)** (Source 30: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0044).
    *   Спочатку це пояснюється на прикладі назв істот: `батькові/батьку`, `коневі/коню`, `другові/другу` (Source 30, 31).
    *   У старших класах (6-10) це правило поглиблюється, і додається стилістична рекомендація: для уникнення повторів краще чергувати ці закінчення, надаючи перевагу `-ові, -еві` для першого іменника в реченні: `подякувати **сусідові Данилу**`, `написати **видавцеві Сергію**` (Source 6: 10-klas-ukrajinska-mova-zabolotnij-2018_s0213; Source 10: 11-klas-ukrajinska-mova-avramenko-2019_s0256).

4.  **Систематизація через відміни (6 клас):** Поняття чотирьох відмін іменників вводиться в 6 класі. Це дозволяє систематизувати знання про відмінкові закінчення, групуючи іменники за спільними морфологічними ознаками (Source 2: 6-klas-ukrmova-litvinova-2023_s0150; Source 3: 6-klas-ukrmova-zabolotnyi-2020_s0096). Давальний відмінок розглядається в межах парадигми кожної відміни.

## Повна парадигма (Full Paradigm)

Відмінювання іменників у давальному відмінку залежить від їхньої відміни та групи (твердої, м'якої, мішаної).

### І відміна
(Іменники жіночого, чоловічого та спільного роду на `-а, -я`) (Джерело: 4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0049, ext-other_blogs-46)

| Група | Рід | Однина (кому? чому?) | Множина (кому? чому?) |
| :--- | :--- | :--- | :--- |
| **Тверда** | жін. | сестр**і**, книз**і**, ру**ц**і (чергування `к`→`ц`) | сестрам, книгам |
| (основа на твердий приголосний) | чол. | Микол**і**, старост**і** | Миколам, старостам |
| **М'яка** | жін. | земл**і**, надi**ї**, пiсн**і** | землям, надіям |
| (основа на м'який приголосний) | чол. | Ілл**і** | <!-- VERIFY --> |
| **Мішана** | жін. | груш**і**, тиш**і**, круч**і** | грушам, тишам |
| (основа на шиплячий) | чол. | <!-- VERIFY --> | <!-- VERIFY --> |

**Увага:** В давальному відмінку однини іменників твердої групи відбувається історичне чергування задньоязикових `[г], [к], [х]` на `[з'], [ц'], [с']` перед закінченням `-і` (Source 4: ext-other_blogs-46, Source 37: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0046).
*   *но**г**а* → *но**з**і*
*   *ру**к**а* → *ру**ц**і*
*   *свекру**х**а* → *свекру**с**і*

### ІІ відміна
(Іменники чоловічого роду на `_` (нульове) або `-о`; середнього роду на `-о, -е, -я`) (Джерело: 6-klas-ukrmova-zabolotnyi-2020_s0103, 10-klas-ukrmova-karaman-2018_s0264)

| Рід | Група | Однина (кому? чому?) | Множина (кому? чому?) |
| :--- | :--- | :--- | :--- |
| **Чоловічий** | Тверда | студент**ові** / студент**у**; батьк**ові** / батьк**у** | студентам, батькам |
| | М'яка | учител**еві** / учител**ю**; геро**єві** / геро**ю** | учителям, героям |
| | Мішана | читач**еві** / читач**у**; товариш**еві** / товариш**у** | читачам, товаришам |
| **Середній** | Тверда | міст**у**, сел**у** | містам, селам |
| | М'яка | пол**ю**, мор**ю** | полям, морям |
| | Мішана | плеч**у** | <!-- VERIFY --> |

**Важливо:** Іменники чоловічого роду мають паралельні закінчення **-ові/-у** (тверда група), **-еві/-ю** (м'яка та мішана), **-єві/-ю** (м'яка група після голосного). Стилістично для назв істот перевага надається закінченням `-ові, -еві` (Source 30: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0044).

### ІІІ відміна
(Іменники жіночого роду на `_` (нульове) та слово *мати*) (Джерело: 6-klas-ukrmova-zabolotnyi-2020_s0096)

| Однина (кому? чому?) | Множина (кому? чому?) |
| :--- | :--- |
| радост**і**, любов**і**, ноч**і**, матер**і** | радостям, ночам <!-- VERIFY --> |

### ІV відміна
(Іменники середнього роду на `-а, -я` з суфіксами `-ат-, -ят-, -ен-`) (Джерело: 6-klas-ukrmova-zabolotnyi-2020_s0096, 10-klas-ukrmova-karaman-2018_s0264)

| Однина (кому? чому?) | Множина (кому? чому?) |
| :--- | :--- |
| тел**яті**, ім'**ені**, кошен**яті** | телятам, іменам |

## Частотність і пріоритети (A2 Level)

Для рівня А2 пріоритетним є засвоєння найбільш уживаних форм і конструкцій.

1.  **Найвища пріоритетність: Давальний відмінок займенників.** Конструкції `мені подобається`, `тобі треба`, `йому холодно` є надзвичайно поширеними і часто вивчаються як лексичні одиниці ще до формального вивчення відмінка (Source 42: ext-ulp_youtube-252).
2.  **Висока пріоритетність: Іменники, що позначають людей (адресатів дії).**
    *   **І відміна, однина:** *мамі, сестрі, подрузі, Оксані, Миколі*. Форми на `-і` та з чергуванням приголосних є ключовими.
    *   **ІІ відміна, однина:** *братові/брату, другові/другу, татові/тату, Андрієві/Андрію*. Учень повинен розпізнавати обидві форми як правильні і надавати перевагу `-ові/-еві` для активного вживання.
3.  **Середня пріоритетність: Давальний відмінок множини для назв людей.** Форми *студентам, друзям, дітям* важливі для узагальнень.
4.  **Нижча пріоритетність: Давальний відмінок для неістот.** Засвоюється переважно в сталих виразах: `дякую випадку`, `кінець фільму` (тут родовий, поганий приклад), `радіти сонцю`. Відмінювання іменників ІІІ та IV відмін у давальному відмінку є менш частотним на рівні А2.

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why?) |
| :--- | :--- | :--- |
| Я пишу листа моїй *подругі*. | Я пишу листа моїй **подрузі**. | Не відбулося обов'язкове чергування `г` → `з` перед закінченням `-і` в іменниках І відміни. (Source 37: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0046) |
| Він допомагає *брата*. | Він допомагає **братові** / **брату**. | Дієслово *допомагати* вимагає давального відмінка (`кому?`), а не знахідного (`кого?`). Поширена помилка через інтерференцію англійської (`help someone`). |
| Зателефонуй *директор*. | Зателефонуй **директорові** / **директору**. | Не додано відмінкове закінчення давального відмінка (`-ові` або `-у`). |
| Ми дали квіти *учительці*. | Ми дали квіти **учительці**. | Правильно! Але часто плутають з місцевим відмінком і кажуть *на учительці*. Важливо розрізняти `кому?` (давальний) і `на кому?` (місцевий). |
| Це подарунок для *Оксану*. | Це подарунок для **Оксани**. | Плутанина прийменникових конструкцій. `Для` вимагає родового відмінка. Безприйменникова конструкція з давальним буде: "Я даю подарунок **Оксані**". |
| Він подобається *я*. | **Мені** він подобається. | Конструкція `подобатися` вимагає давального відмінка займенника (`мені`, `тобі`, `йому`...), а не називного. (Source 42: ext-ulp_youtube-252) |

## Деколонізаційні застереження (Decolonization Notes)

Критично важливо викладати українську граматику як самостійну, унікальну систему, уникаючи порівнянь з російською як з "нормою".

1.  **Закінчення `-і` в І відміні:** Наголошуйте, що закінчення `-і` в давальному відмінку однини для іменників І відміни (*сестрі, воді, книзі*) є питомою українською рисою. Це не "виняток" і не "дивна форма". В російській мові тут використовується закінчення `-е` (*сестре, воде, книге*).
2.  **Паралельні форми `-ові` / `-у`:** Акцентуйте, що форми на **-ові, -еві, -єві** є не просто допустимими, а повноцінними, стилістично багатими і дуже поширеними в українській мові, особливо для назв істот (`директорові`, `професорові`, `котові`). Це суттєво відрізняється від російської, де аналогічні форми на `-овичу` (для по батькові) та рідкісні `-ове` є вузько стилістично маркованими, а основною нормою є `-у/-ю` (`директору`, `профессору`). Навчання чергувати ці форми для милозвучності (`братові Сергію`) є ознакою високого володіння саме українською мовою (Source 10: 11-klas-ukrajinska-mova-avramenko-2019_s0256).
3.  **Чергування приголосних:** Явище зміни `г, к, х` на `з, ц, с` перед `-і` (`нозі, руці, мусі`) є глибоко вкоріненим у фонетичній системі української мови. Його слід подавати як закономірний і регулярний процес, а не як складний набір винятків.

## Природні приклади (Natural Examples)

**Група 1: Адресат дії (істоти)**
*   Я напишу листа **другові**. (Джерело: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0045)
*   Галя рекомендує **Тарасу** словник "Лінво". (Джерело: ext-ulp_youtube-252)
*   Моя сестра подарувала **мені** планшет на день народження. (Джерело: ext-ulp_youtube-252)
*   Передай листа **товаришеві Бондаренку**. (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0256)

**Група 2: Стилістичне чергування закінчень**
*   Написати **видавцеві Сергію Данилевському**. (Джерело: 10-klas-ukrmova-zabolotnyi-2018_s0213)
*   Подякувати **сусідові Данилу**. (Джерело: 10-klas-ukrmova-zabolotnyi-2018_s0213)
*   Україн**цеві** Васил**ю** Вірастюку 2004 року присвоєно титул «Найсильніша людина світу». (Джерело: 11-klas-ukrajinska-mova-avramenko-2019_s0256)

**Група 3: Іменники І відміни з чергуванням**
*   Що ти подаруєш **мамі** й **сестрі** на свято? <!-- VERIFY -->
*   Я довіряю своїй **подрузі**. (Джерело: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0068, adapted)
*   На цій **доріжці** завжди багато людей. (приклад на чергування, хоча відмінок місцевий, але правило те ж: `доріжка` -> `доріжці`) <!-- VERIFY -->

**Група 4: Конструкції з `треба`, `варто`, `подобається`**
*   **Тобі** варто встановити цей додаток на телефон. (Джерело: ext-ulp_youtube-252)
*   **Мені** треба купити новий ноутбук. (Джерело: ext-ulp_youtube-252)
*   **Мені** подобається цей фільм. (Джерело: ext-ulp_youtube-252)

## Рекомендації для вправ (Activity Concepts)

*   **Фаза 1: Розпізнавання.**
    *   **Вправи на вибір:** "Я телефоную ... (А) друг, (Б) другу, (В) друга".
    *   **Зіставлення:** Поєднати іменники в називному відмінку з їх формами в давальному (`мама` → `мамі`, `брат` → `братові`).
    *   **Пошук у тексті:** Знайти в короткому тексті всі іменники в давальному відмінку і визначити, на яке питання вони відповідають.

*   **Фаза 2: Контрольоване відтворення.**
    *   **Розкриття дужок:** "Дай цю книгу (сестра)". → "Дай цю книгу **сестрі**".
    *   **Трансформація:** Перетворити речення з родовим відмінком на речення з давальним. "Цей подарунок для (вчитель)". → "Я даю цей подарунок **вчителеві**".
    *   **Побудова речень за зразком:** "Зразок: *Я допомагаю мамі.*". Скласти речення зі словами *друг, тато, подруга*.

*   **Фаза 3: Вільне мовлення.**
    *   **Відповіді на питання:** `Кому ти зазвичай даруєш подарунки?`, `Кому ти допомагаєш удома?`, `Що ти порадиш другові, який хоче вивчити українську?`.
    *   **Ситуативні завдання:** Уявіть, що ви радите другові фільм. Напишіть йому коротке повідомлення. "Привіт, **Андрію**! Раджу **тобі** подивитися..."

## Зв'язки з іншими темами

*   **Попередні теми:** Розуміння **роду іменників** та **числа** є обов'язковим. Базове знання системи **відмінків** (принаймні, називного та знахідного). Знання **І та ІІ відмін** іменників.
*   **Паралельні теми:** Давальний відмінок іменників вивчається разом з **давальним відмінком особових займенників** (`мені, тобі, йому...`).
*   **Наступні теми:** Знання давального відмінка є основою для вивчення **місцевого відмінка**, оскільки деякі форми та правила (напр., чергування приголосних) є спільними. Також це відкриває шлях до складніших дієслівних конструкцій та вираження модальності (`можна`, `треба`).

## Пов'язані статті

*   `grammar/a1/noun-gender`
*   `grammar/a2/declensions-overview`
*   `grammar/a2/dative-pronouns`
*   `grammar/b1/locative-case`

---

### Вікі: grammar/a2/dative-pronouns.md

# Граматика A2: Мені, тобі, йому...



## Як це пояснюють у школі (How Schools Teach This)

Давальний відмінок особових займенників вводиться в українських школах у початкових класах, зазвичай у 4-му класі, як частина вивчення системи відмінків (Source 15, 31, 38).

Основна педагогічна логіка така:
1.  **Назва відмінка**: Назва «Давальний» походить від дієслова «давати» (`давати щось **комусь**`). Це є ключовим, найбільш інтуїтивним прикладом для учнів (Source 5, 41).
2.  **Питання**: Основні питання, на які відповідає давальний відмінок, це **кому? чому?** (Source 9, 15, 31, 41).
3.  **Введення через фрази**: Займенники в давальному відмінку часто вводяться через сталі та високочастотні конструкції. Педагогічний підхід для іноземців, як у подкасті Ukrainian Lessons, починає з фрази **«Мені подобається»** як першого знайомства з давальним відмінком, оскільки вона є надзвичайно поширеною і демонструє непрямий суб'єкт (to me it is pleasing) (Source 5, 45).
4.  **Парадигма**: Учням надають повні таблиці відмінювання особових займенників (я, ти, ми, ви), де вони можуть побачити всі форми, включаючи давальний відмінок: `мені`, `тобі`, `нам`, `вам` (Source 9, 23, 27, 35, 42, 43). Згодом додається 3-тя особа: `йому`, `їй`, `їм` (Source 14, 32, 37, 39).
5.  **Розрізнення**: Наголос робиться на розрізненні давального відмінка від інших, що можуть мати схожі форми або плутатися. Наприклад, `мене` (Родовий/Знахідний) vs. `мені` (Давальний) або `тебе` vs. `тобі` (Source 8, 42). Також пояснюється різниця між Давальним і Місцевим відмінками, які для іменників можуть мати однакове закінчення `-і` (Source 26, 40).

Уроки часто включають вправи на заміну іменника займенником або на постановку займенника в дужках у правильну відмінкову форму (Source 12, 21, 29).

## Повна парадигма (Full Paradigm)

Відмінювання особових займенників у Давальному відмінку є фундаментальним. На відміну від Називного, інші відмінки (непрямі) для 1-ї та 2-ї особи утворюються від іншої основи (Source 21, 22, 32).

| Називний (Хто?) | Давальний (Кому?) | Приклад речення | Джерело |
| :--- | :--- | :--- | :--- |
| **я** | **мені** | *Мені* треба купити новий ноутбук. | (Source 5) |
| **ти** | **тобі** | *Тобі* варто встановити додаток. | (Source 5) |
| **він / воно** | **йому** | Дати *йому* книгу. | (Source 5) |
| **вона** | **їй** | Сказав *їй* зірвати квітку. | (Source 14) |
| **ми** | **нам** | Можна *нам* вам написати? | (Source 5) |
| **ви** | **вам** | Дякую *вам*. | (Source 29) |
| **вони**| **їм** | Потрібно *їм* допомогти. | (Source 20) |

**Важливо:** На відміну від 3-ї особи, займенники 1-ї та 2-ї особи (`мені`, `тобі`, `нам`, `вам`) не мають приставного **н-** після прийменників. Давальний відмінок рідко використовується з прийменниками, але це правило важливе для інших відмінків.

Нижче наведено повну таблицю відмінювання для порівняння.

| Відмінок | 1-ша особа (одн.) | 2-га особа (одн.) | 3-тя особа (одн.) | 1-ша особа (мн.) | 2-га особа (мн.) | 3-тя особа (мн.) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Н.** | я | ти | він, вона, воно | ми | ви | вони |
| **Р.** | мене | тебе | його, її (нього, неї) | нас | вас | їх (них) |
| **Д.** | **мені** | **тобі** | **йому, їй** | **нам** | **вам** | **їм** |
| **Зн.**| мене | тебе | його, її (нього, неї) | нас | вас | їх (них) |
| **Ор.** | мною | тобою | ним, нею | нами | вами | ними |
| **М.** | (на) мені | (на) тобі | (на) ньому, (на) ній | (на) нас | (на) вас | (на) них |

*(За матеріалами джерел 9, 14, 21, 32, 43)*

## Частотність і пріоритети

Для рівня A2/B1 пріоритетними є такі конструкції з Давальним відмінком займенників:

1.  **Безособові конструкції (вираження стану, думки, потреби):** Це найпоширеніший вжиток.
    *   **Подобається/Здається**: `Мені подобається...`, `Мені здається...` (Source 5). Це ключова структура для вираження особистої думки.
    *   **Треба/Потрібно/Варто**: `Мені треба...`, `Тобі варто...` (Source 5). Вираження необхідності або поради.
    *   **Вік**: `Мені 25 років.` <!-- VERIFY -->. Хоча не знайдено в джерелах, це надважлива базова конструкція.
    *   **Емоційний/фізичний стан**: `Мені холодно`, `Мені сумно`, `Мені шкода`. (Source 8: `без тебе буде сумно`).

2.  **Адресат дії (непрямий додаток):** Класична функція Давального відмінка.
    *   **Давати/Дарувати**: `Сестра мені подарувала...`, `Дай мені...` (Source 5).
    *   **Говорити/Казати/Розповідати**: `Скажи мені...`, `Він сказав їй...` (Source 14).
    *   **Радити/Рекомендувати**: `Порадиш мені якийсь [додаток]?` (Source 5).
    *   **Допомагати**: `Допомогти комусь` -> `допомогти тобі`. <!-- VERIFY -->

У розмовній мові конструкції першого типу (`мені подобається`, `тобі треба`) значно переважають за частотністю і мають бути засвоєні в першу чергу.

## Типові помилки L2 (Common L2 Errors)

Англомовні студенти часто припускаються помилок через прямий переклад з англійської та плутанину між українськими відмінками.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| *Я подобаюся музика.* | **Мені** подобається музика. | В українській мові в конструкції `подобатися` логічний суб'єкт (той, хто відчуває) стоїть у Давальному відмінку, а об'єкт симпатії — в Називному. Це безособова конструкція, на відміну від англійської "I like music", де "I" є підметом (Source 5). |
| *Я треба йти.* | **Мені** треба йти. | Модальні слова `треба`, `потрібно`, `варто` вимагають Давального відмінка для позначення особи, яка має потребу. В англійській мові "I need to go" використовує підмет "I" (Source 5). |
| Я бачу **тобі**. | Я бачу **тебе**. | Дієслово `бачити` вимагає прямого додатка у Знахідному відмінку (`кого?`), а не непрямого в Давальному (`кому?`). Це поширена плутанина між формами `тобі` (Д.в.) і `тебе` (Зн.в./Р.в.) (Source 8). |
| Дай **я** книгу. | Дай **мені** книгу. | Дієслово `давати` вимагає Давального відмінка для позначення отримувача. Використання Називного відмінка "я" є грубою помилкою, що ігнорує систему відмінків (Source 5). |
| Він сказав **про неї**. Я сказав **її**. | Він сказав **про неї**. Я сказав **їй**. | Дієслово `казати` без прийменника, коли вказує на адресата, вимагає Давального відмінка (`сказати кому?` -> `їй`). Форма `її` — це Родовий/Знахідний відмінок (`бачу кого?` -> `її`). |

## Деколонізаційні застереження

1.  **Самостійність форм**: Українські особові займенники та їх відмінкові форми (`мені`, `тобі`, `йому`) мають глибоке коріння в давньоруській мові (Old East Slavic) і розвивалися незалежно. Джерела, що аналізують літописи 10-12 століть, показують існування цих форм (`мині`, `тобѣ`, `ѥму`) задовго до формування сучасної російської мови (Source 2, 3, 7). Неприпустимо подавати українські форми як варіації чи "винятки" з російських норм.
2.  **Уникати російських кальок**: Незважаючи на схожість конструкцій `мне нравится` / `мені подобається`, слід наголошувати на унікальному наборі українських дієслів, що керують Давальним відмінком. Наприклад, для вираження думки в українській мові використовується `мені здається`, а не калька з російського `мне кажется`.
3.  **Вимова та наголос**: Слід звернути увагу на правильний наголос у формах `мен**е́**` (Р.в./Зн.в.) vs. `мен**і́**` (Д.в.), `теб**е́**` vs. `тоб**і́**` (Source 32). Це є важливою фонетичною рисою української мови.

## Природні приклади

Приклади згруповано за функцією Давального відмінка.

**Група 1: Вираження стану, потреби, думки (безособові конструкції)**
*   `Мені подобається лінво.` (Source 5) — *Вираження вподобання.*
*   `Мені здається, що планшет — це просто великий смартфон.` (Source 5) — *Вираження думки.*
*   `Ой, а мені треба купити новий ноутбук.` (Source 5) — *Вираження потреби.*
*   `Тобі варто встановити додаток на телефон, це дуже зручно.` (Source 5) — *Надання поради.*
*   `Що ж тобі не подобається в лісі? Мені тут добре, їжі багато!` (Source 12) — *Питання про стан та констатація власного стану.*

**Група 2: Адресат дії (кому щось дають, говорять, радять)**
*   `Мені сестра подарувала [планшет] на день народження.` (Source 5) — *Отримувач подарунка.*
*   `Порадиш мені якийсь [додаток]?` (Source 5) — *Адресат поради.*
*   `Скажи мені, хто твій друг, і я скажу тобі, хто ти.` (Source 14) — *Адресат мовлення.*
*   `Я би тобі сказав щось, та хай тобі скаже хтось.` (Source 11) — *Адресат мовлення.*

**Група 3: У сталих виразах та формулах ввічливості**
*   `Вибач мені.` (Source 29) — *Формула вибачення.*
*   `Дякую вам.` (Source 29) — *Формула подяки.*
*   `Несила мені більше жити в цьому лісі!` (Source 12) — *Вираження неспроможності.*

## Рекомендації для вправ

**Phase 1: Розпізнавання та базове відтворення**
1.  **Вправа "Слухай і знаходь"**: Дати учням текст (або аудіо) і попросити знайти всі займенники в Давальному відмінку. Почати з діалогів, де часто зустрічаються `мені`/`тобі`.
2.  **Вправа "Мені подобається"**: Дати список іменників (музика, спорт, фільми, книжки) і попросити скласти речення за моделлю `Мені подобається... / Мені не подобається...`.

**Phase 2: Контрольована практика**
1.  **Вправа "Заповни пропуски"**: Надати речення з пропущеним займенником, де потрібно вибрати правильну форму (Називний чи Давальний).
    *   *Приклад*: `(___ я/мені) треба більше практикуватися.` -> `Мені...`
2.  **Вправа "Трансформація"**: Дати речення в 1-й особі і попросити переробити його для 2-ї або 3-ї.
    *   *Приклад*: `Мені потрібен словник.` -> `Тобі потрібен словник.` -> `Йому потрібен словник.`

**Phase 3: Вільна практика**
1.  **Вправа "Порадник"**: Учень має дати поради другу, використовуючи конструкцію `Тобі варто...` або `Я раджу тобі...`.
2.  **Ситуативні діалоги**: Розіграти ситуації "в магазині", "планування вечора", "обговорення фільму", де учні змушені використовувати `мені здається`, `тобі пасує`, `нам треба` тощо.
3.  **Вправа "Що кому подарувати?"**: Дати список людей (він, вона, вони) і предметів. Учень має скласти речення, кому і що він хоче подарувати.
    *   *Приклад*: `Я хочу подарувати йому книгу, а їй — квитки в театр.`

## Зв'язки з іншими темами

*   **Передумови**: Учень повинен знати особові займенники в **Називному відмінку** (я, ти, він...).
*   **Паралельне вивчення**: Давальний відмінок займенників є ідеальною точкою входу для вивчення **Давального відмінка іменників**. Логіка питань (`кому? чому?`) та функції (адресат) є однаковими.
*   **Наступні кроки**: Опанувавши Давальний відмінок, учень готовий до порівняння його зі **Знахідним** (`бачу кого?` - `тебе`) та **Родовим** (`немає кого?` - `тебе`), де форми можуть збігатися і викликати плутанину. Також це відкриває шлях до вивчення складніших **безособових конструкцій**.

## Пов'язані статті

*   grammar/a2/dative-nouns
*   grammar/a2/accusative-pronouns
*   grammar/a2/impersonal-constructions
*   grammar/b1/verbs-of-giving-and-telling
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Давальний відмінок іменників чоловічого роду (Dative of Masculine Nouns)` (~650 words)
- `## Давальний відмінок іменників жіночого роду (Dative of Feminine Nouns)` (~500 words)
- `## Давальний відмінок іменників середнього роду (Dative of Neuter Nouns)` (~350 words)
- `## Давальний відмінок у реченні (Dative Nouns in Sentences)` (~500 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 2000 words minimum.

---

## Content Rules

TARGET: 45-65% Ukrainian. THIS IS A HARD GATE — the audit REJECTS modules below 45%.
LANGUAGE ROLES:
- THEORY: English prose for grammar explanations — keep these SHORT (2-3 sentences max per concept).
- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.
- HEADERS: Ukrainian with English in parentheses.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence.
HOW TO REACH 45-65% UKRAINIAN (mandatory techniques):
1. After EVERY grammar explanation, add a «Читаємо українською» block: 4-6 full Ukrainian sentences demonstrating the concept just explained. These are comprehensible input, not exercises.
2. Include 3-4 multi-turn dialogues (6+ lines each) spread through the module. Dialogues are the fastest way to boost Ukrainian content.
3. Pattern boxes showing Ukrainian transformations: «стіл → стола → на столі».
4. Section introductions can be 1-2 Ukrainian sentences before the English theory.
5. :::tip and :::note callout boxes should contain Ukrainian mnemonic phrases.
If your module has long English paragraphs without Ukrainian blocks between them, you are below target. Every English paragraph should be followed by Ukrainian content.
A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles.

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
  1. **At a post office — addressing packages to different people: Студентові Петренку — підручник (m, textbook). Сестрі Олені — листівка (f, postcard). Дитині — іграшка (f, toy).**
     Speakers: Відправник (sender), Працівник пошти
     Why: Dative nouns: студент→студентові, сестра→сестрі, дитина→дитині

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

**Required:** студентові (to the student (dat.)), сестрі (to the sister (dat.)), другові (to the friend (dat.)), подарувати (to give as a gift), показати (to show), написати (to write), розповісти (to tell, to narrate), пояснити (to explain), відповісти (to answer, to reply), закінчення (ending (grammar))
**Recommended:** відміна (declension), чергування (alternation (grammar)), одержувач (recipient), немовля (baby, infant)

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
