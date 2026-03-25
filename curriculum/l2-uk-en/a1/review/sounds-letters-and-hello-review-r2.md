All linguistic checks done. Now I have enough data to produce the full review.

---

## Linguistic Scan

**Russianisms:** None found. All Ukrainian words verified against VESUM.

**Surzhyk:** None found.

**Calques:** None found.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Factual claims check:**
- "33 літери, 38 звуків" — ✅ Confirmed by Заболотний Grade 5, p.73: "38 звуків в українській мові: 6 голосних + 32 приголосні"
- "6 vowel sounds: [а], [о], [у], [е], [и], [і]" — ✅ Correct
- "10 vowel letters" — ✅ Correct (А, О, У, Е, И, І, Я, Ю, Є, Ї)
- "32 consonant sounds" — ✅ Confirmed by Заболотний
- Большакова poems — ✅ Confirmed from RAG: Grade 1 p.24 matches exactly
- "Щ always makes [шч]" — ✅ Correct for standard Ukrainian phonetics
- "Ї always = [йі]" — ✅ Correct
- "рада/радий" gender distinction — ✅ Both verified in VESUM (радий = adj)

**One potential issue:** The module says "Голосні (vowels) — made with voice only, mouth open, no obstruction" — the Большакова textbook says "Голосні звуки утворюються за допомогою голосу" without mentioning "no obstruction." The "no obstruction" is phonetically accurate but not from the cited textbook. This is minor — it's supplementary accurate information, not a factual error.

**No linguistic errors found.**

## Exercise Check

### Exercise 1: `:::quiz` — "Звук чи літера?"
- **Plan match:** ✅ Matches `activity_hints[0]` — type: quiz, focus: distinguish звуки/літери
- **Items:** 6 (plan says 6) ✅
- **Logic check:**
  - Q1: "Що ми чуємо і вимовляємо?" → "звуки" (index 1) ✅
  - Q2: "Що ми бачимо і пишемо?" → "літери" (index 0) ✅
  - Q3: "Скільки літер в абетці?" → "33" (index 2) ✅
  - Q4: "Скільки звуків в українській мові?" → "38" (index 1) ✅
  - Q5: "Які звуки утворюються тільки голосом?" → "голосні" (index 1) ✅
  - Q6: "Які звуки створюють перешкоду в роті?" → "приголосні" (index 0) ✅
- **Answer position distribution:** 1, 0, 2, 1, 1, 0 — reasonable spread ✅
- **Distractors:** Plausible — "слова" and "речення" are real linguistic terms a beginner might confuse ✅
- **Testable with module knowledge:** Yes — all answers covered in section 1 ✅

### Exercise 2: `:::match-up` — "Match false friend Cyrillic letters to their REAL sounds"
- **Plan match:** ✅ Matches `activity_hints[1]` — type: match-up, focus: false friends
- **Items:** 6 (plan says 6) ✅
- **Logic check:** All 6 pairs correct (В→[в], Н→[н], Р→[р], С→[с], У→[у], Х→[х]) ✅
- **Testable:** Yes — taught in section 2 ✅

### Exercise 3: `:::group-sort` — "Sort Cyrillic letters into Голосні and Приголосні"
- **Plan match:** ✅ Matches `activity_hints[3]` — type: group-sort, focus: sort vowels/consonants
- **Items:** 14 letters sorted into 2 groups (plan says 8 items — but 14 total letters across 2 groups is actually better) — acceptable ✅
- **Logic check:** А, О, У, Е, И, І = голосні ✅; К, М, Т, В, Н, Р, С, Х = приголосні ✅
- **Testable:** Yes ✅

### Exercise 4: `:::fill-in` — "Complete a basic greeting dialogue with blanks"
- **Plan match:** ✅ Matches `activity_hints[2]` — type: fill-in, focus: greeting dialogue
- **Items:** 4 (plan says 4) ✅
- **Logic check:**
  - "— ___! Як справи?" → "Привіт" ✅
  - "— Привіт! Як ___?" → "справи" ✅
  - "— Добре. А у ___?" → "тебе" ✅
  - "— ___." → "Чудово" ✅
