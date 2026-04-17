## Linguistic Scan
No linguistic errors found.

## Exercise Check
6 `INJECT_ACTIVITY` markers are present.

Type prefixes match the contract:
`quiz → match-up → group-sort → letter-grid → fill-in → watch-and-repeat`

One contract-order problem:
the module’s actual order is `quiz → match-up → group-sort → letter-grid → fill-in → watch-and-repeat`, but the contracted order is `quiz → match-up → fill-in → group-sort → letter-grid → watch-and-repeat`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Section order and budgets are all on target, but the `Привіт!` section does not deliver the contracted introduction dialogue act `Привіт! Як тебе звати? Мене звати...`; instead the hallway exchange is `**Марко**: Привіт! Як справи?` / `**Софія**: Чудово! А у тебе?` / `**Марко**: Нормально. Радий тебе бачити!`. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, or incorrect Ukrainian forms found. Checked forms such as `нормально`, `радий`, `рада`, `бачити`, `звуковий`, and `аналіз` are attested. |
| 3. Pedagogical quality | 8/10 | The phonetics sections are concrete and example-rich (`мА-мА`, `мО-лО-кО`, `П [п] + р [р] + и [и]...`), but the greeting lesson spends its main dialogue on `Як справи?` rather than the contracted first-contact introduction pattern for new classmates. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is present in prose: `звук`, `літера`, `голосний`, `приголосний`, `Привіт`, `Як справи`, `Добре`, `Чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 7/10 | Marker count is correct and marker types match, but the order is wrong: `group-sort-sounds` and `letter-grid-alphabet` appear before `fill-in-greetings`, violating the contracted sequence. |
| 6. Engagement & tone | 8/10 | The tone is teacherly and concrete, with usable textbook examples, but the conversation section is less interactive than the contract promises. |
| 7. Structural integrity | 10/10 | All H2 headings are present and correctly ordered, and the pipeline word count is 1214, which clears the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module stays Ukrainian-centered and uses appropriate classroom and peer-greeting contexts. |
| 9. Dialogue & conversation quality | 7/10 | Dialogues use named speakers, but the second scene does not match its planned function of two new classmates introducing themselves; the name-exchange pattern never appears. |

## Findings
[1. Plan adherence] [SEVERITY: major]  
Location: `## Привіт! (Hello!)` — `**Марко**: Привіт! Як справи?` / `**Софія**: Чудово! А у тебе?` / `**Марко**: Нормально. Радий тебе бачити!`  
Issue: The contract’s second dialogue act is missing. The scene is supposed to introduce `Як тебе звати? / Мене звати...`, but that pattern does not appear in the section.  
Fix: Rewrite the hallway exchange so the classmates introduce themselves with `Як тебе звати?` and `Мене звати...`, while keeping `Привіт!` and the gendered `рада/радий` contrast.

[5. Exercise quality] [SEVERITY: major]  
Location: marker sequence after `## Приголосні звуки (Consonant Sounds)` and `## Привіт! (Hello!)` — `<!-- INJECT_ACTIVITY: match-up-letters-sounds -->`, `<!-- INJECT_ACTIVITY: group-sort-sounds -->`, `<!-- INJECT_ACTIVITY: letter-grid-alphabet -->`, later `<!-- INJECT_ACTIVITY: fill-in-greetings -->`  
Issue: The marker order violates the contracted activity order. `fill-in-greetings` must come before `group-sort-sounds` and `letter-grid-alphabet`.  
Fix: Move `group-sort-sounds` and `letter-grid-alphabet` to the greeting block so the final order is `quiz → match-up → fill-in → group-sort → letter-grid → watch-and-repeat`.

## Verdict: REVISE
REVISE. The module is linguistically clean and structurally solid, but it misses a contracted first-contact dialogue beat and fails the contracted activity-marker order.

<fixes>
- find: "Now, let's see how two classmates, Marko and Sofia, talk to each other informally in the hallway.\n\n**Марко**: Привіт! Як справи?\n**Софія**: Чудово! А у тебе? (Great! And you?)\n**Марко**: Нормально. Радий тебе бачити! (Normal. Glad to see you!)\n**Софія**: І я рада тебе бачити! (And I am glad to see you!)\n\nThe greeting **«Привіт!»** (Hi!) is perfect for friends and classmates. Notice how Sofia returns the initial question using **«А у тебе?»** (And you?)."
  replace: "Now, let's see how two new classmates meet in the hallway before class.\n\n**Марко**: Привіт! Як тебе звати? (Hi! What is your name?)\n**Софія**: Привіт! Мене звати Софія. А тебе? (Hi! My name is Sofia. And you?)\n**Марко**: Мене звати Марко. Радий тебе бачити! (My name is Marko. Glad to see you!)\n**Софія**: І я рада тебе бачити! (And I am glad to see you!)\n\nThe greeting **«Привіт!»** (Hi!) is perfect for friends and classmates. This dialogue also gives you your first introduction pattern: **«Як тебе звати?»** (What is your name?) and **«Мене звати...»** (My name is...)."
- find: "<!-- INJECT_ACTIVITY: match-up-letters-sounds -->\n<!-- INJECT_ACTIVITY: group-sort-sounds -->\n<!-- INJECT_ACTIVITY: letter-grid-alphabet -->"
  replace: "<!-- INJECT_ACTIVITY: match-up-letters-sounds -->"
- find: "<!-- INJECT_ACTIVITY: fill-in-greetings -->\n<!-- INJECT_ACTIVITY: watch-and-repeat-videos -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-greetings -->\n<!-- INJECT_ACTIVITY: group-sort-sounds -->\n<!-- INJECT_ACTIVITY: letter-grid-alphabet -->\n<!-- INJECT_ACTIVITY: watch-and-repeat-videos -->"
</fixes>