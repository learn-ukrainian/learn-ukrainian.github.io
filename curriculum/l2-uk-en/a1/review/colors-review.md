## Linguistic Scan
- Orthographic error: `Ось короткий Діалог.` → `Ось короткий діалог.`

## Exercise Check
Five markers are present, and their type prefixes match the contracted order: `quiz`, `fill-in`, `quiz`, `match-up`, `group-sort`. The problem is placement: `<!-- INJECT_ACTIVITY: match-up-appearance -->` appears before the prose that actually teaches `карі очі`, `русяве волосся`, `сиве волосся`, so that exercise is injected too early.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | Contract Section `Кольори` requires `12 базових кольорів...`; the prose says `we start with twelve базових кольорів` but explicitly lists only six hard-group colors plus `синій`, pushing `блакитний`, `коричневий`, `рожевий`, `помаранчевий`, `фіолетовий` into the next section. Section budgets are also off: `Діалоги` and `Синій ≠ блакитний` are roughly 390 and 399 words against a max of 330. |
| 2. Linguistic accuracy | 8/10 | Most Ukrainian forms are correct, but the very first sentence has an orthographic capitalization error: `Ось короткий Діалог.` |
| 3. Pedagogical quality | 4/10 | The module is dominated by English meta-exposition instead of Ukrainian-first teaching flow: `To describe the visual world...`, `One crucial exception exists...`, `You have learned how to describe the world around you...`. That weakens PPP sequencing and bloats sections with theory. |
| 4. Vocabulary coverage | 7/10 | Core targets do appear in prose: `червоний`, `жовтий`, `зелений`, `синій`, `блакитний`, `білий`, `чорний`, `сірий`, `Якого кольору?`, `карі очі`, `русяве волосся`, `сиве волосся`. Coverage is decent, but the rollout is misallocated across sections. |
| 5. Exercise quality | 8/10 | Marker count and type order match the five `activity_obligations`, but `<!-- INJECT_ACTIVITY: match-up-appearance -->` is placed before the appearance-collocation teaching it is supposed to test. |
| 6. Engagement & tone | 3/10 | Formulaic meta openers and filler recur: `You have learned...`, `Now it is time...`, `Mastering short, direct answers is highly effective for everyday communication.` The teacher voice feels generic rather than anchored in Ukrainian examples. |
| 7. Structural integrity | 8/10 | All four H2 headings are present and ordered, and the pipeline word count is 1505, so the module clears the overall minimum. Structural weakness comes from section-level bloat, not missing sections. |
| 8. Cultural accuracy | 9/10 | The `синій` / `блакитний` contrast is presented on Ukrainian terms, and the module avoids Russian-centric framing. |
| 9. Dialogue & conversation quality | 5/10 | Named speakers are present, but the section is padded with English narration (`Meanwhile, Dmytro and Liza...`) and the line `Я думаю, цей білий светр і коричневі черевики.` sounds clipped and robotic. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Діалоги` — `Ось короткий Діалог.`  
Issue: Unmotivated capitalization of the common noun `діалог`.  
Fix: Change `Діалог` to lowercase: `діалог`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Кольори` — `To describe the visual world, we start with twelve базових кольорів... Six essential hard group colors are...`  
Issue: The section promises twelve base colors but explicitly teaches only six hard-group colors plus `синій`; contracted items are deferred to the next section instead of being rolled out here.  
Fix: Rewrite `Кольори` so Section 2 actually introduces the contracted color inventory and the hard/soft split within the section, while staying inside the 270–330-word budget.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги` and `## Синій ≠ блакитний`  
Issue: Both sections are materially over the contract max because they spend too many words on English framing and glosses rather than contracted teaching beats.  
Fix: Rewrite those sections to fit the 270–330-word budgets and keep only the contracted teaching content.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `## Синій ≠ блакитний` — `<!-- INJECT_ACTIVITY: match-up-appearance -->` placed before `When describing a person's physical appearance in Ukrainian...`  
Issue: The appearance match-up marker is injected before the learner sees the target collocations `карі очі`, `русяве волосся`, `сиве волосся`.  
Fix: Move `<!-- INJECT_ACTIVITY: match-up-appearance -->` to after the appearance-collocation paragraph.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Кольори`, `## Синій ≠ блакитний`, `## Підсумок` — `To describe the visual world...`, `One crucial exception exists...`, `You have learned how to describe the world around you...`  
Issue: English-heavy lecture prose overwhelms the Ukrainian examples and weakens the teach-then-practice flow required for A1.  
Fix: Rewrite these sections in concise, Ukrainian-first pedagogy with examples leading the explanation, not the other way around.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `## Підсумок` — `You have learned...` and `Now it is time to put your new knowledge into practice...`  
Issue: Formulaic meta narration and filler replace concrete teacher guidance.  
Fix: Rewrite the summary as a direct, example-driven recap and self-check in a teacher voice, without generic lesson narration.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `## Діалоги` — `Meanwhile, Dmytro and Liza are preparing for a social event...` and `Я думаю, цей білий светр і коричневі черевики.`  
Issue: The second scene is narrated in English instead of unfolding through dialogue, and the reply is stilted rather than conversational Ukrainian.  
Fix: Rewrite the section so both scenarios are carried by natural Ukrainian turns with named speakers and realistic responses.

