# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> The review already applied some fixes. You handle what's still failing.
> You have **Edit** and **Grep** tools — fix files directly.

---

## Ukrainian Alphabet Reference (use when editing letter/sound content)

When fixing content about the Ukrainian alphabet, vowels, or consonants, use these EXACT classifications:
- **10 vowel letters (голосні)**: А, О, У, Е, И, І, Я, Ю, Є, Ї (6 base + 4 iotated)
- **22 consonant letters (приголосні)**: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ
- **1 modifier**: Ь (soft sign)
- Common confusions: В is a CONSONANT, І is a VOWEL, Й is a CONSONANT

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)



**NOTE: 5 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module, Line 112, 123 / Section "Інтеграційне завдання (Integration Task)", Line 135 / Section "Підсумок", Line 84 / Section "Навичка 3: Узгодження (Skill 3: Agreement)", Section "Навичка 3: Узгодження (Skill 3: Agreement)", Section "Огляд (Overview)" / entire module structure, Section openings across "Навичка 1", "Навичка 2", "Навичка 3"

### Finding 1: Stress Error — ви́бачте
**Location**: Line 112, 123 / Section "Інтеграційне завдання (Integration Task)"
**Problem**: Wrong stress. VESUM confirms вибачити → ви́бачте (stress on ви-), not Виба́чте.
**Required Fix**: Replace `Виба́чте` with `Ви́бачте` on both lines 112 and 123.
**Severity**: HIGH

### Finding 2: Stress Error — використо́вуємо
**Location**: Line 135 / Section "Підсумок"
**Problem**: Wrong stress on використову́ємо. Correct: використо́вуємо (stress on -то́-).
**Required Fix**: Replace `використову́ємо` with `використо́вуємо` on lines 135 and 136.
**Severity**: HIGH

### Finding 3: TTT Structure Not Implemented (Pedagogy)
**Location**: Section "Огляд (Overview)" / entire module structure
**Problem**: The module CLAIMS TTT but delivers only Teach. There is no opening diagnostic test (Test 1) and no closing test (Test 2). The self-check on lines 133-138 gives answers inline, defeating self-assessment. Plan specifies `pedagogy: TTT` and research notes explicitly say "Open with a diagnostic task."
**Required Fix**: Add a brief diagnostic mini-exercise at the start of section "Огляд (Overview)" (3-5 questions without answers, asking learner to try before reviewing). Move integration dialogue or add a similar diagnostic before the teaching sections. Hide self-check answers behind a spoiler/details tag or remove inline answers.
**Severity**: HIGH

### Finding 4: Missing Adjective Paradigm Table
**Location**: Section "Навичка 3: Узгодження (Skill 3: Agreement)"
**Problem**: Research notes explicitly recommend "Adjective paradigm table (новий: Nom/Acc/Loc across genders) should appear as a reference box — learners have seen individual forms but never side-by-side." This visual aid is missing. The content explains forms in prose only, which is harder for beginners to reference.
**Required Fix**: Add a 3×3 paradigm table for нови́й showing Nominative, Accusative, and Locative forms across masculine, feminine, and neuter genders.
**Severity**: HIGH

