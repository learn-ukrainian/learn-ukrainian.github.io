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

The **м'який знак** (soft sign) looks like a lowercase "b", but it produces absolutely no sound. Instead, it acts solely as a modifier to soften, or palatalize, the consonant that comes right before it. In Ukrainian phonetics, there is a clear three-way distinction for consonants. We have **м'які** (truly soft) consonants, **пом'якшені** (partially softened) consonants which include lip, hissing, and back-tongue sounds, and finally **тверді** (hard) consonants. Some Ukrainian primers mark hard consonants as [–] and soft consonants as [=], which can help you see this contrast on the page. The soft sign only interacts with specific letters to create those truly soft sounds. You will never hear the soft sign itself. You will only hear what it does to its neighbor.

> **Студент:** Що це? *(What is this?)*
> **Вчитель:** Це **м'який знак**. *(This is a soft sign.)*
> **Студент:** Там звук? *(Is there a sound?)*
> **Вчитель:** Ні, він тихий. *(No, it is quiet.)*

Not every consonant can be softened. There are exactly nine consonants that can be truly softened by the **м'який знак**: **Д**, **Т**, **З**, **С**, **Ц**, **Л**, **Н**, **Р**, and **ДЗ**. To help students remember these letters, Ukrainian schools use a classic mnemonic phrase: «**ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи**». If you look closely at the capital letters in that funny phrase, you will see the exact nine consonants that can pair with a soft sign. When you pronounce a hard consonant, your tongue rests normally in your mouth. But when you pronounce its soft equivalent, the middle of your tongue presses up against the roof of your mouth. This physical movement creates a distinct feeling.

:::tip
A common school mnemonic for these letters is «**ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи**». Memorize it, and you will always know which consonants can take a soft sign!
:::

Look at some common word-final patterns where the **м'який знак** appears. You will often see the ending **-нь**, like in the word **день** (day), **кінь** (horse), or **осінь** (autumn). Another frequent ending is **-ль**, which you can find in **сіль** (salt) or **біль** (pain). You will also encounter **-ть** in **мить** (moment) and **-зь** in **мазь** (ointment). To practice reading these soft sounds aloud, try pronouncing these broader words: **учитель** (teacher), **батько** (father), and **маленький** (small). Pay attention to how your tongue moves up to soften that final consonant. It takes time for English speakers to master this palatalized movement, so practice slowly.

<!-- INJECT_ACTIVITY: odd-one-out-soft-sign -->

## Апостроф (The Apostrophe)

