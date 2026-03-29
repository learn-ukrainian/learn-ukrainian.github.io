<!-- version: 1.0.0 | updated: 2026-03-27 -->
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
- 'Genitive forms appear ONLY as memorized chunks: у мене, у тебе, у вас are taught
  explicitly. Forms like у нього, у неї may appear in dialogues for exposure but are NOT
  drilled — full genitive paradigm is A2.'
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

After class, two classmates — **Оля** and **Марк** — sit together scrolling through photos on a phone. Оля spots a group picture and asks about Марк's family. This is the most natural way to talk about siblings in Ukrainian: you ask **«У тебе є брати чи сестри?»** (Do you have brothers or sisters?) and answer with **«У мене є...»** (I have...). The little word **чи** (or) connects the two options in the question.

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Оля:</span> У тебе є брати чи сестри? *(Do you have brothers or sisters?)*</div>

<div class="dialogue-line"><span class="speaker">Марк:</span> Так, у мене є два брати і одна сестра. *(Yes, I have two brothers and one sister.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Ого! У мене тільки один брат. *(Wow! I only have one brother.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Як його звати? *(What's his name?)*</div>

<div class="dialogue-line"><span class="speaker">Марк:</span> Коля. А твоя сестра? *(Kolya. And your sister?)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Її звати Даша. *(Her name is Dasha.)*</div>

</div>

Notice two things here. First, **чи** works like "or" inside yes-or-no questions — you'll hear it constantly in Ukrainian conversation. Second, the number "one" changes by gender: **один брат** (masculine) but **одна сестра** (feminine).

Марк swipes to the next photo — a full family picture from a birthday celebration. He turns the screen toward Оля and starts pointing at faces. This is where the structure **«Це моя...»** (This is my...) becomes essential: it's how you introduce people by name and role.

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Марк:</span> Це моя сім'я на фотографії. *(This is my family in the photo.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Класно! Хто це? *(Cool! Who is this?)*</div>

<div class="dialogue-line"><span class="speaker">Марк:</span> Це моя мама Марина. *(This is my mom Maryna.)*</div>

<div class="dialogue-line"><span class="speaker">Марк:</span> Це мій тато Євген. *(This is my dad Yevhen.)*</div>

<div class="dialogue-line"><span class="speaker">Марк:</span> Це моя сестра Катя і мої брати — Іван і Денис. *(This is my sister Katia and my brothers — Ivan and Denys.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> А це твоя бабуся? *(And is this your grandmother?)*</div>

<div class="dialogue-line"><span class="speaker">Марк:</span> Так, її звати Тетяна. *(Yes, her name is Tetiana.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Яка гарна родина! *(What a lovely family!)*</div>

</div>

Оля uses **родина** here, while Марк said **сім'я** earlier — both words mean "family" and both are completely natural. Ukrainians use them interchangeably every day.

Now imagine you need to introduce your own family in a few sentences — at a language exchange, in a message to a Ukrainian friend, or in class. Here is what that sounds like when you combine all the skills from A1.1 so far: self-introduction, city, family members, and possession.

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Оля:</span> Привіт! Мене звати Оля. *(Hi! My name is Olya.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Я з Києва. *(I'm from Kyiv.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Моя мама — вчителька. *(My mom is a teacher.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Її звати Олена. *(Her name is Olena.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Мій тато — інженер. *(My dad is an engineer.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Його звати Петро. *(His name is Petro.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> У мене є один брат. *(I have one brother.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Його звати Коля. *(His name is Kolya.)*</div>

<div class="dialogue-line"><span class="speaker">Оля:</span> Це моя сім'я. *(This is my family.)*</div>

</div>

This is a learnable template: name → city → family members → possession. You can swap in your own details and have a ready-made self-presentation.

## Сім'я (Family Vocabulary)

Ukrainian has two words for "family" — **сім'я** and **родина**. Both are used by native speakers; neither is more correct than the other. A Grade 1 textbook by Захарійчук uses both in the same lesson: the section title says «Я і моя **родина**» while the poem inside says «В мене дружна є **сім'я**». Notice the apostrophe in **сім'я** — it separates the **м** from the **я** and is a feature of Ukrainian spelling you'll see often.

The core nuclear family words are: **мама** (mother; the more formal/literary word is **мати**), **тато** (father; formally **батько**), **брат** (brother), **сестра** (sister), **син** (son), **дочка** (daughter; **донька** is a warmer, colloquial variant). You already know how to present them: **Це мій брат. Це моя сестра. Це мій тато.**

Extended family: **бабуся** (grandmother; colloquially also **баба**), **дідусь** (grandfather; colloquially **дід**), **тітка** (aunt), **дядько** (uncle). One important cultural note: Ukrainian has no single word for "grandparents" — you always say **бабуся і дідусь** as a pair. The Захарійчук Grade 1 poem captures the affectionate diminutive forms perfectly: «Люба мама і татусь, / Бабця Віра і дідусь» — here **татусь** is a warm form of **тато** and **бабця** is a variant of **бабуся**.

A few more useful words: **батьки** (parents) is always plural — say **мої батьки**, not *мої мама і тато*. **Дружина** means "wife." **Чоловік** means both "husband" and "man" — context tells you which: **Це мій чоловік** (This is my husband) versus **Там стоїть чоловік** (A man is standing there). And remember: **дочка** is the more common everyday form, while **донька** carries a warm, affectionate tone.

<!-- INJECT_ACTIVITY: match-family-vocab -->

## У мене є (I Have)

Ukrainian expresses possession completely differently from English. There is no verb meaning "to have" the way English uses "have." Instead, Ukrainian says literally "At me there-is" — **У мене є брат** (I have a brother). Break this structure down: **у** means "at" or "by" (indicating where the possession exists), **мене** is the form of "me" used after **у** (this is a frozen chunk — don't worry about why it changes), and **є** means "there is" or "there are." The word **є** is the present-tense form of "to be" — and it stays the same for all persons, singular and plural. Three forms to learn as ready-made chunks: **У мене є** (I have), **У тебе є** (you have — informal), **У вас є** (you have — formal or plural). Examples: **У мене є одна сестра.** **У тебе є брат?** **У вас є діти?**

Asking questions is simple. In Ukrainian, you turn a statement into a question just by raising your intonation at the end — no word order changes needed. **У тебе є сестра? ↗** The answers are straightforward: **Так, у мене є сестра.** / **Так, у мене є два брати.** / **Ні.** / **Ні, у мене тільки один брат.** The word **тільки** (only) is very useful in real conversation. You'll hear it all the time: **У мене тільки одна сестра.** **У мене тільки один брат.**

You might wonder: how do you say "I don't have"? The word **немає** means "there is not," but it requires a grammatical form called the genitive case — which changes the ending of the noun after it. That belongs to A2. For now, the simplest and most natural way to say "no" is just **Ні** or **Ні, у мене тільки...** Native speakers use these short answers in casual conversation constantly.

A quick preview of numbers with family members. **Один** and **одна** change to match gender: **один брат** (masculine), **одна сестра** (feminine). The same pattern applies to "two": **два** and **дві** — **два брати** (masculine), **дві сестри** (feminine). You don't need to memorize a rule — just notice the pattern as it appears: **У мене є два брати і дві сестри.**

<!-- INJECT_ACTIVITY: quiz-u-tebe-ye -->

## Мій, моя, моє (Possessive Pronouns)

The core rule: possessive pronouns match the gender of the thing you possess — not the gender of the speaker. A man still says **моя сестра** (my sister), because **сестра** is a feminine noun. Ukrainian Grade 3 textbooks by Вашуленко teach this as the gender test for nouns: if you can say **мій** before it, it's masculine; **моя** — feminine; **моє** — neuter. Four forms to know: **мій** (masculine) — **мій брат, мій тато, мій дядько**; **моя** (feminine) — **моя сестра, моя мама, моя бабуся**; **моє** (neuter) — **моє місто, моє фото**; **мої** (plural) — **мої батьки, мої брати, мої сестри**. The ending mirrors the noun's gender, not who is speaking.

**Твій, твоя, твоє, твої** work exactly the same way — they mean "your" (informal). **Це твій брат?** **Де твоя мама?** **Це твоє фото?** **Це твої батьки?** Use these forms with people you address as **ти** — friends, family, children. Here's a natural mini-exchange: **— Це мій тато. — Це твій тато? — Так, це мій тато.** / **— Ні, це не мій тато, це мій дядько.**

**Його** (his) and **її** (her) are different — they never change form. **Це його мама. Це його тато. Це його сестра.** **Це її брат. Це її місто.** No matter what gender the noun is, **його** and **її** stay exactly the same. Compare this to **мій/моя/моє**, which always change to match.

The forms **наш** (our), **ваш** (your — formal/plural), and **їхній** (their) belong to A2, where you'll learn the full paradigm with case changes. At A1, use only **мій/твій/його/її** in the nominative.

<!-- INJECT_ACTIVITY: fill-in-possessives -->

<!-- INJECT_ACTIVITY: fill-in-family-dialogue -->

## Підсумок — Summary

**Перевір себе (Self-check):**

- Назви 5 членів сім'ї українською. *(мама, тато, брат, сестра, бабуся...)*
- Як сказати "I have a sister" по-українськи? *(У мене є сестра.)*
- Яка різниця між **мій** і **моя**? *(мій = masculine noun, моя = feminine noun)*
- Як сказати "his" і "her"? Чи вони змінюються? *(його, її — не змінюються)*
- Познайом свою сім'ю у 4–5 реченнях. Зразок:

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Ти:</span> Привіт! Мене звати Карен. *(Hi! My name is Karen.)*</div>

<div class="dialogue-line"><span class="speaker">Ти:</span> У мене є мама, тато і один брат. *(I have a mom, dad, and one brother.)*</div>

<div class="dialogue-line"><span class="speaker">Ти:</span> Моя мама — лікарка. *(My mom is a doctor.)*</div>

<div class="dialogue-line"><span class="speaker">Ти:</span> Мій брат — студент. *(My brother is a student.)*</div>

<div class="dialogue-line"><span class="speaker">Ти:</span> Це моя сім'я. *(This is my family.)*</div>

</div>

Use this as a template — swap in your real family, your real names, your real details. This is yours now.

**Що далі?** In Module 7 (Checkpoint — First Contact), you will combine everything from A1.1: alphabet, sounds, self-introduction, and family — in a full communicative checkpoint.

**Deterministic word count: 1640 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 95 words | Not found: 17 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Євген — NOT IN VESUM
  ✗ Іван — NOT IN VESUM
  ✗ Вашуленко — NOT IN VESUM
  ✗ Даша — NOT IN VESUM
  ✗ Денис — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Карен — NOT IN VESUM
  ✗ Катя — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Коля — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Марк' — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Оля — NOT IN VESUM
  ✗ Петро — NOT IN VESUM
  ✗ Тетяна — NOT IN VESUM
  ✗ українськи — NOT IN VESUM

All 95 other words are confirmed to exist in VESUM.

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
