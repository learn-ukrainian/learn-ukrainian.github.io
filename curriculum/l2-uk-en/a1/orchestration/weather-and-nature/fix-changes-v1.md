## Applied Fixes

1. [File: activities] Removed untaught words (`мороз`, `зелено`, `сад`, `ведмідь`, `кущ`) and replaced with taught vocabulary (`сніг`, `тепло`, `ліс`, `кіт`, `парк`) — Issue 1.
2. [File: activities] Fixed "What Season?" quiz scenarios to avoid complex phrases ("Люди на пляжі", "Листя падає", "Птахи повертаються") and use taught concepts — Issue 1.
3. [File: activities] Fixed Instrumental case error in `fill-in` (Nature and Animals), changed "У мене є акваріум з [рибою]" to "У воді плаває [риба]" — Issue 3.
4. [File: activities] Fixed odd phrasing in `fill-in` (Weather), changed "Падає біла вода..." to "Взимку холодно і [йде сніг]" / "Восени часто [йде дощ]" — Issue 4.
5. [File: vocabulary] Completely rewrote vocabulary list to include core module words (`тепло`, `холодно`, `дощ`, `сніг`, `весна`, etc.) instead of random nouns — Issue 2.

## Fixes NOT Applied

- No fixes required for `content` (29-weather-and-nature.md) as it already contained the core vocabulary and sufficient examples. The instruction "Add these words to the 'Weather Vocabulary' or 'Examples'" was conditional on whether I replaced words in activities, but I replaced activities with words *already* in the content (tables/examples), so the sync is achieved without content modification.

## Files Changed: activities, vocabulary
## Files Unchanged: content