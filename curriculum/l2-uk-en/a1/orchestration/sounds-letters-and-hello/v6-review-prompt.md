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

Look at the text on this page. What you are seeing right now are letters. Now, say a word out loud. What you just produced is a sound. This distinction is a fundamental concept in Ukrainian phonetics. There is a golden rule taught to every Ukrainian student in the fifth grade, as stated by the linguist Zabolotnyi: **«Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо.»** We hear and pronounce sounds (**звуки**), but we see and write letters (**літери** or **букви**). A letter is just a costume for a sound, a visual symbol on paper. In Ukrainian schools, this boundary between the spoken sound and the written letter is emphasized from the very first day. Understanding that your mouth makes sounds and your pen writes letters helps you navigate pronunciation.

In Ukrainian, we have 33 letters (**літери**), but we produce 38 sounds (**звуки**). Why are there more sounds than letters? The answer lies in how some letters behave. Certain letters, specifically **Я**, **Ю**, **Є**, and **Ї**, can carry two sounds at once [йа, йу, йе, йі] depending on where they are placed in a word. Furthermore, there is one very special letter, the **Ь** (**м’який знак** or soft sign), which is a silent ghost. It makes absolutely no sound of its own. It only exists to change the texture of the consonant that comes right before it. A Ukrainian textbook by Litvinova poses a clever challenge to fifth graders: "Can you say 'vowel letter'?" The answer is strictly no! A vowel describes the physical sound you make, not the written symbol. Sounds are vowels or consonants; letters simply represent them on the page.

The Ukrainian alphabet (**абетка** or **алфавіт**) has 33 letters in total, arranged in a specific, standardized order. Each letter has its own official name, like «А», «Бе», «Ве», but what matters most are the actual sounds they make: [а], [б], [в]. Unlike English, where spelling can be chaotic and unpredictable, Ukrainian spelling is highly phonetic and remarkably consistent. What you see is almost exactly what you hear. There are no silent letters hidden inside words, and no surprise pronunciations that you have to guess. Once you learn the sound of a letter, it rarely surprises you. If you know the sounds, you can read any word you see, whether it is a short word like **сон** (dream) or **дім** (home).

<!-- INJECT_ACTIVITY: quiz -->

Just like a large family, all these different sounds have two main branches. Every sound you make in Ukrainian belongs to one of two categories: **голосні** (vowels) and **приголосні** (conants). Understanding how these two families work is your next essential step.

## Голосні звуки (Vowel Sounds)

What exactly is a vowel? We call them **голосні** (vowels), coming from the word **голос** (voice). A first-grade textbook by Bolshakova teaches this concept beautifully through a poem: **«Голосні почуєш в пісні... Легко вимовляються, весело співаються!»** You will hear vowels in a song... they are easily pronounced and cheerfully sung! The mechanics are quite simple: when you say a vowel, the air flows freely from your lungs through your mouth with absolutely no obstruction from your lips, teeth, or tongue. You use only your voice to shape the air. If you can sing it loudly across a wide field, it is definitely a vowel.

There are exactly 6 vowel sounds in Ukrainian: [а], [о], [у], [е], [и], [і]. However, as we discussed earlier, there are 10 vowel letters used to write them down: **А**, **О**, **У**, **Е**, **И**, **І**, **Я**, **Ю**, **Є**, **Ї**. The extra four letters (**Я**, **Ю**, **Є**, **Ї**) are known as "iotated" letters — they are specialized ways to write the basic vowel sounds paired with an extra "y" sound. For now, you only need to focus on the core 6 sounds. Every single Ukrainian word must have at least one vowel sound in it.

To visualize these sounds, Ukrainian first-graders use a special notation created by Zakhariichuk. Vowel sounds are marked with a solid circle [•] in sound models. Let's practice identifying the heart of the word. In the word **мама** (mother), there are two [а] sounds: [•][•]. In the word **молоко** (milk), there are three [о] sounds: [•][•][•]. In the name **Уля** (Ulya), there is one [у]. You can also see this in the word **тато** (dad), which has two vowels [а] and [о], or the word **око** (eye), which has two [о] sounds. A syllable cannot possibly exist without a vowel. The vowel functions as the phonetic core of the word, providing structure and voice.

You will practice with Anna Ohoiko's pronunciation videos for all the letters after we cover the consonants in the next section.

## Приголосні звуки (Consonant Sounds)

If vowels are pure voice, consonants are sounds of obstruction. We call them **приголосні** (consonants). Bolshakova’s poem explains: **«Приголосні деренчать і тихенько шелестять...»** Consonants rattle and quietly rustle. They are formed when your mouth creates a physical barrier to the airflow. Your lips press tightly together for [п], or your tongue taps your teeth for [т]. They are made with a combination of voice and noise, or sometimes just noise alone. You cannot sing a pure consonant without a vowel’s help — try singing [к] or [п] and you will quickly run out of breath!

