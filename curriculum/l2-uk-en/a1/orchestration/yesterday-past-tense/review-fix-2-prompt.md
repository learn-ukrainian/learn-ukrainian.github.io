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



**NOTE: 8 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 20 items
  - Fix: Add 5 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 6 items
  - Fix: Add 19 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 6 items
  - Fix: Add 14 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities file, all 3 activities, Entire module — all 4 sections, Line 3, Section "Вступ: Що було вчора? (Introduction: What Happened Yesterday?)", Line 67, Section "Складні випадки та практика (Irregular Verbs and Practice)", Lines 44 and 83, Sections "Основи минулого часу (Grammar: Past Tense Formation)" and "Підсумок: Мій день (Summary and Production)", Lines 5 and 67, Sections "Вступ: Що було вчора?" and "Складні випадки та практика (Irregular Verbs and Practice)"

### Finding 1: Spelling Error — "републіка"
**Location**: Line 67, Section "Складні випадки та практика (Irregular Verbs and Practice)"
**Problem**: "републіка" is not a Ukrainian word (VESUM returns NOT FOUND). The correct spelling is "республіка" (with с).
**Required Fix**: Change "републіка" to "республіка"
**Severity**: HIGH

### Finding 2: Anglicism — "робити каву" (make coffee)
**Location**: Lines 44 and 83, Sections "Основи минулого часу (Grammar: Past Tense Formation)" and "Підсумок: Мій день (Summary and Production)"
**Problem**: "робити каву" is a direct English calque of "make coffee". Native Ukrainian speakers say "варити каву" (to brew coffee) or "готувати каву" (to prepare coffee). This is explicitly listed in the A1 Anglicism Lookup: "роблять каву" → "готують каву".
**Required Fix**: Replace "робив каву" → "варив каву" / "готував каву" throughout; update activities and vocabulary file accordingly. NOTE: This calque is present in the **plan itself** (vocabulary_hints and content_outline both use "робити каву"), so this is a plan-level issue that should be reported upstream.
**Severity**: HIGH

### Finding 3: Zero Engagement Boxes
**Location**: Entire module — all 4 sections
**Problem**: Pre-computed audit shows 0 engagement boxes (minimum 1 for A1). Richness score is 54% (threshold 60%). The module reads as a dense wall-of-text with no visual variety.
**Required Fix**: Add at least 2 callout boxes: (1) A `[!tip]` for the "no preposition with минулого" rule (line 16 area), (2) A `[!did-you-know]` or `[!culture-note]` for the Fedorov printing or ЗУНР cultural hook.
**Severity**: HIGH

### Finding 4: Perfective Verbs in A1 Module
**Location**: Lines 5 and 67, Sections "Вступ: Що було вчора?" and "Складні випадки та практика (Irregular Verbs and Practice)"
**Problem**: Research notes explicitly state: "Imperfective aspect ONLY (per A1 quick-ref) — do NOT introduce perfective verbs (прочитав, з'їв)." Both надрукував (perf. of надрукувати) and прийняла (perf. of прийняти) are perfective. These appear in cultural hooks, not drills, which partially mitigates the issue — but the learner may confuse them with the imperfective forms being taught.
**Required Fix**: Add a brief note near each perfective use explaining these are fixed historical phrases, not drill targets. Or rephrase: "Федоров друкував «Апостол» у Львові" (imperfective, emphasizing the process).
**Severity**: HIGH

### Finding 5: LLM Filler Opening
**Location**: Line 3, Section "Вступ: Що було вчора? (Introduction: What Happened Yesterday?)"
**Problem**: Generic LLM-style opening. A real tutor would open with a specific hook, not a formulaic greeting. The module should open with the cultural hook (Fedorov) or a direct question about yesterday.
**Required Fix**: Replace with a more direct, engaging opening: "What did you do yesterday? If you can't answer that question in Ukrainian yet — that's exactly what we're fixing today."
**Severity**: HIGH

### Finding 6: Activity Monotony — All Fill-In
**Location**: Activities file, all 3 activities
**Problem**: Zero variety. Plan specifies 3 fill-in activities with different focuses, which is met, but from a learner experience perspective, 51 items of the exact same type (choose from 4 options) is monotonous. At minimum, one activity should be a different type (match-up pairing masculine/feminine forms, or a sorting activity).
**Required Fix**: Convert one fill-in to a match-up type (e.g., match subject to correct verb form) to break monotony. This is a MEDIUM priority since the plan does specify fill-in only.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Spelling Error — "републіка"
- **Location**: Line 67, Section "Складні випадки та практика (Irregular Verbs and Practice)"
- **Original**: 「Because the word "републіка" (implied by the acronym) is a singular feminine subject」
- **Problem**: "републіка" is not a Ukrainian word (VESUM returns NOT FOUND). The correct spelling is "республіка" (with с).
- **Fix**: Change "републіка" to "республіка"

