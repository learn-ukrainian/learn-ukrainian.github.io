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



**NOTE: 10 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥8 items
  - Actual: Activity has 6 items
  - Fix: Add 2 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 6 items
  - Fix: Add 9 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Line 10, Section "Вступ (Introduction)", Line 121, Section "Summary", Line 156, Section "Summary", Section "Практика (Practice)" (lines 68-117), at-the-cafe.yaml line 23, Activity "Complete the Café Order" item 5, at-the-cafe.yaml lines 74, 78, 82, 86, 90 (Activity "Complete the Ordering Phrases") and lines 49, 53, 245

### Finding 1: Stress Errors (Linguistic Accuracy — HIGH)
**Location**: Line 10, Section "Вступ (Introduction)"
**Problem**: каже́ has wrong stress. Correct stress is ка́же (stress on first syllable). Appears again on line 93.
**Required Fix**: Replace каже́ → ка́же in all occurrences.
**Severity**: HIGH

### Finding 2: Non-Existent VESUM Distractors in Activity (Activities — HIGH)
**Location**: at-the-cafe.yaml line 23, Activity "Complete the Café Order" item 5
**Problem**: менюу, менює, and менюм are not real Ukrainian word forms (confirmed not found in VESUM). Students would practice rejecting non-existent forms, which teaches nothing useful and could confuse them. The whole point of the activity item is that меню is indeclinable — the distractors should be plausible but wrong case forms of other words, or common learner misconceptions.
**Required Fix**: Replace with plausible distractors that a learner might actually confuse: e.g., `["меню", "меню́ю", "меню́а", "меню́і"]` — or better, replace the entire item with a different ordering scenario since the indeclinability of меню is hard to test with a fill-in format.
**Severity**: HIGH

### Finding 3: Missing Plan Section "Продукція та Підсумок" (Pedagogy — MEDIUM)
**Location**: Line 121, Section "Summary"
**Problem**: Plan defines section "Продукція та Підсумок (Production and Summary)" but the content only has "Summary". The "Продукція" (Production) phase — where learners produce language freely — is collapsed into the Summary. The plan's Production points include "Можна рахунок?" (completely absent) and a full-cycle roleplay with the "Chatty Barista" persona.
**Required Fix**: Rename "## Summary" to "## Продукція та Підсумок (Production and Summary)" and add the missing "Можна рахунок?" phrase with practice context.
**Severity**: HIGH

### Finding 4: Missing Imperative Practice in Prose (Pedagogy — MEDIUM)
**Location**: Section "Практика (Practice)" (lines 68-117)
**Problem**: Plan point "Форми наказового способу: практика вживання ввічливих команд «дайте, будь ласка» та «принесіть, будь ласка»" is not addressed in the prose content. Neither "дайте" nor "принесіть" appears in the lesson text. They only appear as activity answer options. The research notes grant these as a plan exception (chunks, not paradigm), but they still need to appear in the teaching content.
**Required Fix**: Add a short subsection in section "Практика (Practice)" introducing "Дайте, будь ласка..." and "Принесіть, будь ласка..." as polite request chunks, with 2-3 example phrases.
**Severity**: HIGH

### Finding 5: Activity Explanations Leak A2 Grammar Scope (Pedagogy — MEDIUM)
**Location**: at-the-cafe.yaml lines 74, 78, 82, 86, 90 (Activity "Complete the Ordering Phrases") and lines 49, 53, 245
**Problem**: Plan explicitly states: "вивчення конструкцій «з молоком» та «без цукру» як готових фраз-чанків **без пояснення відмінків** для рівня A1." But 7 activity explanations label these as "Instrumental case" and "Genitive case" — terms not yet in scope. This contradicts the chunk-first approach.
**Required Fix**: Rewrite explanations to use chunk language instead of case terminology. E.g., "З (with) requires the Instrumental case: молоко → молоком" → "З (with) changes the word: молоко → молоком. Memorize this as a fixed phrase."
**Severity**: HIGH

### Finding 6: False Summary Claim (Factual Accuracy — LOW)
**Location**: Line 156, Section "Summary"
**Problem**: "request a table" is never taught in this module. No vocabulary for столик, no phrases for requesting seating.
**Required Fix**: Remove "politely request a table" — replace with something actually taught, like "greet the staff and place your order."
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Stress Errors (Linguistic Accuracy — HIGH)

**Multiple stress placement errors across the module:**

- **Location**: Line 10, Section "Вступ (Introduction)"
- **Original**: 「Коли́ хтось каже́: «Пі́демо на ка́ву?» — це запро́шення поговори́ти.」
- **Problem**: каже́ has wrong stress. Correct stress is ка́же (stress on first syllable). Appears again on line 93.
- **Fix**: Replace каже́ → ка́же in all occurrences.

- **Location**: Line 13, Section "Вступ (Introduction)"
- **Original**: 「Ка́ва — це мо́мент для спілкува́ння, для дру́жби.」
- **Problem**: мо́мент has wrong stress. Correct stress is моме́нт (stress on second syllable).
- **Fix**: Replace мо́мент → моме́нт.

- **Location**: Line 28, Section "Презентація (Presentation)"
- **Original**: 「Прочита́йте ці фра́зи вголо́с. Уяві́ть, що ви — бари́ста у льві́вській кав'я́рні.」
- **Problem**: вголо́с has wrong stress. Correct stress is вго́лос.
- **Fix**: Replace вголо́с → вго́лос.

- **Location**: Line 93, Section "Практика (Practice)"
- **Original**: 「О дев'я́тій ра́нку Олена́ іде́ до кав'я́рні.」
- **Problem**: Олена́ has wrong stress. Correct stress is Оле́на (stress on second syllable). Appears 3 times on this line.
- **Fix**: Replace Олена́ → Оле́на in all occurrences.

