## Linguistic Scan
No linguistic errors found. I verified the higher-risk forms in VESUM (`сонячно`, `дощить`, `подобається`, `взимку`, `восени`, `навесні`, `влітку`, `улюблена`, `температура`) and found no Russianisms, Surzhyk, calques, paronym errors, forbidden Russian characters, or factual grammar/culture errors in the Ukrainian teaching content.

## Exercise Check
- Markers found: `fill-in-weather-dialogue`, `match-up-weather-season`, `fill-in-season-weather` — 3 total, matching the 3 `activity_hints`.
- `match-up-weather-season` and `fill-in-season-weather` appear after the seasons/weather material they are meant to test.
- `fill-in-weather-dialogue` is misplaced: it appears after the impersonal-weather exposition instead of immediately after the dialogue section it is supposed to practice.
- No inline DSL exercise blocks are present.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The plan objective says “Combine weather with seasons and months,” but the module only teaches seasons: “Use the seasonal adverbs **взи́мку** (in winter), **навесні́** (in spring), **влітку** (in summer), and **восени** (in autumn)” and gives no month examples anywhere. |
| 2. Linguistic accuracy | 10/10 | Core forms are standard and verified: “**іде дощ**,” “**іде сніг**,” “**дощи́ть**,” “**сонячно**,” “**влітку**,” “**восени**.” No Russianisms, Surzhyk, calques, paronyms, or grammar misinformation found. |
| 3. Pedagogical quality | 8/10 | The grammar section is example-rich (“**Сьогодні дуже спекотно.**”, “**Вчора було холодно.**”, “**Іде сніг.**”), but the dialogue practice marker is delayed until after the grammar block, weakening PPP presentation→practice flow. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears naturally in prose/dialogue: “**погода**,” “**холодно**,” “**тепло**,” “**дощ**,” “**сніг**,” “**сонце**,” “**сьогодні**,” “**завтра**.” Recommended items like “**спекотно**,” “**прохолодно**,” “**вітер**,” “**хмарно**,” “**ясно**,” “**сонячно**,” “**градус**,” and “**вчора**” are also used. |
| 5. Exercise quality | 8/10 | The marker count is correct, but `<!-- INJECT_ACTIVITY: fill-in-weather-dialogue -->` appears after the weather-grammar exposition rather than directly after the dialogue it is meant to reinforce. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and mostly concrete, built around usable lines like “**Яка сьогодні погода?**” and “**На вулиці тепло**,” without gamified fluff. |
| 7. Structural integrity | 9/10 | All planned H2 sections are present and in order, and the deterministic pipeline word count is 1293, which is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module explains Ukrainian weather patterns on Ukrainian terms (“Ukrainian drops the subject entirely”) and avoids Russia-centering or cultural distortion. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues have named speakers, a real hiking/weather decision, and a season-preference exchange rather than anonymous drill lines. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: Objective in plan: “Combine weather with seasons and months”; generated content: “Use the seasonal adverbs **взи́мку** (in winter), **навесні́** (in spring), **влітку** (in summer), and **восени** (in autumn)”  
Issue: The module covers seasons but never teaches weather with months, so one explicit plan objective is missing.  
Fix: Add a short paragraph with month-based examples, e.g. `У грудні холодно і йде сніг`, `У квітні тепло і сонячно`, `У жовтні часто хмарно і йде дощ`.

[PEDAGOGICAL QUALITY / EXERCISE QUALITY] [SEVERITY: major]  
Location: After “Other weather events use different verbs: **світи́ть со́нце** (the sun is shining) and **дме ві́тер** (the wind is blowing).” the module places `<!-- INJECT_ACTIVITY: fill-in-weather-dialogue -->`  
Issue: The dialogue fill-in practice is detached from the dialogue presentation by a long grammar section, which weakens the intended PPP sequencing.  
Fix: Move `<!-- INJECT_ACTIVITY: fill-in-weather-dialogue -->` to immediately after the dialogue explanation paragraph and before `## Яка погода? (What's the Weather?)`.

## Verdict: REVISE
The module is linguistically solid, but it misses one explicit plan objective (months) and weakens the teaching flow by placing the dialogue practice too late. Dimensions 1, 3, and 5 are below 9, so this cannot pass as-is.

<fixes>
- find: "<!-- INJECT_ACTIVITY: fill-in-weather-dialogue -->"
  replace: ""
- insert_after: "This conversation uses the verb construction **мені подобається** (I like / it is pleasing to me) alongside the adverbs **тепло** (warm), **сонячно** (sunny), and **красиво** (beautiful). Ukrainian relies heavily on these descriptive adverbs to convey states and environments accurately."
  text: "\n\n<!-- INJECT_ACTIVITY: fill-in-weather-dialogue -->"
- insert_after: "You can now describe the environment around you in Ukrainian. The fundamental question is **Яка сьогодні погода?** (What is the weather like today?). To answer, you rely on impersonal adverbs without subjects or verbs: **холодно** (cold), **тепло** (warm), **спекотно** (hot), and **прохолодно** (cool). Precipitation is personified as a moving object, giving us the natural conversational phrases **іде дощ** (it is raining) and **іде сніг** (it is snowing). We also use active verbs for other phenomena, such as **дме вітер** (the wind is blowing) and **світить сонце** (the sun is shining). When you look at the sky, you can describe it as **хмарно** (cloudy), **ясно** (clear), or **сонячно** (sunny). Connecting these conditions to the time of year allows you to build rich sentences like **взимку холодно** (in winter it is cold) or **влітку спекотно** (in summer it is hot)."
  text: "\n\nA useful next step is to connect weather to specific months, not only seasons. For example, **У грудні холодно і йде сніг.** (In December it is cold and it is snowing.) **У квітні тепло і сонячно.** (In April it is warm and sunny.) **У жовтні часто хмарно і йде дощ.** (In October it is often cloudy and raining.) This gives learners the month-level practice promised in the plan."
</fixes>