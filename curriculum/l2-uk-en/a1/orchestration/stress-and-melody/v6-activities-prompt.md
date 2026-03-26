# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/stress-and-melody.yaml` file for module **4: Stress and Melody** (a1).

Output **pure YAML only** — no markdown fencing, no preamble, no explanation. Just the YAML document.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-stress-syllable -->`
- `<!-- INJECT_ACTIVITY: quiz-sentence-type -->`
- `<!-- INJECT_ACTIVITY: fill-in-punctuation -->`
- `<!-- INJECT_ACTIVITY: match-stress-pairs -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Where is the stress? Choose the correct syllable.
  items: 8
  type: quiz
- focus: 'Match stress pairs: замок (castle) ↔ замок (lock)'
  items: 4
  type: match-up
- focus: Statement, question, or exclamation? Choose based on punctuation.
  items: 6
  type: quiz
- focus: 'Add the correct punctuation: Це кава_ Де метро_ Як гарно_'
  items: 6
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- мука (flour) — stress pair with мука (torment)
- ранок (morning) — first-syllable stress
- метро (metro) — last-syllable stress
- фотографія (photograph) — long word practice
required:
- наголос (stress/accent) — metalanguage word
- замок (castle) — stress pair (first syllable)
- замок (lock) — stress pair (second syllable)
- кава (coffee) — first-syllable stress
- вода (water) — second-syllable stress
- столиця (capital) — Київ — столиця України


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Наголос (Stress)

Ukrainian has 38 sounds, and one invisible force organizes them all: **наголос** (stress). When you say a word, one syllable comes out louder and longer than the others. That syllable carries the stress. What makes Ukrainian special — and challenging — is that stress is free. It can land on any syllable. **Мама** (mother) — stress on the first syllable. **Вода** (water) — stress on the last. **Столиця** (capital city) — stress in the middle. There is no fixed position, no shortcut. And stress moves between forms of the same word: **рука** (hand) becomes **руки** (hands), with the stress jumping from the last syllable to the first. French always stresses the last syllable. Czech always stresses the first. Ukrainian follows no such pattern — every word must be learned with its stress.

Why does this matter so much? Because wrong stress produces a different word entirely. Consider **замок**. With stress on the first syllable — **замок** — it means "castle." With stress on the second — **замок** — it means "lock." Two completely different things. The same happens with **мука**: stress on the first syllable gives you **мука** (torment), stress on the last gives you **мука** (flour). And **атлас**: first syllable — **атлас** (atlas, a book of maps); second syllable — **атлас** (satin fabric). A learner pointing at a castle and saying замОК will confuse every listener. This is not a subtle distinction — it is the difference between two unrelated words.

In textbooks and dictionaries, stress is shown with a mark (´) over the vowel. But everyday Ukrainian — books, street signs, text messages — has no stress marks at all. Native speakers simply know. As a learner, you have an excellent tool: the online dictionary goroh.pp.ua, where you can check the stress on any Ukrainian word. Over time, stress becomes automatic — like knowing where the beat falls in a familiar song.

Here are common A1 words grouped by stress position. First syllable: **мама** (mother), **тато** (father), **ранок** (morning), **кава** (coffee), **книга** (book), **хата** (house). Last syllable: **вода** (water), **зима** (winter), **рука** (hand), **метро** (metro), **кафе** (café). Middle syllable: **столиця** (capital), **аптека** (pharmacy), **дитина** (child). These groupings are for convenience only — there is no reliable rule that predicts stress position. The only real strategy is to learn each word's stress when you first meet it. A Grade 2 textbook puts it simply: "Щоб запам'ятати наголос у слові, правильно проговори його кілька разів" — to remember a word's stress, say it correctly several times.

<!-- INJECT_ACTIVITY: quiz-stress-syllable -->

One more thing to notice now: stress moves between forms. **Рука** (hand) has stress on the last syllable, but **руки** (hands) shifts it to the first. **Вода** (water) stresses the last syllable, but **води** (waters) moves stress to the first. You cannot simply memorize "вода = last syllable" and apply it everywhere — the stress shifts when the word changes form. For now, just notice that this happens. Later modules will cover these patterns systematically as you learn noun forms.

## Інтонація (Intonation)

Same words. Different melody. Different meaning. This is **інтонація** (intonation) — the rise and fall of your voice across a sentence. Listen to the difference in these three sentences, all built from the same two words:

