## Linguistic Scan
- Orthography: `Це не велика проблема.` should be `Це невелика проблема.`
- Calque / inaccurate rule: the `по` section teaches `«по пошті» (by mail)` and says `the locative case remains strictly the standard.` Repo evidence conflicts with that: `curriculum/l2-uk-en/a2/research/services-and-communication-knowledge-packet.md` classifies `відправити по пошті` as a calque and recommends `поштою`.

## Exercise Check
Found 7 markers:
- `quiz-identify-the-function-of-locative-in-each-sentence`
- `fill-in-complete-sentences-with-the-correct-locative-form` twice
- `fill-in-locative-forms`
- `error-correction-prepositions`
- `quiz-locative-functions`
- `match-up-expressions`

Issues:
- The first quiz marker appears before temporal and `по` uses are taught, so it cannot validly test “all four functions.”
- The fill-in marker appears before the `по` section even though the plan focus includes `по ___`.
- Marker inventory does not match the plan’s 4 activities; quiz/fill-in are duplicated under different IDs.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned H2s are present and the planned vocab is covered, but the activity plan is not followed cleanly: the module has 7 markers for 4 planned activities, including duplicate quiz/fill-in markers. |
| 2. Linguistic accuracy | 5/10 | `Це не велика проблема.` is orthographically wrong; the section teaches `«по пошті» (by mail)` and says `the locative case remains strictly the standard`, which conflicts with repo research preferring `поштою`. |
| 3. Pedagogical quality | 6/10 | The module has PPP structure, but it teaches an over-absolute rule in the `по` section and places practice before the relevant material is fully taught. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary appears naturally: `місцевий`, `абстрактний`, `минулий`, `місяць`, `тиждень`, `телефон`, `подорож`, `зустріч`, `думка`, `проблема`; recommended words like `дитинство`, `молодість`, `майбутнє`, `освіта`, `мистецтво` also appear. |
| 5. Exercise quality | 4/10 | `<!-- INJECT_ACTIVITY: quiz-identify-the-function-of-locative-in-each-sentence -->` and the first fill-in marker appear before all target functions are taught; marker duplication makes the activity set inconsistent with the plan. |
| 6. Engagement & tone | 7/10 | Mostly teacherly, but lines like `This preserves the beautiful logic of the locative case` add filler rather than instruction. |
| 7. Structural integrity | 8/10 | Clean H2 structure and pipeline word count is above target (`2927`), but marker clutter/duplication creates structural noise. |
| 8. Cultural accuracy | 6/10 | Calling `по + locative` for mail `traditional, authentic Ukrainian` is too strong given the repo’s decolonization note preferring `поштою` over `по пошті`. |
| 9. Dialogue & conversation quality | 7/10 | Dialogues are named and multi-turn, but `Добрий день! Як ваші справи на цьому тижні?` sounds stiff and translated. |

## Findings
[DIMENSION 2] [SEVERITY: critical]  
Location: `> — **Ігор:** Не хвилюйся. Це не велика проблема.`  
Issue: Non-contrastive `не велика` should be written together.  
Fix: Change it to `Це невелика проблема.`

[DIMENSION 2] [SEVERITY: critical]  
Location: `Common examples include «по телефону» (by phone), «по радіо» (on the radio), «по пошті» (by mail), and «по дорозі» (on the way).` and `the locative case remains strictly the standard.`  
Issue: The module teaches `по пошті` as standard locative usage and states the rule absolutely. Repo research (`curriculum/l2-uk-en/a2/research/services-and-communication-knowledge-packet.md`) treats `відправити по пошті` as a calque and recommends `поштою`.  
Fix: Replace mail examples with `поштою` and narrow the rule to fixed expressions like `по телефону`, `по радіо`, `по дорозі`.