### Issue 2: Anglicism — "робити каву" (make coffee)
- **Location**: Lines 44 and 83, Sections "Основи минулого часу (Grammar: Past Tense Formation)" and "Підсумок: Мій день (Summary and Production)"
- **Original**: 「Я **робив** каву. — I made coffee. (masculine)」and 「such as **робити каву** (to make coffee)」
- **Problem**: "робити каву" is a direct English calque of "make coffee". Native Ukrainian speakers say "варити каву" (to brew coffee) or "готувати каву" (to prepare coffee). This is explicitly listed in the A1 Anglicism Lookup: "роблять каву" → "готують каву".
- **Fix**: Replace "робив каву" → "варив каву" / "готував каву" throughout; update activities and vocabulary file accordingly. NOTE: This calque is present in the **plan itself** (vocabulary_hints and content_outline both use "робити каву"), so this is a plan-level issue that should be reported upstream.

### Issue 3: Zero Engagement Boxes
- **Location**: Entire module — all 4 sections
- **Original**: No `[!tip]`, `[!did-you-know]`, `[!example]`, `[!cultural-note]`, or any callout box found anywhere.
- **Problem**: Pre-computed audit shows 0 engagement boxes (minimum 1 for A1). Richness score is 54% (threshold 60%). The module reads as a dense wall-of-text with no visual variety.
- **Fix**: Add at least 2 callout boxes: (1) A `[!tip]` for the "no preposition with минулого" rule (line 16 area), (2) A `[!did-you-know]` or `[!culture-note]` for the Fedorov printing or ЗУНР cultural hook.

### Issue 4: Perfective Verbs in A1 Module
- **Location**: Lines 5 and 67, Sections "Вступ: Що було вчора?" and "Складні випадки та практика (Irregular Verbs and Practice)"
- **Original**: 「Федоров надрукував «Апостол»」and 「ЗУНР **прийняла** закон」
- **Problem**: Research notes explicitly state: "Imperfective aspect ONLY (per A1 quick-ref) — do NOT introduce perfective verbs (прочитав, з'їв)." Both надрукував (perf. of надрукувати) and прийняла (perf. of прийняти) are perfective. These appear in cultural hooks, not drills, which partially mitigates the issue — but the learner may confuse them with the imperfective forms being taught.
- **Fix**: Add a brief note near each perfective use explaining these are fixed historical phrases, not drill targets. Or rephrase: "Федоров друкував «Апостол» у Львові" (imperfective, emphasizing the process).

### Issue 5: LLM Filler Opening
- **Location**: Line 3, Section "Вступ: Що було вчора? (Introduction: What Happened Yesterday?)"
- **Original**: 「Welcome back to our journey through the fascinating world of the Ukrainian language!」
- **Problem**: Generic LLM-style opening. A real tutor would open with a specific hook, not a formulaic greeting. The module should open with the cultural hook (Fedorov) or a direct question about yesterday.
- **Fix**: Replace with a more direct, engaging opening: "What did you do yesterday? If you can't answer that question in Ukrainian yet — that's exactly what we're fixing today."

### Issue 6: Activity Monotony — All Fill-In
- **Location**: Activities file, all 3 activities
- **Original**: All three activities are `type: fill-in` with identical interaction pattern
- **Problem**: Zero variety. Plan specifies 3 fill-in activities with different focuses, which is met, but from a learner experience perspective, 51 items of the exact same type (choose from 4 options) is monotonous. At minimum, one activity should be a different type (match-up pairing masculine/feminine forms, or a sorting activity).
- **Fix**: Convert one fill-in to a match-up type (e.g., match subject to correct verb form) to break monotony. This is a MEDIUM priority since the plan does specify fill-in only.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 67 | 「републіка」 | 「республіка」 | Spelling |
| 44 | 「робив каву」 | 「варив каву」 or 「готував каву」 | Anglicism/Calque |
| 83 | 「робити каву」 | 「варити каву」 or 「готувати каву」 | Anglicism/Calque |
| 5 | 「надрукував」 | Consider imperfective or add scope note | Grammar scope |
| 67 | 「прийняла」 | Consider imperfective or add scope note | Grammar scope |

---

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add 2-3 callout boxes: `[!tip]` for the минулого-without-preposition rule, `[!did-you-know]` for cultural hooks
2. Add a mini-practice after the first grammar table (after line 31)
3. Break up wall-of-text in section "Складні випадки та практика (Irregular Verbs and Practice)" with visual separators or sub-headers

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 67: Fix spelling "републіка" → "республіка"
2. Lines 44, 83: Replace "робити/робив каву" → "варити/варив каву" (NOTE: requires plan-level fix upstream)

**Expected score after fix:** 9/10

### Activities: 7/10 → 8/10
**What to fix:**
1. Add at least one non-fill-in activity type (match-up or sorting)
2. This is constrained by plan specifying fill-in only — score limited without plan amendment

**Expected score after fix:** 8/10

