# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **3: Special Signs** (A1, A1.1 [Sounds, Letters, and First Contact]).

**Target: 1200–1800 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1200+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 8 Hard Rules

1. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

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
module: a1-003
level: A1
sequence: 3
slug: special-signs
version: '1.1'
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
  - 'Ь has no sound. Its job: soften the consonant before it. Ukrainian distinguishes
    hard (тверді) and soft (м''якшені) consonants. Захарійчук Grade 1 p.15 notation:
    hard = [–], soft = [=]. Common words: день (day), сіль (salt), кінь (horse), мідь
    (copper). The Ь appears only after consonants, never at word start.'
  - 'Where Ь commonly appears: -нь: день, кінь, осінь -ль: сіль, біль (pain) -ть:
    мить, путь -зь: мазь (ointment) Practice: учитель (teacher), батько (father),
    маленький (small).'
- section: Апостроф (The Apostrophe)
  words: 250
  points:
  - 'Захарійчук Grade 1 p.97: Apostrophe comes after б, п, в, м, ф, р before я, ю,
    є, ї. It keeps the consonant HARD and gives the vowel its full [й] + vowel sound.'
  - 'Without apostrophe: consonant softens (пісня — Н is soft). With apostrophe: consonant
    stays hard + vowel = two sounds. сім''я [сім-йа] (family), м''ясо [м-йасо] (meat),
    п''ять [п-йать] (five), комп''ютер [комп-йутер] (computer). Reading practice:
    п''ять, дев''ять, м''який, м''яч, об''єкт.'
- section: Дзвінкі і глухі (Voiced and Voiceless)
  words: 250
  points:
  - 'Consonants come in voiced-voiceless pairs. Hand on throat test: vibration = voiced.
    Pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.'
  - 'Critical difference from Russian: Ukrainian does NOT devoice consonants at word
    end. дуб is [дуб], NOT *[дуп]. мороз is [мороз], NOT *[морос]. This is authentic
    Ukrainian.'
  - 'Minimal pairs for ear training: балка (beam) vs палка (stick), коза (goat) vs
    коса (braid).'
- section: Важкі звуки (Tricky Sounds)
  words: 250
  points:
  - 'И — not English ''ee'' or ''i''. Between them. Smile for ''ee'' but pull tongue
    back slightly. Practice: бик, лист, зима, тихо, синій.'
  - 'Г — voiced glottal fricative [ɦ]. NOT Russian hard [g]. Like saying ''h'' but
    with voice. Words: гарно, гори, голова. Ґ = hard [g], only in: ґанок, ґудзик,
    ґречний.'
  - 'Р — rolled/trilled, like Spanish. Practice: рука, робота, ранок, риба. Even imperfect
    Р is understood — don''t stress about it.'
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
  - м'який (soft) — apostrophe + soft sign
activity_hints:
- type: quiz
  focus: Does this word have a soft sign, apostrophe, or neither?
  items: 8
- type: match-up
  focus: 'Match voiced-voiceless pairs: Б↔П, Д↔Т, etc.'
  items: 8
- type: fill-in
  focus: 'Add the missing Ь or apostrophe: сім_я, ден_, п_ять'
  items: 6
- type: quiz
  focus: Choose the correct pronunciation for Г vs Ґ words
  items: 4
connects_to:
- a1-004 (Stress and Melody)
prerequisites:
- a1-002 (Reading Ukrainian)
grammar:
- Soft sign (Ь) — softens preceding consonant, no sound
- Apostrophe — after б,п,в,м,ф,р before я,ю,є,ї (Захарійчук rule)
- Voiced/voiceless consonant pairs (8 pairs)
- Ukrainian non-devoicing at word end (vs Russian)
- Г [ɦ] vs Ґ [g] distinction
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

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Special Signs
**Module:** special-signs | **Phase:** A1.1 [Sounds, Letters, and First Contact]
**Textbook grades searched:** 1, 2

---

