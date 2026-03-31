<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Too short: 325 words (target: 2000, minimum: 1700)
- NOTE: Plan expects 4 exercise(s) but content has 0 placeholders
</correction_directive>

LEARNINGS FROM PAST BUILDS (same error patterns seen before):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
- [GLOBAL] NO LLM filler phrases. Do NOT write: "Let us start with...", "Numbers unlock the real Ukraine", "You now possess a complete...", "It is incredibly versatile", "one of the most rewarding skills". Start sections with a dialogue, a question, or a concrete example — never with a generic motivational opener. If a sentence could appear in any language course about any topic, delete it.
- [GLOBAL] Every exercise item must test something EXPLICITLY taught in the preceding prose. If an exercise tests the collocation "малювати картину", the prose must contain "малювати картину" as a taught example. Do NOT test collocations, vocabulary, or patterns that the learner has to infer — test what was taught.
- [GLOBAL] Quiz correct answers must be RANDOMIZED across positions. Do NOT place the correct answer at index 0 for all items. Distribute correct answers roughly evenly across all positions (0, 1, 2) to prevent pattern-guessing.
- [GLOBAL] Do NOT use spatial metaphors for abstract grammatical requirements. Example: "на" with musical instruments is NOT "on top of" — it is an abstract grammatical requirement that must be memorized. Misleading mnemonics cause incorrect generalizations. If a rule must simply be memorized, say so directly.
- [GLOBAL] Memorized chunks are allowed before their grammar is formally taught. Natural Ukrainian expressions (Мені подобається, У мене є, Мене звати, Як справи?, Звідки ти?, Скільки коштує?, Мені ... років) can appear in ANY module as memorized chunks, even if the underlying grammar (dative, genitive, etc.) is not taught until later. This mirrors how Ukrainian children and L2 learners naturally acquire language. Do NOT flag these as forward-references. DO flag premature drilling of case paradigms, untaught vocabulary words, and grammar analysis before its module.
- [GLOBAL] Inline activity markers (<!-- INJECT_ACTIVITY: ... -->) must ONLY appear AFTER all concepts they test have been taught. If an activity tests both soft signs and apostrophes, it must appear after BOTH sections, not after the first one. This is critical in Ukrainian where apostrophe rules (б,п,в,м,ф,р + я,ю,є,ї) appear constantly — placing an apostrophe exercise before the apostrophe section teaches wrong sequencing. Rule: scan each activity's items and verify every tested concept has a preceding H2 section that teaches it.

# Section-by-Section Generation — Section 1/5

You are writing ONE SECTION of a Ukrainian language module. Write ONLY this section — nothing else.

**Module:** 3: Дієслова ходять парами (A2, A2.1 [Foundation and Aspect Introduction])
**Section to write:** Чому дієслова потрібно вчити парами? (~440 words total)
**Word target for this section:** 440 words (aim for 484 to account for undershoot)

---

## Section Skeleton (follow this exactly)

## Чому дієслова потрібно вчити парами? (~440 words total)

- P1 (~80 words): Hook — two contrasting sentences that show the aspect difference in action: "Я писала листа цілий вечір." vs. "Я написала листа." Both use the same verb root, but something fundamental changed. Pose the question: what is the difference? Guide the learner to feel the distinction before naming it.

- P2 (~100 words): Introduce the core concept: in Ukrainian, most verbs exist as a видова пара — an inseparable duo. One describes the process (недоконаний вид — what you were doing, що робити?), the other describes the completed act (доконаний вид — what you did/will do, що зробити?). Introduce the standard notation: imperfective / perfective, e.g., писати / написати. Learning only one form is like owning one chopstick — technically a real object, but useless without its pair.

- P3 (~80 words): Practical consequence: from today, every new verb entry has two slots. Not "писати" — but "писати / написати". Show how Ukrainian dictionaries (e.g., slovnyk.ua, e2u.org.ua) list aspect pairs together. Ukrainian school textbooks always present видові пари this way from Grade 5 onward (Заболотний §52).

- P4 (~80 words): Introduce the two-column mental model: Недоконаний вид (process, duration, repetition) | Доконаний вид (completed, one-time, result). Brief preview: three structural patterns will explain how most pairs are formed. Some pairs differ by a prefix (писати / написати), some by a suffix or vowel (запитувати / запитати), and a few are completely different words (брати / взяти).

