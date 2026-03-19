# Рецензія: Direction and Origin

**Level:** A1 | **Module:** 35
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PASS (with minor deviations)
- Sections: All 5 plan sections present as H2 headers (+ Підсумок as bonus)
- Vocabulary: 10/10 required present in prose, 4/4 recommended present; 20 total in vocab file
- Grammar scope: CLEAN — no scope creep beyond A1.4
- Objectives: All 4 objectives addressed
- Activity hints: 4/4 types present with correct item counts (fill-in:12, quiz:10, match-up:10, unjumble:8≥6)
```

### Plan Adherence Checklist

**Section "Куди? + Знахідний":**
- Direction with в/у + Accusative: COVERED — lines 9-10 「Я іду в магазин」, 「Я їду у Львів」
- Direction with на + Accusative: COVERED — lines 16-18
- Key contrast drill Де? vs Куди?: COVERED — lines 22-27

**Section "До + Родовий":**
- До + Genitive for person/institution: COVERED — lines 38-39, 43-44
- Semantic difference в/у/на vs до: COVERED — line 46 (uses аптеку instead of plan's лікарню per builder deviation — acceptable)
- Common collocations: COVERED — line 48 (до дому, до брата, до школи)

**Section "Звідки? + Родовий":**
- Origin з/із/зі + Genitive: COVERED — lines 58-60
- Від + Genitive for person: PARTIAL — plan says "Лист від мами, Подарунок від друга" but content uses "Книжка від мами, Кава від брата" (builder deviation: лист/подарунок not in cumulative A1 vocab). Acceptable substitution.
- Euphonic з/із/зі rules per Pravopys §25: COVERED — lines 68-74 table. BUT table has errors (see Critical Issues).

**Section "Три питання":**
- Three-question paradigm: COVERED — lines 82-84, 86-99
- Same place, three perspectives: COVERED — lines 103-105
- Summary table: COVERED — lines 109-114

**Section "Практика":**
- Direction/origin dialogues: COVERED — lines 126-144
- Three-question transformation drills: COVERED — lines 148-156

**Pronunciation videos:** Plan has none specified; module includes 1 video embed (line 118-120) — fine.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm conductor persona, good arc, but NO engagement callout boxes and immersion far too low |
| 2 | Language | 7/10 | <8 | Euphony table contains factual errors (із лісу wrong, зі rule oversimplified); vocabulary file has ungrammatical usage examples |
| 3 | Pedagogy | 8/10 | <7 | Strong PPP flow, excellent contrast drills (Де?/Куди?), but lacks engagement boxes for variety |
| 4 | Activities | 7/10 | <7 | Activity line 36 teaches fabricated euphony rule ("Л + consonant cluster"); otherwise solid coverage |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 4/5 — warm, encouraging, manageable pacing; slightly too dense in section "Звідки? + Родовий" |
| 6 | LLM Fingerprint | 8/10 | <7 | Some filler phrases (「language muscles」, 「miles ahead in your fluency」) but generally natural tutor voice |
| 7 | Linguistic Accuracy | 7/10 | <9 | Euphony table error (із лісу); fabricated rule in activity; vocabulary usage has infinitives instead of conjugated forms |

**Weighted Overall:** (8×1.5 + 7×1.1 + 8×1.2 + 7×1.3 + 9×1.3 + 8×1.0 + 7×1.5) / 8.9 = (12 + 7.7 + 9.6 + 9.1 + 11.7 + 8.0 + 10.5) / 8.9 = 68.6 / 8.9 = **7.7/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no Russianisms detected
- Calques: CLEAN
- Colonial framing: CLEAN — no "Unlike Russian..." patterns
- Grammar scope: CLEAN — all grammar within A1.4 scope
- Activity errors: 1 found — fabricated euphony rule in explanation (line 36)
- Beginner safety: 4/5
- Factual accuracy: 2 issues — superlative claim about melodic language; euphony table errors

### D.0 Pre-Screen Disposition

1. **[IPA_BANNED]** — DISMISSED (false positive). Line 120 contains 「[Watch on YouTube](https://www.youtube.com/watch?v=QhKN_tj05Rg)」 — this is a markdown link, not IPA transcription. The square brackets are part of markdown link syntax.

2. **[ACTIVITY_VESUM_FAIL]** — DISMISSED (false positive). Both Києва and Львова are valid VESUM forms — verified as Genitive of Київ and Львів respectively.

### D.0 Word Verification Disposition

- `Києва` — VALID (Genitive of Київ, confirmed VESUM)
- `Львова` — VALID (Genitive of Львів, confirmed VESUM)
- `ш` and `щ` — DISMISSED (not standalone words; extracted from activity explanation text mentioning "ш-/щ-/з-/с-" sounds)

## Critical Issues Found

### Issue 1: Euphony Table Error — із лісу
- **Location**: Line 73, Section "Звідки? + Родовий"
- **Original**: 「**із** | sibilants or clusters | **із села**, **із лісу**」
- **Problem**: Per Pravopys §25.2, "із" is used before sibilants (з, с, ц, ч, ш, шч) and between consonant clusters. "Село" starts with "с" (sibilant) — correct. But "ліс" starts with "л" — NOT a sibilant and NOT a cluster. The standard form is "з лісу", not "із лісу".
- **Fix**: Replace "із лісу" with a correct example like "із заходу" or "із Сум".

### Issue 2: Euphony Table Oversimplification — зі rule
- **Location**: Line 74, Section "Звідки? + Родовий"
- **Original**: 「**зі** | words starting with з-, с-, ш-, щ- | **зі школи**, **зі столу**」
- **Problem**: The table says зі is used only before з-/с-/ш-/щ- initial words, but the content itself uses 「Вона зі Львова.」 on line 60 — Львів starts with Л, not з/с/ш/щ. Pravopys §25.3 explicitly gives "Прибув зі Львова" as a correct example, and uses the phrase "та ін." (and others) indicating зі applies more broadly to difficult consonant clusters. The table should reflect this.
- **Fix**: Change the зі description to "words starting with з-, с-, ш-, щ- and difficult clusters" and add "зі Львова" as an example.

### Issue 3: Fabricated Euphony Rule in Activity
- **Location**: Activities file, line 36
- **Original**: `explanation: "We use зі before words starting with Л + consonant cluster (Львів → зі Львова)."`
- **Problem**: This invents a non-existent rule ("Л + consonant cluster"). The Pravopys §25.3 explains зі is used before difficult initial consonant clusters (including Львів) — it never mentions "Л + consonant cluster" as a specific rule category. This will teach learners a wrong generalization.
- **Fix**: Change to: "Pravopys §25 uses зі before difficult initial consonant clusters. Львів starts with Льв-, a difficult cluster, so we say зі Львова."

### Issue 4: Vocabulary Usage — Unconjugated Verbs
- **Location**: Vocabulary file, lines 73 and 79
- **Original**: `usage: "Я повертатися додому."` and `usage: "Він виходити з дому."`
- **Problem**: These usage examples use infinitives instead of conjugated forms. A learner reading "Я повертатися" will learn ungrammatical Ukrainian. The correct forms are "Я повертаюся додому" and "Він виходить з дому."
- **Fix**: Conjugate the verbs in usage examples.

### Issue 5: Zero Engagement Boxes — Audit Gate Failure
- **Location**: Entire content file
- **Problem**: The module has 0 engagement boxes (`[!did-you-know]`, `[!tip]`, `[!culture]`, etc.). The audit requires ≥2. The module also has only 1 video embed. This fails the richness gate (engagement: 0/2, video_embeds: 1/2).
- **Fix**: Add at least 2 engagement callout boxes. Suggestions: (1) A `[!did-you-know]` about Ukrainian Railways (Укрзалізниця) — naturally fits the conductor persona and direction theme. (2) A `[!tip]` about the в/у euphony alternation before the first section.

### Issue 6: Підсумок Uses H1 Instead of H2
- **Location**: Line 163
- **Original**: 「# Підсумок」
- **Problem**: All section headers should be H2 (`##`). Using H1 breaks the document structure hierarchy.
- **Fix**: Change to `## Підсумок`

