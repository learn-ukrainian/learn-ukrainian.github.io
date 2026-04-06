✅ Message sent to Gemini (ID: 28129) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28129...
📨 Message #28129
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-a1-sounds-letters-and-hello-r4
   Time: 2026-04-05T21:34:46.595487+00:00

============================================================

You are a HARSH adversarial reviewer of a A1 pedagogical brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: a1, Slug: sounds-letters-and-hello, Round: 4

## Review Rubric (score EACH dimension 1-10, then average)

1. **Factual accuracy** — every claim must have evidence from sources. Vague or unsourced claims → deduct points.
2. **Ukrainian language quality** — check for Russianisms (кон→кін), surzhyk (шо→що), calques (приймати душ→брати душ). Even ONE Russianism = max 7/10.
3. **Decolonization** — is Ukrainian presented on its own terms? Any 'like Russian but...' framing = max 6/10.
4. **Completeness** — does it cover ALL aspects a module writer needs? Missing sections or shallow treatment → deduct.
5. **Actionable guidance** — can a writer actually USE this? Generic advice like 'teach it well' = max 5/10. Must have specific examples, sequences, exercises.

## Rules
- Score each dimension separately, then give weighted average.
- Be honest. If the article is excellent, say so. 10/10 IS possible.
- 9/10 = excellent with minor issues. 8/10 = good. 7/10 = needs work.
- Output a <fixes> block with specific changes. If the article is clean, output <fixes></fixes> (empty).
- Do NOT invent problems. Fabricated issues waste rebuild cycles.

## Fix syntax

Two formats are available:

**1. Replace existing text** (for corrections, rewording):
Use a SHORT anchor (1-2 sentences max) for the old: text. Do NOT paste massive paragraphs — they break exact matching.
```
old: short exact text to find
new: replacement text
```

**2. Insert new content** (for missing sections, added examples):
Use INSERT AFTER with a short anchor from the article, then the new text to add.
```
INSERT AFTER: short anchor text that exists in the article
NEW TEXT: the new content to insert after the anchor
```

Separate multiple fixes with `---`.

## Output format

Dimension scores:
1. Factual: X/10 — [evidence]
2. Language: X/10 — [evidence]
3. Decolonization: X/10 — [evidence]
4. Completeness: X/10 — [evidence]
5. Actionable: X/10 — [evidence]

**Overall: X/10**

<fixes>
old: exact text to find in the article
new: replacement text
---
INSERT AFTER: anchor text in article
NEW TEXT: content to add after the anchor
</fixes>

## Article to review

# Педагогіка A1: Sounds, Letters, And Hello

<!-- wiki-meta
slug: sounds-letters-and-hello
domain: pedagogy/a1
tracks: [a1, a2]
sources: [5-klas-ukrmova-uhor-2022-1_s0139, 10-klas-ukrmova-glazova-2018_s0138, 2-klas-ukrmova-kravcova-2019-1_s0026, 2-klas-ukrmova-kravcova-2019-1_s0045, 5-klas-ukrmova-avramenko-2022_s0097, 5-klas-ukrmova-avramenko-2022_s0104, 5-klas-ukrmova-avramenko-2022_s0105, 5-klas-ukrmova-litvinova-2022_s0117, 5-klas-ukrmova-litvinova-2022_s0165, 5-klas-ukrmova-uhor-2022-1_s0155, 9-klas-ukrajinska-mova-voron-2017_s0199, 10-klas-ukrajinska-mova-avramenko-2018_s0115, 10-klas-ukrajinska-mova-zabolotnij-2018_s0110, 10-klas-ukrmova-karaman-2018_s0078, 10-klas-ukrmova-zabolotnyi-2018_s0110, 1-klas-bukvar-bolshakova-2018-1_s0028, 1-klas-bukvar-zaharijchuk-2025-1_s0013, 2-klas-ukrmova-bolshakova-2019-1_s0004, 2-klas-ukrmova-bolshakova-2019-1_s0049, 2-klas-ukrmova-kravcova-2019-1_s0029, 2-klas-ukrmova-kravcova-2019-1_s0034, 2-klas-ukrmova-kravcova-2019-1_s0039, 2-klas-ukrmova-kravcova-2019-1_s0042, 5-klas-ukrmova-avramenko-2022_s0078, 5-klas-ukrmova-avramenko-2022_s0114, 5-klas-ukrmova-avramenko-2022_s0138, 5-klas-ukrmova-golub-2022_s0073, 5-klas-ukrmova-golub-2022_s0089, 5-klas-ukrmova-litvinova-2022_s0107, 5-klas-ukrmova-litvinova-2022_s0111, 5-klas-ukrmova-litvinova-2022_s0126, 5-klas-ukrmova-litvinova-2022_s0143, 5-klas-ukrmova-uhor-2022-1_s0148, 5-klas-ukrmova-uhor-2022-1_s0160, 5-klas-ukrmova-zabolotnyi-2023_s0077, 5-klas-ukrmova-zabolotnyi-2023_s0081, 5-klas-ukrmova-zabolotnyi-2023_s0103, 5-klas-ukrmova-zabolotnyi-2023_s0105, 5-klas-ukrmova-zabolotnyi-2023_s0136, 5-klas-ukrmova-zabolotnyi-2023_s0144, ext-article-0, ext-article-1, ext-article-2, ext-video-3, ext-video-4]
compiled: 2026-04-05
-->

