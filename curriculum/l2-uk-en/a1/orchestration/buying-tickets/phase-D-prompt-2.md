# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/buying-tickets.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/buying-tickets.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/buying-tickets.yaml`

---

## Review (from Phase D.1)

**Reviewed-By:** claude-opus-4-6

# Рецензія: Buying Tickets

**Level:** A1 | **Module:** 39
**Overall Score:** 7.9/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 5/5 match meta content_outline (Види транспорту та вокзали, Купівля квитка та напрямок, Деталі подорожі: Клас і Розклад, Практика: Діалоги на вокзалі, Подорож поїздом: Традиції)
- Vocabulary: 5/5 required from plan present, 9/9 recommended present, 0 extra. MISSING: "електронний квиток" (plan vocabulary_hints.required mentions it, content has zero coverage)
- Grammar scope: CLEAN — до + Genitive is within scope, no scope creep
- Objectives: 4/4 addressed (buy tickets ✓, specify destination/class ✓, understand ticket info ✓, ask schedules ✓)
- Plan deviations: (1) "електронний квиток (QR-код)" completely absent; (2) plan specifies "Наратив про подорож у Карпати" but reading text is about Odesa; (3) "квиткова каса" and "центральний вокзал" collocations from plan not used; (4) "автовокзал vs залізничний вокзал" reinforcement in practice section missing
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Cold opening at line 11: «Купівля квитків — це просто.» — no greeting, no warmth. Weak motivation box «Це важливо для вас.» (line 15). Good dialogues in section «Практика: Діалоги на вокзалі» partially compensate. |
| 2 | Coherence | 8/10 | <7 | Logical flow: transport types → ticket buying → details → practice → culture. Good section-to-section transitions. Minor: section «Подорож поїздом: Традиції» repeats провідник/постіль info already covered in section «Деталі подорожі: Клас і Розклад». |
| 3 | Relevance | 9/10 | <7 | Highly practical topic for A1 travelers. Covers all essential ticket-buying scenarios. Missing only electronic tickets/QR codes which are now standard for Укрзалізниця. |
| 4 | Educational | 8/10 | <7 | Strong до + Genitive pattern teaching with city examples in section «Купівля квитка та напрямок». Missing "електронний квиток" from plan. 4 dialogues provide excellent practice in section «Практика: Діалоги на вокзалі». |
| 5 | Language | 8/10 | <8 | Ukrainian prose is clean — no Russianisms, no calques. However, bridging sentences in intro are robotic: «Це важливий урок. Ви хочете купити квиток? Ви хочете поїхати до Львова? Це прекрасно. Ви маєте знати слова.» (line 19) — stilted string of simple declarations. |
| 6 | Pedagogy | 8/10 | <7 | PPP structure works. Good Present in sections «Види транспорту та вокзали» and «Купівля квитка та напрямок». Practice dialogues are strong. However, ~1000 words of presentation before first reader-active moment (line 103 "read aloud") is too long for beginners. |
| 7 | Immersion | 7/10 | <6 | 35.9% vs target 35-55%. Within range but barely at the floor. For module 39/44 (A1.4 phase), immersion could be higher. Most sections have only 1-2 Ukrainian bridging sentences before reverting to English. |
| 8 | Activities | 7/10 | <7 | 10 activities with good variety (group-sort, match-up, quiz, fill-in, unjumble). BUT: unjumble activity has systematic comma omissions in 3/6 answers — contradicts the lesson's own emphasis on «будь ласка» as polite formula. |
| 9 | Richness | 8/10 | <6 | Good cultural hooks: підстаканник tradition, плацкарт food-sharing culture, провідник role. 4 situated dialogues. Named cities (Київ, Львів, Одеса, Харків, Умань, Дніпро, Житомир, Херсон, Вінниця). Reading text «Моя подорож» at line 266-269. |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — see Beginner Safety Audit below. Cold opening hurts, but dialogues and closing encouragement («Ви молодець!» line 316) partially recover. |
| 11 | LLM Fingerprint | 7/10 | <7 | 14 identical "Example:" blocks with same formatting pattern. Every content section follows: English paragraph → 1-2 Ukrainian bridging sentences → "Example:" → bulleted Ukrainian sentences. This is unmistakably template-generated. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Prose Ukrainian is grammatically clean. However, unjumble activity answers systematically omit required commas: «Один квиток будь ласка» (should have comma), «Скажіть будь ласка де каса» (needs two commas). Line 179 «Дайте нижнє місце.» contradicts politeness emphasis by omitting "будь ласка". |
| 13 | Factual Accuracy | 9/10 | <8 | Transport descriptions accurate. Підстаканник, купе/плацкарт distinctions correct. Intercity trains box (line 168-169) accurate. [!myth-buster] about train safety (line 300-302) is reasonable. No fabricated claims. |

