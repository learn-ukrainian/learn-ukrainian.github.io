## Linguistic Scan
No linguistic errors found.

## Exercise Check
Three exercise markers are present: `fill-in-schedule-time`, `match-invitations`, and `fill-in-weekly-plan`.

Each marker comes after the relevant teaching:
- `fill-in-schedule-time` and `match-invitations` follow the Planning section that teaches day/time patterns and invitation chunks.
- `fill-in-weekly-plan` follows the My Week modeling section.

The marker count matches the three `activity_hints` in the plan. No inline exercise-logic errors are visible from the marker placeholders alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned H2 sections are present and the core topics are covered, but section pacing is badly off the plan’s 300-word design: computed section counts are `Dialogues 538`, `Планування 458`, `Мій тиждень 394`, `Summary 308`. The My Week model also breaks the plan point “Each day = буду + activity” with “`У п'ятницю я буду відпочивати. Я піду в кіно.`” |
| 2. Linguistic accuracy | 10/10 | No confirmed Russianisms, Surzhyk, calques, paronym errors, bad case endings, or false grammar claims. The prompt’s VESUM verification already confirms all non-name Ukrainian words in the module. |
| 3. Pedagogical quality | 6/10 | The module has too much English meta-explanation, e.g. “`This short conversation is rich with real-world communication patterns...`”, which reduces Ukrainian input. More importantly, the Planning section gives present-tense models — “`У понеділок вранці я працюю.`”, “`У суботу ввечері ми читаємо.`” — immediately before teaching the target formula “`У [day] о [time] я буду [verb]`”. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is used in context: “`тиждень`”, “`вільний / вільна`”, “`зустріч`”, “`відпочивати`”, “`прибирати квартиру`”, “`вечірка`”. Recommended items also appear naturally, including “`зустрінемося`”, “`допізна`”, “`звичайно`”, “`кіно`”, and “`вчити`”. |
| 5. Exercise quality | 9/10 | The three markers align well with the three `activity_hints`, and each appears after the material it should test. No visible logic problems are present in the placeholders. |
| 6. Engagement & tone | 7/10 | The teacher voice is generally calm and usable, but parts of the Summary drift into generic filler: “`The ability to structure your time and share your schedule is a major milestone in communication.`” and “`This pattern is the primary way you will express future plans in the early stages of your learning journey.`” |
| 7. Structural integrity | 10/10 | Clean markdown, all planned H2 headings are present and ordered correctly, markers are intact, and the pipeline word count is 1665, which is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | No Russia-centric framing or suspect cultural claims. Ukrainian is presented on its own terms. |
| 9. Dialogue & conversation quality | 8/10 | Dialogue 1 is natural and multi-turn. Dialogue 2 is much flatter: one speaker lists “`У понеділок... У вівторок... У середу...`” while the other mostly prompts, so it reads more like a schedule dump than a lively planning exchange. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: Dialogues and Planning sections; e.g. “`This short conversation is rich with real-world communication patterns...`” and “`This second dialogue shifts focus from a single day to the entire week...`”  
Issue: English meta-commentary bloats the sections far past the plan’s 300-word pacing and displaces Ukrainian input/practice.  
Fix: Compress these paragraphs into brief form-focused notes.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: Planning section — “`У понеділок вранці я працюю.`”, “`У суботу ввечері ми читаємо.`”, “`В неділю вдень вона гуляє.`”  
Issue: The section models present tense immediately before explicitly teaching analytic future, which muddies the target pattern for A1 learners.  
Fix: Replace these examples with analytic-future versions.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: My Week model — “`У п'ятницю я буду відпочивати. Я піду в кіно.`”  
Issue: This breaks the plan’s stated pattern “Each day = буду + activity” and undercuts the following claim that Taras uses “the same foundational structure for every single day.”  
Fix: Rewrite the Friday cinema sentence so it stays in the taught analytic-future pattern.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: Summary opener — “`The ability to structure your time and share your schedule is a major milestone in communication...`”  
Issue: This is generic encouragement rather than instruction, and it spends words without adding much learning value.  
Fix: Shorten it to a direct recap of the module’s core pattern.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: minor]  
Location: Dialogue 2 — “`> **Антон:** А у четвер?`”  
Issue: The second dialogue is too one-sided; Anton mostly prompts while Viktor recites a schedule.  
Fix: Add one short reactive turn so the exchange feels more conversational.

