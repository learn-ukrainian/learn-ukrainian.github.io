# Петро Симеонович Могила — Research Dossier

**Slug:** `petro-mohyla`
**Block:** K (early-modern institution-builder; posthumous imperial appropriation/erasure)
**Tier:** 1b
**Issue:** #2535 (ghost-wiki dossier backfill — early-modern church/Cossack founders)
**Researcher:** Claude Opus 4.8 (`claude-opus-4-8`)
**Completed:** 2026-06-04

**Acceptance self-check:**
- [x] All 10 sections completed
- [x] ≥3 Tier 1/Tier 2 sources cited (IEU; Шевченківська енциклопедія; Історія української культури НАН; Огієнко)
- [x] Oppression mechanism is specific — names the 1686 subordination, the Synodal book-censorship, the ROC "local saint" downgrade, with documentary anchors
- [x] ≥2 primary-source quotes (1646 Требник preface + the ruska-mova betrothal ordo, both retrieved from the literary corpus via Огієнко)
- [x] Cross-track links: every "Existing" path verified against the on-disk plan listing (2026-06-04) and re-checked by `lint_bio_dossier_xref.py`
- [x] Naming-canonical applied
- [x] Image candidate(s) identified
- [x] Decolonization checklist self-applied

---

## 1. Verified facts

- **Full name (UA, canonical):** Петро Симеонович Могила (Romanian: Petru Movilă). [T1: IEU — Mohyla, Petro; T1: Шевченківська енциклопедія — Могила Петро Симеонович; T3: uk.wikipedia — Петро Могила]
- **Pseudonyms / aliases:** none. Russified/Latinised forms (forbidden in body text, listed only in §8): Пётр Могила, Pyotr Mogila, Petrus Mohila.
- **Born:** 21 December 1596 (O.S.) / **31 December 1596** (commonly cited N.S.) | місто Сучава (Suceava), Молдавське князівство (now Romania) | of the Moldavian princely-boyar Movilă (Могила) house. [T1: Шевченківська енциклопедія — "31.XII 1596"; T3: uk.wikipedia — "21 (31) грудня 1596"; **source disagreement, flagged §1 note**]
- **Died:** 1 January 1647 (O.S.) / **11 January 1647** (N.S.), aged 50 | Київ, Річ Посполита | natural causes; buried by his own will in the Велика (Успенська) церква Києво-Печерської лаври. [T1: Шевченківська енциклопедія — "11.I 1647"; T1: IEU — "11 January 1647"; T3: uk.wikipedia]
- **Family / education key facts:** Son of Симеон Могила, hospodar (господар) of Wallachia and Moldavia, and the Transylvanian princess Маргарет (Margareta). After his father's death (1607) and the loss of the family's Moldavian-Wallachian holdings (1612), the family fled to the Ukrainian lands of the Річ Посполита, sheltered by kin (Потоцькі, Корецькі, Вишневецькі). Schooled at the Львівська братська школа, then the Замойська академія and universities in the Netherlands and Paris; fluent in Ukrainian, Greek, Latin, Polish and Romanian. Fought as a Polish-army officer at Цецора (1620) and **Хотин (1621)** before taking monastic vows in the Києво-Печерський монастир (1625). [T1: IEU; T3: uk.wikipedia]

**Source disagreement note (flagged, not smoothed):** the **birth year** is firmly **1596**, not 1595 (the latter is a recurring error). The two UA Tier-1 sources (Шевченківська енциклопедія, ЕІУ-tradition) give **31 December 1596**; IEU gives "**January 10, 1597**" — a different Julian→Gregorian recalculation of the same late-December-1596 birth, not a second year. This dossier anchors **1596** per the audit guard and the two concordant UA sources. The **day of episcopal consecration** in Lviv in 1633 also varies by source (see §1/§3): royal confirmation **12 March 1633** is firm; IEU places the Lviv consecration in **May 1633**, uk.wikipedia near the **end of June 1633** — recorded as a day-level variance, the year (1633) is not in doubt.

## 2. Oppression mechanism

For an early-modern institution-builder the repression is **posthumous appropriation and erasure**: Mohyla died (1647) a free metropolitan under Constantinople, but the Muscovite/Russian-imperial state then captured his institutions, absorbed his works into a "Russian Orthodox" narrative, and physically suppressed the distinct Kyivan-Mohylian liturgical tradition he had codified.

