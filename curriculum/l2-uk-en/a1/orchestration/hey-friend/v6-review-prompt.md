<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 42: Hey, Friend! (A1, A1.7 [Communication])
**Writer:** Claude
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-042
level: A1
sequence: 42
slug: hey-friend
version: '1.2'
title: Hey, Friend!
subtitle: Олено! Тарасе! Друже! Мамо! — calling people by name
focus: grammar
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Form vocative case for common names and family words (Олено! Тарасе! Мамо!)
- Use vocative in greetings and direct address (Привіт, Андрію!)
- Recognize vocative endings for masculine (-е, -у/-ю) and feminine (-о, -ю, -є) nouns
- Address people naturally using vocative in everyday situations
dialogue_situations:
- setting: 'At a busy birthday party — calling people across the room by name: Олено!
    Тарасе! Друже! Мамо! Бабусю! Дідусю! Each person is doing something different
    (dancing, eating, talking).'
  speakers:
  - Іменинник (birthday person)
  - Друзі
  motivation: 'Vocative: Олена→Олено, Тарас→Тарасе, мама→мамо, бабуся→бабусю'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting a friend: — Олено, привіт! Як справи? — Добре, дякую, Тарасе!
    А в тебе? — Теж добре. Олено, ти знаєш мого брата? — Ні. — Андрію, ходи сюди!
    Це Олена. Олено, це Андрій. Vocative forms: Олено (Олена), Тарасе (Тарас), Андрію
    (Андрій).'
  - 'Dialogue 2 — At home: — Мамо, де мій телефон? — На столі, синку. — Тату, а де
    ключі? — У кишені, дочко. — Бабусю, ми йдемо! — Добре, будьте обережні! Family
    vocatives: мамо, тату, синку, дочко, бабусю.'
- section: Кличний відмінок (The Vocative Case)
  words: 300
  points:
  - 'Ukrainian has a special case for calling someone — кличний відмінок. In English
    you just say the name: ''Olena, come here!'' In Ukrainian the name CHANGES: Олена
    → Олено, ходи сюди! This is not optional — Ukrainians always use vocative when
    addressing someone. Grade 4 helper word: Кл. (!) — the exclamation mark reminds
    you: you''re calling someone, so the ending changes.'
  - 'Why vocative matters: Олена прийшла. (Olena came.) — nominative, talking ABOUT
    her. Олено, ходи сюди! (Olena, come here!) — vocative, talking TO her. Using nominative
    to address someone sounds unnatural in Ukrainian. It''s like saying ''Hey, him!''
    instead of ''Hey, you!'' in English.'
- section: Закінчення кличного (Vocative Endings)
  words: 300
  points:
  - 'Feminine names and nouns (-а → -о): Олена → Олено, мама → мамо, сестра → сестро,
    Оксана → Оксано, подруга → подруго, бабуся → бабусю (-ся → -сю). Names on -ка:
    Наталка → Наталко, Ірка → Ірко. Names on -ія: Марія → Маріє (not Маріо!). Names
    on -а (long): Катерина → Катерино, Тетяна → Тетяно.'
  - 'Masculine names and nouns: Hard consonant → -е: Тарас → Тарасе, Іван → Іване,
    брат → брате, пан → пане. Soft consonant / -й → -ю: Андрій → Андрію, дідусь →
    дідусю, вчитель → вчителю. Special: друг → друже (г → ж), козак → козаче (к →
    ч). Тато → тату (exceptional -у ending, memorize).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Vocative quick reference: | Pattern | Nominative → Vocative | Example | | Feminine
    -а | -а → -о | Олена → Олено, мама → мамо | | Feminine -ія | -ія → -іє | Марія
    → Маріє | | Feminine -ся | -ся → -сю | бабуся → бабусю | | Masculine hard | +
    -е | Тарас → Тарасе, брат → брате | | Masculine -й/soft | + -ю | Андрій → Андрію,
    вчитель → вчителю | | Special (г, к) | г→ж, к→ч + -е | друг → друже | Self-check:
    How do you call your family? мама → ? тато → ? брат → ?'
vocabulary_hints:
  required:
  - друг (friend, m)
  - подруга (friend, f)
  - брат (brother, m)
  - сестра (sister, f)
  - пан (Mr., m)
  - пані (Mrs./Ms., f)
  recommended:
  - синку (son — vocative, from син)
  - дочко (daughter — vocative, from дочка)
  - козак (Cossack, m)
  - вчитель (teacher, m)
  - бабуся (grandmother, f)
  - дідусь (grandfather, m)
