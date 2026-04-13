## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian letters found.

Critical grammar error:
- In **Мі́сяці і по́ри ро́ку — Months and Seasons**, the text says: `You must add the ending **-і** to the base word... The exception is **лютий**`. That is a false generalization. The safe A1 treatment here is chunk-based (`у січні`, `у лютому`, `у березні`, `у листопаді`), not a single-rule explanation.

## Exercise Check
Three exercise markers are present and placed after the relevant teaching blocks:
- `fill-in-days-order` after **Дні ти́жня**
- `match-up-months-seasons` after **Мі́сяці і по́ри ро́ку**
- `fill-in-day-month-chunks` after **Мі́сяці і по́ри ро́ку**

This matches the plan’s three `activity_hints`. No marker-placement problem found. The actual YAML exercise bodies are not shown here, so distractor logic cannot be fully audited from this prompt alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The weekly dialogue gives `У понеділок я працю́ю ... У вівторок я вивча́ю украї́нську ... У суботу гуля́ю` but never models a clock time, so the objective `Plan a week using days, times, and activities` is only partially met. Dialogue 2 also stops at `Так, поча́ток весни́.` instead of recycling the planned August/summer exchange. |
| 2. Linguistic accuracy | 6/10 | The months section says `You must add the ending **-і** to the base word... The exception is **лютий**`, which teaches an incorrect general rule for month forms. |
| 3. Pedagogical quality | 6/10 | The module presents a broken grammar rule (`add the ending **-і**`) instead of teaching month forms as chunks, and the weekly-planning presentation never combines a day with a clock time despite the stated objective. |
| 4. Vocabulary coverage | 9/10 | All required core items appear in prose: days of the week, all 12 months, all 4 seasons, `ти́ждень`, and `день наро́дження`. Ordinal-date language is also modeled in `П'ятна́дцятого бе́резня`. |
| 5. Exercise quality | 9/10 | The three markers align with the three planned activity types and are placed after the relevant teaching sections. |
| 6. Engagement & tone | 7/10 | The summary shifts into inflated phrasing: `Learning this vocabulary is a vital step in thinking like a Ukrainian` and `aligning yourself with the cultural rhythms of Ukraine`, which adds hype instead of instruction. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present in order, the markdown is clean, and the pipeline word count is 1293, above target. |
| 8. Cultural accuracy | 6/10 | The `неділя` explanation centers Russian: `In Russian, a similar-sounding word means "week."` The rubric explicitly asks for Ukrainian on its own terms, not `like Russian but...` framing. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers are a plus, but Dialogue 1 is mostly one speaker prompting short schedule answers, and Dialogue 2 ends before the reciprocal birthday exchange promised in the plan. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Мі́сяці і по́ри ро́ку — Months and Seasons** — `You must add the ending **-і** to the base word... The exception is **лютий**`  
Issue: This teaches a false rule. Month forms in this module should be taught as memorized chunks, not as a universal `-і` rule with one exception.  
Fix: Replace the paragraph with an accurate chunk-based explanation including `у сі́чні`, `у лю́тому`, `у бе́резні`, `у кві́тні`, `у се́рпні`, `у листопа́ді`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: **Діало́ги — Dialogues** — `> **Марко:** У вівторок я вивча́ю украї́нську.`  
Issue: The plan objective says learners should plan a week using days, times, and activities, but the weekly dialogue never models a clock time.  
Fix: Add at least one day + time + activity line, e.g. `У вівторок о сьомій вечора я вивча́ю украї́нську.`

[PLAN ADHERENCE] [SEVERITY: major]  
Location: **Діало́ги — Dialogues** — the birthday exchange ends at `> **Софія:** Так, поча́ток весни́.`  
Issue: The planned reciprocal follow-up (`А у тебе? — У мене в серпні. — О, це літо!`) is missing, so the dialogue underuses the target months/seasons pattern.  
Fix: Extend the dialogue with the reciprocal August/summer exchange.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: **Дні ти́жня — Days of the Week** — `In Russian, a similar-sounding word means "week."`  
Issue: This is Russian-centered framing. The rubric explicitly asks for Ukrainian explained on its own terms.  
Fix: Replace the paragraph with a Ukrainian-centered explanation: `неділя` = Sunday, `тиждень` = week.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: **Підсумок — Summary** — `Learning this vocabulary is a vital step in thinking like a Ukrainian... aligning yourself with the cultural rhythms of Ukraine.`  
Issue: The tone becomes inflated and essentializing instead of instructional.  
Fix: Replace this with a concrete practice-oriented summary focused on schedules, birthdays, and seasons.

