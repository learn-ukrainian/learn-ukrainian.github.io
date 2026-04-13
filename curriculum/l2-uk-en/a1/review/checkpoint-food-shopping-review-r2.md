## Linguistic Scan
No linguistic errors found.

## Exercise Check
Found 3 `INJECT_ACTIVITY` markers: `quiz-accusative-forms`, `fill-in-dialogue`, `quiz-situational-phrases`.

Marker placement is mostly sensible:
- `quiz-accusative-forms` comes after the grammar section.
- `fill-in-dialogue` and `quiz-situational-phrases` come after the dialogue section.

The problem is the planned fourth activity:
- The module includes an inline `### Швидке сортування (Quick Sort)` block, but it is not a real exercise because the answers are already pre-grouped as `Inanimate` and `Animate`.
- So the plan’s `group-sort` activity is not actually assessable in its current form.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The reading plan says Anna “meets a friend and introduces her brother,” but the text only gives `— Олено, привіт! Ти знаєш мого брата?` The hosting flow also stops at `Я ставлю тарілки і склянки на стіл для гостей.` without the planned serving moment. |
| 2. Linguistic accuracy | 10/10 | Accusative forms such as `каву`, `водy`, `Олену`, `брата` and the numeral phrase `тридцять гривень` are correct; no Russian-only letters appear. |
| 3. Pedagogical quality | 8/10 | The grammar section gives clear examples (`Я п'ю воду.`, `Я бачу брата.`), but the `Швидке сортування` task gives the sorted answers immediately instead of making the learner perform the categorization. |
| 4. Vocabulary coverage | 9/10 | Key plan vocabulary is integrated naturally: `продукти`, `вареники`, `салат`, `тарілки`, `склянки`, `кава з молоком`, `ринок`. |
| 5. Exercise quality | 6/10 | There are only 3 inject markers, and the inline `Швидке сортування` block is pre-solved (`Inanimate ... / Animate ...`), so one of the four planned activities is not functioning as an exercise. |
| 6. Engagement & tone | 9/10 | The voice is teacherly and not gamified: `Look at the self-check questionnaire below.` / `Treat them as reliable tools...` |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and ordered, and the pipeline word count is 1196, which is above the 1000-word target. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian food/shopping situations directly, without Russian-centric framing or cultural distortion. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers help, but the cafe scene is compressed into one narrated turn: `Після ринку я заходжу в кафе: Мені борщ і воду, будь ласка. Рахунок, будь ласка. Можна карткою?` That reads like summary, not live conversation. |

## Findings
[Plan adherence] [SEVERITY: major]  
Location: Reading section — `> **— Олено, привіт! Ти знаєш мого брата?**`  
Issue: The plan requires Anna to meet a friend and introduce her brother. This line only asks about the brother; it does not perform an introduction.  
Fix: Make the brother present in the scene and change the line to an actual introduction such as `Це мій брат.`

[Plan adherence] [SEVERITY: major]  
Location: Connected Dialogue — `> **Марія:** Так. Я ставлю тарілки і склянки на стіл для гостей.`  
Issue: The plan’s hosting flow includes serving guests, but the dialogue stops at table-setting and never reaches the serving moment.  
Fix: Extend this line with a serving move, e.g. `Ось вареники і салат, прошу.`

[Exercise quality] [SEVERITY: major]  
Location: `### Швидке сортування (Quick Sort)` — `*   **Inanimate (що?):** ...` / `*   **Animate (кого?):** ...`  
Issue: This is not an exercise; it is the answer key. The learner is not asked to sort anything because the forms are already sorted.  
Fix: Replace the pre-sorted bullets with one unsorted item bank.

[Dialogue & conversation quality] [SEVERITY: major]  
Location: Connected Dialogue — `> **Марія:** Після ринку я заходжу в кафе: Мені борщ і воду, будь ласка. Рахунок, будь ласка. Можна карткою?`  
Issue: The entire cafe interaction is compressed into one narrated turn, so the “dialogue” loses turn-taking and sounds staged rather than spoken.  
Fix: Split this into a short multi-turn exchange with an `Офіціант` line and a separate ordering line.

## Verdict: REVISE
REVISE — there are no linguistic blockers, but there are major plan/exercise/dialogue problems: the reading misses the planned brother introduction, the hosting flow stops before serving guests, the group-sort is currently an answer key rather than an activity, and the cafe scene is narrated instead of dialogued.

<fixes>
- find: |
    > **Раптом вона бачить Олену.**
    > *(Suddenly she sees Olena.)*
    > **— Олено, привіт! Ти знаєш мого брата?**
    > *(— Olena, hi! Do you know my brother?)*
  replace: |
    > **Раптом вона бачить Олену і свого брата.**
    > *(Suddenly she sees Olena and her brother.)*
    > **— Олено, привіт! Це мій брат.**
    > *(— Olena, hi! This is my brother.)*
- find: |
    ### Швидке сортування (Quick Sort)

    Sort these forms into two groups.

    *   **Inanimate (що?):** борщ, хліб, сік, чай, сир
    *   **Animate (кого?):** брата, лікаря, сусіда, друга, вчителя
  replace: |
    ### Швидке сортування (Quick Sort)

    Sort these forms into two groups: борщ, хліб, сік, чай, сир, брата, лікаря, сусіда, друга, вчителя.
- find: |
    > **Марія:** Так. Я ставлю тарілки і склянки на стіл для гостей.
    > *(Yes. I am putting plates and glasses on the table for the guests.)*
  replace: |
    > **Марія:** Так. Я ставлю тарілки і склянки на стіл для гостей. Ось вареники і салат, прошу.
    > *(Yes. I am putting plates and glasses on the table for the guests. Here are the varenyky and salad.)*
- find: |
    > **Марія:** Після ринку я заходжу в кафе: Мені борщ і воду, будь ласка. Рахунок, будь ласка. Можна карткою?
    > *(After the market I stop at a cafe: Borscht and water for me, please. The bill, please. Can I pay by card?)*
  replace: |
    > **Марія:** Після ринку я заходжу в кафе.
    > *(After the market I stop at a cafe.)*
    > **Офіціант:** Що будете?
    > *(What would you like?)*
    > **Марія:** Мені борщ і воду, будь ласка.
    > *(Borscht and water for me, please.)*
    > **Офіціант:** Добре.
    > *(All right.)*
    > **Марія:** Рахунок, будь ласка. Можна карткою?
    > *(The bill, please. Can I pay by card?)*
</fixes>