- **Issue:** The plan specifies "Options per blank: Привіт / справи / Добре / тебе / Чудово / Нормально" — the fill-in exercise has no explicit options listed. The fill-in DSL format may handle this downstream, but as written, there are no distractors/options shown. This is a **minor** format issue — the pipeline's fill-in renderer may add options automatically.
- **Testable:** Yes — all words taught in section 3 ✅

### Exercise 5: `<!-- INJECT_ACTIVITY: quiz-reading-practice -->`
- This is a placeholder for a reading practice quiz that hasn't been filled yet. The plan doesn't have a 5th activity hint, so this is an extra activity the writer added. Not a problem — but it IS still an unfilled placeholder, which means the deterministic tool hasn't processed it. This should be noted.

**Exercise total:** 4 filled exercises + 1 unfilled placeholder. Plan specifies 4 activity types — all 4 are present and filled. ✅

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 5 content_outline sections present. Звуки і літери covers the golden rule ("Ми чуємо і вимовляємо звуки"), 6 vowel sounds, 10 vowel letters, Большакова poems — all plan points hit. Перші слова covers familiar letters (А, О, К, М, Т), false friends (В, Н, Р, С, У, Х), new shapes, Щ=[шч], Ь softens, Ї=[йі]. Привіт covers greeting dialogue, gendered рада/радий, letter-by-letter reading. Читаємо covers environmental signs, city names, Це sentences, Що це?/Хто це?. Підсумок covers self-check. Minor deduction: the plan's Підсумок asks explicit self-check questions ("How many letters? How many sounds?") as questions — the module delivers them as statements in the summary rather than as explicit questions the learner should answer. Also, the plan references (Большакова, Захарійчук, Заболотний, ULP) are mentioned but Захарійчук's [•]/[–] sound notation is not used. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian verified against VESUM (76 words ✓, 6 not-found are proper nouns). No Russianisms, no Surzhyk, no calques. Phonetic claims verified against textbooks (38 sounds = 6+32, Заболотний p.73). Gender forms рада/радий correct. Большакова poems match RAG source exactly. |
| 3. Pedagogical quality | 8/10 | Good PPP flow: presents concept (звуки vs літери) → pattern (poems, letter groups) → practice (exercises). Textbook pedagogy used (Большакова poems integrated naturally). However: the "New shapes" paragraph (Б, Г, Ґ, Д...) is essentially a bare list of 15 letters with only 5 example words — a learner seeing these for the first time gets minimal practice. The plan says "Through words: банк, дім, зима, книга, школа" but 5 words for 15 new letter shapes is thin. Also, the dental T and unaspirated K/T explanation is given but immediately dismissed with "Close enough for now" — which undermines the instruction. |
| 4. Vocabulary coverage | 10/10 | All 10 required vocab used naturally in prose: мама ✅, тато ✅, вода ✅, рука ✅, книга ✅, школа ✅, привіт ✅, як справи ✅, добре ✅, чудово ✅. All 6 recommended vocab present: банк ✅, аптека ✅, метро ✅, пошта ✅, зупинка ✅, нормально ✅. Words introduced in context, not as lists. |
| 5. Exercise quality | 9/10 | All 4 plan activity types present with correct item counts. Quiz has varied answer positions (0,1,2 spread). Match-up tests exactly what was taught. Group-sort has balanced groups. Fill-in follows the exact dialogue pattern from the plan. Minor: fill-in lacks explicit option lists (plan specifies "Options per blank"). One unfilled `<!-- INJECT_ACTIVITY -->` placeholder remains — but this is an extra, not a missing plan activity. |
| 6. Engagement & tone | 7/10 | **Deductions:** Multiple instances of meta-commentary and telling-not-showing: "Look at the text on this page. What you are seeing right now are letters. Now, say a word out loud. What you just produced is a sound." — this is generic and could apply to any language. "Guide your eyes through each word slowly" — instructional filler. "Encourage yourself to recognize" — self-help language. "By sounding out these famous locations, you are training your brain to decode the Cyrillic alphabet quickly and accurately" — motivational filler. No humor. No cultural details beyond city names. The Привіт dialogue is natural but very short (3 lines). **Rewards:** The Большакова poems add genuine cultural texture. The environmental reading (street signs) is a concrete, imaginable scenario. The false friends framing is engaging. |
| 7. Structural integrity | 9/10 | All H2 headings match plan sections. Clean markdown. Word count 1315 meets 1200 target ✅. One minor issue: the `<!-- INJECT_ACTIVITY: quiz-reading-practice -->` placeholder is a stray artifact that should either be filled or removed. The `<div class="dialogue">` block uses raw HTML — should this be a `:::dialogue` DSL block instead? |
| 8. Cultural accuracy | 10/10 | Ukrainian presented entirely on its own terms. No "like Russian but..." framing. Decolonized city names (Київ, not "Kiev"; Одеса, not "Odessa"; Харків, not "Kharkov"). Большакова and Заболотний cited — real Ukrainian pedagogical tradition. Gender distinction (рада/радий) introduced naturally without comparison to other languages. |
| 9. Dialogue & conversation quality | 7/10 | Only one dialogue in the entire module — the Оленка/Тарас greeting exchange. It's natural and uses named speakers ✅, but it's extremely minimal (3 lines). The plan's greeting section has more material (Рада/Радий тебе бачити!) that could have been woven into a second dialogue exchange. The fill-in exercise is essentially a second dialogue, but it's an exercise, not a modeled conversation. For a module titled "Sounds, Letters, and Hello," the "Hello" part is underrepresented in dialogue form. A second short dialogue showing рада/радий in use would strengthen this significantly. |

