<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 3: Special Signs (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-003
level: A1
sequence: 3
slug: special-signs
version: '1.3'
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
  - 'Ь has no sound. Its job: soften the consonant before it. Three-way distinction
    (Авраменко Grade 5 p.75, Большакова Grade 2 p.46): м''які приголосні (truly soft,
    9 pairs: Д/Д'', Т/Т'', З/З'', С/С'', Ц/Ц'', Л/Л'', Н/Н'', Р/Р'', ДЗ/ДЗ'' + Й),
    пом''якшені (partially softened: губні, шиплячі, задньоязикові — Ь never after
    these), тверді (hard). Захарійчук Grade 1 p.15 notation: hard = [–], soft = [=].'
  - 'Літвінова Grade 5 mnemonic: «ДЗіДЗьо, Де Ти З''їСи Ці ЛиНи» — exactly
    the 9 consonants Ь can soften. Common patterns: -нь (день, кінь, осінь),
    -ль (сіль, біль), -ть (мить), -зь (мазь). Practice: учитель, батько, маленький.'
- section: Апостроф (The Apostrophe)
  words: 250
  points:
  - 'Захарійчук Grade 1 p.97: Apostrophe comes after б, п, в, м, ф, р before я, ю,
    є, ї. It keeps the consonant HARD and gives the vowel its full [й] + vowel sound.'
  - 'Without apostrophe: consonant softens (пісня — Н is soft). With apostrophe: consonant
    stays hard + vowel = two sounds. сім''я [сім-йа] (family), м''ясо [м-йасо] (meat),
    п''ять [п-йать] (five), комп''ютер [комп-йутер] (computer). Reading practice:
    п''ять, дев''ять, м''який, м''яч, об''єкт. IMPORTANT: Only use apostrophe words
    where apostrophe follows the labial rule (б,п,в,м,ф,р + я,ю,є,ї). Do NOT include
    під''їзд or з''їзд — these follow the prefix rule (під-/з- + їзд) which is A2+.
    Also: тварь is a RUSSIAN form — do NOT use it. Ukrainian has тварина (animal).'
- section: Дзвінкі і глухі (Voiced and Voiceless)
  words: 250
  points:
  - 'Consonants come in voiced-voiceless pairs. Hand on throat test: vibration = voiced.
    Pairs: Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.'
  - 'Ukrainian pronounces voiced consonants clearly at word end — дуб is [дуб], мороз is
    [мороз]. Voiced consonants переважно (mostly) keep their sound. Exception: легко
    [лехко]. This is a defining feature of Ukrainian phonetics.'
  - 'Minimal pairs for ear training: балка (beam) vs палка (stick), коза (goat) vs
    коса (braid).'
- section: Вимова українських звуків (Pronouncing Ukrainian Sounds)
  words: 250
  points:
  - 'И [и] — a unique Ukrainian vowel. It is NOT the same as І [і]. Minimal pairs to hear
    the difference: бик (bull) vs бік (side), дим (smoke) vs дім (house), лист (letter/leaf)
    vs ліс (forest), кит (whale) vs кіт (cat). Practice with Anna Ohoiko''s И video.'
  - 'Г [ɦ] vs Ґ [g] — two different letters, two different sounds. Г is a voiced
    fricative (air flows through narrowed throat): гарно, гора, голова. Its voiceless
    partner is Х — say Х then add voice to get Г. Ґ is a voiced stop (full throat
    closure then release): ґанок, ґудзик. Its voiceless partner is К. Ґ is uniquely
    Ukrainian — an important part of Ukrainian phonetic identity. DO NOT call Г "soft"
    — in Ukrainian phonetics "м''який" means palatalized, which Г is not.'
  - 'Р [р] — the Ukrainian rolled/trilled Р. Practice with Anna Ohoiko''s video: рука, робота,
    ранок, риба. An imperfect Р is always understood — focus on getting comfortable, not perfect.'
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
  - м'який (soft) — apostrophe only (NO soft sign! Й is inherently soft)
activity_hints:
- type: odd-one-out
  section: "М'який знак"
  focus: 'Which consonant does NOT have a soft pair? (Ь can''t soften it)'
  items: 6
- type: fill-in
  section: "Апостроф"
  focus: 'Add the missing Ь or apostrophe: сім_я, ден_, п_ять'
  items: 6
- type: error-correction
  section: "Апостроф"
  focus: 'Find missing apostrophes in words like м''ясо, сім''я, п''ять'
  items: 6
- type: group-sort
  section: "Апостроф"
  focus: 'Sort words into: has Ь / has apostrophe / neither'
  items: 18
- type: match-up
  section: "Дзвінкі і глухі"
  focus: 'Match voiced-voiceless pairs: Б↔П, Д↔Т, Г↔Х, Ґ↔К, etc.'
  items: 8
- type: true-false
  section: "Дзвінкі і глухі"
  focus: 'Statements about voiced/voiceless rules and non-devoicing'
  items: 6
- type: quiz
  section: "Вимова українських звуків"
  focus: 'Г vs Ґ: choose the correct letter for each word'
  items: 6
connects_to:
- a1-004 (Stress and Melody)
prerequisites:
- a1-002 (Reading Ukrainian)
grammar:
- 'Soft sign (Ь) — softens preceding consonant, no sound. Only after 9 consonants:
  Д, Т, З, С, Ц, Л, Н, Р, ДЗ (mnemonic: ДЗіДЗьо, Де Ти З''їСи Ці ЛиНи)'
- 'Three-way distinction: м''які (truly soft, 9+Й), пом''якшені (partially softened
  губні/шиплячі/задньоязикові), тверді (hard)'