- Dialogue (~100 words): Cooking varenyky scene — Бабуся reads the recipe aloud step by step while Онучка follows. Бабуся: "Ліпи вареники — ось так, знову і знову." Онучка: "Я злípила перший!" Бабуся: "Чудово! Тепер вари їх рівно десять хвилин." Онучка: "А скільки ще варити?" Бабуся: "Як тільки зваришь — вони спливуть на поверхню." Use bold to highlight the pairs: ліпити / зліпити (to shape, one by one → to finish shaping one); варити / зварити (to boil, ongoing → to finish boiling). The recipe context makes the aspect contrast concrete.

---

---
## Full Plan (for reference)

<plan_content>
module: a2-003
level: A2
sequence: 3
slug: aspect-in-vocabulary
version: '1.0'
title: Дієслова ходять парами
subtitle: Як утворюються та вивчаються видові пари
focus: grammar
pedagogy: PPP
phase: A2.1 [Foundation and Aspect Introduction]
word_target: 2000
objectives:
- Learner can recognize that most Ukrainian verbs exist in aspectual pairs and understand
  the importance of learning them together.
- 'Learner can identify the three main patterns of aspect pair formation: prefixation,
  suffix/root vowel change, and suppletion.'
- Learner can list and use approximately 20 essential A2-level aspectual pairs in
  simple sentences.
- Given one verb from a common pair, the learner can name its aspectual partner.
dialogue_situations:
- setting: 'Cooking varenyky together — one person reads the recipe step by step:
    Ліпи (impf, keep forming) вареники. Зліпи (pf, form one). Вари (impf) 10 хвилин.
    Звари (pf) до готовності.'
  speakers:
  - Бабуся (teaching recipe)
  - Онучка (cooking)
  motivation: 'Aspect pairs in cooking: ліпити/зліпити, варити/зварити'
content_outline:
- section: Чому дієслова потрібно вчити парами? (Why Verbs Must Be Learned in Pairs)
  words: 400
  points:
  - Reinforce the idea that aspect is fundamental. Learning a verb without its partner
    is like learning only half a word.
  - 'Introduce the standard notation: imperfective / perfective (e.g., робити / зробити).'
  - 'Using a dictionary: how to find aspectual pairs in online or paper dictionaries.'
- section: 'Спосіб 1: Додавання префікса (Method 1: Adding a Prefix)'
  words: 600
  points:
  - 'The most common way to form a perfective verb: add a prefix to the imperfective
    base. The prefix often adds a specific meaning, but for now, we focus on its role
    in creating a perfective verb.'
  - 'Core examples: писати / **на**писати; читати / **про**читати; робити / **з**робити;
    бачити / **по**бачити; готувати / **при**готувати.'
  - 'Practice: given an imperfective verb, learner adds the correct prefix to make
    it perfective.'
- section: 'Спосіб 2: Зміна в корені або суфіксі (Method 2: Change in the Root or
    Suffix)'
  words: 600
  points:
  - 'The ''imperfectivization'' pattern: a complex perfective verb (often with a prefix)
    gets an ''-ува-'' or ''-юва-'' suffix to become imperfective.'
  - 'This is a more advanced concept, so we introduce it with simple pairs: відповідати
    / відповісти; вирішувати / вирішити; запитувати / запитати.'
  - 'Show the vowel change that often accompanies this: ''о'' -> ''а'' (допомогти
    / допомагати).'
- section: 'Спосіб 3: Зовсім інші слова (суплетивізм) (Method 3: Completely Different
    Words - Suppletion)'
  words: 400
  points:
  - Some of the most common verbs have suppletive pairs that must be memorized.
  - 'Essential pairs: брати / взяти (to take); говорити / сказати (to say/tell); ловити
    / зловити (to catch); шукати / знайти (to look for / to find).'
  - Present a list of the 20 most important aspectual pairs for A2 learners to memorize,
    covering all three formation types.
vocabulary_hints:
  required:
  - пара (pair)
  - префікс (prefix)
  - суфікс (suffix)
  - корінь (root)
  - читати / прочитати (to read)
  - писати / написати (to write)
  - брати / взяти (to take)
  - говорити / сказати (to speak / to say)
  recommended:
  - утворювати (to form)
  - словник (dictionary)
  - запам'ятовувати (to memorize)
  - базовий (basic)