### Issue 2: Non-Existent VESUM Distractors in Activity (Activities — HIGH)

- **Location**: at-the-cafe.yaml line 23, Activity "Complete the Café Order" item 5
- **Original**: `options: ["меню", "менюу", "менює", "менюм"]`
- **Problem**: менюу, менює, and менюм are not real Ukrainian word forms (confirmed not found in VESUM). Students would practice rejecting non-existent forms, which teaches nothing useful and could confuse them. The whole point of the activity item is that меню is indeclinable — the distractors should be plausible but wrong case forms of other words, or common learner misconceptions.
- **Fix**: Replace with plausible distractors that a learner might actually confuse: e.g., `["меню", "меню́ю", "меню́а", "меню́і"]` — or better, replace the entire item with a different ordering scenario since the indeclinability of меню is hard to test with a fill-in format.

### Issue 3: Missing Plan Section "Продукція та Підсумок" (Pedagogy — MEDIUM)

- **Location**: Line 121, Section "Summary"
- **Problem**: Plan defines section "Продукція та Підсумок (Production and Summary)" but the content only has "Summary". The "Продукція" (Production) phase — where learners produce language freely — is collapsed into the Summary. The plan's Production points include "Можна рахунок?" (completely absent) and a full-cycle roleplay with the "Chatty Barista" persona.
- **Fix**: Rename "## Summary" to "## Продукція та Підсумок (Production and Summary)" and add the missing "Можна рахунок?" phrase with practice context.

### Issue 4: Missing Imperative Practice in Prose (Pedagogy — MEDIUM)

- **Location**: Section "Практика (Practice)" (lines 68-117)
- **Problem**: Plan point "Форми наказового способу: практика вживання ввічливих команд «дайте, будь ласка» та «принесіть, будь ласка»" is not addressed in the prose content. Neither "дайте" nor "принесіть" appears in the lesson text. They only appear as activity answer options. The research notes grant these as a plan exception (chunks, not paradigm), but they still need to appear in the teaching content.
- **Fix**: Add a short subsection in section "Практика (Practice)" introducing "Дайте, будь ласка..." and "Принесіть, будь ласка..." as polite request chunks, with 2-3 example phrases.

### Issue 5: Activity Explanations Leak A2 Grammar Scope (Pedagogy — MEDIUM)

- **Location**: at-the-cafe.yaml lines 74, 78, 82, 86, 90 (Activity "Complete the Ordering Phrases") and lines 49, 53, 245
- **Problem**: Plan explicitly states: "вивчення конструкцій «з молоком» та «без цукру» як готових фраз-чанків **без пояснення відмінків** для рівня A1." But 7 activity explanations label these as "Instrumental case" and "Genitive case" — terms not yet in scope. This contradicts the chunk-first approach.
- **Fix**: Rewrite explanations to use chunk language instead of case terminology. E.g., "З (with) requires the Instrumental case: молоко → молоком" → "З (with) changes the word: молоко → молоком. Memorize this as a fixed phrase."

### Issue 6: False Summary Claim (Factual Accuracy — LOW)

- **Location**: Line 156, Section "Summary"
- **Original**: 「You are now fully equipped to enjoy the vibrant Ukrainian café scene. You know how to politely request a table, order your favorite beverages using the proper grammar, customize your drinks with handy chunks, and settle your bill without any awkward mix-ups.」
- **Problem**: "request a table" is never taught in this module. No vocabulary for столик, no phrases for requesting seating.
- **Fix**: Remove "politely request a table" — replace with something actually taught, like "greet the staff and place your order."

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 10 | 「каже́」 | 「ка́же」 | Stress |
| 13 | 「мо́мент」 | 「моме́нт」 | Stress |
| 28 | 「вголо́с」 | 「вго́лос」 | Stress |
| 93 | 「Олена́」 (×3) | 「Оле́на」 | Stress |
| 93 | 「каже́」 | 「ка́же」 | Stress |

### Pre-Screen Dismissals

- **#3 (Agreement 'вели́ку' + 'Вам')**: FALSE POSITIVE. 「Вам вели́ку чи малу́ ка́ву?」 — вели́ку agrees with ка́ву (fem. acc.), not with Вам. Correct Ukrainian.
- **#4 (Agreement 'дев'я́тій' + 'ра́нку')**: FALSE POSITIVE. "О дев'я́тій ра́нку" is a fixed time expression where дев'ятій modifies implied годині (hour), not ра́нку.
- **#1-2 (Imperatives Прочитайте/Уявіть)**: DISMISS. Research notes document a plan exception granting imperatives for this module. These are also meta-instructions to the learner, not café vocabulary being taught.
- **#7 (Бари́ста stress unknown)**: DISMISS. VESUM confirms бариста exists. Stress on second syllable is standard for this loanword.
- **#10 (вікна́ → ві́кна)**: DISMISS. In 「бі́ля вікна́」 this is genitive singular of вікно́. Stress вікна́ is correct for genitive singular.

---

## Fix Plan to Reach 9/10 (REQUIRED)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 10: Change 「каже́」 → 「ка́же」
2. Line 13: Change 「мо́мент」 → 「моме́нт」
3. Line 28: Change 「вголо́с」 → 「вго́лос」
4. Line 93: Change 「Олена́」 → 「Оле́на」 (3 occurrences) and 「каже́」 → 「ка́же」
5. Activities line 23: Replace non-existent distractors менюу, менює, менюм with plausible alternatives
6. Line 156: Remove false claim about "request a table"