**Weighted Overall:** (7×1.5 + 8×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 7×1.0 + 7×1.3 + 8×0.9 + 8×1.3 + 7×1.0 + 8×1.5 + 9×1.5) / 15.5 = (10.5 + 8.0 + 9.0 + 9.6 + 8.8 + 9.6 + 7.0 + 9.1 + 7.2 + 10.4 + 7.0 + 12.0 + 13.5) / 15.5 = 121.7 / 15.5 = **7.9/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no Russian-baseline comparisons found
- Grammar scope: [CLEAN] — до + Genitive presented as lexicalized chunks, appropriate for A1
- Activity errors: [3 ISSUES] — unjumble punctuation (see Critical Issue 2)
- Beginner safety: 4/5
- Factual accuracy: [CLEAN]
- **AUTO-FAIL TRIGGERED**: Linguistic Accuracy 8/10 < 9 threshold

## Critical Issues Found

### Issue 1: Cold Opening — No Warm Greeting (Experience Quality / Beginner Safety)
- **Location**: Lines 11-19 / Section «Купівля квитків» (intro before first H2)
- **Original**: «Купівля квитків — це просто.» (line 11) followed by «Це важливо для вас.» (line 15) and «Це важливий урок. Ви хочете купити квиток? Ви хочете поїхати до Львова? Це прекрасно. Ви маєте знати слова. Слухайте і читайте.» (line 19)
- **Problem**: No "Привіт!" or warm greeting. The opening line is a flat declarative statement. The motivation box «Це важливо для вас.» is vague — WHY is it important? The Ukrainian bridging at line 19 reads like a robot: 6 consecutive simple declarations. For module 39 (late A1), a learner should feel welcomed, not lectured.
- **Fix**: Open with "Привіт! Сьогодні ми вчимо нові слова." Replace motivation box with concrete hook: "Imagine you're at the Kyiv train station, ready to explore Ukraine — but you need a ticket first." Replace line 19 with a warmer, more varied bridging paragraph.

### Issue 2: Unjumble Activities — Systematic Comma Omission (Linguistic Accuracy / Activities)
- **Location**: Activities file, unjumble activity (lines 186, 190, 194)
- **Original**: answer: `"Один квиток будь ласка"` (line 186), answer: `"Я хочу нижнє місце будь ласка"` (line 190), answer: `"Скажіть будь ласка де каса"` (line 194)
- **Problem**: All three answers omit commas before/around «будь ласка». The content itself consistently uses the comma: «Один квиток, будь ласка.» (line 70), «Я хочу нижнє місце, будь ласка.» (line 177). This directly contradicts what the lesson teaches and presents incorrect Ukrainian punctuation as the "correct" answer. 3 out of 6 unjumble items are affected.
- **Fix**: Add commas: `"Один квиток, будь ласка"`, `"Я хочу нижнє місце, будь ласка"`, `"Скажіть, будь ласка, де каса"`

### Issue 3: Structural Monotony — 14 Identical "Example:" Blocks (LLM Fingerprint)
- **Location**: Lines 30, 39, 54, 69, 92, 118, 152, 162, 176, 190, 200, 282, 296, 307 — across all sections
- **Original**: Every section follows the pattern: English explanation paragraph → 1-2 Ukrainian bridging sentences → bare `Example:` label → bulleted bold Ukrainian sentences with English translation in parentheses.
- **Problem**: 14 consecutive instances of the exact same structural template. No variation — no "Try these:", no "Here's how it sounds:", no inline examples, no dialogue snippets mixed in. This screams LLM generation.
- **Fix**: Vary example presentation — use inline examples in some sections, "Спробуйте:" or "Прочитайте:" headers in others, integrate some examples directly into the prose rather than as standalone blocks.

### Issue 4: Plan Compliance — Missing "електронний квиток" Coverage
- **Location**: Section «Купівля квитка та напрямок» (lines 58-133)
- **Problem**: The plan (vocabulary_hints.required) explicitly lists "електронний квиток" as required vocabulary. The plan section "Каса та замовлення" point 2 specifies: "Вивчення різниці між «квитковою касою» та «електронним квитком» (QR-код)". The content has ZERO mention of electronic tickets, QR codes, or online booking — which is now the primary way to buy tickets on Укрзалізниця. The collocation "квиткова каса" also doesn't appear.
- **Fix**: Add 3-4 sentences about електронний квиток/QR-код to section «Купівля квитка та напрямок», with an example like "Я маю електронний квиток на телефоні."