### LLM Fingerprint: 7/10 → 9/10
**What to fix:**
1. Line 3: Replace generic opening with direct, specific hook
2. Line 18: Trim motivational filler 「It is incredibly motivating to realize that...」— replace with a concrete preview of what the learner will be able to do

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Fix "републіка" spelling
2. Fix "робити каву" calque
3. Add brief scope notes near perfective verbs in cultural hooks

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 9.6 + 10.4 + 10.4 + 9.0 + 13.5) / 8.9
= 76.3 / 8.9 = 8.6/10
```

---

## Audit Failures (from automated re-audit)

```
❌ YAML schema violations: 1
❌ [YAML_SCHEMA_VIOLATION] Schema error in yesterday-past-tense.yaml: Schema validation error at key '2': {'type': 'match-up', 'title': 'Match the Subject to the Correct Verb Form', 'instruction': 'Match each subject with the correct past tense form of the verb.', 'items': [{'left': 'Він (читати)', 'right': 'читав'}, {'left': 'Вона (читати)', 'right': 'читала'}, {'left': 'Вони (читати)', 'right': 'читали'}, {'left': 'Він (бути)', 'right': 'був'}, {'left': 'Вона (бути)', 'right': 'була'}, {'left': 'Воно (бути)', 'right': 'було'}, {'left': 'Вони (бути)', 'right': 'були'}, {'left': 'Він (їсти)', 'right': 'їв'}, {'left': 'Вона (їсти)', 'right': 'їла'}, {'left': 'Він (йти)', 'right': 'ішов'}, {'left': 'Вона (йти)', 'right': 'йшла'}, {'left': 'Він (пити)', 'right': 'пив'}, {'left': 'Вона (пити)', 'right': 'пила'}, {'left': 'Він (спати)', 'right': 'спав'}, {'left': 'Вона (спати)', 'right': 'спала'}, {'left': 'Він (дивитися)', 'right': 'дивився'}, {'left': 'Вона (дивитися)', 'right': 'дивилася'}, {'left': 'Він (варити)', 'right': 'варив'}, {'left': 'Вона (варити)', 'right': 'варила'}, {'left': 'Вони (ходити)', 'right': 'ходили'}]} is not valid under any of the given schemas
⚠️  English hints in A2+ activities: 1
⚠️ [ENGLISH_HINTS_IN_ACTIVITY] Choose the Correct Gender Ending
📚 IMMERSION TOO LOW (12.6% vs 20-35% target)
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 2 violations
Immersion    ❌ 12.6% LOW (target 20-35% (M36))
📚 PEDAGOGICAL VIOLATIONS FOUND:
[YAML_SCHEMA_VIOLATION] Schema error in yesterday-past-tense.yaml: Schema validation error at key '2': {'type': 'match-up', 'title': 'Match the Subject to the Correct Verb Form', 'instruction': 'Match each subject with the correct past tense form of the verb.', 'items': [{'left': 'Він (читати)', 'right': 'читав'}, {'left': 'Вона (читати)', 'right': 'читала'}, {'left': 'Вони (читати)', 'right': 'читали'}, {'left': 'Він (бути)', 'right': 'був'}, {'left': 'Вона (бути)', 'right': 'була'}, {'left': 'Воно (бути)', 'right': 'було'}, {'left': 'Вони (бути)', 'right': 'були'}, {'left': 'Він (їсти)', 'right': 'їв'}, {'left': 'Вона (їсти)', 'right': 'їла'}, {'left': 'Він (йти)', 'right': 'ішов'}, {'left': 'Вона (йти)', 'right': 'йшла'}, {'left': 'Він (пити)', 'right': 'пив'}, {'left': 'Вона (пити)', 'right': 'пила'}, {'left': 'Він (спати)', 'right': 'спав'}, {'left': 'Вона (спати)', 'right': 'спала'}, {'left': 'Він (дивитися)', 'right': 'дивився'}, {'left': 'Вона (дивитися)', 'right': 'дивилася'}, {'left': 'Він (варити)', 'right': 'варив'}, {'left': 'Вона (варити)', 'right': 'варила'}, {'left': 'Вони (ходити)', 'right': 'ходили'}]} is not valid under any of the given schemas
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
→ 2 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/yesterday-past-tense-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ЗУНР` (source: prose)
  ❌ `ли` (source: prose)
  ❌ `ло` (source: prose)
  ❌ `републіка` (source: prose)
  ❌ `Федоров` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md`

