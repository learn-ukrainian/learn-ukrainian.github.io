## Linguistic Scan
No linguistic errors found.

## Exercise Check
Marker-only module. I found 6 markers, and they match the contract exactly in count, order, and type: `quiz → match-up → fill-in → group-sort → letter-grid → watch-and-repeat`. No type mismatches and no missing markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Section budgets are on target (`304 / 253 / 256 / 238 / 157` words against the contract bands), and the textbook beats are largely covered, but the required hallway dialogue does not complete the contract’s “exchange names” requirement: `> **Марко:** Привіт! Як справи? ... > **Софія:** Добре, дякую. А у тебе? ...` never uses `Як тебе звати? / Мене звати...`. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, or wrong Ukrainian forms found. Spot checks via local tools supported forms such as `радий`, `рада`, `привіт`, `чудово`, `нормально`, `милуєшся`. |
| 3. Pedagogical quality | 9/10 | The module teaches in a clear progression: rule (`«Звуки ми чуємо й вимовляємо...»`), classification, examples (`мама`, `молоко`), then application in `звуковий аналіз` of `привіт`. The explanations are concrete and example-rich. |
| 4. Vocabulary coverage | 10/10 | All required target items appear in prose: `звук`, `літера`, `голосний`, `приголосний`, `привіт`, `як справи`, `добре`, `чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 10/10 | Marker-only module, so this score is based on contract compliance only: all 6 required markers are present, in the exact obligated order, with exact contracted types. |
| 6. Engagement & tone | 9/10 | The tone is mostly solid teacher talk with concrete classroom framing, especially in lines like `Let us practice hearing these vowels in simple words` and the guided `звуковий аналіз` walkthrough. |
| 7. Structural integrity | 10/10 | All five H2 sections are present and correctly ordered, markdown is clean, and the pipeline word count is `1202`, which clears the minimum target. |
| 8. Cultural accuracy | 9/10 | The module is decolonized and Ukrainian-centered throughout: Ukrainian textbooks, Ukrainian pedagogical terminology, and Ukrainian greeting norms are foregrounded rather than filtered through Russian comparison. |
| 9. Dialogue & conversation quality | 7/10 | The hallway dialogue has named speakers, but it misses the required name exchange, and the classroom exchange models `> **Учні:** Привіт! Добре.` immediately after stating that `Добрий день` is the formal greeting, which creates a register mismatch in a teacher-student setting. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> **Марко:** Привіт! Як справи? *(Hi! How are you?)*` / `> **Софія:** Добре, дякую. А у тебе? *(Good, thanks. And you?)*`  
Issue: The contract requires the hallway dialogue to use named speaker labels, exchange names, and include reciprocal `А у тебе?`. The speaker labels and reciprocal question are present, but the name exchange is missing.  
Fix: Rewrite the hallway dialogue so the classmates say `Як тебе звати?` and `Мене звати...` before moving into `Як справи?`.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> **Вчитель:** Добрий день! Як справи? *(Good day! How are you?)*` / `> **Учні:** Привіт! Добре. *(Hi! Good.)*`  
Issue: This models an informal reply (`Привіт`) to a teacher right after the prose explicitly defines `Добрий день` as the formal greeting and `привіт` as the informal one. That is a register mistake in the first classroom example.  
Fix: Change the students’ reply to a formal response such as `Добрий день! Добре.` and keep `Привіт` for the peer dialogue.

## Verdict: REVISE
REVISE. The module is structurally sound and linguistically clean, but it misses a contract-required dialogue element and teaches the wrong register in the first classroom exchange. That is enough to fail the severity gate, and dimensions 1 and 9 are below 9.

<fixes>
- find: |-
    > **Вчитель:** Добрий день! Як справи? *(Good day! How are you?)*
    > **Учні:** Привіт! Добре. *(Hi! Good.)*
  replace: |-
    > **Вчитель:** Добрий день! Як справи? *(Good day! How are you?)*
    > **Учні:** Добрий день! Добре. *(Good day! Fine.)*
- find: |-
    > **Марко:** Привіт! Як справи? *(Hi! How are you?)*
    > **Софія:** Добре, дякую. А у тебе? *(Good, thanks. And you?)*
    > **Марко:** Нормально. Радий тебе бачити! *(Okay. Glad to see you!)*
    > **Софія:** Рада тебе бачити! *(Glad to see you!)*
  replace: |-
    > **Марко:** Привіт! Як тебе звати? *(Hi! What is your name?)*
    > **Софія:** Мене звати Софія. А як тебе звати? *(My name is Sofia. And what is your name?)*
    > **Марко:** Мене звати Марко. Як справи? *(My name is Marko. How are you?)*
    > **Софія:** Чудово. А у тебе? *(Great. And you?)*
    > **Марко:** Нормально. Радий тебе бачити! *(Okay. Glad to see you!)*
    > **Софія:** Рада тебе бачити! *(Glad to see you!)*
</fixes>