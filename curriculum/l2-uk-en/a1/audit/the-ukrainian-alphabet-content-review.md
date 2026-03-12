# Content Review: the-ukrainian-alphabet

**Track:** a1 | **Sequence:** 1
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: 1695, target: 1200)
**Verdict:** C

## Plan Adherence

| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Full 33-letter alphabet as coherent system | YES | Вступ, Голосні та приголосні | Listed but no visual chart |
| Letter ≠ sound (букви vs звуки) | YES | Букви і звуки | Well explained |
| Vowels vs consonants distinction | YES | Голосні та приголосні | Listed as bullets, no table |
| Read/write 10 practice letters | YES | Перші 10 літер | Good blending walkthroughs |
| 5+ survival sight words | PARTIAL | Перші слова | привіт, дякую mentioned; **це barely used** |

### Vocabulary Coverage

| Required Word | In Prose? | In Vocab YAML? | In Activities? |
|--------------|-----------|----------------|----------------|
| мама | YES | YES | YES |
| тато | YES | YES | YES |
| кіт | YES | YES | YES |
| молоко | YES | YES | YES |
| масло | YES | YES | YES |
| ліс | YES | YES | YES |
| місто | YES | YES | YES |
| око | YES | YES | YES |
| так | YES | YES | YES |
| ні | YES | YES | YES |

All 10 required words present across all three files. 27/27 vocabulary items verified in VESUM.

### Missing Plan Points

- **No full alphabet chart** — Plan point: "Show the full 33-letter alphabet chart as a reference map." Content lists vowels and consonants as bullet points but no visual table or chart. **HIGH**
- **No micro-dialogues with Це** — Plan: "— Це кіт? — Так, це кіт. / — Це місто? — Ні, це ліс." Content uses тут/там sentences but the Це pattern is only in the dialogue block (lines 144-149), not as formally introduced sight word construction. **MEDIUM**
- **Missing "Next lesson" preview** — Plan: "Next: M2 deep-dives into the vowel system." Summary doesn't mention what's next. **LOW**
- **Pronunciation videos not embedded** — Plan has 10 per-letter videos + overview + poster from Anna Ohoiko. Zero appear in the content markdown. Activities have them but prose does not. **HIGH**

## Linguistic Accuracy

| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| No issues found | — | — | All 27 vocabulary items verified in VESUM. No Russianisms detected. |

All Ukrainian text is accurate. No ghost words, no false friend claim errors.

## Pedagogical Quality

**Lesson Quality Score:** 7/10

**"Would I Continue?" Test:**

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | PASS | Pacing is comfortable, 10 letters is manageable |
| Were instructions clear? | PASS | Clear letter-by-letter guidance |
| Did I get quick wins? | PASS | Reading мама, тато, кіт early on |
| Was Ukrainian scary? | PASS | Introduced gently with English support |
| Would I come back tomorrow? | MARGINAL | The "Presentation" section is cold and discouraging |

4/5 = baseline 9, but **deducted -2 for the "Presentation" section** (see Critical below).

**Lesson Arc:**

| Element | Status | Notes |
|---------|--------|-------|
| WELCOME | ✅ | Warm opening, context setting |
| PREVIEW | ✅ | "You do not need to memorize all 33 letters today" |
| PRESENT | ⚠️ | Good content but broken by spurious "Presentation" section |
| PRACTICE | ✅ | Blending exercises, word reading, sentences |
| CELEBRATE | ✅ | "You have taken your first major step" + self-check |

## Activities Quality

| Activity | Type | Issues |
|----------|------|--------|
| Listen and Repeat | watch-and-repeat | ✅ All 10 letters, videos linked |
| First Letter | image-to-letter | ✅ Good emoji usage, correct answers |
| Vowels and Consonants | classify | ✅ Exact 10-letter split |
| Letter Facts | true-false | ✅ Tests false friends (Н≠H, С=S) |
| Word Scramble | anagram | ✅ All decodable words |
| Letter Sounds | match-up | ✅ Covers false friends |
| Complete the Word | fill-in | ✅ Good missing-letter format |
| Read and Recognize | quiz | ✅ Translation recognition |

8 activity types with 56 total items. Excellent variety. All answers verified correct. All words use only the 10 decodable letters (plus sight words in quiz). **Activities are the strongest part of this module.**

## Engagement

| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | 4 | 3 | PASS |
| Tables | 0 | — | FAIL (grammar needs tables) |
| Videos embedded in prose | 0 | 10+ (per plan) | FAIL |
| Direct address (you/your) | 23 | 15 | PASS |
| Encouragement phrases | 8 | 3 | PASS |

## Issues Found

### CRITICAL (blocks deployment)

1. **Spurious "Presentation" section (line 26-28)** — A `## Presentation` section exists between Вступ and Букви і звуки that is NOT in the plan. It's a pure LLM template leak: "Welcome to the main portion of this lesson. In this section, we will delve into the fundamental concepts of the Ukrainian writing system. We will explore the vital distinction between written letters and spoken sounds..." This paragraph adds zero content, uses classic AI fingerprint language ("delve into", "vital distinction", "structured approach will ensure"), and breaks the lesson flow. **Must be deleted.**

### HIGH (should fix before deployment)

1. **No pronunciation videos in prose** — Plan specifies 10 per-letter videos from Anna Ohoiko (@UkrainianLessons) plus overview and poster videos. They appear correctly in activities but are completely absent from the content markdown. For a phonics module, this is a major gap — learners need to hear the sounds while reading about them.

2. **No alphabet chart/table** — Plan explicitly says "Show the full 33-letter alphabet chart as a reference map." Content lists vowels and consonants as bullet-point lists. A visual table organized by category (vowels, consonants, modifier) would be far more scannable and serve as a reference learners can return to.

3. **"Це" not properly introduced as sight word** — Plan requires "це" as one of 5 survival sight words. It's mentioned in the sight word explanation but never formally introduced with the same prominence as привіт/дякую. The plan's Це-pattern dialogues ("— Це кіт? — Так, це кіт.") are partially present but not using Це as the primary pattern.

### MEDIUM (fix if possible)

1. **No grammar tables at all** — Vowel/consonant classification, letter-sound mappings, and the 10-letter practice set all cry out for tables. Bullet-point lists work but tables would be pedagogically superior for this visual-heavy topic.

2. **LLM fingerprint in "Presentation" section** — "we will delve into the fundamental concepts", "We will explore the vital distinction", "This structured approach will ensure you build a strong foundation" — textbook AI voice. If the section isn't deleted entirely (per CRITICAL #1), it must be completely rewritten.

### LOW (informational)

1. **No "Next lesson" preview** — Plan says to mention M2 (vowels). Summary celebrates progress but doesn't preview what's next.
2. **"Let us" formality** — Content uses "Let us" 6 times instead of the more natural "Let's". Minor but contributes to a slightly formal tone.

## Grade Justification

**Grade C.** The content is pedagogically sound at its core — vocabulary is accurate (27/27 VESUM verified), the blending walkthroughs are excellent, and activities are outstanding (8 types, 56 items, correct answers, decodable words only). However, the spurious "Presentation" section is a template leak that must be removed, pronunciation videos are completely missing from the prose (critical for a phonics module), and the plan's alphabet chart requirement is unmet. These are fixable issues, not fundamental problems with the content quality.
