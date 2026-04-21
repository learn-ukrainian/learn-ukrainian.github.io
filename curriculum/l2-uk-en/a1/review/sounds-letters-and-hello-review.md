## Linguistic Scan
Errors found: Typos (англіиськоі, голоснии, англіиськіи), Russianism (Справа в тому), Calques (Давайте + дієслово), non-existent word (міло). 

## Exercise Check
Issues found:
- Activity markers in the text (e.g., `<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->`) have suffixes that do not strictly match the contract's type names.
- `<!-- INJECT_ACTIVITY: fill-in-greetings -->` is injected twice (once in `Голосні звуки` and once in `Привіт!`). 
- English scaffolding inside parentheses violates the "кириличність прози" rule.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covers all required beats and sections, but activity markers are slightly off. |
| 2. Linguistic accuracy | 7/10 | Typos in adjectives (англіиськоі, голоснии), "Справа в тому" (Russianism), non-existent word "міло". |
| 3. Pedagogical quality | 8/10 | English scaffolding incorrectly placed in the text; minimal pair "мило / міло" is flawed. |
| 4. Vocabulary coverage | 9/10 | Integrates words well but includes English translations. |
| 5. Exercise quality | 8/10 | Markers need renaming to exactly match contract types; duplicate fill-in marker. |
| 6. Engagement & tone | 9/10 | Very natural teacher tone, encouraging and clear. |
| 7. Structural integrity | 10/10 | Proper use of headings and structure. |
| 8. Cultural accuracy | 10/10 | Culturally rooted explanations, references to real textbooks. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are natural and correctly use the target vocabulary. |

## Findings
[Linguistic accuracy] [major]
Location: `На відміну від англіиськоі мови`, `Кожен голоснии звук`, `в англіиськіи мові`
Issue: OCR/Generation typos confusing 'й/и' and 'ї/і'.
Fix: Replace with correct forms: `англійської`, `голосний`, `англійській`.

[Linguistic accuracy] [minor]
Location: `Справа в тому, що деякі літери...`
Issue: "Справа в тому" is a Russianism (дело в том).
Fix: Replace with "Річ у тім".

[Linguistic accuracy] [minor]
Location: `Давайте спробуємо зробити`, `Давайте подивимося`, `Давайте зробимо`
Issue: Use of "Давайте" + verb is a calque. The Ukrainian imperative form should be used.
Fix: Change to `Спробуймо зробити`, `Погляньмо`, `Зробімо`.

[Pedagogical quality] [major]
Location: `Порівняйте: «мило» ( soap ) та «міло» ( swept ).`
Issue: Contains English translations in prose (violates rule) and uses "міло", which is not a valid Ukrainian word (swept is "мело").
Fix: Replace with a valid minimal pair without English translations, e.g., `Порівняйте: «лис» та «ліс».`

[Pedagogical quality] [major]
Location: `«стан» ( condition ) та «стань» ( stand up! )`, `«Добре» ( fine ), «Чудово» ( great ) або «Нормально» ( okay ).`, `схожий на англійське «garden»`, `(як «k» у слові «know»)`
Issue: English scaffolding inside Ukrainian prose.
Fix: Remove the English words and parentheses entirely.

[Exercise quality] [minor]
Location: Activity markers
Issue: Markers do not match the exact names from `activity_obligations` and one is duplicated.
Fix: Rename to exact types (`quiz`, `watch-and-repeat`, `fill-in`) and remove the duplicate `fill-in` from the "Голосні звуки" section.

## Verdict: REVISE
The text has excellent tone and structure but suffers from several noticeable typos, a few Russianisms/calques, and the incorrect inclusion of English scaffolding in the Ukrainian-canonical text.

<fixes>
- find: "На відміну від англіиськоі мови, де одна й та сама літера може читатися по-різному в різних словах, або існують «німі» літери (як «k» у слові «know»), український правопис переважно фонетичний."
  replace: "На відміну від англійської мови, де одна й та сама літера може читатися по-різному в різних словах, або існують «німі» літери, український правопис переважно фонетичний."
- find: "Кожен голоснии звук утворюється виключно за допомогою голосу."
  replace: "Кожен голосний звук утворюється виключно за допомогою голосу."
- find: "Порівняйте: «мило» ( soap ) та «міло» ( swept )."
  replace: "Порівняйте: «лис» та «ліс»."
- find: "Подивіться на пару слів: «стан» ( condition ) та «стань» ( stand up! )."
  replace: "Подивіться на пару слів: «стан» та «стань»."
- find: "«Добре» ( fine ), «Чудово» ( great ) або «Нормально» ( okay )."
  replace: "«Добре», «Чудово» або «Нормально»."
- find: "На відміну від того, як сприймається приголосний в англіиськіи мові"
  replace: "На відміну від того, як сприймається приголосний в англійській мові"
- find: "Літера Ґ позначає твердий звук [g], схожий на англійське «garden» (наприклад, у слові «ґанок»)."
  replace: "Літера Ґ позначає твердий звук [g] (наприклад, у слові «ґанок»)."
- find: "<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->"
  replace: "<!-- INJECT_ACTIVITY: quiz -->"
- find: "<!-- INJECT_ACTIVITY: fill-in-greetings -->\n\n<!-- INJECT_ACTIVITY: group-sort -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort -->"
- find: "<!-- INJECT_ACTIVITY: watch-and-repeat-vowels -->"
  replace: "<!-- INJECT_ACTIVITY: watch-and-repeat -->"
- find: "<!-- INJECT_ACTIVITY: fill-in-greetings -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in -->"
- find: "Справа в тому, що деякі літери можуть позначати одразу два звуки."
  replace: "Річ у тім, що деякі літери можуть позначати одразу два звуки."
- find: "Давайте спробуємо зробити звуковий аналіз простих слів."
  replace: "Спробуймо зробити звуковий аналіз простих слів."
- find: "Давайте подивимося, як це виглядає на практиці в класі під час першого уроку."
  replace: "Погляньмо, як це виглядає на практиці в класі під час першого уроку."
- find: "Давайте зробимо наш перший звуковий аналіз слова «Привіт»."
  replace: "Зробімо наш перший звуковий аналіз слова «Привіт»."
- find: "настала Ваша перша розмова українською."
  replace: "час для вашої першої розмови українською."
- find: "Звук [и] вимовляється більш глибоко в роті"
  replace: "Звук [и] вимовляється глибше в роті"
</fixes>