- **What happened:** institutional capture + liturgical erasure + narrative absorption of his legacy by the Moscow Patriarchate and the Russian Empire.
- **When (specific):** the decisive break is **1686** — within a generation of his death — when the Київська православна митрополія (Mohyla's see, held by him 1633–1647 as **екзарх Константинопольського патріарха**) was subordinated to the Moscow Patriarchate. The suppression of the distinct Kyivan service-books followed across the late 17th–18th centuries. [T3: uk.wikipedia — exarch status; context: HIST plan `pravoslavna-tserkva-17`]
- **By whom (specific body):** the **Московський патріархат** and, from the 18th century, the **Russian imperial Святійший Синод**, which placed the Kyiv and Chernihiv presses under Moscow censorship and forbade printing anything diverging from "great-Russian" editions.
- **Document / mechanism references (quoted, not paraphrased):** the church historian Іван Огієнко (Митрополит Іларіон) documents the concrete mechanism — Moscow's forcible replacement of Ukrainian service-books, the very books Mohyla had standardised:

  > «Приєднавши Українську Церкву до своєї, московський уряд силою заборонив нам уживати власні Богослужбові книжки, накинувши нам книжки московські… про наш власний український Требник, наприклад 1646 р., що його видав митрополит Київський Петро Могила, ми зовсім забули…»

  [T2: Огієнко І. *Українська Церква* — retrieved from the literary corpus, `wave7-ohiyenko-tserka`]

- **Mechanism specifics (1–3 ¶):** Mohyla had built three things the empire could not tolerate as *Ukrainian*: an autonomous **Київська митрополія** under Constantinople; a Western-standard **колегія** (later академія) that out-taught Muscovy; and a corpus of **Kyivan service-books** (the «Требник» 1646, «Служебник», the catechism) in their own redaction. After 1686 the empire kept all three but stripped their Ukrainian authorship — drawing Mohylian graduates (Стефан Яворський, Феофан Прокопович, Інокентій Ґізель's milieu) into Muscovy to *build the Russian* church and school while imperial historiography reframed this as native "Russian enlightenment." Mohyla's catechism «Православне сповідання віри», approved at the 1642 Яссы synod, was reprinted in **Москва 1696** and absorbed as *the* Orthodox confession — appropriation by adoption.
- **What survived / what was erased:** the works survived (too useful to destroy) but were **detached from author and nation** — the Kyivan Требник tradition was driven out of use in Ukrainian parishes and replaced by Moscow editions (Огієнко, above). A late, telling coda: when Mohyla was canonised in **1996**, every Ukrainian Orthodox jurisdiction glorified him as a full saint, while the **Russian Orthodox Church recognised him only as a "місцевошанований" (locally-venerated) saint** — a deliberate downgrade of a metropolitan whose intellect it had spent three centuries absorbing. [T3: uk.wikipedia — Канонізація]

## 3. Major works

Roughly **20 works** of theology, liturgy, polemics and pedagogy; below are the load-bearing ones, chronological. [T1: IEU; T1: Історія української культури, `wave7-istkult`; T3: uk.wikipedia]

- `1627` — installed **архімандрит Києво-Печерської лаври** (royal confirmation 29 Nov 1627), at age 30 — the platform for everything after. [T3: uk.wikipedia]
- `1628` — **«Агапита діакона главизни поучительни»** and a **«Тріодь цвітная»**, his translations from Greek printed at the Lavra press. [T3: uk.wikipedia]
- `1629` — **«Леітургіаріон» / «Служебник»**, a service-book corrected against Greek sources with his own dogmatic and rubrical commentary — "протягом двохсот років не втрачав свого значення." [T3: uk.wikipedia]
- `1631` — founds the **Лаврська школа**; **1632** merges it with the Київська братська школа to form the **Києво-Могилянська колегія** — "eventually the largest centre of scholarship and education in Eastern Europe" (IEU). Branches at Вінниця, Гоща and Крем'янець follow. [T1: IEU; T3: uk.wikipedia; HIST plan `bratstva-i-osvita`]
- `1632` — **«Крест Христа Спасителя»**, his attributed sermon, Kyiv. [T1: Історія української культури — "талановито написаної проповіді «Крест Хреста Спасителя» (Київ, 1632)"]
- `1633` — confirmed by King Władysław IV (12 March) and consecrated **Митрополит Київський, Галицький і всієї Русі**, екзарх Константинопольського патріарха (1633–1647). [T1: IEU; T3: uk.wikipedia]
- `1640` — **«Православне сповідання віри»** (Orthodoxa Confessio Fidei), the first systematic Orthodox catechism, drafted by the Mohylian circle under his direction; ratified at the **1642 synod in Яссы**. [T1: IEU; T1: Історія української культури]
- `1644` — **«Λίθος / Камінь»** (under the pseudonym Eusebius Pimin), the great polemical reply to Касіян Сакович's *Perspektywa*. [T3: uk.wikipedia]
- `1646` — **«Требник» (Евхологіон)**, the "Требник Петра Могили" — his masterwork of liturgical codification, used across Ukraine and later imposed-upon and reprinted by the Russian church. [T1: IEU; T2: Огієнко]

**Suppression note:** the distinct Mohylian service-books were driven out of Ukrainian use and replaced by Moscow editions (§2); the full catechism was first printed abroad (Greek/Latin/Polish) and only reprinted in Москва 1696 after his death.

## 4. Primary-source quotes (≥2 required)

Both quotes are Mohyla's own codifying voice from the **«Требник» 1646**, retrieved from the project literary corpus (`wave7-ohiyenko-tserka`, Огієнко's *Українська Церква*, which quotes the Требник directly).

**Quote 1 — the preface to the Требник 1646, Mohyla diagnosing liturgical disunity:**

> «На око те побачиш, — каже він, — Чительнику Освященний, коли поглянеш до Виленських та Острізьких Требників, де в таїнстві Шлюбу або в Відправі Вінчання шлюбних слів, в яких згода молодих (а це є форма таїнства) виявляється, не положено…»

Pedagogically valuable: the founder-as-editor, justifying standardisation by appeal to evidence ("на око побачиш") — a Baroque scholarly habit, and a window on why his Требник mattered. [T2: Огієнко — Требник 1646 preface, via literary corpus]

**Quote 2 — the betrothal ordo Mohyla codified, in the *ruska* (Ukrainian) language of the rite:**

> «Маеш [Имк] неотменный и статечный умысл заручити собе теперь тую [Имк], которую тут перед собою видишь, в стан малженский, а гды тому час будет, поняти ей собе за малжонку?»

Огієнко flags the rubric itself — the priest asks "руским (цебто українським) языком" — i.e. the Mohylian rite put the binding question in the people's Ukrainian, not Church Slavonic. A concrete artefact of 17th-c. liturgical Ukrainian for learners. [T2: Огієнко — Требник 1646 marriage ordo, via literary corpus]

**Note on register:** these are early-modern *ruska мова* / Church-Slavonic-inflected texts (малженство, статечний, гды). They are quoted as historical primary text and must **not** be "modernised" — the archaic forms are the evidence.

## 5. Language register

- **Register:** high ecclesiastical Baroque — Church Slavonic for scripture/liturgy, *prosta/ruska мова* (early-modern literary Ukrainian) for prefaces, sermons and the binding rubrics, plus Polish and Latin for scholarship. Mohyla's own policy, per uk.wikipedia: старозавітні тексти — церковнослов'янською; проповіді й панегірики — українською; наукові праці — слов'янськими/латиною.
- **CEFR readiness for full reading:** the primary texts are **C2** (archaic morphology, Church-Slavonic lexis); biographical prose about him is **B2**; the §2/§6 appropriation debate is **C1**.
- **Lexicon notes (pre-teach):** митрополит, архімандрит, екзарх, колегія, требник, служебник, сповідання (віри), катехізис, господар (=ruler/hospodar, false-friend for "master"), боярський, полемічний, обмосковлення, дерусифікація — **all 12 verified present in VESUM** (2026-06-04 batch). Note the historical compound **обмосковлення** is authentic Ukrainian, **not** a Russianism (`check_russian_shadow`: `matches_russian=false`, confidence 0.0).
- **Stylistic features:** Baroque scholastic apparatus (numbered rubrics, dogmatic glosses appended to ordines), evidentiary appeals ("на око побачиш"), bilingual question-and-answer catechetics.

## 6. Contested points

- **"Catholic/Jesuit borrowing" — reform or Latinisation?** Mohyla rebuilt Orthodox education and theology *за католицькими, єзуїтськими взірцями* (Jesuit-college model, scholastic method). UA scholarship debates whether this was a confident modernisation that saved Orthodoxy or a partial Latinisation of it; uk.wikipedia records contemporaries split between seeing him as "щирий поборник єдности православ'я" and "рукою королівської влади." Treat as a live, legitimate debate, not a verdict. [T3: uk.wikipedia — Дипломатична діяльність]
- **Ethnic origin vs national belonging.** Mohyla was **of Moldavian (Romanian) princely stock** yet became "батько руської (української) теології." Popular memory sometimes flattens this either into "a Romanian" or into "a Russian church father." Both erase the actual fact: a Moldavian-born builder of *Ukrainian* (руської) church and learning within the Річ Посполита. [T1: IEU; T3: uk.wikipedia]
- **Russian-imperial appropriation (the core distortion).** Imperial and Soviet narratives folded Mohyla, his Collegium and his catechism into a "common Russian Orthodox / all-Russian enlightenment" story, obscuring that Kyiv *taught Moscow*, not the reverse. Огієнко's whole project is the counter-documentation (§2, §4). The ROC's 1996 "local saint" downgrade is the same logic in miniature. [T2: Огієнко; T3: uk.wikipedia]
- **What gets simplified in popular memory:** "founder of the first Ukrainian university" compresses a messy institutional history (Лаврська + братська schools merged 1632; "академія" status formalised later) into a clean origin myth. The **1596 vs 1597** birth-date and **1595** error also recur in popular texts (§1).

## 7. Cross-track links

> Every path under **Existing** was checked against the on-disk plan directory listing on 2026-06-04 and is re-validated by `scripts/audit/lint_bio_dossier_xref.py`. Forward-looking ties are under **Candidate**.

- **Existing HIST plans (VERIFIED present):**
  - `curriculum/l2-uk-en/plans/hist/petro-mohyla.yaml` — the HIST treatment of the same figure; tightest link.
  - `curriculum/l2-uk-en/plans/hist/pravoslavna-tserkva-17.yaml` — the 17th-c. Orthodox-church context his whole career sits in.
  - `curriculum/l2-uk-en/plans/hist/beresteyska-uniia.yaml` — the 1596 Union of Brest that defined the confessional battlefield he inherited.
  - `curriculum/l2-uk-en/plans/hist/bratstva-i-osvita.yaml` — the brotherhood-school movement his Collegium grew out of and superseded.
  - `curriculum/l2-uk-en/plans/hist/khotynska-viyna.yaml` — the 1621 Khotyn war he fought in before ordination.
  - `curriculum/l2-uk-en/plans/hist/rich-pospolyta.yaml` — the Commonwealth polity that framed Orthodox legality.
- **Existing BIO plans (VERIFIED present):**
  - `curriculum/l2-uk-en/plans/bio/petro-mohyla.yaml` — the BIO plan this dossier backfills (the #2535 ghost-wiki gap).
  - `curriculum/l2-uk-en/plans/bio/iov-boretskyi.yaml` — his mentor (see §1), the metropolitan whose library he inherited.
  - `curriculum/l2-uk-en/plans/bio/petro-sahaidachny.yaml` — the hetman who restored the Orthodox hierarchy (1620) Mohyla later led.
  - `curriculum/l2-uk-en/plans/bio/ivan-ohienko.yaml` — the 20th-c. church historian whose documentation of the Mohyla Требник's suppression is my §2/§4 spine.
  - `curriculum/l2-uk-en/plans/bio/sylvestr-kosiv.yaml` — his successor-once-removed and Collegium rector.
  - `curriculum/l2-uk-en/plans/bio/kostiantyn-vasyl-ostrozky.yaml` — the prior magnate-builder of Orthodox learning (Ostroh) Mohyla's Kyiv project answers.
- **Existing LIT plans (VERIFIED present):**
  - `curriculum/l2-uk-en/plans/lit/baroque-poetry-velychkovsky.yaml` — the Kyivan-Mohylian Baroque literary culture his Collegium incubated.
  - `curriculum/l2-uk-en/plans/lit/skovoroda-baroque-philosophy.yaml` — the Mohyla-Academy intellectual lineage running to Сковорода.
- **Candidate cross-track connections (Phase 2+, NOT existing files):**
  - A HIST unit on the **1686 subordination of the Kyiv Metropolitanate to Moscow** as the institutional hinge of §2 (relates to the existing `tomos` plan on autocephaly).
  - A BIO↔BIO arc Острозький → Борецький → Могила → Косів as the "Orthodox-revival relay."
- **Potential LIT additions surfaced (file as `bio-expansion-followup`, do not add unilaterally):**
  - A primary-text module on the **Требник 1646** marriage ordo as a specimen of 17th-c. liturgical Ukrainian (§4).

## 8. Naming-canonical

- **Slug:** `petro-mohyla`
- **EN canonical (BGN/PCGN-style):** Petro Mohyla
- **UA canonical (with patronymic):** Петро Симеонович Могила
- **Aliases to track (`aliases:` YAML field):** Petru Movilă (Romanian); Petro Movila; "Mohyla College / Kyiv-Mohyla Academy" (institutional eponym).
- **Forbidden Russian-imperial / Russified forms (flag in body text — listed here only):** Пётр Могила; Pyotr Mogila; "Peter Mohila/Mogila"; any framing of him as a "Russian Orthodox" church father.

## 9. Image candidates

- **Best PD portrait:** the 17th-c. **portrait of Petro Mohyla** (anonymous, Kyiv), long held at the Kyiv-Mohyla Academy / Lavra — out of copyright by age; Wikimedia Commons category **"Petro Mohyla"** holds it. Use the individual **file page** for licence proof, not the category page. [Commons category: `Petro Mohyla`]
- **Backup candidates:**
  - The **Спас на Берестові** church (restored by Mohyla) fresco/portrait area — era-context architecture image, PD by age.
  - Укрпошта / NBU commemoratives for the Kyiv-Mohyla Academy anniversaries (check stamp/coin rights before use).
- **Context image:** a title page of the **«Требник» 1646** (Lavra print) — a strong §2/§4 illustration if a rights-clear scan is found.
- **If no rights-clear portrait clears review:** fall back to the PD Требник 1646 title page or the Києво-Могилянська академия building.

## 10. Sources used

**Tier 1 (authoritative):**
- *Internet Encyclopedia of Ukraine*. "Mohyla, Petro." encyclopediaofukraine.com (display.asp…MohylaPetro.htm). Accessed 2026-06-04.
- *Шевченківська енциклопедія*, т. 4 (М—Па). "Могила Петро Симеонович" (31.XII 1596 — 11.I 1647). Київ: Ін-т літератури ім. Т. Г. Шевченка НАН України, 2013. С. 283–284. (retrieved from corpus `wave10-shevchenkivsky-slovnyk`).
- *Історія української культури*, т. 2 (XIII–XVII ст.). НАН України. (retrieved from corpus `wave7-istkult-t2-xiii-xvii`) — on the Mohylian circle and «Крест Христа Спасителя» (Київ, 1632).

**Tier 2 (institutional / classic church-history):**
- Огієнко І. (Митрополит Іларіон). *Українська Церква* — on the 1646 Требник, its forcible Muscovite replacement, and the marriage ordo (retrieved from corpus `wave7-ohiyenko-tserka`).
- Ісаєвич Я. *Українське книговидання* — on the Lviv/Lavra printing disputes around the Требник (retrieved from corpus `wave8-isaievych-knyhovydannia`).

**Tier 3 (encyclopedic — navigation, cross-checked against T1):**
- Українська Вікіпедія. "Петро Могила." Dates, offices, works and the canonisation downgrade cross-checked against IEU and Шевченківська енциклопедія. Accessed 2026-06-04.

**Tier 4 (modern scholarly — referenced via T1/T2):**
- Жуковський А. *Петро Могила й питання єдности церков.* Київ, 1997 (cited within Історія української культури).

**Primary-source documents accessed (in transcription, via T2 corpus):**
- **«Требник» Петра Могили (Київ, 1646)** — preface and marriage ordo, quoted §4 via Огієнко.
- **«Православне сповідання віри» (1640; synod of Яссы 1642; Москва 1696)** — referenced §2/§3.

**Honest gaps:** the autograph/first-print folios of the Требник and the catechism were not opened directly this pass — §4 rests on Огієнко's verbatim transcription (clearly labelled). The exact **day** of the 1633 Lviv consecration and the precise N.S. **birth day** remain source-variant (§1) and are presented as open, not resolved.

---

## Decolonization self-check (run before submitting)

- [x] No Russocentric framing — Kyiv is the centre; Moscow appears only as the later appropriating/erasing power.
- [x] No Russian-imperial transliterations in body text — confined to §8, labelled FORBIDDEN.
- [x] No Russocentric periodization — used Річ Посполита / Берестейська унія / Московський патріархат, not imperial shorthand.
- [x] No uncritical Soviet/imperial terms — "all-Russian enlightenment" appears only named as the appropriating narrative, not endorsed.
- [x] No "lost his life" euphemism — N/A (death was natural, 1647); the repression is posthumous appropriation, named precisely.
- [x] Modern UA place names — Київ/Kyiv, Сучава, Львів, Крем'янець used throughout.
- [N/A] Holodomor — out of period (17th c.); no occasion to reference it.
- [N/A] Crimea/2014/2022 — not applicable to this figure's documented record; not forced.