activity_hints:
- type: fill-in
  focus: 'Write vocative: Олена → Олено, Тарас → Тарасе, мама → мамо'
  items:
  - Олена → {Олено}
  - Тарас → {Тарасе}
  - мама → {мамо}
  - Іван → {Іване}
  - сестра → {сестро}
  - Андрій → {Андрію}
  - подруга → {подруго}
  - брат → {брате}
  - Марія → {Маріє}
  - бабуся → {бабусю}
- type: quiz
  focus: 'Choose correct vocative: (Олена / Олено / Оленю), привіт!'
  items:
  - question: ___, привіт!
    options:
    - Олено
    - Олена
    - Оленю
  - question: Як справи, ___?
    options:
    - Тарасе
    - Тарас
    - Тарасу
  - question: Дякую, ___!
    options:
    - мамо
    - мама
    - маме
  - question: Ходи сюди, ___!
    options:
    - Іване
    - Іван
    - Івану
  - question: Будь обережний, ___!
    options:
    - синку
    - синок
    - синке
  - question: Що ти робиш, ___?
    options:
    - брате
    - брат
    - брату
  - question: Добрий день, ___!
    options:
    - пане
    - пан
    - пану
  - question: Привіт, ___!
    options:
    - Андрію
    - Андрій
    - Андріє
- type: group-sort
  focus: 'Sort vocative endings: -о (feminine) vs -е (masculine hard) vs -ю (masculine
    soft)'
  groups:
  - name: -о (feminine)
    items:
    - Олено
    - мамо
    - сестро
  - name: -е (masculine hard)
    items:
    - Тарасе
    - Іване
    - брате
    - пане
  - name: -ю (masculine soft)
    items:
    - Андрію
    - дідусю
    - вчителю
- type: fill-in
  focus: 'Complete dialogue: ___, привіт! Як справи? (name → vocative)'
  items:
  - — {Олено|Олена}, привіт! Як справи?
  - — Добре, дякую, {Тарасе|Тарас}!
  - — {Мамо|Мама}, де мій телефон?
  - — На столі, {синку|синок}.
  - — {Бабусю|Бабуся}, ми йдемо!
  - — Добре, до побачення, {Андрію|Андрій}!
connects_to:
- a1-043 (Please Do This)
prerequisites:
- a1-041 (Checkpoint — Food and Shopping)
grammar:
- 'Vocative case (кличний відмінок): special endings for direct address'
- Feminine -а → -о (Олена → Олено), -ія → -іє (Марія → Маріє)
- Masculine hard → -е (Тарас → Тарасе), soft/-й → -ю (Андрій → Андрію)
- 'Consonant alternation: друг → друже (г → ж)'
register: розмовний
references:
- title: State Standard 2024, §4.2.3.4
  notes: 'Vocative case — address forms. A1 scope: common patterns only.'
- title: 'Grade 4 textbook: Кличний відмінок (Заболотний)'
  notes: Helper word Кл. (!). Feminine -а→-о, masculine hard→-е, soft→-ю.

</plan_content>

## Generated Content

<generated_module_content>
## Діало́ги (Dialogues)
It's Taras's birthday — **Тара́су вісімна́дцять ро́кі́в** (Taras is eighteen) — and everyone is at the party. He spots friends across the room and calls them over. Listen to how every name changes when someone is called directly.
> — **Тара́с:** Оле́но, приві́т! Як спра́ви? *(Olena, hi! How are you?)*
> — **Оле́на:** До́бре, дякую, Тара́се! А в тебе́? *(Good, thanks, Taras! And you?)*
> — **Тарас:** Теж добре! Олено, ти зна́єш мого бра́та? *(Also good! Olena, do you know my brother?)*
> — **Олена:** Ні. *(No.)*
> — **Тарас:** Андрію, ходи́ сюди́! Це Олена. *(Andrii, come here! This is Olena.)*
> — **Тарас:** Олено, це Андрі́й. *(Olena, this is Andrii.)*
> — **Олена:** Привіт, Андрію! *(Hi, Andrii!)*
> — **Андрій:** Привіт! Ра́дий ба́чити! *(Hi! Glad to see you!)*