```markdown
## Вступ: Що було вчора? (Introduction: What Happened Yesterday?)

What did you do yesterday? If you can't answer that question in Ukrainian yet, that's exactly what we're fixing today! As your dedicated tutor and part-time museum curator, I love connecting grammar to real life and history. Up until now, we have focused on what is happening right now — the present tense. We learned how to say what you are doing, where you are going, and what you see around you today. But what if you want to talk about what happened **вчора** (yesterday)? What if you want to describe an important historical event, or simply tell your friends about your weekend? To do all of these things, you need the past tense.

In Ukrainian, we have a very clear and distinct contrast between the present and the past. Let's look at a famous event in our history to illustrate this cultural context. On February 15, 1574, Ivan Fedorov "printed" the first book in Lviv, called the Apostol. To say "Fedorov was printing", we use the past tense: Федоров друкував «Апостол». That was a long time ago, but the amazing thing is that the grammatical structure we use to talk about that grand historical event is exactly the same one you will use to describe your morning routine! 

To successfully talk about the past, we rely heavily on specific time expressions. These words set the stage for your story. The most common adverb you will use is **вчора** (yesterday). We also frequently use the adjective **минулий** (past, last) to point to a previous timeframe. Let's see some extremely useful examples:

- **вчора ввечері** — yesterday evening
- **вчора зранку** — yesterday morning
- **тільки вчора** — only yesterday
- **минулого тижня** — last week
- **минулого місяця** — last month
- **минулого року** — last year

Do you notice a very important grammatical detail here? When we say "last week" or "last month" using the word **минулого**, we absolutely do not use the preposition "в" or "у" (in/on). You just use the words directly in the Genitive case. This is a very common mistake for English speakers who try to literally translate "in the past week", so please remember: it is just **минулого тижня**.

> [!tip] No Preposition Needed!
> Unlike English "in the last week", Ukrainian time expressions with **минулого** never use a preposition. Just say **минулого тижня** — no "в" or "у" needed!

With just this one new tense, you will be able to tell friends about your day, report on your weekend, and even describe historical events. Are you ready? Let's learn how to build it!

## Основи минулого часу (Grammar: Past Tense Formation)

> [!did-you-know] 🇺🇦 Cultural Connection
> On February 15, 1574, Ivan Fedorov printed the first book in Lviv — the Apostol. The sentence "Федоров друкував «Апостол»" uses the exact same past tense structure you are about to learn!

Forming the past tense in Ukrainian is surprisingly straightforward, and many students find it much easier than the present tense! According to the State Standard rules for Ukrainian grammar (§4.2.4.1), the past tense is built using what we call the L-participle. Please do not worry about the formal linguistic name; the actual process is incredibly simple. You take the infinitive base of the verb, drop the final **-ти**, and add a specific suffix: **-в**, **-ла**, **-ло**, or **-ли**. 

The absolute most important rule in the Ukrainian past tense is gender agreement. Unlike in the present tense where the verb changes based on the person (I, you, he, she), in the past tense, the verb ending must strictly match the gender of the person or thing doing the action. Let's look at the highly frequent verb **читати** (to read) in a clear table to see these endings in action.

| Subject | Verb Form | English |
|---|---|---|
| Він (Masculine) | **читав** | He read |
| Вона (Feminine) | **читала** | She read |
| Воно (Neuter) | **читало** | It read |
| Вони (Plural) | **читали** | They read |

**Міні-практика (Mini-practice):** Try reading these sentences aloud and notice the endings:

- Він **читав** книгу. Вона **читала** книгу. Вони **читали** книгу.
- Він **був** удома. Вона **була** удома. Вони **були** удома.
- Він **спав**. Вона **спала**. Вони **спали**.

Notice how the feminine form always ends in **-ла**. This brings us to a typical and very frequent error. English speakers often do not think about grammatical gender when talking about themselves because the phrase "I wrote" is exactly the same for everyone. However, in Ukrainian, if a woman says "I wrote", she must correct the masculine phrase "я писав" to the proper feminine form: "я писала". If a woman says "я писав", it sounds like a man is speaking, which can cause confusion. The emphasis on the **-ла** ending for feminine subjects (for example, comparing він читав vs вона читала) is vital for sounding natural. 

Let's look at another example using the verb **працювати** (to work):
- Я **працював** у офісі. — I worked in the office. (masculine speaker)
- Вона **працювала**. — She worked. (feminine speaker)
- Ми **працювали**. — We worked. (plural group)

Another critical warning involves a common calque, or direct literal translation, from English. In English, we often use the past progressive tense to describe an ongoing action: "I was working". In Ukrainian, our imperfective past tense naturally covers both the simple "I worked" and the continuous "I was working". You simply translate "I was working" as "Я **працював**". Never say "Я був працював" just because English uses the word "was". That form is an English calque and is entirely incorrect in modern Ukrainian.

Let's practice this concept with the essential verb **робити** (to do, to make):
- Що ти **робив**? — What did you do? (asking a man)
- Я **варив** каву. — I brewed coffee. (masculine)
- Вона **робила** уроки. — She did homework. (feminine)

And here is the verb **спати** (to sleep), which you will use when talking about your daily routine:
- Він **спав** довго. — He slept long.
- Вона **спала**. — She slept.

As you can see, the core pattern remains perfectly stable. You just need to match the ending to the subject!

## Складні випадки та практика (Irregular Verbs and Practice)

While the vast majority of Ukrainian verbs follow the regular pattern we just discussed, there are a few irregular verbs and cases of suppletion (which means using a completely different root) that you absolutely must know. These are among the most common words in the language, so learning them now will save you a lot of trouble later.

First, let's look at the essential verb **їсти** (to eat). The infinitive looks perfectly normal, but the past tense forms undergo a sudden root vowel change that you need to memorize. 
- Він **їв** обід. — He ate lunch.
- Вона **їла** яблуко. — She ate an apple.
- Ми **їли** в ресторані. — We ate in a restaurant.

### Дієслова руху (Motion Verbs)

Another crucial pair involves verbs of motion, which are central to describing your day. The multidirectional verb **ходити** (to walk, go regularly) is completely regular: він **ходив**, вона **ходила**. However, the unidirectional verb **йти** (to go, walk right now) uses a completely different root for the past tense. This is an important vowel alternation in the root of motion verbs that you will see often.
- Він **ішов** додому. — He was walking home.
- Вона **йшла**. — She was walking.
- Вони **йшли**. — They were walking.

Let's practice these forms in the context of my museum. As a curator, I often describe exhibits, analyze historical events, and guide visitors through the past. Here is a great cultural hook to practice our new grammar: on February 15, 1919, the West Ukrainian People's Republic (ЗУНР) passed a landmark law on the state language. We can proudly say: «ЗУНР **прийняла** закон» (The ZUNR passed a law). Note: **прийняла** is a perfective verb — a fixed historical phrase, not a drill target for this module. You only need to recognize it here, not produce it. Because the word "республіка" (implied by the acronym) is a singular feminine subject, the verb correctly ends in **-ла**.

Let's do a quick drill to clearly distinguish these tricky forms. Notice the sharp contrast between masculine and feminine endings:
- Він **пив** воду. — He drank water.
- Вона **пила** чай. — She drank tea.
- Він **ішов**. — He was walking.
- Вона **йшла**. — She was walking.

### Зворотні дієслова (Reflexive Verbs)

We must also carefully look at the reflexive verb **дивитися** (to watch). Reflexive verbs end in **-ся**, and the rule here is that this reflexive particle stays at the very end of the word, right after the gender ending. 
- Він **дивився** фільм. — He watched a film.
- Вона **дивилася** телевізор. — She watched TV.

By automating your skills through practice drills with foundational verbs like **бути**, **робити**, and **читати**, these patterns will quickly become second nature to you.

## Підсумок: Мій день (Summary and Production)

Now it is your turn for a productive task! It is time to take everything we have learned and use it to talk about your own life. Let's talk about your day and what you did **вчора** (yesterday). I want you to try to create a short story about your previous day using the helpful collocations we studied, such as **варити каву** (to brew coffee), **ішов додому** (was walking home), and **ходила в магазин** (went to the store). 

Imagine this dialog practice with a good friend as you discuss your leisure time and daily activities:

> — Привіт! Що ти **робив** **вчора**?
> — Hello! What did you do yesterday?
> — Я **був** удома. **Дивився** фільм, **читав** новини.
> — I was at home. Watched a film, read the news.
> — А я **ходила** в магазин. 
> — And I went to the store. 
> — Я теж **читав** новини **раніше**.
> — I also read the news earlier.

When you practice writing or speaking, I want you to always perform a final check. Did you use the correct gender and number ending for your verbs? 
- If the subject is masculine, you must use **-в**: він **був**, він **робив**, він **читав**.
- If the subject is feminine, you must use **-ла**: вона **була**, вона **робила**, вона **читала**.
- If the subject is plural, you must use **-ли**: вони **були**, вони **робили**, вони **читали**.

Repeating these rules for gender agreement will prevent the most typical mistakes and make your Ukrainian sound wonderfully natural.

> [!tip] 🎉 You Can Now...
> Tell a friend what you did yesterday, describe your morning routine in the past, and use correct gender endings on past-tense verbs. That's a huge step — keep going!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/yesterday-past-tense.yaml`

