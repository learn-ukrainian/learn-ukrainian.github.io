# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 6: My Family (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-006
level: A1
sequence: 6
slug: my-family
version: '1.2'
title: My Family
subtitle: У мене є брат — Showing photos
focus: vocabulary
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Name close family members in Ukrainian
- Use "У мене є" to say what you have (memorized chunk)
- Use possessive pronouns мій/моя/моє in nominative only
- Introduce family members using Це + possessives
content_outline:
- section: Діалоги (Dialogues)
  words: 400
  points:
  - 'Dialogue 1 — Showing phone photos (Anna Ep6-7): — У тебе є брати чи сестри? —
    Так, у мене є два брати і одна сестра. — Ого! У мене тільки один брат. Як його
    звати? — Коля.'
  - 'Dialogue 2 — Family in a photo (Anna Ep7): — Це моя сім''я на фотографії. Класно!
    Хто це? — Це моя мама Марина. Це мій тато Євген. Це моя сестра Катя і мої брати
    — Іван і Денис. — А це твоя бабуся? — Так, її звати Тетяна.'
  - 'Dialogue 3 — Connected speech (Anna Ep10 review pattern): Привіт! Мене звати...
    Моя мама — вчителька. Мій тато — інженер. У мене є один брат. Combining all A1.1
    skills.'
- section: Сім'я (Family Vocabulary)
  words: 200
  points:
  - 'Anna Ep6: Two words for family: сім''я and родина (both used). Core: мама/мати,
    тато/батько, брат, сестра, син, дочка/донька. Extended: бабуся/баба, дідусь/дід,
    тітка, дядько. Note: Ukrainian has NO single word for ''grandparents'' — always
    say бабуся і дідусь.'
- section: У мене є (I have)
  words: 250
  points:
  - 'Anna Ep6 pattern: Ukrainian doesn''t say ''I have'' with a verb. Instead: ''At
    me there-is'' — У мене є брат. For A1, teach only: у мене є, у тебе є (informal),
    у вас є (formal). Other forms (у нього, у неї, у нас, у них) use genitive pronouns
    which are A2 grammar — introduce them gradually through dialogues as memorized
    phrases, not as a paradigm table.'
  - 'Questions with rising intonation: У тебе є сестра? ↗ Negative: Defer ''У мене
    немає'' to A2 where genitive is taught. For A1, learners answer: Ні. / Ні, у мене
    тільки один брат. This avoids the pedagogical trap of немає + nominative (*немає
    брат).'
  - 'Numbers preview (Anna Ep6): один/одна changes by gender: один брат, одна сестра.
    два/дві: два брати, дві сестри.'
- section: Мій, моя, моє (Possessive Pronouns)
  words: 200
  points:
  - 'Anna Ep7: Possessives match the gender of the thing possessed. мій брат (m),
    моя сестра (f), моє місто (n), мої батьки (pl). твій/твоя/твоє/твої (your, informal).
    його (his — doesn''t change), її (her — doesn''t change). State Standard note:
    full paradigm (наш, ваш, їхній) is A2. At A1: мій/твій/його/її in nominative only.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Self-check: Name 5 family members. Say ''I have a sister.'' What''s the difference
    between мій and моя? Introduce your family in 4-5 sentences.'