activity_hints:
- type: quiz
  focus: Find the Partner (Verb Matching)
  items: 8
- type: fill-in
  focus: Categorize by Formation Type
  items: 8
- type: match-up
  focus: Fill in the Blanks with the Correct Pair
  items: 8
- type: match-up
  focus: Sentence Translation (Aspect Focus)
  items: 8
references:
- title: Заболотний Grade 6, §52-54
  notes: 'Вид дієслова: доконаний і недоконаний'
- title: 'ULP: Ukrainian Verb Aspect'
  url: https://www.ukrainianlessons.com/ukrainian-verb-aspect/
  notes: Imperfective vs perfective

</plan_content>

---

## Knowledge Packet

<knowledge_packet>
# Verified Knowledge Packet: Дієслова ходять парами
**Module:** aspect-in-vocabulary | **Phase:** A2.1 [Foundation and Aspect Introduction]
**Textbook grades searched:** 1, 2, 3, 5

---

## Чому дієслова потрібно вчити парами? (Why Verbs Must Be Learned in Pairs)

> **Source:** vashulenko, Grade 2
> **Section:** Сторінка 78
> **Score:** 0.33
>
> § 14 СЛОВА — НАЗВИ Дій 
> предметів (дієслова)
> НАВЧАЮСЯ ВИЗНАЧАТИ СЛОВА — НАЗВИ 
> дій предметів
> у, — учителька
> Прочитай і розкажи 
> ; у класі.
> 1
> визначаю
> Я — учитель
> що робить?
> — - — ■*
> що робив?
> що зробить?
> В українській мові є слова — назви дій предметів, 
> які відповідають на питання що робити? 
> що робить? що роблять? що робив? що зробив? 
> що буде робити? що зробить?. Це дієслова.
> Вивчіть напам'ять уривок із 
> і розкажіть одне одному.
> Дієслово — слово діє: 
> ходить, робить, носить, сіє. 
> Слово плаче і радіє, 
> усміхається і мріє.
> вірша Лесі Лужецької
> • Випишіть за абеткою слова — назви дій предметів. На яке 
> питання вони відповідають?
> 2| Утвори і запиши прислів'я. Назви дієслова. Усно постав до них 
> питання.
> Що посієш,
> Під лежачий камінь
> Робиш наспіх —
> /
> зробиш на сміх. 
> те й пожнеш.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 144
> **Score:** 0.50
>
> 144
> Поняття про дієслово як частину 
> мови
> Навчаюся визначати дієслова
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> писати
> пише
> пишуть
> писав
> написав
> напише
> 45
> Слова, які називають дії предметів і відповідають на 
> питання що робити? що робить? що роблять? що 
> робив? що зробив? що буде робити? що зробить?, 
> є дієсловами. Дієслово — це частина мови.
> 	 	
> 1   Вивчіть напам’ять вірш Володимира Верховеня. Розкажіть одне 
> одному.
>   Випишіть із вірша дієслова за абеткою. Що вони називають? На які 
> питання відповідають?
> А дієслово ні хвилини,
> повір, без дії не живе:
> працює, вчить, співає, лине,
> читає, грається, пливе.
> спільнокореневі
> різні форми слова
> Слова  
> співає, співаєш, співають
> ? 
> 2   Допиши прислів’я, користуючись довідкою.

> **Source:** kravcova, Grade 2
> **Section:** Сторінка 87
> **Score:** 0.25
>
> 87
> 312. Утвори прислів’я. 
> 313. 1.	 Вибери навчальний предмет. 
> 2.	 Напиши чотири дієслова, які означають навчальні дії.
> 314. До поданих іменників добери дієслова за зразком та 
> запиши утворені пари.
> 315. 1.	 Прочитай прислів’я та поясни їх зміст.
> Не говори, що знаєш, але знай, що говориш. Сказав, як 
> сокирою одрубав. Що вимовиш язиком, то не витягнеш і волом.
> 2.	 Спиши. Підкресли дієслова.
> 2 учиться — 4 пригодиться. 3 завжди 1 Потрібно
> Зразок. Радість — радіти.
> радість	
> 	
> 	
> сум	 	
> 	
> тривога
> співчуття	 	
> 	
> жаль		
> 	
> обурення
> гордість	 	
> 	
> повага	
> 	
> заздрість
> 316. 1.	 Прочитай вірш.

