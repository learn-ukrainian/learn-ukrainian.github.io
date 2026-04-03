## Linguistic Scan
1 error found:
- Russian calque ("по імені" instead of "на ім'я") used in the Summary section.
*All other Ukrainian vocabulary and grammar structures are verified correct and appropriate for A1.*

## Exercise Check
**MAJOR ISSUES FOUND:** The injected activity markers are completely scrambled and do not match the surrounding pedagogical context.
- `activity-1` (Vocative + imperative fill-in) is set up as if it were a reading comprehension question block. The writer hallucinates an instruction to "Answer these questions in a single sentence" which is not supported by the activity YAML.
- `activity-3` (Complete complex sentences with що/де/коли) is placed at the end of the *Holiday greetings* section, testing unrelated concepts.
- `activity-4` (Holiday match) is placed directly after a dialogue about a *school fair* and is introduced with the confusing instruction to "circle every vocative case...".

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module is missing the "Next: A1.8..." teaser from the Summary outline. It also misses `тому що` which was specified in the objectives block. The writer correctly mapped `dialogue_situations` to the dialogue section. |
| 2. Linguistic accuracy | 9/10 | One Russian calque detected: "звертатися по імені" (should be "на ім'я"). Otherwise, excellent grammar and formatting. |
| 3. Pedagogical quality | 7/10 | DEDUCT: Marker placement breaks pedagogical flow completely. The text asks students to "Answer these questions" but injects a grammar fill-in. |
| 4. Vocabulary coverage | 10/10 | Uses all required A1.7 vocabulary naturally across both reading and dialogue sections. |
| 5. Exercise quality | 5/10 | DEDUCT: Total mismatch between prose setup, marker placement, and the plan's `activity_hints`. |
| 6. Engagement & tone | 9/10 | Good checkpoint tone. Avoids being overly robotic while still clearly summarizing the phase's skills. |
| 7. Structural integrity | 10/10 | Clean Markdown. All expected H2 headings are present and the word count is safely within the target range. |
| 8. Cultural accuracy | 10/10 | Accurately teaches Ukrainian holiday greetings (З Різдвом, З Великоднем) and traditional foods (кутя) without relying on stereotypes. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue is instructional but functions perfectly as an end-of-phase checkpoint to show vocative and imperative in action. |

## Findings

[5. Exercise quality] [critical]
Location: `## Чита́ння (Reading Practice)`, `## Грама́тика (Grammar Summary)`, `## Діало́г (Connected Dialogue)`
Issue: The activity markers are completely mismatched with their surrounding context and prose setup. `activity-1` is set up as reading comprehension questions; `activity-3` (complex sentences) is placed after holiday greetings; `activity-4` (holiday match) is placed after a dialogue about a school fair. This completely breaks the pedagogical flow.
Fix: Remove the hallucinated reading questions and move `activity-1` after the imperative summary; place `activity-2` and `activity-3` after the subordinating conjunctions; place `activity-4` after the holiday greetings block.

[2. Linguistic accuracy] [major]
Location: `## Підсумок — Summary`
Issue: The phrase "звертатися до люде́й по і́мені" uses a Russian calque ("по імені"). Textbooks and style guides dictate that the correct Ukrainian idiom is "звертатися на ім'я".
Fix: Replace "по і́мені" with "на ім'я́".

[1. Plan adherence] [major]
Location: `## Підсумок — Summary`
Issue: The plan outline explicitly requests "Next: A1.8 — Past, Future, Graduation" to be included in the summary, but it was omitted.
Fix: Add "**Next: A1.8 — Past, Future, Graduation.**" to the end of the summary.

[1. Plan adherence] [minor]
Location: `## Грама́тика (Grammar Summary)`
Issue: The plan objectives require teaching "і, а, але, бо, тому що", but `тому що` was completely omitted from the text (likely because it was missing from the `content_outline` bullet).
Fix: Add a bullet for `тому що` to the coordinating/subordinating conjunctions list.

## Verdict: REVISE
The text has a critical pedagogical failure regarding the placement and setup of the exercise markers, as well as a major linguistic calque and missed plan points. These must be patched deterministically before the module can be published.

<fixes>
- find: "**З Різдвом!**» (Merry Christmas!)\n\nLet's check your understanding. Answer these questions in a single sentence:\n1. **Що про́сить Олена?** (What does Olena ask for?)\n2. **Що ма́є Тарас?** (What does Taras have?)\n\n<!-- INJECT_ACTIVITY: activity-1 -->\n\n## Грама́тика (Grammar Summary)"
  replace: "**З Різдвом!**» (Merry Christmas!)\n\n## Грама́тика (Grammar Summary)"

- find: "| **принести** (to bring) | **принеси!** | **принесіть!** |\n\nConjunctions connect your thoughts."
  replace: "| **принести** (to bring) | **принеси!** | **принесіть!** |\n\n<!-- INJECT_ACTIVITY: activity-1 -->\n\nConjunctions connect your thoughts."

- find: "- **бо** (because: **Принеси кутю, бо я не вмі́ю вари́ти.** - Bring kutia, because I don't know how to cook.)\n\nSubordinating conjunctions"
  replace: "- **бо** (because: **Принеси кутю, бо я не вмі́ю вари́ти.** - Bring kutia, because I don't know how to cook.)\n- **тому́ що** (because: **Я йду, тому́ що вже пі́зно.** - I am going, because it is already late.)\n\nSubordinating conjunctions"

- find: "- **коли** (**Я не знаю, коли ти вільний.** - I don't know when you are free.)\n\n<!-- INJECT_ACTIVITY: activity-2 -->\n\nThe holiday greeting formula uses"
  replace: "- **коли** (**Я не знаю, коли ти вільний.** - I don't know when you are free.)\n\n<!-- INJECT_ACTIVITY: activity-2 -->\n\n<!-- INJECT_ACTIVITY: activity-3 -->\n\nThe holiday greeting formula uses"

- find: "**З Новим ро́ком!** (Happy New Year!), **З днем наро́дження!** (Happy Birthday!).\n\n<!-- INJECT_ACTIVITY: activity-3 -->\n\n## Діало́г (Connected Dialogue)"
  replace: "**З Новим ро́ком!** (Happy New Year!), **З днем наро́дження!** (Happy Birthday!).\n\n<!-- INJECT_ACTIVITY: activity-4 -->\n\n## Діало́г (Connected Dialogue)"

- find: "This is exactly what natural A1.7 Ukrainian looks like in action.\n\n<!-- INJECT_ACTIVITY: activity-4 -->\n\n## Підсумок — Summary"
  replace: "This is exactly what natural A1.7 Ukrainian looks like in action.\n\n## Підсумок — Summary"

- find: "✅ **Ти мо́жеш зверта́тися до люде́й по і́мені:** (You can address people by name:)"
  replace: "✅ **Ти мо́жеш зверта́тися до люде́й на ім'я́:** (You can address people by name:)"

- find: "**З Різдвом! З Великоднем!**\n\n**Deterministic word count:"
  replace: "**З Різдвом! З Великоднем!**\n\n**Далі (Next): A1.8 — Past, Future, Graduation.**\n\n**Deterministic word count:"
</fixes>
