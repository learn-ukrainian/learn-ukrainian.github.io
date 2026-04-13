## Linguistic Scan
- Semantic gloss error in `## Діало́ги — Dialogues`: `лежу́` is translated as “I lie down,” and the follow-up paragraph repeats `**лежу** (I lie down)`. SУМ-11 defines `лежати` as being/lying in a horizontal position; “lie down” is `лягати / лягти`.

## Exercise Check
4 markers are present: `fill-in-reflexive-endings`, `quiz-reflexive-choice`, `order-morning-sequence`, `write-morning-routine`.

All four appear after the relevant teaching sections and match the four `activity_hints` in the plan. No inline DSL exercises are present, so there is no answer logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned H2 sections are present and the Karaman/Kravtsova references are cited, but section pacing is badly over budget: approx. 402 / 448 / 402 / 314 words against the planned 300 each, and Dialogue 1 only partly fulfills “Two roommates comparing their morning routines.” |
| 2. Linguistic accuracy | 8/10 | No Russianisms/Surzhyk/Russian characters verified, but Dialogue 2 teaches one wrong meaning: `лежу́` is glossed as “I lie down,” which does not match `лежати`. |
| 3. Pedagogical quality | 6/10 | The lesson spends 115 English words before the first Ukrainian line, and the grammar section says learners can “simply attach **-ся**” right before showing `**вмива́є-ться**`, which is confusing at A1. |
| 4. Vocabulary coverage | 8/10 | Required vocabulary is present, but recommended items `**збира́тися**` and `**поверта́тися**` occur only once each, as list items rather than taught in context. |
| 5. Exercise quality | 9/10 | Four exercise markers are present, correctly placed after the relevant teaching blocks, and they map cleanly to the plan’s four activity hints. |
| 6. Engagement & tone | 6/10 | Several lines drift into inflated meta-language rather than teacherly explanation: “The spelling is perfectly regular, the pronunciation holds a secret” and “Phonetics play a massive role... authentic Ukrainian accent.” |
| 7. Structural integrity | 9/10 | All required H2 headings are present and ordered correctly; markdown is clean; pipeline word count is 1521, so there is no underlength problem. |
| 8. Cultural accuracy | 9/10 | No Russian-centric framing or cultural inaccuracies were found; the module treats Ukrainian on its own terms and uses local school-textbook references. |
| 9. Dialogue & conversation quality | 6/10 | Dialogue 1 is mostly an interview (`Коли...?`, `Що...?`, `А коли...?`) instead of a mutual comparison, so the English narration carries more of the situation than the dialogue itself. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діало́ги — Dialogues` opening paragraph beginning “Every morning has a distinct rhythm...” and overall section pacing (approx. 402 / 448 / 402 / 314 words vs. 300 / 300 / 300 / 300 in the plan)  
Issue: The module covers the planned content, but English scene-setting and meta-explanation push every section well past the intended pacing.  
Fix: Compress the long English setup and meta-commentary so the lesson stays closer to the plan’s section budgets.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Діало́ги — Dialogues`, opening paragraph before the first `> **Ліна:**` line  
Issue: The module delays Ukrainian input with 115 English words before the first example. For PPP/A1, the presentation should reach the target language much faster.  
Fix: Replace the opening paragraph with a two-sentence setup.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `> **Ліна:** У суботу я не поспіша́ю. Прокидаюся пі́зно, лежу́, чита́ю нови́ни. *(On Saturday I do not hurry. I wake up late, lie down, read the news.)*` and `**лежу** (I lie down)` in the next paragraph  
Issue: `лежу / лежати` means “I lie / I am lying,” not “I lie down.”  
Fix: Change the gloss to “I lie / I am lying” or “I lie in bed.”

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Conjugating these verbs is simple because the core mechanics do not change... simply attach **-ся**...` plus the table row `**вмива́є-ться**`  
Issue: The explanation says learners can mechanically add `-ся`, then immediately introduces `-ться` and segmented spellings. That is internally inconsistent and obscures the actual beginner forms `вмиваюся / вмиваєшся / вмивається`.  
Fix: Teach the full written forms directly and explain that 2nd person writes `-шся`, while 3rd person writes `-ться / -ється`.

[VOCABULARY COVERAGE] [SEVERITY: major]  
Location: `## Мій ра́нок — My Morning`, bullet list `**прокидатися** ... **поверта́тися**`  
Issue: `збира́тися` and `поверта́тися` are presented as glossary items only, not in contextualized A1 sentences.  
Fix: Replace the bare list with short example sentences using each verb.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: first weekday dialogue block  
Issue: The plan calls for two roommates comparing routines, but the exchange is mostly one speaker interviewing the other.  
Fix: Make the dialogue reciprocal by giving Ліна a short answer about her own routine.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `:::tip` block in `## Підсумок — Summary`  
Issue: Phrases like “massive role” and “authentic Ukrainian accent” are inflated and generic for an A1 summary.  
Fix: Replace the tip with a short pronunciation practice note tied to the actual examples.

## Verdict: REVISE
REVISE because there is a critical linguistic error (`лежу` glossed as “I lie down”) plus multiple major pedagogy/plan/dialogue issues. The module is structurally usable, but it should not ship unchanged.

<fixes>
- find: |
    Every morning has a distinct rhythm. We use specific verbs to describe daily routines, and in Ukrainian, many of these share a special feature because they describe actions performed on ourselves. Consider a typical morning scenario. Two roommates, **Лі́на** (Lina) and **На́стя** (Nastia), are in their shared kitchen on a Tuesday morning. The time is early, and the sun is just coming up. Lina is an early bird; she is already sitting at the table and drinking her morning coffee. Nastia, however, is just starting her daily routine and walks into the kitchen looking a bit sleepy. Lina asks Nastia about her timing, wanting to know exactly when her day begins. Nastia explains her sequence clearly.
  replace: |
    Two roommates, **Лі́на** and **На́стя**, are talking in the kitchen before work. Ліна asks about Настя's routine, and then they compare weekday and weekend habits.

