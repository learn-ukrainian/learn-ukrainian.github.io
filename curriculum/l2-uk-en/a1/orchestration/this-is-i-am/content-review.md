# Content Review: this-is-i-am

**Track:** a1 | **Sequence:** 9
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: 2269, target: 1200)
**Verdict:** B

## Plan Adherence

| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Use personal pronouns (я, ти, він, вона, etc.) | YES | Презентація | All 8 pronouns in table |
| Form identity statements without 'to be' (zero copula) | YES | Граматика | Well explained with Ø mapping |
| Use це to point out people and objects | YES | Вступ | Хто це? / Що це? pattern |
| Distinguish masculine/feminine nationality forms | YES | Граматика | українець/українка examples |

### Vocabulary Coverage

| Required Word | In Prose? | In Vocab YAML? | In Activities? |
|--------------|-----------|----------------|----------------|
| це | YES | YES | YES |
| я | YES | YES | YES |
| ти | YES | YES | YES |
| він | YES | YES | YES |
| вона | YES | YES | YES |
| хто | YES | YES | YES |
| що | YES | YES | YES |
| студент/студентка | YES | YES | YES |
| ви (recommended) | YES | YES | NO |
| ми (recommended) | YES | YES | NO |
| вони (recommended) | YES | YES | YES |
| воно (recommended) | YES | YES | YES |
| українець/українка (recommended) | YES | YES | YES |
| вчитель/вчителька (recommended) | YES | YES | YES |
| ось (recommended) | YES | YES | NO |

### Content Outline Adherence

All 5 plan sections are covered. The plan sections "Робота над помилками та практика" and "Продакшн: Хто я і Хто ви?" were restructured to "Робота над помилками: Пастка «Воно»" and "Підсумок та самоперевірка" in the meta outline. The meta outline was followed faithfully. The summary section is significantly oversized (704 words vs 150 target) due to 7 practice dialogues — this is pedagogically beneficial but represents a major deviation from section budgets.

## Linguistic Accuracy

| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| "на роботі" uses locative case | HIGH | Line 182, 194 | The grammar constraints state "FORBIDDEN: all cases except nominative." The phrase "на роботі" is locative case (місцевий відмінок). Also "вдома" is an adverbial form that is fine, but "на роботі" is explicitly case-inflected. This appears in example sentences and vocabulary. |
| "Давай на ти?" uses imperative mood | MEDIUM | Line 127, 304 | The word "давай" is an imperative form of "давати." Constraints say "FORBIDDEN: imperatives." However, this is taught as a memorized phrase (like "Дякую"), not as grammar, which is a reasonable pedagogical choice. |
| "Де стіл?" — "де" not in vocab hints | LOW | Lines 221-234 | The question word "де" (where) is used extensively in the "It Trap" section and dialogues but is not listed in the plan's vocabulary_hints. It is a natural addition though. |

All Ukrainian words verified via VESUM. VESUM misses (Анна, Марія, Ольга, Іван) are proper nouns — expected and not errors.

## Pedagogical Quality

**Lesson Quality Score:** 8/10

**"Would I Continue?" Test:** 4/5
- Overwhelmed? PASS — pacing is comfortable, concepts introduced one at a time
- Instructions clear? PASS — English scaffolding is consistent and clear
- Quick wins? PASS — simple "Це + noun" sentences provide early wins
- Ukrainian scary? PASS — Ukrainian is introduced gently with translations
- Come back tomorrow? FAIL (borderline) — the summary section with 7 dialogues is a LOT for a beginner. Texts 4-7 feel like homework rather than celebration.

**Lesson arc:** WELCOME (hook) -> PRESENT (це, pronouns) -> PRESENT (zero copula) -> PRACTICE (It Trap) -> CONSOLIDATE (dialogues) -> CELEBRATE (self-check). The arc is solid but the consolidation section is disproportionately heavy.

**Cognitive load:** Each section introduces 1-2 concepts before practice. The pronoun table is 8 items at once, which is standard for pronoun introduction. The "It Trap" section effectively reinforces M7 gender concepts.

## Activities Quality

| Activity | Type | Issues |
|----------|------|--------|
| Personal Pronouns | match-up | Clean — 8 pairs, straightforward |
| Grammar and Culture Check | true-false | Clean — 8 items, tests language understanding not content recall |
| Who or What? | fill-in | Clean — 8 items, good хто/що discrimination |
| The It Trap | quiz | Clean — 8 items, tests gender-pronoun mapping |
| Self-Introductions | fill-in | Clean — 8 items, zero copula practice |
| Who vs. What | group-sort | Clean — 11 items, хто/що sorting |
| Complete the Phrase | match-up | MEDIUM: Some pairs are trivially matching (e.g., "Хто" -> "це?", "Що" -> "це?" both end the same way, making it a guess). Also "Дуже" -> "приємно" is the only pair that tests a phrase, not a pattern. |
| Word Scramble | anagram | Clean — 8 items |

Activity variety: 6 types (match-up x2, true-false, fill-in x2, quiz, group-sort, anagram) — good variety.

**Rule 10a check:** Activities test Ukrainian language skills (pronoun matching, gender agreement, хто/що discrimination), not content recall. PASS.

## Engagement

| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | 4 | 3 | PASS |
| Tables | 2 | -- | Good |
| Videos embedded | 0/0 | -- | N/A |

Callout types: [!tip] x2, [!warning] x1, [!culture] x1 — good variety.

## LLM Fingerprint

| Pattern | Found? | Details |
|---------|--------|---------|
| "In this lesson, we will..." | NO | Clean |
| Repetitive transitions | MINOR | "Let us" appears 4 times across sections (L96, L145, L219, L245). Not egregious but slightly formulaic. |
| Generic AI voice | NO | Warm, encouraging tone throughout |
| Word salad | NO | Each paragraph has one clear point |

## Issues Found

### CRITICAL (blocks deployment)
None.

### HIGH (should fix before deployment)
1. **"на роботі" violates nominative-only constraint** — Lines 182, 194. The locative case phrase appears in examples ("Вона на роботі" — She is at work). This is a grammar scope violation per the plan constraints. Either remove these examples or explicitly note that "на роботі" is learned as a memorized chunk, not analyzed grammatically.

### MEDIUM (fix if possible)
1. **Summary section vastly oversized** — 704 words vs 150 target (370% over). The 7 practice dialogues (Texts 1-7) are pedagogically valuable but should be in a separate section or the meta outline should be updated to reflect this. The section budget tolerance is ±10%.
2. **"Давай на ти?" uses imperative** — Borderline. If treated as a memorized social phrase (like "Дякую"), this is acceptable. Should be explicitly marked as a set phrase in the content.
3. **"Complete the Phrase" match-up has ambiguous pairs** — "Хто" -> "це?" and "Що" -> "це?" have identical right-side values, making the match non-unique.

### LOW (informational)
1. **"де" (where) used but not in vocabulary hints** — Added organically, which is fine, but exceeds the plan's vocabulary scope.
2. **"Let us" appears 4 times** — Minor LLM fingerprint; varying sentence openers would improve naturalness.
3. **Research phase recommended IPA** — Contradicts the hard ban; research prompt should reinforce the IPA ban.

## Grade Justification

Grade B. The module is pedagogically strong with clear explanations, good activity variety, and effective use of the zero copula concept. The "на роботі" grammar scope violation is the most significant issue (HIGH), and the massively oversized summary section represents a structural problem. No CRITICAL issues found. The module would benefit from trimming the dialogues and addressing the locative case usage, but is deployable with these fixes.
