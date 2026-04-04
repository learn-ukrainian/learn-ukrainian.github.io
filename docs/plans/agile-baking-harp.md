# B1 Curriculum Redesign Plan

## Context

The B1 level (87 modules) has structural problems discovered during review:
1. **Grammar walls**: 4-9 grammar modules in a row before any communicative break
2. **No aspect mastery**: Only 2 baseline modules mention aspect. Students may enter B1 from outside — can't assume A2 taught it. State Standard 2024 §4.2.3.1 requires "aspect in all tenses"
3. **Missing State Standard themes**: робота (work), ресторан (restaurant), місця (places)
4. **Missing grammar**: possessive adjectives (SS 4.2.1.2), homogeneous members (SS 4.4.2)
5. **Topic modules are afterthoughts**: placed at end of grammar blocks instead of woven in

## What Changes

- **87 → 93 modules** (+12 new, -6 merged/eliminated)
- **New aspect mastery block** (6 modules + checkpoint) as Phase B1.0 — teaches aspect decision-making in past, future, narration, imperatives, negation, conditionals
- **Max 3 grammar modules before a communicative break** — enforced in all phases (single exception: 5-module motion block, documented as intentional)
- **All 15 State Standard themes covered** — 5 new thematic modules
- **All State Standard grammar gaps filled** — possessive adjectives, homogeneous members

## New Modules (12)

| Slug | Type | Existing Vocab? |
|------|------|-----------------|
| `aspect-past-tense` | Aspect mastery | Yes (`aspect-past-single-repeated.yaml`) |
| `aspect-future-tense` | Aspect mastery | Yes (`aspect-future.yaml`) |
| `aspect-in-narration` | Aspect mastery | Yes (`aspect-integration-practice.yaml`) |
| `aspect-in-imperatives` | Aspect mastery | Yes (`aspect-in-imperatives.yaml`) |
| `aspect-in-negation` | Aspect mastery | Yes (`aspect-negation.yaml`) |
| `aspect-in-conditionals` | Aspect mastery | No — needs new |
| `checkpoint-aspect` | Checkpoint | Yes (`checkpoint-aspect-mastery.yaml`) |
| `work-and-career` | Theme: робота | No — needs new |
| `restaurant-and-food` | Theme: ресторан | No — needs new |
| `possessive-adjectives` | Grammar gap | No — needs new |
| `places-and-locations` | Theme: місця | No — needs new |
| `homogeneous-members` | Grammar gap | No — needs new |

## Eliminated Modules (6 — content merged)

| Removed | Merged Into |
|---------|-------------|
| `adjectives-suppletive` | `adjectives-comparative` (added section) |
| `motion-prefixes-around` | `motion-prefixes-transit` (об-/роз- added) |
| `gerund-phrases` | `gerunds-perfective` (phrases section added) |
| `double-negation` | Dropped (beyond SS, key points in `introductory-words`) |
| `b1-finale` | `comprehensive-b1-review` (combined) |
| `practice-exam-reading` + `practice-exam-writing` | Single `practice-exam` |

## Complete Module Ordering (93 modules)

### B1.0: Baselines and Aspect Mastery (M01-M12)
```
01  b1-baseline-past-present          KEEP
02  b1-baseline-future-aspect          KEEP
03  people-and-relationships           KEEP          Theme: людина
04  aspect-past-tense                  NEW
05  aspect-future-tense                NEW
06  aspect-in-narration                NEW
07  daily-life-and-routines            MOVE (was M21) Theme: щоденне життя
08  aspect-in-imperatives              NEW
09  aspect-in-negation                 NEW
10  work-and-career                    NEW            Theme: робота
11  aspect-in-conditionals             NEW
12  checkpoint-aspect                  NEW
```