## Методичний підхід (Methodological Approach)

The foundational A1 modules must be grounded in the native Ukrainian pedagogical tradition for teaching literacy. This approach is sound-first (`звуковий аналіз`), not letter-first. It prioritizes phonemic awareness and the physical act of pronunciation before overwhelming the learner with graphemes.

**1. Від Звука до Букви (Sound-First Principle):**
Before introducing a single letter, the learner must understand the concept of sounds (`звуки`) as distinct from letters (`букви`). The core distinction is between vowels (`голосні`), which are produced with voice and an open vocal tr

## Instructions
1. Read the critique carefully.
2. Identify which SPECIFIC sections need rewriting to address the critique.
3. Output the COMPLETE article with those sections rewritten.
4. Do NOT remove or degrade sections that scored well.
5. Do NOT add commentary — output ONLY the article markdown.

## Current article

# Педагогіка A1: Sounds, Letters, And Hello

<!-- wiki-meta
slug: sounds-letters-and-hello
domain: pedagogy/a1
tracks: [a1, a2]
sources: [5-klas-ukrmova-uhor-2022-1_s0139, 10-klas-ukrmova-glazova-2018_s0138, 2-klas-ukrmova-kravcova-2019-1_s0026, 2-klas-ukrmova-kravcova-2019-1_s0045, 5-klas-ukrmova-avramenko-2022_s0097, 5-klas-ukrmova-avramenko-2022_s0104, 5-klas-ukrmova-avramenko-2022_s0105, 5-klas-ukrmova-litvinova-2022_s0117, 5-klas-ukrmova-litvinova-2022_s0165, 5-klas-ukrmova-uhor-2022-1_s0155, 9-klas-ukrajinska-mova-voron-2017_s0199, 10-klas-ukrajinska-mova-avramenko-2018_s0115, 10-klas-ukrajinska-mova-zabolotnij-2018_s0110, 10-klas-ukrmova-karaman-2018_s0078, 10-klas-ukrmova-zabolotnyi-2018_s0110, 1-klas-bukvar-bolshakova-2018-1_s0028, 1-klas-bukvar-zaharijchuk-2025-1_s0013, 2-klas-ukrmova-bolshakova-2019-1_s0004, 2-klas-ukrmova-bolshakova-2019-1_s0049, 2-klas-ukrmova-kravcova-2019-1_s0029, 2-klas-ukrmova-kravcova-2019-1_s0034, 2-klas-ukrmova-kravcova-2019-1_s0039, 2-klas-ukrmova-kravcova-2019-1_s0042, 5-klas-ukrmova-avramenko-2022_s0078, 5-klas-ukrmova-avramenko-2022_s0114, 5-klas-ukrmova-avramenko-2022_s0138, 5-klas-ukrmova-golub-2022_s0073, 5-klas-ukrmova-golub-2022_s0089, 5-klas-ukrmova-litvinova-2022_s0107, 5-klas-ukrmova-litvinova-2022_s0111, 5-klas-ukrmova-litvinova-2022_s0126, 5-klas-ukrmova-litvinova-2022_s0143, 5-klas-ukrmova-uhor-2022-1_s0148, 5-klas-ukrmova-uhor-2022-1_s0160, 5-klas-ukrmova-zabolotnyi-2023_s0077, 5-klas-ukrmova-zabolotnyi-2023_s0081, 5-klas-ukrmova-zabolotnyi-2023_s0103, 5-klas-ukrmova-zabolotnyi-2023_s0105, 5-klas-ukrmova-zabolotnyi-2023_s0136, 5-klas-ukrmova-zabolotnyi-2023_s0144, ext-article-0, ext-article-1, ext-article-2, ext-video-3, ext-video-4]
compiled: 2026-04-05
-->

