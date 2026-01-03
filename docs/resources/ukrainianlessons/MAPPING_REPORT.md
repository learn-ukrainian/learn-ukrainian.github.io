# Ukrainian Lessons Mapping - Automated Scoring Report

**Generated:** 2026-01-02
**Algorithm Version:** v2 (with minimum topic relevance filter)
**Threshold:** 60 points (Priority 1-3 only)

---

## Executive Summary

**Automated scoring completed:**
- **Total pairs evaluated:** 83,080 (268 resources × 310 modules)
- **Mappings above threshold:** 1,214 (1.46% of pairs)
- **Modules with mappings:** 173/310 (56% coverage)
- **Modules without mappings:** 137/310 (44% uncovered)

**Priority distribution:**
- **Priority 1 (Critical):** 2 mappings (0.16%)
- **Priority 2 (High):** 337 mappings (27.8%)
- **Priority 3 (Moderate):** 875 mappings (72.1%)

**Resources utilized:**
- **28 blog articles** from Ukrainian Lessons
- **240 ULP podcast episodes**

---

## Scoring Algorithm

### 4-Dimension Scoring (0-100 points)

| Dimension | Max Points | Criteria |
|-----------|------------|----------|
| **Topic Match** | 25 | Keyword overlap between resource and module topics/titles |
| **Level Match** | 25 | CEFR level distance (same=25, ±1=20, ±2=10, ±3+=0) |
| **Content Alignment** | 25 | Resource type vs module type compatibility |
| **Source Priority** | 25 | Ukrainian Lessons=25, Trusted=15, General=10 |

### Quality Filters Applied

1. **Minimum topic relevance:** Topic match score must be ≥10 (rejects pure level-based matching)
2. **Threshold:** Total score ≥60 required for mapping (Priority 1-3 only)
3. **Score to priority mapping:**
   - 90-100 → Priority 1 (Critical)
   - 75-89 → Priority 2 (High)
   - 60-74 → Priority 3 (Moderate)

---

## Priority 1 Mappings (Critical - 2 total)

### 1. Past Tense Module → Past Tense Guide

**Module:** `a1-yesterday-past-tense`
**Resource:** "Past Tense in Ukrainian" (ULP Blog)
**Score:** 90 | **Priority:** 1

**Breakdown:**
- Topic match: 15 points ("past", "tense" overlap)
- Level match: 25 points (both A1)
- Content alignment: 25 points (grammar guide → grammar module)
- Source priority: 25 points (Ukrainian Lessons)

**Status:** ✅ APPROVED - Perfect match

---

### 2. Future Tense Module → Future Tense Guide

**Module:** `a1-tomorrow-future-tense`
**Resource:** "Future Tense in Ukrainian" (ULP Blog)
**Score:** 90 | **Priority:** 1

**Breakdown:**
- Topic match: 15 points ("future", "tense", "grammar" overlap)
- Level match: 25 points (both A1)
- Content alignment: 25 points (grammar guide → grammar module)
- Source priority: 25 points (Ukrainian Lessons)

**Status:** ✅ APPROVED - Perfect match

---

## Sample Priority 2 Mappings (High - 337 total)

### ✅ Good Mappings (Verified)

1. **`a1-food-and-drinks` → "40+ Ukrainian Dishes"**
   - Score: 75 | Topic: food, vocabulary
   - Status: ✅ APPROVED

2. **`a1-the-accusative-i-things` → "Accusative Case in Ukrainian"**
   - Score: 75 | Topic: accusative, grammar
   - Status: ✅ APPROVED

3. **`a1-the-genitive-i-absence` → "Genitive Case in Ukrainian"**
   - Score: 75 | Topic: genitive, grammar
   - Status: ✅ APPROVED

4. **`a1-numbers-and-money` → "ULP 1-05 Numbers 1-20"**
   - Score: 75 | Topic: numbers
   - Status: ✅ APPROVED

5. **`a1-my-family` → "Family Vocabulary in Ukrainian"**
   - Score: 75 | Topic: family, vocabulary
   - Status: ✅ APPROVED

### ⚠️ Questionable Mappings (Require Review)

1. **`a1-the-cyrillic-code-i` → "ULP 1-01 Informal Greetings"**
   - Score: 75 | Topic match: 10 ("01" only - tangential)
   - **Issue:** Alphabet module mapped to greetings episode (not relevant)
   - **Recommendation:** REJECT - Find alphabet-specific content or leave unmapped

2. **`a1-this-is-i-am` → "ULP 1-07 Family + Possessive Pronouns"**
   - Score: 75 | Topic match: 10 ("i" only - weak)
   - **Issue:** Introductions module mapped to family/pronouns
   - **Recommendation:** REVIEW - May be useful as supplementary listening

3. **`a1-at-the-cafe` → "ULP 1-07 Family + Possessive Pronouns"**
   - Score: 75 | Topic match: 10 ("more" only)
   - **Issue:** Cafe/food module mapped to family topic
   - **Recommendation:** REJECT - No topical connection

---

## Coverage Analysis

### By Level