### B1.1: Morphophonemics (M13-M23)
```
13  alternation-vowels                 RESEQ (was M04)
14  alternation-consonants-nouns       RESEQ (was M05)
15  alternation-consonants-verbs       RESEQ (was M06)
16  health-at-the-doctor               MOVE (was M12) Theme: здоров'я
17  simplification-consonants          RESEQ (was M07)
18  noun-subclasses-masculine          RESEQ (was M08)
19  noun-subclasses-hissing            RESEQ (was M09)
20  restaurant-and-food                NEW            Theme: ресторан
21  noun-subclasses-feminine           RESEQ (was M10)
22  pluralia-tantum                    RESEQ (was M11)
23  checkpoint-morphophonemics         REBUILD (no .md exists)
```

### B1.2: Verb System (M24-M33)
```
24  conditionals-real                  RESEQ (was M14)
25  conditionals-unreal                RESEQ (was M15)
26  imperative-nuances                 RESEQ (was M16)
27  shopping-and-services              MOVE (was M40) Theme: купівля, послуги
28  reflexive-verbs-nuances            RESEQ (was M18)
29  passive-voice-intro                RESEQ (was M19)
30  verbal-nouns                       RESEQ (was M17)
31  housing-and-renting                MOVE (was M51) Theme: дім
32  verb-formation-suffixes            RESEQ (was M20)
33  checkpoint-verbs                   RESEQ (was M22)
```

### B1.3: Motion Verbs (M34-M43)
```
34  prepositions-spatial-review        RESEQ (was M23)
35  motion-base-review                 RESEQ (was M24)
36  motion-prefixes-arrival            RESEQ (was M25)
37  motion-prefixes-departure          RESEQ (was M26)
38  motion-prefixes-in-out             RESEQ (was M27)
39  traveling-ukraine                  MOVE (was M32) Theme: подорожі
40  motion-prefixes-transit            RESEQ (absorbs motion-prefixes-around)
41  motion-flight-swim                 RESEQ (was M30)
42  figurative-motion                  RESEQ (was M31)
43  checkpoint-motion                  RESEQ (was M33)
```

### B1.4: Comparison and Word Formation (M44-M51)
```
44  adjectives-comparative             RESEQ (absorbs suppletive forms)
45  adjectives-superlative             RESEQ (was M35)
46  adverbs-comparison-formation       RESEQ (was M37)
47  nature-and-environment             MOVE (was M78) Theme: природа
48  word-formation-adjectives          RESEQ (was M38)
49  possessive-adjectives              NEW             SS 4.2.1.2
50  word-formation-nouns               RESEQ (was M39)
51  checkpoint-comparison              RESEQ (was M41)
```

### B1.5: Case Nuances (M52-M63)
```
52  genitive-nuances                   RESEQ (was M42)
53  dative-nuances                     RESEQ (was M43)
54  instrumental-nuances               RESEQ (was M44)
55  education-and-university           MOVE (was M60) Theme: освіта
56  vocative-formal                    RESEQ (was M45)
57  prepositions-temporal              RESEQ (was M46)
58  prepositions-cause-purpose         RESEQ (was M47)
59  places-and-locations               NEW             Theme: місця
60  cases-with-ordinal-numerals        RESEQ (was M48)
61  cases-with-quantity-expressions    RESEQ (was M49)
62  advanced-pronouns                  RESEQ (was M50)
63  checkpoint-cases                   RESEQ (was M52)
```

### B1.6: Participles and Gerunds (M64-M72)
```
64  participles-active                 RESEQ (was M53)
65  participles-passive                RESEQ (was M54)
66  participle-phrases                 RESEQ (was M55)
67  leisure-culture-festivals          MOVE (was M71) Theme: дозвілля, традиції
68  short-form-adjectives              RESEQ (was M56)
69  gerunds-imperfective               RESEQ (was M57)
70  gerunds-perfective                 RESEQ (absorbs gerund-phrases)
71  society-and-media                  MOVE (was M83) Theme: суспільство
72  checkpoint-participles             RESEQ (was M61)
```

