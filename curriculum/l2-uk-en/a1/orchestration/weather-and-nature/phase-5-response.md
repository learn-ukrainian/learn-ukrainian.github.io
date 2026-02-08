# Рецензія: Weather & Nature

**Level:** A1 | **Module:** 29
**Overall Score:** 7.3/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 required used, but vocabulary.yaml file is missing core words]
- Grammar scope: [clean]
- Objectives: [all covered]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Activities test untaught vocabulary causing frustration. |
| 2 | Coherence | 7/10 | <7 | `vocabulary.yaml` does not match the content (missing core words). |
| 3 | Relevance | 9/10 | <7 | Weather is highly relevant and useful. |
| 4 | Educational | 6/10 | <7 | Quizzes test material not presented in the lesson (e.g., "листя падає", "птахи повертаються"). |
| 5 | Language | 9/10 | <8 | Natural Ukrainian phrasing ("Йде дощ", impersonal expressions). |
| 6 | Pedagogy | 6/10 | <7 | Assessment mismatch: testing untaught vocabulary. |
| 7 | Immersion | 8/10 | <6 | Good balance of Ukrainian examples and English explanation. |
| 8 | Activities | 5/10 | <7 | Extensive use of untaught vocabulary (мороз, трава, сад, пляж) and grammar (Instrumental case). |
| 9 | Richness | 8/10 | <6 | Good cultural context (Songs, Myth vs Fact). |
| 10 | Beginner Safety | 6/10 | <7 | High frustration risk in quizzes due to unknown words. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural, though "біла вода" for snow is odd. |
| 12 | Linguistic Accuracy | 9/10 | <9 | No grammar errors found in text. |

**Weighted Overall:** 7.27/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - Instrumental case "з рибою" used in activity but likely not taught.
- Activity errors: [FAIL] - Multiple items test untaught vocabulary.
- Beginner safety: 3/5

## Critical Issues Found

### Issue 1: Assessment Mismatch (Untaught Vocabulary)
- **Location**: Activities file, `group-sort` (Seasons, Animals/Plants), `quiz` (What Season?, Animal or Plant?)
- **Original**: Items include: `мороз`, `трава`, `зелено`, `сад`, `пляжі`, `листя`, `троянда`, `ведмідь`, `кущ`.
- **Problem**: None of these words are taught in the module content. Asking beginners to categorize words they haven't seen creates anxiety and guessing.
- **Fix**: Replace with taught vocabulary or add these words to the "Weather Vocabulary" or "Examples" sections in the content.

### Issue 2: Vocabulary File Mismatch
- **Location**: `vocabulary/29-weather-and-nature.yaml`
- **Original**: Lists `квітка, клімат, мурчик, осінь...`
- **Problem**: Missing CORE module vocabulary: `тепло`, `холодно`, `дощ`, `сніг`, `весна`, `літо`, `зима`, `вітер`, `жарко`. The YAML file should reflect the primary vocabulary target, not just random nouns found in the text.
- **Fix**: Update YAML to include all bolded terms from the presentation tables.

### Issue 3: Grammar Scope (Instrumental Case)
- **Location**: Activities file, `fill-in` (Nature and Animals), Item "У мене є акваріум з ___."
- **Original**: Answer: `рибою`
- **Problem**: This requires the Instrumental case (`риба` -> `рибою`) after preposition `з`. Module 29 (A1) typically has not mastered the Instrumental case (usually A2).
- **Fix**: Change sentence to avoid Instrumental, e.g., "У акваріумі плаває ___." (In the aquarium swims a fish - Nominative `риба`).

### Issue 4: Odd Phrasing
- **Location**: Activities file, `fill-in` (Weather), Item "Падає біла вода з неба."
- **Original**: "Падає біла вода з неба."
- **Problem**: Describing snow as "white water" is unnatural and confusing.
- **Fix**: Change to "З неба падають білі сніжинки" (White snowflakes fall from sky) or simply "Взимку все біле. Падає..."

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Fail** (Quizzes are guessing games)
- Instructions clear? **Pass**
- Quick wins? **Pass** (Warm-up is easy)
- Ukrainian scary? **Fail** (Sudden unknown words in test)
- Come back tomorrow? **Pass** (Topic is interesting)

## Fix Plan to Reach 9/10

### Activities: 5/10 → 9/10

**What to fix:**
1. **Remove Untaught Words**: In `activities/29-weather-and-nature.yaml`:
   - Replace `мороз` with `сніг`.
   - Replace `трава` with `квітка` or `дерево`.
   - Replace `зелено` with `тепло`.
   - Replace `сад` with `парк` or `ліс`.
   - Replace `троянда` with `квітка`.
   - Replace `ведмідь` with `кіт` or `собака`.
   - Remove `кущ`.
2. **Fix Quiz Scenarios**:
   - Change "Люди на пляжі" (People on beach) to "Сонце і тепло" (Sun and warmth).
   - Change "Листя падає з дерев" to "Вересень, жовтень, листопад".
   - Change "Птахи повертаються з півдня" to "Вже не холодно, квіти цвітуть".
3. **Fix Grammar**:
   - Change "У мене є акваріум з [рибою]" to "Це моя маленька [риба]." or "У воді плаває [риба]."

### Pedagogy: 6/10 → 9/10

**What to fix:**
1. **Sync Content & Activities**: Ensure every word in the activities is either explicitly taught in the MD tables/examples or is a cognate.
2. **Clarify Snow Description**: Change "Падає біла вода" to something simpler like "Взимку падає ___."

### Coherence: 7/10 → 9/10

**What to fix:**
1. **Update Vocabulary YAML**: Completely rewrite `vocabulary/29-weather-and-nature.yaml` to include the actual core vocabulary: `тепло, холодно, жарко, сонячно, хмарно, вітряно, дощ, сніг, весна, літо, осінь, зима`.

### Projected Overall After Fixes

`(9*1.5 + 9*1 + 9*1 + 9*1.2 + 9*1.1 + 9*1.2 + 8*1 + 9*1.3 + 8*0.9 + 9*1.3 + 9*1 + 9*1.5) / 14`
`= 124.4 / 14 = 8.88` (approx 9.0)

## Verdict

**FAIL**

The module content is good, but the activities and vocabulary metadata are broken. The activities aggressively test vocabulary that was never taught (animals, plants, seasonal phenomena), which violates beginner safety rules. The vocabulary YAML file misses almost all the actual lesson content. These must be synced before passing.