## Linguistic Scan
[NEEDS RAG VERIFICATION] Location: the `:::caution` box in **Діалоги**. The claim that `відкрити підручник` is “a calque” and that `розгорнути` is the “gold standard” could not be verified in local style-guide data. Textbook search does show `Розгорніть підручники!` / `Розгорніть підручник...`, but that does not prove `відкрити підручник` is wrong.

No Russianisms, Surzhyk forms, paronym errors, or forbidden Russian letters (`ы`, `э`, `ё`, `ъ`) found.

## Exercise Check
Markers present: `quiz-imperative-choice`, `group-sort-forms`, `fill-in-imperative-forms`, `fill-in-polite-requests`.

The marker IDs match the four `activity_hints` in the plan, and there are enough markers total.

Issue found:
- `<!-- INJECT_ACTIVITY: group-sort-forms -->` appears before the `ви`-form teaching begins. The learner has seen `ти` forms and irregulars, but the contrastive `ви` section starts only after that marker, so the exercise is placed too early.

No inline DSL exercise blocks were present.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned H2 sections are present and the core plan verbs recur throughout, but the lesson front-loads a long English paragraph starting “We use commands, requests, and instructions every single day...”, which pushes the module away from the plan’s dialogue-first pacing. |
| 2. Linguistic accuracy | 7/10 | I found no Russian letters or obvious bad Ukrainian forms, and spot-checked imperatives like `читайте`, `пишіть`, `дивіться`, `сідай`, `ідіть`, `скажіть`. The weak point is the caution-box claim: “`відкрити підручник` ... linguists often consider it a calque ... `розгорнути` is the gold standard!” |
| 3. Pedagogical quality | 6/10 | The lesson spends a long English paragraph before the first Ukrainian dialogue, and the rule text later says “The vowel sound becomes softer and higher,” which is vague phonetic theory instead of a clean A1 pattern explanation. |
| 4. Vocabulary coverage | 9/10 | Required verbs from the plan are well covered: `читати`, `писати`, `слухати`, `дивитися`, `говорити`, `дати`, `сказати`, `іти`. Recommended classroom vocabulary like `підручник`, `сторінка`, `речення`, `запитати`, `відкрити`, `сісти` also appears in context. |
| 5. Exercise quality | 7/10 | All four planned markers are present, but `<!-- INJECT_ACTIVITY: group-sort-forms -->` comes before “Forming the **ви** (formal or plural) imperative...”, so the learner is tested on a contrast before both sides are taught. |
| 6. Engagement & tone | 7/10 | The teacher voice improves once the examples start, but the opening relies on generic lines like “the imperative mood is absolutely essential” instead of getting to the Ukrainian quickly. |
| 7. Structural integrity | 8/10 | The planned H2 headings are present and the pipeline word count is 1666, so the module clears the target. The weakness is prose-heavy front-loading before practice. |
| 8. Cultural accuracy | 7/10 | The module avoids Russian-centered framing, but the `відкрити підручник` caution box introduces unsupported prescriptivism about what is “stylistically perfect” Ukrainian. |
| 9. Dialogue & conversation quality | 8/10 | The dialogues use named speakers and real situations, especially the classroom exchange. The main issue is that the surrounding English explanation is longer than it needs to be, which weakens the immediacy of the dialogue work. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: major]  
Location: `:::caution The phrase **відкрити підручник** (to open the textbook) is very common in spoken Ukrainian and appears in many classrooms. However, linguists often consider it a calque. The more traditional, stylistically perfect Ukrainian phrase for opening a book is **розгорнути підручник** (to unfold the textbook). You will hear both, but **розгорнути** is the gold standard! :::`  
Issue: This teaches an unverified prescriptive claim as fact. Local style-guide search did not confirm that `відкрити підручник` is a calque.  
Fix: Remove the prescriptive claim and replace it with a neutral note, or delete the box entirely.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `We use commands, requests, and instructions every single day. Whether asking a friend to **відкрити** (to open) a door...`  
Issue: The lesson opens with a long generic English paragraph before any Ukrainian input. That weakens PPP flow and bloats the section with exposition instead of example-first teaching.  
Fix: Replace the paragraph with a short setup that points directly to the two dialogues and the `ти` / `ви` contrast.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `A phonetic shift is required for certain verbs. When the **ти** form ends in **-и** or a consonant (like **пиши**, **сиди**, **скажи**), the **ви** form takes the ending **-іть** (instead of "-ить"), and the stress shifts to this new ending. The vowel sound becomes softer and higher.`  
Issue: This explanation is muddled for A1. Its own examples do not illustrate the “or a consonant” part clearly, and “The vowel sound becomes softer and higher” is not useful beginner guidance.  
Fix: Replace it with a simple pattern-based explanation focused on visible form changes.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: group-sort-forms -->` placed before `Forming the **ви** (formal or plural) imperative requires...`  
Issue: The group-sort exercise tests `ти` vs `ви` forms before the `ви` forms have been taught.  
Fix: Move the marker to after the `ви`-form examples.

## Verdict: REVISE
The module is structurally complete and contains mostly correct Ukrainian forms, but it still has actionable quality problems: one unverified linguistic prescription, one too-early exercise marker, and two pedagogy issues that make the lesson wordy and less clear than the plan requires. Several dimensions are below 9, so this cannot pass as-is.

<fixes>
- find: |
    :::caution
    The phrase **відкрити підручник** (to open the textbook) is very common in spoken Ukrainian and appears in many classrooms. However, linguists often consider it a calque. The more traditional, stylistically perfect Ukrainian phrase for opening a book is **розгорнути підручник** (to unfold the textbook). You will hear both, but **розгорнути** is the gold standard!
    :::
  replace: |
    In classroom speech, you may also hear **розгорнути підручник**. At this level, focus on recognizing and using the imperative forms themselves.

- find: |
    We use commands, requests, and instructions every single day. Whether asking a friend to **відкрити** (to open) a door, telling a dog to **сісти** (to sit down), or instructing someone to **показати** (to show) you a menu, the imperative mood is absolutely essential. At the A1 level, mastering these direct requests allows for confident and clear communication. You will hear these forms in stores, on the street, and in classrooms. By learning just a few common verbs, you can actively participate in conversations rather than just listening. Observe these two common situations where these requests happen naturally. First is a formal classroom setting where a teacher gives clear instructions to students about an exercise in a **підручник** (textbook). A student asks about a **сторінка** (page) and how to write a **речення** (sentence), and asks permission to **запитати** (to ask) a question. Second is an informal chat between two friends deciding what to do at a cafe. The verb forms change depending on who is being addressed.
  replace: |
    Commands and requests appear constantly in everyday Ukrainian. Read the two dialogues first, then notice how the verb forms change when the speaker addresses one person (**ти**) or a group / a person formally (**ви**).

- find: |
    A phonetic shift is required for certain verbs. When the **ти** form ends in **-и** or a consonant (like **пиши**, **сиди**, **скажи**), the **ви** form takes the ending **-іть** (instead of "-ить"), and the stress shifts to this new ending. The vowel sound becomes softer and higher.
  replace: |
    For many verbs whose **ти** form ends in **-и**, the **ви** form uses **-іть**. Learn this as a pattern from examples: **пиши → пишіть**, **скажи → скажіть**, **іди → ідіть**, **говори → говоріть**. Reflexive forms like **дивись** become **дивіться**.

- find: "<!-- INJECT_ACTIVITY: group-sort-forms -->"
  replace: ""

- find: |
    *   **говори** → **говоріть**

    To see this in action, observe a sports scenario where a coach is giving quick, direct instructions to the team:
  replace: |
    *   **говори** → **говоріть**

    <!-- INJECT_ACTIVITY: group-sort-forms -->

    To see this in action, observe a sports scenario where a coach is giving quick, direct instructions to the team:
</fixes>