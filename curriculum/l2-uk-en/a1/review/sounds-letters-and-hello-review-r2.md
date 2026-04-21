## Linguistic Scan
- Russianisms: none found.
- Surzhyk: none found.
- Calques: no high-confidence lexical calques, but Latin-script metacommentary appears inside Ukrainian prose: `ULP`, `M02`, `M08`.
- Paronyms: no clear paronym substitutions found.
- Other: `Різниця полягає в оста́нньому зву́ці.` is pedagogically imprecise for `рада/радий`; this is a change of form/ending, not just one sound.

## Exercise Check
- `fill-in` is placed after the greetings dialogue, which is correct.
- The marker set does not cleanly mirror the six obligated activity types: `alphabet-grid`, `match-letters-to-sounds`, `sort-vowels-consonants`, and `watch-and-repeat-consonants` do not correspond directly to the contract’s `letter-grid`, `match-up`, `group-sort`, and single `watch-and-repeat`.
- `watch-and-repeat` is split into two marker slots, so the obligation set is not represented cleanly as contracted.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 4/10 | All required sections exist, but the module is 1977 words vs target 1200, and local section counts are far above max budgets: ~658/581/518/504/191 vs 330/275/275/275/165. The named dialogue also misses the contracted mutual `А у тебе?` in the name exchange. |
| 2. Linguistic accuracy | 7/10 | No Russianisms or Surzhyk found, but Latin `ULP`, `M02`, `M08` break the all-Ukrainian prose register; `Різниця полягає в останньому звуці` is imprecise. |
| 3. Pedagogical quality | 6/10 | Core explanations are correct, but the lesson overexplains beyond A1 and buries key beats under long expository expansions. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is introduced naturally: `звук`, `літера`, `голосний`, `приголосний`, `привіт`, `як справи`, `добре`, `чудово`, `мама`, `молоко`. |
| 5. Exercise quality | 5/10 | Exercise placement is partly sensible, but the marker inventory does not map cleanly to the contracted activity types and duplicates `watch-and-repeat`. |
| 6. Engagement & tone | 6/10 | The tone is teacherly and clear, but the prose is overextended and stress-mark saturation makes it feel less canonical and less natural to read. |
| 7. Structural integrity | 5/10 | Headings are present and ordered correctly, but section budgets are badly exceeded and the activity marker scheme is not contract-clean. |
| 8. Cultural accuracy | 8/10 | The module treats Ukrainian on its own terms and avoids colonial framing; the main issue is formatting/register drift, not cultural stance. |
| 9. Dialogue & conversation quality | 7/10 | Dialogues are mostly natural and the formal `Ви` exchange works, but the required reciprocal `А у тебе?` is not used in the name-exchange slot. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `В украї́нській мо́ві 33 літери, але́ 38 зву́ків... Це дуже важли́во запам'ята́ти.` and similarly expanded paragraphs across all core sections  
Issue: The module massively exceeds the word budget; the prose keeps restating already-covered beats instead of staying at A1 teaching density.  
Fix: Compress each explanatory paragraph back to the contract beat, keeping one clear explanation plus 1-2 examples.

