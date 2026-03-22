<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [Dimension 5] [SEVERITY: major]
  Location: Exercise block `:::fill-in` "Ь чи апостроф?", specifically: `- sentence: "батьк___вщина"` `answer: "батьківщина"`
  Issue: The exercise prompt asks learners to choose between Ь or an apostrophe, but the gap is placed where the vowel `і` belongs. If the intention was to test the soft sign, the gap is in the wrong place.
  Fix: Change the gap to test the soft sign correctly: `- sentence: "бат___ківщина"` `answer: "батьківщина"` OR replace the word entirely with an easier A1 word like `пальто`.
- FIX: [Dimension 1] [SEVERITY: major]
  Location: Entire exercise section (`:::fill-in`, `:::match-up`, `:::quiz`)
  Issue: The generated activities violate the strict `activity_hints` prescribed in the plan. The plan asked for 4 specific exercises (Quiz 8 items, Match-up 8 items, Fill-in 6 items, Quiz 4 items). The generator created 5 exercises, replaced the first quiz with a fill-in, and hallucinated an extra quiz.
  Fix: Delete the unprompted `:::fill-in` ("Де потрібен Ь?") and `:::quiz` ("Дзвінкий чи глухий?"). Generate the missing 8-item `:::quiz` focusing on "Does this word have a soft sign, apostrophe, or neither?" exactly as specified in the plan.