vocabulary_hints:
  required:
  - сім'я (family) — apostrophe word
  - мама (mother)
  - тато (father)
  - брат (brother)
  - сестра (sister)
  - бабуся (grandmother)
  - дідусь (grandfather)
  - мій, моя, моє, мої (my — m/f/n/pl)
  - твій, твоя, твоє (your — m/f/n, informal)
  - у мене є (I have)
  - у тебе є (you have, informal)
  recommended:
  - батьки (parents)
  - дядько (uncle)
  - тітка (aunt)
  - дочка (daughter)
  - син (son)
  - дружина (wife)
  - чоловік (man / husband)
  - його (his — doesn't change)
  - її (her — doesn't change)
  - один, одна (one — m/f)
  - два, дві (two — m/f)
  - чи (or — in questions)
  - тільки (only)
activity_hints:
- type: quiz
  focus: 'У тебе є...? — answer Так/Ні. Use ONLY the chunk ''у тебе є''. Example questions:
    ''У тебе є брат?'', ''У тебе є сестра?'', ''У тебе є бабуся?'' Answer options:
    ''Так, у мене є брат.'' / ''Ні.'' / ''Так, у мене є два брати.'' Do NOT use genitive
    names (no ''У Оксани є'').'
  items: 6
- type: fill-in
  focus: 'Choose correct possessive pronoun. EXACT pattern: ''Це {___} мама.'' → моя
    | ''Де {___} тато?'' → твій | ''Ось {___} батьки.'' → мої All nominative case.
    Options: мій/моя/моє/мої or твій/твоя/твоє/твої.'
  items: 8
- type: match-up
  focus: 'Match English family words to Ukrainian. Pairs: parents↔батьки, uncle↔дядько,
    aunt↔тітка, grandfather↔дідусь, grandmother↔бабуся, brother↔брат, sister↔сестра,
    mother and father↔мама і тато.'
  items: 8
- type: fill-in
  focus: 'Complete a family introduction dialogue with blanks. Pattern: ''— Привіт!
    Це {твій} брат?'' / ''— Так, це мій брат. Ось мій {тато}.'' Options per blank:
    family members or possessives. NO genitive forms.'
  items: 4
connects_to:
- a1-007 (Checkpoint — First Contact)
prerequisites:
- a1-005 (Who Am I?)
grammar:
- У мене є / у тебе є / у вас є (memorized chunks for possession)
- Possessive pronouns мій/моя/моє/мої, твій/твоя/твоє — nominative is the focus
- 'Genitive ALLOWED ONLY as memorized chunks in exercises: у тебе, у мене, у нього,
  у неї — do NOT teach genitive paradigm, just teach these as fixed phrases'
- 'Gender agreement preview (possessive + noun): мій брат, моя сестра'
- Numbers один/одна, два/дві with family members
- 'Family relationship descriptions: use Це + nominative (Це мій брат), NOT genitive
  constructions (avoid: мама мого тата). Describe relationships through simple sentences:
  Мій тато. Його мама — моя бабуся.'
- 'Negation: Ні + simple response (NOT У мене немає — deferred to A2)'
register: розмовний
references:
- title: ULP Season 1, Episode 6 — Family + I Have
  url: https://www.ukrainianlessons.com/episode6/
  notes: У мене є with family. Один/одна gender.
- title: ULP Season 1, Episode 7 — Possessive Pronouns
  url: https://www.ukrainianlessons.com/episode7/
  notes: мій/моя/моє paradigm. Це моя мама.
- title: ULP Season 1, Episode 10 — Review
  url: https://www.ukrainianlessons.com/episode10/
  notes: 'Connected self-introduction: Я і моя сім''я.'

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

Оля and Максим sit in a cafe. Maksym pulls out his phone — he has new photos from a family gathering. Showing phone photos to friends is universal, and in Ukraine it often turns into a full family introduction.

<div class="dialogue">


**Оля:** У тебе є брати чи сестри? *(Do you have brothers or sisters?)*


**Максим:** Так, у мене є два брати і одна сестра. *(Yes, I have two brothers and one sister.)*


**Оля:** Ого! У мене тільки один брат. *(Wow! I only have one brother.)*


**Максим:** Як його звати? *(What's his name?)*


**Оля:** Коля. *(Kolya.)*


</div>



A few words to notice: **чи** (or) appears in yes/no questions when offering a choice. **Тільки** (only) is a useful word — it softens a statement. **Як його звати?** literally means "How is he called?" — you already know **Як тебе звати?** from Module 5, and **його** (his/him) simply replaces **тебе** (you).

Maksym swipes to a group photo. Ukrainians often keep extended family photos on their phones — family ties run deep.

<div class="dialogue">


**Максим:** Це моя сім'я на фотографії. *(This is my family in a photo.)*


**Оля:** Класно! Хто це? *(Cool! Who is this?)*


**Максим:** Це моя мама Марина. *(This is my mom Maryna.)*


**Максим:** Це мій тато Євген. *(This is my dad Yevhen.)*


**Максим:** Це моя сестра Катя. *(This is my sister Katia.)*


**Максим:** І мої брати — Іван і Денис. *(And my brothers — Ivan and Denys.)*


**Оля:** А це твоя бабуся? *(And is this your grandmother?)*


**Максим:** Так, її звати Тетяна. *(Yes, her name is Tetiana.)*


</div>



**Хто це?** (Who is this?) is your go-to question when pointing at someone in a photo. **Її звати** (her name is) works exactly like **його звати** — just swap the pronoun.

Notice the pattern **Це** + possessive + noun: **Це мій тато**, **Це моя мама**, **Це мої брати**. Ukrainian uses **Це** (this is) the same way English uses "This is" for introductions. Already you can see that **мій** and **моя** are different — this is because they match the gender of the person you are introducing.

Now Оля introduces her own family — a connected monologue combining everything from Modules 1–5 with new family vocabulary:

<div class="dialogue">


**Оля:** Привіт! Мене звати Оля. *(Hi! My name is Olya.)*


**Оля:** Моя мама — вчителька. *(My mom is a teacher.)*


**Оля:** Мій тато — інженер. *(My dad is an engineer.)*


**Оля:** У мене є один брат. *(I have one brother.)*


**Оля:** Його звати Коля. *(His name is Kolya.)*


**Оля:** Моя бабуся Ганна живе в Києві. *(My grandmother Hanna lives in Kyiv.)*


**Оля:** У мене дружна сім'я. *(I have a close-knit family.)*


</div>



Three key patterns carry this entire module. First: **У мене є** + family member for saying what family you have. Second: **Це мій/моя** + person for introducing someone. Third: **Як його/її звати?** → **Його/Її звати...** for asking and giving names. Master these three and you can talk about any family.

## Сім'я (Family Vocabulary)

Ukrainian has two words for family: **сім'я** and **родина**. Both are common, both are correct, and you will hear them interchangeably. A Grade 1 textbook poem by Марія Братко captures both:

> Поділюся з вами я: В мене дружна є сім'я.

Notice the apostrophe in **сім'я** — this is the same apostrophe you learned in Module 4. It separates the **м** from the **я**, keeping them as distinct sounds. **Дружна** (close-knit, friendly) is a word Ukrainians often use to describe their families.

Here are the core family members you need. Each noun has a grammatical gender — this matters for possessive pronouns later:

| Ukrainian | English | Gender |
|-----------|---------|--------|
| **мама** / **мати** | mother | f |
| **тато** / **батько** | father | m |
| **брат** | brother | m |
| **сестра** | sister | f |
| **син** | son | m |
| **дочка** / **донька** | daughter | f |

**Мама** is everyday speech; **мати** is formal or literary. **Тато** is everyday; **батько** is formal. The plural **батьки** (parents) is one of the first words where the plural meaning differs from the singular — it does not mean "fathers."

Extended family members: **бабуся** / **баба** (grandmother), **дідусь** / **дід** (grandfather), **тітка** (aunt), **дядько** (uncle), **дружина** (wife), and **чоловік** (husband). A cultural note: Ukrainian has no single word for "grandparents" — you always say **бабуся і дідусь**. Diminutive forms are very common in families: **татусь** (daddy), **матуся** (mommy), **бабця** (granny). The word **дідусь** is already a diminutive of **дід**. A Grade 2 textbook has a fun unscrambling exercise with family words: "маам, отат, дусьід, басябу" — can you figure them out? мама, тато, дідусь, бабуся.

<!-- INJECT_ACTIVITY: match-family-vocab -->

## У мене є (I have)

While Ukrainian does have a verb for "to have" (*мати*), everyday speech prefers a different construction. It is literally "At me there-is": **У мене є брат** — "I have a brother." This is completely different from English "I have," and it is one of the first structures that shows you how Ukrainian thinks differently.

For A1, you need only three forms:

| Ukrainian | English |
|-----------|---------|
| **У мене є** | I have |
| **У тебе є** | You have (informal) |
| **У вас є** | You have (formal) |

Examples with family: **У мене є сестра** (I have a sister). **У тебе є брат?** (Do you have a brother?). **У вас є діти?** (Do you have children?). Other pronoun forms like **у нього є** (he has) and **у неї є** (she has) are also useful memorized phrases — the full genitive pronoun system comes in A2. For now, just recognize them when you hear them.

Questions use rising intonation only — no word-order change needed: **У тебе є сестра?** ↗ Compare English "Do you have...?" which requires a helper verb. Ukrainian is simpler here. Short answers: **Так, у мене є сестра.** Or simply: **Ні.** For now, if you want to say you don't have someone, just say **Ні** or offer a correction: **Ні, у мене тільки один брат.** We will learn how to say "I don't have" later.

<!-- INJECT_ACTIVITY: quiz-u-tebe-ye -->

Numbers make a brief appearance here, because family talk naturally involves counting. Two numbers show gender agreement: **один брат** (one brother, masculine) vs. **одна сестра** (one sister, feminine). **Два брати** (two brothers, masculine) vs. **дві сестри** (two sisters, feminine). **Один/одна** and **два/дві** change by gender — this is your first encounter with number-gender agreement. Keep it to just these two numbers for now. Examples: **У мене є один брат і дві сестри.** **У мене є одна бабуся і два дідусі.**

:::tip Pattern Summary
Four sentences that show the full **У мене є** pattern in action:

1. **У мене є два брати.** *(I have two brothers.)*
2. **У тебе є сестра?** — **Так, у мене є одна сестра.** *(Do you have a sister? — Yes, I have one sister.)*
3. **У вас є діти?** — **Так, у мене є син і дочка.** *(Do you have children? — Yes, I have a son and a daughter.)*
4. **У мене є бабуся. Її звати Ганна.** *(I have a grandmother. Her name is Hanna.)*

Notice how **У мене є** connects naturally to family introductions from the dialogues.
:::

## Мій, моя, моє (Possessive Pronouns)

Possessives in Ukrainian match the gender of the **thing possessed**, not the owner. This is different from English "my," which never changes form.

| | Masculine | Feminine | Neuter | Plural |
|---|-----------|----------|--------|--------|
| my | **мій** | **моя** | **моє** | **мої** |

**Мій брат** (my brother — masculine noun). **Моя сестра** (my sister — feminine noun). **Моє місто** (my city — neuter noun). **Мої батьки** (my parents — plural noun). The key: look at the noun's gender, not who is speaking. A man says **моя сестра** (not *мій сестра) because **сестра** is feminine. A woman says **мій брат** because **брат** is masculine. The speaker's gender is irrelevant.

**Твій/твоя/твоє/твої** (your, informal) follows the same pattern: **твій тато** (your dad, masculine), **твоя мама** (your mom, feminine), **твоє ім'я** (your name, neuter), **твої друзі** (your friends, plural). Third-person possessives are even easier: **його** (his) and **її** (her) never change form regardless of the noun. **Його мама, його тато, його місто** — always **його**. **Її брат, її сестра, її місто** — always **її**. This makes **його** and **її** the simplest possessives in Ukrainian.

The **Це** + possessive + noun pattern is the workhorse for family introductions: **Це моя мама. Це мій тато. Це моя сестра. Це мої брати.** We will learn other possessives like **наш** (our) and **ваш** (your, formal) later — for now, **мій/твій/його/її** covers everything you need for simple introductions. A quick exchange shows the contrast between **мій** and **твій**:

<div class="dialogue">


**Максим:** Це мій тато. *(This is my dad.)*


**Оля:** А це твій брат? *(And is this your brother?)*


</div>



<!-- INJECT_ACTIVITY: fill-in-possessives -->

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

## Підсумок — Summary

In this module you learned to talk about your family in Ukrainian. Three key patterns carry your family conversations: (1) **У мене є** + noun for saying what family you have, (2) **Це** + **мій/моя/моє** for introducing family members, and (3) **Як його/її звати?** for asking and giving names. You can now name **мама**, **тато**, **брат**, **сестра**, **бабуся**, **дідусь**, **дядько**, **тітка**, **син**, **дочка**, and **батьки**. You know that possessives change by gender — **мій брат** but **моя сестра** — and that **його** and **її** never change form.

Test yourself:

1. Name 5 family members in Ukrainian.
2. Say "I have a sister." — **У мене є сестра.**
3. What is the difference between **мій** and **моя**? (Gender of the noun!)
4. Introduce your family in 4–5 sentences using **Це мій/моя...** and **У мене є...**
5. Ask someone "Do you have a brother?" — **У тебе є брат?**

**Deterministic word count: 1529 words** (calculated by pipeline, do NOT estimate manually)

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

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

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

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

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

Verified: 84 words | Not found: 13 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Євген — NOT IN VESUM
  ✗ Іван — NOT IN VESUM
  ✗ Ганна — NOT IN VESUM
  ✗ Денис — NOT IN VESUM
  ✗ Катя — NOT IN VESUM
  ✗ Коля — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оля — NOT IN VESUM
  ✗ Тетяна — NOT IN VESUM
  ✗ басябу — NOT IN VESUM
  ✗ дусьід — NOT IN VESUM
  ✗ маам — NOT IN VESUM
  ✗ отат — NOT IN VESUM

All 84 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `rag_verify_lemma` — full declension/conjugation for a lemma
- `rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `rag_search_literary` — verify literary references against primary sources
- `rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