```yaml
- type: fill-in
  title: "Change the Verb to Past Tense"
  instruction: "Choose the correct past tense form of the verb in brackets."
  items:
    - sentence: "Він ___ книгу вчора. (читати)"
      answer: "читав"
      options: ["читав", "читала", "читало", "читали"]
      explanation: "Він is masculine, so we use the -в ending: читав."
    - sentence: "Вона ___ каву зранку. (пити)"
      answer: "пила"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "Вона is feminine, so we use the -ла ending: пила."
    - sentence: "Ми ___ в ресторані. (їсти)"
      answer: "їли"
      options: ["їв", "їла", "їло", "їли"]
      explanation: "Ми is plural, so we use the -ли ending: їли."
    - sentence: "Він ___ у офісі. (працювати)"
      answer: "працював"
      options: ["працював", "працювала", "працювало", "працювали"]
      explanation: "Він is masculine, so we use the -в ending: працював."
    - sentence: "Вона ___ фільм. (дивитися)"
      answer: "дивилася"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "Вона is feminine, so we use the -лася ending: дивилася."
    - sentence: "Вони ___ уроки. (робити)"
      answer: "робили"
      options: ["робив", "робила", "робило", "робили"]
      explanation: "Вони is plural, so we use the -ли ending: робили."
    - sentence: "Він ___ довго. (спати)"
      answer: "спав"
      options: ["спав", "спала", "спало", "спали"]
      explanation: "Він is masculine, so we use the -в ending: спав."
    - sentence: "Воно ___ цікаво. (бути)"
      answer: "було"
      options: ["був", "була", "було", "були"]
      explanation: "Воно is neuter, so we use the -ло ending: було."
    - sentence: "Вона ___ газету. (читати)"
      answer: "читала"
      options: ["читав", "читала", "читало", "читали"]
      explanation: "Вона is feminine, so we use the -ла ending: читала."
    - sentence: "Він ___ обід. (їсти)"
      answer: "їв"
      options: ["їв", "їла", "їло", "їли"]
      explanation: "Він is masculine. The irregular past tense of їсти for masculine is їв."
    - sentence: "Вона ___ воду. (пити)"
      answer: "пила"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "Вона is feminine, so we use the -ла ending: пила."
    - sentence: "Він ___ додому. (йти)"
      answer: "ішов"
      options: ["ішов", "йшла", "йшло", "йшли"]
      explanation: "Він is masculine. The irregular past tense of йти for masculine is ішов."
    - sentence: "Вона ___ в магазин. (ходити)"
      answer: "ходила"
      options: ["ходив", "ходила", "ходило", "ходили"]
      explanation: "Вона is feminine, so we use the -ла ending: ходила."
    - sentence: "Він ___ каву. (варити)"
      answer: "варив"
      options: ["варив", "варила", "варило", "варили"]
      explanation: "Він is masculine, so we use the -в ending: варив."
    - sentence: "Вони ___ новини. (читати)"
      answer: "читали"
      options: ["читав", "читала", "читало", "читали"]
      explanation: "Вони is plural, so we use the -ли ending: читали."
    - sentence: "Вона ___ яблуко. (їсти)"
      answer: "їла"
      options: ["їв", "їла", "їло", "їли"]
      explanation: "Вона is feminine. The irregular past tense of їсти for feminine is їла."
    - sentence: "Він ___ удома. (бути)"
      answer: "був"
      options: ["був", "була", "було", "були"]
      explanation: "Він is masculine, so we use the -в ending: був."
    - sentence: "Вона ___ на роботі. (бути)"
      answer: "була"
      options: ["був", "була", "було", "були"]
      explanation: "Вона is feminine, so we use the -ла ending: була."
    - sentence: "Він ___ фільм. (дивитися)"
      answer: "дивився"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "Він is masculine, so we use the -вся ending: дивився."
    - sentence: "Вони ___ чай. (пити)"
      answer: "пили"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "Вони is plural, so we use the -ли ending: пили."
    - sentence: "Він ___ книжку. (писати)"
      answer: "писав"
      options: ["писав", "писала", "писало", "писали"]
      explanation: "Він is masculine, so we use the -в ending: писав."
    - sentence: "Вона ___. (спати)"
      answer: "спала"
      options: ["спав", "спала", "спало", "спали"]
      explanation: "Вона is feminine, so we use the -ла ending: спала."
    - sentence: "Вони ___ в магазині. (купувати)"
      answer: "купували"
      options: ["купував", "купувала", "купувало", "купували"]
      explanation: "Вони is plural, so we use the -ли ending: купували."
    - sentence: "Він ___ вечерю. (готувати)"
      answer: "готував"
      options: ["готував", "готувала", "готувало", "готували"]
      explanation: "Він is masculine, so we use the -в ending: готував."
    - sentence: "Вона ___ вчора ввечері. (гуляти)"
      answer: "гуляла"
      options: ["гуляв", "гуляла", "гуляло", "гуляли"]
      explanation: "Вона is feminine, so we use the -ла ending: гуляла."

- type: fill-in
  title: "Choose the Correct Gender Ending"
  instruction: "Read the sentence and select the verb form that matches the gender of the subject."
  items:
    - sentence: "Мама ___ обід."
      answer: "готувала"
      options: ["готував", "готувала", "готувало", "готували"]
      explanation: "Мама is feminine, so the verb takes the -ла ending."
    - sentence: "Тато ___ газету."
      answer: "читав"
      options: ["читав", "читала", "читало", "читали"]
      explanation: "Тато is masculine, so the verb takes the -в ending."
    - sentence: "Діти ___ в магазин."
      answer: "ходили"
      options: ["ходив", "ходила", "ходило", "ходили"]
      explanation: "Діти is plural, so the verb takes the -ли ending."
    - sentence: "Сестра ___ каву."
      answer: "пила"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "Сестра is feminine, so the verb takes the -ла ending."
    - sentence: "Брат ___ фільм."
      answer: "дивився"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "Брат is masculine, so the verb takes the -вся ending."
    - sentence: "Друзі ___ в ресторані."
      answer: "їли"
      options: ["їв", "їла", "їло", "їли"]
      explanation: "Друзі is plural, so the verb takes the -ли ending."
    - sentence: "Бабуся ___ удома."
      answer: "була"
      options: ["був", "була", "було", "були"]
      explanation: "Бабуся is feminine, so the verb takes the -ла ending."
    - sentence: "Я (a man) ___ новини."
      answer: "читав"
      options: ["читав", "читала", "читало", "читали"]
      explanation: "When a man says I (я), the past tense verb takes the masculine -в ending."
    - sentence: "Я (a woman) ___ у офісі."
      answer: "працювала"
      options: ["працював", "працювала", "працювало", "працювали"]
      explanation: "When a woman says I (я), the past tense verb takes the feminine -ла ending."
    - sentence: "Дідусь ___ довго."
      answer: "спав"
      options: ["спав", "спала", "спало", "спали"]
      explanation: "Дідусь is masculine, so the verb takes the -в ending."
    - sentence: "Подруга ___ в магазин."
      answer: "ходила"
      options: ["ходив", "ходила", "ходило", "ходили"]
      explanation: "Подруга is feminine, so the verb takes the -ла ending."
    - sentence: "Учитель ___ книжку."
      answer: "писав"
      options: ["писав", "писала", "писало", "писали"]
      explanation: "Учитель is masculine, so the verb takes the -в ending."
    - sentence: "Ми ___ каву."
      answer: "пили"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "Ми is plural, so the verb takes the -ли ending."
    - sentence: "Студентка ___ уроки."
      answer: "робила"
      options: ["робив", "робила", "робило", "робили"]
      explanation: "Студентка is feminine, so the verb takes the -ла ending."
    - sentence: "Він ___ додому."
      answer: "ішов"
      options: ["ішов", "йшла", "йшло", "йшли"]
      explanation: "Він is masculine. The irregular past tense of йти for masculine is ішов."
    - sentence: "Вона ___ телевізор."
      answer: "дивилася"
      options: ["дивився", "дивилася", "дивилося", "дивилися"]
      explanation: "Вона is feminine, so the reflexive verb takes the -лася ending."
    - sentence: "Вони ___ вечерю."
      answer: "готували"
      options: ["готував", "готувала", "готувало", "готували"]
      explanation: "Вони is plural, so the verb takes the -ли ending."
    - sentence: "Хлопець ___ воду."
      answer: "пив"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "Хлопець is masculine, so the verb takes the -в ending."
    - sentence: "Дівчина ___ яблуко."
      answer: "їла"
      options: ["їв", "їла", "їло", "їли"]
      explanation: "Дівчина is feminine. The irregular past tense of їсти for feminine is їла."
    - sentence: "Ми ___ удома."
      answer: "були"
      options: ["був", "була", "було", "були"]
      explanation: "Ми is plural, so the verb takes the -ли ending."
    - sentence: "Онук ___ у парку."
      answer: "гуляв"
      options: ["гуляв", "гуляла", "гуляло", "гуляли"]
      explanation: "Онук is masculine, so the verb takes the -в ending."
    - sentence: "Сусідка ___ вечерю."
      answer: "готувала"
      options: ["готував", "готувала", "готувало", "готували"]
      explanation: "Сусідка is feminine, so the verb takes the -ла ending."
    - sentence: "Кіт ___ довго."
      answer: "спав"
      options: ["спав", "спала", "спало", "спали"]
      explanation: "Кіт is masculine, so the verb takes the -в ending."
    - sentence: "Дівчата ___ чай."
      answer: "пили"
      options: ["пив", "пила", "пило", "пили"]
      explanation: "Дівчата is plural, so the verb takes the -ли ending."
    - sentence: "Донька ___ каву."
      answer: "варила"
      options: ["варив", "варила", "варило", "варили"]
      explanation: "Донька is feminine, so the verb takes the -ла ending."

- type: match-up
  title: "Match the Subject to the Correct Verb Form"
  instruction: "Match each subject with the correct past tense form of the verb."
  items:
    - left: "Він (читати)"
      right: "читав"
    - left: "Вона (читати)"
      right: "читала"
    - left: "Вони (читати)"
      right: "читали"
    - left: "Він (бути)"
      right: "був"
    - left: "Вона (бути)"
      right: "була"
    - left: "Воно (бути)"
      right: "було"
    - left: "Вони (бути)"
      right: "були"
    - left: "Він (їсти)"
      right: "їв"
    - left: "Вона (їсти)"
      right: "їла"
    - left: "Він (йти)"
      right: "ішов"
    - left: "Вона (йти)"
      right: "йшла"
    - left: "Він (пити)"
      right: "пив"
    - left: "Вона (пити)"
      right: "пила"
    - left: "Він (спати)"
      right: "спав"
    - left: "Вона (спати)"
      right: "спала"
    - left: "Він (дивитися)"
      right: "дивився"
    - left: "Вона (дивитися)"
      right: "дивилася"
    - left: "Він (варити)"
      right: "варив"
    - left: "Вона (варити)"
      right: "варила"
    - left: "Вони (ходити)"
      right: "ходили"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/yesterday-past-tense.yaml`