## М'який знак (The Soft Sign — Ь)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 102
> ь
>  [  = •  –  ]
> Я не шість, а-ле ра-ді-ю:
> Зву-ки зм’як-шу-вать у-мі-ю. 
> От, на-прик-лад: тінь і лінь,
> Пі-вень, за-єць, сіль і кінь… 
> Ви без ме-не сло-во «ка-мінь»
> Про-чи-та-ли б як «ка-мін»!
>                                                                Ганна Чубач
> т * л ь п
> л ь о н
> а н и
> л * л ь к а
> нь
> кі
> ті
> лі 
> ль
> сі
> мі
> ро 
> нь
> де
> пе
> о-ле 
> тин    [–• – ]	    син   [–• – ]	
> рис    [–• – ]
> тінь   [=• = ]	    синь [–• =]	
> рись  [–• = ]
> Бачу ь (м’який знак).

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 46
> Спиши слова, у яких є пом’якшені приголосні. Познач пом’як-
> шені приголосні знаком 
> .
> Білка, місто, липа, пінгвін, фігура, жінка, чітко, словник, 
> шість, дівчинка, гірка, хід, хлопчик, свято, пюре, буква, цвях.
>  
> Поділи слова для переносу. Познач м’які і пом’якшені при-
> голосні знаком 
> .
> Зразок. Лі-то, … .
> Зразок. Дитя-чий, ди-тячий … .
> Трава, площа, клени, 
> ключі, квіти, стілець.
> Гарячий, лисячий, золотий, 
> металевий, паперовий.
>  
> Тема і головна думка. Головні герої. Досліджуємо медіа
> ДР

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 98
> Бачу З, з (зе). Чую  [з], [з'].
> к о * з а
> * у з о
>  [  – • |  –•  – ]
> к
> з і р к и
>  [ =• –  |  –•]
> Зи-ма в лі-сі. Зві-рі ко-ло 
> . Во-ни 
> при-кра-си-ли 
> : 
>  по-ві-си-ла 
>  і 
> . 
>  по-ві-сив 
>  і 
> . 
>  при-ніс 
> і 
> .
> А де свя-тий  Ми-ко-лай?
> — При-віт!  ЗНовимроком!
> а
> о
> у
> и
> і
> З
> за
> зо
> зу
> зи
> зі
> а
> о
> у
> и
> і
> аз
> оз
> уз
> из
> із
> З
> за- 
>      зо- 
>      зе- 
>      
> З з
> 	 Поділи останнє речення на слова. Дізнайся, 
> що сказав святий Миколай.
> зу- 
>     -за

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 48
> ПЕрЕнос сЛІв З ь І ьо
> Прочитай слова. До якого слова немає малюнка? Чим схожі 
> слова? Чим відрізняються? Спиши. Познач м’які приголосні 
> звуки знаком 
> .  
> галка — галька 
> лан — лань
> мілка — мі лька
> Спиши. Відшукай слова зі знаком м’якшення. Познач м’який 
> приголосний перед знаком м’якшення знаком 
> .
> У метелика біленькі крильця. Василько сів на маленький 
> стільчик. Вітерець підняв легеньку пір’їнку. Сіренький заєць 
> їсть морквинку.  
> Не відривай букву ь від попередньої букви, 
> коли перенос

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 90
> Повторюємо разом
>  М’який знак (ь).  
> Буквосполучення ьо
> При переносі буквосполучення ьо 
> не розриваємо, а м’який знак зали-
> шаємо біля попереднього приголос­
> ного: пе-ньоч-ки, круг-лень-кі.
> 	 Випиши виділені слова в тексті, поділивши їх 
> на склади для переносу (с. 88). 
> 	 Прочитай текст.
> У джмелиному рої лежали лялечки, 
> замотані в павутиння, як у пелюшки. 
> Лялечки були слухняні й тихі, мов діти, 
> коли вони сплять. Уранці виліз малень-
> кий джмелик, волохатий, веселий. 
> Повештався трохи по гні

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> 30
> 104.
> ТВЕРДІ ТА М’ЯКІ ПРИГОЛОСНІ ЗВУКИ. 
> ПОЗНАЧЕННЯ М’ЯКОСТІ ПРИГОЛОСНИХ БУКВАМИ
> 105.
> Дослідиѳ, яка роль знака м’якшення в слові.
> Крок 1. Розглянь малюнки. 
> Крок 2. Зроби висновок, чому змінилося 
> значення слова.
> Буква «знак м’якшення» (ь) разом із попередньою 
> буквою позначає на письмі м’який приголосний звук.
> рись
> рис
> 106.
> Дослідиѳ, які букви позначають м’якість попереднього 
> приголосного звука.
> [л] — [л´]	 	
> 	
> 	
> [н] — [н´]
> лук — люк	
>  	
> 	
> ворона — вороненя
> Пилип — Поліна	
> 	
> сини — синє
> 2. С

## Апостроф (The Apostrophe)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 69
> 	
> Прочитай вірш, правильно вимовляючи сло-
> ва з апострофом. 
> 	
> З’єднай частини прислів’їв. Прочитай. По-
> ясни, як ти їх розумієш.
> — Буквам я усім рідня...
> Може, не потрібен я?
> — Не журись, малюче, так.
> Просто ти — друкарський знак.
> Мусиш бути у словах:
> М’яз, прислів’я, м’яч, під’їзд,
> В’юн, м’якуш, бар’єр та з’їзд,
> П’ятниця, п’ята, ім’я.
> Ось вона — твоя сім’я!
>              Валентина Черняєва 
> ніж  багатство.
> Знає кіт,
> чиє сало з’їв.
> Добре ім’я краще,
> 	
> Випиши з вірша підкреслені слова з апо-

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 45
> На подвір’ячку, під в’язом,
> вся зібралася сім’я:
> відпочить, побути разом
> та послухать солов’я.
> 	
> 	
> 	
> Надія Красоткіна
> 2.	 Випиши слова, у яких є апостроф.
> 163. 1.	 Користуючись словами для довідки, доповни речення.
> 1.  Тіло риб покриває луска, а тіло птахів — ...  . 
> 2. В’юн — риба, а м’ята — ... . 3. Пір’їна легка, а камінь ... . 
> 4. Найбільше багатство — ... . 5. Тато, мама і я — дружна ... . 
> 6. П’ятий день тижня — ... .
> Слова для довідки: п’ятниця, здоров’я, рослина, пір’я, 
> важкий, сім’я

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 22
> Апостроф — це знак ’. У словах апостроф пишуть угорі 
> між буквами: м’яч, пір’я.
> Б У|Р Я К
> [р′][а]
> П І|Р ’ Я
> [р][йа]
> Знайди слово — підпис до малюнка.
> 	 м’яч	
> м’який	
> хом’як	
> п’ять
> 	 м’ята	
> рум’яний	
> черв’як	
> п’ятниця 
> 	 м’ясо	
> дерев’яний	
> реп’ях	
> п’ята
> 
> Порівняй слова в стовпчиках. Чим вони схожі? Чим від-
> різняються?
> 	
> комп’ютер	
> солов’ї	
> м’ята
> 	
> комп’ютерний	
> солов’їний	
> м’ятний
> 
> Текст. Тема тексту
> У нашій школі є комп’ю-
> терний клас. У ньому багато 
> комп’ютерів. Діти грають 
> у  комп’ютер

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 58
> аПостроФ. ПЕрЕнос сЛІв
> Хто правильно відповів на запитання? 
> Коли я пишу апостроф у слові м’ята, то це означає, що…
> Звук [м] — м’який 
> приголосний, 
> буква я позначає 
> два звуки [йа].
> Звук [м] — твердий 
> приголосний, 
> буква я позначає 
> два звуки [йа].
> Звук [м] — твердий 
> приголосний, 
> буква я позначає 
> один звук [а].
>  
> Знайди схему до слів в’ють і в’є.
>  
> Назви птахів. Спиши назви птахів та їхніх пташенят.
> Голуб’яче 
> гніздо
> Гороб’яче 
> гніздо
> Солов’їне 
> гніздо
> Ластів’яче 
> гніздо
> голуб  
> голуб’

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 23
> ’
> Апостроф
> і |м’я
> Прочитай. Назви імена. Склади речення з одним іменем.
> 	
> ім’я	
> Дар’я	
> Дем’ян	
> В’ячеслав
> 	
> сім’я	
> Мар’яна	
> Лук’ян	
> Валер’ян
> 
> Відшукай слово до схеми.
> 	
> п’є	
> в’є	
> б’є	
> з’єднати	
> під’їхати
> 	 п’ють	 в’ють	 б’ють	
> роз’єднати	
> від’їхати
> 
> Текст. Театралізуємо
> Моє ім’я
> Я — Мар’яна. 
> Сьогодні на подвір’ї я грала в м’яч. 
> —  Мар’яше! — кличуть подруги. —  
> Кидай м’яч. 
> Потім мене гукнула бабуся:
> —  Мар’яночко! Іди обідати.
> Я пішла додому і зустріла сусідку. 
> —  Як справи, Мар’янко?

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> 57
> аПостроФ
> Прочитай слова. Чим відрізняється вимова ря і р’я? 
> моря — подвір’я 
> буряк — бур’ян 
> зоря — сузір’я
> • Як називають знак ’, який стоїть після р перед я?
> апостроф — це знак ’. Він показує, що приголосний 
> звук перед апострофом твердий, а букви я, ю, є 
> позначають два звуки [йа], [йу], [йе].
> [м]
> твердий приголосний звук
> [йа]
> два звуки
> м ’ я
>  
> Визнач, у яких словах потрібно написати апостроф. Після 
> яких букв пишеться апостроф? Перед якими буквами? 
>    б..є м..яч    п..ю чай   в..ють сол

## Дзвінкі і глухі (Voiced and Voiceless)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 66
> дз
> Бачу  Дз, дз (дз). 
> Чую  [дз], [дз′]. 
> 	     еркало        ґу	          ики      кукуру            а  
> дзвонити
> дзвонила
> а
> д з в о н
> д з и ґ
> д з
>  [ – •| –•] 
>  [ –  –• – ] 
> б а н
> и к
>  [ –  –•| –• –]  
> дзвінкий
> дзюрчить
> Дзюрчать-дзвенять струмочки,
> І птах вітає птаха...
> Мала, хрустка бурулька
> Додолу впала з даху.
>                                        Лідія Компанієць
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## М'який знак (The Soft Sign — Ь)` (~250 words)
- `## Апостроф (The Apostrophe)` (~250 words)
- `## Дзвінкі і глухі (Voiced and Voiceless)` (~250 words)
- `## Важкі звуки (Tricky Sounds)` (~250 words)
- `## Підсумок — Summary` (~200 words)
- `## Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 5-15% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.
- UKRAINIAN CONTENT: Words and short phrases inline: "The letter **Н** looks like H but sounds like N."
- DIALOGUES & READING PRACTICE: Short Ukrainian sentences in blockquotes are encouraged.
- TABLES: Simple letter-sound or word-meaning tables.
Ukrainian sentences max 10 words.

HARD GRAMMAR RULES (audit will reject violations):
- Max 10 words per Ukrainian sentence (STRICT — count every word)
- ONLY 1 clause per sentence (no compound sentences)
- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
  Exception (M15 what-i-like): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed
    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized
    chunk — do NOT explain dative case rules or paradigms.
- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)
  Exception: M37 introduces basic Instrumental 'з' (кава з молоком)
- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED
- Only imperfective aspect verbs
- No participles
- Allowed cases: Nominative, Accusative, Locative (from M30), Genitive (basics), Vocative

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
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- Dialogues: natural, not stilted. Real situations, real responses. **Use the knowledge packet** — it contains textbook excerpts with real Ukrainian dialogues and situations. Adapt them, don't invent artificial conversations. A dialogue about немає should show someone SEARCHING for something and not finding it (keys, notebook, phone), not an interrogation. A dialogue about the market should sound like a real market conversation. If the knowledge packet has a textbook dialogue on the topic, use that pattern.
- **Tone:** Authoritative but warm. Like a skilled Ukrainian teacher — confident, clear, culturally grounded. Let the content be interesting on its own.
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.

GRAMMAR CONSTRAINTS (A1.1 — Phonetics, M01-M03):
NO CONJUGATED VERBS. NO IMPERATIVES. This is the phonetics phase.

ALLOWED structures (Ukrainian examples only):
- Це + noun: «Це кіт», «Це мама»
- Noun + тут/там: «Мама тут», «Кіт там»
- Question words: «Хто це?», «Що це?», «Де мама?»
- Так/Ні: «Так, це кіт», «Ні, це не кіт»
- Fixed phrases (memorized, no grammar): дякую, будь ласка, привіт

BANNED: ALL verbs, past/future tense, cases, compound sentences

STRESS MARKS: Do NOT add stress marks (´). Write plain Ukrainian.
The pipeline adds stress marks deterministically after you write.

METALANGUAGE: English prose, Ukrainian examples. Bilingual headings.

### Vocabulary

**Required:** сім'я (family) — apostrophe word, день (day) — soft sign after Н, сіль (salt) — soft sign after Л, м'ясо (meat) — apostrophe after М, п'ять (five) — apostrophe after П, гарно (nicely, beautifully) — Г [ɦ] practice, риба (fish) — Р and И practice
**Recommended:** батько (father, formal) — soft sign, учитель (teacher) — soft sign at end, дев'ять (nine) — apostrophe, комп'ютер (computer) — apostrophe in cognate, м'який (soft) — apostrophe + soft sign

### Pronunciation Videos



---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*



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
## М'який знак (The Soft Sign — Ь) (~275 words total)
- P1 (~90 words): Introduce Ь as a letter with no sound of its own — its job is to soften the consonant before it. Ukrainian distinguishes тверді (hard) and м'якшені (softened) consonants. Textbook notation from Захарійчук Grade 1 p.15: hard = [–], soft = [=]. Show the minimal pair from the Grade 2 textbook: рис [р•с] vs рись [р'•с'], тин vs тінь, син vs синь — the Ь changes meaning entirely. Reference the Ганна Чубач poem: "Ви без мене слово «камінь» прочитали б як «камін»!"
- P2 (~100 words): Where Ь commonly appears — pattern by consonant. -нь: день (day), кінь (horse), осінь (autumn), камінь (stone). -ль: сіль (salt), біль (pain). -ть: мить (moment), радість (joy). -зь: мазь (ointment). Everyday words with Ь: учитель (teacher), батько (father), маленький (small). Ь appears only after consonants, never at word start, never before О without the ьо combination.
- P3 (~45 words): Reading tip — when you see Ь, soften the consonant before it. Imagine pressing the consonant gently. Practice reading aloud: день, сіль, кінь, учитель, батько, маленький, стілець.
- Exercise: fill-in — Add the missing Ь: ден_, сіл_, кін_, учител_, бат_ко, мален_кий (6 items, from activity_hints type 3)
- P4 (~40 words): Transition — Ь softens consonants, but Ukrainian has another sign that does the opposite: it keeps consonants hard. That sign is the apostrophe.

## Апостроф (The Apostrophe) (~275 words total)
- P1 (~90 words): Introduce the apostrophe rule from Захарійчук Grade 1 p.97: apostrophe appears after б, п, в, м, ф, р before я, ю, є, ї. Its job is the opposite of Ь — it keeps the consonant HARD and signals that the following vowel letter represents TWO sounds: [й] + vowel. Reference the textbook comparison: моря (no apostrophe, р is soft) vs подвір'я (apostrophe, р is hard + [йа]).
- P2 (~100 words): Break down the phonetics with key vocabulary. сім'я [с'ім-йа] (family) — м stays hard, я = [йа]. м'ясо [м-йасо] (meat). п'ять [п-йать] (five). комп'ютер [комп-йутер] (computer). дев'ять [дев-йать] (nine). Without the apostrophe, the consonant would soften and the vowel would represent just one sound — completely different pronunciation. Reference the textbook exercise: буряк (no apostrophe) vs бур'ян (with apostrophe) — hear the difference.
- P3 (~45 words): Reading practice list from textbook examples: м'яч (ball), м'який (soft), п'ятниця (Friday), ім'я (name), сім'я (family), подвір'я (yard), здоров'я (health), об'єкт (object). Read each word aloud, feeling the hard consonant before the apostrophe.
- Exercise: quiz — Does this word have a soft sign, apostrophe, or neither? Items: сім'я, день, м'ясо, батько, комп'ютер, сіль, зима, п'ять (8 items, from activity_hints type 1)
- P4 (~40 words): Quick comparison table — Ь softens consonant (день, сіль), apostrophe keeps consonant hard before я/ю/є/ї (м'ясо, сім'я). Two signs, opposite jobs. Both essential for reading Ukrainian correctly.

## Дзвінкі і глухі (Voiced and Voiceless) (~275 words total)
- P1 (~80 words): Introduce the concept of voiced and voiceless consonants. Simple test from Ukrainian pedagogy: put your hand on your throat. If it vibrates, the consonant is voiced (дзвінкий). If not, voiceless (глухий). Try it: say Б — vibration. Say П — no vibration. Same mouth position, different voicing.
- P2 (~90 words): Present the eight voiced-voiceless pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч. Note the uniquely Ukrainian pairs ДЗ-Ц and ДЖ-Ч — these are single sounds (африкати), not two letters. Reference дзвонити (to ring) from Grade 1 textbook as a ДЗ example.
- P3 (~65 words): Critical difference from Russian — Ukrainian does NOT devoice consonants at word end. In Russian, дуб sounds like *[дуп] and мороз like *[морос]. In Ukrainian, дуб is [дуб] and мороз is [мороз]. Every consonant keeps its true voice. This is authentic Ukrainian pronunciation — resist the Russian habit if you've been exposed to it.
- Exercise: match-up — Match voiced-voiceless pairs: Б↔П, Д↔Т, Г↔Х, Ґ↔К, З↔С, Ж↔Ш, ДЗ↔Ц, ДЖ↔Ч (8 items, from activity_hints type 2)
- P4 (~40 words): Minimal pairs for ear training: балка (beam) vs палка (stick), коза (goat) vs коса (braid), дім (house) vs тім... These pairs show that voicing changes meaning — getting it right matters.

## Важкі звуки (Tricky Sounds) (~275 words total)
- P1 (~90 words): И — the sound that trips up every English speaker. It is NOT English "ee" (like in "see") and NOT English "i" (like in "sit"). It lives between them. Technique: start to smile as for "ee" but pull your tongue back slightly. Your jaw drops a tiny bit compared to І. Practice words: бик (bull), лист (leaf/letter), зима (winter), тихо (quietly), синій (blue). Listen for the difference between И and І: бик vs бік, лис vs ліс.
- P2 (~90 words): Г — the voiced glottal fricative [ɦ]. This is NOT the Russian hard [г] and NOT the English "h." It is like English "h" but with your voice turned on — a breathy, voiced sound from the throat. Words: гарно (beautifully), гори (mountains), голова (head), гарячий (hot). Now contrast with Ґ — the hard [g] sound, which exists in very few Ukrainian words: ґанок (porch), ґудзик (button), ґречний (polite). Г [ɦ] is the default; Ґ [g] is the exception.
- P3 (~55 words): Р — rolled/trilled, similar to Spanish or Italian R. Tongue tip taps the ridge behind your upper teeth. Practice: рука (hand), робота (work), ранок (morning), риба (fish). Even an imperfect Р is always understood — don't let it stop you from speaking.
- Exercise: quiz — Choose the correct pronunciation description for Г vs Ґ words: гарно, ґанок, голова, ґудзик (4 items, from activity_hints type 4)
- P4 (~40 words): These four sounds — И, Г, Ґ, Р — take time. The goal is not perfection today but awareness. You now know what to listen for, and your ear will sharpen with every Ukrainian conversation you hear.

## Підсумок — Summary (~220 words total)
- P1 (~100 words): Recap the four core concepts. Ь softens the consonant before it (день, сіль, кінь) — it has no sound of its own. The apostrophe after б, п, в, м, ф, р keeps the consonant hard and gives я, ю, є, ї their full two-sound value (сім'я, м'ясо, п'ять). Voiced and voiceless consonants come in eight pairs, and unlike Russian, Ukrainian keeps consonants voiced at word end. И, Г, and Р need practice but are learnable.
- P2 (~70 words): Self-check questions: What does Ь do to a consonant? After which six letters can apostrophe appear? Name three voiced-voiceless pairs. How is Г different from Ґ? How is И different from English "ee"?
- P3 (~50 words): Final reading challenge — read these words aloud with confidence: сім'я, день, п'ять, гарно, кінь, м'ясо, батько, риба, комп'ютер, учитель. If you can read all ten, you have mastered the special signs. Next: stress and melody (наголос).

Grand total: ~1320 words (275 + 275 + 275 + 275 + 220)
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