- 'Apostrophe — after б,п,в,м,ф,р before я,ю,є,ї (Захарійчук rule). NO prefix
  apostrophe examples (під''їзд, з''їзд) at A1.'
- 'Voiced/voiceless pairs (8): Б-П, Д-Т, Г-Х, Ґ-К, З-С, Ж-Ш, ДЗ-Ц, ДЖ-Ч.
  Сонорні (В,Л,М,Н,Й,Р) are NEITHER voiced nor voiceless.'
- 'Non-devoicing: voiced consonants переважно keep sound at word end. Exception: легко [лехко].'
- 'Г [ɦ] voiced fricative (NOT "soft") vs Ґ [g] voiced stop'
register: розмовний
references:
- title: Захарійчук Grade 1 (NUS 2025), p.97
  notes: 'Apostrophe rule: after б,п,в,м,ф,р before я,ю,є,ї.'
- title: Захарійчук Grade 1 (NUS 2025), p.15
  notes: Hard [–] vs soft [=] consonant notation.
- title: Большакова Grade 1, p.45-47
  notes: Тверді і пом'якшені приголосні звуки.

</plan_content>

## Generated Content

<generated_module_content>
## М'який знак (The Soft Sign — Ь)

> **Оленка:** Хто це там? *(Who is that there?)*
> **Тарас:** Це батько. *(This is a father.)*
> **Оленка:** А там учитель? *(And is a teacher there?)*
> **Тарас:** Так, там учитель. *(Yes, a teacher is there.)*

The soft sign — written as **Ь** — is unique because it is entirely silent. It has no sound of its own, but it acts as a very specific instruction for your tongue. Its only job is to change the quality of the consonant that comes immediately before it, making it soft, or palatalized. When you see this sign, you press the middle of your tongue up toward the roof of your mouth while pronouncing the consonant. For example, look at the word **день** (day). The letter **Н** usually sounds like a firm English "n". But the soft sign at the end tells you to soften it into a delicate, almost airy sound. You can hear this same softening effect in the word **сіль** (salt), where the hard **Л** becomes light and lifted. The soft sign is a crucial part of Ukrainian phonetics. Without it, you cannot pronounce words correctly.

