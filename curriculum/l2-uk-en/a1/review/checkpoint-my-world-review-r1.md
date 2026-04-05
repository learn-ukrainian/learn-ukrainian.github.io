## Linguistic Scan
No major linguistic errors found. Minor stylistic polish items identified.

## Exercise Check
- `<!-- INJECT_ACTIVITY: group-sort-vocab-categories -->` is present after the first section ( Що ми знаємо?). Matches plan.
- `<!-- INJECT_ACTIVITY: quiz-gender-agreement -->` is present after the grammar summary. Matches plan.
- `<!-- INJECT_ACTIVITY: quiz-singular-plural -->` is present after the grammar summary. Matches plan.
- `<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->` is present after the dialogue. Matches plan.
Markers are well distributed and match the hints.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covers all 6 points and themes from the plan. Deducting 1 point because the deterministic word count (1483) is >20% over the target (1200). |
| 2. Linguistic accuracy | 9/10 | Good use of target grammar. Deducting 1 point for a minor stylistic calque ("На столі є лампа") and a missing typological dash in parallel syntax ("Та біла. А ця — синя"). |
| 3. Pedagogical quality | 10/10 | Excellent summary format for a Checkpoint. Clear patterns, strong rule definitions, and highly contextual examples that stick strictly to M08-M13 limits. |
| 4. Vocabulary coverage | 10/10 | Required cultural vocab (вишиванка, глечик, писанки, намисто) effectively contextualized in the market dialogue. Good reuse of colors and numbers. |
| 5. Exercise quality | 10/10 | All 4 activity markers injected at the correct logical points (after instruction/review blocks). |
| 6. Engagement & tone | 9/10 | Conversational and supportive tone. A little bit of "telling instead of showing" at the end ("Your vocabulary milestone is real..."), but acceptable for a checkpoint milestone. |
| 7. Structural integrity | 9/10 | Clean Markdown and good flow, but deducting 1 point due to exceeding the word count budget significantly (+283 words). |
| 8. Cultural accuracy | 10/10 | Excellent authentic cultural details regarding ярмарки, вишиванки, and глечики. |
| 9. Dialogue & conversation quality | 10/10 | Natural shopping interaction. Good illustration of "цей" vs "той" distance mechanics in practice. |

## Findings

[2. Linguistic accuracy] [minor]
Location: Читання (Reading Practice) - `На столі є лампа. Ця лампа біла.`
Issue: "На столі є лампа" is a slight calque of English "there is a lamp on the table". In Ukrainian, for objects located somewhere, the verb of presence 'є' is typically omitted ("На столі лампа") unless emphasizing existence vs absence.
Fix: Remove "є" for a more natural nominal sentence.

[2. Linguistic accuracy] [minor]
Location: Діалог - `> **Катя:** Та біла. А ця — синя й червона.`
Issue: Missing typological dash for the omitted verb in the parallel structure ("Та біла" vs "А ця — синя").
Fix: Add the dash to "Та — біла."

## Verdict: REVISE
The module is high-quality, but there are minor linguistic and stylistic fixes required before it passes the quality gate.

<fixes>
- find: "На столі є лампа. Ця лампа біла."
  replace: "На столі лампа. Ця лампа біла."
- find: "**Катя:** Та біла. А ця — синя й червона. *(That one is white. And this one is blue and red.)*"
  replace: "**Катя:** Та — біла. А ця — синя й червона. *(That one is white. And this one is blue and red.)*"
</fixes>