### Issue 7: Superlative Factual Claim
- **Location**: Line 68, Section "Звідки? + Родовий"
- **Original**: 「Our language is often called one of the most melodic in the world, and this rule is exactly why.」
- **Problem**: The claim "one of the most melodic in the world" is an unverifiable superlative. While Ukrainian IS melodic, this specific claim (often attributed to a dubious 1934 Paris linguists congress) has no reliable sourcing. At A1, superlatives about language beauty risk seeming like propaganda rather than fact.
- **Fix**: Rephrase to something factual: "Ukrainian values smooth, flowing speech, and this rule shows how the language achieves that."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 73 | 「із лісу」 | із Сум / із заходу | Grammar (wrong euphony example) |
| vocab:73 | 「Я повертатися додому.」 | Я повертаюся додому. | Grammar (unconjugated verb) |
| vocab:79 | 「Він виходити з дому.」 | Він виходить з дому. | Grammar (unconjugated verb) |
| act:36 | "Л + consonant cluster" rule | Pravopys §25 difficult cluster rule | Factual (fabricated rule) |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is manageable, sections are well-sized
- Instructions clear? **Pass** — always know what to do next
- Quick wins? **Pass** — early examples are simple and pattern-based
- Ukrainian scary? **Pass** — introduced with English support throughout
- Come back tomorrow? **Borderline Pass** — the module lacks engagement variety (no callout boxes, no fun-facts), which makes it feel more like a textbook than a tutoring session. The conductor persona is charming but underutilized.