## Методичний підхід (Methodological Approach)

The foundational A1 modules must be grounded in the native Ukrainian pedagogical tradition for teaching literacy. This approach is sound-first (`звуковий аналіз`), not letter-first. It prioritizes phonemic awareness and the physical act of pronunciation before overwhelming the learner with graphemes.

**1. Звук-Спочатку (Sound-First Principle):**
Before introducing a single letter, the learner must understand the concept of sounds (`звуки`) as distinct from letters (`букви`). The core distinction is between vowels (`голосні`), which are produced with voice and an open vocal tract, and consonants (`приголосні`), which involve obstruction.
- **Native Method:** Ukrainian first-grade textbooks (e.g., Захарійчук, Source 17) introduce simple visual models: a circle `[•]` for a vowel and a dash `[–]` for a consonant. This abstract representation is a cornerstone of early literacy and should be used in initial exercises.
- **Application:** The first lesson should involve listening to words like `мама` and identifying the sounds: `[–] [•] [–] [•]`.

**2. Від Дзвінкого до Глухого (From Voiced to Voiceless):**
The distinction between voiced (`дзвінкі`) and voiceless (`глухі`) consonants is fundamental. This is not just a theoretical concept; it's a physical one.
- **Native Method:** Кравцова (Source 22) suggests a brilliant kinesthetic exercise: have students cover their ears and pronounce sounds like `[д]` and `[т]`. They will *feel* the vibration ("дзвенить" - it rings) for the voiced consonant, but not for the voiceless one. This physical feedback is more effective than abstract explanations.
- **Application:** This "ear-covering" technique should be presented as a primary tool for learners to self-diagnose and correctly produce voiced/voiceless pairs.

**3. Принцип Милозвучності (The Principle of Euphony):**
Ukrainian is characterized by its "милозвучність" (euphony), a natural flow that avoids difficult consonant clusters. This is not an advanced topic; it's a core feature that explains the `у/в` and `і/й` alternations (Source 12, 28).
- **Native Method:** Textbooks demonstrate how sentences become clunky and hard to pronounce without these alternations.
- **Application:** Introduce this concept early as a feature that makes the language beautiful and easier to speak. Frame `в/у` not as two separate prepositions but as one, which changes its "clothing" depending on its neighbors to make the sentence "sing". Example: `Він в школі` (awkward) becomes `Він у школі`, but `Побувала у Одесі` becomes `Побувала в Одесі`. Presenting this as a rule of "politeness" between sounds makes it intuitive.

**4. Транскрипція як Інструмент (Transcription as a Tool):**
Phonetic transcription is not just for linguists. Ukrainian pedagogy uses a simplified version to clarify pronunciation where it deviates from writing (Source 29, 10). It's a bridge between sound and letter.
- **Application:** Introduce transcription symbols gradually as needed. The most crucial are: `[´]` for stress, `[′]` for softness (`[т′]`), and `[:]` for length (`[н′:]`). Using them clarifies pronunciation rules before the learner has fully internalized them.
**5. Наголос (Stress as a Meaning-Maker):**
Ukrainian stress is free and mobile, meaning it can fall on any syllable and can change forms or meanings (`за́мок` vs `замо́к`, `брати́` vs `бра́ти`).
- **Application:** From lesson one, every new word must be presented with an explicit stress mark (`´`). English speakers tend to swallow unstressed syllables; explicit stress marks help them maintain the "proud and clear" vowels of Ukrainian.

## Послідовність введення (Introduction Sequence)

The order of introduction is critical to build confidence and avoid cognitive overload. The path should be from simple and familiar to complex and unique.

1.  **Phase 1: The Core Vowels and "Easy" Consonants.**
    *   **Vowels:** `А, О, У`. These have relatively stable pronunciations and parallels in English.
    *   **Consonants:** `М, Т, К`. These look familiar and sound as expected.
    *   **First Words:** `мама`, `тато`, `там`, `так`, `мак`, `тут`. Immediately readable words that use ONLY the introduced letters (А, О, У, М, Т, К).

