## Linguistic Scan
4 errors found:
- `опредмечену` (Russian calque, should be `опредметнену`)
- `опредмечена` (Russian calque, should be `опредметнена`)
- `з оточуючим світом` (Russianism / active participle, should be `з навколишнім світом`)
- `повсякденнішим` (Invalid comparative form, should be `буденнішим`)

## Exercise Check
All 5 placeholder markers are present and correctly mapped to the activity hints.
- `<!-- INJECT_ACTIVITY: nominalization-intro -->` is placed after the introduction. Matches the `match-up` activity.
- `<!-- INJECT_ACTIVITY: suffix-practice -->` is placed after the -ння suffix section. Matches the `fill-in` activity.
- `<!-- INJECT_ACTIVITY: zero-derivation -->` is placed after the -ття and zero-derivation section. Matches the `group-sort` activity.
- `<!-- INJECT_ACTIVITY: sentence-transformation -->` is placed after the syntax section. Matches the `sentence-builder` activity.
- `<!-- INJECT_ACTIVITY: news-analysis -->` is placed after the reading section. Matches the `quiz` activity.
The distribution is even and logically follows the pedagogical progression.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | DEDUCT for missing textbook references. The plan explicitly requires citing "Вашуленко Grade 3", "Голуб Grade 6", "Литвінова Grade 6", and "Заболотний Grade 7", but none of these authors or textbooks are mentioned anywhere in the prose. All other grammatical points are well covered. |
| 2. Linguistic accuracy | 7/10 | CRITICAL errors found: "опредмечена дія" and "опредмечену дію" (Russian calques, should be "опредметнена/у"). Also, "з оточуючим світом" (Russian active participle, should be "з навколишнім світом"). Also "повсякденнішим" (invalid synthetic comparative form). |
| 3. Pedagogical quality | 9/10 | Excellent pedagogical progression from concept to practice. The use of contrastive examples (process vs result, formal vs neutral) is strong and very helpful for B1 learners. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary from the plan is introduced naturally in the text with clear explanations and bolded keywords. |
| 5. Exercise quality | 10/10 | The placeholder markers are perfectly positioned after each relevant grammatical section, ensuring progressive, immediate practice. |
| 6. Engagement & tone | 8/10 | DEDUCT for generic enthusiasm ("магію перетворення", "лінгвістичну магію"), which violates the rule against "The magic of..." meta-commentary. Otherwise, the tone is professional. |
| 7. Structural integrity | 7/10 | DEDUCT for adding two unauthorized H2 headings (`## Суфікси -іння та -ення...` and `## Стилістика: Канцелярит...`) that are not in the metadata `content_outline`. Also altered two H2 names from the exact plan wording (`Синтаксис:` and `текстах`). This will break the pipeline validation script. |
| 8. Cultural accuracy | 10/10 | Good use of Ukrainian context in the reading examples (Дія, digital state, green energy, rebuilding). |
| 9. Dialogue & conversation quality | 6/10 | DEDUCT for stilted/textbook-robotic phrasing in the opening dialogue. While it intentionally crams verbal nouns for the lesson, sentences like "Моє фотографування на заводі пройшло успішно" sound completely unnatural for native speakers. |

## Findings
[1. Plan adherence] [major]
Location: Entire text
Issue: Textbook references from the plan (Вашуленко, Голуб, Литвінова, Заболотний) were completely ignored.
Fix: Since this requires rewriting multiple paragraphs, no exact fix is provided, but this is a significant plan adherence failure.

[2. Linguistic accuracy] [critical]
Location: "...над яким виконується опредмечена дія."
Issue: "опредмечена" is a Russian calque (опредмеченный). The correct Ukrainian linguistic term is "опредметнена".
Fix: Replace "опредмечена дія." with "опредметнена дія."

[2. Linguistic accuracy] [critical]
Location: "...що позначають опредмечену дію:"
Issue: "опредмечену" is a Russian calque.
Fix: Replace "опредмечену дію:" with "опредметнену дію:"

[2. Linguistic accuracy] [critical]
Location: "...описувати свої почуття та взаємини з оточуючим світом, людьми та предметами."
Issue: "оточуючим" is an active participle calqued from Russian "окружающим". In Ukrainian, the environment is "навколишній світ" or "довкілля".
Fix: Replace "з оточуючим світом," with "з навколишнім світом,"