### Issue 5: Impolite Example Contradicts Politeness Teaching (Pedagogy)
- **Location**: Line 179 / Section «Деталі подорожі: Клас і Розклад»
- **Original**: «Дайте нижнє місце.» (line 179)
- **Problem**: This bare imperative "Give a lower bunk" without "будь ласка" contradicts the module's own politeness emphasis. The [!note] at line 74-78 and [!tip] at line 262-264 both stress the importance of «будь ласка», yet this example models impolite speech. At A1, learners will internalize whatever examples they see.
- **Fix**: Change to «Дайте нижнє місце, будь ласка.»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 179 | «Дайте нижнє місце.» | «Дайте нижнє місце, будь ласка.» | Pedagogical inconsistency |
| Act. 186 | «Один квиток будь ласка» | «Один квиток, будь ласка» | Punctuation |
| Act. 190 | «Я хочу нижнє місце будь ласка» | «Я хочу нижнє місце, будь ласка» | Punctuation |
| Act. 194 | «Скажіть будь ласка де каса» | «Скажіть, будь ласка, де каса» | Punctuation |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — manageable chunks, vocabulary introduced in small groups (3-5 per subsection)
- Instructions clear? **Pass** — English explanations are clear throughout, grammar table at line 128-132 is excellent
- Quick wins? **Fail** — first reader-active moment is "read aloud" at line 103, approximately 1000 words into the module. No mini-exercise or prompt before that.
- Ukrainian scary? **Pass** — Ukrainian introduced gently with English support. Bridging sentences are short and simple.
- Come back tomorrow? **Pass** — Dialogues in section «Практика: Діалоги на вокзалі» are engaging and practical. Reading text «Моя подорож» (line 269) is delightful. Closing encouragement «Ви молодець!» (line 316) is motivating.

**Emotional beat mapping:**
- Welcome/orientation: WEAK — no greeting, «Це важливо для вас» is flat
- Curiosity trigger: PRESENT — travel to Lviv, Carpathians mentioned in English intro (line 17)
- Quick wins: LATE — first occurs ~halfway through module
- Encouragement: PRESENT — «Це прекрасно» (line 19), «Ви молодець!» (line 316)
- Progress marker: PRESENT — «Тепер ви знаєте все» (line 316), self-check questions (lines 320-326)

## Strengths

- **Excellent dialogue section**: Section «Практика: Діалоги на вокзалі» has 4 well-constructed, realistic dialogues covering different scenarios (train, bus, clarification, information desk). These are the strongest part of the module.
- **Cultural depth**: Section «Подорож поїздом: Традиції» authentically captures Ukrainian train culture — підстаканник, провідник, food-sharing tradition. The paragraph at line 292 «Українці люблять їсти в поїзді. Це наша традиція.» is natural and engaging.
- **Grammar table**: The Direction vs Location comparison table at lines 128-132 in section «Купівля квитка та напрямок» is pedagogically excellent — visual, concise, and immediately clarifies a common confusion.
- **City coverage**: Uses 9 real Ukrainian cities (Київ, Львів, Одеса, Харків, Умань, Дніпро, Житомир, Херсон, Вінниця) providing diverse Genitive pattern practice.
- **Reading text**: «Моя подорож» (line 269) is a gem — short, flowing, uses all key vocabulary in a natural narrative.

## Fix Plan to Reach 9.0/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Activities file line 186: Change answer to `"Один квиток, будь ласка"` — add comma
2. Activities file line 190: Change answer to `"Я хочу нижнє місце, будь ласка"` — add comma
3. Activities file line 194: Change answer to `"Скажіть, будь ласка, де каса"` — add two commas
4. Line 179: Change «Дайте нижнє місце.» → «Дайте нижнє місце, будь ласка.» — consistency with politeness teaching

**Expected score after fix:** 9/10

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Line 11: Replace «Купівля квитків — це просто.» with warm greeting: "Привіт! Сьогодні ви навчитеся купувати квитки."
2. Lines 13-16: Rewrite motivation box with concrete scenario instead of vague «Це важливо для вас.»
3. Line 19: Replace robotic bridging with warmer, varied sentences

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Vary "Example:" labels — use "Спробуйте:", "Прочитайте:", "Ось як це звучить:" for at least 5 of the 14 blocks
2. Integrate 3-4 examples directly into prose paragraphs instead of standalone blocks
3. Open at least 2 sections differently (not English paragraph → Ukrainian bridging → Example:)

**Expected score after fix:** 8/10

### Activities: 7/10 → 8/10
**What to fix:**
1. Fix all 3 unjumble comma issues (see Linguistic Accuracy above)
2. Consider adding comma as a separate token in unjumble word lists for explicit punctuation practice