## Спосіб 1: Додавання префікса (Method 1: Adding a Prefix)

> **Source:** zabolotnyi, Grade 5
> **Section:** Сторінка 67
> **Score:** 0.50
>
> 64
> 146.	І. Прочитайте виразно слова вголос. Обґрунтуйте написання пра-
> вилом. 
> Пришити, прибудувати, презавзятий, придорожній, пре-
> злий, прибережний, привокзальний, премудрий, прикову-
> вати, преніжний. 
> ІІ. Запишіть слова в три колонки залежно від значення префікса.
> Наближення,  
> приєднання 
> Розміщення  
> біля чогось
> Найвищий ступінь  
> вияву ознаки
> 147.	І. Спишіть слова, уставляючи пропущену букву е, и або і. Обґрун-
> туйте написання. Правильність написання перевірте за орфографіч-
> ним словником. 
> Пр..вітати, пр..щедрий, пр..звище, пр..лютий, пр..по-
> рошений, пр..солодкий, пр..сісти, пр..дорого, пр..гальмува-
> ти, пр..горіти, пр..чудово, пр..рва, пр..г¾рклий, пр..гіркий, 
> пр..перчити, пр..смачний.
> ІІ. Складіть і запишіть по одному реченню з кожним виділеним словом. 
> 148.	І. СИТУАЦІЯ.

## Спосіб 2: Зміна в корені або суфіксі (Method 2: Change in the Root or Suffix)

> **Source:** bolshakova, Grade 2
> **Section:** Сторінка 83
> **Score:** 0.50
>
> 83
> роЗДІЛ 4. БУДова сЛова
> БУДова сЛова. ЗакІнчЕння. основа
> Слово складається з частин. У слові є основа і закін-
> чення. Закінчення — це частина слова, яка зміню-
> ється. основа — частина слова без закінчення.
> Визнач закінчення у слові риба. Що потрібно зробити, щоб 
> визначити закінчення? Назви основу слова.
>     РИБа            (немає) РИБи      (їсть) РИБУ
>  
> Які питання ставлять діти, щоб змінити слово?
> (немає) 
> кого? чого?
> (даю) 
> кому? чому?
> (задоволений) 
> ким? чим?
> як виЗначити ЗакІнчЕння Й основУ сЛова
> РИБа 
> РИБи
> РИБа 
> РИБи
> РИБ а 
> РИБ и
> Зміни слово 
> за питаннями
> Познач частину сло-
> ва, яка змінюється
> Познач частину слова 
> без закінчення
> Зміни слова. Визнач закінчення й основу слів. Розподіли 
> слова на групи.

> **Source:** vashulenko, Grade 3
> **Section:** Сторінка 100
> **Score:** 0.33
>
> 100
> Навчаюся розбирати слова за будовою
> 6   Розбери за будовою слова.
>  сніги 
> морозець 
> біленький
> безбарвний
> Зразок усного розбору слова за будовою
> У слові безмежний закінчення -ий, основа безмежн-, бо 
> воно змінюється так: безмежний, безмежному, безмежним. 
> Корінь -меж-, бо такий самий корінь є у спільнокореневих 
> словах межа, межувати. Префікс без-, суфікс -н-.
> Зразок письмового розбору слова за будовою
> Безмежн ий  	 	
> 	
> 	
> сніжок 
>  
> 	 	
> 7   Розберіть  слова за будовою (письмово).
> Сад — садок, кущ — кущик, хліб — хлібець, мир — мирний, 
> хмарний — безхмарний, учитель — учителька.
> 	 	
>   Поясни, які частини другого слова змінили значення першого 
> слова. Познач їх.

## Спосіб 3: Зовсім інші слова (суплетивізм) (Method 3: Completely Different Words - Suppletion)