**Expected score after fix:** 9/10

### Language: 7/10 → 9/10
**What to fix:** Same stress fixes as Linguistic Accuracy. All stress errors are the only Language issue.
**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Add imperative chunks (дайте, будь ласка / принесіть, будь ласка) to section "Практика (Practice)" — 3-4 sentences with English translations
2. Add "Можна рахунок?" to section "Summary" or rename section to match plan
3. Rename "## Summary" → "## Продукція та Підсумок (Production and Summary)"
4. Rewrite 7 activity explanations to remove Instrumental/Genitive case labels

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Replace VESUM-failing distractors in activity item 5
2. Rewrite case-labeling explanations to use chunk language

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience: 8 → 8.5 (with section rename + preview)
Language: 7 → 9 (stress fixes)
Pedagogy: 7 → 9 (missing content added)
Activities: 7 → 9 (distractors + explanations fixed)
Beginner Safety: 9 → 9 (unchanged)
LLM Fingerprint: 9 → 9 (unchanged)
Linguistic Accuracy: 7 → 9 (stress + distractors + summary fixed)

Projected = (8.5×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
         = (12.75 + 9.9 + 10.8 + 11.7 + 11.7 + 9.0 + 13.5) / 8.9
         = 79.35 / 8.9
         = 8.9/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️  Outline compliance: 1 errors, 0 warnings
❌ [MISSING_OUTLINE_SECTION] Section 'Продукція та Підсумок (Production and Summary)' defined in outline but not found in markdown.
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 2 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
→ 6 violations (moderate)
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• 1 Outline Compliance Errors
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/at-the-cafe-audit.log for details)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: 1 Outline Compliance Errors
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe.md`

```markdown
## Вступ (Introduction)

Stepping into a Ukrainian café is about much more than just grabbing a quick drink. In Ukraine, especially in the historic city of Lviv, visiting a café is a fundamental social ritual. When someone invites you with the phrase **піти на каву** (to go for coffee), they are extending an invitation for connection, deep conversation, or even a romantic date. The café acts as an extension of the living room, a place where people gather to share news, discuss business, or simply watch the world go by. You will find that **кава** (coffee) is a cornerstone of daily life, and understanding how to order it correctly opens doors to genuine cultural immersion. 

> 🌍 **Культу́рна замі́тка (Cultural Note)**
>
> У Льво́ві ка́ва — це не про́сто напі́й. Це тради́ція.
> (In Lviv, coffee is not just a drink. It is a tradition.)
>
> Коли́ хтось ка́же: «Пі́демо на ка́ву?» — це запро́шення поговори́ти.
> (When someone says: "Shall we go for coffee?" — it is an invitation to talk.)
>
> Ка́ва — це моме́нт для спілкува́ння, для дру́жби.
> (Coffee is a moment for communication, for friendship.)

The roots of this deep appreciation for coffee can be traced back to a legendary figure in Ukrainian history, Yuriy Kulchytskyi. He was a Ukrainian Cossack hero who played a pivotal role during the Battle of Vienna in the seventeenth century. After the battle, he was rewarded with massive sacks of captured Ottoman coffee beans, which he used to open one of the very first coffeehouses in Europe. He is widely credited with popularizing the practice of adding milk and sweetener to the dark, bitter brew, transforming European tastes forever. If you visit Lviv today, you can find a beautiful monument dedicated to Kulchytskyi, serving as a visual symbol of this rich, centuries-old coffee tradition. 

When you enter a bustling café or a quiet neighborhood coffee shop, the first question you might hear from a hospitable host or a friend is **Чай чи кава?** (Tea or coffee?). This is the canonical Ukrainian hospitality question offered to almost any guest entering a home or office. It is the perfect starting point for our journey. By mastering the vocabulary and etiquette of ordering your favorite drinks and a sweet **тістечко** (pastry), you are not just learning transactions; you are stepping into a vibrant cultural space. You will soon be able to confidently read the **меню** (menu) and interact with the **офіціант** (waiter) just like a local.

## Презентація (Presentation)

When you approach the counter or sit at your table, the interaction follows a predictable and polite script. The primary rule of Ukrainian service etiquette is the mandatory use of the formal **Ви** (you) when speaking with café staff. 

The **офіціант** (waiter) or barista will typically welcome you and initiate the interaction with a standard greeting. 

> 🎬 **Рольова́ гра: Бари́ста (Roleplay: Barista)**
>
> Прочита́йте ці фра́зи вго́лос. Уяві́ть, що ви — бари́ста у льві́вській кав'я́рні.
> (Read these phrases aloud. Imagine you are a barista in a Lviv café.)
>
> — **До́брий день! Що ви бажа́єте?** (Good afternoon! What do you desire?)
> — **Вам вели́ку чи малу́ ка́ву?** (For you, a large or small coffee?)
> — **З молоко́м чи без?** (With milk or without?)
> — **Ось ваш раху́нок.** (Here is your bill.)
> — **Дякую! На все до́бре!** (Thank you! All the best!)

> — **До́брий день! Що бажа́єте?** (Good afternoon! What do you desire?)
> — **До́брий день. Що ви замо́вите?** (Good afternoon. What will you order?)

In English, it feels completely natural to say "I want coffee." However, directly translating this into Ukrainian as **Я хочу каву** can sound surprisingly blunt or even child-like to native ears. Instead, Ukrainian relies on more polite, indirect structures for ordering. The most common and natural ways to order are using **Мені, будь ласка...** (To me, please...) or **Я буду...** (I will be...). Both expressions soften the request and show respect for the staff.

