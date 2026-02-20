Now I have all source materials. Let me do the deep adversarial review.

---

## Phase 9: Final QA Review — the-cyrillic-code-i

### Issues Found

**Issue 1: Non-standard IPA `[pɑrrrk]`** (content line 274)
- **Location**: Section "Pronunciation Lab: The 'P' and 'B' Check"
- **Text**: `*Correct*: [pɑrrrk]`
- **Problem**: Triple "r" is not valid IPA notation. IPA uses `[r]` for a trill; duration/repetition is indicated with `ː` or diacritics, never by repeating the symbol. This confuses notation with an attempt to visually show trilling. The Green Team review flagged this but it remains unfixed.
- **Fix**: Use standard `[pɑrk]` with a descriptive nudge.

**Issue 2: Low-frequency vocabulary "Вар"** (content lines 276-278)
- **Location**: Section "Pronunciation Lab: The 'P' and 'B' Check"
- **Text**: `Say "**Бар**" vs "**Вар**". ... **Вар** (boiling water)`
- **Problem**: "Вар" (pitch/boiling water) is archaic/specialized vocabulary with near-zero utility for an A1 learner. It's used solely for a minimal pair, prioritizing textbook logic over learner utility. Green Team also flagged this.
- **Fix**: Replace with **База** (base) vs **Ваза** (vase) — both cognates, high-utility, perfect Б/В contrast.

**Issue 3: Hen mnemonic — excessive cognitive chain** (content line 89)
- **Location**: Section "The 'H' Trap: Н"
- **Text**: `The letter H stands for **H**en, which ends in N.`
- **Problem**: The chain requires 3 cognitive hops: see H shape → think "Hen" → realize Hen ends in "N" → remember Н = [n]. The first hop reinforces H = [h] before the correction arrives. The plan specifies "Hen" as the keyword, so I preserve it but shorten the chain.
- **Fix**: Rephrase to one hop: hear N at the end of "Hen" directly.

**Issue 4: Activity 1 — Ф incorrectly categorized as "True Friend"** (activities lines 17-18)
- **Location**: First match-up activity "Справжні друзі: Літери та звуки"
- **Text**: Activity includes `Ф ф → f (photo)` among True Friends
- **Problem**: In the content (line 158-162), Ф is explicitly in **Group 3: New Letters** (unique shapes), NOT Group 1: True Friends (look AND sound like English). Ф's shape is unfamiliar to English speakers — it's a "new letter" that happens to have a familiar sound. Including it in a "True Friends" activity contradicts the content's own categorization and confuses the three-category system.
- **Fix**: Remove Ф from Activity 1, add it to Activity 2 (which covers New Letters + False Friends).

**Issue 5: Activity 2 — Missing П and Ф from New Letters** (activities lines 40-43)
- **Location**: Second match-up "Нові літери та хибні друзі: Звуки"
- **Text**: Lists Б, Д, З, Л but omits П and Ф from the New Letters group
- **Problem**: Content teaches 6 New Letters (Б, Д, З, Л, П, Ф) but Activity 2 only covers 4 of them. П and Ф are missing, meaning students never do a sound-matching exercise for these two letters.
- **Fix**: Add П and Ф to Activity 2.

**Issue 6: Activity true-false — Л "ladder" contradicts content "legs"** (activities lines 298-300)
- **Location**: True-false activity, item 8
- **Text**: `The letter «Л» looks like a ladder and makes the sound [l].`
- **Problem**: Content (line 156) teaches Л as "a pair of **L**egs walking" — not a ladder. The student was taught "legs" but is tested on "ladder." This mismatch undermines trust in the material and could cause a correct student to mark it "false."
- **Fix**: Change "ladder" to "a pair of legs" in both statement and explanation.

**Issue 7: Activity quiz #9 — Л explanation says "ladder or legs"** (activities line 338)
- **Location**: Quiz "Нові знайомі", Л question explanation
- **Text**: `Літера Л looks like a ladder or legs.`
- **Problem**: Same inconsistency as Issue 6 — "ladder" was never taught. Content only uses "legs."
- **Fix**: Change to "a pair of legs" only.

**Issue 8: Meta word_target: 300 is incorrect** (meta line 3)
- **Location**: `curriculum/l2-uk-en/a1/meta/the-cyrillic-code-i.yaml`
- **Text**: `word_target: 300`
- **Problem**: The plan specifies `word_target: 2000`. The meta's section word sums (350+650+400+300+300) also equal 2000. The top-level `word_target: 300` contradicts both the plan and the meta's own section totals. Content is 2492 words. The audit tool appears to use the plan's 2000 (status shows "2492/2000"), so this doesn't cause a failure, but it's wrong data that could confuse future tooling or human readers.
- **Fix**: Change to 2000.

