# Content Review: the-gender-code

**Track:** a1 | **Sequence:** 7
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: 2867, target: 1200)
**Verdict:** B

## Plan Adherence
| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Identify noun gender by word ending | YES | Презентація правил | Thorough coverage with tables and examples |
| Categorize nouns into 4 declension families | YES | Практичні вправи | Families 1-4 each get dedicated subsections |
| Recognize patterns: consonant (m), -а/-я (f), -о/-е (n) | YES | Презентація правил | Clear comparison table at end of section |
| Identify common exceptions | YES | Практичні вправи + Самостійна робота | тато, ніч, ім'я, собака all covered |

### Vocabulary Coverage
| Required Word | In Prose? | In Vocab YAML? | In Activities? |
|--------------|-----------|----------------|----------------|
| брат | YES | YES | YES (quiz, anagram) |
| сестра | YES | YES | YES (anagram, group-sort) |
| мама | YES | YES | YES (anagram) |
| тато | YES | YES | YES (fill-in, true-false, quiz) |
| дім | YES | YES | YES (quiz, match-up, anagram) |
| вікно | YES | YES | YES (quiz, match-up, fill-in) |
| книга | YES | YES | YES (quiz, group-sort) |
| місто | YES | YES | YES (group-sort, match-up, fill-in) |

All 8 required vocabulary items present across all three locations.

## Linguistic Accuracy
| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| собака gender claim | HIGH | Практичні вправи, line ~197 | Module states "собака is Masculine by default in standard Ukrainian." VESUM lists собака as BOTH m and f (noun:anim:m:v_naz and noun:anim:f:v_naz). Standard dictionaries (SUM, Hrinchenko) list it as feminine. The vocab YAML correctly marks it as gender: f. The prose contradicts the vocabulary file. The standard form is "моя собака" (feminine). Saying "мій собака" is dialectal/colloquial, not standard. |
| татою form | MEDIUM | Практичні вправи, line ~213 | Module claims "The instrumental case confirms this: татом (like містом), not татою." The form "татою" does not exist in VESUM. This is correct -- the point being made is valid (тато takes -ом not -ою) -- but presenting a non-existent form even to negate it may confuse beginners. |
| Scope violation: instrumental case | LOW | Практичні вправи, line ~213 | Module discusses instrumental case forms (татом, містом) but GRAMMAR STATUS says "Instrumental case FORBIDDEN." Used for illustrative purposes but still technically out of scope. |
| Adjective forms beyond scope | LOW | Multiple locations | Uses добрий день, великий стіл, цікава книга, etc. This is explicitly allowed by the M7 exception ("Adjective agreement examples allowed to demonstrate what gender does"), so this is not a violation -- but it's worth noting the module relies heavily on adjective phrases. |

## Pedagogical Quality
**Lesson Quality Score:** 8/10

**Tier-1 "Would I Continue?" Test:**
- Did I feel overwhelmed? PASS -- pacing is comfortable, progressive
- Were instructions clear? PASS -- English scaffolding throughout
- Did I get quick wins? PASS -- early practice exercises after each gender
- Was Ukrainian scary? PASS -- Ukrainian introduced gently with translations
- Would I come back tomorrow? PASS -- encouraging, practical, S.T.A.L.K.E.R. hook engaging

**Score: 5/5 = Lesson Quality 10/10 on tier rubric, capped at 8 due to pedagogical concern:**
The module is substantially over target (2867 vs 1200 words). While this is not a failing gate, it means a beginner encounters 2.4x the expected cognitive load. The declension families section (Families 1-4) introduces complex linguistic taxonomy that may overwhelm a true A1 learner. The "собака is masculine" claim adds confusion rather than clarity.

## Activities Quality
| Activity | Type | Issues |
|----------|------|--------|
| Sort the Nouns by Gender | group-sort | Clean, 12 items, well-designed |
| Identify the Gender | quiz | 8 items, all correct. "Not applicable" distractor is weak. |
| True or False: Gender Rules | true-false | 8 items. **собака item states it is "grammatically Feminine"** -- contradicts the prose which says masculine. The activity is correct per standard Ukrainian; the prose is wrong. |
| The 'My' Test | match-up | 8 pairs, all correct |
| Complete the Phrases | fill-in | 8 items, all correct. собака item uses "моя" (correct). |
| Unscramble Core Vocabulary | anagram | 8 items, letter counts verified |
| Spot the Gender Exceptions | quiz | 8 items, well-designed exception-focused questions |
| Harmonious Patterns | group-sort | 12 items using adjective+noun phrases -- good reinforcement |

**Activity variety:** 6 unique types (group-sort, quiz, true-false, match-up, fill-in, anagram) -- excellent.

## Engagement
| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | 9 | 3 | PASS |
| Tables | 1 | -- | Present |
| Videos embedded | 0/0 | -- | N/A |

## Issues Found

### CRITICAL (blocks deployment)
(none)

### HIGH (should fix before deployment)
1. **собака gender inconsistency**: The prose (line ~197) claims собака is "Masculine by default in standard Ukrainian" and uses "мій собака." Standard dictionaries and VESUM both list собака as feminine (noun:anim:f:v_naz). The vocabulary YAML correctly lists gender: f. The activities correctly use "моя собака." The prose must be corrected to match: собака is grammatically feminine in standard Ukrainian. "Моя собака" is correct.

### MEDIUM (fix if possible)
1. **Instrumental case out of scope**: Line ~213 discusses instrumental forms (татом, містом, татою). The grammar constraints say "Instrumental case FORBIDDEN." While used for illustration, this introduces case forms that aren't taught yet.
2. **Module length 2.4x target**: At 2867 words vs 1200 target, the module is substantially longer than planned. Not a failing gate but increases cognitive load for beginners.

### LOW (informational)
1. **Mini-dialogues use verb forms**: The Cafe dialogue uses "де" (where) which is fine, but the question pattern "А де мій чай?" contains verb-like constructions that are slightly beyond M7's stated scope.
2. **LLM fingerprint**: Several sections use mechanical "The X Trap" pattern (The Dad Trap, The Name Trap, The Dog Distinction) -- repetitive but pedagogically intentional.

## Grade Justification

Grade B. The module is pedagogically strong with excellent plan adherence, comprehensive activities, and good beginner warmth. The single HIGH issue -- собака gender being stated as masculine when it is standard feminine -- is a factual error that contradicts both the module's own vocabulary YAML and activities. This inconsistency must be fixed before deployment but does not warrant an F because the activities themselves are correct and the error is localized to one paragraph of prose. The over-length content is a minor concern but doesn't harm quality.