*   **Мені́, будь ла́ска, ка́ву.** (For me, please, a coffee.)
*   **Я бу́ду чай.** (I will have tea.)
*   **Мені́, будь ла́ска, меню́.** (For me, please, the menu.)

Notice what happens to the words for coffee and water when we place an order. Because you are the subject performing the action of ordering, the drink itself becomes the direct object. In Ukrainian grammar, direct objects take the Accusative case. For feminine nouns ending in **-а**, this means the ending transforms into **-у**.

| Basic Form (Nominative) | Ordering Form (Accusative) | Example Phrase |
|-------------------------|---------------------------|----------------|
| **ка́ва** (coffee) | **ка́ву** | **Я бу́ду ка́ву.** |
| **вода́** (water) | **воду́** | **Я бу́ду воду́.** |
| **чай** (tea) | **чай** (no change) | **Я бу́ду чай.** |

As you can see, masculine nouns that refer to inanimate objects, like **чай** (tea) or **цу́кор** (sugar), do not change their endings in the Accusative case. They look exactly the same as their dictionary forms.

Another crucial word you will use is **меню́** (menu). This is a borrowed word and is completely indeclinable. It never changes its ending, no matter its role in the sentence. You can simply say **меню́, будь ла́ска** (menu, please) without worrying about any case transformations.

Customizing your drink is an essential part of the modern café experience. Instead of worrying about complex grammar rules right now, it is easiest to learn these common additions as fixed, ready-to-use phrases. Memorize these practical chunks to easily modify your order:

*   **ка́ва з молоко́м** (coffee with milk)
*   **ка́ва без цу́кру** (coffee without sugar)
*   **вода́ з га́зом** (water with gas/sparkling)
*   **вода́ без га́зу** (water without gas/still)
*   **чай з лимо́ном** (tea with lemon)

If you memorize these chunks, you can simply attach them directly to your main request.

## Практика (Practice)

Let us put this knowledge into active use. The most common mistake learners make is forgetting to change the feminine ending when ordering, resulting in sentences like **Я буду кава.** Remember that the action of ordering requires the Accusative form for feminine nouns. 

Review this pattern of transformation for your orders:

кава → каву
вода → воду
тістечко → тістечко (neuter, no change)

Sometimes you need to politely direct the staff, such as asking for the menu or requesting a specific item. You already know **будь ла́ска** (please), which is an essential part of any request. Remember that you can pair it with the name of the item you want to order. This is a very reliable way to communicate your needs in any restaurant or café setting.

*   **Меню́, будь ла́ска.** (The menu, please.)
*   **Воду́, будь ла́ска.** (Water, please.)
*   **Ка́ву, будь ла́ска.** (Coffee, please.)

There is another way to make polite requests in Ukrainian — using special command forms directed at the staff. At this stage, simply memorize these as ready-made chunks without worrying about how they are formed:

*   **Да́йте, будь ла́ска, меню́.** (Give [me], please, the menu.)
*   **Да́йте, будь ла́ска, раху́нок.** (Give [me], please, the bill.)
*   **Принесі́ть, будь ла́ска, ка́ву.** (Bring, please, coffee.)
*   **Принесі́ть, будь ла́ска, воду́.** (Bring, please, water.)

Both **да́йте** and **принесі́ть** are polite request forms used with **Ви** (the formal "you"). They are very common in cafés and restaurants, and pairing them with **будь ла́ска** makes your request sound natural and respectful.

When ordering, the barista might ask you to clarify your choice. You will need to understand and use basic descriptive adjectives. Are you looking for a large drink to start your morning, or a small one? Do you prefer it hot or iced?

> — **Вели́ку чи малу́?** (Large or small?)
> — **Малу́, будь ла́ска.** (Small, please.)
> — **Холо́дний чай чи гаря́чий?** (Cold tea or hot?)
> — **Гаря́чий, будь ла́ска.** (Hot, please.)

Now read through this short narrative about a typical morning café visit. Try to understand the Ukrainian before reading the English translation:

> **Ра́нок у кав'я́рні.** О дев'я́тій ра́нку Оле́на іде́ до кав'я́рні. Вона́ замовля́є вели́ку ка́ву з молоко́м і смачне́ ті́стечко. Бари́ста ка́же: «До́брий ра́нок! Ось ва́ша ка́ва.» Оле́на відповіда́є: «Дякую!» Вона́ сіда́є бі́ля вікна́ й п'є ка́ву пові́льно. Потім вона́ про́сить раху́нок і пла́тить ка́рткою. «До поба́чення!» — ка́же Оле́на.
>
> (Morning at the café. At nine in the morning, Olena goes to the café. She orders a large coffee with milk and a tasty pastry. The barista says: "Good morning! Here is your coffee." Olena answers: "Thank you!" She sits by the window and drinks her coffee slowly. Then she asks for the bill and pays by card. "Goodbye!" — says Olena.)

Let us review a full conversation between a guest and a waiter. Notice how the polite forms and the Accusative case are used throughout the interaction.

