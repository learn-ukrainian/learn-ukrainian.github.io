## Linguistic Scan
- No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian letters (`ы, э, ё, ъ`) found.
- Factual grammar issue: `Think of this suffix as the English equivalent of the words "oneself" or "myself." If you take a standard verb and attach this suffix, you instantly change the target of the action from an external object back to the speaker.` This is too absolute. The textbook corpus used in RAG gives broader `-ся` uses, including `навчатися, закохатися` (Grade 10, p.176) and also reflexive meanings beyond literal self-action (Grade 11, p.96).
- The summary repeats the same overgeneralization in `These verbs are essential because they describe actions directed at the speaker, which is exactly what a morning routine involves.`

## Exercise Check
- 4 activity markers are present: `fill-in-reflexive-endings`, `quiz-reflexive-choice`, `order-morning-sequence`, `write-morning-routine`.
- Marker count matches the 4 `activity_hints` in the plan.
- Placement is correct: the reflexive markers come after the reflexive-verb teaching, and the sequence/routine markers come after the routine-sequencing section.
- No inline DSL exercise logic is present to audit.
- No exercise-placement or count issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections are present and the module covers `прокидатися → вмиватися → одягатися → снідати → йти`, but only `*Карама́н Grade 10 (p. 176)*` and `*Кравцо́ва Grade 4 (p. 113)*` are cited; the plan’s `Захарійчук Grade 4, p.162` is absent. |
| 2. Linguistic accuracy | 7/10 | No Russianisms/Surzhyk found, but the grammar explanation overstates `-ся` as if it simply equals `"oneself"/"myself"` in all cases: `Think of this suffix as...` / `you instantly change the target...`. |
| 3. Pedagogical quality | 7/10 | The PPP skeleton is there, but the core reflexive explanation leans on an overly broad English shortcut instead of staying with the concrete pairs `вмивати → вмиватися`, `одягати → одягатися`. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is covered in prose or examples: `прокидатися`, `вмиватися`, `одягатися`, `снідати`, `йти`, `спочатку`, `потім`; recommended items like `збиратися`, `повертатися`, `поспішати`, `вранці` also appear. |
| 5. Exercise quality | 9/10 | All 4 markers are present and aligned to the plan; they appear after the relevant teaching and match the hinted exercise types/focus. |
| 6. Engagement & tone | 8/10 | The teacher voice is generally solid, but some lines are padded or overstated: `This rule is fundamental to fluent Ukrainian speech...` and `This simple structure is exactly how a native speaker outlines their basic routine.` |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present and ordered correctly; pipeline word count is 1470, above the 1200 target; no dangling sections or formatting breakage. |
| 8. Cultural accuracy | 9/10 | No Russian-centric framing or cultural inaccuracies found. The module treats Ukrainian on its own terms, though it is not especially culture-rich. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers and a plausible roommate setting help, but the opening exchange is still mostly prompt-response: `Ко́ли ти прокида́єшся?` → `Що ти ро́биш по́тім?` → `А коли ти йдеш на робо́ту?` |

## Findings
- [Linguistic accuracy] [SEVERITY: critical]  
Location: `Think of this suffix as the English equivalent of the words "oneself" or "myself." If you take a standard verb and attach this suffix, you instantly change the target of the action from an external object back to the speaker.`  
Issue: This teaches an overgeneralized rule for `-ся/-сь`. The module itself includes `навчаюся`, and the textbook corpus shows broader reflexive meanings than literal self-directed action.  
Fix: Soften the statement to `for many daily-routine verbs` and anchor it to the concrete verb pairs actually taught in this module.

- [Linguistic accuracy] [SEVERITY: critical]  
Location: `These verbs are essential because they describe actions directed at the speaker, which is exactly what a morning routine involves.`  
Issue: The summary repeats the same blanket claim and turns a useful beginner pattern into an absolute rule.  
Fix: Narrow it to `In this module, many of these verbs...`.

- [Plan adherence] [SEVERITY: minor]  
Location: `According to the textbook *Кравцо́ва Grade 4 (p. 113)*, there is a crucial pronunciation note you must memorize to sound natural.`  
Issue: The plan lists three references, but the prose cites only Караман and Кравцова; `Захарійчук Grade 4, p.162` does not appear in the module.  
Fix: Add `Захарійчук Grade 4 (p. 162)` to the pronunciation-reference sentence.

- [Dialogue & conversation quality] [SEVERITY: major]  
Location: first dialogue block, especially `Ко́ли ти прокида́єшся?` / `Що ти ро́биш по́тім?` / `А коли ти йдеш на робо́ту?`  
Issue: The exchange is functional but too interview-like for a “two roommates comparing routines” situation.  
Fix: Add one reciprocal turn so Настя reacts to Ліна’s routine before asking the next question.

- [Engagement & tone] [SEVERITY: minor]  
Location: `This rule is fundamental to fluent Ukrainian speech, and native children practice it extensively in primary school.` and `This simple structure is exactly how a native speaker outlines their basic routine.`  
Issue: These are inflated claims/filler rather than useful A1 guidance.  
Fix: Replace them with concrete practice-oriented phrasing.

## Verdict: REVISE
REVISE because there is a critical grammar overgeneralization about `-ся/-сь`, plus a missing planned reference and weaker-than-planned dialogue/tone. Multiple dimensions are below 9, and there are fixable findings.

<fixes>
- find: 'Think of this suffix as the English equivalent of the words "oneself" or "myself." If you take a standard verb and attach this suffix, you instantly change the target of the action from an external object back to the speaker.'
  replace: 'For many daily-routine verbs, this suffix is roughly similar to "oneself" or "myself." In this module, it helps you understand pairs like **вмивати** → **вмиватися** and **одягати** → **одягатися**.'
- find: "According to the textbook *Кравцо́ва Grade 4 (p. 113)*, there is a crucial pronunciation note you must memorize to sound natural."
  replace: "According to the textbooks *Кравцо́ва Grade 4 (p. 113)* and *Захарійчук Grade 4 (p. 162)*, there is a crucial pronunciation note you must memorize to sound natural."
- find: "> **Ліна:** А я споча́тку п'ю ка́ву, а потім збира́юся. *(I drink coffee first, and then I get ready.)*"
  replace: "> **Ліна:** А я споча́тку п'ю ка́ву, а потім збира́юся. А ти довго сні́даєш? *(I drink coffee first, and then I get ready. Do you spend a long time having breakfast?)*"
- find: "> **Настя:** А коли ти йдеш на робо́ту? *(And when do you go to work?)*"
  replace: "> **Настя:** Ні, недо́вго. А коли ти йдеш на робо́ту? *(No, not long. And when do you go to work?)*"
- find: "This rule is fundamental to fluent Ukrainian speech, and native children practice it extensively in primary school."
  replace: "This spelling-pronunciation difference is common, so it is worth practicing aloud."
- find: "This simple structure is exactly how a native speaker outlines their basic routine. Practice sequencing your own actions using these identical words."
  replace: "This simple structure gives you a clear model for describing your own routine. Practice sequencing your own actions with the same words."
- find: "These verbs are essential because they describe actions directed at the speaker, which is exactly what a morning routine involves."
  replace: "In this module, many of these verbs describe actions directed back toward the speaker, which is why they fit a morning routine well."
</fixes>