## Findings

```
[ENGAGEMENT] [MAJOR]
Location: Section 1, opening paragraph: "Look at the text on this page. What you are seeing right now are letters. Now, say a word out loud. What you just produced is a sound."
Issue: Generic meta-commentary that could apply to any language course. Tells instead of shows. The module should open with Ukrainian, not with an abstract English thought experiment.
Fix: Replace with a concrete Ukrainian-grounded opening that immediately uses Ukrainian sounds/letters to demonstrate the concept.

[ENGAGEMENT] [MINOR]
Location: Section 4 (Читаємо), paragraph 2: "Encourage yourself to recognize both the familiar letters that look like English and the entirely new shapes. By sounding out these famous locations, you are training your brain to decode the Cyrillic alphabet quickly and accurately."
Issue: Motivational filler — "training your brain to decode... quickly and accurately" is generic self-help language that adds no content.
Fix: Replace with concrete reading guidance or an additional example.

[PEDAGOGY] [MINOR]
Location: Section 2 (Перші слова), paragraph 1: "Close enough for now."
Issue: Dismissive phrasing that undermines the instruction about dental T and unaspirated K/T. The learner might think pronunciation doesn't matter.
Fix: Reframe positively — e.g., "You will refine this naturally as you hear more Ukrainian."

[DIALOGUE] [MAJOR]
Location: Section 3 (Привіт!): Only one 3-line dialogue (Оленка/Тарас).
Issue: The "Hello" section — the module's title topic — has only one minimal dialogue. The рада/радий тебе бачити! phrase is explained but never demonstrated in a conversation. A module teaching greetings should model at least 2 dialogue exchanges.
Fix: Add a second short dialogue demonstrating рада/радий тебе бачити! with named speakers and a natural situation (e.g., two friends meeting after a break).

[STRUCTURAL] [MINOR]
Location: Section 4 (Читаємо): `<!-- INJECT_ACTIVITY: quiz-reading-practice -->`
Issue: Unfilled activity placeholder remains in the content. This is a stray artifact.
Fix: Either fill with a reading quiz or remove the placeholder.

[PLAN ADHERENCE] [MINOR]
Location: Section 5 (Підсумок)
Issue: The plan specifies self-check questions ("How many letters? How many sounds? Why are they different?...") but the summary delivers answers as statements, not questions. The plan's intent is a self-check quiz format.
Fix: Reframe key points as questions the learner should answer before reading the answer.
```