- find: |
    > **Ліна:** Ко́ли ти прокида́єшся? *(When do you wake up?)*
    > **Настя:** Я прокида́юся о сьо́мій. *(I wake up at seven.)*
    > **Ліна:** Що ти ро́биш по́тім? *(What do you do then?)*
    > **Настя:** Вмива́юся, одяга́юся і сні́даю. *(I wash up, get dressed, and have breakfast.)*
    > **Ліна:** А коли ти йдеш на робо́ту? *(And when do you go to work?)*
    > **Настя:** О во́сьмій. *(At eight.)*
  replace: |
    > **Ліна:** Ко́ли ти прокида́єшся? *(When do you wake up?)*
    > **Настя:** Я прокида́юся о сьо́мій. *(I wake up at seven.)*
    > **Ліна:** Що ти ро́биш по́тім? *(What do you do then?)*
    > **Настя:** Вмива́юся, одяга́юся і сні́даю. *(I wash up, get dressed, and have breakfast.)*
    > **Ліна:** А я споча́тку п'ю ка́ву, а потім збира́юся. *(I drink coffee first, and then I get ready.)*
    > **Настя:** А коли ти йдеш на робо́ту? *(And when do you go to work?)*
    > **Ліна:** О во́сьмій. *(At eight.)*

- find: |
    > **Ліна:** У суботу я не поспіша́ю. Прокидаюся пі́зно, лежу́, чита́ю нови́ни. *(On Saturday I do not hurry. I wake up late, lie down, read the news.)*
  replace: |
    > **Ліна:** У суботу я не поспіша́ю. Прокидаюся пі́зно, лежу́, чита́ю нови́ни. *(On Saturday I do not hurry. I wake up late, lie in bed, and read the news.)*

- find: |
    In this weekend contrast, Lina uses the verb **прокидаюся** (I wake up) again, but follows it with regular, non-reflexive verbs like **лежу** (I lie down) and **читаю** (I read). Nastia mentions another verb with that special ending: **навчаюся** (I study). Mixing these different verb types is how you naturally describe your day in Ukrainian.
  replace: |
    In this weekend contrast, Lina uses the verb **прокидаюся** (I wake up) again, but follows it with regular, non-reflexive verbs like **лежу** (I lie / I am lying) and **читаю** (I read). Nastia mentions another verb with that special ending: **навчаюся** (I study). Mixing these different verb types is how you naturally describe your day in Ukrainian.

- find: |
    Conjugating these verbs is simple because the core mechanics do not change. You take the standard verb endings you already know from Group I and simply attach **-ся** to the very end. The reflexive suffix acts like a fixed addition hooked to the end of the conjugated form. The conjugation paradigm for the present tense demonstrates this consistent pattern.
  replace: |
    In the present tense, reflexive verbs keep the usual personal endings, but beginners should learn the full written forms: **вмиваюся**, **вмиваєшся**, **вмивається**. In writing, the 2nd-person form ends in **-шся**, and the 3rd-person form ends in **-ться / -ється**.

- find: |
    | Займе́нник | Дієсло́во | Переклад |
    | --- | --- | --- |
    | Я | **вмива́ю-ся** | I wash myself |
    | Ти | **вмива́єш-ся** | You wash yourself |
    | Він / Вона́ | **вмива́є-ться** | He / She washes himself/herself |
  replace: |
    | Займе́нник | Дієсло́во | Переклад |
    | --- | --- | --- |
    | Я | **вмива́юся** | I wash myself |
    | Ти | **вмива́єшся** | You wash yourself |
    | Він / Вона́ | **вмива́ється** | He / She washes himself/herself |

- find: |
    Notice that the core endings (**-ю**, **-єш**, **-є**) remain perfectly regular. You just add the **-ся** (or **-ться** for "він / вона") suffix to the end.
  replace: |
    Notice the written pattern: **вмиваюся**, **вмиваєшся**, **вмивається**. For beginners, it is safer to memorize these full forms than to think of them as a mechanical add-on.

- find: |
    *   **прокидатися** (to wake up)
    *   **вмиватися** (to wash face/hands)
    *   **одягатися** (to get dressed)
    *   **збира́тися** (to get ready)
    *   **поверта́тися** (to return home)
  replace: |
    *   **прокидатися** — **Я прокидаюся о сьомій.** (I wake up at seven.)
    *   **вмиватися** — **Потім я вмиваюся.** (Then I wash up.)
    *   **одягатися** — **Після цього я одягаюся.** (After that I get dressed.)
    *   **збира́тися** — **Я швидко збира́юся на роботу.** (I get ready for work quickly.)
    *   **поверта́тися** — **Увечері я поверта́юся додому.** (In the evening I return home.)

- find: |
    :::tip
    Phonetics play a massive role in making your speech sound natural. The written letters and the spoken sounds are entirely different for the **ти** and **він/вона** forms of reflexive verbs. The ending **-шся** must always be pronounced as a long, soft **[с':а]**. The ending **-ється** must always be pronounced as a long, soft **[ц':а]**. Focus heavily on these soft, merged sounds to develop an authentic Ukrainian accent.
    :::
  replace: |
    :::tip
    Practice these aloud: **вмиваєшся** → **[вмиваєс':а]**, **вмивається** → **[вмиваєц':а]**. The spelling stays the same, but the sound changes in fast speech.
    :::
</fixes>