[DIMENSION 5] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: quiz-identify-the-function-of-locative-in-each-sentence -->`, `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->`, `<!-- INJECT_ACTIVITY: fill-in-locative-forms -->`, `<!-- INJECT_ACTIVITY: quiz-locative-functions -->`  
Issue: The quiz/fill-in markers are duplicated and placed too early; the first quiz appears before temporal and `по` functions are taught, and the first fill-in appears before `по ___` is taught.  
Fix: Remove the early quiz/fill-in markers, keep one fill-in after the `по` section, and keep one quiz at the end.

[DIMENSION 9] [SEVERITY: major]  
Location: `> — **Викладач:** Добрий день! Як ваші справи на цьому тижні?`  
Issue: This line sounds translated and stiff.  
Fix: Replace it with a more natural tutor prompt such as `Що у вас заплановано на цьому тижні?`

[DIMENSION 6] [SEVERITY: minor]  
Location: `This preserves the beautiful logic of the locative case showing the "where" or "how" of an action.`  
Issue: Generic filler; it does not teach anything concrete.  
Fix: Replace it with a precise explanation of channel/path vs. topic marking.

## Verdict: REVISE
Critical linguistic problems remain, and the exercise-marker logic does not match the plan. The module is salvageable with deterministic edits, so this is `REVISE`, not `REJECT`.

<fixes>
- find: "> — **Ігор:** Не хвилюйся. Це не велика проблема. *(Don't worry. It is not a big problem.)*"
  replace: "> — **Ігор:** Не хвилюйся. Це невелика проблема. *(Don't worry. It is not a big problem.)*"
- find: "In Ukrainian, we use the preposition «по» with the **місцевий** (locative) case to talk about the means or channel of communication. This pattern describes how information travels from one person to another. Common examples include «по телефону» (by phone), «по радіо» (on the radio), «по пошті» (by mail), and «по дорозі» (on the way)."
  replace: "In Ukrainian, we use several common expressions with «по» to talk about a channel or path, such as «по телефону» (by phone), «по радіо» (on the radio), and «по дорозі» (on the way). For sending something by mail, standard Ukrainian often prefers «поштою», so learners should memorize the whole expression rather than generalize «по» to every noun."
- find: "Я часто говорю з мамою по телефону. Ми почули гарні новини по радіо. Мій брат надіслав лист по пошті. Ми зустріли друга по дорозі додому."
  replace: "Я часто говорю з мамою по телефону. Ми почули гарні новини по радіо. Мій брат надіслав лист поштою. Ми зустріли друга по дорозі додому."
- find: "Notice how these phrases describe the method of connection or the path something takes. The word for mail changes to «пошті», and the word **телефон** (phone, telephone) takes the special locative ending «-у» to form «по телефону»."
  replace: "Notice how these phrases describe the method of connection or the path something takes. Because some Ukrainian forms are syncretic, it is safer to learn the full expressions: «по телефону», «по радіо», «по дорозі», but «надіслати лист поштою»."
- find: "Mixing these up changes the meaning entirely. Always use «по» + locative for how you communicate, and «про» + accusative to share a **думка** (thought, opinion) about a specific subject, whether physical or **абстрактний** (abstract)."
  replace: "Mixing these up changes the meaning entirely. Use «по телефону» and «по радіо» for the channel of communication, «поштою» for sending something by mail, and «про» + accusative to share a **думка** (thought, opinion) about a specific subject, whether physical or **абстрактний** (abstract)."
- find: "Завтра я подзвоню тобі по телефону. Ми часто чуємо цікаві новини по радіо. Він надіслав важливі документи по пошті."
  replace: "Завтра я подзвоню тобі по телефону. Ми часто чуємо цікаві новини по радіо. Він надіслав важливі документи поштою."
- find: "> — **Марія:** Я надіслала тобі новий план по пошті. *(I sent you a new plan by mail.)*"
  replace: "> — **Марія:** Я надіслала тобі новий план поштою. *(I sent you a new plan by mail.)*"
- find: "**Grammar box** — The preposition «по» followed by the locative case is the traditional, authentic Ukrainian pattern for describing means or paths. In modern grammar, you might sometimes see «по» used with the dative case to express distribution, like giving things out «по одному» (one by one). However, for communication means and paths («по телефону», «по пошті», «по дорозі»), the locative case remains strictly the standard. This preserves the beautiful logic of the locative case showing the \"where\" or \"how\" of an action."
  replace: "**Grammar box** — Fixed expressions like «по телефону», «по радіо», and «по дорозі» can mark a channel or path. But when you mean \"by mail\", standard Ukrainian often prefers the instrumental form «поштою». Do not confuse these expressions with «про» + accusative, which names the topic of conversation."
- find: "<!-- INJECT_ACTIVITY: quiz-identify-the-function-of-locative-in-each-sentence -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in-locative-forms -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->"
- find: "<!-- INJECT_ACTIVITY: quiz-locative-functions -->"
  replace: "<!-- INJECT_ACTIVITY: quiz-identify-the-function-of-locative-in-each-sentence -->"
- find: "> — **Викладач:** Добрий день! Як ваші справи на цьому тижні? *(Good day! How are your things this week?)*"
  replace: "> — **Викладач:** Добрий день! Що у вас заплановано на цьому тижні? *(Good day! What do you have planned for this week?)*"
</fixes>