2.  **Phase 2: "False Friends" and the Key Vowel Distinction.**
    *   **Consonants:** Introduce Cyrillic letters that are "false friends" to the Latin alphabet user: `В` (V), `Н` (N), `Р` (R), `С` (S). Drill them until the Latin-based instinct is broken.
    *   **Vowels:** Introduce `И` and `І`. This is the single most important vowel contrast for an English speaker to master. Use minimal pairs from day one: `дим - дім`, `кит - кіт`. (Source 1, 31). Explain that `І` softens the preceding consonant.

3.  **Phase 3: The Iotated Vowels (The "Й" System).**
    *   Introduce `Я, Ю, Є` as a system. Explain their dual function based on position (Source 43):
        *   **After a vowel/start of word:** `Й + Vowel` (`моя` = `[мойа]`, `яблуко` = `[йаблуко]`).
        *   **After a consonant:** Softens the consonant + `Vowel` (`дякую` = `[д′акуйу]`).
    *   Introduce `Ї` separately as the "always honest" iotated vowel. It *always* represents `[йі]`, no exceptions (`їжак`, `Київ`).

4.  **Phase 4: The Soft Sign and the Apostrophe (The Softener and the Hard Wall).**
    *   **Soft Sign `ь`:** Introduce `ь` as a pure grammatical marker that has no sound but softens the preceding consonant from a specific list (`д, т, з, с, ц, л, н` - mnemonic "Де Ти З’їСи Ці ЛиНи?", plus `дз`, Source 31). Use minimal pairs: `рис - рись`. (Source 20).
    *   **Apostrophe `’`:** Introduce the apostrophe as a "hard wall". It does the opposite of the soft sign: it *prevents* softening and forces the following `я, ю, є, ї` to be pronounced with a full `[й]` sound. This should be taught with labial consonants (`б, п, в, м, ф`) and `р`. Example: `сім'я` (`[с′імйа]`, not `[с′ім′а]`). (Source 9, 39).

5.  **Phase 5: The Unique Sounds.**
    *   **`Г` vs `Ґ`:** Teach `Г` as the standard voiced fricative `/ɦ/` and `Ґ` as the `/g/` stop found in a limited set of words (`ґрунт`, `ґудзик`, `аґрус`). Do not present `Г` as a "weird G".
    *   **`Щ`:** Teach this letter as a consistent two-sound combination: `[шч]`. (`борщ` = `[боршч]`). (Source 3).
    *   **Digraphs `ДЖ` and `ДЗ`:** Teach these as single sounds (affricates). `ДЖ` is like "j" in "jeans" (`джинси`). For `ДЗ` (`дзеркало`), explain it is a single consonant burst, unlike the two separate sounds in the English "kids" (which has a morpheme boundary). Contrast the single-sound `дз` in root words with two separate sounds at a prefix boundary, e.g., `під-земний`. (Source 33).

## Типові помилки L2 (Common L2 Errors)

The writer must proactively build exercises to counter these predictable errors for English speakers.

1.  **Devoicing Final Consonants:** An English speaker will automatically pronounce `гриб` as `[грип]`.
    *   **Prevention:** Ukrainian textbooks are explicit: "Дзвінкі приголосні... не можна оглушувати" (Voiced consonants... must not be devoiced) (Source 6). Drill minimal pairs like `гриб` (mushroom) / `грип` (flu), `казка` (fairy tale) / `каска` (helmet) from the very beginning. The kinesthetic "cover your ears" test helps here.

2.  **Mispronunciation of `И`:** Learners will default to English "i" (as in "sit") or "ee" (as in "see").
    *   **Prevention:** Use the "smile-unsmile" technique. `І` is pronounced with lips spread, like a smile. `И` is pronounced with the lips relaxed, jaw slightly dropped, and the tongue pulled back slightly from the `І` position. It's the sound of disgust, "eugh". Use minimal pairs relentlessly: `лис - ліс`, `ти - ті`.

3.  **Incorrect `В` Pronunciation:** It will be pronounced as a hard English `[v]` or a `[w]`.
    *   **Prevention:** Explain and drill the concept of the non-syllabic `[ў]` (Source 6). At the end of a word (`лев` -> `[леў]`) or before a consonant (`завтра` -> `[заўтра]`), the lips come together lightly without teeth touching the bottom lip. It is a vowel-like consonant.

4.  **Failure to Palatalize (Soften):** Consonants before `і, є, ю, я, ь` will be pronounced hard. `Дякую` will sound like `[дйакую]` instead of `[д′акую]`.
    *   **Prevention:** Treat soft consonants as distinct phonemes. The tongue position changes. For `[т′]`, the body of the tongue raises towards the palate. Use drills contrasting `[ту]` and `[т′у]` (`тюль`).