## Verdict: REVISE
REVISE. The module has no confirmed Ukrainian-language errors, but it has clear fixable quality problems: section pacing is well outside plan, the Planning section briefly teaches the wrong tense pattern for the module’s target, and the My Week model breaks the promised `буду + infinitive` structure. Several dimensions are below 9, so it cannot pass.

<fixes>
- find: |-
    This short conversation is rich with real-world communication patterns. Notice how Максим combines a time of day with a future action to structure his day. He uses the words **зранку** (in the morning) and **вдень** (in the afternoon) to divide his Saturday into clear segments. Дарина shifts the conversation from personal routines to a shared invitation. Then, Оксана quickly confirms the specific time using the question phrase **о котрій?** (at what time?). This flow moves logically from individual tasks to a shared group activity, representing exactly how friends communicate.
  replace: |-
    Notice the time words **зранку** and **вдень**, plus the scheduling question **о котрій?**. The dialogue moves from individual plans to a shared invitation.

- find: |-
    This second dialogue shifts focus from a single day to the entire week. The speakers map out their obligations chronologically, from Monday to Friday. They use the days of the week alongside the future tense to create a clear timeline of events like a **зустріч** (meeting) or a **вечірка** (party). Notice the question **Ти будеш?** (Will you be there?) — this is a highly natural, conversational way to confirm attendance at an event. You do not always need a full verb like "attend"; the verb "to be" in the future tense is perfectly sufficient for asking if someone plans to show up.
  replace: |-
    This dialogue maps out the week from Monday to Friday and shows a natural attendance question: **Ти будеш?**

- find: |-
    To express what you plan to do at these times, use the compound future tense. This structure is very straightforward: use the future form of the verb "to be" (**бути**), which must match the subject (like **я буду**, **ти будеш**, **ми будемо**), and add an imperfective infinitive verb. The imperfective aspect emphasizes the process or the duration of the action, which is perfect for laying out a continuous schedule. The full structural formula is **У [day] о [time] я буду [verb]**.
  replace: |-
    To express a plan, use the compound future tense: **я буду**, **ти будеш**, **ми будемо** + imperfective infinitive. The core pattern is **У [day] о [time] я буду [verb]**.

- find: |-
    - У понеділок вранці я працюю. *(On Monday morning I work.)*
    - У суботу ввечері ми читаємо. *(On Saturday evening we read.)*
    - В неділю вдень вона гуляє. *(On Sunday afternoon she walks.)*
  replace: |-
    - У понеділок вранці я буду працювати. *(On Monday morning I will work.)*
    - У суботу ввечері ми будемо читати. *(On Saturday evening we will read.)*
    - В неділю вдень вона буде гуляти. *(On Sunday afternoon she will walk.)*

- find: |-
    У понеділок я буду працювати. Після роботи буду вчити українську. У вівторок я буду обідати в кафе. У середу ввечері я буду дивитися футбол. У четвер я буду готувати вечерю для родини. У п'ятницю я буду відпочивати. Я піду в кіно. У суботу зранку я буду прибирати. Вдень я буду гуляти в парку. В неділю я буду спати довго!
  replace: |-
    У понеділок я буду працювати. Після роботи буду вчити українську. У вівторок я буду обідати в кафе. У середу ввечері я буду дивитися футбол. У четвер я буду готувати вечерю для родини. У п'ятницю я буду відпочивати. Я буду дивитися фільм у кіно. У суботу зранку я буду прибирати. Вдень я буду гуляти в парку. В неділю я буду спати довго!

- find: |-
    The ability to structure your time and share your schedule is a major milestone in communication. The core grammatical formula for scheduling in this module is extremely reliable: Day + time + буду + infinitive. This scheduling focus aligns with **State Standard 2024, §4.2.4.1**. This pattern is the primary way you will express future plans in the early stages of your learning journey.
  replace: |-
    The core scheduling formula in this module is clear and reliable: Day + time + буду + infinitive. This focus aligns with **State Standard 2024, §4.2.4.1**.

- find: |-
    > **Антон:** А у четвер? *(And on Thursday?)*
  replace: |-
    > **Антон:** О, у тебе багато планів! А у четвер? *(Oh, you have a lot of plans! And on Thursday?)*
</fixes>