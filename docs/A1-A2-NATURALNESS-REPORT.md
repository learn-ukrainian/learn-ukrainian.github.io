# A1/A2 Naturalness Check Report

**Date**: 2026-01-11
**Tool**: `check_naturalness` MCP tool
**Threshold**: Score < 7 flagged for review
**Samples Checked**: 6 activities across A1 and A2

---

## Summary

**Finding**: Grammar drill activities with isolated, disconnected sentences consistently score **4-6/10** for naturalness, while contextual mini-dialogues score **8/10**.

**Pattern Identified**:
- ❌ **Disconnected sentences** (subject shifts: Я → Вона → Він)
- ❌ **Lack of discourse markers** (no connectors, transitions, or logical flow)
- ❌ **Mechanical repetition** (repeated patterns without variation)
- ❌ **No cohesive narrative** (random topic jumps within activity)

---

## Detailed Results

### ✅ PASS (Score >= 7)

1. **A2 - Complete the Story** (cloze)
   Score: **8/10**
   Text: "Марія і Петро в Одесі. Їм подобається море. Їм тепло і весело. Погода чудова!"
   Issues: Short sentences, staccato flow
   Context: Mini-narrative about a couple at the beach - **coherent**

2. **A2 - At the Restaurant** (cloze)
   Score: **8/10**
   Text: "Ми з другом у ресторані. Офіціант підходить і каже: «Добрий вечір! Дати вам меню?» Я відповідаю: «Так, дайте нам меню, будь ласка.»"
   Issues: 'Дати' slightly direct, but acceptable for A2
   Context: Restaurant dialogue - **coherent situational context**

---

### ⚠️ FLAGGED (Score < 7)

3. **A2 - Choose the Correct Aspect** (cloze) - `12-aspect-introduction.yaml`
   Score: **4/10**
   Text: "Я читав книгу дві години. Вона писала листа вчора. Він малював картину. Ми читаємо щодня. Вона завжди говорить правду. Я вже прочитав цю книгу. Що ти робив увечері? Я зробив домашнє завдання! Він довго говорив. Він сказав «ні.» Ми їхали три години. Ми нарешті приїхали!"
   **Issues**:
   - Completely disconnected sentences (book → letter → painting → truth)
   - No narrative thread or logical sequence
   - Artificial subject switching (Я → Вона → Він → Ми)
   - Lacks context for aspect choice

   **Recommendation**: Rewrite as coherent narrative (e.g., diary entry about a busy day)

4. **A2 - Perfective or Imperfective Past** (fill-in) - `13-the-completed-past.yaml`
   Score: **6/10**
   Text: "Я читав книгу цілий вечір. Вона нарешті прочитала всю книгу."
   **Issues**:
   - Sudden subject shift (Я → Вона)
   - Missing contrastive connector (e.g., 'а', 'але')
   - Implied relationship not established

   **Recommendation**: Add connector: "Я читав книгу цілий вечір, а вона прочитала її за годину"

5. **A1 - My Daily Routine** (fill-in) - `25-my-daily-routine.yaml`
   Score: **4/10**
   Text: "Я прокидаюся о сьомій ранку. Вона одягається швидко. Спочатку я прокидаюся. Потім я вмиваюся. Спочатку я снідаю. Потім я виходжу."
   **Issues**:
   - Subject shift without context (Я → Вона)
   - Redundancy: "Я прокидаюся" stated twice
   - Repetitive sequencing pattern (Спочатку... Потім... repeated)
   - Mechanical, lacks narrative flow

   **Recommendation**: Unify subject, vary sequence words: "Спочатку → Потім → Після цього → Нарешті"

6. **A2 - Preposition Sentences** (unjumble) - `07-spatial-prepositions.yaml`
   Score: **4/10**
   Text: "Я йду до школи щодня о восьмій годині. Кава без цукру і молока, будь ласка."
   **Issues**:
   - Complete narrative incoherence (school → coffee order)
   - Context mismatch: "без" (without) is not a spatial preposition
   - No discourse markers

   **Recommendation**: Focus on location: "Я йду до школи щодня о восьмій годині. Школа знаходиться біля парку."

---

## Root Cause Analysis

### Why Grammar Drills Score Low

**Traditional textbook approach**:
- Isolates grammar points for focused practice
- Uses disconnected example sentences
- Prioritizes grammatical accuracy over discourse coherence
- Assumes learners will apply patterns in natural contexts later

**Result**: Technically correct but **robotic-sounding** Ukrainian text.

### Why This Matters

From CLAUDE.md issue #412:
> Users reported that some activities "sound like they were written by AI" or "feel disconnected"

**User experience impact**:
- Learners internalize unnatural sentence patterns
- Reduces engagement with authentic-sounding material
- Contradicts communicative language teaching principles

---

## Recommendations

### 1. **Immediate Fixes** (Tactical)

For activities scoring < 7:
- Add discourse markers: а, але, тому, потім, нарешті, зате
- Maintain consistent subjects within activity contexts
- Create mini-narratives instead of isolated sentences
- Add situational framing (diary entry, dialogue, description)

### 2. **Structural Changes** (Strategic)

**Option A - Narrative Wrapping**:
```yaml
- type: cloze
  title: Busy Weekend
  passage: |
    У суботу я {був|буду} дуже зайнятий. Спочатку я {читав|прочитав} книгу дві години.
    Потім моя сестра {писала|написала} листа. Увечері ми {дивилися|подивилися} фільм разом.
```

**Option B - Dialogue Format**:
```yaml
- type: fill-in
  title: At the Café
  context: "Діалог між друзями в кав'ярні"
  items:
    - sentence: "— Що ти ___ увечері?"
      answer: "робив"
    - sentence: "— Я ___ домашнє завдання."
      answer: "робив"
```

**Option C - Situational Clustering**:
Group sentences by situation (morning routine, at restaurant, at school) to create coherent mini-contexts.

### 3. **Process Improvements**

- **Pre-commit hook**: Run `check_naturalness` on new/edited activities
- **Acceptance criteria**: Naturalness score >= 7 for all prose activities
- **Stage-3 documentation**: Add "Create cohesive context" to activity checklist

---

## Next Steps

**Decision needed from user**:

1. **Scope**: Fix flagged activities only OR review entire A1/A2 corpus?
2. **Approach**: Quick tactical fixes OR deeper narrative restructuring?
3. **Priority**: Which activities/modules to fix first?

**Effort estimate**:
- Tactical fixes (6 flagged activities): ~2-3 hours
- Full A1/A2 review (92 files): ~15-20 hours
- Structural redesign (templates + guidelines): ~30+ hours

---

## Appendix: Tool Output Examples

### Example - Score 4 (Robotic)

```json
{
  "score": 4,
  "issues": [
    "Sentences are completely disconnected and lack a narrative thread",
    "No discourse markers or logical connectors to create flow",
    "Artificial switching of subjects typical of mechanical drills"
  ],
  "recommendation": "Rewrite as a coherent narrative or dialogue",
  "rewrite_needed": true
}
```

### Example - Score 8 (Natural)

```json
{
  "score": 8,
  "issues": [
    "Sentences are somewhat staccato/short",
    "Lacks discourse markers for better flow"
  ],
  "recommendation": "Add time markers like 'Сьогодні' or connectors",
  "rewrite_needed": false
}
```