> — **До́брий день! Що ви бажа́єте?** (Good afternoon! What do you desire?)
> — **До́брий день. Мені́, будь ла́ска, меню́.** (Good afternoon. For me, please, the menu.)
> — **Ось, будь ла́ска.** (Here you go, please.)
> — **Дякую. Мені́ гаря́чу ка́ву, будь ла́ска.** (Thank you. For me, hot coffee, please.)
> — **Вели́ку чи малу́?** (Large or small?)
> — **Вели́ку ка́ву, будь ла́ска.** (A large coffee, please.)
> — **З молоко́м чи без?** (With milk or without?)
> — **З молоко́м, але без цу́кру. І ті́стечко, будь ла́ска.** (With milk, but without sugar. And a pastry, please.)
> — **Так, звича́йно. Щось ще?** (Yes, of course. Anything else?)
> — **Я бу́ду чай. Зеле́ний чай з лимо́ном.** (I will have tea. Green tea with lemon.)
> — **Холо́дний чи гаря́чий?** (Cold or hot?)
> — **Гаря́чий, будь ла́ска.** (Hot, please.)
> — **Дякую. Я принесу́ ва́ше замо́влення.** (Thank you. I will bring your order.)
> — **Ду́же дякую. Раху́нок, будь ла́ска.** (Thank you very much. The bill, please.)
> — **Опла́та ка́рткою чи готі́вкою?** (Payment by card or cash?)
> — **Я заплачу ка́рткою.** (I will pay by card.)
> — **Ось ваш раху́нок.** (Here is your bill.)
> — **Дякую, до поба́чення!** (Thank you, goodbye!)
> — **На все до́бре!** (All the best!)

A critical moment arrives when you are ready to leave. There is a very common trap here for English speakers. In English, we often ask for the "check." If you ask a Ukrainian waiter for a **чек**, they will bring you the small printed fiscal receipt from the cash register, but this is not the word used to ask for the total amount you owe. In a Ukrainian dining establishment, you must always ask for the **рахунок** (bill). Asking for a **чек** when you want to pay can lead to mild confusion or an awkward pause. You can also use the very natural phrase **Мо́жна раху́нок?** (Can I have the bill?) — this is one of the most common ways Ukrainians ask for the bill in everyday life. Let us practice the correct way to wrap up your meal.

## Summary

When you are ready to finish your café visit, you need to call the waiter and ask for your total. You can simply catch the waiter's eye and politely ask for the bill. It is also helpful to clarify how you intend to pay, as many modern Ukrainian cafés accept digital payments, but some traditional spots might still prefer cash.

> 💡 **Review: Your Cafe Vocabulary**
>
> Make sure you know these essential items:
>
> — **Чо́рний чай** (black tea)
> — **Зеле́ний чай** (green tea)
> — **Міцна́ ка́ва** (strong coffee)
> — **Смачне́ ті́стечко** (tasty pastry)
> — **Холо́дна вода́** (cold water)
> — **Гаря́ча вода́** (hot water)
> — **Мінера́льна вода́** (mineral water)
> — **Чайові́** (tip)

*   **Раху́нок, будь ла́ска.** (The bill, please.)
*   **Я заплачу ка́рткою.** (I will pay by card.)
*   **Я заплачу готі́вкою.** (I will pay with cash.)

> [!cultural-note] Tipping in Ukraine
> It is common practice in Ukraine to show appreciation for good service by leaving **чайові́** (a tip). The standard amount is generally around ten percent of the total **раху́нок**. You can often leave **чайові́** directly on the table in cash, or occasionally add it via the terminal when you pay with a **ка́ртка** (card).

Now, imagine you are stepping up to the counter of a busy, aromatic Lviv café. The barista smiles and greets you. Use everything you have learned to complete the interaction smoothly.

> — **До́брий день! Що ви замо́вите?** (Good afternoon! What will you order?)
> — **До́брий день. Мені́, будь ла́ска, ка́ву.** (Good afternoon. For me, please, coffee.)
> — **З молоко́м чи без?** (With milk or without?)
> — **З молоко́м, але без цу́кру.** (With milk, but without sugar.)
> — **Щось ще? Ті́стечко?** (Anything else? A pastry?)
> — **Ні, дякую. Раху́нок, будь ла́ска.** (No, thank you. The bill, please.)
> — **Так, звича́йно. Опла́та ка́рткою чи готі́вкою?** (Yes, of course. Payment by card or cash?)
> — **Ка́рткою, будь ла́ска.** (By card, please.)

You are now fully equipped to enjoy the vibrant Ukrainian café scene. You know how to greet the staff, order your favorite beverages using the proper grammar, customize your drinks with handy chunks, and settle your bill without any awkward mix-ups.
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-cafe.yaml`

```yaml
- type: fill-in
  title: "Complete the Café Order"
  instruction: "Choose the correct word to complete each ordering phrase."
  items:
    - sentence: "Мені, будь ласка, ___."
      answer: "каву"
      options: ["каву", "кава", "каві", "кавою"]
      explanation: "When ordering, coffee becomes the direct object and takes the Accusative case: кава → каву."
    - sentence: "Я буду ___."
      answer: "чай"
      options: ["чай", "чаю", "чаєм", "чаї"]
      explanation: "Masculine inanimate nouns like чай do not change in the Accusative case."
    - sentence: "Мені, будь ласка, ___."
      answer: "воду"
      options: ["воду", "вода", "воді", "водою"]
      explanation: "Feminine nouns ending in -а change to -у in the Accusative: вода → воду."
    - sentence: "Я буду ___ з молоком."
      answer: "каву"
      options: ["каву", "кава", "каві", "кавою"]
      explanation: "You are ordering coffee (direct object), so use the Accusative form: каву."
    - sentence: "Мені ___ воду, будь ласка."
      answer: "холодну"
      options: ["холодну", "холодний", "холодна", "холодною"]
      explanation: "The adjective must agree with воду (Accusative feminine): холодна → холодну."
    - sentence: "___, будь ласка."
      answer: "Тістечко"
      options: ["Тістечко", "Тістечку", "Тістечка", "Тістечком"]
      explanation: "Neuter nouns like тістечко do not change in the Accusative case."
    - sentence: "Я буду зелений ___ з лимоном."
      answer: "чай"
      options: ["чай", "чаю", "чаєм", "чаї"]
      explanation: "Чай is masculine inanimate — it stays the same in the Accusative."
    - sentence: "Мені ___ каву, будь ласка."
      answer: "гарячу"
      options: ["гарячу", "гарячий", "гаряча", "гарячою"]
      explanation: "The adjective must agree with каву (Accusative feminine): гаряча → гарячу."
    - sentence: "Я буду чорний ___."
      answer: "чай"
      options: ["чай", "чаю", "чаєм", "чаї"]
      explanation: "Чай is masculine inanimate — it stays the same when you order it."
    - sentence: "Мені мінеральну ___, будь ласка."
      answer: "воду"
      options: ["воду", "вода", "воді", "водою"]
      explanation: "Feminine nouns ending in -а change to -у when ordering: вода → воду."
    - sentence: "Я буду ___ без цукру."
      answer: "каву"
      options: ["каву", "кава", "каві", "кавою"]
      explanation: "You are ordering coffee (direct object): кава → каву."
    - sentence: "Принесіть, будь ласка, ___."
      answer: "воду"
      options: ["воду", "вода", "воді", "водою"]
      explanation: "You are requesting water (direct object): вода → воду."
    - sentence: "Дайте, будь ласка, ___."
      answer: "рахунок"
      options: ["рахунок", "рахунку", "рахунком", "рахунки"]
      explanation: "Рахунок (bill) is masculine inanimate — it stays the same when you request it."
    - sentence: "Мені ___ каву, будь ласка."
      answer: "міцну"
      options: ["міцну", "міцна", "міцний", "міцною"]
      explanation: "The adjective must agree with каву (Accusative feminine): міцна → міцну."
    - sentence: "Я буду ___ з газом."
      answer: "воду"
      options: ["воду", "вода", "воді", "водою"]
      explanation: "You are ordering water (direct object): вода → воду."