**Це кава.** ↘ — Your voice falls at the end. You are telling someone: this is coffee.
**Це кава?** ↗ — Your voice rises on the last stressed syllable. You are asking: is this coffee?
**Це кава!** ↘↘ — Your voice drops sharply. You are surprised or excited: this is coffee!

The words are identical. Only the melody and the punctuation change. Intonation is how Ukrainian distinguishes telling from asking from exclaiming — and getting it right matters just as much as getting the words right.

There is one important exception. When a sentence starts with a question word — **хто** (who), **що** (what), **де** (where), **коли** (when) — the question word itself signals "this is a question." So the intonation falls, not rises: **Що це?** ↘ **Де метро?** ↘ **Коли?** ↘ But yes/no questions — the kind with no question word — must rise: **Це метро?** ↗ **Ти тут?** ↗ Here is a simple test: if you can answer **так** (yes) or **ні** (no), the intonation rises. If the question begins with a question word, it falls. Practice this pair: **Де кава?** ↘ versus **Це кава?** ↗

<!-- INJECT_ACTIVITY: quiz-sentence-type -->

Ukrainian grammar gives names to these sentence types. **Розповідні речення** (declarative sentences) tell or report something — they end with a period. **Питальні речення** (interrogative sentences) ask something — they end with a question mark. **Спонукальні речення** (imperative sentences) command or request — they end with an exclamation mark or a period. Any of these three types can also be **окличні** (exclamatory) — that is a separate quality layered on top, not a fourth category. For A1, focus on recognizing the three punctuation marks and matching them to the right melody: period ↘, question mark ↗ (or ↘ with question words), exclamation mark ↘↘.

<!-- INJECT_ACTIVITY: fill-in-punctuation -->

Here is a short dialogue that uses all three intonation patterns. Two friends meet at a café:

