<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Russian/archaic words: кон→кін
</correction_directive>

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
5. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format.

**CRITICAL: Each exercise MUST match a specific `activity_hints` entry from the Plan.**
- Use the EXACT `type` specified (quiz, fill-in, match-up, group-sort, true-false)
- Follow the `focus` description EXACTLY — if the plan says "Answer: У тебе є...? Так / Ні", your quiz must test exactly that pattern
- Match the `items` count specified
- Do NOT invent different exercises — the plan's activity_hints are the specification

Write REAL content: real questions, real answers, real distractors. Every exercise must be solvable by a learner who read the preceding prose.

### DSL Format

Use these exact formats. Each block starts with `:::type` and ends with `:::`.

**Quiz** (multiple choice):
```
:::quiz
title: "Звук чи літера?"
---
- q: "Що ми чуємо і вимовляємо?"
  o: ["звуки", "літери", "слова"]
  a: 0
- q: "Що ми бачимо і пишемо?"
  o: ["літери", "звуки", "речення"]
  a: 0
:::
```

**Fill-in** (complete the sentence):
```
:::fill-in
title: "Complete the greeting"
---
- sentence: "Привіт! Як ___?"
  answer: "справи"
- sentence: "Дякую, ___."
  answer: "добре"
:::
```

**Match-up** (connect pairs):
```
:::match-up
title: "Match false friend letters to their real sounds"
---
- left: "В"
  right: "sounds like [в], not [b]"
- left: "Н"
  right: "sounds like [н], not [h]"
:::
```

**Group-sort** (classify into categories):
```
:::group-sort
title: "Classify letters"
---
groups:
  - name: "Голосні"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні"
    items: ["М", "К", "Б", "Ш"]
:::
```

**True-false**:
```
:::true-false
title: "True or false?"
---
- statement: "В українській мові 33 літери."
  answer: true
- statement: "Голосних звуків більше, ніж приголосних."
  answer: false
:::
```

Spread exercises evenly throughout the module. Never cluster them.

### Approved Exercise Patterns

Use these Ukrainian textbook-inspired patterns (Заболотний, Авраменко) instead of generic "quiz" types:

- **Знайди помилку (Find the error):** Give 3 correct sentences and 1 with an error. Learner identifies the mistake. Tests: grammar rules, calques, Russianisms.
- **Обери правильне слово (Choose the right word):** Fill in the blank from 2-3 options (synonyms, paronyms, or confusable words). Tests: vocabulary nuance, register.
- **Утвори пару (Match-up):** Match words to antonyms, translations, or grammatical pairs (e.g., masculine → feminine). Tests: vocabulary, morphology.
- **Розподіли (Group-sort):** Sort items into 2-3 categories (e.g., голосні vs приголосні, hard vs soft consonants). Tests: foundational phonetics, grammar classification.
- **Склади речення (Build a sentence):** Give scrambled words, learner arranges into correct order. Tests: word order, sentence structure.
- **Знайди місце (Find the right place):** Give 4 sentences with blanks and 4 words — each word fits exactly one sentence. Tests: contextual meaning, collocations.

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
  - 'Ь has no sound. Its job: soften the consonant before it. Ukrainian distinguishes hard (тверді) and soft (м''якшені) consonants.
    Захарійчук Grade 1 p.15 notation: hard = [–], soft = [=]. Common words: день (day), сіль (salt), кінь (horse), мідь (copper).
    The Ь appears only after consonants, never at word start.'
  - 'Where Ь commonly appears: -нь: день, кінь, осінь -ль: сіль, біль (pain) -ть: мить, путь -зь: мазь (ointment) Practice:
    учитель (teacher), батько (father), маленький (small).'
- section: Апостроф (The Apostrophe)
  words: 250
  points:
  - 'Захарійчук Grade 1 p.97: Apostrophe comes after б, п, в, м, ф, р before я, ю, є, ї. It keeps the consonant HARD and gives
    the vowel its full [й] + vowel sound.'
  - 'Without apostrophe: consonant softens (пісня — Н is soft). With apostrophe: consonant stays hard + vowel = two sounds.
    сім''я [сім-йа] (family), м''ясо [м-йасо] (meat), п''ять [п-йать] (five), комп''ютер [комп-йутер] (computer). Reading
    practice: п''ять, дев''ять, м''який, м''яч, об''єкт.'
- section: Дзвінкі і глухі (Voiced and Voiceless)
  words: 250
  points:
  - 'Consonants come in voiced-voiceless pairs. Hand on throat test: vibration = voiced. Pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш,
    ДЗ-Ц, ДЖ-Ч.'
  - 'Critical difference from Russian: Ukrainian does NOT devoice consonants at word end. дуб is [дуб], NOT *[дуп]. мороз
    is [мороз], NOT *[морос]. This is authentic Ukrainian.'
  - 'Minimal pairs for ear training: балка (beam) vs палка (stick), коза (goat) vs коса (braid).'
- section: Важкі звуки (Tricky Sounds)
  words: 250
  points:
  - 'И — not English ''ee'' or ''i''. Between them. Smile for ''ee'' but pull tongue back slightly. Practice: бик, лист, зима,
    тихо, синій.'
  - 'Г — voiced glottal fricative [ɦ]. NOT Russian hard [g]. Like saying ''h'' but with voice. Words: гарно, гори, голова.
    Ґ = hard [g], only in: ґанок, ґудзик, ґречний.'
  - 'Р — rolled/trilled, like Spanish. Practice: рука, робота, ранок, риба. Even imperfect Р is understood — don''t stress
    about it.'
- section: Підсумок — Summary
  words: 200
  points:
  - 'Self-check: What does Ь do? After which letters does apostrophe appear? Name 3 voiced-voiceless pairs. How is Ukrainian
    Г different from Ґ? Read these words: сім''я, день, п''ять, гарно.'
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
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
  relevant:
    Ь: https://www.youtube.com/watch?v=cJlal8XKBxo
    Г: https://www.youtube.com/watch?v=gVnclpSI0DU
    Ґ: https://www.youtube.com/watch?v=gNjHqjTW9WQ
    Р: https://www.youtube.com/watch?v=fMGsQ5KPQgg
    И: https://www.youtube.com/watch?v=W-1rCu0indE

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
- Dialogues: natural, not stilted. Real situations, real responses.
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

Playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::quiz` / `:::fill-in` / `:::match-up` / `:::group-sort` / `:::true-false` for exercises (using the DSL formats above)

Do NOT write MDX component syntax or JSON. Plain Markdown with the exercise DSL blocks described above.

Begin writing now. Start with the first section heading.