## Verdict: REVISE
REVISE. There is one critical grammar-teaching error, plus multiple major plan/cultural issues. Several dimensions are below 9, and the module needs deterministic fixes before it can ship.

<fixes>
- find: |-
    When you want to say that something happens "in" a specific month, you again use the prepositions **у** or **в**. However, months require a different grammatical ending than days. You must add the ending **-і** to the base word. Often, the final fleeting vowel **-е-** in the month's name drops out. Here is the pattern you need to learn: **січень** → **у січні** (in January), **березень** → **у березні** (in March), **квітень** → **у квітні** (in April), **жовтень** → **у жо́втні** (in October). The exception is **лютий**, which takes a different ending: **у лю́тому** (in February).
  replace: |-
    When you want to say that something happens "in" a specific month, you again use the prepositions **у** or **в**. At A1 level, the safest approach is to learn each month together with its "in" form as a fixed chunk, rather than forcing one ending onto every month name. Useful chunks are: **січень** → **у сі́чні** (in January), **лютий** → **у лю́тому** (in February), **березень** → **у бе́резні** (in March), **квітень** → **у кві́тні** (in April), **серпень** → **у се́рпні** (in August), **листопад** → **у листопа́ді** (in November).

- find: |-
    > **Марко:** У вівторок я вивча́ю украї́нську. *(On Tuesday I study Ukrainian.)*
  replace: |-
    > **Марко:** У вівторок о сьомій вечора я вивча́ю украї́нську. *(On Tuesday at seven in the evening I study Ukrainian.)*

- find: |-
    > **Андрі́й:** Софіє, коли́ у тебе́ день наро́дження? *(Sofia, when is your birthday?)*
    > **Софія:** У бе́резні. *(In March.)*
    > **Андрій:** Яко́го чи́сла? *(What date?)*
    > **Софія:** П'ятна́дцятого бе́резня. *(The fifteenth of March.)*
    > **Андрій:** Це весна́? *(Is that spring?)*
    > **Софія:** Так, поча́ток весни́. *(Yes, the beginning of spring.)*
  replace: |-
    > **Андрі́й:** Софіє, коли́ у тебе́ день наро́дження? *(Sofia, when is your birthday?)*
    > **Софія:** У бе́резні. *(In March.)*
    > **Андрій:** Яко́го чи́сла? *(What date?)*
    > **Софія:** П'ятна́дцятого бе́резня. *(The fifteenth of March.)*
    > **Андрій:** Це весна́? *(Is that spring?)*
    > **Софія:** Так, поча́ток весни́. *(Yes, the beginning of spring.)*
    > **Софія:** А у тебе́? *(And yours?)*
    > **Андрій:** У ме́не в се́рпні. О, це лі́то! *(Mine is in August. Oh, that's summer!)*

- find: |-
    Let us focus specifically on the word **неділя** (Sunday). For learners coming from other Slavic languages, this word can be a tricky false friend. In Russian, a similar-sounding word means "week." In Ukrainian, **неділя** only means Sunday. The etymology is fascinating and helps anchor its meaning: it comes from the phrase "не ділати," which translates to "not to work." Note that while **неділя** means Sunday in standard Ukrainian, in some regional dialects it can also mean "week." However, the standard word for "week" is always **тиждень**.
  replace: |-
    Let us focus specifically on the word **неділя** (Sunday). In standard Ukrainian, **неділя** means only the seventh day of the week. If you want to say "week," the standard word is **тиждень**. This is an important contrast to memorize early: **неділя** = Sunday, **тиждень** = week.

- find: |-
    Learning this vocabulary is a vital step in thinking like a Ukrainian. By using native Slavic names like **березень** instead of Latin-based alternatives, and by structuring your week to begin on **понеділок**, you are aligning yourself with the cultural rhythms of Ukraine. Remember to practice the soft endings on months like **січень** and **вересень** to make your pronunciation sound natural and authentic. The soft sign **ь** indicates that the preceding consonant is soft.
  replace: |-
    This vocabulary helps you talk about schedules, birthdays, and seasons more naturally in Ukrainian. Remember that days and months are written in lowercase, and learn common time chunks such as **у понеділок**, **у березні**, and **взимку**. The soft sign **ь** indicates that the preceding consonant is soft.
</fixes>