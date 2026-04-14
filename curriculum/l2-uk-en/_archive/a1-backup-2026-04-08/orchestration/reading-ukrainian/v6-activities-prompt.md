<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/reading-ukrainian.yaml` file for module **2: Reading Ukrainian** (a1).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: count-syllables -->`
- `<!-- INJECT_ACTIVITY: match-up -->`
- `<!-- INJECT_ACTIVITY: divide-words -->`
- `<!-- INJECT_ACTIVITY: quiz -->`
- `<!-- INJECT_ACTIVITY: odd-one-out -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Поділи слова на склади: мо-ло-ко, ап-те-ка, у-ні-вер-си-тет'
  items: 8
  type: divide-words
- focus: Порахуй склади — скільки голосних, стільки й складів
  items: 8
  type: count-syllables
- focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 6
  type: match-up
- focus: Read the word and choose its meaning
  items: 6
  type: quiz
- focus: Яке слово зайве? — by syllable count (односкладове серед двоскладових)
  items: 6
  type: odd-one-out


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- університет (university) — long word practice
- бібліотека (library) — 5 syllables
- фотографія (photography) — long word with Ф
- шоколад (chocolate) — Ш + О + К combination
required:
- яблуко (apple) — Я at word start = [йа]
- молоко (milk) — 3 syllables, all simple vowels
- людина (person) — Л + Ю combination
- вулиця (street) — Ц sound practice
- столиця (capital) — Київ — столиця України
- каша (porridge) — Ш sound practice
- пісня (song) — softening by Я after consonant


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
<!-- TAB:Урок -->

## Склади (Syllables)

Every Ukrainian first-grader learns one golden rule before reading a single word. The textbook states it plainly: **«У сло́ві сті́льки складів, скі́льки голосни́х зву́ків»** — a word has as many syllables as it has vowel sounds. This rule never breaks. Look at **ма́ма** (mother): two vowels, А and А, so two syllables — **ма-ма**. Now **молоко́** (milk): three vowels, О, О, О — three syllables, **мо-ло-ко**. And **банк** (bank): one vowel, А — one syllable, just **банк**. Count the vowels, count the syllables. Every time.

> **Марко́:** Скільки складів у слові "молоко"? *(How many syllables in the word "moloko"?)*
> **Аня:** Три голосні́ — О, О, О. О́тже, три склади: мо-ло-ко! *(Three vowels — O, O, O. So, three syllables: mo-lo-ko!)*
> **Марко:** Пра́вильно! А "банк"? *(Correct! And "bank"?)*
> **Аня:** Ті́льки оди́н! *(Only one!)*

With that rule in hand, Ukrainian textbooks teach a four-step method called **звукови́й ана́ліз слова́** (sound analysis of a word). Большако́ва's Grade 1 textbook (p.29) lays it out: (1) **Визнача́ю голосні зву́ки** — find all the vowels in the word. (2) **Ділю́ сло́во на склади** — split the word into syllables, one vowel per syllable. Ukrainian syllables tend to be open (ending in a vowel) — this process is called **складопо́діл** (syllable division). (3) **Ста́влю на́голос** — mark which syllable carries the stress. (4) **Познача́ю при́голосні звуки** — identify consonants as hard or soft. Walk through it with **мама** (mother): vowels А, А → two syllables **ма-ма** → stress on the first syllable → both М sounds are hard. Now **апте́ка** (pharmacy): vowels А, Е, А → three syllables **а-пте-ка** → stress on the second syllable → consonants П, Т, К are hard.

For reading, apply звуковий аналіз as a practical strategy: (1) spot the vowels, (2) split into syllables, (3) read each syllable aloud slowly, (4) blend the syllables together at natural speed. Try it: **а-пте-ка** → а... пте... ка → **аптека**. Done.

Here is a physical trick from Кравцо́ва's Grade 2 textbook (p.13): place your palm under your chin and say the word aloud. Each time your chin touches your hand, that is one syllable. Try it with **мо-ло-ко** — you should feel three touches.

Ukrainian Grade 1 textbooks (Захарійчук, p.15) use a simple notation for sound analysis: **[●]** marks a vowel sound, **[—]** marks a hard consonant, and **[=]** marks a soft consonant. For **мама**: [— ● | — ●] — two hard consonants, two vowels, two syllables. For **пі́сня**: [— ● | — = ●] — the Н before Я is soft. Every Ukrainian child learns these symbols in first grade.

Ukrainian children build reading skill through **складові ланцюжки́** (syllable chains). Start with one consonant and cycle through vowels: **М → ма, мо, му, ми, мі, ме**. Then reverse: **ам, ом, ум**. Then build words from the chains: **ма-ма**, **мо-ло-ко**. Add a second consonant: **Т → та, то, ту, ти, ті, те**. Now combine: **та-то**, **мо-ло-то**. This is bottom-up reading: sound → syllable → word.

This method conquers even intimidating long words. Take **шокола́д** (chocolate): three vowels О, О, А give **шо-ко-лад** — three syllables. **Університе́т** (university): five vowels У, І, Е, И, Е give **у-ні-вер-си-тет** — five syllables. **Бібліоте́ка** (library): five vowels І, І, О, Е, А give **бі-блі-о-те-ка** — five syllables. A word that looked impossible becomes five manageable pieces. The rule never fails: count the vowels, and the word opens up.

<!-- INJECT_ACTIVITY: count-syllables -->

## Голосні лі́тери (Vowel Letters)

You already know from M01 that Ukrainian has six vowel sounds but ten vowel letters. The first six are the simple vowels — each letter makes exactly one sound, every time, no surprises. **А** sounds like the "a" in "father" — **аптека** (pharmacy). **О** as in "or" — **молоко** (milk). **У** as in "moon" — **рука́** (hand). **Е** is between English "e" in "met" and "a" in "cat" — **ве́чір** (evening). **И** is a sound English does not have, deeper and more central than "i" — **кит** (whale). **І** is a high front sound, close to "ee" in "see" — **кіт** (cat). These six are completely reliable: what you see is what you say.

The remaining four vowel letters are called iotated vowels: **Я**, **Ю**, **Є**, **Ї**. They follow a two-sound rule. When **Я** appears at the start of a word or after another vowel, it produces two sounds — [й] + [а]. Say **я́блуко** (apple): the Я at the beginning gives [йа], so you hear [йа]-блу-ко. The same happens in **моя́** (my, feminine): мо-[йа]. But when **Я** comes after a consonant, it does something different — it softens that consonant and adds only [а]. In **пісня** (song), the Н before Я becomes soft. The same pattern applies to **Ю** ([йу] at word start, softening + [у] after consonant) and **Є** ([йе] at word start, softening + [е] after consonant). Look at **люди́на** (person): Л is softened by Ю. In **вечі́рнє** (evening, neuter adjective), Н is softened by Є.

<!-- INJECT_ACTIVITY: match-up -->

**Ї** stands apart. It always produces two sounds — [й] + [і] — with zero exceptions. **Ї** never appears directly after a consonant, so it never softens anything. You find it at the start of a word (**їжа́к** — hedgehog), after a vowel (**краї́на** — country), or after an apostrophe. **Ї** is distinctly Ukrainian — Russian has no equivalent letter.

Now, the critical minimal pairs: **И** vs **І**. These two sounds distinguish meaning. **Кит** (whale) vs **кіт** (cat). **Дим** (smoke) vs **дім** (house). The difference between [и] (more central, deeper) and [і] (high, front) changes the word entirely. They are two separate phonemes — never interchangeable. Listen carefully to model pronunciations and practice hearing the contrast before you drill.

<!-- INJECT_ACTIVITY: divide-words -->

## Чита́ння слів (Reading Words)

The syllable method is a scaffold, not a permanent crutch. The goal is to internalize the rhythm so you stop reading letter-by-letter and start reading syllable-by-syllable, then word-by-word. Here is the reading strategy in order: (1) spot the vowels — they are the cores of each syllable. (2) Build the consonant clusters around them. (3) Read syllable-by-syllable. (4) Repeat until the word flows at natural speed. Try it with **кни́га** (book): vowels И and А give two syllables — **кни-га**. Read each piece, then blend: **книга**.

Ukrainian words follow recognizable patterns. The easiest pattern alternates consonant-vowel: **мама** (mother), **та́то** (father), **ка́ша** (porridge), **вода́** (water), **рука** (hand), **ха́та** (house), **коза́** (goat). These words practically read themselves — each syllable is open, ending on a vowel. Slightly harder are words with consonant clusters before a vowel: **шко́ла** (school), **книга** (book). And then closed-syllable words, where a syllable ends on a consonant: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank). Practice each group separately before mixing them. Most Ukrainian syllables are open — ending in a vowel — which makes blending easier than you might expect.

<!-- INJECT_ACTIVITY: quiz -->

Time to read. Start with two-syllable words. Read each one twice — first split, then blended:

**ма-ма** → **мама** (mother). **та-то** → **тато** (father). **во-да** → **вода** (water). **ру-ка** → **рука** (hand). **ха-та** → **хата** (house). **ка-ша** → **каша** (porridge).

Now three-syllable words. Split first, then blend:

**а-пте-ка** → **аптека** (pharmacy). **мо-ло-ко** → **молоко** (milk). **лю-ди-на** → **людина** (person). **ву-ли-ця** → **ву́лиця** (street). **сто-ли-ця** → **столи́ця** (capital) — **Ки́їв** (Kyiv) is **столиця** Украї́ни.

Now the long words. Count the vowels, split, and conquer:

**у-ні-вер-си-тет** → **університет** (university) — five syllables. **бі-блі-о-те-ка** → **бібліотека** (library) — five syllables. **фо-то-гра-фі-я** → **фотогра́фія** (photography) — five syllables. These look intimidating, but the vowel-counting method handles them completely. Finish with Ukrainian city names as a confidence-builder: **Ки-їв** (Kyiv — note the Ї), **О-де-са** (Odesa), **Хар-ків** (Kharkiv), **Дні-про** (Dnipro), **Пол-та-ва** (Poltava).

Three special combinations appear in Ukrainian words that you should recognize now. They will be drilled thoroughly in M03 — today, just notice them when they appear.

First: **Щ** always reads as [шч] — one letter, two sounds. **Що** means "what," **ще** means "still" or "more." Never read Щ as [ш] alone.

Second: **Ь** (the soft sign, **м'яки́й знак**) has no sound of its own. It only softens the consonant before it. **День** (day) — the Н is soft. **Сіль** (salt) — the Л is soft. **Кінь** (horse) — the Н is soft. Think of Ь as a silent softener.

Third: the apostrophe (**'**) separates — it prevents the iotated vowel from softening the preceding consonant. **Сім'я́** (family) — the М stays hard, then Я gives [йа]. **М'я́со** (meat) — same pattern. **П'ять** (five) — П stays hard. These three features will be explored fully in M03; for now, recognize them when you see them.

> **Аня:** Бі-блі-о-те-ка... **бібліотека**! *(Library!)*
> **Марко:** Так! А це? *(Yes! And this?)*
> **Аня:** Яб-лу-ко... **яблуко**! *(Apple!)*
> **Марко:** А це — **шоколад**! *(And this is chocolate!)*

Аня uses the syllable method — splitting each word, then blending. Марко confirms and adds a new word. This is exactly how the method works in practice: slow and careful at first, then faster with each repetition.

<!-- INJECT_ACTIVITY: odd-one-out -->

## Підсумок — Summary

Self-check — answer each question before reading the answer:

- **How do you count syllables in a Ukrainian word?** → Count the vowels. Each vowel = one syllable. The rule never breaks.
- **What are the 6 vowel sounds?** → [а], [о], [у], [е], [и], [і].
- **Name the 4 iotated vowel letters.** → **Я**, **Ю**, **Є**, **Ї**.
- **What do Я, Ю, Є do at the start of a word?** → They produce two sounds: Я = [й] + [а], Ю = [й] + [у], Є = [й] + [е].
- **What does Ї always produce?** → Always [й] + [і] — two sounds, no exceptions.
- **What does Ь do?** → It softens the consonant before it but has no sound of its own.
- **What does the apostrophe do?** → It separates the consonant from a following iotated vowel, preventing softening.
- **Read this word and count syllables: бібліотека.** → **Бі-блі-о-те-ка**. Five syllables — five vowels: І, І, О, Е, А.


<!-- TAB:Словник -->

### Обов'язко́ві та рекомендо́вані слова

| Слово | Переклад | Части́на мо́ви | Рід |
|-------|----------|-------------|-----|
| **університе́т** | university | ім. | ч. |
| **бібліоте́ка** | library | ім. | ж. |
| **фотогра́фія** | photography | ім. | ж. |
| **шокола́д** | chocolate | ім. | ч. |
| **я́блуко** | apple | ім. | с. |
| **молоко́** | milk | ім. | с. |
| **люди́на** | person | ім. | ж. |
| **ву́лиця** | street | ім. | ж. |
| **столи́ця** | capital (city) | ім. | ж. |
| **ка́ша** | porridge | ім. | ж. |
| **пі́сня** | song | ім. | ж. |
| **ма́ма** | mother | ім. | ж. |
| **та́то** | father | ім. | ч. |
| **банк** | bank | ім. | ч. |
| **апте́ка** | pharmacy | ім. | ж. |
| **рука́** | hand | ім. | ж. |
| **ве́чір** | evening | ім. | ч. |
| **кит** | whale | ім. | ч. |
| **кіт** | cat | ім. | ч. |
| **їжа́к** | hedgehog | ім. | ч. |
| **краї́на** | country | ім. | ж. |
| **дим** | smoke | ім. | ч. |
| **кни́га** | book | ім. | ж. |
| **вода́** | water | ім. | ж. |
| **ха́та** | house, cottage | ім. | ж. |
| **коза́** | goat | ім. | ж. |
| **шко́ла** | school | ім. | ж. |
| **ліс** | forest | ім. | ч. |
| **дуб** | oak | ім. | ч. |
| **хліб** | bread | ім. | ч. |
| **що** | what | спол. |  |
| **ще** | still, more, yet | присл. |  |
| **день** | day | ім. | ч. |
| **кінь** | horse | ім. | ч. |
| **сім'я́** | family | ім. | ж. |
| **м'я́со** | meat | ім. | с. |
| **п'ять** | five | числ. |  |
| **моя́** | my (feminine) | прикм. |  |
| **так** | yes | присл. |  |
| **Ки́їв** | Kyiv | ім. |  |
| **Оде́са** | Odesa |  |  |
| **Харків** | Kharkiv |  |  |
| **Дніпро́** | Dnipro |  |  |
| **Полта́ва** | Poltava |  |  |
| **склади** | syllables | ім. |  |
| **голосні́** | vowels | прикм. |  |
| **складопо́діл** | syllable division | ім. | ч. |

### Ви́рази

| Ви́раз | Переклад |
|-------|----------|
| **м'який знак** | soft sign (the letter Ь) |
| **звуковий аналіз слова** | sound analysis of a word |
| **столиця України** | capital of Ukraine |

### Картки́ — Flashcards

<FlashcardDeck client:only="react" cards={[{ front: "університе́т", back: "university", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "бібліоте́ка", back: "library", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "фотогра́фія", back: "photography", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "шокола́д", back: "chocolate", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "я́блуко", back: "apple", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "молоко́", back: "milk", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "люди́на", back: "person", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ву́лиця", back: "street", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "столи́ця", back: "capital (city)", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ка́ша", back: "porridge", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "пі́сня", back: "song", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ма́ма", back: "mother", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "та́то", back: "father", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "банк", back: "bank", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "апте́ка", back: "pharmacy", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "рука́", back: "hand", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ве́чір", back: "evening", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "кит", back: "whale", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "кіт", back: "cat", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "їжа́к", back: "hedgehog", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "краї́на", back: "country", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "дим", back: "smoke", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "кни́га", back: "book", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "вода́", back: "water", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ха́та", back: "house, cottage", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "коза́", back: "goat", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "шко́ла", back: "school", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ліс", back: "forest", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "дуб", back: "oak", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "хліб", back: "bread", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "що", back: "what", subtitle: "спол." }, { front: "ще", back: "still, more, yet", subtitle: "присл." }, { front: "день", back: "day", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "кінь", back: "horse", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "сім'я́", back: "family", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "м'я́со", back: "meat", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "п'ять", back: "five", subtitle: "числ." }, { front: "моя́", back: "my (feminine)", subtitle: "прикм." }, { front: "так", back: "yes", subtitle: "присл." }, { front: "Ки́їв", back: "Kyiv", subtitle: "ім." }, { front: "Оде́са", back: "Odesa" }, { front: "Харків", back: "Kharkiv" }, { front: "Дніпро́", back: "Dnipro" }, { front: "Полта́ва", back: "Poltava" }, { front: "склади", back: "syllables", subtitle: "ім." }, { front: "голосні́", back: "vowels", subtitle: "прикм." }, { front: "складопо́діл", back: "syllable division", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }]} />


<!-- TAB:Зошит -->

:::note
Розши́рені впра́ви для цього́ уро́ку ще в розро́бці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

**Дже́рела — References**

- Большако́ва Grade 1 буква́р, p.25
  _Syllable rule: 'У слові стільки складів, скільки голосних звуків.'_
- Большакова Grade 1 буквар, p.29
  _Звуковий аналіз слова method — how to analyze word sounds._
- Захарійчук Grade 1 (NUS 2025), p.13-15
  _Sound notation: [•] for vowels, [–] for consonants, [=] for soft._

**Грама́тика — Grammar (МійКлас)**

- [МійКлас: Голосні й приголосні звуки](https://miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/golosni-i-prigolosni-zvuki-40864) (miyklas.com.ua)
- [МійКлас: Співвідно́шення звуків і букв](https://miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/spivvidnoshennia-zvukiv-i-bukv-41281) (miyklas.com.ua)
- [МійКлас: Алфа́ві́т (абе́тка, а́збука)](https://miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/poznachennia-zvukiv-movlennia-na-pismi-alfavit-abetka-azbuka-41217) (miyklas.com.ua)

**Статті́ — Articles**

- [Ukrainian Cyrillic Alphabet — Letters and Sounds](https://www.ukrainianlessons.com/ukrainian-cyrillic-alphabet/) (ukrainianlessons.com)
- [Ukrainian Alphabet: Full Guide with Examples and Pronunciation](https://www.ukrainianlessons.com/ukrainian-alphabet/) (ukrainianlessons.com)
- [Talk Ukrainian: Ukrainian alphabet with pronunciation](https://talkukrainian.com/ukrainian-alphabet/) (talkukrainian)
- [How to talk about transport in Ukrainian](https://www.ukrainianlessons.com/fmu5/) (ukrainianlessons.com)
- [How to ORDER at the restaurant in Ukrainian](https://www.ukrainianlessons.com/fmu16/) (ukrainianlessons.com)
- [Grammar point: Plural of nouns in Ukrainian](https://www.ukrainianlessons.com/fmu46/) (ukrainianlessons.com)
- [Grammar Point: Verb conjugations in Ukrainian](https://www.ukrainianlessons.com/fmu57/) (ukrainianlessons.com)

**Ві́део — Videos**

- [UKRAINIAN: handwritten cyrillic alphabet](https://www.youtube.com/watch?v=2tEPOopp7-I) (Red Purple Ukrainian)

**Anna Ohoiko — Ukrainian Lessons**

- [Ukrainian Cyrillic Alphabet](https://www.ukrainianlessons.com/ukrainian-cyrillic-alphabet/)
- [Ukrainian Г vs Ґ](https://www.ukrainianlessons.com/h-g/)
- [Nouns After Numbers](https://www.ukrainianlessons.com/nouns-after-numbers/)
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: reading-ukrainian
level: a1

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.1 (Module 2/55) — COMPLETE BEGINNER**

The learner is on their FIRST DAYS learning Ukrainian. They:
- Cannot read Ukrainian yet (learning the alphabet)
- Know zero Ukrainian grammar
- Can recognize only a few words (мама, тато, привіт)

**ALL instructions MUST be in English.** The learner cannot read Ukrainian instructions.

**Best activity types for this level:**
- image-to-letter: hear/see → pick the letter
- letter-grid: interactive alphabet practice
- match-up: letter ↔ sound, letter ↔ word
- quiz: in ENGLISH about Ukrainian sounds ('What sound does В make?')
- observe: show patterns in Ukrainian with English prompts
- group-sort: sort letters into vowels/consonants
- divide-words: split words into syllables (складоподіл)
- count-syllables: count syllables by counting vowels
- pick-syllables: select open/closed syllables
- odd-one-out: find the word that doesn't belong
- watch-and-repeat: pronunciation video practice
- translate: single words/short phrases English→Ukrainian (multiple choice)
- error-correction: find simple errors (gender agreement, missing ь)

**DO NOT use:** cloze, mark-the-words, select, essay-response, unjumble (learner can't construct Ukrainian sentences yet).


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-sounds-letters [§4.1.1, §4.1.4]
**Звуки і літери** (Sounds and letters)
- **quiz** — Звук чи літера?: Розрізнити звук і літеру — основа української фонетики / Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Оберіть правильну відповідь*
- **match-up** — Літера → Звук: Зіставити літери зі звуковими значеннями, особливо багатозвучні (я, ю, є, ї) / Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *З'єднайте літеру зі звуком*
- **group-sort** — Голосні й приголосні: Розподілити звуки на голосні та приголосні / Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: Побачити зображення, визначити українську літеру / See image, identify the Ukrainian letter it starts with
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні знання
- ❌ fill-in-no-options: Занадто складно для A1 — початківці потребують варіантів відповідей

### Pattern: phonetics-syllables [§4.1.1, §4.1.4]
**Склад і складоподіл** (Syllables and syllable division)
- **divide-words** — Поділи слова на склади: Інтерактивний поділ на склади — натиснути між літерами для вставки дефіса / Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Порахувати склади — кожен голосний = один склад (складотворчі голосні) / Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *Скільки складів?*
- **pick-syllables** — Вибери закриті/відкриті склади: Визначити тип складу: відкритий (закінчується голосним) чи закритий (приголосним) / Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Оберіть усі закриті склади*
- **odd-one-out** — Четверте зайве: Обрати слово, що не пасує — за кількістю або типом складів / Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні навички поділу

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **3-5 options per quiz/fill-in question** — enough to prevent guessing, not so many to overwhelm.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp__rag__verify_words` / `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp__rag__search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp__rag__search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp__rag__query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp__rag__search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp__rag__search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp__rag__search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp__rag__search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp__rag__query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp__rag__query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp__rag__search_style_guide` first (it knows calques). Then `mcp__rag__query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp__rag__verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp__rag__query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp__rag__verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp__rag__search_idioms` for Ukrainian expressions, `mcp__rag__search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp__rag__query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp__rag__query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp__rag__verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp__rag__verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp__rag__verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp__rag__query_pravopys` or `mcp__rag__search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
