## Linguistic Scan
2 errors found.

## Exercise Check
4 placeholder markers found, all match the plan's `activity_hints`. Markers are placed logically after their respective reading/grammar sections. No issues.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The plan requires "автобусом" for transport, but the module uses the calqued phrase "на автобусі". All other points covered. |
| 2. Linguistic accuracy | 7/10 | The imperative "Ідіть" (to walk) is incorrectly translated as "Go by subway" in the dialogue. Ukrainian requires "Їдьте" for vehicular transport. Also uses colloquial "на автобусі". |
| 3. Pedagogical quality | 9/10 | Good progression and clear summaries, though the "strictly used" claim about в/на is slightly simplified. |
| 4. Vocabulary coverage | 10/10 | All review vocabulary from the plan is naturally integrated into the text and dialogue. |
| 5. Exercise quality | 10/10 | Four exercise markers correctly placed after their respective grammar/reading blocks. |
| 6. Engagement & tone | 8/10 | Violates the prompt's tone rule by including a self-congratulatory opener: "Congratulations on reaching the end of the A1.5 phase!". |
| 7. Structural integrity | 10/10 | Word count is 1636 (comfortably over the 1200 target). All required headings are present. |
| 8. Cultural accuracy | 10/10 | Contextually rich scenarios (tourist in Kyiv, polite register, Odesa landmarks). |
| 9. Dialogue & conversation quality | 8/10 | Good transactional scenario but contains the critical linguistic error ("Ідіть" vs "Їдьте") which disrupts the reality of the exchange. |

## Findings

[2. Linguistic accuracy] [Critical]
Location: `> **Місцевий:** Музей у центрі. Ідіть на метро до станції Хрещатик. *(The museum is in the center. Go by subway to Khreshchatyk station.)*`
Issue: "Ідіть" strictly means "walk/go on foot" in Ukrainian. You cannot "walk by subway". The English translation "Go by subway" requires the verb "їхати". The correct imperative is "Їдьте".
Fix: Replace "Ідіть на метро" with "Їдьте на метро".

[2. Linguistic accuracy] [Minor]
Location: `using forms like **на автобусі** (by bus) or **на метро** (by subway).`
Issue: While colloquial, "на автобусі" is considered a Russian calque ("на автобусе"). The plan explicitly specified "автобусом". Ukrainian norm prefers the Instrumental case for transport (автобусом).
Fix: Replace "на автобусі" with "автобусом".

[6. Engagement & tone] [Minor]
Location: `Congratulations on reaching the end of the A1.5 phase!  The following points summarize your new achievements.`
Issue: The system prompt explicitly forbids self-congratulatory openers and gamified language ("Congratulations on reaching the end..."). This must be neutral.
Fix: Remove the congratulations and transition smoothly to the summary.

## Verdict: REVISE
The module is comprehensive and well-structured, but contains a critical linguistic error confusing verbs of motion ("іти" vs "їхати") which is fatal for learners. Additionally, there is a minor tone violation and a calqued form. Applying the fixes will resolve these issues.

<fixes>
- find: "> **Місцевий:** Музей у центрі. Ідіть на метро до станції Хрещатик. *(The museum is in the center. Go by subway"
  replace: "> **Місцевий:** Музей у центрі. Їдьте на метро до станції Хрещатик. *(The museum is in the center. Go by subway"
- find: "using forms like **на автобусі** (by bus) or **на метро**"
  replace: "using forms like **автобусом** (by bus) or **на метро**"
- find: "Congratulations on reaching the end of the A1.5 phase!  The following points summarize your new achievements."
  replace: "The following points summarize your A1.5 achievements."
</fixes>