- type: fill-in
  title: "Customer and Waiter"
  instruction: "Fill in the missing word from the café dialogue."
  items:
    - sentence: "Добрий день! Що ви ___?"
      answer: "бажаєте"
      options: ["бажаєте", "бажаю", "бажати", "бажає"]
      explanation: "The waiter addresses the customer formally with ви, so the verb is бажаєте (you desire)."
    - sentence: "Оплата ___ чи готівкою?"
      answer: "карткою"
      options: ["карткою", "картка", "картку", "картці"]
      explanation: "Оплата карткою — payment by card changes the word: картка → карткою. Memorize this as a fixed phrase."
    - sentence: "Я заплачу ___."
      answer: "готівкою"
      options: ["готівкою", "готівка", "готівку", "готівці"]
      explanation: "Paying with cash changes the word: готівка → готівкою. Memorize this as a fixed phrase."
    - sentence: "___, будь ласка."
      answer: "Рахунок"
      options: ["Рахунок", "Чек", "Оплата", "Замовлення"]
      explanation: "In Ukrainian cafés, you ask for рахунок (the bill), not чек (which is a fiscal receipt)."
    - sentence: "Ось ваше ___."
      answer: "замовлення"
      options: ["замовлення", "замовляти", "замовити", "замовлю"]
      explanation: "Замовлення (order) is a noun. The waiter says: Here is your order."
    - sentence: "Дякую! На все ___!"
      answer: "добре"
      options: ["добре", "добрий", "добра", "добром"]
      explanation: "На все добре! is a fixed farewell phrase meaning All the best!"
    - sentence: "Вам велику ___ малу?"
      answer: "чи"
      options: ["чи", "або", "і", "та"]
      explanation: "Чи is the Ukrainian word for 'or' when offering a choice between two options."
    - sentence: "З молоком ___ без?"
      answer: "чи"
      options: ["чи", "або", "і", "та"]
      explanation: "Чи means 'or' — the waiter offers a choice between two options."
    - sentence: "Я ___ каву з молоком."
      answer: "буду"
      options: ["буду", "будь", "будемо", "будете"]
      explanation: "Я буду... is a polite way to say 'I will have...' when ordering."
    - sentence: "Мені, ___ ласка, воду."
      answer: "будь"
      options: ["будь", "буду", "була", "будемо"]
      explanation: "Будь ласка means 'please' — an essential polite phrase in every order."
    - sentence: "Дякую, до ___!"
      answer: "побачення"
      options: ["побачення", "зустрічі", "ранку", "вечора"]
      explanation: "До побачення! means 'Goodbye!' — a standard farewell in Ukrainian."
    - sentence: "Я ___ карткою."
      answer: "заплачу"
      options: ["заплачу", "заплатити", "заплатив", "заплатила"]
      explanation: "Заплачу is the future form: I will pay. Used when settling the bill."
    - sentence: "___ день! Що ви замовите?"
      answer: "Добрий"
      options: ["Добрий", "Добра", "Добре", "Добрим"]
      explanation: "Добрий день! is the standard afternoon greeting — Добрий agrees with день (masculine)."
    - sentence: "Можна ___?"
      answer: "рахунок"
      options: ["рахунок", "рахунку", "рахунком", "рахунки"]
      explanation: "Можна рахунок? means 'Can I have the bill?' — a very natural way to ask for the bill."
    - sentence: "Щось ___?"
      answer: "ще"
      options: ["ще", "щось", "вже", "тут"]
      explanation: "Щось ще? means 'Anything else?' — a standard question from café staff."