[LINGUISTIC ACCURACY] [SEVERITY: major]  
Location: `Усі дета́лі — в M02.` / `На осно́ві епізо́ду 1 ULP Анни Огойко.` / `почина́ючи з M08.`  
Issue: Latin-script meta labels inside Ukrainian prose violate the canonical Ukrainian-only register required by this review mode.  
Fix: Replace them with plain Ukrainian references such as `у наступному модулі`, `у першому епізоді`, `у наступних модулях`.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `> **Марко:** Ме́не звати Марко. А тебе?`  
Issue: The contract explicitly requires reciprocal `А у тебе?` in the named dialogue; the current line does not satisfy that requirement.  
Fix: Change the replica to `Мене звати Марко. А у тебе?`

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: alphabet-grid -->`, `<!-- INJECT_ACTIVITY: match-letters-to-sounds -->`, `<!-- INJECT_ACTIVITY: sort-vowels-consonants -->`, `<!-- INJECT_ACTIVITY: watch-and-repeat-consonants -->`  
Issue: The marker inventory does not cleanly match the contracted activity types and splits one obligated `watch-and-repeat` into two separate markers.  
Fix: Normalize markers to the contracted types: `letter-grid`, `match-up`, `group-sort`, and one `watch-and-repeat`.

[PEDAGOGICAL QUALITY] [SEVERITY: minor]  
Location: `Різниця поляга́є в оста́нньому зву́ці.`  
Issue: This explains `рада/радий` too loosely; the contrast is a grammatical form/ending difference, not just one sound.  
Fix: Replace with `Різниця полягає в закінченні та формі слова.`

## Verdict: REVISE
The module is usable in principle and broadly Ukrainian-centered, but it is not contract-clean. The main blockers are the severe word-count overrun, Latin-script meta insertions inside prose, non-clean activity marker mapping, and one explicit dialogue-contract miss.

<fixes>
- find: "Усі дета́лі — в M02."
  replace: "Докладніше про йотовані літери буде в наступному модулі."

- find: "На осно́ві епізо́ду 1 ULP Анни Огойко."
  replace: "На основі першого епізоду Анни Огойко."

- find: "Це ста́не вели́кою те́мою, почина́ючи з M08."
  replace: "До теми роду ми ще повернемося в наступних модулях."

- find: "> **Марко:** Ме́не звати Марко. А тебе?"
  replace: "> **Марко:** Ме́не звати Марко. А у тебе?"

- find: "Різниця поляга́є в оста́нньому зву́ці."
  replace: "Різниця полягає в закінченні та формі слова."

- find: "<!-- INJECT_ACTIVITY: alphabet-grid -->"
  replace: "<!-- INJECT_ACTIVITY: letter-grid -->"

- find: "<!-- INJECT_ACTIVITY: match-letters-to-sounds -->"
  replace: "<!-- INJECT_ACTIVITY: match-up -->"

- find: "<!-- INJECT_ACTIVITY: sort-vowels-consonants -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort -->"

- find: "<!-- INJECT_ACTIVITY: watch-and-repeat-consonants -->"
  replace: ""

- find: "Це пита́ння матема́тики мо́ви. Якби́ ко́жна літера за́вжди́ познача́ла лише оди́н звук, ми ма́ли б рі́вно 33 літери і 33 звуки. Але систе́ма тро́хи гнучкі́ша. Літери «Я», «Ю», «Є», «Ї» — це особли́ві си́мволи. Вони́ мо́жуть хова́ти в собі́ одра́зу два звуки."
  replace: "Тому звуків більше, ніж літер: я, ю, є, ї можуть передавати два звуки, а ь окремого звука не має."

- find: "Запам'ята́йте ці шість чи́стих звуків. Щоб вимовити [а], ви ши́роко відкриваєте рот. Для [о] та [у] ви окру́глюєте губи. Для [е] рот відкри́тий трохи ме́нше."
  replace: "Запам'ятайте ці шість звуків і поступово вчіться впізнавати їх на слух та у вимові."

- find: "Щоб вимовити звук [п], ваші губи мі́цно стиска́ються, а по́тім рі́зко розмикаються, випуска́ючи повітря. Щоб вимовити [с], ваш язик наближа́ється до зубі́в і ство́рює вузьку́ щі́ли́ну, через яку проходить повітря із характерним сви́стом. Саме тому ці звуки так і називаються — вони здебільшого «при го́лосі», вони супрово́джують голосні, але самі по собі не можуть утвори́ти повноці́нний склад. Ви можете спро́бувати потягну́ти звук [с], але це бу́де лише шум, а не спів. Приголосні звуки — це кістки́ слова, його тверди́й карка́с."
  replace: "Наприклад, у [п] губи змикаються і розмикаються, а у [с] язик створює щілину для повітря. Приголосний не можна проспівати так, як голосний."

- find: "Після того́, як ми розібра́лися зі звуками, час скла́сти їх у спра́вжнє спілкува́ння. Найпрості́ший спо́сіб розпоча́ти розмо́ву з дру́зями, ро́дичами або коле́гами ва́шого ві́ку — сказа́ти «Привіт!». Це неформа́льне віта́ння. Для офіці́йних ситуа́цій використовують фра́зи на кшталт «До́брий день!». Відра́зу після вітання прийня́то запи́тувати «Як справи?». Це станда́ртне питання, на яке зазвича́й відповіда́ють позити́вно або нейтра́льно. Ви можете сказати «Добре», якщо все йде за пла́ном. Якщо у вас прекра́сний на́стрій, скажі́ть «Чудово». Якщо ні́чого особли́вого не відбу́вається, піді́йде слово «Нормально». А щоб підтри́мати розмову, завжди додава́йте вві́чливе запита́ння: «А у тебе?»."
  replace: "Тепер складімо вивчені звуки в коротке спілкування. Для друзів, родини й однолітків кажемо «Привіт!». На «Як справи?» можна відповісти: «Добре», «Чудово», «Нормально». Після цього природно запитати: «А у тебе?». "
</fixes>