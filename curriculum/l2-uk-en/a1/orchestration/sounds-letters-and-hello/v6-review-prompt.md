<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 1: Sounds, Letters, and Hello (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-001
level: A1
sequence: 1
slug: sounds-letters-and-hello
version: '1.4'
title: Sounds, Letters, and Hello
subtitle: 33 літери, 38 звуків, Привіт!
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Understand the difference between sounds (звуки) and letters (літери) — the foundational distinction in Ukrainian phonetics
- Recognize the two families of sounds — vowels (голосні) and consonants (приголосні) — and how they are formed
- Know why Ukrainian has 33 letters but 38 sounds, and which letters represent multiple sounds
- Meet the Ukrainian alphabet through Anna Ohoiko's letter videos — hear each sound, see each letter
- Say hello and respond to a greeting
content_outline:
- section: "Звуки і літери (Sounds and Letters)"
  words: 300
  points:
  - "Golden rule from Заболотний Grade 5 p.83: 'Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо.'
    We hear and pronounce sounds (звуки). We see and write letters (літери). These are NOT the same thing.
    A letter is a symbol on paper. A sound is what your mouth produces. This distinction is the foundation
    of Ukrainian phonetics — Ukrainian teachers drill it from Grade 1."
  - "Ukrainian has 33 letters (літери) but 38 sounds (звуків). Why the mismatch? Some letters represent
    two sounds (Я, Ю, Є, Ї in certain positions). One letter (Ь) makes no sound at all — it only softens
    the consonant before it. Litvinova Grade 5 p.130 asks: 'Чи можна говорити «голосна літера»?' Answer: no!
    Sounds are голосні or приголосні, not letters. Letters only represent sounds."
  - "The Ukrainian alphabet (абетка/алфавіт): all 33 letters in order. Each letter has a name.
    Unlike English, Ukrainian spelling is highly phonetic — what you see is (mostly) what you hear.
    No silent letters, no surprise pronunciations. Once you know the sounds, you can read any word."
- section: "Голосні звуки (Vowel Sounds)"
  words: 250
  points:
  - "Большакова Grade 1 p.24 teaches vowels through a poem: 'Голосні почуєш в пісні, і у темному у лісі,
    і коли дивуєшся, і коли милуєшся. Легко вимовляються, весело співаються!'
    Голосні (vowels) are made with voice only — air flows freely through the mouth with no obstruction.
    You can sing them. You can shout them across a field."
  - "6 vowel sounds: [а], [о], [у], [е], [и], [і]. But 10 vowel letters: А, О, У, Е, И, І, Я, Ю, Є, Ї.
    The extra four (Я, Ю, Є, Ї) are 'iotated' — they can represent two sounds. Full details in M02.
    For now: every Ukrainian word has at least one vowel sound. Vowels are the heart of every syllable."
  - "Захарійчук Grade 1 p.13 notation: vowel sounds are marked [•] in sound models.
    Practice hearing vowels: мА-мА (two [а]), мО-лО-кО (three [о]), У-ля (one [у]).
    Anna Ohoiko video for each vowel letter — watch, listen, repeat."
- section: "Приголосні звуки (Consonant Sounds)"
  words: 250
  points:
  - "Большакова Grade 1 p.24: 'Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять.'
    Приголосні (consonants) are made with voice + noise or noise only. Your lips, teeth, or tongue
    create an obstruction. You cannot sing a pure consonant — try singing [к] or [п]."
  - "32 consonant sounds from 22 consonant letters. Some consonants come in pairs: тверді (hard) and м'які (soft).
    Захарійчук Grade 1 p.15: hard sounds marked [–], soft sounds marked [=].
    This hard/soft distinction doesn't exist in English — it's uniquely Slavic."
  - "Consonant letters to meet through Anna Ohoiko videos: М, Н, С, К, Л, Р, Б, В, Д, П, Т, Г, Ґ, З, Ж, Ш, Х, Й, Ч, Щ, Ц, Ф.
    Each video shows the letter, demonstrates the sound, and gives example words.
    Special: Ґ is uniquely Ukrainian. Щ always = two sounds [шч]. Ь (м'який знак) makes no sound —
    it softens the consonant before it."
- section: "Привіт! (Hello!)"
  words: 250
  points:
  - "Your first Ukrainian conversation. Following Anna Ohoiko ULP Episode 1.
    Привіт! — Hi! (informal, for friends, family, peers).
    Як справи? — How are you? Answers: Добре (fine). Чудово (great). Нормально (okay).
    А у тебе? — And you?"
  - "Рада тебе бачити! (female speaker) / Радий тебе бачити! (male speaker) — Glad to see you!
    Ukrainian has gendered forms — women say рада, men say радий. This is your first encounter
    with grammatical gender. It will become a major topic starting M08."
  - "Let's read Привіт letter by letter — your first sound analysis (звуковий аналіз):
    П [п] приголосний + р [р] приголосний + и [и] голосний + в [в] приголосний +
    і [і] голосний + т [т] приголосний. Two голосні, four приголосні.
    Every type of sound you learned in this module appears in this one word."
- section: "Підсумок (Summary)"
  words: 150
  points:
  - "Self-check questions: How many letters in the Ukrainian alphabet? (33) How many sounds? (38)
    Why are they different? What are голосні? What are приголосні? Can you say 'голосна літера'?
    (No — sounds are голосні, not letters!) What does Привіт mean? How do you answer Як справи?"
vocabulary_hints:
  required:
  - звук (sound)
  - літера (letter)
  - голосний (vowel sound)
  - приголосний (consonant sound)
  - привіт (hi, informal)
  - як справи (how are you)
  - добре (fine, good)
  - чудово (great, wonderful)
  - мама (mother)
  - молоко (milk)
  recommended:
  - нормально (okay)
  - тато (father)
  - око (eye)
  - дім (house)
  - ніс (nose)
  - сон (dream)
activity_hints:
- type: quiz
  focus: "Distinguish between sounds (звуки) and letters (літери). Example questions:
    'Що ми чуємо і вимовляємо?' → 'звуки' |
    'Що ми бачимо і пишемо?' → 'літери' |
    'Скільки літер в абетці?' → '33' |
    'Скільки звуків в українській мові?' → '38' |
    'Чи можна говорити «голосна літера»?' → 'Ні, голосний — це звук, не літера.'"
  items: 6
- type: match-up
  focus: "Match Ukrainian letters to the sounds they represent — following Захарійчук's
    'Бачу... Чую...' pattern. Pairs: А ↔ [а], О ↔ [о], У ↔ [у], М ↔ [м], К ↔ [к], Н ↔ [н].
    This is how Ukrainian first-graders learn: see the letter (бачу), hear the sound (чую)."
  items: 6
- type: fill-in
  focus: "Complete a basic greeting dialogue with blanks.
    '— {Привіт}! Як {справи}?' / '— {Добре}. А у {тебе}?' / '— {Чудово}.'
    Options per blank: Привіт / справи / Добре / тебе / Чудово / Нормально."
  items: 4
- type: group-sort
  focus: "Sort Ukrainian sounds into Голосні (vowels) and Приголосні (consonants).
    Голосні: [а], [о], [у], [е], [и], [і].
    Приголосні: [к], [м], [т], [в], [н], [р], [с], [х]."
  items: 8
- type: letter-grid
  focus: "Interactive alphabet card grid showing all 33 Ukrainian letters.
    Each card: upper/lower case, emoji key word, vowel/consonant coloring.
    Vowel letters highlighted differently from consonant letters.
    Ь marked as special (no sound)."
  items: 33
- type: watch-and-repeat
  focus: "Pronunciation practice with Anna Ohoiko videos.
    Vowels: А (hvB3VpcR3ZE), У (VB1O6PmtYRU), Е (KFlsroBW0dk), И (W-1rCu0indE), І (Z9TH0H4ShGo).
    Consonants: М (Ez95H4ibuJo), Н (vNUfiKHPYaU), С (7UsFBgSL91E), К (J7sGEI4-xJo), Л (v6-3Xg52Buk), Р (fMGsQ5KPQgg).
    Each item: YouTube video + letter + key word + sound notation."
  items: 11
connects_to:
- a1-002 (Reading Ukrainian)
prerequisites: []
grammar:
- "Звуки vs літери — 33 літери, 38 звуків. 'Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо.'"
- "Голосні (6 sounds, 10 letters) — voice only, no obstruction, singable"
- "Приголосні (32 sounds, 22 letters) — voice + noise or noise only, obstruction"
- "Why 38 > 33: iotated vowels (Я, Ю, Є, Ї), hard/soft pairs, Ь (no sound)"
- "Звуковий аналіз — identifying голосні and приголосні in a word"
- Привіт greeting as first spoken Ukrainian
register: розмовний
references:
- title: Большакова Grade 1 буквар, p.24
  notes: "Голосні/приголосні taught through poems. 'Голосні почуєш в пісні.' 'Приголосні деренчать.'"
- title: Захарійчук Grade 1 буквар (NUS 2025), p.13
  notes: "Sound notation: [•] for vowels, [–] for consonants, [=] for soft consonants."
- title: Заболотний Grade 5, p.83
  notes: "'Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо.' 33 букви, 38 звуків."
- title: Litvinova Grade 5, p.130
  notes: "'Чи можна говорити «голосна літера»? Чому?' — pedagogical question about sounds vs letters."
- title: ULP Season 1, Episode 1 — Informal Greetings
  url: https://www.ukrainianlessons.com/episode1/
  notes: Привіт, Як справи?, response patterns.
pronunciation_videos:
  credit: Anna Ohoiko — Ukrainian Lessons
  overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
  vowels:
    А: https://www.youtube.com/watch?v=hvB3VpcR3ZE
    О: null
    У: https://www.youtube.com/watch?v=VB1O6PmtYRU
    Е: https://www.youtube.com/watch?v=KFlsroBW0dk
    И: https://www.youtube.com/watch?v=W-1rCu0indE
    І: https://www.youtube.com/watch?v=Z9TH0H4ShGo
  consonants:
    М: https://www.youtube.com/watch?v=Ez95H4ibuJo
    Л: https://www.youtube.com/watch?v=v6-3Xg52Buk
    Н: https://www.youtube.com/watch?v=vNUfiKHPYaU
    С: https://www.youtube.com/watch?v=7UsFBgSL91E
    К: https://www.youtube.com/watch?v=J7sGEI4-xJo
    Р: https://www.youtube.com/watch?v=fMGsQ5KPQgg
    Б: https://www.youtube.com/watch?v=V1hxBE_JbGg
    В: https://www.youtube.com/watch?v=aFcvYfvQ2X4
    Д: https://www.youtube.com/watch?v=g4Bh-lqzd48
    П: https://www.youtube.com/watch?v=JksSjjxyW5Y
    Т: https://www.youtube.com/watch?v=m-jcLR_gK0k
    Г: https://www.youtube.com/watch?v=gVnclpSI0DU
    Ґ: https://www.youtube.com/watch?v=gNjHqjTW9WQ
    З: https://www.youtube.com/watch?v=BhASNxitC1A
    Ж: https://www.youtube.com/watch?v=dIrGVcqPwqM
    Ш: https://www.youtube.com/watch?v=1D-6MIw3OXY
    Х: https://www.youtube.com/watch?v=vpr58zJSJKc
    Й: https://www.youtube.com/watch?v=aq0cjB90s3w
    Ч: https://www.youtube.com/watch?v=UsJkbdsY2RA
    Щ: https://www.youtube.com/watch?v=QmBLieIuf6Q
    Ц: https://www.youtube.com/watch?v=u44eCjR2Oz8
    Ф: https://www.youtube.com/watch?v=haHRsFFZRQI
  special:
    Я: https://www.youtube.com/watch?v=yhSAf41LX8I
    Ю: https://www.youtube.com/watch?v=9JdIBYCTWGw
    Є: https://www.youtube.com/watch?v=O0bwRyyBQSc
    Ь: https://www.youtube.com/watch?v=cJlal8XKBxo
    Ї: https://www.youtube.com/watch?v=UcjdjQXhAY8

</plan_content>

## Generated Content

<generated_module_content>
## Звуки і літери (Sounds and Letters)

Look at this page. What you see are letters — shapes printed in ink. Now say a word out loud. Any word. What your mouth just produced is a sound — vibrations shaped by breath, lips, and tongue. In Ukrainian, this distinction is not a footnote. It is the absolute foundation of how the language is taught. Every Ukrainian student learns a golden rule in their first year of school, from the textbook of Заболотний (Grade 5, p. 83): **Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо** — "We hear and pronounce sounds, but we see and write letters." Take the word **мама** (mother). You *hear* and *say* two sounds repeating — [м] then [а], [м] then [а]. You *see* and *write* four letters: М-А-М-А. A **звук** (sound) is breath shaped by your mouth and throat. A **літера** (letter) is ink on paper. These are not the same thing.

Ukrainian has **33 літери** (letters) in its alphabet, but **38 звуків** (sounds). Why the mismatch? Two reasons. First, four letters — **Я**, **Ю**, **Є**, **Ї** — can each represent *two* sounds in certain positions. You will master how this works in M02. Second, the letter **Ь** (called **м'який знак**, the soft sign) represents *no sound at all*. It is a silent instruction — it tells you that the consonant before it should be pronounced softly, and then it disappears from the sound picture entirely. There is a famous pedagogical question from Litvinova (Grade 5, p. 130): "Чи можна говорити «голосна літера»?" — "Can you say 'vowel letter'?" The answer is no. Sounds are **голосні** (vowel) or **приголосні** (consonant). Letters only *represent* sounds. They are not sounds themselves. This distinction matters throughout all of Ukrainian phonetics.

The Ukrainian alphabet is called **абетка** (also **алфавіт**). Its 33 letters run in a fixed order from **А** to **Я**. Unlike English, Ukrainian spelling is largely phonetic — what you see on the page is almost always what you say aloud. There are no "silent e" surprises, no "gh" ambiguities, no letters pretending to be other letters. Once you know the 38 sounds and which letters represent them, you can read any Ukrainian word aloud — even before you understand its meaning. From Вашуленко (Grade 2, p. 26): "Усі тут літери живуть, їх 33 — від А до Я" — "All the letters live here, all 33 — from А to Я."

Here is the full **абетка** — your map for every module ahead. Ten of these letters represent vowel sounds (marked below). Twenty-two represent consonant sounds. One — **Ь** — represents no sound at all.

| | | | | | | | | |
|---|---|---|---|---|---|---|---|---|
| **А а** | **Б б** | **В в** | **Г г** | **Ґ ґ** | **Д д** | **Е е** | **Є є** | **Ж ж** |
| **З з** | **И и** | **І і** | **Ї ї** | **Й й** | **К к** | **Л л** | **М м** | **Н н** |
| **О о** | **П п** | **Р р** | **С с** | **Т т** | **У у** | **Ф ф** | **Х х** | **Ц ц** |
| **Ч ч** | **Ш ш** | **Щ щ** | **Ь** | **Ю ю** | **Я я** | | | |

Vowel letters: А, Е, И, І, О, У + Я, Ю, Є, Ї. Consonant letters: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ. Special: Ь (no sound — softens the consonant before it).

<!-- INJECT_ACTIVITY: letter-grid -->

<!-- INJECT_ACTIVITY: quiz -->

<!-- INJECT_ACTIVITY: match-up -->

## Голосні звуки (Vowel Sounds)

Ukrainian first-graders learn vowels through a poem from Большакова (Grade 1, p. 24): "Голосні почуєш в пісні, і у темному у лісі, і коли дивуєшся, і коли милуєшся. Легко вимовляються, весело співаються!" — "You'll hear vowels in a song, and in a dark forest, when you're surprised, and when you're delighted. Easy to pronounce, fun to sing!" **Голосні** (vowel sounds) are produced when air flows freely through the mouth with nothing blocking the way. Voice alone shapes them — no lips pressing together, no tongue touching the roof of your mouth, no teeth getting in the way. Because nothing obstructs the air, you can sustain a голосний indefinitely: **А-А-А-А** across a field, **О-О-О** into an empty room. You can sing every vowel. That singability is the definition.

There are six vowel *sounds*: [а], [о], [у], [е], [и], [і]. But ten vowel *letters*: А, О, У, Е, И, І — plus Я, Ю, Є, Ї. From Кравцова (Grade 2, p. 9), the chart makes this mapping explicit: the sound [а] can be written as А or Я; [у] as У or Ю; [е] as Е or Є; [і] as І or Ї. Those extra four letters — Я, Ю, Є, Ї — are called "iotated." They can add a [й] sound before the vowel in certain positions. A full explanation waits in M02. For now, the key lesson: count the *sounds*, not the letters. Ukrainian has six голосні звуки, not ten.

Hear vowels in real words. **мАмА** — two [а] sounds. **мОлОкО** (milk) — three [о] sounds (from Большакова, p. 24). **око** (eye) — two [о] sounds. **дім** (house) — one [і] sound. **ніс** (nose) — one [і] sound. Every syllable in Ukrainian contains exactly one голосний звук. Vowels are the heartbeat of syllables. A word with three vowel sounds has three syllables. When you meet a new Ukrainian word, finding the голосні is always your first step.

<!-- INJECT_ACTIVITY: watch-and-repeat -->

## Приголосні звуки (Consonant Sounds)

Where голосні flow freely, **приголосні** (consonant sounds) are blocked. Большакова (Grade 1, p. 24) captures the contrast in another poem: "Приголосні деренчать і тихенько шелестять, голосно свистять, скриплять, і гарчать, і точуть, співати не хочуть." — "Consonants rattle and quietly rustle, whistle loudly, screech, growl, and grind — they don't want to sing!" The obstruction comes from different places: lips pressing together ([м], [б], [п]), tongue touching teeth ([с], [з], [т], [д]), or the back of the throat ([г], [х]). That obstruction creates noise — hissing [с-с-с], buzzing [з-з-з], tapping [р-р-р]. Try holding [к] or [п] for three seconds. You cannot. That unsingability is what defines a приголосний.

Ukrainian has 32 consonant *sounds* from just 22 consonant letters. The reason: many consonants come in pairs — **тверді** (hard) and **м'які** (soft). From Большакова (Grade 2, p. 42): "Приголосні звуки бувають тверді та м'які." A hard [д] and a soft [д'] are two different sounds represented by the same letter **Д**. A hard [н] and a soft [н'] — same letter **Н**, two sounds. Захарійчук (Grade 1, p. 15) marks them in sound models: [–] for hard consonants, [=] for soft consonants. This hard/soft pairing does not exist in English. It is one of the distinctly Slavic features of Ukrainian phonetics, and you will return to it in depth in M03.

Three special consonant facts to note now. First, **Ґ** — a letter unique to Ukrainian, representing a hard [ґ] sound, as in **ґанок** (porch). It looks like Г but sounds different. Second, **Щ** always represents *two* sounds together: [шч]. The word **щука** (pike, the fish) starts with [шч], not a single sound. Third, the **м'який знак** (**Ь**) represents *zero* sounds. It is a softness signal, not a sound. In the word **сіль** (salt), the Ь tells you the final [л] is soft — and then Ь vanishes from the sound picture completely.

<!-- INJECT_ACTIVITY: watch-and-repeat -->

<!-- INJECT_ACTIVITY: group-sort -->

## Привіт! (Hello!)

Time for your first real Ukrainian conversation. **Привіт!** means "Hi!" — informal, used with friends, classmates, and family. After **Привіт**, the most natural follow-up is **Як справи?** (How are you?). Three answers you will hear every day: **Добре** (fine, good), **Чудово** (great, wonderful), **Нормально** (okay, so-so). To return the question: **А у тебе?** (And you?). These five phrases form the building block of every casual encounter in Ukrainian. They are not formulas to memorize in isolation — they are the actual words Ukrainians say to each other every single day.

> <div class="dialogue-line"><span class="speaker">Тарас:</span> Привіт, Олю! *(Hi, Olya!)*</div>
> <div class="dialogue-line"><span class="speaker">Оля:</span> Привіт, Тарасе! Як справи? *(Hi, Taras! How are you?)*</div>
> <div class="dialogue-line"><span class="speaker">Тарас:</span> Добре, дякую. А у тебе? *(Good, thanks. And you?)*</div>
> <div class="dialogue-line"><span class="speaker">Оля:</span> Чудово! Рада тебе бачити. *(Great! Glad to see you.)*</div>
> <div class="dialogue-line"><span class="speaker">Тарас:</span> І я радий тебе бачити! *(And I'm glad to see you!)*</div>

Notice something: Оля says **рада** while Тарас says **радий**. Both mean "glad," but **рада** is the feminine form and **радий** is the masculine form. Ukrainian adjectives agree with the speaker's gender — confirmed in Заболотний (Grade 5, p. 218). This is your very first glimpse of grammatical gender, a major topic from M08 onward. For now, just notice the difference and use the form that matches you.

Now, a **звуковий аналіз** (sound analysis) of **Привіт** — following the method from Большакова (Grade 1, p. 29). Letter by letter: **П** [п] — приголосний; **р** [р] — приголосний; **и** [и] — голосний; **в** [в] — приголосний; **і** [і] — голосний; **т** [т] — приголосний. Count: 2 голосні, 4 приголосні. Six letters, six sounds. This single word contains every type of sound you learned today — vowels and consonants together in one real Ukrainian greeting.

<!-- INJECT_ACTIVITY: fill-in -->

## Підсумок (Summary)

Test yourself with these questions — every answer comes from what you learned above.

**How many letters are in the Ukrainian alphabet?** → **33 літери**.

**How many sounds does Ukrainian have?** → **38 звуків**.

**Why are there more sounds than letters?** → Because Я, Ю, Є, Ї can represent two sounds each, and Ь represents no sound — it only softens the consonant before it.

**What are голосні звуки?** → Sounds made with free-flowing voice — [а], [о], [у], [е], [и], [і]. Air passes through the mouth without obstruction. You can sing them.

**What are приголосні звуки?** → Sounds made with obstruction — lips, tongue, or teeth create noise. You cannot sing them.

**Can you say "голосна літера"?** → **Ні!** Голосні are sounds, not letters. Letters *represent* sounds — they are not sounds themselves.

**What does Привіт mean?** → Hi! (informal greeting).

**What do you say after Як справи?** → **Добре**, **Чудово**, or **Нормально** — then **А у тебе?**

**What is the difference between рада and радий?** → **Рада** is the feminine form (a woman speaking); **радий** is the masculine form (a man speaking). Both mean "glad."

**Deterministic word count: 1756 words** (calculated by pipeline, do NOT estimate manually)

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

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

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

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 73 words | Not found: 9 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Большакова — NOT IN VESUM
  ✗ Вашуленко — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Кравцова — NOT IN VESUM
  ✗ Олю — NOT IN VESUM
  ✗ Оля — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ точуть — NOT IN VESUM

All 73 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