## Strengths
- **Excellent three-question paradigm teaching**: Section "Три питання" with the Марія dialogue (lines 86-99) is pedagogically brilliant — same noun, three forms, clear visual contrast
- **Strong contrast drills**: The Де?/Куди? pairs on lines 22-27 directly target the #1 learner error
- **Well-structured activities**: 40 activity items across 4 types with good coverage of all module objectives
- **Builder deviations were smart**: Replacing лікарня→аптека and лист→книжка for cumulative vocabulary consistency shows good pedagogical awareness
- **Conductor persona**: The train journey metaphor is warm and consistent throughout

## Fix Plan to Reach 9/10 (REQUIRED)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 73: Fix euphony table — replace "із лісу" with "із Сум" (с = sibilant, correct per §25.2)
2. Line 74: Expand зі description to "words starting with з-, с-, ш-, щ- and difficult clusters (e.g., Льв-)" and add "зі Львова" as example
3. Activities line 36: Replace fabricated "Л + consonant cluster" explanation with accurate Pravopys §25 reference
4. Vocabulary lines 73, 79: Conjugate verbs in usage examples

**Expected score after fix:** 9/10

### Language: 7/10 → 9/10
**What to fix:**
1. Fix euphony table errors (same as Linguistic Accuracy #1-2)
2. Fix vocabulary usage (same as Linguistic Accuracy #4)
3. Line 68: Remove unverifiable "most melodic" superlative

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add 2 engagement callout boxes: `[!did-you-know]` about Укрзалізниця (fits conductor persona), `[!tip]` about в/у alternation
2. Line 163: Fix `# Підсумок` → `## Підсумок`

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Fix fabricated euphony rule explanation (activities line 36)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 8×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 9.6 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 77.9 / 8.9 = 8.8/10
```

## Verification Summary

- Content lines read: 175
- Activity items checked: 40 (12 fill-in + 10 quiz + 10 match-up + 8 unjumble)
- Ukrainian sentences verified: 28
- Citations in bank: 15
- Issues found: 7

## Verdict

**FAIL**

Blocking issues: (1) Euphony table contains factual error (із лісу) and oversimplification (зі rule) — teaches wrong rules. (2) Activity explanation fabricates a non-existent "Л + consonant cluster" rule. (3) Vocabulary file has ungrammatical usage examples (unconjugated verbs). (4) Zero engagement boxes fails audit richness gate.