In Ukrainian phonetics, there is a three-way distinction: consonants can be truly soft (**м'які**), partially softened (**пом'якшені**), or hard (**тверді**). The soft sign creates truly soft sounds. However, there is a specific, closed group of consonants that can take the soft sign. Ukrainian students memorize these letters using a famous phrase: **«ДЗіДЗьо, Де Ти З’їСи Ці ЛиНи»** (Dzidzio, where will you eat these tench fish?). This phrase contains eight of the nine consonants that can be truly softened: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, and **ДЗ** (just remember to add **Р** to complete the set of nine). You will never see a soft sign after labial, sibilant, or velar consonants, which can only be partially softened. To help young learners visualize this, textbooks like *Захарійчук Grade 1* use a special notation. A hard consonant is marked with a single dash **[–]**, and a soft consonant is marked with a double dash **[=]**.

:::tip
The mnemonic **«ДЗіДЗьо, Де Ти З’їСи Ці ЛиНи»** is taught to every Ukrainian first grader. Memorizing this funny phrase about eating tench fish is the fastest way to know exactly which consonants can take a soft sign.
:::

The soft sign is not restricted to the end of a word; it frequently appears right in the middle. Common structural patterns include **-нь** as in **день** (day) or **осінь** (autumn), **-ль** as in **сіль** (salt) or **біль** (pain), **-ть** as in **мить** (moment), and **-зь** as in **мазь** (ointment). When it sits inside a word, it softens the preceding consonant before the next sound begins. A classic example is the word **батько** (father). The soft sign sits right after the **Т**, making it soft before you pronounce the hard **К**. You will also see this pattern in professional titles, such as **учитель** (teacher), and very commonly in adjectives, like **маленький** (small). It is also important to know that the Ukrainian letter **Й** is inherently soft by its very nature and never needs a soft sign next to it. 