- type: fill-in
  title: "Complete the Ordering Phrases"
  instruction: "Choose the correct word or phrase to complete each sentence you might hear or say at a Ukrainian café."
  items:
    - sentence: "Кава з ___."
      answer: "молоком"
      options: ["молоком", "молоко", "молока", "молоку"]
      explanation: "З (with) changes the word ending: молоко → молоком. Memorize this as a ready-made phrase."
    - sentence: "Кава без ___."
      answer: "цукру"
      options: ["цукру", "цукор", "цукром", "цукрі"]
      explanation: "Без (without) changes the word ending: цукор → цукру. Memorize this as a ready-made phrase."
    - sentence: "Вода з ___."
      answer: "газом"
      options: ["газом", "газ", "газу", "газі"]
      explanation: "З (with) changes the word ending: газ → газом. Memorize this as a ready-made phrase."
    - sentence: "Вода без ___."
      answer: "газу"
      options: ["газу", "газ", "газом", "газі"]
      explanation: "Без (without) changes the word ending: газ → газу. Memorize this as a ready-made phrase."
    - sentence: "Чай з ___."
      answer: "лимоном"
      options: ["лимоном", "лимон", "лимона", "лимону"]
      explanation: "З (with) changes the word ending: лимон → лимоном. Memorize this as a ready-made phrase."
    - sentence: "Велику ___, будь ласка."
      answer: "каву"
      options: ["каву", "кава", "каві", "кавою"]
      explanation: "You are ordering a large coffee — Accusative case: кава → каву."
    - sentence: "Мені ___ каву, будь ласка."
      answer: "велику"
      options: ["велику", "великий", "велика", "великою"]
      explanation: "The adjective agrees with каву (Accusative feminine): велика → велику."
    - sentence: "___ чай, будь ласка."
      answer: "Гарячий"
      options: ["Гарячий", "Гарячу", "Гаряча", "Гарячою"]
      explanation: "Чай is masculine — the adjective stays in masculine Accusative form: гарячий."
    - sentence: "Холодний чай чи ___?"
      answer: "гарячий"
      options: ["гарячий", "гаряча", "гарячу", "гарячою"]
      explanation: "The adjective must agree with чай (masculine): гарячий."
    - sentence: "___, будь ласка, принесіть меню."
      answer: "Прошу"
      options: ["Прошу", "Просити", "Просиш", "Просить"]
      explanation: "Прошу is the first person singular form of просити (to ask/request)."
    - sentence: "Мені ___ тістечко, будь ласка."
      answer: "смачне"
      options: ["смачне", "смачний", "смачна", "смачну"]
      explanation: "Тістечко is neuter — the adjective takes the neuter form: смачне."
    - sentence: "___, будь ласка, каву."
      answer: "Принесіть"
      options: ["Принесіть", "Принести", "Принесу", "Приносити"]
      explanation: "Принесіть is the polite imperative form (Ви) of принести — Bring (the coffee), please."
    - sentence: "Я ___ каву з молоком."
      answer: "замовлю"
      options: ["замовлю", "замовляти", "замовлення", "замовите"]
      explanation: "Замовлю is the first person future form of замовити: I will order."
    - sentence: "Щось ___?"
      answer: "ще"
      options: ["ще", "щось", "вже", "тут"]
      explanation: "Щось ще? means Anything else? — a standard question from café staff."
    - sentence: "Мені ___ каву, будь ласка."
      answer: "міцну"
      options: ["міцну", "міцна", "міцний", "міцною"]
      explanation: "The adjective agrees with каву (Accusative feminine): міцна → міцну."