```yaml
items:
  - lemma: "вчора"
    translation: "yesterday"
    pos: "adverb"
    usage: "вчора ввечері, вчора зранку, тільки вчора"
    notes: "High frequency adverb (Top 100). The most common time word for past events."
  - lemma: "бути"
    translation: "to be"
    pos: "verb"
    aspect: "imperfective"
    usage: "був удома, була на роботі, було цікаво"
    notes: "Very High frequency (Top 10). Past tense forms are irregular: був/була/було/були."
  - lemma: "робити"
    translation: "to do, to make"
    pos: "verb"
    aspect: "imperfective"
    usage: "робити уроки, що ти робив?"
    notes: "Very High frequency (Top 20). Regular past tense: робив/робила/робило/робили."
  - lemma: "їсти"
    translation: "to eat"
    pos: "verb"
    aspect: "imperfective"
    usage: "їв обід, вона їла яблуко, ми їли в ресторані"
    notes: "Irregular past tense forms: їв/їла/їло/їли (root vowel change)."
  - lemma: "пити"
    translation: "to drink"
    pos: "verb"
    aspect: "imperfective"
    usage: "пив воду, вона пила чай"
    notes: "High frequency verb. Past tense: пив/пила/пило/пили."
  - lemma: "читати"
    translation: "to read"
    pos: "verb"
    aspect: "imperfective"
    usage: "читав книгу, читала новини"
    notes: "High frequency (Top 50). Regular past tense: читав/читала/читало/читали."
  - lemma: "дивитися"
    translation: "to watch"
    pos: "verb"
    aspect: "imperfective"
    usage: "дивився фільм, дивилася телевізор"
    notes: "Reflexive verb. The -ся particle stays at the end after the gender suffix."
  - lemma: "ходити"
    translation: "to go, to walk (regularly)"
    pos: "verb"
    aspect: "imperfective"
    usage: "ходила в магазин, ходив на роботу"
    notes: "Multidirectional motion verb. Regular past tense: ходив/ходила/ходило/ходили."
  - lemma: "минулий"
    translation: "last, past"
    pos: "adjective"
    usage: "минулого тижня, минулого року, минулої ночі"
    notes: "Used without preposition в/у. Genitive form: минулого (masc/neut), минулої (fem)."
  - lemma: "раніше"
    translation: "earlier"
    pos: "adverb"
    usage: "Я теж читав новини раніше."
    notes: "Common time adverb used in past tense contexts."
  - lemma: "тиждень"
    translation: "week"
    pos: "noun"
    gender: "m"
    usage: "минулого тижня"
    notes: "Genitive: тижня. Used in the expression минулого тижня (last week)."
  - lemma: "місяць"
    translation: "month"
    pos: "noun"
    gender: "m"
    usage: "минулого місяця"
    notes: "Genitive: місяця. Used in the expression минулого місяця (last month)."
  - lemma: "спати"
    translation: "to sleep"
    pos: "verb"
    aspect: "imperfective"
    usage: "спав довго, вона спала"
    notes: "Regular past tense: спав/спала/спало/спали."
  - lemma: "працювати"
    translation: "to work"
    pos: "verb"
    aspect: "imperfective"
    usage: "працював у офісі, вона працювала"
    notes: "Regular past tense: працював/працювала/працювало/працювали."
  - lemma: "йти"
    translation: "to go, to walk (in one direction)"
    pos: "verb"
    aspect: "imperfective"
    usage: "ішов додому, вона йшла"
    notes: "Unidirectional motion verb. Irregular past tense: ішов/йшла/йшло/йшли."
  - lemma: "писати"
    translation: "to write"
    pos: "verb"
    aspect: "imperfective"
    usage: "писав книжку, вона писала"
    notes: "Regular past tense: писав/писала/писало/писали."
  - lemma: "варити"
    translation: "to brew, to cook (liquids)"
    pos: "verb"
    aspect: "imperfective"
    usage: "варив каву, варила чай"
    notes: "Regular past tense: варив/варила/варило/варили. Native Ukrainian for brewing coffee (NOT робити каву)."
  - lemma: "готувати"
    translation: "to cook, to prepare"
    pos: "verb"
    aspect: "imperfective"
    usage: "готував вечерю, вона готувала обід"
    notes: "Regular past tense: готував/готувала/готувало/готували."
  - lemma: "купувати"
    translation: "to buy"
    pos: "verb"
    aspect: "imperfective"
    usage: "купував у магазині, вона купувала"
    notes: "Regular past tense: купував/купувала/купувало/купували."
  - lemma: "гуляти"
    translation: "to walk, to stroll"
    pos: "verb"
    aspect: "imperfective"
    usage: "гуляв у парку, вона гуляла вчора ввечері"
    notes: "Regular past tense: гуляв/гуляла/гуляло/гуляли."
  - lemma: "додому"
    translation: "home (direction), homeward"
    pos: "adverb"
    usage: "ішов додому, ходила додому"
    notes: "Adverb of direction. Means going towards home."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/yesterday-past-tense.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/yesterday-past-tense.yaml`

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
