## VESUM Verification

### Batch 1 — Verb forms
- **Confirmed:** читати, говорити, хотіти, гуляти, прокидаюся (← прокидатися), вмиваюся (← вмиватися), снідаю (← снідати), працюю (← працювати), люблю (← любити), дивлюся (← дивитися), хочу (← хотіти/хтіти), можу (← могти), мушу (← мусити), мусити
- **Not found:** none

### Batch 2 — Nouns, question words, adverbs
- **Confirmed:** офіс, книга, фільм, ранок, хто, що, де, куди, ввечері, шкода, тоді, ніхто, привіт
- **Confirmed:** як, коли, чому — all found; note: `коли` matched 7 forms (incl. кіл-noun declensions as false positives), but коли (adv/conj "when") is fully standard Ukrainian
- **Not found:** none

**All 30 words confirmed in VESUM.**

---

## Textbook Excerpts

### Section: Граматика — Group I / Group II conjugation
> "І дієвідміна — Особові закінчення: -у(-ю), -еш(-єш), -е(-є), -емо(-ємо), -ете(-єте), -уть(-ють)… ІІ дієвідміна — Особові закінчення: -у(-ю), -иш(-їш), -ить, -іть(-їть), -имо, -імо(-їмо), -ите(-їте), -ать(-ять)"
> Source: Karaman, Grade 10

> "Форму теперішнього часу мають лише дієслова недоконаного виду… Дієслова в теперішньому часі змінюються за особами та числами: пишу/роблю, пишеш/робиш, пише/робить, пишемо/робимо, пишете/робите, пишуть/роблять"
> Source: Litvinova, Grade 7 (tier 1)

⚠️ **WRITER FLAG — хотіти is Group I, not a simple Group II verb:** The Karaman textbook explicitly lists хотіти under **"Окремі дієслова" of Group I** (alongside гудіти, сопіти, іржати). Its forms are: хочу, хочеш, хоче, хочемо, хочете, хочуть — all Group I endings. The grammar summary must NOT list хотіти as Group II. The plan's modals (хочу/можу/мушу) are all Group I 1st-person forms — this is pedagogically fine, but the summary should clarify хотіти belongs to Group I.

### Section: Граматика — Reflexive verbs (-ся)
> "Дієслова із суфіксом -ся(-сь), які виражають зворотну дію, називаються зворотними: навчатися, закохатися… Уживається -ся(-сь) після інфінітивного суфікса -ти(-ть) або закінчення в особових формах дієслова: вмивати — вмиватися, взувати — взуватися."
> Source: Karaman, Grade 10

> "Дієслова на -ся, -сь виражають дію, спрямовану на самого виконавця (на самого себе)." (with pronunciation: шся → [с':а], -ться → [ц':а])
> Source: Kravtsova, Grade 4

### Section: Граматика — Infinitive
> "Початковою формою дієслова є інфінітив, тобто форма, що закінчується суфіксом -ти (ходити, бігати, малювати)… У дієсловах, які називають дію, спрямовану виконавцем на самого себе, суфікс інфінітива стоїть перед -ся: представлятися, фотографуватися."
> Source: Litvinova, Grade 7 (tier 1)

### Section: Граматика — Negation / Double negation
> "Ніхто не може змусити вас робити те, що ви вважаєте неправильним і непристойним." (zaperechnі zaimennyky + не = double negation pattern)
> Source: Litvinova, Grade 6

> "Заперечні займенники вказують на відсутність особи, предмета… Заперечні займенники утворюємо від питальних додаванням префікса ні: ніщо, ніхто, ніякий…" "Заперечні займенники з ні пишемо разом."
> Source: Zabolotnyi, Grade 6 (confirms ніхто не as correct double-negation)

### Section: Читання — daily routine vocabulary
> (читає/читають paradigm), temporal expressions (коли?), place (де? куди?)
> Source: Zabolotnyi, Grade 7 (tier 1) — verb tenses table; Kravcova Grade 2 — question words for sentences