### Non-issues Verified (No Fix Needed)

- **IPA [ʋ] for В**: Content correctly uses [ʋ] (labiodental approximant). Activities simplify to [v] — acceptable at A1.
- **IPA [t͡sɛ] for Це**: Tie bar on affricate is correct. ✅
- **Letter count "19 letters"**: 7+6+6 = 19. ✅
- **Historical claims**: Glagolitic/Cyrillic/First Bulgarian Empire — mainstream scholarly view. ✅
- **"Alphabet Wars" / 19th century**: References Ems Decree (1876) / Valuev Circular (1863). Accurate. ✅
- **No Russianisms detected**: All Ukrainian text is standard. ✅
- **No Russian characters**: No ы, э, ё, ъ in Ukrainian text. ✅
- **Fill-in activities**: All 8 produce grammatical Ukrainian sentences when answers are inserted. ✅
- **Plan vocabulary compliance**: All required words (так, банк, метро, кафе, такт, кіт, мама, тато) present in prose. ✅
- **Objectives → self-check mapping**: All 4 objectives have corresponding self-check questions (#1-5). ✅
- **LLM artifacts**: No purple prose, no "Це не просто X, а Y" pattern, no fake statistics. ✅
- **Forward references**: Ч mentioned as a teaser for next module — appropriate, not taught. ✅
- **У as False Friend**: Correctly categorized (looks like Y, sounds like [u]). Plan confirms. ✅

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
---OLD---
-   **Mnemonic**: It looks like an "H", but think of a **H**en. The letter H stands for **H**en, which ends in N.
---NEW---
-   **Mnemonic**: It looks like an "H", but think of a He**N** — what do you hear at the end? **N**! That's the sound this letter makes.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
---OLD---
    *   *Correct*: [pɑrrrk]
---NEW---
    *   *Correct*: [pɑrk] (make that Р roll!)
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-i.md
---OLD---
2.  **The "B" vs "V" Check**: Say "**Бар**" vs "**Вар**".
    *   **Бар** starts with a B-boy sound. Explosive.
    *   **Вар** (boiling water) starts with a V-vehicle sound. Buzzing.
---NEW---
2.  **The "B" vs "V" Check**: Say "**База**" vs "**Ваза**".
    *   **База** (base) starts with a B-boy sound. Explosive.
    *   **Ваза** (vase) starts with a V-vehicle sound. Buzzing.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml
---OLD---
  - left: Т т
    right: t (stop)
  - left: Ф ф
    right: f (photo)
  title: 'Справжні друзі: Літери та звуки'
---NEW---
  - left: Т т
    right: t (stop)
  title: 'Справжні друзі: Літери та звуки'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml
---OLD---
  - left: Л л
    right: l (look)
  title: 'Нові літери та хибні друзі: Звуки'
---NEW---
  - left: Л л
    right: l (look)
  - left: П п
    right: p (park)
  - left: Ф ф
    right: f (photo)
  title: 'Нові літери та хибні друзі: Звуки'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml
---OLD---
  - correct: true
    explanation: True! Літера Л looks like a ladder and makes the sound [l].
    statement: The letter «Л» looks like a ladder and makes the sound [l].
---NEW---
  - correct: true
    explanation: True! Літера Л looks like a pair of legs and makes the sound [l].
    statement: The letter «Л» looks like a pair of legs and makes the sound [l].
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml
---OLD---
  - explanation: Літера Л looks like a ladder or legs.
---NEW---
  - explanation: Літера Л looks like a pair of legs.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/meta/the-cyrillic-code-i.yaml
---OLD---
word_target: 300
---NEW---
word_target: 2000
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Rationale**: 8 issues found — all fixable with the patches above. No Russianisms, no factual errors in core claims, no broken activities, no grammar scope violations. Content is 2492 words against a 2000-word target (124% — healthy). All 5 plan sections present and compliant. Activities are well-structured with good variety (9 activities, 8 types). The fixes address: 1 IPA notation error, 1 low-utility vocabulary choice, 1 mnemonic phrasing improvement, 2 activity category mismatches, 2 mnemonic consistency errors across activities, and 1 meta data error. After these fixes, the module is solid A1 introductory material.