# Book-pattern coverage and unresolved senses

Authority: Антоненко-Давидович, «Як ми говоримо». The source inventory has
342 structured records and 169 prose page chunks under
`antonenko-davydovych-yak-my-hovorymo`. Structured records include duplicate
headings, verse lines and general grammatical discussions; 342 is not a calque
denominator. The structured `russianism_pattern` column is neither complete nor
safe to execute (some values are recommendations, rather than rejected forms).
Both `search_style_guide` and source-scoped `search_text` were queried; prose
pages supply the locations in the reviewed table. An empty structured search
does not exclude a prose rule. The table is data, not an automatically extracted
list of anything following “замість”. That word also introduces optional style
improvements and quotations that the author expressly defends.

`antonenko_data.py` records each admitted surface rule, recommendation, page,
positive and negative. Inflections use VESUM lemma/POS readings. The participation
rule covers the clean VESUM verb paradigms of both `приймати` and `прийняти`,
including analytic futures and intervening adjectives. Temporal `на протязі`
requires a genitive duration with VESUM-attested genitive modifiers; nominative
or accusative quantifiers before or after the duration break the match. Literal
draughts, proper names, borrowing suggestions and ordinary function words do not
constitute pattern evidence. Recommendations are guidance, not inflection-aware
automatic rewrites.

The following **55 residual entries** lack a safe, general surface decision in
this layer. Each needs meaning, discourse, syntactic role or unavailable form
evidence; matching an arbitrary printed sentence alone would not resolve it.
Owner for source/sense adjudication: the #9640 accountable driver. No residual
licenses a firm finding or a fabricated paradigm. `<!-- VERIFY -->` applies to
the unresolved classification, not to the existence of the cited discussion.