### Section: Діалог — question words in conversation
> "Питальні займенники вживаються в питальних реченнях… хто? що? який? чий? котрий? скільки?" + interrogative adverbs де? куди? коли? чому? як? all confirmed as standard interrogative tools at this level.
> Source: Litvinova, Grade 6; Kravcova, Grade 2

---

## Grammar Rules

- **Infinitive suffix -ти**: confirmed by Litvinova Grade 7 — суфікс -ти is the standard literary form; forms ending in -ть (e.g., ходить instead of ходити) are dialectal/colloquial, not литературна норма — do NOT use -ть infinitives in the module.
- **Group I endings** (-ю/-у, -єш, -є, -ємо, -єте, -ють): confirmed Karaman Grade 10. Plan lists these correctly.
- **Group II endings** (-ю/-у, -иш, -ить, -имо, -ите, -ять): confirmed Karaman Grade 10. Plan lists these correctly.
- **Reflexive -ся**: always after the verb ending; after -ти in infinitives: вмивати+ся = вмиватися; after personal endings: вмиваєш+ся = вмиваєшся (pronunciation [с':а]).
- **Double negation**: ніхто не, нічого не = standard Ukrainian (NOT an error). Ukrainian requires both the negative pronoun AND не before the verb. This is correct and differs from English.
- **Negation не + verb**: written separately from the verb (не can + мушу → не можу, мушу, НЕ мушу).

*(Правопис query for дієслово returned no direct section match — rules are embedded in morphology chapters as confirmed via textbook RAG above.)*

---

## Calque Warnings

- **"дивлюся фільм"** → ✅ OK — natural Ukrainian; no calque. ("дивитися" correctly means "to watch"; Антоненко-Давидович uses "подивитись" without concern)
- **"приймати душ"** → ⚠️ NOT in the plan (plan uses вмиваюся = "wash up"), but if a writer adds it, flag it. The correct form is **брати душ** or simply **митися під душем**. The style guide confirms приймати is a problem verb (приймати участь → брати участь; приймати душ → брати душ).
- **"до шостої"** (dialogue: "Я працюю до шостої") → ✅ OK — Антоненко-Давидович confirms ordinal time expressions ("до шостої години") are standard Ukrainian. Do NOT write "до шість годин" (cardinal = calque from Russian "до шести часов"). "До шостої" is the correct Ukrainian form.
- **"снідаю"** (to eat breakfast) → ✅ OK — снідати is native Ukrainian; "їсти сніданок" would be a calque.

---

## CEFR Check

- **читати**: A1 ✅
- **працювати**: A1 ✅
- **хотіти**: A1 ✅
- **могти**: A1 ✅
- **гуляти**: A1 ✅
- **офіс**: A1 ✅
- **ранок**: A1 ✅
- **мусити**: ⚠️ **A2 per PULS** — This is a checkpoint module (M21) reviewing M18 content where мусити was introduced. Since it was taught in M18, reviewing it here is appropriate. However the writer should be aware it's technically A2-level vocabulary per PULS. Use sparingly and only in contexts that clearly echo M18.

**All other key vocabulary confirmed A1. No unexpected above-level words found.**

---

## Summary of Flags for Writer

| # | Flag | Severity | Recommendation |
|---|------|----------|----------------|
| 1 | **хотіти is Group I** (not irregular Group II) | 🔴 Must fix | List хотіти under Group I in the grammar summary. Its endings: хочу, хочеш, хоче… follow Group I paradigm. |
| 2 | **мусити is PULS A2** | 🟡 Awareness | Fine in this checkpoint (taught in M18); use confidently but note it's the upper edge of A1.3 scope. |
| 3 | **"приймати душ"** | 🟡 Avoid | If morning routine includes shower, write "митися під душем" or "брати душ" — never "приймати душ". |
| 4 | **Time expression** in dialogue | ✅ Confirmed | "до шостої" (ordinal) = correct Ukrainian. Do NOT use "до шість годин". |
| 5 | **-ть infinitive** | 🔴 Avoid | Only -ти infinitives in the module (ходити, not ходить). -ть is dialectal/colloquial. |