## Verdict: REVISE

The module has strong linguistic accuracy (10/10), excellent vocabulary coverage, and solid plan adherence. No critical issues. However, two major findings need fixing: (1) the generic meta-commentary opening that misses an opportunity to hook the learner with Ukrainian from the start, and (2) the thin dialogue coverage for a module titled "Hello" — only one 3-line exchange when a second dialogue demonstrating рада/радий would significantly improve the greeting section. These are fixable without rewrite.

<fixes>
- find: "Look at the text on this page. What you are seeing right now are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade:"
  replace: "Every Ukrainian child learns one golden rule on their very first day of language class:"
- find: "Encourage yourself to recognize both the familiar letters that look like English and the entirely new shapes. By sounding out these famous locations, you are training your brain to decode the Cyrillic alphabet quickly and accurately."
  replace: "Pay attention to the false friends — Харків starts with Х [х], not an English \"H\". Львів has two letters (ь, і) that English lacks entirely."
- find: "Also, the letters **К** and **Т** are unaspirated, meaning there is no puff of air when you say them."
  replace: "Also, the letters **К** and **Т** are unaspirated, meaning there is no puff of air when you say them. You will refine this naturally as you hear more Ukrainian."
- find: "Close enough for now."
  replace: ""
- find: "Try reading **Привіт!** letter by letter."
  replace: "Here is another greeting you will hear often:\n\n<div class=\"dialogue\">\n\n\n**Марія:** Привіт, Андрію!\n\n\n**Андрій:** О, Марія! Привіт! Рада тебе бачити!\n\n\n**Марія:** Радий... Андрію, я — жінка. Я кажу «рада». А ти кажеш «радий».\n\n\n**Андрій:** Ой! Радий тебе бачити! А ти — рада?\n\n\n**Марія:** Так, рада! Як справи?\n\n\n**Андрій:** Чудово!\n\n\n</div>\n\nNotice how Марія corrects Андрій — she says **рада** (feminine), and he says **радий** (masculine). This playful moment shows how gender works naturally in Ukrainian conversation.\n\nNow try reading **Привіт!** letter by letter."
- find: "You have learned the fundamental difference between sounds and letters: there are 33 **літери** (letters) that we write, but 38 **звуки** (sounds) that we hear and pronounce. You now recognize the two main sound families: **голосні** (vowels) which use only your voice, and **приголосні** (consonants) which use your voice and noise. Always remember to watch out for the false friend letters (В, Н, Р, С, У, Х) that look like English but sound completely different in Ukrainian. You also learned essential conversational phrases like **Привіт!** (Hi!), **Як справи?** (How are you?), and how to answer with **Добре** (good) or **Чудово** (great). Finally, you practiced your reading skills by decoding common street signs and major city names. Keep practicing these signs and sounding out new Cyrillic words to build your reading speed before moving on to the next module."
  replace: "Test yourself before moving on:\n\n- Скільки літер в абетці? How many letters in the alphabet? — **33**\n- Скільки звуків в українській мові? How many sounds? — **38**\n- Чому їх кількість різна? Why are they different? — Because some letters represent two sounds, and the soft sign (Ь) represents no sound at all.\n- Що таке голосні? What are vowels? — Sounds made with voice only, no obstruction: [а], [о], [у], [е], [и], [і].\n- Що таке приголосні? What are consonants? — Sounds made with voice and noise, or noise only — lips, teeth, and tongue create obstruction.\n- Що означає «Привіт»? What does Привіт mean? — Hi! (informal)\n- Як відповісти на «Як справи?» How to answer? — Добре. Чудово. Нормально.\n\nWatch out for the false friend letters (В, Н, Р, С, У, Х) — they look like English but sound completely different. Keep sounding out new Cyrillic words to build your reading speed before moving on to the next module."
- find: "<!-- INJECT_ACTIVITY: quiz-reading-practice -->"
  replace: ""
</fixes>
