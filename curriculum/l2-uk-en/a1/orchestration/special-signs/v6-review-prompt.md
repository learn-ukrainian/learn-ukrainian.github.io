# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 3: Special Signs (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Claude Opus
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-003
level: A1
sequence: 3
slug: special-signs
version: '1.0'
title: Special Signs
subtitle: "Ь, apostrophe, and the voice of consonants"
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
- section: "М'який знак (The Soft Sign — Ь)"
  words: 250
  points:
  - "Ь has no sound. Its job: soften the consonant before it.
    Ukrainian distinguishes hard (тверді) and soft (м'якшені) consonants.
    Захарійчук Grade 1 p.15 notation: hard = [–], soft = [=].
    Common words: день (day), сіль (salt), кінь (horse), мідь (copper).
    The Ь appears only after consonants, never at word start."
  - "Where Ь commonly appears:
    -нь: день, кінь, осінь
    -ль: сіль, біль (pain)
    -ть: мить, путь
    -зь: мазь (ointment)
    Practice: учитель (teacher), батько (father), маленький (small)."
- section: "Апостроф (The Apostrophe)"
  words: 250
  points:
  - "Захарійчук Grade 1 p.97: Apostrophe comes after б, п, в, м, ф, р
    before я, ю, є, ї. It keeps the consonant HARD and gives the vowel
    its full [й] + vowel sound."
  - "Without apostrophe: consonant softens (пісня — Н is soft).
    With apostrophe: consonant stays hard + vowel = two sounds.
    сім'я [сім-йа] (family), м'ясо [м-йасо] (meat),
    п'ять [п-йать] (five), комп'ютер [комп-йутер] (computer).
    Reading practice: п'ять, дев'ять, м'який, м'яч, об'єкт."
- section: "Дзвінкі і глухі (Voiced and Voiceless)"
  words: 250
  points:
  - "Consonants come in voiced-voiceless pairs. Hand on throat test:
    vibration = voiced. Pairs:
    Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч."
  - "Critical difference from Russian: Ukrainian does NOT devoice
    consonants at word end. дуб is [дуб], NOT *[дуп].
    мороз is [мороз], NOT *[морос]. This is authentic Ukrainian."
  - "Minimal pairs for ear training:
    балка (beam) vs палка (stick),
    коза (goat) vs коса (braid)."
- section: "Важкі звуки (Tricky Sounds)"
  words: 250
  points:
  - "И — not English 'ee' or 'i'. Between them. Smile for 'ee' but
    pull tongue back slightly. Practice: бик, лист, зима, тихо, синій."
  - "Г — voiced glottal fricative [ɦ]. NOT Russian hard [g].
    Like saying 'h' but with voice. Words: гарно, гори, голова.
    Ґ = hard [g], only in: ґанок, ґудзик, ґречний."
  - "Р — rolled/trilled, like Spanish. Practice: рука, робота, ранок, риба.
    Even imperfect Р is understood — don't stress about it."
- section: "Підсумок — Summary"
  words: 200
  points:
  - "Self-check: What does Ь do? After which letters does apostrophe appear?
    Name 3 voiced-voiceless pairs. How is Ukrainian Г different from Ґ?
    Read these words: сім'я, день, п'ять, гарно."
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
  - м'який (soft) — apostrophe + soft sign
activity_hints:
- type: quiz
  focus: "Does this word have a soft sign, apostrophe, or neither?"
  items: 8
- type: match-up
  focus: "Match voiced-voiceless pairs: Б↔П, Д↔Т, etc."
  items: 8
- type: fill-in
  focus: "Add the missing Ь or apostrophe: сім_я, ден_, п_ять"
  items: 6
- type: quiz
  focus: "Choose the correct pronunciation for Г vs Ґ words"
  items: 4
connects_to:
- a1-004 (Stress and Melody)
prerequisites:
- a1-002 (Reading Ukrainian)
grammar:
- "Soft sign (Ь) — softens preceding consonant, no sound"
- "Apostrophe — after б,п,в,м,ф,р before я,ю,є,ї (Захарійчук rule)"
- "Voiced/voiceless consonant pairs (8 pairs)"
- "Ukrainian non-devoicing at word end (vs Russian)"
- "Г [ɦ] vs Ґ [g] distinction"
register: розмовний
references:
- title: "Захарійчук Grade 1 (NUS 2025), p.97"
  notes: "Apostrophe rule: after б,п,в,м,ф,р before я,ю,є,ї."
- title: "Захарійчук Grade 1 (NUS 2025), p.15"
  notes: "Hard [–] vs soft [=] consonant notation."
- title: "Большакова Grade 1, p.45-47"
  notes: "Тверді і пом'якшені приголосні звуки."
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
  relevant:
    Ь: https://www.youtube.com/watch?v=cJlal8XKBxo
    Г: https://www.youtube.com/watch?v=gVnclpSI0DU
    Ґ: https://www.youtube.com/watch?v=gNjHqjTW9WQ
    Р: https://www.youtube.com/watch?v=fMGsQ5KPQgg
    И: https://www.youtube.com/watch?v=W-1rCu0indE

</plan_content>

## Generated Content

<generated_module_content>
<!-- TAB:Урок -->

## М'яки́й знак (The Soft Sign — Ь)

Look at these two words: **рис** (rice) and **рись** (lynx). Same letters, one tiny addition — **Ь** — and the meaning changes completely. This single letter, called **м'який знак** (the soft sign), has no sound of its own. Its only job is to soften the consonant that comes before it. Ukrainian distinguishes between **тверді** (hard) and **пом'я́кшені** (softened) consonants — a distinction that shapes how every word sounds. Ukrainian Grade 1 textbooks mark this difference with a simple notation from Захарійчук: hard consonants get [–], soft consonants get [=]. So **рис** is [–•–] — all hard — while **рись** is [–•=] — the final consonant softened. One important rule: **Ь** never appears at the beginning of a word. It always follows a consonant.

Where does **Ь** show up most often? In certain consonant endings that you will see again and again. The ending **-нь** appears in **день** (day), **кінь** (horse), **о́сінь** (autumn), and **тінь** (shadow). The ending **-ль** gives us **сіль** (salt) and **біль** (pain). You will find **-ть** in **мить** (moment) and **-зь** in **мазь** (ointment). But **Ь** also appears inside words, not just at the end: **учи́тель** (teacher), **ба́тько** (father), **мале́нький** (small), **стіле́ць** (chair). A Grade 1 textbook poem by Га́нна Чу́бач captures this perfectly — **Ь** speaks for itself: "Зву-ки зм'як-шу-вать у-мі-ю" — "I know how to soften sounds." And the poem proves it with a clever example: remove **Ь** from **ка́мінь** (stone) and you get **камі́н** (fireplace). Different word, different meaning — all because of one silent letter.

Read these words aloud: **день**, **сіль**, **кінь**, **мідь** (copper), **батько**, **маленький**, **пальто́** (coat), **о́лень** (deer). Notice how your tongue shifts position on the softened consonant — it presses slightly higher and more forward in the mouth. That subtle shift is the sound of **Ь** doing its work.

:::fill-in
title: "Де потрі́бен Ь? (Where is Ь needed?)"
---
- sentence: "ден___"
  answer: "день"
- sentence: "сіл___"
  answer: "сіль"
- sentence: "кін___"
  answer: "кінь"
- sentence: "бат___ко"
  answer: "батько"
- sentence: "учител___"
  answer: "учитель"
- sentence: "мален___кий"
  answer: "маленький"
:::

## Апо́стро́ф (The Apostrophe)

The apostrophe in Ukrainian is not a letter — it is a written sign that appears between a consonant and a vowel, and it does the exact opposite of **Ь**. Where **Ь** softens a consonant, the apostrophe blocks softening and keeps the consonant hard. The rule, straight from Захарійчук Grade 1 (p. 97): the apostrophe appears after the consonants **б**, **п**, **в**, **м**, **ф**, **р** — and only before the vowels **я**, **ю**, **є**, **ї**. When the apostrophe is present, the consonant stays hard, and the vowel gets its full two-sound value: the hidden "й" sound plus the vowel itself. Without the apostrophe, the consonant would simply soften, and the vowel would lose that extra sound.

The textbook shows this beautifully with a real pair: **мо́ря** (of the sea) — here **р** is soft, and **я** is just one sound. But **подві́р'я** (yard) — here **р** stays hard, and **я** splits into two sounds. Feel the difference. Now look at key vocabulary words with their pronunciation breakdown: **сім'я́** (family) — the **м** stays hard, and **я** sounds like "йа." **М'я́со** (meat) — hard **м**, then "йа." **П'ять** (five) — hard **п**, then "йа." **Комп'ю́тер** (computer) — hard **п**, then "йу." The Grade 2 textbook asks a perfect diagnostic question: when you write an apostrophe in **м'я́та** (mint), does it mean the **м** is soft or hard? The answer is hard — and the **я** carries two sounds.

Practice reading these apostrophe words from the textbooks: **п'ять**, **де́в'ять** (nine), **м'який** (soft), **м'яч** (ball), **об'є́кт** (object), **сім'я**, **пі́р'я** (feathers), **здоро́в'я** (health), **п'я́тниця** (Friday), **ім'я́** (name). Pronounce the consonant before each apostrophe firmly — keep it hard — then let the vowel ring with its full sound.

:::fill-in
title: "Ь чи апостроф? (Soft sign or apostrophe?)"
---
- sentence: "сім___я"
  answer: "сім'я"
- sentence: "ден___"
  answer: "день"
- sentence: "п___ять"
  answer: "п'ять"
- sentence: "бат___ківщина"
  answer: "батьківщина"
- sentence: "м___ясо́"
  answer: "м'ясо"
- sentence: "осін___"
  answer: "осінь"
:::

## Дзвінкі́ і глухі́ (Voiced and Voiceless)

Place your hand on your throat and say **б**. Feel the vibration? That is a **дзвінки́й** (voiced) consonant — your vocal cords are working. Now say **п**. The vibration stops. That is a **глухи́й** (voiceless) consonant — same mouth position, but the vocal cords stay silent. Ukrainian consonants come in eight voiced-voiceless pairs:

**Б–П**, **Д–Т**, **Г–Х**, **Ґ–К**, **З–С**, **Ж–Ш**, **ДЗ–Ц**, **ДЖ–Ч**

Notice that **ДЗ** and **ДЖ** are each a single sound written with two letters — you already encountered this in the alphabet.

Here is one of the most important pronunciation rules in Ukrainian, and it sets Ukrainian apart sharply. Ukrainian does NOT devoice consonants at the end of a word. The word **дуб** (oak) is pronounced [дуб] — the final **б** stays voiced. NOT *[дуп]. The word **моро́з** (frost) is pronounced [мороз] — the final **з** stays voiced. NOT *[морос]. The word **хліб** (bread) is [хліб], NOT *[хліп]. This is authentic Ukrainian pronunciation. If you have been exposed to Russian or Russian-influenced teaching materials, you must unlearn devoicing. Every final consonant keeps its voiced quality in Ukrainian — this is a hallmark of natural Ukrainian speech.

Try these minimal pairs — words that differ only by a voiced or voiceless consonant: **ба́лка** (beam) vs **па́лка** (stick), **коза́** (goat) vs **коса** (braid). Say each pair aloud with your hand on your throat. Feel the vibration switch on and off between the first consonant of each word.

:::match-up
title: "Дзвінкий ↔ Глухий (Match voiced-voiceless pairs)"
---
- left: "Б"
  right: "П"
- left: "Д"
  right: "Т"
- left: "Г"
  right: "Х"
- left: "Ґ"
  right: "К"
- left: "З"
  right: "С"
- left: "Ж"
  right: "Ш"
- left: "ДЗ"
  right: "Ц"
- left: "ДЖ"
  right: "Ч"
:::

:::quiz
title: "Дзвінкий чи глухий? (Voiced or voiceless?)"
---
- q: "Б in балка?"
  o: ["Дзвінкий (voiced)", "Глухий (voiceless)"]
  a: 0
- q: "С in коса?"
  o: ["Дзвінкий (voiced)", "Глухий (voiceless)"]
  a: 1
- q: "З in зима́?"
  o: ["Дзвінкий (voiced)", "Глухий (voiceless)"]
  a: 0
- q: "Ш in шум?"
  o: ["Дзвінкий (voiced)", "Глухий (voiceless)"]
  a: 1
- q: "Г in га́рно?"
  o: ["Дзвінкий (voiced)", "Глухий (voiceless)"]
  a: 0
- q: "Т in ти́хо?"
  o: ["Дзвінкий (voiced)", "Глухий (voiceless)"]
  a: 1
- q: "ДЖ in джміль?"
  o: ["Дзвінкий (voiced)", "Глухий (voiceless)"]
  a: 0
- q: "Ц in цвях?"
  o: ["Дзвінкий (voiced)", "Глухий (voiceless)"]
  a: 1
:::

## Важкі́ зву́ки (Tricky Sounds)

**И** — the vowel that trips up every English speaker. It is not English "ee" (that sound is too high and too far forward — in Ukrainian, that is **І**). And it is not the short English "i" in "bit" (that sound is too lax). Ukrainian **И** sits right between them. To find it, start with an "ee" smile, then pull your tongue slightly back and down. The sound drops just a little — not as bright, not as tense. Practice words: **бик** (bull), **лист** (leaf), **зима** (winter), **тихо** (quietly), **си́ній** (blue). Now compare the pair **і** vs **и**: **ліс** (forest) vs **лис** (fox). Different vowel, completely different meaning. **И** requires deliberate, focused practice — but your ear will learn to hear the distinction quickly.

**Г** — the signature Ukrainian sound, a voiced glottal fricative. This is NOT the Russian hard "g." Imagine saying English "h," but turning on your voice — that breathy, vibrating sound is Ukrainian **Г**. Words: **гарно** (nicely), **гора́** (mountain), **голова́** (head), **гаря́чий** (hot). Now meet **Ґ** — the actual hard "g" sound, which exists only in a small set of Ukrainian words: **ґа́нок** (porch), **ґу́дзик** (button), **ґре́чний** (polite). The **Г**/**Ґ** distinction is uniquely Ukrainian. Confusing them marks non-native speech immediately — so pay attention to which letter a word uses.

**Р** — rolled and trilled, similar to Spanish or Italian R. The tip of the tongue vibrates against the ridge behind the upper teeth. Practice: **рука́** (hand), **робо́та** (work), **ра́нок** (morning), **ри́ба** (fish), **рік** (year). Even an imperfect **Р** is understood — do not let it block your communication. It improves naturally with practice and time.

:::quiz
title: "Г чи Ґ? (Г or Ґ?)"
---
- q: "How is Г in гарно pronounced?"
  o: ["Like a voiced 'h' (breathy)", "Like a hard 'g'"]
  a: 0
- q: "How is Ґ in ґудзик pronounced?"
  o: ["Like a voiced 'h' (breathy)", "Like a hard 'g'"]
  a: 1
- q: "Which letter is in the word гора (mountain)?"
  o: ["Г (voiced h)", "Ґ (hard g)"]
  a: 0
- q: "Which letter is in the word ґанок (porch)?"
  o: ["Г (voiced h)", "Ґ (hard g)"]
  a: 1
:::


### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

Four tools now sit in your toolkit. **М'який знак (Ь)** softens the consonant before it — no sound of its own, just a quiet instruction: **день**, **сіль**, **кінь**. Remove it, and the word changes: **камінь** becomes **камін**. The **apostrophe** does the opposite — after **б**, **п**, **в**, **м**, **ф**, **р** and before **я**, **ю**, **є**, **ї**, it keeps the consonant hard and lets the vowel carry its full two-sound value: **сім'я**, **м'ясо**, **п'ять**. Voiced consonants vibrate (**Б**, **Д**, **Г**), voiceless ones do not (**П**, **Т**, **Х**) — and unlike some other languages, Ukrainian keeps voiced consonants voiced even at the end of a word. **Дуб** stays [дуб]. And the tricky sounds — **И** (between "ee" and "i"), **Г** (a voiced "h"), **Ґ** (a hard "g"), **Р** (rolled) — are the sounds that will make your Ukrainian authentic.

Test yourself. What does **Ь** do to a consonant? After which six letters can an apostrophe appear? Name three voiced-voiceless pairs. How is **Г** different from **Ґ**? Now read these words aloud: **сім'я**, **день**, **п'ять**, **гарно**, **риба**, **ґудзик**. If any word feels uncertain, go back and revisit that section above.

What comes next? Module 4 — **На́голос** (Stress and Melody). Now that you know the individual sounds, the next step is where the stress falls in Ukrainian words and how it changes meaning. **Наголос** is the heartbeat of Ukrainian — it makes words come alive.


<!-- TAB:Словник -->

### Обов'язкові слова — Required words

| Слово | Переклад | Частина мови | Рід |
|-------|----------|-------------|-----|
| **сім'я** | family | ім. | ж. |
| **день** | day | ім. | ч. |
| **сіль** | salt | ім. | ж. |
| **м'ясо** | meat | ім. | с. |
| **п'ять** | five | числ. |  |
| **гарно** | nicely, beautifully | присл. |  |
| **риба** | fish | ім. | ж. |

### Рекомендовані слова — Recommended words

| Слово | Переклад | Частина мови | Рід |
|-------|----------|-------------|-----|
| **батько** | father, formal | ім. | ч. |
| **учитель** | teacher | ім. | ч. |
| **дев'ять** | nine | числ. |  |
| **комп'ютер** | computer | ім. | ч. |
| **м'який** | soft | прикм. |  |

### Додаткові слова з уроку — Additional words from the lesson

| Слово | Переклад | Частина мови | Рід |
|-------|----------|-------------|-----|
| **рис** | rice | ім. | ч. |
| **рись** | lynx | ім. | ж. |
| **тверді** | hard | прикм. |  |
| **кінь** | horse | ім. | ч. |
| **тінь** | shadow | ім. | ж. |
| **біль** | pain | ім. | ч. |
| **мить** | moment | ім. | ж. |
| **мазь** | ointment | ім. | ж. |
| **мідь** | copper | ім. | ж. |
| **м'яч** | ball | ім. | ч. |
| **дуб** | oak | ім. | ч. |
| **хліб** | bread | ім. | ч. |
| **коса** | braid | ім. | ж. |
| **бик** | bull | ім. | ч. |
| **лист** | leaf | ім. | ч. |
| **зима** | winter | ім. | ж. |
| **тихо** | quietly | присл. |  |
| **ліс** | forest | ім. | ч. |
| **лис** | fox | ім. | ч. |
| **рік** | year | ім. | ч. |
| **маленький** |  | прикм. |  |
| **камінь** |  | ім. | ч. |
| **камін** |  | ім. | ч. |
| **ґудзик** |  | ім. | ч. |
| **Наголос** | the heartbeat of Ukrainian — it makes words come alive | присл. |  |

### Вирази — Expressions

| Вираз | Переклад |
|-------|----------|
| **м'який знак** | the soft sign |


<!-- TAB:Зошит -->

:::note
Розширені вправи для цього уроку ще в розробці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

- Захарійчук Grade 1 (NUS 2025), p.97
  _Apostrophe rule: after б,п,в,м,ф,р before я,ю,є,ї._
- Захарійчук Grade 1 (NUS 2025), p.15
  _Hard [–] vs soft [=] consonant notation._
- Большакова Grade 1, p.45-47
  _Тверді і пом'якшені приголосні звуки._
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

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence.

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

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
```


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 105 words | Not found: 42 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Апо — NOT IN VESUM
  ✗ Большакова — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Комп'ю — NOT IN VESUM
  ✗ М'я — NOT IN VESUM
  ✗ М'яки — NOT IN VESUM
  ✗ в'я — NOT IN VESUM
  ✗ в'ять — NOT IN VESUM
  ✗ вать — NOT IN VESUM
  ✗ гаря — NOT IN VESUM
  ✗ глухи — NOT IN VESUM
  ✗ дзик — NOT IN VESUM
  ✗ здоро — NOT IN VESUM
  ✗ камі — NOT IN VESUM
  ✗ кшені — NOT IN VESUM
  ✗ лень — NOT IN VESUM
  ✗ лка — NOT IN VESUM
  ✗ м'я — NOT IN VESUM
  ✗ морос — NOT IN VESUM
  ✗ мінь — NOT IN VESUM
  ✗ нна — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ нький — NOT IN VESUM
  ✗ об'є — NOT IN VESUM
  ✗ п'я — NOT IN VESUM
  ✗ подві — NOT IN VESUM
  ✗ пом'я — NOT IN VESUM
  ✗ потрі — NOT IN VESUM
  ✗ прикм — NOT IN VESUM
  ✗ присл — NOT IN VESUM
  ✗ р'я — NOT IN VESUM
  ✗ рно — NOT IN VESUM
  ✗ стро — NOT IN VESUM
  ✗ стіле — NOT IN VESUM
  ✗ сінь — NOT IN VESUM
  ✗ тель — NOT IN VESUM
  ✗ тниця — NOT IN VESUM
  ✗ тько — NOT IN VESUM
  ✗ хліп — NOT IN VESUM
  ✗ числ — NOT IN VESUM
  ✗ чний — NOT IN VESUM
  ✗ ґре — NOT IN VESUM

Sample of verified words (all confirmed to exist in Ukrainian):
  ✓ Важкі → lemma: важкий, POS: adj
  ✓ Вираз → lemma: вираз, POS: noun
  ✓ Вирази → lemma: вираз, POS: noun
  ✓ Відео → lemma: відео, POS: noun
  ✓ Глухий → lemma: глухий, POS: adj
  ✓ Дзвінкий → lemma: дзвінкий, POS: adj
  ✓ Дзвінкі → lemma: дзвінкий, POS: adj
  ✓ Додаткові → lemma: додатковий, POS: adj
  ✓ Дуб → lemma: дуб, POS: noun
  ✓ Зву → lemma: звати, POS: verb
  ✓ Зошит → lemma: зошит, POS: noun
  ✓ М'який → lemma: м'який, POS: adj
  ✓ Наголос → lemma: наголос, POS: adv
  ✓ Обов'язкові → lemma: обов'язковий, POS: adj
  ✓ П'ять → lemma: п'ять, POS: numr
  ✓ Переклад → lemma: переклад, POS: noun
  ✓ Повний → lemma: повний, POS: adj
  ✓ Підсумок → lemma: підсумок, POS: noun
  ✓ Рекомендовані → lemma: рекомендований, POS: adj
  ✓ Ресурси → lemma: ресурс, POS: noun
  ✓ Розширені → lemma: розширений, POS: adj
  ✓ Рід → lemma: рід, POS: noun
  ✓ Словник → lemma: словник, POS: noun
  ✓ Слово → lemma: слово, POS: noun
  ✓ Урок → lemma: урка, POS: noun
  ✓ Частина → lemma: частина, POS: noun
  ✓ апостроф → lemma: апостроф, POS: noun
  ✓ балка → lemma: балка, POS: noun
  ✓ батько → lemma: батько, POS: noun
  ✓ батьківщина → lemma: батьківщина, POS: noun
  ✓ бач → lemma: бачити, POS: verb
  ✓ бен → lemma: бен, POS: part
  ✓ бик → lemma: бик, POS: noun
  ✓ біль → lemma: біль, POS: noun
  ✓ вправи → lemma: вправа, POS: noun
  ✓ гарно → lemma: гарно, POS: adv
  ✓ глухий → lemma: глухий, POS: adj
  ✓ глухі → lemma: глухий, POS: adj
  ✓ голова → lemma: голова, POS: noun
  ✓ голос → lemma: голос, POS: noun
  ✓ гора → lemma: гора, POS: noun
  ✓ дев'ять → lemma: дев'ять, POS: numr
  ✓ день → lemma: день, POS: noun
  ✓ джміль → lemma: джміль, POS: noun
  ✓ дзвінки → lemma: дзвінка, POS: noun
  ✓ для → lemma: для, POS: prep
  ✓ дуб → lemma: дуб, POS: noun
  ✓ дуп → lemma: дупа, POS: noun
  ✓ зву → lemma: звати, POS: verb
  ✓ звуки → lemma: звук, POS: noun

</vesum_verification>