To truly understand the power of the soft sign, we must look at how it changes the actual meaning of words. In Ukrainian, a hard consonant and a soft consonant are treated as two entirely different sounds. Consider the minimal pair of **стан** (waist/state) and the imperative verb form **стань** (stand/become). In **стан**, your tongue presses firmly against your teeth for a hard [н]. But in **стань**, the soft sign instructs you to lift the middle of your tongue, creating a soft [н']. That single physical shift in your mouth completely changes what you are saying. Palatalization is a structural pillar of the language.

<!-- INJECT_ACTIVITY: odd-one-out-softening -->

## Апостроф (The Apostrophe)

> **Тато:** Це наша сім'я. *(This is our family.)*
> **Син:** М'ясо тут? *(Is the meat here?)*
> **Тато:** Так, м'ясо тут. *(Yes, the meat is here.)*

If the soft sign is a gentle instruction to soften a sound, the apostrophe — written as **’** — acts as a solid brick wall. The apostrophe performs the exact opposite function of the soft sign. It is a strict separator. When you see an apostrophe in a Ukrainian word, it commands you to keep the preceding consonant absolutely hard. Simultaneously, it forces the vowel that follows it to break apart and be pronounced as two completely distinct sounds: a clear **[й]** sound followed by the vowel. It creates a physical pause, a sharp phonetic boundary that you must respect.

But where does this wall appear? According to the standard orthography (*Захарійчук Grade 1*, p.97), the apostrophe is placed after the labial consonants **Б**, **П**, **В**, **М**, **Ф**, and the letter **Р**. It appears only when these consonants are followed by the iotated vowels **Я**, **Ю**, **Є**, or **Ї**. Without an apostrophe, a consonant softens naturally before these vowels, as in **пісня** (song), where the **Н** is soft. With the apostrophe, the consonant stays hard, and the vowel equals two sounds. A perfect example is the word **сім'я** (family). Because of the apostrophe, the **М** remains completely hard, and the **Я** splits into its full **[йа]** sound. You pronounce it as **[сім-йа]**, distinctly separating the syllables.

This strict separation is crucial for many high-frequency words that you will use every day. Consider the word **м'ясо** (meat). English speakers often make the mistake of softening the **М**, blending it into a mushy sound. But the apostrophe forbids this. You must say **[м-йасо]**, keeping the labial consonant firm. The same applies to the adjective **м'який** (soft) — notice that it contains an apostrophe, but absolutely no soft sign, because the **Й** is inherently soft. The strict separation also applies to numbers. When you say **п'ять** (five), you must clearly articulate **[п-йать]**. When you say **дев'ять** (nine), the **В** stays hard before the **Я**. Practicing this firm separation will immediately make your Ukrainian sound authentic.

This spelling rule is so deeply embedded in Ukrainian phonetics that it also applies to modern loanwords and international vocabulary. Whenever a foreign word contains a labial consonant followed by a "yu" or "ya" sound, Ukrainian spelling enforces the apostrophe to maintain the hard consonant. You will see this clearly in words like **комп'ютер** (computer) and **об'єкт** (object). The apostrophe is an active, consistent rule that shapes how the language absorbs new concepts.

<!-- INJECT_ACTIVITY: fill-in-special-signs -->
<!-- INJECT_ACTIVITY: error-correction-apostrophe -->
<!-- INJECT_ACTIVITY: group-sort-signs -->

## Дзвінкі і глухі (Voiced and Voiceless)

> **Анна:** Це великий дуб? *(Is this a big oak tree?)*
> **Марко:** Так, це старий дуб. *(Yes, this is an old oak tree.)*
> **Анна:** А там коза? *(And is a goat there?)*
> **Марко:** Ні, там коса. *(No, a braid is there.)*

Ukrainian consonants have their own distinct personalities, and they often come in pairs. These pairs are categorized by how they are produced in your throat: they are either voiced (**дзвінкі**) or voiceless (**глухі**). There is a very simple physical test to understand this difference. Cover your ears with your hands (закрий долонями вуха). Now, make a strong **[б]** sound. You will hear a distinct vibration — your vocal cords are engaged, making it a voiced consonant. Now, make a **[п]** sound. The vibration stops completely. You are using the exact same lip position, but only pushing air. That makes it a voiceless consonant.

:::note
The "hands on ears" test is a perfect physical tool for learning pronunciation. If you hear a buzz, the sound is voiced. If you only hear air leaving your mouth, the sound is voiceless.
:::

This vibration test defines the eight main voiced-voiceless pairs in the Ukrainian language. They are: **Б-П**, **Д-Т**, **Г-Х**, **Ґ-К**, **З-С**, **Ж-Ш**, **ДЗ-Ц**, and **ДЖ-Ч**. Learning these partners is essential for mastering spelling and pronunciation. However, not every consonant has a partner. There is a special group of sounds called sonorants (**сонорні**), which include **В**, **Л**, **М**, **Н**, **Й**, and **Р**. These are highly resonant, musical sounds. They flow smoothly and do not have voiceless equivalents in Ukrainian.

One of the most defining and beautiful features of Ukrainian phonetics is its "Resilience Rule." In many languages, voiced consonants lose their voice and become weak when they sit at the very end of a word. Ukrainian strictly forbids this. Voiced consonants **переважно** (mostly) keep their sound, no matter where they appear. When you say **дуб** (oak tree), you must clearly pronounce the strong **[дуб]** at the end. When you say **мороз** (frost), the final **[з]** must vibrate clearly. There is only one common exception to this rule of resilience: the word **легко** (easily), which is pronounced as **[лехко]**.

This resilience is not just an aesthetic preference; it is absolutely necessary for meaning. Because Ukrainian preserves final voicing, minimal pairs sound distinctly different. Listen carefully to the difference between **балка** (beam) and **палка** (stick). The only difference is the vibration in your throat. Similarly, the vibration is the only thing separating **коза** (goat) from **коса** (braid). Ear training with these pairs is vital.

<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->
<!-- INJECT_ACTIVITY: true-false-devoicing -->

## Вимова українських звуків (Pronouncing Ukrainian Sounds)

> **Максим:** Що це там? *(What is this there?)*
> **Юля:** Це великий бик. *(This is a big bull.)*
> **Максим:** А там дім? *(And is a house there?)*
> **Юля:** Ні, це дим. *(No, this is smoke.)*

Some Ukrainian sounds require special attention because they do not have exact matches in English. The vowel **И** is one of the most unique sounds in the language. It is a completely distinct vowel, and you must never confuse it with the sharper, higher **І**. If you swap them, you will say an entirely different word. To train your ear, practice these minimal pairs out loud. Notice the difference between **бик** (bull) and **бік** (side). Feel the shift in your mouth between **дим** (smoke) and **дім** (house), or between **лист** (leaf) and **ліс** (forest). Hear the stark contrast between **кит** (whale) and **кіт** (cat). Watch the Anna Ohoiko pronunciation video to see the exact mouth position for **И**.

Another crucial distinction is the difference between **Г** and **Ґ**. They look similar, but they are two different letters that produce two completely different sounds. The letter **Г** is a voiced fricative. You produce it by letting air flow smoothly through a narrowed throat, creating a deep, breathy sound. You can hear this in words like **гарно** (nicely), **гора** (mountain), and **голова** (head). Never call **Г** "soft" — in Ukrainian phonetics, it is an independent, firm sound. On the other hand, **Ґ** is a voiced stop. You close your throat completely and release it sharply, much like the English "g" in "goat". Practice this sharp stop with words like **ґанок** (porch) and **ґудзик** (button).

Finally, we meet the Ukrainian **Р**, a vibrant, rolled, or trilled consonant. To produce it, your tongue must lightly tap against the alveolar ridge right behind your upper teeth. Practice with Anna Ohoiko's video, focusing on words that build a strong rhythm: **риба** (fish), **ранок** (morning), **робота** (work), and **рука** (hand). Do not worry if your trill is imperfect at first; native speakers will always understand you.

<!-- INJECT_ACTIVITY: quiz-g-vs-ge -->

## Підсумок — Summary

We have covered the foundational rules that give the Ukrainian language its distinct phonetic character. Now it is time to review and test your understanding of these core principles.

First, what does the soft sign (**Ь**) do? It is completely silent, but it acts as an instruction to soften or palatalize the consonant that comes immediately before it.

Second, which consonants can be followed by the soft sign? Remember the mnemonic rule: **«ДЗіДЗьо, Де Ти З’їСи Ці ЛиНи»**. This phrase contains eight of the nine eligible consonants: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, and **ДЗ** (just remember to add **Р**).

Third, when do we use an apostrophe? It acts as a separator and is placed after the labial consonants **Б**, **П**, **В**, **М**, **Ф**, and the letter **Р**, specifically before the iotated vowels **Я**, **Ю**, **Є**, and **Ї**.

Fourth, does a voiced consonant like "б" change its sound at the end of a word? No, it does not. The Ukrainian rule of resilience dictates that voiced consonants mostly stay proudly voiced at the end of words.

Fifth, what is the difference between **Г** and **Ґ**? The letter **Г** is a deep, breathy voiced fricative, while the letter **Ґ** is a sharp, hard voiced stop.

Finally, test yourself by reading these challenge words aloud: **сім'я** (family), **день** (day), **п'ять** (five), **гарно** (nicely), **риба** (fish), and **м'ясо** (meat).
</generated_module_content>

**PIPELINE NOTE — Word count: 2024 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 75 words | Not found: 7 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Юля — NOT IN VESUM
  ✗ йасо — NOT IN VESUM
  ✗ йать — NOT IN VESUM
  ✗ лехко — NOT IN VESUM

All 75 other words are confirmed to exist in VESUM.

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
