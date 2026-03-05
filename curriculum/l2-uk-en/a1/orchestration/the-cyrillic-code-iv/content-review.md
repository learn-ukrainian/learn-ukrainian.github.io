# Content Review: the-cyrillic-code-iv

**Track:** a1 | **Sequence:** 4
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: ~1400+, target: 1200)
**Verdict:** C

## Plan Adherence

| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Recognize and pronounce all 33 Ukrainian letters | YES | Full Alphabet section | All letters presented |
| Explain iotated vowels and dual nature | YES | Iotated Vowels section | Dual nature explained clearly |
| Explain soft sign and apostrophe functions | YES | Soft Sign & Apostrophe | Both explained with examples |
| Identify digraphs as single sounds | YES | Affricates section | ДЖ and ДЗ covered |
| Read the complete Ukrainian alphabet fluently | PARTIAL | Summary section | Alphabet listing is **garbled** (see CRITICAL issue 1) |

### Section Structure

Plan has 6 sections; content has 5 sections. The plan's separate section "Дигріфи та Ґ -- Digraphs ДЖ, ДЗ + Letter Ґ" was merged into "Злиті звуки та рідкісні букви". This is a minor structural deviation -- the content covers the same material.

### Vocabulary Coverage

| Required Word | In Prose? | In Vocab YAML? | In Activities? |
|--------------|-----------|----------------|----------------|
| чай (tea) | YES | YES | YES |
| яблуко (apple) | YES | YES | YES |
| ще (more/still) | YES (table only) | YES | NO |
| їжа (food) | YES | YES | YES |
| день (day) | YES | YES | YES |
| сім'я (family) | YES | YES | YES |
| Львів (Lviv) | YES | YES | NO |

All required vocabulary present in prose and vocab YAML.

## Linguistic Accuracy

| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| Garbled alphabet listing | **CRITICAL** | Line 236 | See Critical Issues below |
| Й classified as vowel | **HIGH** | Line 239 | Й is a consonant. Module itself says so on line 175. |
| юшка as "fish soup" | **MEDIUM** | Line 141 | юшка means broth/soup generally, not specifically fish soup |

## Pedagogical Quality

**Lesson Quality Score:** 8/10

"Would I Continue?" Test: 4/5
- Overwhelmed? PASS
- Instructions clear? PASS
- Quick wins? PASS
- Ukrainian scary? PASS
- Come back tomorrow? FAIL (garbled alphabet at milestone moment)

## Activities Quality

10 activities, 7 distinct types. All correct answers verified. Classify activity correctly places Й in consonants (contradicting the prose error).

## Engagement

| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | 4 | 3 | PASS |
| Tables | 14+ | -- | PASS |
| Videos embedded | 10 | 10 | PASS |

## Issues Found

### CRITICAL (blocks deployment)

1. **Garbled alphabet listing (line 236)**: Multiple uppercase/lowercase swaps and extra characters. "У в" should be "В в", "Із з" should be "З з", "Й і" should be "І і" then later "Й й", "В у" should be "У у". Correct sequence: А а, Б б, В в, Г г, Ґ ґ, Д д, Е е, Є є, Ж ж, З з, И и, І і, Ї ї, Й й, К к, Л л, М м, Н н, О о, П п, Р р, С с, Т т, У у, Ф ф, Х х, Ц ц, Ч ч, Ш ш, Щ щ, Ь ь, Ю ю, Я я

### HIGH (should fix before deployment)

1. **Й misclassified as vowel (line 239)**: Text lists "10 голосні: А, Е, И, Й, О, У + 4 йотовані". Й is a consonant. Fix: 10 vowels are А, Е, И, І, О, У + Є, Ї, Ю, Я (iotated).

### MEDIUM (fix if possible)

1. **юшка translated as "fish soup"** -- should be "soup/broth"
2. **Repetitive sentence patterns** -- heavy "Це X" / "Там X" reliance

### LOW (informational)

1. **Formal "Let us" instead of "Let's"** throughout
2. **Plan key words not used** -- replacements are reasonable

## Grade Justification

Grade **C**: One CRITICAL issue (garbled alphabet listing at the culmination of the 4-module Cyrillic arc) and one HIGH issue (Й misclassified as vowel). Pedagogy, activities, and engagement are solid. The alphabet error blocks deployment.