> **Source:** zaharijchuk, Grade 1
> **Section:** Сторінка 30
> **Score:** 0.50
>
> 28
> Вшниі, шаркептик, шмкруаа, 
> шшпииан, аачкш.
> 	
> «Збери» слова — назви намальованих пред-
> метів. Поділи на склади слово, у якому дві 
> букви ш (усно).
> Бачу Ш, ш (ша). Чую [ш].
> ш и н ш и
> ш и ш к
> к о м и ш
> и
> а
> л
> а
> о
> у
> и
> і
> Ш
> ша
> шо
> шу
> ши
> ші
> а
> о
> у
> и
> і
> аш
> ош
> уш
> иш
> іш
> Ш
> ша-                  
> шо-                       шпа-                   
> ши
> шка
> на
> шу
> м
> міти
> ше
> лест
> рех
>  [  –  •–  |  –•|  –•] 
>  [  –  •|  –  •– ] 
> Ш ш
> Pidruchnyk.com.ua


## МійКлас Theory (miyklas.com.ua)

*Ukrainian school curriculum theory — use this terminology and teaching approach.*

### Правила вживання знака м'якшення
> **Source:** МійКлас — [Правила вживання знака м'якшення](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/fonetika-grafika-orfoepiia-orfografiia-14565/pravila-vzhivannia-znaka-m-iakshennia-39904)

### Теорія:
  

*www.ua.pistacja.tv*  
 
Знаком ь позначаємо м’якість приголосних звуків на письмі.
Знак м’якшення пишемо:
- Ь пишеться після м’яких д, т, з, с, дз, ц, л, н у кінці **слова** та **складу**: *дядько, радість, низько, заносьте, гедзь, доброволець, коваль, тінь.
*  
- Після **м’яких** приголосних у **середині складу** перед о: *чотирьох, дзьоб, сьомий, льодяний, відьом*.

### Речення, його граматична основа
> **Source:** МійКлас — [Речення, його граматична основа](https://www.miyklas.com.ua/p/ukrainska-mova/5-klas/vidomosti-z-sintaksisu-i-punktuatciyi-14562/rechennia-iogo-gramatichna-osnova-pidmet-i-prisudok-39372)

### Теорія:

*www.ua.pistacja.tv*  
Речення
Реченням називаємо одне або кілька слів, що виражають закінчену думку.
Саме за допомогою речень ми спілкуємось, висловлюємо прохання, наказ, виражаємо емоції, повідомляємо інформацію.
Приклад:
- Весна іде, красу несе \(Нар. творчість\). 
- Ліс. Тиша. Благодать. 
Слова в реченні зв'язані між собою **за змістом** і **граматично**. **Граматичний зв'язок** — це поєднання за допомогою **закінчень** і **службових слів**. На початок і кінець речення вказує **інтонація**. Між реченнями робимо **паузи**.
Ознаки речення
1. Речення відображає дійсність. Інформація **стверджується** або **заперечується**, сприймається як **реальна** або **нереальна**, **можлива** або **неможлива**.
 

... (truncated for context window)
</knowledge_packet>

---

## Rules

TARGET: 45-65% Ukrainian.
LANGUAGE ROLES:
- THEORY: English prose for grammar explanations that would be too complex in Ukrainian at this level.
- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.
- HEADERS: Ukrainian with English in parentheses.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence. Ukrainian paragraphs and dialogues carry most content. English appears for grammar theory and in callout boxes.
A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles.

GRAMMAR RULES:
- Max 15 words per Ukrainian sentence
- Max 2 clauses per sentence
- All cases allowed
- Simple subordinate clauses allowed (який/що/коли)
- Aspect pairs introduced but not complex
- No participles



- **NO IPA, NO Latin transliteration** — describe sounds by comparison.
- **Ukrainian quotes: «...»** for Ukrainian text.
- **Place exercise markers only** — write `<!-- INJECT_ACTIVITY: type, topic hint -->` where the skeleton places exercises. Do NOT write :::quiz or :::fill-in DSL directly.
- **NO meta-commentary** — no "In this section we will...", no vocabulary tables, no word count notes.
- **Zero Russian, zero Surzhyk, zero calques.**
- **Every bold Ukrainian word MUST have an English translation on first use.**
- **NO stress marks** — a deterministic tool adds them later.
- **Dialogue formatting:** Use blockquote `>` with speaker names in bold. Each turn on its own line.

## Output

Write the section starting with the H2 heading. Output ONLY the section content — no preamble, no summary, no notes.