If the soft sign exists to soften a consonant, the Ukrainian apostrophe (') exists to do the exact opposite. You can think of the apostrophe as the "anti-soft-sign" or a structural "wall" inside a word. Its main function is to keep the preceding consonant strictly hard and force the following iotated vowel (**я**, **ю**, **є**, **ї**) to split into two distinct sounds. A softened word like **пісня** (song) flows together perfectly because the **Н** is soft. But a word with an apostrophe, like **сім'я** (family), is sharply separated. The **М** stays completely hard, and the **я** splits into a clear [й] plus [а] sound. You must clearly hear two parts.

> **Марія:** Це твоя **сім'я**? *(Is this your family?)*
> **Іван:** Так, це моя **сім'я**. *(Yes, this is my family.)*
> **Марія:** Дуже велика! *(Very big!)*
> **Іван:** Так, нас **п'ять**. *(Yes, there are five of us.)*

There is a core spelling rule for the apostrophe in Ukrainian orthography. The apostrophe appears after the labial, or lip, consonants: **б**, **п**, **в**, **м**, and **ф**. It also appears after the trill **р**. It is placed right before the iotated vowels **я**, **ю**, **є**, and **ї**. It is crucial to understand that this is a unique Ukrainian phonetic separator. It serves a very specific phonetic purpose in the Ukrainian language. When you see it, you must pause slightly and pronounce the following vowel fully. It acts as a visual command to maintain hard boundaries.

:::caution
English speakers often forget to pronounce the [й] sound after an apostrophe. Remember that the apostrophe acts as a wall: **м'ясо** is pronounced with a hard [м], followed by [йасо].
:::

Get some essential reading practice using high-frequency apostrophe words. Try reading these aloud, keeping the first part hard: **п'ять** (five), **дев'ять** (nine), **м'ясо** (meat), **м'яч** (ball), and **об'єкт** (object). You should also practice the word **м'який** (soft), which ironically contains an apostrophe to keep the **М** hard, while the **Й** provides the softness at the end. Note that for the English word "animal", Ukrainian uses **тварина**. You must always avoid the Russian cognate "тварь", which is not standard Ukrainian. The apostrophe appears frequently in borrowed words too, such as **комп'ютер** (computer), functioning exactly the same way.

<!-- INJECT_ACTIVITY: fill-in-missing-sign -->
<!-- INJECT_ACTIVITY: error-correction-apostrophe -->
<!-- INJECT_ACTIVITY: group-sort-signs -->

## Дзвінкі і глухі (Voiced and Voiceless)

Many Ukrainian consonants form voiced-voiceless pairs, but not all consonants do. Sonorants such as **в**, **л**, **м**, **н**, **й**, and **р** are not part of these pairs. The physical concept is simple: voiced consonants use your vocal cords, while voiceless ones do not. You can test this by putting your hand on your throat and saying the sound [з]. You will feel a vibration. Now say [с]. The vibration stops. There are eight primary voiced-voiceless pairs in Ukrainian: **Б-П**, **Д-Т**, **Г-Х**, **Ґ-К**, **З-С**, **Ж-Ш**, **ДЗ-Ц**, and **ДЖ-Ч**. Learning these pairs is vital for clear pronunciation. It also helps you spell correctly when you hear a new word for the first time.

> **Анна:** Це **дуб**? *(Is this an oak?)*
> **Петро:** Так, старий **дуб**. *(Yes, an old oak.)*
> **Анна:** Він там? *(Is it there?)*
> **Петро:** Ні, **дуб** тут. *(No, the oak is here.)*

A defining feature of Ukrainian phonetics is the concept of non-devoicing. In many other languages, voiced consonants lose their voice at the very end of a word. But in Ukrainian, voiced consonants mostly keep their full voiced sound at the end of a word or before voiceless consonants. For example, the word **дуб** (oak) is pronounced exactly as it is written, with a strong [б] at the end. The word **мороз** (frost) is pronounced with a clear [з] at the end. There is one rare exception to remember: the word **легко** (easily) is pronounced [лехко]. Otherwise, trust the spelling and always keep your voice active.

:::note
Unlike English or German, Ukrainian strongly preserves voicing at the end of words. A final **Б** remains a clear **Б**, never turning into a **П**. This gives Ukrainian its characteristic resonant sound.
:::

Understanding voicing is critical because it changes the meaning of words entirely. We can use minimal pairs for ear training to demonstrate this concept. Listen to the difference between **балка** (beam) and **палка** (stick). The only difference is the voicing of the first consonant. Similarly, contrast **коза** (goat) and **коса** (braid). If you accidentally turn that voiced **З** into a voiceless **С**, you will be talking about a braid of hair instead of a farm animal! Practice saying these pairs aloud while covering your ears to ensure the vibration is there.

<!-- INJECT_ACTIVITY: true-false-voicing -->

## Вимова українських звуків (Pronouncing Ukrainian Sounds)

We must focus intensely on the unique Ukrainian vowel **И** [и]. This sound does not exist in English, and it is a common stumbling block for learners. It is entirely distinct from the vowel **І** [і], which sounds like the "ee" in "feet". The sound **И** is deeper and slightly lower in the mouth. We can use minimal pairs to train the ear to hear this crucial difference. Listen to **бик** (bull) versus **бік** (side). Compare **дим** (smoke) with **дім** (house). Contrast **лист** (leaf or letter) against **ліс** (forest). Finally, hear the difference between **кит** (whale) and **кіт** (cat). Mixing these up causes major confusion. Anna Ohoiko's videos on **И** and **Р** are useful for slow repetition practice as you work through these sound drills.

> **Олена:** Це **кіт** чи **кит**? *(Is this a cat or a whale?)*
> **Максим:** Це маленький **кіт**. *(This is a small cat.)*
> **Олена:** Дуже **гарно**! *(Very nicely!)*

Next, we must contrast the letters **Г** and **Ґ**. They look similar, but they are two different letters representing two completely different sounds. The letter **Г** [ɦ] is a voiced fricative. This means air flows continuously through your narrowed throat, creating a soft, breathy sound. Practice this sound in words like **гарно** (nicely, beautifully), **гора** (mountain), and **голова** (head). Its voiceless partner is **Х**. If you say **Х** and add voice, you get **Г**. Do not call **Г** "soft", because in Ukrainian phonetics, **м'який** means palatalized. The letter **Ґ** [g], on the other hand, is a voiced stop. You close your throat fully and release the air, like in **ґанок** (porch) or **ґудзик** (button). Its voiceless partner is **К**.

Finally, practice the Ukrainian rolled or trilled **Р** [р]. This sound requires the tip of your tongue to vibrate rapidly against the roof of your mouth. Practice this trill with words like **рука** (hand or arm), **робота** (work), **ранок** (morning), and **риба** (fish). Many learners worry intensely about perfecting this trill immediately. Reassure yourself: while getting the trill is a great goal, an imperfect **Р** will always be understood by native speakers. Focus on getting comfortable with the language first. You will naturally develop the tongue strength over time.

<!-- INJECT_ACTIVITY: match-up-voiced-voiceless -->
<!-- INJECT_ACTIVITY: quiz-g-vs-g -->

## Підсумок — Summary

Review the fundamental phonetic tools we have covered. What does the **м'який знак** (Ь) do? It acts as a modifier that softens, or palatalizes, the preceding consonant, but it makes absolutely no sound of its own. It is a silent instruction for your tongue to move upward. After which letters does the apostrophe appear? It appears after the labial consonants **б**, **п**, **в**, **м**, **ф**, and the trill **р**, right before the iotated vowels **я**, **ю**, **є**, **ї**. It keeps the consonant completely hard and splits the vowel into two sounds. Can you name three voiced-voiceless pairs? You can use the hand-on-throat vibration test to find them, such as **Б-П**, **Д-Т**, and **З-С**. Remember that sonorants such as **в**, **л**, **м**, **н**, **й**, and **р** do not belong to these voiced-voiceless pairs.
 How is Ukrainian **Г** different from **Ґ**? The letter **Г** is a continuous, breathy voiced fricative that flows through the narrowed throat, while **Ґ** is a hard voiced stop that strictly blocks and releases air. To finish, read these words out loud, paying close attention to the signs and sounds we have practiced today: **сім'я**, **день**, **п'ять**, **гарно**, and **риба**. Understanding these special signs will make your pronunciation authentic and clear.
</generated_module_content>

**PIPELINE NOTE — Word count: 1676 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 73 words | Not found: 8 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іван — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Петро — NOT IN VESUM
  ✗ йасо — NOT IN VESUM
  ✗ лехко — NOT IN VESUM
  ✗ тварь — NOT IN VESUM

All 73 other words are confirmed to exist in VESUM.

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