**Expected score after fix:** 8/10

### Immersion: 7/10 → 8/10
**What to fix:**
1. Add 2-3 more Ukrainian bridging sentences per section (especially in section «Види транспорту та вокзали» and «Деталі подорожі: Клас і Розклад»)
2. Convert some English-only explanations to bilingual (Ukrainian first, English gloss)

**Expected score after fix:** 8/10

### Educational: 8/10 → 9/10
**What to fix:**
1. Add coverage of "електронний квиток" and QR-code in section «Купівля квитка та напрямок» (3-4 sentences + 1 example)
2. Add "квиткова каса" collocation (plan required)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience: 9×1.5=13.5, Coherence: 8×1.0=8.0, Relevance: 9×1.0=9.0
Educational: 9×1.2=10.8, Language: 8×1.1=8.8, Pedagogy: 8×1.2=9.6
Immersion: 8×1.0=8.0, Activities: 8×1.3=10.4, Richness: 8×0.9=7.2
Beginner Safety: 9×1.3=11.7, LLM: 8×1.0=8.0, Linguistic Accuracy: 9×1.5=13.5
Factual Accuracy: 9×1.5=13.5
Total = 132.0 / 15.5 = 8.5/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A1 core track — no research file)
- Key Facts Ledger present: NO
- Dates checked: 0 (no historical dates in content)
- Named figures verified: 0 (no named historical figures)
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: N/A

**Callout box verification (all tracks):**
- [!culture] line 43-47: Вокзал vs станція distinction — **ACCURATE**. Вокзал is indeed used for major terminals; станція for metro/smaller stops.
- [!note] line 74-78: Politeness at ticket window — **ACCURATE**. Naming destination + count + будь ласка is standard.
- [!warning] line 97-101: «квиток до Києва» vs «квиток в Київ» — **ACCURATE** for formal/written context. (Note: colloquially «квиток в Київ» is heard but «до» is standard for tickets.)
- [!fact] line 167-169: Інтерсіті trains — **ACCURATE**. Інтерсіті+ connects Kyiv-Lviv-Kharkiv-Odesa.
- [!tip] line 262-264: «будь ласка» usage — **ACCURATE**.
- [!myth-buster] line 300-302: Train safety — **ACCURATE**. Ukrainian trains are generally safe; food sharing is genuine cultural practice.

## Verification Summary

- Content lines read: 328
- Activity items checked: 65 (across 10 activities)
- Ukrainian sentences verified: 38
- IPA transcriptions checked: 8 (залізничний вокзал, каса, довідка, розклад, в один бік, туди й назад, нижнє місце, верхнє місце)
- Factual claims verified: 6 (all callout boxes)
- Issues found: 5

## Verdict

**FAIL**

Blocking issues: (1) **Linguistic Accuracy 8/10 < 9 auto-fail** — systematic comma omission in 3/6 unjumble activity answers contradicts the lesson's own politeness teaching; (2) **LLM Fingerprint 7/10** — 14 identical "Example:" blocks create unmistakable template monotony; (3) **Plan compliance gap** — required vocabulary item "електронний квиток" completely absent from content. The cold opening without a greeting also hurts beginner safety. Fixes are straightforward: correct activity punctuation, add warm greeting, vary example formatting, add electronic ticket coverage.

---

## Audit Failures (from automated re-audit)

```
Gates:   7 pass, 1 info
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/buying-tickets.md
---
FIND:
exact text to replace (full sentence or paragraph, verbatim from the file)
REPLACE:
corrected replacement text
---
FIND:
next problematic text
REPLACE:
corrected replacement
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/buying-tickets.yaml
---
FIND:
exact activity text to replace
REPLACE:
corrected activity text
---
===SECTION_FIX_END===
```

## Fix Rules

- **FIND text must be verbatim** from the file — use Grep to verify before including
- Only fix issues documented in the review or audit failures above
- You MAY add new activities or modify existing ones if the review's Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the review's Fix Plan explicitly requests it
- Maximum **20 FIND/REPLACE pairs** total (prioritize the most impactful fixes)
- Each FILE: line starts a new sub-block for that file
- If nothing needs fixing, output:
  ```
  ===SECTION_FIX_START===
  ===SECTION_FIX_END===
  ```

---

## Friction Report (MANDATORY)

After the fix block, include:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | FIND_TEXT_MISMATCH | FILE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT modify files directly — only output fix blocks
- You MAY add/modify activities if the review's Fix Plan requests it (use FIND/REPLACE on the YAML file)
- Do NOT make cosmetic changes beyond what the review flagged