| # | Discussion / prose page | Why withheld |
|---|---|---|
| 1 | Вид / вигляд, p.17–18 | Face, visibility, landscape, prospects and physical shape need noun senses; the unambiguous phrase subset is admitted. |
| 2 | Відношення, p.18–19 | Human relationships versus scientific ratios; `по відношенню до` and `у всіх відношеннях` are admitted separately. |
| 3 | Відсутність / присутність, p.19 | Absence of a person versus lack of a thing is semantic. |
| 4 | З метою, p.27 | Stylistic nominalization advice is not a categorical lexical calque. |
| 5 | Недолік, p.32–33 | Shortfall versus qualitative defect cannot be decided by the noun alone. |
| 6 | Переписка, p.35 | Copying versus correspondence needs the activity's meaning. |
| 7 | Поля / береги, p.37 | Agricultural fields versus page margins; a page reference alone can describe a picture of fields. |
| 8 | Порівняння, p.38 | The book permits actual comparison operations and discusses alternative phrasing; the prepositional span alone is insufficient. |
| 9 | Порядок, p.39 | Arrangement, custom and “all right” are distinct senses, with optional stylistic alternatives. |
| 10 | Посмішка, p.39–40 | Mockery versus a friendly smile needs intent. |
| 11 | Свідомість, p.42 | Broader social-awareness senses remain unresolved; only the printed loss/return collocations are admitted. |
| 12 | Становище, p.44 | Figurative predicament versus literal position; only `безвихідне становище` is admitted. |
| 13 | Вірний / вірно, p.51,131 | Loyalty versus correctness requires the proposition's meaning. |
| 14 | Живописний, p.54–55,164–165 | Painting versus scenery; institutional names must remain protected. |
| 15 | Запущений, p.56 | Launching, neglect and illness require referent senses. |
| 16 | Любий, p.58 | Affection versus unrestricted choice is not a surface distinction. |
| 17 | Старий, p.65 | Age versus long acquaintance requires facts about the referent. |
| 18 | Віддієслівні іменники, p.67–68 | The book explicitly permits them as subjects/objects; nominalization density is not positive calque evidence. |
| 19 | Пасивні дієприкметники, p.69 | Predicate versus attribute requires clause analysis; the book permits both with different roles. |
| 20 | Одружитися на, p.72 | Person-object government versus a following time/location phrase needs grammatical role; do not reject every `на`. |
| 21 | Відчитати, p.75 | Reading/reporting versus reprimanding needs the action's sense. |
| 22 | Збутися, p.80 | Getting rid of something versus a prediction coming true is semantic. |
| 23 | Знаходитися, p.81–82 | Search/discovery versus static location cannot be decided by the lemma. |
| 24 | Зустрічатися, p.82,153–154 | A meeting versus an occurrence needs subject meaning. |
| 25 | Іти назустріч, p.83 | Literal movement versus assistance; do not flag approaching a person. |
| 26 | Користуватися успіхом, p.83,155 | The book explicitly permits deriving a benefit from success; popularity versus benefit needs discourse. |
| 27 | Нагадувати, p.87 | Reminding versus resembling requires the predicate's meaning. |
| 28 | Носити ім'я, p.88 | Naming an institution versus literal carrying/inscription cannot safely be inferred from the short phrase. |
| 29 | Привести, p.91 | Leading/moving versus causing adverse consequences; the book permits memory, motion and equilibrium expressions. |
| 30 | Присвоїти, p.91–92 | Institutional conferment versus improper self-appropriation needs agent and intent. |
| 31 | Рахувати / числитися, p.92–93 | Counting, membership and opinion require grammatical/semantic roles; regional attestation is not a blanket calque verdict. |
| 32 | Не дивлячись, p.104 | Literal not looking and concessive “despite” share the surface; the book explicitly defends literal use. |
| 33 | Години, p.106,152 | Clock time versus elapsed duration; numeral + `годин` alone cannot decide. |
| 34 | Зараз, p.111 | Immediate moment versus an extended current period needs discourse. |
| 35 | По рахунку, p.113 | A bill versus a small measured allowance is semantic. |
| 36 | Як би не / не то / не бійсь, p.120–121 | Conditional negation, literal negation and fear are legitimate; concessive/disjunctive/modal readings require clause interpretation. |
| 37 | Наглий / покращити / професійний, p.160,167 | Suddenness versus insolence, beauty versus quality, and professional domains versus professionals require senses. |
| 38 | Unattested calque paradigms, pp.31,55,86,99–103,112,131,134–145 | The table retains book-attested spellings of unattested lemmas, but no VESUM paradigm exists to justify inventing further inflections. Active-participle roles and lexicalized adjectives also need syntactic evidence. The coined recommendation `утопальник` is absent from VESUM; the admitted rule uses the book's attested descriptive alternative `той, що втопає`. |
| 39 | Прийняти пропозицію, p.91 | Withdrawn: the alternatives concern approval/adoption by an assembly. Accepting an offer to become a director, or an offer from another person, is legitimate. A nearby meeting word alone does not establish the subject or sense. |
| 40 | По моїй думці, formerly p.117 | Withdrawn: both `search_style_guide` and source-scoped `search_text` were queried; an exact full-book scan found no passage containing this phrase. Page 117 prints `по-моєму`, with a preference for another expression. Search ranking does not prove exact phrase presence. |
| 41 | Як не дивно, p.131 | Withdrawn: `краще` recommends an alternative without condemning this phrase. Page 137 explicitly distinguishes suggestions from categorical rules. |
| 42 | Прийняти постанову, p.91 | Withdrawn: the passage says `краще користуватись`; no separate condemnation supports a firm finding. |
| 43 | Як правило, p.40 | Withdrawn: the passage identifies borrowing and recommends remembering native alternatives, without condemning the phrase categorically. |
| 44 | Приймати міри; прийняли всі необхідні міри | Withdrawn: page 31 discusses `міроприємство`, not this collocation. Neither required search surface supplied positive evidence; exact full-book scanning found no condemned collocation. Both the adjacent form and the intervening-modifier miss need an actual source citation before admission. <!-- VERIFY --> |
| 45 | Наносити шкоду / образу / смуток / жаль / сором, p.161 | Withdrawn: the book explicitly permits the literal `нанести шкоду` when carrying dirt/snow into a house. Surface matching cannot decide figurative harm versus bringing something harmful. |
| 46 | Прийняла свою гірку участь: possible fate sense | `query_sum20` has no offline entry; `search_slovnyk_me` returned a bounded ВТС participation snippet, which does not resolve the fate sense. Participation behavior is unchanged, as the brief prescribes for undetermined senses. It may still produce a firm finding; this unresolved risk belongs to the driver and requires source adjudication. <!-- VERIFY --> |
| 47 | Не приймали участі, p.91 | Miss: genitive after negation needs agreement/negation scope and a case-aware noun alternative; the admitted noun atom remains `участь`. |
| 48 | Приймали також участь, p.91 | Miss: only intervening adjectives are transparent. Adverb/clause scope is not admitted; arbitrary intervening words must not join unrelated verb and noun uses. |
| 49 | Участь… ми приймали, p.91 | Miss: reversed order and ellipsis need clause/object attachment. The forward whitespace-only matcher deliberately cannot cross punctuation. |
| 50 | Вилазить зі шкіри, p.158 | Miss: the admitted verb lemmas are `лізти` and `вилізти`. Further verbs require lexical/sense adjudication, including literal versus figurative use. |
| 51 | Вона й вигляду не подала, p.90 | Miss: noun-before-verb order requires negation and predicate attachment; only verb-before-noun with an explicit feigning complement is admitted. |
| 52 | І вигляду не показав, p.18 | Miss: noun-before-verb order remains withheld for the same attachment boundary as row 51. |
| 53 | Ні–ні та й, p.121 | Miss: the shared tokenizer splits the en-dash spelling into two words, unlike the hyphenated admitted form. Changing shared tokenization is outside this packet; accepting arbitrary separators would misread literal negation. The citation audit normalizes this typography only for source presence, not production matching. |
| 54 | Capitalised-after-colon and all-caps phrases | Miss: the existing proper-name guard withholds non-sentence-initial capitals. Capitalization alone cannot resolve names versus emphasis without broader named-entity context. |
| 55 | На протязі 2 років: digit duration | Withheld: digits have no VESUM case evidence. The previous unconditional numeric skip could manufacture a duration; digits before or after the duration are withheld; spelled-out genitive numerals remain supported. |

