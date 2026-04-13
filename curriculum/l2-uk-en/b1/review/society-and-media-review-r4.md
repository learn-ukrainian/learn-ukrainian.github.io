## Linguistic Scan
Linguistic errors found:
- **Russianisms / Calques**: "Зустріти" applied to abstract concepts ("зустріти запитання", "зустрічаємо абревіатури") is a stylistic calque from Russian "встретить"; the natural Ukrainian phrasing is "натрапити на" or "траплятися". "А що щодо" is an unnatural, cacophonous calque of "what about".
- **Phraseology/Style**: "Прийняли закон" is used instead of the normative "ухвалили закон". 
- **Orthography**: "прес-конференція" is spelled with a hyphen instead of together (пресконференція) as mandated by Правопис 2019.
- **Syntax/Punctuation**: "Також як стало відомо щойно," has a missing comma after the introductory word and an awkward word order.

## Exercise Check
- Exercises are injected perfectly according to the plan's `activity_hints`.
- **Issue:** The markers are clustered entirely in the first two sections (3 markers after "Що таке медіа?" and 3 after "Читання новин"). This violates the general rule to spread them evenly, but this occurred because the plan specifically scoped its 6 hints ONLY to these two sections (e.g., `focus: "...з розділу «Що таке медіа?»"`). No penalty is applied since the writer followed the plan faithfully.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module accurately covers almost all plan points, but it entirely misses the specific social media examples ("Фейсбук, Iнстаграм, Ютуб, ТікТок") from the Section 1 outline. |
| 2. Linguistic accuracy | 7/10 | Contains critical stylistic calques ("зустріти глибокі запитання", "зустрічаємо абревіатури", "що щодо"), non-normative legal vocabulary ("прийняли закон" замість "ухвалили"), and an orthography error ("прес-конференція"). |
| 3. Pedagogical quality | 10/10 | Explanations of participles and gerunds are seamlessly integrated into the media context. Excellent use of clear examples and PPP flow. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words are introduced contextually, with correct definitions. |
| 5. Exercise quality | 9/10 | The markers match the plan's hints perfectly, though they are clustered in the first two sections (due to explicit plan instructions). |
| 6. Engagement & tone | 10/10 | Professional, engaging tone suitable for B1 learners discussing media and civil society. No gamified language. |
| 7. Structural integrity | 10/10 | Clean structure, perfectly matching headings, and the word count (4747) exceeds the 4000 target. |
| 8. Cultural accuracy | 10/10 | Highly accurate cultural representation of the Ukrainian media landscape (Суспільне, StopFake) and strong decolonial framing. |
| 9. Dialogue & conversation quality | 9/10 | Good use of journalism vocabulary in context, though the phrasing "А що щодо масштабної евакуації" is unnatural and stilted. |

## Findings
[1. Plan adherence] [major]
Location: Section "Що таке медіа?", paragraph 6: "Сьогодні більшість людей щоденно отримує новини саме з соціальних мереж. Для типового українського користувача існує своя спеціальна і дуже поширена термінологія."
Issue: Missing social media examples requested by the plan (Фейсбук, Iнстаграм, Ютуб, ТікТок).
Fix: Add them to the introductory sentence about social media.

[2. Linguistic accuracy] [critical]
Location: Section "Що таке медіа?", paragraph 4: "— Головний редактор: Це чудово. А що щодо масштабної евакуації в тому небезпечному регіоні?"
Issue: "А що щодо" is an unnatural phrasing (calque). "А як щодо" is the correct Ukrainian idiom.
Fix: Change to "А як щодо масштабної евакуації".

[2. Linguistic accuracy] [critical]
Location: Section "Що таке медіа?", paragraph 4: "Також як стало відомо щойно, наш уряд терміново виділив"
Issue: Missing comma after "Також" and awkward word order in the introductory phrase.
Fix: Change to "Також, як щойно стало відомо, наш уряд терміново виділив".

[2. Linguistic accuracy] [critical]
Location: Section "Що таке медіа?", paragraph 3: "У статтях можна часто зустріти глибокі запитання:"
Issue: "Зустріти" applied to abstract things (questions) is a stylistic calque from Russian "встретить".
Fix: Change to "У статтях часто можна натрапити на глибокі запитання:".

[2. Linguistic accuracy] [critical]
Location: Section "Медіатекст: аналіз і створення", paragraph 2: "Коли ми читаємо та аналізуємо публіцистику, ми постійно зустрічаємо абревіатури."
Issue: "Зустрічати" for words/abbreviations is a stylistic calque. "Трапляються" is correct.
Fix: Change to "Коли ми читаємо та аналізуємо публіцистику, нам постійно трапляються абревіатури."

[2. Linguistic accuracy] [major]
Location: Section "Читання новин", paragraph 5: "«Депутати парламенту вчора прийняли новий закон», журналісти стисло напишуть: «Новий закон прийнято»"
Issue: "Прийняти закон" is technically acceptable but "ухвалити закон" is the standard normative Ukrainian term.
Fix: Change to "ухвалили новий закон" / "ухвалено".

[2. Linguistic accuracy] [major]
Location: Section "Читання новин", paragraph 6: "велика і дуже важлива прес-конференція"
Issue: According to Правопис 2019, words starting with "прес-" are written together (пресконференція).
Fix: Change to "пресконференція".

## Verdict: REVISE
The module contains several critical stylistic calques ("зустріти", "зустрічаємо", "що щодо") and minor spelling/vocabulary issues ("прес-конференція", "прийняли закон") that teach incorrect natural Ukrainian phrasing. It requires targeted automated fixes before publication.

<fixes>
- find: "Сьогодні більшість людей щоденно отримує новини саме з соціальних мереж. Для типового українського користувача існує своя спеціальна і дуже поширена термінологія."
  replace: "Сьогодні більшість людей щоденно отримує новини саме з соціальних мереж. В Україні користувачі активно використовують такі платформи, як Фейсбук, Інстаграм, Ютуб та ТікТок. Для типового українського користувача існує своя спеціальна і дуже поширена термінологія."
- find: "Це чудово. А що щодо масштабної евакуації в тому небезпечному регіоні?"
  replace: "Це чудово. А як щодо масштабної евакуації в тому небезпечному регіоні?"
- find: "Також як стало відомо щойно, наш уряд терміново виділив"
  replace: "Також, як щойно стало відомо, наш уряд терміново виділив"
- find: "У статтях можна часто зустріти глибокі запитання:"
  replace: "У статтях часто можна натрапити на глибокі запитання:"
- find: "Коли ми читаємо та аналізуємо публіцистику, ми постійно зустрічаємо абревіатури."
  replace: "Коли ми читаємо та аналізуємо публіцистику, нам постійно трапляються абревіатури."
- find: "«Депутати парламенту вчора прийняли новий закон», журналісти стисло напишуть: «Новий закон **прийнято**»"
  replace: "«Депутати парламенту вчора ухвалили новий закон», журналісти стисло напишуть: «Новий закон **ухвалено**»"
- find: "в центрі Києва відбулася велика і дуже важлива **прес-конференція**"
  replace: "в центрі Києва відбулася велика і дуже важлива **пресконференція**"
</fixes>