- type: quiz
  title: "Understand Café Dialogue"
  instruction: "Choose the correct answer about Ukrainian café culture and language."
  items:
    - question: "How do you politely order coffee in Ukrainian?"
      options:
        - text: "Мені, будь ласка, каву."
          correct: true
        - text: "Я хочу кава."
          correct: false
        - text: "Дай мені каву."
          correct: false
        - text: "Кава зараз."
          correct: false
      explanation: "The polite way to order is Мені, будь ласка, каву. Saying Я хочу sounds blunt in Ukrainian."
    - question: "What happens to the word кава when you order it?"
      options:
        - text: "It changes to каву (Accusative case)"
          correct: true
        - text: "It stays as кава"
          correct: false
        - text: "It changes to каві"
          correct: false
        - text: "It changes to кавою"
          correct: false
      explanation: "Feminine nouns ending in -а change to -у in the Accusative case when they become the direct object."
    - question: "You want to ask for the bill. What do you say?"
      options:
        - text: "Рахунок, будь ласка."
          correct: true
        - text: "Чек, будь ласка."
          correct: false
        - text: "Оплата, будь ласка."
          correct: false
        - text: "Гроші, будь ласка."
          correct: false
      explanation: "In Ukrainian restaurants and cafés, you ask for the рахунок (bill). A чек is just the printed fiscal receipt."
    - question: "What does the phrase кава з молоком mean?"
      options:
        - text: "Coffee with milk"
          correct: true
        - text: "Coffee without milk"
          correct: false
        - text: "Coffee with sugar"
          correct: false
        - text: "Black coffee"
          correct: false
      explanation: "З means 'with' and changes the word: молоко → молоком. Memorize кава з молоком as a fixed phrase."
    - question: "Why does чай NOT change its ending when you order it?"
      options:
        - text: "Because masculine inanimate nouns stay the same in the Accusative"
          correct: true
        - text: "Because чай is an indeclinable word"
          correct: false
        - text: "Because чай is neuter"
          correct: false
        - text: "Because you only change feminine words in Ukrainian"
          correct: false
      explanation: "Masculine inanimate nouns keep the same form in the Accusative case. Чай is masculine inanimate."
    - question: "What does the waiter mean by Що ви бажаєте?"
      options:
        - text: "What do you desire? (What would you like?)"
          correct: true
        - text: "Where do you want to sit?"
          correct: false
        - text: "How will you pay?"
          correct: false
        - text: "Are you ready to leave?"
          correct: false
      explanation: "Що ви бажаєте? is a standard polite question from a waiter meaning What would you like?"
    - question: "What is the correct way to say sparkling water?"
      options:
        - text: "Вода з газом"
          correct: true
        - text: "Вода без газу"
          correct: false
        - text: "Вода з цукром"
          correct: false
        - text: "Холодна кава"
          correct: false
      explanation: "Вода з газом means water with gas (sparkling). Вода без газу means still water (without gas)."
    - question: "Who is Yuriy Kulchytskyi and why is he mentioned in Ukrainian café culture?"
      options:
        - text: "A Cossack hero credited with opening one of the first coffeehouses in Europe"
          correct: true
        - text: "A famous Ukrainian barista from Lviv"
          correct: false
        - text: "The inventor of espresso"
          correct: false
        - text: "A Ukrainian tea merchant"
          correct: false
      explanation: "Yuriy Kulchytskyi was a Ukrainian Cossack who opened one of Europe's first coffeehouses after the Battle of Vienna."
    - question: "What does Я буду чай mean?"
      options:
        - text: "I will have tea"
          correct: true
        - text: "I want tea"
          correct: false
        - text: "Give me tea"
          correct: false
        - text: "I am tea"
          correct: false
      explanation: "Я буду... is a polite ordering construction meaning I will have... It is one of the most natural ways to order."
    - question: "How do you say I will pay by card in Ukrainian?"
      options:
        - text: "Я заплачу карткою."
          correct: true
        - text: "Я заплачу картку."
          correct: false
        - text: "Я заплачу картка."
          correct: false
        - text: "Я заплачу картці."
          correct: false
      explanation: "Paying by card changes the word: картка → карткою. Memorize 'Я заплачу карткою' as a fixed phrase."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/at-the-cafe.yaml`

```yaml
items:
  - lemma: "кава"
    translation: "coffee"
    pos: "noun"
    gender: "f"
    usage: "філіжанка кави, міцна кава, кава з молоком"
    notes: "Accusative: каву. Cornerstone of Ukrainian social life, especially in Lviv."
  - lemma: "чай"
    translation: "tea"
    pos: "noun"
    gender: "m"
    usage: "чорний чай, зелений чай, чай з лимоном"
    notes: "Masculine inanimate — does not change in the Accusative case."
  - lemma: "меню"
    translation: "menu"
    pos: "noun"
    gender: "n"
    usage: "принести меню, подивитися меню"
    notes: "Indeclinable borrowed word — never changes its ending."
  - lemma: "рахунок"
    translation: "bill"
    pos: "noun"
    gender: "m"
    usage: "просити рахунок, оплатити рахунок"
    notes: "Not to be confused with чек (fiscal receipt). Always ask for рахунок when paying."
  - lemma: "офіціант"
    translation: "waiter"
    pos: "noun"
    gender: "m"
    usage: "покликати офіціанта, ввічливий офіціант"
  - lemma: "замовляти"
    translation: "to order"
    pos: "verb"
    aspect: "imperfective"
    usage: "я замовляю каву, що ви замовите?"
    notes: "Perfective pair: замовити."
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    usage: "вода з газом, вода без газу, склянка води"
    notes: "Accusative: воду."
  - lemma: "будь ласка"
    translation: "please"
    pos: "noun"
    usage: "Мені, будь ласка...; скажіть, будь ласка"
    notes: "Essential polite phrase used in every ordering situation."
  - lemma: "тістечко"
    translation: "pastry"
    pos: "noun"
    gender: "n"
    usage: "смачне тістечко, шоколадне тістечко"
    notes: "Neuter — does not change in the Accusative."
  - lemma: "картка"
    translation: "card"
    pos: "noun"
    gender: "f"
    usage: "оплатити карткою"
    notes: "Instrumental: карткою. Used for payment by card."
  - lemma: "готівка"
    translation: "cash"
    pos: "noun"
    gender: "f"
    usage: "платити готівкою"
    notes: "Instrumental: готівкою. Traditional payment method."
  - lemma: "чайові"
    translation: "tip"
    pos: "noun"
    usage: "залишати чайові"
    notes: "Plural noun. Standard tip is around 10% of the bill."
  - lemma: "принести"
    translation: "to bring"
    pos: "verb"
    aspect: "perfective"
    usage: "принесіть, будь ласка"
    notes: "Polite imperative: принесіть. Used to request items from staff."
  - lemma: "цукор"
    translation: "sugar"
    pos: "noun"
    gender: "m"
    usage: "кава без цукру"
    notes: "Genitive: цукру (used after без)."
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    usage: "кава з молоком"
    notes: "Instrumental: молоком (used after з)."
  - lemma: "кав'ярня"
    translation: "café, coffeehouse"
    pos: "noun"
    gender: "f"
    usage: "піти до кав'ярні, львівська кав'ярня"
  - lemma: "замовлення"
    translation: "order"
    pos: "noun"
    gender: "n"
    usage: "ваше замовлення, зробити замовлення"
  - lemma: "лимон"
    translation: "lemon"
    pos: "noun"
    gender: "m"
    usage: "чай з лимоном"
    notes: "Instrumental: лимоном."
  - lemma: "бариста"
    translation: "barista"
    pos: "noun"
    usage: "бариста каже, бариста готує каву"
    notes: "Indeclinable borrowed word."
  - lemma: "оплата"
    translation: "payment"
    pos: "noun"
    gender: "f"
    usage: "оплата карткою чи готівкою?"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-cafe.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/at-the-cafe.yaml`

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