> **Оленка:** Привіт! Це нове кафе? ↗ *(Hi! Is this a new café?)*
> **Тарас:** Так, це нове кафе. ↘ *(Yes, this is a new café.)*
> **Оленка:** Де кава? ↘ *(Where's the coffee?)*
> **Тарас:** Ось кава. ↘ *(Here's the coffee.)*
> **Оленка:** Як гарно! ↘↘ *(How lovely!)*

Notice: **Це нове кафе?** rises because it is a yes/no question. **Де кава?** falls because **де** is a question word. **Так, це нове кафе.** and **Ось кава.** both fall as statements. **Як гарно!** drops sharply as an exclamation. This dialogue recycles **кафе** and **кава** from the stress section and **Привіт** from Module 1.

## Читаємо вголос (Reading Aloud)

Long Ukrainian words can look intimidating. Here is a three-step method: (1) break the word into syllables, (2) find the stressed syllable, (3) read at natural speed. Watch it work with three words. **Українська** (Ukrainian): у-кра-їн-ська — stress on the third syllable, **ї**. **Фотографія** (photograph): фо-то-гра-фі-я — stress on the third **а**. **Відпочинок** (rest): від-по-чи-нок — stress on **и**. Start with the broken form, say each syllable slowly, then speed up until it sounds natural. Breaking into syllables is a learning tool — not how Ukrainians actually speak. The goal is smooth, connected reading.

Now try a short connected text. Every word here comes from A1 vocabulary you have already encountered or is transparently simple:

> **Це Київ. Київ — столиця України. Тут є метро, аптеки, кафе. А це Львів. Львів — гарне місто. Тут є кава і книги.**

Read it aloud. Use falling intonation on each sentence — these are all statements. Pay attention to stress: Ки́їв, столи́ця, Украї́ни, метро́, апте́ки, кафе́, Льві́в, га́рне, мі́сто, ка́ва, кни́ги. Now read it again without looking at the stress marks. Can you remember them? In real Ukrainian text, those marks would not appear.

<!-- INJECT_ACTIVITY: match-stress-pairs -->

Finally, combine everything — stress and intonation together — in a dialogue using greetings from Module 1:

> **Оленка:** Привіт! ↘ *(Hello!)*
> **Тарас:** Привіт! Як справи? ↗ *(Hello! How are you?)*
> **Оленка:** Добре! А у тебе? ↗ *(Good! And you?)*
> **Тарас:** Теж добре! ↘ *(Also good!)*
> **Оленка:** Де кава? ↘ *(Where's the coffee?)*
> **Тарас:** Ось кава. ↘ *(Here's the coffee.)*

Read this with a partner or record yourself. Check: does your voice rise on **Як справи?** and fall on **Де кава?** Play it back and compare. The rising question **Як справи?** should feel different from the falling question **Де кава?** — that difference is intonation at work.

Stress and intonation can feel like a lot to track at first, but native speakers handle both automatically. Every time you hear Ukrainian — in music, podcasts, or conversations — listen for the melody. Notice which syllable is louder, whether the voice rises or falls at the end. Your ear learns faster than your eyes. Read the dialogue above one more time — first slowly, then at natural speed.

## Підсумок — Summary

This module introduced three connected skills. First: **наголос** (stress) is free and mobile — it can fall on any syllable and moves between word forms. Wrong stress changes meaning entirely: **замок** (castle) versus **замок** (lock), **мука** (torment) versus **мука** (flour). There is no shortcut — learn each word's stress individually. Second: **інтонація** (intonation) distinguishes sentence types. Statements fall ↘. Yes/no questions rise ↗. Question-word questions fall ↘. Exclamations fall sharply ↘↘. Third: reading aloud combines both skills — find the stress, apply the melody, build toward natural speed. These are not abstract rules. They are how Ukrainian sounds. Without them, even perfect grammar sounds foreign.

Test yourself with these questions. Що таке наголос? — The syllable you pronounce louder and longer. Чи може наголос змінити значення слова? — Yes: **замок** (castle) versus **замок** (lock). Яка інтонація у реченні «Це кава?» — Rising ↗, because it is a yes/no question. А у реченні «Де кава?» — Falling ↘, because **де** is a question word. Now read aloud: **Це аптека? Так, це аптека. Як гарно!** Did your voice rise on the first sentence, fall on the second, and drop sharply on the third?

You now have the building blocks of Ukrainian sound: letters and sounds (Modules 2–3), special signs (Module 3), and now stress and melody (Module 4). In the next module — **Хто я?** (Who Am I?) — you will use all of these to introduce yourself in Ukrainian. You will say your name, where you are from, and what you do — with correct stress and natural intonation. The sounds become words, the words become sentences, and the sentences become you speaking Ukrainian.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: stress-and-melody
level: a1

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

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
```

---

## Activity Type Reference

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.1 (Module 4/55) — COMPLETE BEGINNER**

The learner is on their FIRST DAYS learning Ukrainian. They:
- Cannot read Ukrainian yet (learning the alphabet)
- Know zero Ukrainian grammar
- Can recognize only a few words (мама, тато, привіт)

**ALL instructions MUST be in English.** The learner cannot read Ukrainian instructions.

**Best activity types for this level:**
- image-to-letter: hear/see → pick the letter
- letter-grid: interactive alphabet practice
- match-up: letter ↔ sound, letter ↔ word
- quiz: in ENGLISH about Ukrainian sounds ('What sound does В make?')
- observe: show patterns in Ukrainian with English prompts
- group-sort: sort letters into vowels/consonants

**DO NOT use:** fill-in with Ukrainian sentences, error-correction, translate (learner can't write Ukrainian yet), cloze, unjumble.


## Quality Rules

1. **Instructions match learner level:**
   - **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
   - **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
   - **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
   - **A2+:** Instructions in Ukrainian.
   - **B1+:** Full Ukrainian, no English.
2. **3-5 options per quiz/fill-in** — enough to prevent guessing, not so many to overwhelm
3. **No duplicate options** — each option in a quiz item must be unique
4. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
5. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
6. **Min 3 pairs for match-up** — to prevent trivial elimination
7. **Explanations for true-false and error-correction** — help the learner understand WHY
8. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp__rag__verify_words` / `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp__rag__search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp__rag__search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp__rag__query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp__rag__search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp__rag__search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp__rag__search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp__rag__search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp__rag__query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp__rag__query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp__rag__search_style_guide` first (it knows calques). Then `mcp__rag__query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp__rag__verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp__rag__query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp__rag__verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp__rag__search_idioms` for Ukrainian expressions, `mcp__rag__search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp__rag__query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp__rag__query_grac` with mode='collocations' to see real-world usage.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 8-15 tool calls per module**, not 50.

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