5.  **Unstressed Vowel Reduction (Russian Interference):** Learners familiar with Russian will reduce unstressed `о` to `[a]`.
    *   **Prevention:** Emphasize that Ukrainian vowels are "proud and clear". `молоко` is `[молоко]`, not `[малако]` (Source 5). This is a crucial decolonization point and makes Ukrainian pronunciation easier than Russian. The only major reduction is `[е]` towards `[еи]` and `[и]` towards `[ие]`, which can be taught later.

## Деколонізаційні застереження (Decolonization Notes)

From the first lesson, the curriculum must establish Ukrainian as a language in its own right, not as a dialect or derivative of Russian.

1.  **NEVER Use Russian as a Phonetic Reference:**
    *   **Do not** say "Ukrainian `И` is like Russian `Ы`". Instead, describe its articulation independently.
    *   **Do not** say "Ukrainian `Г` is different from Russian `Г`". Instead, teach `[г]` `/ɦ/` as the primary sound and `[ґ]` `/g/` as its partner. The Russian pronunciation is irrelevant.
    *   **DO** highlight key differences that prevent negative transfer. The clearest example is unstressed `[o]`. Explicitly state: "Unlike in Russian, Ukrainian `о` is always pronounced as `[o]`. The word `молоко` is pronounced `[молоко]`. This makes Ukrainian very consistent."

2.  **Emphasize Unique Ukrainian Features:**
    *   Celebrate the letter `Ї`. It is unique to Ukrainian in the modern Cyrillic alphabets and a point of pride.
    *   Celebrate the letter `Ґ`. Its return to the alphabet in 1990 was an act of de-Russification.
    *   Frame "милозвучність" (euphony) as a defining characteristic of the language's beauty.

3.  **Avoid Surzhyk and Russianisms:**
    *   Use `дякую` as the primary "thank you". While `спасибі` is a native Ukrainian word (from "Спаси Біг"), `дякую` is preferred in many modern contexts to establish a distinct rhythm and avoid perceived overlap with Russian.
    *   Use vocabulary that is unambiguously Ukrainian. Check words against the `r2u.org.ua` dictionary to ensure they are not calques. For A1, this is less of a risk, but the principle must be established.



============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18324 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a A1 pedagogical brief for the Ukrainian language curri...
Dimension scores:
1. Factual: 8/10 — Misses the `[=]` symbol for soft consonants in the visual model, which is factually incorrect and incomplete when describing the native Ukrainian method (Bukvar). `[–]` specifically means a *hard* consonant, not just any consonant.
2. Language: 7/10 — "Звук-Спочатку" is an awkward, direct calque of English "Sound-First". The established native pedagogical phrase is "Від звука до букви" or "Звуковий аналіз". 
3. Decolonization: 10/10 — Excellent. Properly frames Ґ/Г independently of Russian, and specifically targets the Russian unstressed `о` reduction as a negative transfer to avoid.
4. Completeness: 8/10 — Fails to include the soft consonant visual model `[=]`, which is essential for laying the groundwork for Phase 4 where palatalization (softening) is explicitly taught. 
5. Actionable: 10/10 — The "cover your ears" kinesthetic test, "smile-unsmile" technique, and the `в`/`у` euphony framing are highly specific, practical tools for module writers.

**Overall: 8.6/10**

<fixes>
old: **1. Звук-Спочатку (Sound-First Principle):**
new: **1. Від звука до букви (Sound-First Principle):**
---
old: introduce simple visual models: a circle `[•]` for a vowel and a dash `[–]` for a consonant. This abstract representation
new: introduce simple visual models: a circle `[•]` for a vowel, a single dash `[–]` for a hard consonant, and a double dash `[=]` for a soft consonant. This abstract representation
---
old: identifying the sounds: `[–] [•] [–] [•]`.
new: identifying the sounds: `[–] [•] [–] [•]`, and later contrasting hard and soft consonants with words like `ліс` `[=] [•] [–]`.
</fixes>


────────────────────────────────────────
✅ Gemini finished (1642 chars)
✅ Message sent to Claude (ID: 28130)
✓ Message 28130 acknowledged
   Auto-acknowledged reply #28130 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-a1-sounds-letters-and-hello-r4' — skipping GH posting (review saved to orchestration/)
✓ Message 28129 acknowledged