### Finding 5: Unnatural Example — "Я бачу велику каву"
**Location**: Line 84 / Section "Навичка 3: Узгодження (Skill 3: Agreement)"
**Problem**: Pragmatically unnatural. A native speaker wouldn't say "I see a big coffee" — you'd say "Я замовляю велику каву" (I'm ordering a big coffee) or use a different noun like "Я бачу велику будівлю" (I see a big building).
**Required Fix**: Replace with a more natural example: **Я ба́чу вели́ку буді́влю.** — I see a big building. Or: **Я хо́чу вели́ку ка́ву.** — I want a big coffee.
**Severity**: HIGH

### Finding 6: Low Immersion (11.5% vs 30-55% target)
**Location**: Entire module
**Problem**: At module 34, A1 calibration expects 30-55% Ukrainian immersion. The module is 11.5%, far below target. The content is almost entirely English prose with scattered bolded Ukrainian examples.
**Required Fix**: Add Ukrainian reading practice blocks after each skill section (3-5 Ukrainian sentences with glosses). Add Ukrainian section summaries. This would also help close the engagement richness gap.
**Severity**: HIGH

### Finding 7: Structural Monotony (LLM Fingerprint)
**Location**: Section openings across "Навичка 1", "Навичка 2", "Навичка 3"
**Problem**: While line 49 has a metaphor, lines 24 and 80 both use flat declarative openings. All three skill sections use identical example formatting (bulleted `**Ukrainian** — English` lists of 3-4 items). The uniformity across sections signals LLM generation.
**Required Fix**: Vary section openings (question, scenario, mini-dialogue). Mix example formats: use a table in one section, inline examples in another, a mini-dialogue in a third.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Stress Error — ви́бачте
- **Location**: Line 112, 123 / Section "Інтеграційне завдання (Integration Task)"
- **Original**: 「Виба́чте, **де** тут нове́ кафе́?」 and 「**«Виба́чте, де...»**」
- **Problem**: Wrong stress. VESUM confirms вибачити → ви́бачте (stress on ви-), not Виба́чте.
- **Fix**: Replace `Виба́чте` with `Ви́бачте` on both lines 112 and 123.

### Issue 2: Stress Error — використо́вуємо
- **Location**: Line 135 / Section "Підсумок"
- **Original**: 「Яки́й відмі́нок ми використову́ємо для напря́мку?」
- **Problem**: Wrong stress on використову́ємо. Correct: використо́вуємо (stress on -то́-).
- **Fix**: Replace `використову́ємо` with `використо́вуємо` on lines 135 and 136.

### Issue 3: TTT Structure Not Implemented (Pedagogy)
- **Location**: Section "Огляд (Overview)" / entire module structure
- **Original**: 「Welcome to the checkpoint! This module uses a special Test-Teach-Test structure designed specifically to help you consolidate your knowledge.」
- **Problem**: The module CLAIMS TTT but delivers only Teach. There is no opening diagnostic test (Test 1) and no closing test (Test 2). The self-check on lines 133-138 gives answers inline, defeating self-assessment. Plan specifies `pedagogy: TTT` and research notes explicitly say "Open with a diagnostic task."
- **Fix**: Add a brief diagnostic mini-exercise at the start of section "Огляд (Overview)" (3-5 questions without answers, asking learner to try before reviewing). Move integration dialogue or add a similar diagnostic before the teaching sections. Hide self-check answers behind a spoiler/details tag or remove inline answers.

### Issue 4: Missing Adjective Paradigm Table
- **Location**: Section "Навичка 3: Узгодження (Skill 3: Agreement)"
- **Problem**: Research notes explicitly recommend "Adjective paradigm table (новий: Nom/Acc/Loc across genders) should appear as a reference box — learners have seen individual forms but never side-by-side." This visual aid is missing. The content explains forms in prose only, which is harder for beginners to reference.
- **Fix**: Add a 3×3 paradigm table for нови́й showing Nominative, Accusative, and Locative forms across masculine, feminine, and neuter genders.

### Issue 5: Unnatural Example — "Я бачу велику каву"
- **Location**: Line 84 / Section "Навичка 3: Узгодження (Skill 3: Agreement)"
- **Original**: 「Я ба́чу вели́ку ка́ву.」
- **Problem**: Pragmatically unnatural. A native speaker wouldn't say "I see a big coffee" — you'd say "Я замовляю велику каву" (I'm ordering a big coffee) or use a different noun like "Я бачу велику будівлю" (I see a big building).
- **Fix**: Replace with a more natural example: **Я ба́чу вели́ку буді́влю.** — I see a big building. Or: **Я хо́чу вели́ку ка́ву.** — I want a big coffee.

### Issue 6: Low Immersion (11.5% vs 30-55% target)
- **Location**: Entire module
- **Problem**: At module 34, A1 calibration expects 30-55% Ukrainian immersion. The module is 11.5%, far below target. The content is almost entirely English prose with scattered bolded Ukrainian examples.
- **Fix**: Add Ukrainian reading practice blocks after each skill section (3-5 Ukrainian sentences with glosses). Add Ukrainian section summaries. This would also help close the engagement richness gap.

### Issue 7: Structural Monotony (LLM Fingerprint)
- **Location**: Section openings across "Навичка 1", "Навичка 2", "Навичка 3"
- **Original**: Line 24: 「Let's review the main cases you have learned so far.」 / Line 49: 「Prepositions in Ukrainian are like street signs, but they require a specific grammatical case to point you in the right direction.」 / Line 80: 「When you change the case of a noun, any adjective attached to it must change its ending as well.」
- **Problem**: While line 49 has a metaphor, lines 24 and 80 both use flat declarative openings. All three skill sections use identical example formatting (bulleted `**Ukrainian** — English` lists of 3-4 items). The uniformity across sections signals LLM generation.
- **Fix**: Vary section openings (question, scenario, mini-dialogue). Mix example formats: use a table in one section, inline examples in another, a mini-dialogue in a third.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 112 | 「Виба́чте」 | 「Ви́бачте」 | Stress |
| 123 | 「Виба́чте」 | 「Ви́бачте」 | Stress |
| 135 | 「використову́ємо」 | 「використо́вуємо」 | Stress |
| 136 | 「використову́ємо」 | 「використо́вуємо」 | Stress |
| 84 | 「Я ба́чу вели́ку ка́ву.」 | 「Я ба́чу вели́ку буді́влю.」 | Naturalness |

---

## Fix Plan to Reach 9/10 (REQUIRED)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add a 3-5 question diagnostic mini-exercise at the top of section "Огляд (Overview)" — no answers given, just "try these and see how you do." This implements the first T of TTT.
2. Lines 133-138: Remove inline answers from self-check questions or put them behind a details/spoiler element. This implements the final T of TTT.
3. Add a "You can now..." celebration before the self-check (line ~132).

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 112: Change `Виба́чте` → `Ви́бачте`
2. Line 123: Change `Виба́чте` → `Ви́бачте`
3. Line 135: Change `використову́ємо` → `використо́вуємо`
4. Line 136: Change `використову́ємо` → `використо́вуємо`

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Implement TTT structure (see Experience Quality fixes above)
2. Add adjective paradigm table in section "Навичка 3: Узгодження (Skill 3: Agreement)" showing нови́й across Nom/Acc/Loc for all three genders
3. Add Ukrainian reading practice block (3-5 sentences) after at least one skill section to boost immersion

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Fix all stress errors listed above
2. Line 84: Replace 「Я ба́чу вели́ку ка́ву.」 with a more natural example

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Vary section openings — replace at least one with a question or micro-scenario
2. Mix example formats across sections (table in one, dialogue snippet in another)

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 76.5 / 8.9 = 8.6/10
```

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 4 violations
Immersion    🇺🇦 24.9% (checkpoint - no gate)
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
→ 6 violations (moderate)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/checkpoint-cases-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Києва` (source: prose)
  ❌ `н` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-cases.md`

```markdown
<!-- SCOPE
Covers: Review and synthesis of cases (Nominative, Accusative, Locative, Genitive)
Not covered:
  - New grammar or vocabulary
  - Direction and Origin → a1-035
-->

# Checkpoint: Cases

> **Чому це важливо?**
>
> You have learned so much! Over the last several modules, you have conquered three different grammatical cases, a host of prepositions, and the way adjectives and pronouns change their forms to match. Now it is time to bring all of these moving parts together into one unified picture. Let's see how they work together to help you navigate and interact in Ukrainian.

## Огляд (Overview)

Welcome to the checkpoint! This module uses a special Test-Teach-Test structure designed specifically to help you consolidate your knowledge. Over the past lessons, you have been introduced to a lot of grammar, and here we will focus on checking your mastery of the Accusative, Locative, and Genitive cases, along with their matching prepositions. We will also review the declension of adjectives and pronouns. 

The primary goal here is the identification of any gaps in your understanding of the case system before you transition into the A1.4 phase of the curriculum. It is perfectly normal to forget a small rule or an ending, and this review is your chance to patch up those areas. We are placing our focus firmly on practical application in real-world communicative situations. You will not just be staring at grammar tables; instead, you will be using the language to navigate a city, find missing items, and interact with people.

By actively testing yourself, learning from any mistakes, and testing yourself again, you will build a solid foundation. You have worked hard to understand these concepts individually, and now you get to experience the satisfaction of combining them. Remember, understanding how these words change their endings gives you the power to express complex relationships simply and naturally.

> [!quiz] **Діагно́стика (Diagnostic)**
> Before reviewing, test yourself! Try to answer these without looking anything up:
>
> 1. Я йду в ... (шко́ла). Which ending does шко́ла take?
> 2. Я ... робо́ті. (Where am I — what preposition?)
> 3. Тут нема́є ... (ка́ва). What form does ка́ва take after нема́є?
> 4. Я ба́чу ... (брат). Does брат change? Why?
> 5. Це для ... (він). What happens to він after a preposition?
>
> Не хвилю́йтеся, якщо щось забу́ли! Read on to review, then try again at the end.

## Навичка 1: Відмінки (Skill 1: Cases)

Яку́ ро́ль грає відмі́нок у ре́ченні? How does a case ending change the meaning of a word in a sentence? Imagine you want to say "I see a park" versus "I am in a park" — Ukrainian uses different endings on the noun to signal that difference. Let's review the three cases you know.

### Модель:

The Accusative case marks the direct object of your sentence — the person or thing directly receiving the action. For inanimate objects, masculine and neuter nouns keep their Nominative form, while feminine nouns take **-у** or **-ю**. For animate nouns (living people and animals), masculine nouns take the Genitive ending instead. The question words are **Кого́?** (Whom?) and **Що?** (What?).

| Тип | Називни́й | Знахі́дний | Прикла́д |
|-----|----------|-----------|---------|
| Неістота (m) | парк | парк | **Я ба́чу парк.** |
| Неістота (n) | мі́сто | мі́сто | **Я ба́чу мі́сто.** |
| Жіно́чий (f) | ма́ма | ма́му | **Я ба́чу ма́му.** |
| Істо́та (m) | бра́т | бра́та | **Я ба́чу бра́та.** |

Notice the pattern: inanimate nouns keep their Nominative form, feminine nouns change their ending, and animate masculine nouns borrow the Genitive ending.

The Locative case expresses location. It always appears with the prepositions **в/у** (in) or **на** (on), answering the question **Де?** (Where?).

- **Де кафе́?** — Where is the cafe?
- **Кафе́ у це́нтрі.** — The cafe is in the center.
- **Де ти?** — Where are you?
- **Я на робо́ті.** — I am at work.

The Genitive case expresses absence or non-existence. The word **нема́є** (there is no / does not have) always triggers the Genitive. Question words: **Кого́ нема́є?** (Who is not here?) and **Чого́ нема́є?** (What is missing?).

- **Нема́є ка́ви.** — There is no coffee.
- **Нема́є ча́су.** — There is no time.
- **Тут нема́є бра́та.** — The brother is not here.

### Практика:

> **Чита́ємо украї́нською!** Read these sentences and identify which case each bolded noun is in:
>
> Мари́на йде в **парк**. Вона́ ба́чить **ма́му** і **бра́та**. У **па́рку** нема́є **кафе́**. Мари́на ду́має: «Нема́є **ча́су**, я йду на **робо́ту**.»
>
> парк → Accusative (direction) · ма́му → Accusative (feminine) · бра́та → Accusative (animate masculine) · па́рку → Locative (location) · кафе́ → Genitive (нема́є) · ча́су → Genitive (нема́є) · робо́ту → Accusative (direction)

### Самоперевірка:

> [!tip]
> When in doubt, ask yourself the core question. **Де?** → Locative. **Нема́є** + noun → Genitive. Direct target of your action → Accusative.

> **Підсу́мок украї́нською:**
> Знахі́дний відмі́нок відповіда́є на пита́ння «Кого́?» і «Що?». Місце́вий відмі́нок відповіда́є на пита́ння «Де?». Родови́й відмі́нок вжива́ється пі́сля сло́ва «нема́є». Ко́жен відмі́нок має свої́ закі́нчення.
>
> *(відмінок = case · закінчення = endings · відповідає на = answers · вживається = is used)*

## Навичка 2: Прийменники (Skill 2: Prepositions)

Prepositions in Ukrainian are like street signs, but they require a specific grammatical case to point you in the right direction. One of the most important concepts to master is the contrast between direction and static location.

### Модель:

When you use the prepositions **в/у** (in/into) or **на** (on/onto) to indicate movement toward a destination, they must be followed by the Accusative case. This answers the question word **Куди́?** (Where to?).

> — Куди́ ти йдеш?
> — Я йду в парк.
> — А ти?
> — Я ї́ду на робо́ту.

When those same prepositions indicate a static location, they pair with the Locative case. This answers the question word **Де?** (Where?). Compare:

| Напря́мок (Куди́?) + Знахідний | Мі́сце (Де?) + Місце́вий |
|----------------------------------|---------------------------|
| **Йду в шко́лу.** | **Я у шко́лі.** |
| **Йду на по́шту.** | **Я на по́шті.** |
| **Йду в це́нтр.** | **Я у це́нтрі.** |

Beyond direction, the Accusative case works with several other essential prepositions: **за** (for / in exchange for), **че́рез** (through / because of), and **про** (about).

- **Дя́кую за ка́ву.** — Thank you for the coffee.
- **Дя́кую за кни́гу.** — Thank you for the book.
- **Ми йдемо́ че́рез парк.** — We are walking through the park.
- **Я вдо́ма че́рез дощ.** — I am at home because of the rain.
- **Це кни́га про мі́сто.** — This is a book about the city.
- **Я ду́маю про ма́му.** — I am thinking about mom.

> [!did-you-know]
> The word **че́рез** can mean physically going through something, like walking through a park, but it is also the most common way to say "because of" an external reason!

### Практика:

> **Чита́ємо украї́нською!** Read this mini-story about Олéг's morning:
>
> Оле́г йде **на робо́ту**. Він йде **че́рез парк**. У па́рку краси́во! Оле́г ду́має **про ма́му** — він хо́че купи́ти кни́гу **про Ки́їв** **за** сто гри́вень. По́тім він бу́де **на ро́боті** до ве́чора.
>
> Notice how **на робо́ту** (Accusative — direction) changes to **на робо́ті** (Locative — already there).

### Самоперевірка:

The correspondence between a preposition and its required case is a fundamental system in Ukrainian grammar. Ask yourself: **Куди́?** → Accusative. **Де?** → Locative. **За, че́рез, про** → always Accusative.

> **Підсу́мок украї́нською:**
> Прийме́нники «в/у» і «на» потребу́ють знахі́дного відмі́нка для напря́мку і місце́вого відмі́нка для мі́сця. Прийме́нники «за», «че́рез» і «про» за́вжди потребу́ють знахі́дного відмі́нка. Пита́ння «Куди́?» — знахі́дний, «Де?» — місце́вий.
>
> *(прийменники = prepositions · потребують = require · напрямок = direction · місце = place · завжди = always)*

## Навичка 3: Узгодження (Skill 3: Agreement)

Що тра́пляється з прикме́тником, коли́ іме́нник зміню́є відмі́нок? What happens to an adjective when its noun changes case? They must agree — every word in the phrase signals the same grammatical role through its ending.

### Модель:

Let's look at adjectives in the Accusative and Locative cases using **нови́й** (new). For a feminine noun in the Accusative, the adjective takes a matching ending: **нову́ кни́гу** (a new book). In the Locative case, masculine and neuter nouns take **-о́му**: **у ново́му мі́сті** (in a new city), while feminine nouns take **-і́й**: **у нові́й кни́зі** (in a new book).

Here is a reference table for the adjective **нови́й** (new) across cases and genders:

| | Чоловічий (m) | Жіночий (f) | Середній (n) |
|------------|-----------|----------|--------|
| **Називний** | нови́й | нова́ | нове́ |
| **Знахідний** | нови́й (неістота) | нову́ | нове́ |
| **Місцевий** | ново́му | нові́й | ново́му |

The same patterns apply to **вели́кий** (big), **краси́вий** (beautiful), and **мале́нький** (small):

- **Я хо́чу вели́ку ка́ву.** — I want a big coffee.
- **Ми у мале́нькому кафе́.** — We are in a small cafe.
- **Вона́ у краси́вому мі́сті.** — She is in a beautiful city.

Pronouns also decline to match the required case. The pronoun **я** (I) changes to **мене́** (me) in the Accusative and Genitive cases. The pronoun **ти** (you) changes to **тебе́** (you).

- **Він ба́чить мене́.** — He sees me.
- **Це для мене́.** — This is for me.
- **У мене́ є час.** — I have time.
- **Я зна́ю тебе́.** — I know you.
- **Я йду без тебе́.** — I am going without you.
- **У тебе́ є бра́т?** — Do you have a brother?

One vital rule for pronouns: when a third-person pronoun like **його́** (him/it) follows a preposition, it gains an **н**-prefix to become **ньо́го**.

- **Я ба́чу його́.** — I see him.
- **Це для ньо́го.** — This is for him. (його́ → ньо́го після прийме́нника)
- **У ньо́го є ка́ва.** — He has coffee. (його́ → ньо́го після прийме́нника)

> [!warning]
> Remember the **н**-prefix rule! It is a common mistake to say **у його́**, but the correct form must always be **у ньо́го** when the pronoun comes immediately after a preposition.

### Практика:

> **Чита́ємо украї́нською!** Read and trace the agreement chains:
>
> Мари́на у ново́му мі́сті. Вона́ ба́чить краси́ву буді́влю і мале́ньке кафе́. «Я хо́чу вели́ку ка́ву!» — ду́має Мари́на. У кафе́ вона́ ба́чить **його́** — свого́ бра́та. «Це для **тебе́**!» — він дає́ їй нову́ кни́гу.
>
> нового́ мі́ста → ново́му мі́сті (Locative) · краси́ва буді́вля → краси́ву буді́влю (Accusative) · вели́ка ка́ва → вели́ку ка́ву (Accusative) · нова́ кни́га → нову́ кни́гу (Accusative)

### Самоперевірка:

Key takeaway: adjective endings ALWAYS match their noun's case and gender. When in doubt, check the table above.

> **Підсу́мок украї́нською:**
> Прикме́тники узго́джуються з іме́нниками у відмі́нку та ро́ді. Займе́нники тако́ж зміню́ють фо́рму: «я» → «мене́», «ти» → «тебе́». Пі́сля прийме́нника «його́» стає́ «ньо́го».
>
> *(прикметники = adjectives · узгоджуються = agree · іменники = nouns · рід = gender · займенники = pronouns)*

## Інтеграційне завдання (Integration Task)

Now it is time to put all of these skills together in a practical navigation scenario. Imagine you are exploring a beautiful Ukrainian city and need to find your way around. You will use all the cases, prepositions, and agreement rules we just reviewed to describe routes, locate objects, and ask for directions. 

Read the following conversation carefully. Pay attention to how the speakers switch between location questions, direction questions, and statements about absence. 

> — Ви́бачте, **де** тут нове́ кафе́?
> — Воно́ у це́нтрі. Ви йдете́ **в парк**?
> — Ні, я йду **че́рез парк**, а по́тім **на по́шту**.
> — А, я розумі́ю. Кафе́ там.
> — Дя́кую! А **зві́дки** ви?
> — Я з Ки́єва. А **куди́** ви йдете́ по́тім?
> — Додо́му, бо тут **нема́є** мого́ мале́нького бра́та.

This short dialogue features everything from asking about an origin point with **зві́дки** (from where), to requesting directions, to noting that someone is not present using the Genitive. As you review this checkpoint, perform an honest self-assessment of your case competence. Which of these grammatical rules felt the most natural to you? Did you struggle to remember the difference between direction and location? Did the adjective endings match up correctly in your mind?

> [!culture]
> Navigating a Ukrainian city is a great way to practice your grammar in real time. Locals are usually very helpful when you ask **«Ви́бачте, де...»** (Excuse me, where is...). Just remember to listen carefully to whether they use **в** or **на** in their reply!

Identifying your weakest cases now is incredibly beneficial. Spend extra time practicing those specific areas before continuing with the course. Building a strong foundation here ensures that the upcoming lessons will be a rewarding experience! Every time you notice an ending change, you are thinking exactly like a native speaker.

---

# Підсумок

You have successfully reached the end of this grammar review! We covered the essential uses of the Accusative case for direct objects, the Locative case for static locations, and the Genitive case for indicating absence. We also reviewed how prepositions of direction and location completely change the required case, and how adjectives and pronouns must align in agreement chains. You are now well-equipped to navigate the world in Ukrainian.

Тепе́р переві́рте себе́! Try answering these questions — then check your answers below:

1. Яки́й відмі́нок ми використо́вуємо для напря́мку?
2. Яки́й відмі́нок ми використо́вуємо пі́сля сло́ва «нема́є»?
3. Як сказа́ти "I see him" та "This is for him"?
4. Які́ пита́ння ми ста́вимо для мі́сця і напря́мку?

<details>
<summary>Відповіді (Answers)</summary>

1. Знахі́дний відмі́нок (Accusative case)
2. Родови́й відмі́нок (Genitive case)
3. **Я ба́чу його́** та **Це для ньо́го** (н-prefix after a preposition!)
4. **Де?** (Where? — location) та **Куди́?** (Where to? — direction)

</details>

Compare these with your answers from the diagnostic at the beginning. Ви зроби́ли чудо́ву робо́ту! You have done wonderful work! Get ready for the next adventure.

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/checkpoint-cases.yaml`

```yaml
- type: quiz
  title: Comprehensive Case and Preposition Review
  instruction: Choose the correct answer. Each question tests your integrated knowledge of cases, prepositions, and agreement from the previous modules.
  items:
    - question: 'Which case do you use after the word "немає"?'
      options:
        - text: Accusative
          correct: false
        - text: Locative
          correct: false
        - text: Genitive
          correct: true
        - text: Nominative
          correct: false
      explanation: 'Немає always triggers the Genitive case: Немає кави, Немає часу.'
    - question: Which question word helps you decide to use the Locative case?
      options:
        - text: Що?
          correct: false
        - text: Куди?
          correct: false
        - text: Де?
          correct: true
        - text: Кого?
          correct: false
      explanation: 'Де? (Where?) signals static location, which requires the Locative case with в/у or на.'
    - question: Which question word signals the Accusative case for direction?
      options:
        - text: Де?
          correct: false
        - text: Звідки?
          correct: false
        - text: Чого?
          correct: false
        - text: Куди?
          correct: true
      explanation: 'Куди? (Where to?) indicates direction of movement, requiring the Accusative case.'
    - question: 'What is the correct form: "Я йду в ___" (school, direction)?'
      options:
        - text: школі
          correct: false
        - text: школу
          correct: true
        - text: школа
          correct: false
        - text: школи
          correct: false
      explanation: Direction (Куди?) uses Accusative. Feminine школа becomes школу in the Accusative.
    - question: 'What is the correct form: "Я у ___" (school, location)?'
      options:
        - text: школу
          correct: false
        - text: школа
          correct: false
        - text: школі
          correct: true
        - text: школи
          correct: false
      explanation: Static location (Де?) uses Locative. Feminine школа becomes школі in the Locative.
    - question: 'What is the correct form: "Немає ___" (coffee)?'
      options:
        - text: кава
          correct: false
        - text: каву
          correct: false
        - text: каві
          correct: false
        - text: кави
          correct: true
      explanation: 'Немає triggers the Genitive case. Feminine кава becomes кави in the Genitive.'
    - question: 'What is the correct form: "Немає ___" (time)?'
      options:
        - text: час
          correct: false
        - text: часу
          correct: true
        - text: часі
          correct: false
        - text: часом
          correct: false
      explanation: 'Немає triggers the Genitive case. Masculine час becomes часу in the Genitive.'
    - question: 'What is the correct form: "Я бачу ___" (park)?'
      options:
        - text: парку
          correct: false
        - text: парк
          correct: true
        - text: парком
          correct: false
        - text: парці
          correct: false
      explanation: 'Парк is inanimate masculine. In the Accusative, inanimate masculine nouns keep their Nominative form: парк.'
    - question: 'What is the correct form: "Я бачу ___" (brother)?'
      options:
        - text: брат
          correct: false
        - text: брату
          correct: false
        - text: брата
          correct: true
        - text: браті
          correct: false
      explanation: 'Брат is animate masculine. Animate masculine nouns take the Genitive ending in the Accusative: брата.'
    - question: 'What is the correct form: "Я бачу ___" (mom)?'
      options:
        - text: мама
          correct: false
        - text: маму
          correct: true
        - text: мами
          correct: false
        - text: мамою
          correct: false
      explanation: 'Мама is feminine. Feminine nouns take -у/-ю in the Accusative: маму.'
    - question: Which preposition means "through" or "because of" and takes the Accusative case?
      options:
        - text: про
          correct: false
        - text: за
          correct: false
        - text: через
          correct: true
        - text: на
          correct: false
      explanation: 'Через means "through" (physically) or "because of" (reason), and always takes the Accusative.'
    - question: Which preposition means "about" and takes the Accusative case?
      options:
        - text: за
          correct: false
        - text: через
          correct: false
        - text: на
          correct: false
        - text: про
          correct: true
      explanation: 'Про means "about" and takes the Accusative: книга про місто, думати про маму.'
    - question: 'Complete the sentence: "Дякую ___ каву."'
      options:
        - text: про
          correct: false
        - text: через
          correct: false
        - text: за
          correct: true
        - text: на
          correct: false
      explanation: 'За means "for" in the sense of thanking: Дякую за каву (Thank you for the coffee).'
    - question: 'What case does "в парку" use (static location)?'
      options:
        - text: Accusative
          correct: false
        - text: Genitive
          correct: false
        - text: Nominative
          correct: false
        - text: Locative
          correct: true
      explanation: 'В/у + Locative = static location (Де?). В парку answers "Where?" not "Where to?"'
    - question: 'What case does "в парк" use (direction)?'
      options:
        - text: Locative
          correct: false
        - text: Accusative
          correct: true
        - text: Genitive
          correct: false
        - text: Nominative
          correct: false
      explanation: 'В/у + Accusative = direction (Куди?). Я йду в парк answers "Where to?"'
    - question: 'What is the correct adjective form: "___ книгу" (new, Accusative feminine)?'
      options:
        - text: нова
          correct: false
        - text: новій
          correct: false
        - text: нову
          correct: true
        - text: новому
          correct: false
      explanation: 'Feminine Accusative adjective ending: новий → нову. Я бачу нову книгу.'
    - question: 'What is the correct adjective form: "у ___ місті" (new, Locative neuter)?'
      options:
        - text: нове
          correct: false
        - text: нову
          correct: false
        - text: новій
          correct: false
        - text: новому
          correct: true
      explanation: 'Masculine/neuter Locative adjective ending: новий → новому. У новому місті.'
    - question: 'What is the correct adjective form: "у ___ книзі" (new, Locative feminine)?'
      options:
        - text: нову
          correct: false
        - text: новому
          correct: false
        - text: нова
          correct: false
        - text: новій
          correct: true
      explanation: 'Feminine Locative adjective ending: новий → новій. У новій книзі.'
    - question: 'What is the correct pronoun form: "Він бачить ___" (me)?'
      options:
        - text: я
          correct: false
        - text: мені
          correct: false
        - text: мене
          correct: true
        - text: мною
          correct: false
      explanation: 'The Accusative form of я is мене: Він бачить мене.'
    - question: 'What is the correct pronoun form: "Це для ___" (me)?'
      options:
        - text: я
          correct: false
        - text: мене
          correct: true
        - text: мені
          correct: false
        - text: мною
          correct: false
      explanation: 'Для takes Genitive. The Genitive form of я is also мене: Це для мене.'
    - question: 'What happens to "його" after a preposition like "для"?'
      options:
        - text: It stays його
          correct: false
        - text: It becomes нього
          correct: true
        - text: It becomes йому
          correct: false
        - text: It becomes ньому
          correct: false
      explanation: 'After a preposition, third-person pronouns gain an н- prefix: для нього, у нього.'
    - question: 'Choose the correct form: "У ___ є кава."'
      options:
        - text: його
          correct: false
        - text: він
          correct: false
        - text: нього
          correct: true
        - text: йому
          correct: false
      explanation: 'У is a preposition, so його becomes нього: У нього є кава (He has coffee).'
    - question: 'Choose the correct form: "Я знаю ___" (you, singular informal)?'
      options:
        - text: ти
          correct: false
        - text: тобі
          correct: false
        - text: тебе
          correct: true
        - text: тобою
          correct: false
      explanation: 'The Accusative form of ти is тебе: Я знаю тебе.'
    - question: 'Choose the correct form: "У ___ є брат?" (you, singular informal)?'
      options:
        - text: ти
          correct: false
        - text: тебе
          correct: true
        - text: тобі
          correct: false
        - text: тобою
          correct: false
      explanation: 'У + Genitive expresses possession. The Genitive of ти is тебе: У тебе є брат?'
    - question: 'You are walking toward the post office. Which sentence is correct?'
      options:
        - text: Я йду на пошті.
          correct: false
        - text: Я йду на пошту.
          correct: true
        - text: Я йду на пошта.
          correct: false
        - text: Я йду на поштою.
          correct: false
      explanation: 'Direction (Куди?) requires Accusative: на пошту. На пошті would mean you are already there.'
    - question: 'You are already at the post office. Which sentence is correct?'
      options:
        - text: Я на пошту.
          correct: false
        - text: Я на пошта.
          correct: false
        - text: Я на пошті.
          correct: true
        - text: Я на поштою.
          correct: false
      explanation: 'Static location (Де?) requires Locative: на пошті. На пошту would mean you are heading there.'
    - question: 'Complete: "Ми у ___ кафе." (small, Locative neuter)?'
      options:
        - text: маленьке
          correct: false
        - text: маленьку
          correct: false
        - text: маленькому
          correct: true
        - text: маленька
          correct: false
      explanation: 'Locative masculine/neuter adjective: маленький → маленькому. Кафе is neuter.'
    - question: 'Complete: "Я бачу ___ каву." (big, Accusative feminine)?'
      options:
        - text: велика
          correct: false
        - text: великому
          correct: false
        - text: великій
          correct: false
        - text: велику
          correct: true
      explanation: 'Accusative feminine adjective: великий → велику. Я бачу велику каву.'
    - question: 'Complete: "Вона у ___ місті." (beautiful, Locative neuter)?'
      options:
        - text: красива
          correct: false
        - text: красиву
          correct: false
        - text: красивому
          correct: true
        - text: красивій
          correct: false
      explanation: 'Locative masculine/neuter adjective: красивий → красивому. Вона у красивому місті.'
    - question: 'Someone asks "Звідки ви?" — what are they asking?'
      options:
        - text: Where are you?
          correct: false
        - text: Where are you going?
          correct: false
        - text: Where are you from?
          correct: true
        - text: What are you looking for?
          correct: false
      explanation: 'Звідки means "from where" and asks about origin: Звідки ви? = Where are you from?'

- type: fill-in
  title: Choose the Correct Case Ending
  instruction: Select the correct word form to complete each sentence. Think about which case is required.
  items:
    - sentence: 'Я йду в ___.'
      answer: школу
      options: ["школу", "школі", "школа", "школи"]
      explanation: 'Direction (Куди?) takes Accusative: школа → школу.'
    - sentence: 'Кафе у ___.'
      answer: центрі
      options: ["центрі", "центр", "центру", "центром"]
      explanation: 'Location (Де?) takes Locative: центр → центрі.'
    - sentence: 'Тут немає ___.'
      answer: кави
      options: ["кави", "кава", "каву", "каві"]
      explanation: 'Немає triggers Genitive: кава → кави.'
    - sentence: 'Я бачу нову ___.'
      answer: книгу
      options: ["книгу", "книга", "книзі", "книги"]
      explanation: 'Direct object = Accusative. Feminine: книга → книгу, and the adjective agrees: нову.'
    - sentence: 'Дякую ___ книгу.'
      answer: за
      options: ["за", "про", "через", "на"]
      explanation: 'За means "for" when thanking: Дякую за книгу.'
    - sentence: 'Це книга ___ місто.'
      answer: про
      options: ["про", "за", "через", "на"]
      explanation: 'Про means "about": Це книга про місто.'
    - sentence: 'Я вдома ___ дощ.'
      answer: через
      options: ["через", "про", "за", "на"]
      explanation: 'Через means "because of" (external reason): Я вдома через дощ.'
    - sentence: 'Це для ___.'
      answer: нього
      options: ["нього", "його", "йому", "він"]
      explanation: 'After a preposition, його gains н- prefix: для нього.'

- type: match-up
  title: 'Direction vs Location'
  instruction: Match each phrase to its correct meaning. Pay attention to the case ending.
  pairs:
    - left: Я йду в парк.
      right: I am walking to the park.
    - left: Я у парку.
      right: I am in the park.
    - left: Я йду на пошту.
      right: I am walking to the post office.
    - left: Я на пошті.
      right: I am at the post office.
    - left: Я йду в школу.
      right: I am walking to school.
    - left: Я у школі.
      right: I am at school.
    - left: Я йду в центр.
      right: I am walking to the center.
    - left: Я у центрі.
      right: I am in the center.

- type: group-sort
  title: Sort by Case
  instruction: Sort each phrase into the correct grammatical case category.
  groups:
    - name: Accusative (Знахідний)
      items:
        - бачу маму
        - йду в школу
        - бачу брата
        - дякую за каву
    - name: Locative (Місцевий)
      items:
        - у школі
        - на пошті
        - у центрі
        - у місті
    - name: Genitive (Родовий)
      items:
        - немає кави
        - немає часу
        - для мене
        - у тебе є

- type: true-false
  title: Case Rules Check
  instruction: Decide whether each statement about Ukrainian grammar is true or false.
  items:
    - statement: Inanimate masculine nouns change their form in the Accusative case.
      correct: false
      explanation: 'Inanimate masculine nouns keep their Nominative form in the Accusative: Я бачу парк (not парка).'
    - statement: Animate masculine nouns take the Genitive ending in the Accusative case.
      correct: true
      explanation: 'Animate masculine nouns use the Genitive form as their Accusative: Я бачу брата (not брат).'
    - statement: 'The prepositions в/у and на always take the Locative case.'
      correct: false
      explanation: 'В/у and на take Locative for location (Де?) but Accusative for direction (Куди?).'
    - statement: The word немає requires the Genitive case for the noun that follows it.
      correct: true
      explanation: 'Немає always triggers Genitive: Немає кави, Немає часу.'
    - statement: 'After a preposition, the pronoun його stays unchanged.'
      correct: false
      explanation: 'After a preposition, його gains an н- prefix: для нього, у нього.'
    - statement: 'The adjective ending -ому is used in the Locative case for masculine and neuter nouns.'
      correct: true
      explanation: 'Masculine/neuter Locative: у новому місті, у маленькому кафе.'
    - statement: 'Куди? is the question word for static location.'
      correct: false
      explanation: 'Куди? means "Where to?" (direction). Де? means "Where?" (static location).'
    - statement: 'The preposition через can mean both "through" and "because of."'
      correct: true
      explanation: 'Через парк (through the park) and через дощ (because of the rain) — two meanings, same preposition.'

- type: unjumble
  title: Build the Sentence
  instruction: Arrange the words to form a correct Ukrainian sentence.
  items:
    - words: ["йду", "Я", "в", "школу"]
      answer: Я йду в школу.
    - words: ["немає", "Тут", "кави"]
      answer: Тут немає кави.
    - words: ["бачу", "Я", "нову", "книгу"]
      answer: Я бачу нову книгу.
    - words: ["у", "Ми", "маленькому", "кафе"]
      answer: Ми у маленькому кафе.
    - words: ["за", "Дякую", "каву"]
      answer: Дякую за каву.
    - words: ["у", "є", "нього", "кава"]
      answer: У нього є кава.
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/checkpoint-cases.yaml`

```yaml
items:
  - lemma: "де"
    translation: "where"
    pos: "adverb"
    notes: "Location question word; triggers Locative case in response"
    usage: "Де кафе? — Where is the cafe?"
  - lemma: "куди"
    translation: "where to"
    pos: "adverb"
    notes: "Direction question word; triggers Accusative case in response"
    usage: "Куди ти йдеш? — Where are you going?"
  - lemma: "звідки"
    translation: "from where"
    pos: "adverb"
    notes: "Origin question word"
    usage: "Звідки ти? — Where are you from?"
  - lemma: "немає"
    translation: "there is no, does not have"
    pos: "verb"
    notes: "Triggers Genitive case for the following noun"
    usage: "Немає кави. — There is no coffee."
  - lemma: "новий"
    translation: "new"
    pos: "adjective"
    notes: "Paradigm adjective for case agreement; forms: нову (Acc f), новому (Loc m/n), новій (Loc f)"
    usage: "Я бачу нову книгу. У новому місті."
  - lemma: "великий"
    translation: "big"
    pos: "adjective"
    notes: "Forms: велику (Acc f), великому (Loc m/n), великій (Loc f)"
    usage: "Я бачу велику каву."
  - lemma: "красивий"
    translation: "beautiful"
    pos: "adjective"
    notes: "Forms: красиву (Acc f), красивому (Loc m/n), красивій (Loc f)"
    usage: "Вона у красивому місті."
  - lemma: "маленький"
    translation: "small, little"
    pos: "adjective"
    notes: "Forms: маленьку (Acc f), маленькому (Loc m/n)"
    usage: "Ми у маленькому кафе."
  - lemma: "через"
    translation: "through; because of"
    pos: "preposition"
    notes: "Takes Accusative case; two meanings: physical passage and reason"
    usage: "Ми йдемо через парк. Я вдома через дощ."
  - lemma: "за"
    translation: "for; behind"
    pos: "preposition"
    notes: "Takes Accusative case when meaning 'for'"
    usage: "Дякую за каву."
  - lemma: "про"
    translation: "about"
    pos: "preposition"
    notes: "Takes Accusative case"
    usage: "Це книга про місто."
  - lemma: "парк"
    translation: "park"
    pos: "noun"
    gender: "m"
    notes: "Inanimate masculine; Acc = Nom (парк), Loc = парку"
    usage: "Я йду в парк. Я у парку."
  - lemma: "місто"
    translation: "city"
    pos: "noun"
    gender: "n"
    notes: "Neuter; Acc = Nom (місто), Loc = місті"
    usage: "Я бачу місто. Я у місті."
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    notes: "Feminine; Acc = каву, Gen = кави"
    usage: "Дякую за каву. Немає кави."
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"
    notes: "Feminine; Acc = книгу, Loc = книзі (consonant change!)"
    usage: "Я бачу нову книгу. У новій книзі."
  - lemma: "школа"
    translation: "school"
    pos: "noun"
    gender: "f"
    notes: "Feminine; Acc = школу, Loc = школі"
    usage: "Я йду в школу. Я у школі."
  - lemma: "пошта"
    translation: "post office"
    pos: "noun"
    gender: "f"
    notes: "Feminine; Acc = пошту, Loc = пошті"
    usage: "Я йду на пошту. Я на пошті."
  - lemma: "робота"
    translation: "work, job"
    pos: "noun"
    gender: "f"
    notes: "Uses на (not в/у): на роботу (direction), на роботі (location)"
    usage: "Я їду на роботу. Я на роботі."
  - lemma: "брат"
    translation: "brother"
    pos: "noun"
    gender: "m"
    notes: "Animate masculine; Acc = брата (uses Genitive ending)"
    usage: "Я бачу брата. Тут немає брата."
  - lemma: "центр"
    translation: "center"
    pos: "noun"
    gender: "m"
    notes: "Inanimate masculine; Acc = центр, Loc = центрі"
    usage: "Я йду в центр. Кафе у центрі."
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, use **Grep** to verify the exact text exists in the file
2. Use the **Edit** tool to fix each issue directly in the file
3. Only fix issues documented above — no silent extra changes
4. Prioritize: audit gate failures first, then review issues

---

## How to Fix

Use the Edit tool for each fix. The workflow for each issue:

1. **Grep** the file to confirm the text exists and is unique
2. **Edit** the file: provide `old_string` (exact text from file) and `new_string` (corrected text)
3. Move to next issue

File paths:
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-cases.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/checkpoint-cases.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/checkpoint-cases.yaml`

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 edits** total (prioritize the most impactful fixes)
- If nothing needs fixing, state that clearly

---

## Friction Report (MANDATORY)

After all fixes, output:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | EDIT_FAILED | TEXT_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT output FIND/REPLACE blocks — use the Edit tool instead
- You MAY add/modify activities if the Fix Plan requests it
- Do NOT make cosmetic changes beyond what the review flagged