- NOTE: [Dimension 2] [SEVERITY: minor]
  Location: Section 1 (М'яки́й знак) paragraph 1: "...Ukrainian distinguishes between **тверді** (hard) and **м'якшені** (softened) consonants..."
  Issue: The plan explicitly references Большакова Grade 1: "Тверді і пом'якшені приголосні звуки." The text uses the non-standard variant "м'якшені" instead of the standard "пом'якшені".
  Fix: Change "**м'якшені**" to "**пом'якшені**".
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

## 7 Hard Rules

1. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
6. **NO meta-commentary** — do NOT add "Content notes:", word count summaries, or self-audit sections at the end. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format. Base your exercises on the `activity_hints` in the Plan — each hint should become one exercise.

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
## М'який знак (The Soft Sign — Ь) (~280 words total)
- P1 (~90 words): Introduce Ь as a letter with no sound of its own — its only job is to soften the consonant before it. Ukrainian distinguishes тверді (hard) and м'якшені (softened) consonants. Use Захарійчук Grade 1 p.15 notation: hard = [–], soft = [=]. Show the minimal pair from the textbook: рис [–•–] vs рись [–•=] — same letters, different meaning because of Ь. Establish that Ь never appears at word start, only after consonants.
- P2 (~100 words): Present the most common Ь patterns with example words. Group by ending: -нь (день, кінь, осінь, тінь), -ль (сіль, біль), -ть (мить), -зь (мазь). Then show Ь inside words: учитель, батько, маленький, стілець. Reference the textbook poem by Ганна Чубач: "Зву-ки зм'як-шу-вать у-мі-ю" — Ь's own voice explaining its job. Emphasize that removing Ь changes meaning: камінь (stone) → камін (fireplace).
- P3 (~50 words): Reading drill — list 8 words for the learner to read aloud, mixing Ь positions: день, сіль, кінь, мідь, батько, маленький, пальто, олень. Instruction to notice how the tongue position shifts on the softened consonant.
- Exercise: fill-in — "Add Ь where needed: ден_, сол_, кін_, бат_ко, учител_, мален_кий" (6 items, matches activity_hint #3 partially)

## Апостроф (The Apostrophe) (~280 words total)
- P1 (~90 words): Introduce the apostrophe as a written sign (not a letter) that appears between a consonant and a vowel. State the rule from Захарійчук Grade 1 p.97: apostrophe comes after б, п, в, м, ф, р before я, ю, є, ї. Its job: keep the consonant HARD and let the vowel pronounce its full two-sound value [й+vowel]. Contrast with Ь which softens — apostrophe does the opposite, it blocks softening.
- P2 (~100 words): Show how apostrophe changes pronunciation using the textbook pair: моря (sea, gen.) [р'] soft р + [а] vs подвір'я (yard) [р] hard р + [йа] two sounds. Walk through key words with phonetic breakdown: сім'я [с'ім-йа] (family), м'ясо [м-йасо] (meat), п'ять [п-йать] (five), комп'ютер [комп-йутер] (computer). Reference textbook exercise: "Визнач, у яких словах потрібно написати апостроф" — б..є м..яч, п..ю чай.
- P3 (~50 words): Reading practice with apostrophe words drawn from the textbook lists: п'ять, дев'ять, м'який, м'яч, об'єкт, сім'я, пір'я, здоров'я, п'ятниця, ім'я. Instruction to pronounce the consonant hard and give the vowel its full [й+vowel] sound.
- Exercise: fill-in — "Insert Ь or apostrophe: сім_я, ден_, п_ять, батьк_вщина, м_ясо, осін_" (6 items, matches activity_hint #3)

## Дзвінкі і глухі (Voiced and Voiceless) (~280 words total)
- P1 (~80 words): Introduce the concept of voiced vs voiceless consonants. Hand-on-throat test: vibration = дзвінкий (voiced), no vibration = глухий (voiceless). Present all 8 pairs in a clear list: Б–П, Д–Т, Г–Х, Ґ–К, З–С, Ж–Ш, ДЗ–Ц, ДЖ–Ч. Note that ДЗ and ДЖ are single sounds written with two letters (reference module 2 alphabet coverage).
- P2 (~90 words): Critical difference from Russian — Ukrainian does NOT devoice consonants at word end. This is one of the most important pronunciation rules. дуб is [дуб], NOT *[дуп]. мороз is [мороз], NOT *[морос]. хліб is [хліб], NOT *[хліп]. This is authentic Ukrainian pronunciation. Learners exposed to Russian (or Russian-influenced teaching) must unlearn devoicing. Each final consonant keeps its voiced quality — this is a hallmark of natural Ukrainian speech.
- P3 (~60 words): Minimal pairs for ear training — words distinguished only by voiced vs voiceless: балка (beam) vs палка (stick), коза (goat) vs коса (braid/scythe), дим (smoke) vs тим (that, instr.). Instruction to say each pair aloud, hand on throat, feeling the vibration switch on and off.
- Exercise: match-up — "Match voiced-voiceless pairs: Б↔П, Д↔Т, Г↔Х, Ґ↔К, З↔С, Ж↔Ш, ДЗ↔Ц, ДЖ↔Ч" (8 items, matches activity_hint #2)
- Exercise: quiz — "Is the underlined consonant voiced or voiceless? балка, сіль, зима, шум, гарно, тихо, джміль, цвях" (8 items, matches activity_hint #1 format)

## Важкі звуки (Tricky Sounds) (~280 words total)
- P1 (~90 words): И — the sound that trips up every English speaker. Not English "ee" (too high and front) and not English "i" in "bit" (too lax). Ukrainian И sits between them: start with "ee" smile position, then pull the tongue slightly back and down. Practice words: бик (bull), лист (leaf/letter), зима (winter), тихо (quietly), синій (blue). Compare the pair і vs и: ліс (forest) vs лис (fox) — different vowel, different meaning. И requires deliberate practice.
- P2 (~90 words): Г — voiced glottal fricative [ɦ], the signature Ukrainian sound. NOT the Russian hard [g]. Imagine saying English "h" but turning on your voice — that breathy, soft sound is Ukrainian Г. Words: гарно (nicely), гора (mountain), голова (head), гарячий (hot). Then introduce Ґ — the actual hard [g] sound, which exists only in a small set of words: ґанок (porch), ґудзик (button), ґречний (polite). The Г/Ґ distinction is uniquely Ukrainian — confusing them marks non-native speech immediately.
- P3 (~60 words): Р — rolled/trilled, similar to Spanish or Italian R. Tongue tip vibrates against the alveolar ridge. Practice words: рука (hand), робота (work), ранок (morning), риба (fish), рік (year). Reassurance: even an imperfect Р is understood — don't let it block communication. It improves naturally with practice.
- Exercise: quiz — "Choose the correct sound: is Г in гарно pronounced like English 'g' or like a voiced 'h'? Is Ґ in ґудзик a hard [g] or a soft [ɦ]?" (4 items, matches activity_hint #4)

## Підсумок — Summary (~220 words total)
- P1 (~100 words): Recap the four key concepts. Ь softens consonants (день, сіль, кінь) — no sound, just changes the consonant. Apostrophe after б, п, в, м, ф, р before я, ю, є, ї keeps the consonant hard (сім'я, м'ясо, п'ять). Voiced consonants vibrate (Б, Д, Г), voiceless don't (П, Т, Х) — and Ukrainian keeps them voiced at word end. Tricky sounds: И (between ee/i), Г (voiced h), Ґ (hard g), Р (rolled).
- P2 (~70 words): Self-check questions from the plan: What does Ь do to a consonant? After which six letters can apostrophe appear? Name three voiced-voiceless pairs. How is Г different from Ґ? Read these words aloud: сім'я, день, п'ять, гарно, риба, ґудзик. If any feel uncertain, revisit that section.
- P3 (~50 words): Preview of module 4 — Stress and Melody (Наголос). Now that the learner knows the individual sounds, the next module covers where the stress falls in Ukrainian words and how it changes meaning. Наголос is the heartbeat of Ukrainian — it makes words come alive.

Grand total: ~1340 words (280 + 280 + 280 + 280 + 220)
</skeleton>

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