## Verdict: REVISE
Multiple dimensions are below 9, there is one definite orthographic error, and three sections need section-level pedagogical rewrites. The contract skeleton and most target vocabulary are salvageable, so this is a revise, not a full reject.

<fixes>
- find: "Ось короткий Діалог."
  replace: "Ось короткий діалог."
- find: "<!-- INJECT_ACTIVITY: match-up-appearance -->\n\nTo describe other items, you need a broader palette."
  replace: "To describe other items, you need a broader palette."
- find: "If someone has grey hair, you must use «сиве волосся» rather than the basic color «сірий».\n\n:::tip"
  replace: "If someone has grey hair, you must use «сиве волосся» rather than the basic color «сірий».\n\n<!-- INJECT_ACTIVITY: match-up-appearance -->\n\n:::tip"
</fixes>

<rewrite-block section="Діалоги">
Rewrite only this section. Keep the exact H2 heading. Stay within 270–330 words. Remove the English framing paragraphs and make both contracted scenarios unfold through natural Ukrainian dialogue with named speakers. Preserve `Якого кольору?`, the flower-market scene, the outfit/recognition scene, and the fixed collocations `карі очі` and `русяве волосся`. Keep the pedagogy lean and A1-level.
</rewrite-block>

<rewrite-block section="Кольори">
Rewrite only this section. Keep the exact H2 heading. Stay within 270–330 words. Teach the contracted color inventory in this section instead of promising twelve and postponing them. Keep the hard-group pattern, the soft-group exception `синій`, and the `Якого кольору...?` short-answer frame. Replace English lecture prose with concise, Ukrainian-first explanation plus examples.
</rewrite-block>

<rewrite-block section="Синій ≠ блакитний">
Rewrite only this section. Keep the exact H2 heading. Stay within 270–330 words. Teach `синій` vs `блакитний` through ready contexts, then add the second-row colors and the appearance collocations `карі очі`, `русяве волосся`, `сиве волосся`. Keep the exercise order intact by placing the appearance match-up marker after the appearance teaching. Remove the long English explanatory block.
</rewrite-block>

<rewrite-block section="Підсумок">
Rewrite only this section. Keep the exact H2 heading. Stay within 270–330 words. Remove the formulaic English lesson narration and replace it with a compact Ukrainian recap plus self-check that reinforces hard vs soft adjective patterns, `Якого кольору?`, and the fixed appearance collocations without introducing A2 material.
</rewrite-block>