| Level | Modules | With Mappings | Coverage |
|-------|---------|---------------|----------|
| **A1** | 33 | 33 | 100% |
| **A2** | 55 | 53 | 96.4% |
| **B1** | 91 | 65 | 71.4% |
| **B2** | 131 | 22 | 16.8% |
| **Total** | 310 | 173 | 55.8% |

**Observations:**
- **A1/A2:** Excellent coverage (96-100%) - most modules have ULP content
- **B1:** Good coverage (71%) - covers early-intermediate topics
- **B2:** Poor coverage (17%) - ULP content doesn't extend to advanced topics

### Modules Without Mappings (137 total)

**Sample uncovered modules:**
- A1: None (all covered)
- A2: `a2-the-dative-i-pronouns`, `a2-if-i-were` (2 modules)
- B1: 26 modules including grammar checkpoints, advanced topics
- B2: 109 modules (83% of B2 level) - history, passive voice, registers

**Root cause:** Ukrainian Lessons Podcast focuses on A1-B1 beginner/intermediate content. Advanced B2 topics (Ukrainian history, passive constructions, stylistic registers) are not covered by ULP.

---

## Identified Issues

### 1. Tangential Matching (False Positives)

**Problem:** Single-word overlaps (e.g., "i", "more", "01") triggering 75-point matches.

**Examples:**
- `a1-the-cyrillic-code-i` matches ULP episodes containing "i" in title
- Episodes with "More about..." matching any module with "more" in title

**Solution:** Raise minimum topic_match threshold from 10 to 15 points.

---

### 2. Missing Alphabet Content (User Priority)

**Problem:** User reported Ukrainian Lessons has "extensive content on the letters" but:
- No alphabet blog article in `blog_db.json`
- No ULP episode specifically about Cyrillic alphabet
- A1-01 "The Cyrillic Code I" has no alphabet-specific mapping

**Possible causes:**
1. Blog crawl missed the alphabet article
2. Alphabet content exists but wasn't in the 28 articles cataloged
3. Content exists on website but not as blog post or podcast episode

**Action required:**
1. Manual WebFetch: `https://www.ukrainianlessons.com/alphabet/`
2. Manual WebFetch: `https://www.ukrainianlessons.com/cyrillic/`
3. Check sitemap for alphabet-related URLs
4. If found, add to `blog_db.json` and re-run scoring

---

### 3. B2 Coverage Gap

**Problem:** Only 22/131 B2 modules (17%) have mappings.

**Root cause:** ULP content is beginner-focused (A1-B1). Advanced B2 topics not covered:
- Ukrainian history (Modules 71-131)
- Passive voice constructions
- Stylistic registers
- Literary/academic Ukrainian

**Solution:** Accept this limitation. ULP is not designed for advanced learners. Consider:
- Other podcast sources for B2+ (e.g., news podcasts, cultural programs)
- Mark B2 as lower priority for ULP mapping
- Focus manual review on A1-B1 where ULP is strongest

---

### 4. Podcast Episode Metadata

**Problem:** ULP episodes in `podcast_db.json` have `"level": null` - missing CEFR level data.

**Impact:** Level matching defaults to "A1" for episodes, may cause:
- A1 episodes mapped to A2/B1 modules (if topic matches)
- Inaccurate level_match scores

**Solution:**
1. Infer level from episode number (ULP 1-XX = A1, 2-XX = A2, etc.)
2. Update `podcast_db.json` with inferred levels
3. Re-run scoring with correct level data

---

## Recommendations

### Immediate Actions (Before Manual Review)

1. **Fix alphabet mapping:**
   - WebFetch Ukrainian Lessons alphabet page
   - Add to blog_db.json if exists
   - Re-run scoring

2. **Raise topic threshold:**
   - Change minimum topic_match from 10 → 15
   - Filters out single-word tangential matches
   - Re-run scoring

3. **Infer ULP episode levels:**
   - Parse episode ID (ULP 1-XX = A1, 2-XX = A2, etc.)
   - Update podcast_db.json
   - Improves level_match accuracy

### Manual Review Strategy

**Priority 1 (2 mappings):**
- ✅ Already verified above - both APPROVED

**Priority 2 (337 mappings):**
1. **Full review of A1 modules (33 modules)** - User's primary concern
2. **Spot-check A2** (10% sample = 5-6 modules)
3. **Spot-check B1** (10% sample = 6-7 modules)

**Priority 3 (875 mappings):**
- 10% spot-check (88 mappings) across all levels
- Focus on high-frequency resources that appear in many modules

### Expected Timeline

- Fix alphabet + raise threshold + update levels: **30 minutes**
- Re-run scoring: **5 minutes**
- Manual review of Priority 1-2 (A1 focus): **1-2 hours**
- Spot-check Priority 3: **30 minutes**
- **Total:** 2.5-3 hours to validation-ready mappings

---

## Next Steps

1. ✅ **Complete automated scoring** (DONE)
2. ⏸️ **Fix identified issues** (alphabet, threshold, levels)
3. ⏸️ **Re-run scoring** with corrections
4. ⏸️ **Manual review** of Priority 1-2 mappings
5. ⏸️ **Generate final mapping** for external_resources.yaml
6. ⏸️ **Update generation scripts** with priority sorting
7. ⏸️ **Test output** and validate coverage

**Current status:** Ready for issue fixes and manual review phase.