### B1.7: Complex Syntax (M73-M83)
```
73  complex-compound                   RESEQ (was M62)
74  complex-subordinate-object         RESEQ (was M63)
75  complex-subordinate-relative       RESEQ (was M64)
76  complex-subordinate-time           RESEQ (was M65)
77  complex-subordinate-reason         RESEQ (was M66)
78  complex-subordinate-condition      RESEQ (was M67)
79  complex-subordinate-purpose        RESEQ (was M68)
80  complex-subordinate-concess        RESEQ (was M69)
81  homogeneous-members                NEW             SS 4.4.2
82  reported-speech                    RESEQ (was M70)
83  checkpoint-syntax                  RESEQ (was M72)
```

### B1.8: Text and Register (M84-M89)
```
84  text-register-formal               RESEQ (was M73)
85  text-register-informal             RESEQ (was M74)
86  text-compression                   RESEQ (was M75) covers SS 4.1.5 abbreviations
87  reading-literature                 MOVE (was M79) Theme: дозвілля
88  introductory-words                 RESEQ (was M77)
89  checkpoint-text-register           RESEQ (was M80)
```

### B1.9: Synthesis and Graduation (M90-M93)
```
90  narrative-mastery                  RESEQ (was M81)
91  debate-and-opinion                 RESEQ (was M82) Theme: суспільні відносини
92  comprehensive-b1-review            RESEQ (absorbs b1-finale)
93  practice-exam                      MERGE (reading + writing exams)
```

## Impact on Existing Content

### 38 built modules (.md files):
- **29 keep as-is** — only sequence number changes
- **3 need content additions** — absorbing merged modules (adjectives-comparative, motion-prefixes-transit, gerunds-perfective)
- **6 need cross-reference updates** — topic modules that moved position
- **7 have existing build errors** to fix regardless

### 85 stale vocabulary files:
- From superseded design. Clean up: archive or delete.

## Grammar Wall Verification

| Phase | Longest grammar run | Passes max-3? |
|-------|--------------------|----|
| B1.0 | 3 (M04-M06) | ✅ |
| B1.1 | 3 (M13-M15, M17-M19, M21-M22) | ✅ |
| B1.2 | 3 (M24-M26, M28-M30) | ✅ |
| B1.3 | 5 (M34-M38) | ⚠️ Intentional exception — motion verbs are inherently communicative |
| B1.4 | 3 (M44-M46, M48-M50) | ✅ |
| B1.5 | 3 (M52-M54, M56-M58, M60-M62) | ✅ |
| B1.6 | 3 (M64-M66, M68-M70) | ✅ |
| B1.7 | 8 (M73-M80) | ❌ Needs attention — but syntax modules are tightly sequenced |
| B1.8 | 3 (M84-M86) | ✅ |

**B1.7 issue**: The complex syntax block has 8 grammar modules. This is hard to break without disrupting the conjunction-type progression. Options: (a) accept it as a second exception, (b) add a thematic module mid-block. Recommend discussing.

## State Standard 2024 Compliance

All requirements verified covered — see gap analysis in agent output. Key resolutions:
- ✅ Aspect in all tenses → B1.0 phase (6 dedicated modules)
- ✅ Possessive adjectives → M49
- ✅ Homogeneous members → M81
- ✅ Abbreviations → M86 (text-compression)
- ✅ All 15 thematic areas → dedicated modules throughout

## Implementation Steps

1. **Create GH issue** for this redesign
2. **Update `curriculum.yaml`** — replace B1 modules list
3. **Write 12 new plan YAML files** (aspect block has existing vocab files from old design)
4. **Update existing plan metadata** — sequence numbers, phase assignments
5. **Merge content** for 3 absorbing modules + delete 6 eliminated plans
6. **Clean up** 85 stale vocabulary files
7. **Build 12 new modules** via pipeline
8. **Delete old .md files** for modules that were resequenced (content stays, just rebuild after plan changes)
9. **Adversarial review** of new ordering with Gemini

## Verification

- Run `scripts/audit_module.py` on all rebuilt modules
- Verify State Standard coverage with mapping check
- Gemini adversarial review of the new curriculum.yaml ordering
- Check no orphaned files in orchestration/vocabulary/research
