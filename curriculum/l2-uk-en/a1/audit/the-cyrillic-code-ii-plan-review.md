# Plan Review: the-cyrillic-code-ii

**Track:** A1 | **Sequence:** 2 | **Version:** 4.0
**Verdict:** PASS

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1200, Config: 1200 |
| section_budgets | PASS | Sum = 1200 vs target 1200 (100%) |
| required_fields | PASS | All present (module, level, sequence, slug, version, title, subtitle, focus, pedagogy, word_target, objectives, content_outline, vocabulary_hints, activity_hints, persona, grammar, register) |
| version_string | PASS | `'4.0'` — correctly quoted string |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Alphabet (letter recognition) | YES | A1 §4.1.1 | A1 | PASS |
| Vowel/consonant distinction | YES | A1 §4.1.4 | A1 | PASS |
| Sound-letter correspondence | YES | A1 §4.1.1 | A1 | PASS |
| И vs І distinction | YES | A1 §4.1.4 (vowel sounds) | A1 | PASS |

No grammar scope issues — all topics are phonetics/alphabet, squarely within A1 §4.1.

## Grammar Verification (Textbook RAG)
| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Голосні vs приголосні | Grade 1, bolshakova (chunk s0023) | YES | Textbook teaches same vowel/consonant distinction at Grade 1 |
| И vs І as separate sounds | Grade 1, zaharijchuk (NUS 2025) | YES | Standard Bukvar approach — introduce vowels with key words |

The plan's approach (key word per letter, video pronunciation, classify vowels/consonants) aligns with Ukrainian Bukvar pedagogy.

## Vocabulary Verification
| Word | VESUM | Issues |
|------|-------|--------|
| кіт | OK (noun:anim:m) | None |
| молоко | OK (noun:inanim:n) | None |
| рис | OK (noun:inanim:m) | None |
| сир | OK (noun:inanim:m) | None |
| тато | OK (noun:anim:m) | None |
| місто | OK (noun:inanim:n) | None |
| море | OK (noun:inanim:n) | None |
| метро | OK (noun:inanim:n:nv) | None |
| ліс | OK (noun:inanim:m) | None |
| вікно | OK (noun:inanim:n) | None |
| стіл | OK (noun:inanim:m) | None |
| кіно | OK (noun:inanim:n:nv) | None |
| око | OK (noun:inanim:n) | None |
| слово | OK (noun:inanim:n) | None |
| літо | OK (noun:inanim:n) | None |

All 15 vocabulary items verified. No ghost words, no Russicisms.

## Decodability Check (Cyrillic Module — MANDATORY)

**Cumulative charset (14 letters):** А, О, У, М, Н, С, Л (Code I) + К, И, І, Р, В, Т, Е (Code II)

### Required vocabulary — PASS
All words in `vocabulary_hints.required` use only known letters.

### Key words in content_outline — 3 issues

| Word | Role | Unknown Letter | Source Module |
|------|------|---------------|--------------|
| риба | Key word for И | **Б** | Code III |
| індик | Key word for І | **Д** | Code III |
| каша | Additional word for К | **Ш** | Code III |

These are letter-association words (like "A is for Apple"), not reading targets. The learner sees them alongside the letter's pronunciation video to build sound association. This is standard Bukvar pedagogy — the word introduces the letter, the learner doesn't need to decode the full word yet. However, they contain letters the learner hasn't encountered.

### Collocations in vocabulary_hints — 2 issues

| Collocation | Unknown Letters |
|-------------|----------------|
| рудий кіт | **Д**, **Й** |
| мій кіт | **Й** |

Collocations are supplementary examples, not reading targets.

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)
None.

### MEDIUM (fix if possible)
1. **Undecodable key words** — `риба` (Б), `індик` (Д), `каша` (Ш) use letters from Code III. Consider swapping to fully decodable alternatives. For И: `рис` (already in required vocab). For І: `ім'я` has apostrophe issue... or simply `Іра` (proper name, but all letters known: І, Р, А). For К: `кава` (К, А, В, А — all known, already listed as additional).
2. **Undecodable collocations** — `рудий кіт` and `мій кіт` use Д and Й. Replace with decodable collocations: `мале місто`, `наш кіт` — wait, `наш` uses Ш. Better: `мій` can't be fixed without Й. Consider removing collocations for this module or using only decodable ones like `він і кіт`.
3. **Minor section budget concern** — Підсумок section at 100 words (8.3% of total) is thin. Not a compliance issue but the section may feel abrupt.

### LOW (informational)
1. **Content outline warm-up references "масло"** — fully decodable (М, А, С, Л, О from Code I). Good.
2. **Activity types well-suited for primer** — watch-and-repeat, classify, image-to-letter, match-up, quiz. Appropriate for letter-learning.

## Suggested Fixes

### Fix 1: Replace undecodable key words (MEDIUM)
```yaml
# OLD (content_outline, Vowels section)
- 'И — uniquely Ukrainian vowel... Key word: риба.'
- 'І — the soft i... Key word: індик.'

# NEW — use fully decodable key words
- 'И — uniquely Ukrainian vowel... Key word: рис.'
- 'І — the soft i... Key word: місто.'
```

Note: `рис` is already in required vocab and is fully decodable. `місто` uses І prominently and is fully decodable.

### Fix 2: Replace undecodable additional word for К (MEDIUM)
```yaml
# OLD (content_outline, Consonants section)
- 'К — key word: кіт. Additional: кіно, каша, кава.'

# NEW — drop каша, keep decodable words
- 'К — key word: кіт. Additional: кіно, кава, корова.'
```

Wait — `корова` has all known letters (К, О, Р, О, В, А). Good alternative. Or just drop `каша` and keep the other three.

### Fix 3: Remove or replace undecodable collocations (MEDIUM)
```yaml
# OLD (vocabulary_hints)
- 'кіт (cat) — key word for К; collocations: мій кіт, рудий кіт'

# NEW — decodable collocations only
- 'кіт (cat) — key word for К; collocations: він і кіт, наш кіт'
```

Note: `наш` uses Ш (Code III). Better option: just drop collocations for primer modules entirely, since learners can't form phrases yet.

```yaml
# SIMPLEST FIX
- 'кіт (cat) — key word for К'
```
