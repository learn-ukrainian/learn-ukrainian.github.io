# Plan Review: checkpoint-genitive (A2-M14)

**Reviewer:** Claude Opus 4.6 | **Date:** 2026-04-04
**Plan version:** 1.0 | **Status:** PASS (minor suggestions)

---

## Summary

Solid checkpoint plan that reviews all genitive material from M08-M13. Word target (1500) correctly matches A2-checkpoint config. The three-part structure (recognize → choose → produce) follows good pedagogical progression from receptive to productive skills. The Kyiv tour guide dialogue is creative and naturally combines all genitive patterns. Ready to build with minor suggestions.

---

## Findings

### No critical or error-level issues found.

### SUGGESTION: Translation challenge may not fit A2 pedagogy

**Location:** Section 3, point 3: "Translation challenge: translate short English sentences into Ukrainian"

The curriculum's core principle is "think in Ukrainian" — situation → Ukrainian thought → Ukrainian words, no English intermediary. A translation exercise from English goes against this principle. Consider replacing with:
- **Situation-based production:** "You are at the market. Ask for 2 kg of tomatoes and a bottle of water." (situation → Ukrainian, no English sentence to translate)
- **Picture-based production:** describe what you see in a picture using genitive constructions

This is a minor concern for a checkpoint (where some meta-linguistic awareness is expected), but worth flagging.

### SUGGESTION: Error-correction activity is excellent but needs care

**Location:** Activity hints: error-correction (6 items)

Error-correction is a strong choice for a checkpoint — it tests whether learners can detect and fix mistakes, which requires deep understanding. However:
- Items should contain exactly ONE error each (not multiple)
- Errors should be plausible (wrong ending, not random nonsense)
- Include a mix: wrong preposition, wrong case ending, wrong agreement, wrong Gen.Pl. form

The 6-item count (vs. 8 for others) is appropriate — error-correction items take longer to process.

### SUGGESTION: Self-assessment checklist is good for metacognition

**Location:** Section 3, point 4: "Self-assessment checklist"

This is pedagogically sound — learners self-evaluate which genitive patterns they've mastered. In the build, this should be presented as a visual checklist, not as running prose. It serves as a study guide for review.

---

## Vocabulary Verification

All vocabulary hints are metalinguistic terms appropriate for a checkpoint:
- родовий відмінок, прийменник, узгодження, множина, однина, закінчення, перевірка, помилка -- all standard grammatical terminology
- виправити, впізнати, вибрати -- appropriate action verbs for checkpoint tasks

No VESUM verification needed for these (they're metalinguistic, not new content vocabulary).

---

## Dialogue Situation Review

The Kyiv tour guide scenario is creative and well-motivated:

**Strengths:**
- Natural context: a guide explaining a city to tourists
- Combines ALL genitive patterns naturally:
  - біля Софійського собору (location — M10)
  - без квитка (without — M09)
  - для групи з десяти людей (purpose + quantity — M09, M12)
  - до Хрещатику п'ять хвилин (direction/time — M10)
- Cultural content: real Kyiv landmarks (Софійський собор, Хрещатик)
- Speakers have clear roles

This is one of the better dialogue situations in the A2 plans — it naturally consolidates everything without feeling forced.

---

## Content Outline Structure

| Section | Target words | Assessment |
|---------|-------------|------------|
| Впізнавання форм (Recognizing) | 450 | Good — receptive skill, preposition identification |
| Вибір правильної форми (Choosing) | 500 | Good — includes agreement, plural, preposition choice |
| Вільне вживання (Free Production) | 550 | Good — builds to productive output |
| **Total** | **1500** | Matches A2-checkpoint config |

The progression from receptive (recognize) → selective (choose) → productive (create) is pedagogically sound and matches how Ukrainian textbooks structure review lessons.

---

## Activity Hints Review

| Hint | Format | Issues |
|------|--------|--------|
| quiz (8 items) | dict with type/focus/items | OK — preposition identification |
| fill-in (8 items) | dict with type/focus/items | OK — singular + plural with agreement |
| match-up (8 items) | dict with type/focus/items | OK — situations→expressions |
| error-correction (6 items) | dict with type/focus/items | OK — see suggestion above |

All in proper dict format. Good variety. The error-correction type is a strong addition for a checkpoint.

---

## Coverage of M08-M13 Material

| Module | Topic | Covered in checkpoint? |
|--------|-------|----------------------|
| M08 | Gen. prepositions: source (з/із/зі, від, після) | Yes (Section 1, point 3) |
| M09 | Gen. prepositions: purpose (для, без, біля, навпроти, коло) | Yes (Section 1, point 3) |
| M10 | Gen. prepositions: direction (до) + time expressions | Yes (Section 1, point 3) |
| M11 | Gen. adjective/pronoun agreement | Yes (Section 2, point 1) |
| M12 | Gen. plural across all genders | Yes (Section 2, point 2) |
| M13 | Shopping and health contexts | Yes (Section 3, dialogue situations) |

Full coverage of all six modules. No gaps.

---

## Word Target Verification

A2-checkpoint config: 1500 words. Plan target: 1500 words. **Correct.**

Verified via: `.venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); from audit.config import LEVEL_CONFIG; print(LEVEL_CONFIG['A2-checkpoint']['target_words'])"` → 1500

---

## References Review

- Заболотний Grade 5-6: Appropriate comprehensive reference
- ULP "10 Uses of Genitive Case": Good overview for self-study

Both are relevant. The Grade 5-6 range correctly spans the source modules' reference material.

---

## Verdict

**PASS** — Well-structured checkpoint with correct word target, comprehensive coverage of M08-M13, natural dialogue situation, and good activity variety. The translation exercise suggestion is worth considering but not a blocker. Ready to build.