Notice the names: **Олена** became **Олено**, **Тарас** became **Тарасе**, **Андрій** became **Андрію**. Every single time someone was addressed directly, the name changed its ending.
Now the scene shifts. A family is getting ready to leave the house — everyone is busy, everyone is calling everyone else.
> — **Марко́:** Ма́мо, де мій телефо́н? *(Mom, where's my phone?)*
> — **Ма́ма:** На столі́, синку́. *(On the table, son.)*
> — **Оля:** Тату́, а де ключі́? *(Dad, where are the keys?)*
> — **Та́то:** У кише́ні, до́чко. *(In the pocket, daughter.)*
> — **Оля:** Бабу́сю, ми йдемо́! *(Grandma, we're going!)*
> — **Бабу́ся:** Добре, бу́дьте обере́жні! *(Okay, be careful!)*
> — **Оля:** Діду́сю, до поба́чення! *(Grandpa, goodbye!)*

Family vocatives here: **мама** → **мамо**, **тато** → **тату**, **сино́к** → **синку**, **дочка́** → **дочко**, **бабуся** → **бабусю**, **діду́сь** → **дідусю**. Every name and family word changed when someone was spoken to directly.
Notice how every name CHANGED. **Олена** became **Олено**. **Тарас** became **Тарасе**. **Мама** became **мамо**. This is **кли́чний відмі́нок** (the vocative case) — the "calling case." The next two sections explain exactly how the pattern works.
## Кличний відмінок (The Vocative Case)
Ukrainian has seven grammatical cases, and one of them — **кличний відмінок** (the vocative case) — exists specifically for calling someone or addressing them directly. In English, you just say the name as-is: "Olena, come here!" In Ukrainian, the name's ending changes: **Олена** → **Олено, ходи сюди!** This is not a formal or old-fashioned feature. It is everyday, mandatory speech. Every Ukrainian speaker uses it constantly — in texts, at home, with friends, with strangers. Ukrainian Grade 4 grammar uses a helpful shorthand: **Кл. (!)** — the exclamation mark is your memory hook. You're calling someone, so the ending changes.
Here is the core distinction. Compare these two sentences:
- **Олена прийшла́.** *(Olena arrived.)* — nominative case, talking ABOUT her
- **Олено, ходи сюди!** *(Olena, come here!)* — vocative case, talking TO her
In the first sentence, **Олена** is the subject — you are describing what she did. In the second, **Олено** is being addressed — you are speaking directly to her. Using the nominative form to address someone in Ukrainian sounds wrong. It is roughly like saying "Hey, him!" instead of "Hey, you!" in English. Ukrainians immediately notice if you skip the vocative — it marks you as a non-native speaker.
The vocative is alive and vibrant in modern Ukrainian. You hear it everywhere: **Слу́хай, Тарасе!** (Listen, Taras!), **Ви́бачте, па́не!** (Excuse me, sir!), **Дякую, мамо!** (Thanks, Mom!). In songs, in text messages, in street conversations — the vocative is one of the ways Ukrainian encodes human connection directly into grammar. Every time you address someone, the language itself changes shape to acknowledge that relationship.
Go back to the dialogues above and look at every vocative pair: **Олена** → **Олено**, **Тарас** → **Тарасе**, **Андрій** → **Андрію**, **мама** → **мамо**, **тато** → **тату**, **бабуся** → **бабусю**, **синок** → **синку**, **дочка** → **дочко**. Each speaker used the correct form automatically — that natural, effortless use is the goal. The patterns below will show you exactly how to form it.
<!-- INJECT_ACTIVITY: quiz-vocative -->
## Закі́нчення кли́чного (Vocative Endings)
### Feminine: -а → -о
The most common pattern. Feminine names and nouns ending in **-а** change to **-о** in the vocative (hard group):
- **Олена** → **Олено**
- **мама** → **мамо**
- **сестра́** → **се́стро** *(sister)*
- **Окса́на** → **Окса́но**
- **по́друга** → **по́друго** *(female friend)*
Names ending in **-ка** follow the same rule: **Ната́лка** → **Ната́лко**, **Ірка** → **Ірко**. Long names ending in **-ина/-іна** also take **-о**: **Катери́на** → **Катери́но**, **Тетя́на** → **Тетя́но**. The rule is simple: if the name ends in **-а** and the stem is hard, replace **-а** with **-о**.
### Feminine exceptions: soft and mixed groups
Names ending in **-і́я** do NOT become **-іо**. They become **-і́є**: **Марі́я** → **Марі́є**, **Софія** → **Софіє**. Diminutive names with **-уся́/-юся** take **-ю**: **бабуся** → **бабусю** *(grandma)*, **Настуся** → **Настусю**. As Avramenko's Grade 6 textbook notes, forms like **На́сте** and **Катре** also exist, but **бабусю** and **Настусю** are the standard affectionate forms you will use most. Female patronymics ending in **-івна** follow **-о**: **Іва́нівна** → **Іва́нівно**.
### Masculine: hard consonant → -е
Masculine names and nouns with a hard consonant at the end add **-е**:
- **Тарас** → **Тарасе**
- **Іва́н** → **Іва́не**
- **брат** → **бра́те** *(brother)*
- **пан** → **пане** *(Mr./sir)*
Full name address follows the same pattern. From Litvinova Grade 6: **пан Євге́н** → **пане Євге́не**, **Іван Ві́кторович** → **Іване Ві́кторовичу**. Masculine patronymics in **-ович** take **-у**: **Іва́нович** → **Іва́новичу**. Note: **па́ні** (Mrs./Ms.) is невідмі́нюване — it does not change in any case, including vocative. You simply say **пані Оксано!** where **пані** stays the same and only the name takes the vocative ending.
### Masculine: soft consonant / -й → -ю
Masculine names ending in a soft consonant or **-й** add **-ю**:
- **Андрій** → **Андрію**
- **дідусь** → **дідусю** *(grandpa)*
- **вчи́тель** → **вчи́телю** *(teacher)*
Two consonant alternations happen before **-е**: **друг** → **дру́же** *(friend)* (г → ж) and **коза́к** → **коза́че** *(Cossack)* (к → ч). These follow standard Ukrainian phonetic patterns — the back consonant softens before **-е**.
One more form to memorize: **тато** → **тату**. This is an exception — тато doesn't fit neatly into either the -е or -ю pattern. The vocative ending is **-у**, and it simply needs to be learned as a special case alongside **син** → **си́ну** and **дід** → **ді́ду**.
<!-- INJECT_ACTIVITY: fill-in-vocative -->
<!-- INJECT_ACTIVITY: group-sort-vocative -->
## Підсумок — Summary
**Кличний відмінок** is the Ukrainian case of direct address. Every time you speak TO someone — not about them — the name or noun changes its ending. There are four main patterns at A1 level, and most names fall neatly into one of them.
| Pattern | Називни́й → Кличний | Приклади |
|---|---|---|
| Feminine **-а** (hard) | -а → -о | **Олена** → **Олено**, **мама** → **мамо**, **сестра** → **сестро** |
| Feminine **-ія** | -ія → -іє | **Марія** → **Маріє**, **Софія** → **Софіє** |
| Feminine **-уся** | -уся → -усю́ | **бабуся** → **бабусю** |
| Masculine hard | + **-е** | **Тарас** → **Тарасе**, **брат** → **брате**, **пан** → **пане** |
| Masculine **-й**/soft | + **-ю** | **Андрій** → **Андрію**, **вчитель** → **вчителю** |
| Exceptions | memorize | **тато** → **тату**, **син** → **сину**, **дід** → **діду** |
| Special **г/к** | г→ж, к→ч + **-е** | **друг** → **друже**, **козак** → **козаче** |
Can you call your own family? Try these: **мама** → ___, **тато** → ___, **брат** → ___, **сестра** → ___, **бабуся** → ___, **дідусь** → ___. And your own name or a friend's name — what does it become in vocative? (Answers: **мамо**, **тату**, **брате**, **сестро**, **бабусю**, **дідусю**.)
<!-- INJECT_ACTIVITY: quiz-choose-vocative -->

**Deterministic word count: 1265 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 68 words | Not found: 71 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Євге — NOT IN VESUM
  ✗ Іва — NOT IN VESUM
  ✗ Іван — NOT IN VESUM
  ✗ Іване — NOT IN VESUM
  ✗ Ірка — NOT IN VESUM
  ✗ Ірко — NOT IN VESUM
  ✗ Андрі — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Андрію — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Закі — NOT IN VESUM
  ✗ Катре — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Маріє — NOT IN VESUM
  ✗ Називни — NOT IN VESUM
  ✗ Настусю — NOT IN VESUM
  ✗ Настуся — NOT IN VESUM
  ✗ Ната — NOT IN VESUM
  ✗ Окса — NOT IN VESUM
  ✗ Оксано — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Оля — NOT IN VESUM
  ✗ Слу — NOT IN VESUM
  ✗ Софія — NOT IN VESUM
  ✗ Софіє — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ Тетя — NOT IN VESUM
  ✗ відмі — NOT IN VESUM
  ✗ вісімна — NOT IN VESUM
  ✗ дий — NOT IN VESUM
  ✗ дру — NOT IN VESUM
  ✗ друго — NOT IN VESUM
  ✗ дцять — NOT IN VESUM
  ✗ дьте — NOT IN VESUM
  ✗ жні — NOT IN VESUM
  ✗ ина — NOT IN VESUM
  ✗ кише — NOT IN VESUM
  ✗ кли — NOT IN VESUM
  ✗ кторович — NOT IN VESUM
  ✗ кторовичу — NOT IN VESUM
  ✗ лка — NOT IN VESUM
  ✗ лко — NOT IN VESUM
  ✗ невідмі — NOT IN VESUM
  ✗ нович — NOT IN VESUM
  ✗ новичу — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ нчення — NOT IN VESUM

All 68 other words are confirmed to exist in VESUM.

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
