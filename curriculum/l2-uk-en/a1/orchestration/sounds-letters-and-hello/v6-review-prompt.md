<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 1: Sounds, Letters, and Hello (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-001
level: A1
sequence: 1
slug: sounds-letters-and-hello
version: '1.5'
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
dialogue_situations:
- setting: First day of Ukrainian class — teacher greets students, students respond
    and practice basic Привіт/Добрий день exchange
  speakers:
  - Вчитель
  - Учні
  motivation: 'Practice greeting chunks: Привіт! Добрий день! Як справи? Добре.'
- setting: Two new classmates meet in the hallway before their first Ukrainian lesson
    and introduce themselves
  speakers:
  - Марко
  - Софія
  motivation: 'Привіт! Як тебе звати? Мене звати... — first social use of sounds learned'
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

When you listen to someone speaking Ukrainian, what you are actually hearing is a series of sounds. When you read a Ukrainian book or a text message, what you are looking at is a series of letters. This might seem like an obvious statement, but confusing these two concepts is a frequent mistake. There is a golden rule taught to every Ukrainian student in the fifth grade. As the textbook by Заболотний (Grade 5, page 83) states: "Звуки ми чуємо й вимовляємо, а букви бачимо й пишемо." This means we hear and pronounce a **звук** (sound), but we see and write a **літера** (letter). A letter is nothing more than a symbol on a piece of paper or a screen. A sound is the physical vibration your mouth and vocal cords produce. They are not the same thing. This distinction is the absolute foundation of Ukrainian phonetics. Ukrainian teachers drill this concept from the very first day of first grade because everything else in the language builds upon it. You cannot truly understand how Ukrainian works until you stop looking at words as just collections of letters and start hearing them as sequences of sounds.

You might assume that every letter matches exactly one sound, but the numbers tell a different story. The Ukrainian language has exactly 33 letters, but it has 38 distinct sounds. Why is there a mismatch? The answer lies in how certain letters behave. Some letters have the special ability to represent two different sounds at the same time. Specifically, the letters Я, Ю, Є, and Ї can represent a combination of two sounds depending on where they appear in a word. On the other hand, one specific letter makes no sound at all. The soft sign, written as Ь, is completely silent. Its only job is to soften the consonant that comes right before it. Because of these rules, you must be careful with your terminology. The textbook by Litvinova (Grade 5, page 130) asks students a very specific pedagogical question: "Чи можна говорити «голосна літера»?" (Can we say "vowel letter"?). The answer is an absolute no. Sounds are either vowels or consonants, not letters. Letters only represent sounds. Calling a symbol on a page a "vowel" is factually incorrect in Ukrainian linguistics.

To start reading, you need to meet the Ukrainian alphabet, known as the **абетка** or алфавіт. It contains all 33 letters in a specific order: А, Б, В, Г, Ґ, Д, Е, Є, Ж, З, И, І, Ї, Й, К, Л, М, Н, О, П, Р, С, Т, У, Ф, Х, Ц, Ч, Ш, Щ, Ь, Ю, Я. Each letter has its own specific name. For English speakers, a major advantage is that Ukrainian spelling is highly phonetic. This means that what you see is usually very close to what you hear. Unlike English, where the letter "a" sounds completely different in "cat," "father," and "late," Ukrainian letters are relatively consistent. There are no silent letters hiding in words to trick you (except for the functional role of the soft sign Ь). Pronunciation patterns are much more predictable than in English, so once you learn the specific sounds that these 33 symbols represent, you will usually be able to make a strong first reading attempt aloud.
 For example, knowing the sounds allows you to read the word **тато** (father) perfectly on the first try.

<!-- INJECT_ACTIVITY: letter-grid -->

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

## Голосні звуки (Vowel Sounds)

With the difference between a letter and a sound established, the focus shifts to the two main families of sounds. The first family is the **голосний** (vowel sound). A vowel sound is created using only your voice. When you pronounce a vowel, the air flows completely freely from your lungs, through your throat, and out of your mouth with absolutely no obstruction from your lips, teeth, or tongue. Because nothing blocks the air, vowels are the musical core of the language. As the textbook by Большакова (Grade 1, page 24) teaches children through a poem: "Голосні почуєш в пісні, і у темному у лісі... Легко вимовляються, весело співаються!" (You will hear vowels in a song, and in a dark forest... They are easily pronounced, cheerfully sung!). You can sing a vowel sound. You can hold it for as long as you have breath. You can shout a vowel across a wide field to get someone's attention. Without vowels, human speech would just be a series of clicks, hisses, and pops. 

There are exactly 6 vowel sounds in the Ukrainian language: [а], [о], [у], [е], [и], and [і]. However, as discussed earlier, the alphabet has 10 letters that are used to represent these 6 sounds: А, О, У, Е, И, І, Я, Ю, Є, and Ї. The extra four letters (Я, Ю, Є, Ї) are called "iotated" letters. They perform "two jobs," often representing a hidden "y" sound combined with a basic vowel sound. Their exact mechanics appear in depth in the next module. The most important rule to remember is that every single Ukrainian word must have at least one vowel sound. Vowels are the absolute heart of every syllable. A syllable cannot exist without a vowel to give it shape and volume. 

In Ukrainian schools, children learn to map out the sounds in words using special symbols. The textbook by Захарійчук (Grade 1, page 13) introduces a simple sound notation system. In these sound models, every vowel sound is marked with a heavy dot [•]. You can practice hearing these vowel sounds right now. Listen carefully to the word **мама** (mother). You can clearly hear two distinct [а] sounds: мА-мА. Next, listen to the word **молоко** (milk). It contains three identical [о] sounds strung together: мО-лО-кО. Finally, listen to the name **Уля**. It gives you a clear [у] example: У-ля.
 Below, you will find pronunciation videos from Anna Ohoiko for each of the primary letters that represent vowel sounds. Watch each video carefully, listen to the native pronunciation, and repeat the sounds out loud.

## Приголосні звуки (Consonant Sounds)

The second family of sounds in the Ukrainian language is the **приголосний** (consonant sound). The word itself translates to "with a vowel," showing that these sounds are designed to attach themselves to vowels to build syllables. While vowels are made of pure voice, a consonant sound is made with voice plus noise, or sometimes with just noise alone. This noise happens because your mouth creates an obstruction. Your lips might close together, your tongue might tap the roof of your mouth, or your teeth might block the airflow. The textbook by Большакова (Grade 1, page 24) explains this beautifully: "Приголосні деренчать і тихенько шелестять, голосно свистять і шиплять" (Consonants rattle and quietly rustle, loudly whistle and hiss). To prove this, try singing a pure consonant. Take the sound [к] or the sound [п] and try to hold a musical note with it. It is physically impossible. Consonants provide the structure and the hard edges of a word, while vowels provide the volume and the melody. 

The math for consonants is slightly more complex than for vowels. The Ukrainian language has 32 distinct consonant sounds, but these are derived from only 22 consonant letters in the alphabet. This is mostly because many Ukrainian consonants come in distinct pairs: тверді (hard) and м'які (soft). For example, a hard "t" and a soft "t" are considered completely separate sounds, even though they might be written using the same base letter. The notation system from Захарійчук (Grade 1, page 15) shows this clearly: hard consonant sounds are marked with a single dash [–], while soft consonant sounds are marked with a double dash [=]. This hard and soft distinction is central to Ukrainian phonetics and unfamiliar to most English speakers, which means you will need to train your ear to hear the difference.
 You can hear a hard consonant in **сон** (dream), which starts with a hard [с-] sound. Conversely, you can hear a soft consonant in **дім** (house), which starts with a soft [д=] sound, or **ніс** (nose), which starts with a soft [н=] sound.

You will meet the consonant letters through the pronunciation videos below: М, Н, С, К, Л, Р, Б, В, Д, П, Т, Г, Ґ, З, Ж, Ш, Х, Й, Ч, Щ, Ц, and Ф. Watch how the speaker shapes her mouth for each one. There are three special letters to pay close attention to. The letter Ґ with its little upturned tail is uniquely Ukrainian and represents a hard "g" sound. The letter Щ is highly efficient because it always represents two distinct sounds packed together: [шч]. Finally, the soft sign, Ь (м'який знак), makes absolutely no sound of its own, but it serves the crucial purpose of softening the consonant that comes immediately before it.

<!-- INJECT_ACTIVITY: group-sort-vowels-consonants -->

<!-- INJECT_ACTIVITY: match-up-letters-to-sounds -->

<!-- INJECT_ACTIVITY: watch-and-repeat-alphabet -->

## Привіт! (Hello!)

Understanding the mechanics of sounds and letters prepares you for your very first Ukrainian conversation. The fundamental phrases that people use every single day provide the best starting point. Imagine the setting of the first day in a Ukrainian language class. The teacher walks into the room and immediately begins speaking to the students to establish a welcoming atmosphere. 

> **Вчитель:** Добрий день! *(Good afternoon!)*
> **Учні:** Добрий день! *(Good afternoon!)*
> **Вчитель:** **Привіт**! **Як справи**? *(Hi! How are you?)*
> **Учні:** **Добре**, дякую! *(Fine, thank you!)*

In this short exchange, you see the formal greeting "Добрий день" used respectfully with a teacher, followed by the informal greeting **привіт** (hi). When someone asks **як справи** (how are you), you can answer **добре** (fine, good), **чудово** (great), or **нормально** (okay), and ask the question back with **А у тебе?** (And you?).

Consider another situation. Two new classmates meet in the hallway just before their first Ukrainian lesson begins. They want to introduce themselves and be friendly.

> **Марко:** **Привіт**! Як тебе звати? *(Hi! What is your name?)*
> **Софія:** **Привіт**! Мене звати Софія. А тебе? *(Hi! My name is Sofia. And you?)*
> **Марко:** Мене звати Марко. *(My name is Marko.)*

This is the very first social application of the sounds you have just learned. By putting these specific sounds together, Marko and Sofia successfully introduce themselves.

As the conversation continues, Sofia expresses her happiness at meeting her new classmate.

> **Софія:** Рада тебе бачити! *(Glad to see you!)*
> **Марко:** Радий тебе бачити! *(Glad to see you!)*

Notice carefully how they say the exact same English phrase, but the Ukrainian words are slightly different. Sofia, a female speaker, says "рада." Marko, a male speaker, says "радий." The Ukrainian language has gendered forms for many words. This is your first encounter with grammatical gender, which will become a major structural topic starting in module M08. For now, observe that speakers adapt their words based on who they are.

Applying these rules directly, a "звуковий аналіз" (sound analysis) on the word **привіт** breaks down the letters to reveal the exact sounds inside:

* П represents the sound [п] (приголосний)
* р represents the sound [р] (приголосний)
* и represents the sound [и] (**голосний**)
* в represents the sound [в] (приголосний)
* і represents the sound [і] (**голосний**)
* т represents the sound [т] (приголосний)

Counted out, the word contains exactly two **голосні** (vowels) and four приголосні (consonants). Because it has two vowel sounds, the word has two syllables. Every type of sound you learned about in this module appears right here in this one simple greeting.

<!-- INJECT_ACTIVITY: fill-in-greeting -->

## Підсумок (Summary)

This module established the foundation of Ukrainian phonetics. Review the core concepts with a few self-check questions to verify this foundation. 

First, how many letters are in the Ukrainian alphabet? There are exactly 33 літери. 
Second, how many sounds are there in the Ukrainian language? There are 38 звуків. 
Why are the numbers different? The numbers differ because iotated letters (Я, Ю, Є, Ї) can make two distinct sounds, while the soft sign (Ь) makes absolutely no sound at all. 
What are голосні? These are vowel sounds made only with your voice, meaning they can be easily sung without any airflow obstruction. 
What are приголосні? These are consonant sounds made with a physical obstruction in the mouth, which means they cannot be sung. 
Can you say "голосна літера"? Absolutely not. Sounds are голосні, not letters; letters merely represent sounds on paper. 
Finally, what does **привіт** mean? It is the informal greeting for "hi." And how do you answer **як справи**? You can say **добре**, **чудово** (great, wonderful), or **нормально** (okay).
</generated_module_content>

**PIPELINE NOTE — Word count: 2096 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
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

Verified: 71 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Большакова — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Софія — NOT IN VESUM
  ✗ Уля — NOT IN VESUM

All 71 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