In Ukrainian, we have 32 consonant sounds produced by 22 consonant letters. One of the most important concepts to grasp early on is the divide between hard (**тверді**) and soft (**м'які**) consonants. Many Ukrainian consonants have a "twin" brother — one is pronounced hard, marked with a dash [–], and the other is pronounced soft, marked with an equals sign [=]. The **Ь** (**м’який знак** or soft sign) is the crucial softening agent that turns a hard consonant into its soft twin. For example, the letter **С** can be hard [с] or soft [с’], and the **Н** in **ніс** (nose) is soft [н’]. Understanding this hard and soft distinction is important for developing a natural Ukrainian accent.

There are a few special characters in the consonant family you should know immediately. The letter **Ґ** represents a hard, solid 'g' sound, which is uniquely Ukrainian and quite rare. This is contrasted with the much more common **Г**, which is a breathy 'h' sound. Another very special letter is **Щ**, which always represents two distinct sounds at once: [шч], sounding exactly like "fresh cheese" when said quickly together.

You will meet many of these consonant letters through Anna Ohoiko's videos: М, Н, С, К, Л, Р, and more. Each video shows the letter, demonstrates the sound, and gives example words.

<!-- INJECT_ACTIVITY: watch-and-repeat -->

<!-- INJECT_ACTIVITY: match-up -->

<!-- INJECT_ACTIVITY: letter-grid -->

## Привіт! (Hello!)

Here is your very first Ukrainian conversation.

> <div class="dialogue-line"><span class="speaker">Оленка:</span> Привіт! *(Hi!)*</div>
> <div class="dialogue-line"><span class="speaker">Тарас:</span> Привіт! Як справи? *(Hi! How are you?)*</div>
> <div class="dialogue-line"><span class="speaker">Оленка:</span> Добре, дякую. А у тебе? *(Fine, thanks. And you?)*</div>
> <div class="dialogue-line"><span class="speaker">Тарас:</span> Чудово! *(Great!)*</div>
> <div class="dialogue-line"><span class="speaker">Оленка:</span> Рада тебе бачити! *(Glad to see you!)*</div>
> <div class="dialogue-line"><span class="speaker">Тарас:</span> Радий тебе бачити! *(Glad to see you!)*</div>

Notice how Olenka, a woman, says **Рада тебе бачити!** (Glad to see you!), while Taras, a man, says **Радий тебе бачити!** (Glad to see you!). This is your first encounter with grammatical gender in practice. In Ukrainian, the gender of the speaker often changes the specific endings of certain words. Also, note that **привіт** (hi) is a very casual, informal greeting. You should only use it with close friends, family members, and people your own age. Never use it in formal or professional situations. You can answer **Як справи?** (How are you?) with **Добре** (fine) or **Нормально** (okay).

We can analyze the word **привіт** sound-by-sound (**звуковий аналіз**).
First is **П** [п], which is a **приголосний** (consonant).
Next is **Р** [р], another **приголосний**.
Then comes **И** [и], a **голосний** (vowel).
After that is **В** [в], a **приголосний**.
Then we have **І** [і], another **голосний**.
Finally, we end with **Т** [т], a **приголосний**.

<!-- INJECT_ACTIVITY: fill-in -->

## Підсумок (Summary)

Here is a quick self-check Q&A recap:

- Question: **Що ми чуємо і вимовляємо?** (What do we hear and pronounce?)
  Answer: **Звуки.** (Sounds.)
- Question: **Що ми бачимо і пишемо?** (What do we see and write?)
  Answer: **Літери.** (Letters.)
- Question: **Скільки літер в абетці?** (How many letters in the alphabet?)
  Answer: 33.
- Question: **Скільки звуків?** (How many sounds?)
  Answer: 38.
- Question: **Які бувають звуки?** (What kind of sounds are there?)
  Answer: **Голосні** (6 vowels) and **приголосні** (32 consonants).
- Question: **Чи можна сказати «голосна літера»?** (Can you say "vowel letter"?)
  Answer: No, you can only say "a letter representing a vowel sound." The sound itself is the vowel!
- Question: **Як сказати "Hi"?** (How do you say "Hi"?)
  Answer: **Привіт!**

<!-- INJECT_ACTIVITY: group-sort -->

**Deterministic word count: 1466 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 63 words | Not found: 2 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Тарас — NOT IN VESUM
  ✗ Уля — NOT IN VESUM

All 63 other words are confirmed to exist in VESUM.

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