[2. Linguistic accuracy] [critical]
Location: "...тоді як безафіксний іменник розмова ... є набагато теплішим і повсякденнішим."
Issue: "повсякденний" is a relative adjective and cannot naturally form a synthetic comparative degree ("повсякденніший" does not exist in standard dictionaries). "буденніший" is the correct, natural form here.
Fix: Replace "є набагато теплішим і повсякденнішим." with "є набагато теплішим і буденнішим."

[6. Engagement & tone] [minor]
Location: "...здійснювати лінгвістичну магію: перетворювати динамічні..."
Issue: Generic enthusiasm / meta-commentary ("magic of") violates tone guidelines.
Fix: Replace "здійснювати лінгвістичну магію: перетворювати" with "здійснювати лінгвістичну трансформацію: перетворювати"

[6. Engagement & tone] [minor]
Location: "Подивіться на цю магію перетворення:"
Issue: Generic enthusiasm / meta-commentary.
Fix: Replace "Подивіться на цю магію перетворення:" with "Погляньте на це перетворення:"

[7. Structural integrity] [major]
Location: "## Синтаксис: Віддієслівні іменники у реченні"
Issue: H2 heading does not exactly match the plan outline (added "Синтаксис:").
Fix: Replace "## Синтаксис: Віддієслівні іменники у реченні" with "## Віддієслівні іменники у реченні"

[7. Structural integrity] [major]
Location: "## Читання: віддієслівні іменники у текстах"
Issue: H2 heading does not exactly match the plan outline (changed "новинах" to "текстах").
Fix: Replace "## Читання: віддієслівні іменники у текстах" with "## Читання: віддієслівні іменники у новинах"

[7. Structural integrity] [major]
Location: "## Суфікси -іння та -ення: робота з другою дієвідміною"
Issue: Unauthorized H2 heading added that is not in the plan outline. Must be H3.
Fix: Replace "## Суфікси -іння та -ення: робота з другою дієвідміною" with "### Суфікси -іння та -ення: робота з другою дієвідміною"

[7. Structural integrity] [major]
Location: "## Стилістика: Канцелярит та як його уникати"
Issue: Unauthorized H2 heading added that is not in the plan outline. Must be H3.
Fix: Replace "## Стилістика: Канцелярит та як його уникати" with "### Стилістика: Канцелярит та як його уникати"

[2. Linguistic accuracy] [minor]
Location: "Дієслово **збільшити** *(to increase)* стає **збільшенням** *(increase/growth)*."
Issue: Inconsistent case usage (instrumental here, but nominative in the next sentence "утворює зменшення").
Fix: Replace "стає **збільшенням** *(increase/growth)*." with "стає іменником **збільшення** *(increase/growth)*."

## Verdict: REVISE
The module has strong pedagogical value and clear grammar explanations, but contains several critical linguistic errors (Russian calques like "опредмечена", "оточуючим") and structural violations (unauthorized/altered H2 headings that will break the pipeline validation script). These must be fixed before publishing.

<fixes>
- find: "опредмечена дія."
  replace: "опредметнена дія."
- find: "опредмечену дію:"
  replace: "опредметнену дію:"
- find: "з оточуючим світом,"
  replace: "з навколишнім світом,"
- find: "є набагато теплішим і повсякденнішим."
  replace: "є набагато теплішим і буденнішим."
- find: "здійснювати лінгвістичну магію: перетворювати"
  replace: "здійснювати лінгвістичну трансформацію: перетворювати"
- find: "Подивіться на цю магію перетворення:"
  replace: "Погляньте на це перетворення:"
- find: "## Синтаксис: Віддієслівні іменники у реченні"
  replace: "## Віддієслівні іменники у реченні"
- find: "## Читання: віддієслівні іменники у текстах"
  replace: "## Читання: віддієслівні іменники у новинах"
- find: "## Суфікси -іння та -ення: робота з другою дієвідміною"
  replace: "### Суфікси -іння та -ення: робота з другою дієвідміною"
- find: "## Стилістика: Канцелярит та як його уникати"
  replace: "### Стилістика: Канцелярит та як його уникати"
- find: "стає **збільшенням** *(increase/growth)*."
  replace: "стає іменником **збільшення** *(increase/growth)*."
</fixes>