General declension, gender, agreement, paronym, immersion, spelling and optional
synonym discussions are not automatically calque entries. Proper-name spelling
and borrowings (for example the book's `банкет`/`бенкет` preference and discussion
of international technical words) are excluded from calque admission. Source
calque classification outside the admitted table and the listed residuals still
requires independent Ukrainian review; this inventory does not certify that
every calque in every edition has been independently adjudicated.

Round-2 source receipt: **72 admitted patterns / 39 cited chunks**. Use the task-prescribed project interpreter with
`-m scripts.verification.verify_antonenko_citations` to open each
chunk read-only and check its independent literal anchor from
`antonenko_citations.py`. Missing/wrong-source chunks, absent forms and anchor
inventory drift fail the audit. Literal presence proves the citation location,
not condemnation or semantic safety. Preference-only entries are residuals;
`feign` stays admitted because p.18 also calls the analogous expression
`такого ж хибного`, while `moving-participle` p.103 explicitly rejects a
`штучного невдалого витвору`. Neither relies solely on `краще`.

The consciousness rules now exclude a whitespace-adjacent genitive complement
(including possessive adjectives), as p.42 defends awareness of obligations.
VESUM-attested `утратити`/`утрачати` reuse that same guard. A firm book finding
supersedes a shadow heuristic only on the identical item/span; unmatched
occurrences retain their own evidence.

Round-2 stopping rule: the next independent review blocks only on a firm
finding for correct Ukrainian, a citation the book does not support, or a
regression. The additional counterexamples are author regression tests, not
independent held-out proof. The driver owns the next review and all 55 residual
entries; this pushed author revision does not certify issue completion.

Separate existing checker behavior: stress can be ambiguous for an otherwise
correct word (including `гостей`, `протяг` and `правило`). UA-GEC can suggest a
contextual replacement of a correct content word (for example `прийшов`). Those
are not book calque findings. The fixed clean-text acceptance corpus comprises
30 independently word-verified sentences tested with all default checks; ten
additional sense negatives exercise the book layer without asserting that the
existing stress/collocation layers have no other findings. Independent held-out
source evaluation and exact-head cross-family approval remain the driver's gates.
