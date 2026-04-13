<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/euphony-advanced.yaml` file for module **12: Милозвучність у складних контекстах** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: match-up-match-sentence-beginnings-with-euphonically-correct-continuations -->`
- `<!-- INJECT_ACTIVITY: error-correction-find-euphony-errors-in-sentences-e-g-and-correct-them -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-preposition-or-conjunction-form -->`
- `<!-- INJECT_ACTIVITY: quiz -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct euphonic variant (у/в, з/із/зі, і/й) in context
  items: 8
  type: quiz
- focus: Complete sentences with the correct preposition or conjunction form
  items: 8
  type: fill-in
- focus: Find euphony errors in sentences (e.g., *в вікно, *з школи, *і усі) and correct
    them
  items: 8
  type: error-correction
- focus: Match sentence beginnings with euphonically correct continuations
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спрощення (simplification)
- уникати (to avoid)
- мелодійний (melodious)
- межа (boundary)
- правило (rule)
required:
- милозвучність (euphony, melodiousness)
- евфонія (euphony (technical term))
- чергування (alternation)
- голосний (vowel)
- приголосний (consonant)
- збіг (cluster, collision)
- прийменник (preposition)
- сполучник (conjunction)
- вживати (to use, to apply)
- складний (complex, compound)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## У чи в? Складні випадки (U or V? Complex Cases) (~660 words)

When native speakers talk fast, the language flows like a beautiful song. This natural rhythm is called **милозвучність** (euphony, melodiousness). It is not just an optional style choice; it is a strict grammar rule. Let's listen to Olenka and Taras planning a weekend trip. Notice the small prepositions and the **сполучник** (conjunction) they use to connect words.

> — **Оленка:** Поїдемо в Карпати чи у Львів? *(Shall we go to the Carpathians or to Lviv?)*
> — **Тарас:** У Львів! Із задоволенням! *(To Lviv! With pleasure!)*
> — **Оленка:** Я поїду з Оленою й Тарасом. *(I will go with Olena and Taras.)*
> — **Тарас:** А ви зі Львова повернетесь у неділю? *(And will you return from Lviv on Sunday?)*

In just four lines, they changed the little connecting words multiple times. Olenka said «в Карпати» but «у Львів». Taras used «із» and «зі» instead of just «з». This is **евфонія** (euphony (technical term)) in action. The language actively changes its shape to sound better.

To understand how this works, we must review the basic rule for the **прийменник** (preposition) «у» or «в». You already know that the choice depends on the sounds around the word. A **голосний** (vowel) loves to sit next to a **приголосний** (consonant). 

Мій брат зараз у домі. Він працює там щодня. А моя сестра була в Одесі. Вона там відпочивала.

> *My brother is currently in the house. He works there every day. And my sister was in Odesa. She rested there.*

In the first sentence, we use «у» because it sits between two consonants. In the second sentence, we use «в» because it sits between two vowels. We want to avoid a **збіг** (cluster, collision) of identical sound types. This **чергування** (alternation) makes speaking much easier for everyone.

However, real speech is a **складний** (complex, compound) flow of words. What happens at the beginning of a sentence? At the start of a sentence, we look only at the first letter of the next word. If the next word starts with a vowel, we use «в». If it starts with a consonant, we use «у» to create a smooth sound transition.

В Україні зима часто буває холодна. У лісі зараз дуже багато снігу.

> *In Ukraine, winter is often cold. In the forest, there is a lot of snow right now.*

Punctuation marks act like a hard reset. A comma, a period, or a dash creates a pause in your speech. After this pause, the phonetic environment starts over completely. You must apply the rule as if it is the beginning of a brand new sentence.

Мабуть, в Одесі зараз тепло. У лісі, у полі волого й тихо.

> *Probably, it is warm in Odesa right now. In the forest, in the field, it is damp and quiet.*

Learners often memorize a preposition together with a specific noun, like the phrase «у школі» (at school). But the preposition does not belong to the noun at all. The surrounding sounds determine the choice, not the word's base form. We must **вживати** (to use, to apply) the correct variant based on the whole phrase in the sentence.

Мій молодший брат зараз у школі. Але мій старший брат вчиться в університеті.

> *My younger brother is currently at school. But my older brother studies at the university.*

Why do we say «у школі» here? Because «брат в школі» creates a terrible cluster of three consonants. The language fixes this by using «у». Why do we say «в університеті»? Because «вчиться у університеті» creates a clash of three vowels. The letter «в» breaks up this vowel collision perfectly.

:::info
**Grammar box**
Always look at the last letter of the previous word and the first letter of the next word. The preposition is just a phonetic bridge between them.
:::

This rule is so strong that it even changes the first letter of some words. Many common verbs and nouns have two forms. You will see words like «увійти» and «ввійти» (to enter), or «учитель» and «вчитель» (teacher). The choice follows the exact same phonetic logic. The word itself changes to protect the natural rhythm of the sentence.

Наш новий учитель дуже цікаво розповідає. Наша нова вчителька теж чудова. Увечері він прийшов додому. Він швидко увійшов до кімнати.

> *Our new teacher explains things very interestingly. Our new female teacher is also wonderful. In the evening, he came home. He quickly entered the room.*

After a consonant, we use the form starting with «у», like «новий учитель» or «швидко увійшов». After a vowel, we switch to the form starting with «в», like «нова вчителька». Even at the beginning of a sentence before a consonant, we write «Увечері».

There is one special exception you must memorize. It concerns words that begin with the letters В or Ф, or consonant clusters like ТВ, СВ, ЛЬВ, and ХВ. Before these words, we ALWAYS use «у», no matter what comes before them. We do this to avoid repeating the «V» or «F» sound, which is very hard to say twice in a row.

Я вчора був у Львові. Мій друг працює у великій компанії. Вона має успіх у творчості. Ми дивилися у вікно.

> *Yesterday I was in Lviv. My friend works in a large company. She has success in creativity. We looked into the window.*

A very common mistake for learners is to say «в вікно» or «в Львові». This forces you to stutter on the consonant. Always say «у вікно» and «у Львові». Your tongue will thank you, and you will immediately sound like a native speaker.

:::tip
**Quick tip**
If the next word starts with «в» or «ф», don't even look at the previous word. Just use «у».
:::

<!-- INJECT_ACTIVITY: match-up-match-sentence-beginnings-with-euphonically-correct-continuations -->

## З, із чи зі? Правила перед збігами приголосних (Z, Iz, or Zi?) (~660 words)

The **прийменник** (preposition) meaning "with" or "from" has three forms to maintain **милозвучність** (euphony, melodiousness). The default form is «з». We use it most of the time when there is no **збіг** (cluster, collision) of difficult sounds.

Прийменник «з» — це основний варіант. Ми найчастіше вибираємо цю коротку форму. Вона чудово звучить перед голосним та перед багатьма приголосними звуками. Наприклад, ми кажемо «з братом» або «з Оленою». Але українська мова любить мелодійність і уникає важких звуків. Якщо наступне слово має складний початок, ми змінюємо прийменник. Це особливо важливо перед шиплячими та свистячими приголосними, як-от «ш», «щ», «з» або «с».

> *The preposition «з» is the main variant. We most often choose this short form. It sounds wonderful before a vowel and before many consonant sounds. For example, we say "with a brother" or "with Olena". But the Ukrainian language loves melodiousness and avoids heavy sounds. If the next word has a complex beginning, we change the preposition. This is especially important before hissing and sibilant consonants, such as «ш», «щ», «з», or «с».*

When we have a collision of consonants, we often need a longer phonetic bridge. The variant «із» adds a **голосний** (vowel) sound to create space.

Ми **вживаємо** (to use, to apply) варіант «із» між групами приголосних. Наприклад, ми скажемо «лист із Бразилії», щоб зробити паузу для дихання. Також ми обираємо «із» перед словами, які починаються на «з», «с», «ц», «ш», «ч» або «ж». Мій сусід учора повернувся із села. Вона отримала довгий лист із Запоріжжя. Цей голосний звук допомагає нашому язику підготуватися до наступного приголосного.

> *We use the variant «із» between groups of consonants. For example, we will say "a letter from Brazil" to take a breath. We also choose «із» before words that start with «з», «с», «ц», «ш», «ч», or «ж». My neighbor returned from the village yesterday. She received a long letter from Zaporizhzhia. This vowel sound helps our tongue prepare for the next consonant.*

:::note
**Quick tip**
Think of «із» as a soft cushion. It prevents two hard consonants from crashing into each other, keeping the sentence flowing smoothly and naturally.
:::

Sometimes, the beginning of the next word is so **складний** (complex, compound) that even «із» isn't enough. For the hardest clusters, we use «зі». This is a strict **чергування** (alternation) rule.

Форма «зі» працює перед найважчими збігами приголосних на початку слова. Вона обов'язкова, коли ці збіги починаються на «з», «с», «ш» або «щ». Діти радісно бігли зі школи додому. Мій колега приїхав зі Львова на конференцію. Також існує рідкісне чергування з формою «зо». Ми вживаємо його лише з числівниками «два» та «три». Ми чекали на нього зо два дні.

> *The form «зі» works before the hardest consonant clusters at the beginning of a word. It is mandatory when these clusters start with «з», «с», «ш», or «щ». The children happily ran from school towards home. My colleague arrived from Lviv for a conference. There is also a rare alternation with the form «зо». We use it only with the numerals "two" and "three". We waited for him for about two days.*

In the Genitive case, you will apply these rules constantly to say where someone is from or what group they belong to. Let's see how they affect families and places.

Він походить з великої родини. Цей студент приїхав із сім'ї лікарів. Вони щойно повернулися зі школи. Ці правила також впливають на займенники. Скупчення звуків «мн» дуже незручне. Тому ми завжди кажемо «зі мною». Але інші займенники не мають таких проблем. Ми спокійно кажемо «з ним» або «з нею», бо приголосний «н» звучить легко.

> *He comes from a large family. This student came from a family of doctors. They just returned from school. These rules also affect pronouns. The cluster of sounds «мн» is very uncomfortable. Therefore, we always say "with me". But other pronouns do not have such problems. We calmly say "with him" or "with her" because the consonant «н» sounds easy.*

Learners often force unnatural combinations by sticking only to the default form «з» or over-applying the exception «зі». True **евфонія** (euphony (technical term)) requires paying attention to the sounds that follow.

Іноземці часто роблять помилку і кажуть «з школи». Це створює дуже різкий збіг «з-шк», який звучить дуже погано. Правильно казати «зі школи». Інша популярна помилка — «з мною». Це важко вимовити швидко, тому завжди кажіть «зі мною». Іноді студенти додають зайві голосні. Вони кажуть «зі ним», але тут немає складного збігу приголосних. Правильний варіант — «з ним».

> *Foreigners often make a mistake and say «з школи». This creates a very harsh cluster «з-шк», which sounds very bad. It is correct to say «зі школи». Another popular mistake is «з мною». This is hard to pronounce quickly, so always say «зі мною». Sometimes students add unnecessary vowels. They say «зі ним», but there is no complex consonant cluster here. The correct variant is «з ним».*

<!-- INJECT_ACTIVITY: error-correction-find-euphony-errors-in-sentences-e-g-and-correct-them -->

## І чи й? У складних реченнях (I or Y? In Complex Sentences) (~550 words)

The rules for the **сполучник** (conjunction) "and" follow the same principles. We choose between «і» and «й» depending on whether we connect a **голосний** (vowel) or a **приголосний** (consonant). 

Ми завжди обираємо «й» між двома голосними звуками: «Ольга й Андрій». Але якщо слова закінчуються і починаються на приголосний, ми повинні вживати «і»: «син і мати». Ці самі правила працюють у складних реченнях.

> *We always choose «й» between two vowel sounds: "Olha and Andriy". But if the words end and begin with a consonant, we must use «і»: "son and mother". These same rules work in complex sentences.*

When building complex sentences, pay close attention to commas. A comma represents a natural pause that completely resets the phonetic context, so you only look at the sound *after* the comma to know which word to **вживати** (to use, to apply).

Після коми ми робимо паузу, тому попередній звук не має значення. Найбезпечніший варіант після коми — завжди «і»: «Він прийшов, і ми поїхали». Іноді студенти бачать наступний голосний і пишуть «й»: «Вона заспівала, й усі заплакали». Це помилка, бо після паузи звук «й» губиться. Правильно: «Вона заспівала, і усі заплакали».

> *After a comma we make a pause, so the previous sound doesn't matter. The safest option after a comma is always «і»: "He arrived, and we left". Sometimes students see the next vowel and write «й»: "She started singing, and everyone started crying". This is a mistake, because after a pause the «й» sound gets lost. Correct: "She started singing, and everyone started crying" (with і).*

When listing multiple items, analyze each pair of words independently to keep the sentence melodious.

Ми дивимося на кожну пару слів окремо. Ми купуємо хліб і масло, бо тут є приголосні. Потім ми беремо каву й молоко, бо тут є голосні. Якщо ми хочемо зробити салат, ми купуємо помідори й огірки. Кожен сполучник вимагає нового аналізу.

> *We look at each pair of words separately. We buy bread and butter (і), because there are consonants here. Then we take coffee and milk (й), because there are vowels here. If we want to make a salad, we buy tomatoes and cucumbers (й). Each conjunction requires a new analysis.*

There are two special situations where «і» is mandatory. First, always use «і» before words starting with й, я, ю, є, or ї. Second, «і» is required when contrasting two concepts, because a slight pause emphasizes the contrast.

Ми ніколи не ставимо «й» перед словами, які вже мають цей звук на початку. Ми завжди кажемо «Одеса і Ялта». Також ми зберігаємо «і» для філософських або контрастних понять. Ми читаємо про батьків і дітей, думаємо про добро і зло. Тут граматика важливіша за милозвучність.

> *We never put «й» before words that already have this sound at the beginning. We always say "Odesa and Yalta". We also keep «і» for philosophical or contrasting concepts. We read about fathers and children, think about good and evil. Here grammar is more important than euphony.*

If these rules feel overwhelming, there is a convenient alternative: the conjunction «та». It means the same thing, but it never alternates and works between any sounds.

Сполучник «та» — це чудовий помічник. Він ніколи не змінює свою форму. Ви можете вільно казати «мама та тато» замість «мама й тато». Це допомагає уникати повторень у довгих реченнях. Коли ви вже використали багато «і» та «й», просто додайте «та» для різноманітності.

> *The conjunction «та» is a great helper. It never changes its form. You can freely say "mom and dad" (with та) instead of "mom and dad" (with й). This helps to avoid repetitions in long sentences. When you have already used a lot of «і» and «й», simply add «та» for variety.*

:::tip
**Quick tip** — When connecting nouns in a list, «та» simply means "and". However, in other contexts it can sometimes mean "but" (like «Він обіцяв, та не прийшов»), so pay attention to the flow of the sentence.
:::

<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-preposition-or-conjunction-form -->

## Все разом: мелодійні речення (Putting It All Together) (~330 words)

Now we can build multi-clause sentences and see how these rules interact. The ultimate goal is **милозвучність** (euphony, melodiousness). To achieve this natural flow, we rely on **чергування** (alternation). We do this to prevent an awkward **збіг** (cluster, collision) of sounds.

Ми поїхали у Львів із друзями й провели чудовий вихідний. Ми ставимо «у» перед словом «Львів», бо воно починається на специфічну групу приголосних. Далі ми вибираємо «із», бо слово «друзями» має два приголосні звуки на початку. Нарешті, ми використовуємо «й» після голосного «и» перед приголосним «п». Це робить речення плавним.

> *We went to Lviv with friends and spent a wonderful weekend. We put "у" before the word "Львів" because it starts with a specific group of consonants. Next, we choose "із" because the word "друзями" has two consonant sounds at the beginning. Finally, we use "й" after the vowel "и" before the consonant "п". This makes the sentence smooth.*

Ukrainian euphony is a natural process, not a rigid mathematical formula. Linguists formally call this concept **евфонія** (euphony (technical term)). We must always analyze whether a word ends in a **голосний** (vowel) or a **приголосний** (consonant) to maintain the spoken rhythm.

Читайте українські тексти вголос кожного дня. Ви швидко відчуєте, як працює справжня милозвучність. Ваш язик сам хоче уникати нагромадження звуків. Якщо фраза звучить занадто важко, ви інтуїтивно знайдете правильне слово. Секрет полягає в тому, щоб слухати мелодію мови.

> *Read Ukrainian texts aloud every day. You will quickly feel how true euphony works. Your tongue itself wants to avoid a pile-up of sounds. If a phrase sounds too heavy, you will intuitively find the correct word. The secret is to listen to the melody of the language.*

Mastering these small connecting words is the secret to sounding like a native speaker. The surrounding sounds tell us which **прийменник** (preposition) or **сполучник** (conjunction) we need to **вживати** (to use, to apply) when linking ideas together. The rules for "у/в", "з/із/зі", and "і/й" all serve the same phonetic purpose.

Маленькі слова будують велику гармонію. Коли ви говорите плавно, українці чують, що ви поважаєте їхню мову. Ви більше не робите пауз між словами, а поєднуєте їх. Це робить вашу вимову дуже природною.

> *Small words build great harmony. When you speak smoothly, Ukrainians hear that you respect their language. You no longer make pauses between words, but connect them. This makes your pronunciation very natural.*

These principles are essential, especially when building a **складний** (complex, compound) sentence. While an L2 learner might produce a clunky rhythm, a speaker who understands euphony will connect their thoughts effortlessly.

:::tip
**Quick tip** — Don't overthink the rules when speaking. If you stumble over a cluster of sounds, you probably picked the wrong connecting word. Trust your ear and let the language flow naturally!
:::

<!-- INJECT_ACTIVITY: quiz -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: euphony-advanced
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

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

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 12/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

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


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

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
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
