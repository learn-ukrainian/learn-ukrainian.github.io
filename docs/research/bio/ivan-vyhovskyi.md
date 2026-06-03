# Іван Остапович Виговський — Research Dossier

**Slug:** `ivan-vyhovskyi`
**Block:** G (politically charged Cossack-statehood figure; "traitor" myth around Hadiach and anti-Moscow policy)
**Tier:** 1a
**Issue:** #2535 (original-180 ghost-wiki dossier uplift — Wave H)
**Researcher:** GPT-5.5 (Codex)
**Completed:** 2026-06-03

**Acceptance self-check:**
- [x] All 10 sections completed
- [x] ≥3 Tier 1/Tier 2 sources cited (IEU, NBUV, treaty text, Velychko corpus; ЕІУ used bibliographically because stable URL was not resolved)
- [x] Oppression/appropriation mechanism is specific (§2: Moscow war after Hadiach, relatives sent to Siberia, Polish execution in 1664, imperial/Soviet "traitor" framing)
- [x] §4 includes 3 primary/source excerpts; Velychko quote verified at confidence 1.0, treaty/signature excerpts returned 0.0 and are flagged
- [x] Korсун rada warning resolved: 21 October 1657, not conflated with the earlier Chyhyryn council
- [x] Cross-track links: every "Existing" path verified with `test -e` on 2026-06-03
- [x] Naming-canonical applied
- [x] Image candidate(s) identified
- [x] Decolonization checklist self-applied

---

## 1. Verified facts

- **Full name (UA, canonical):** Іван Остапович Виговський; fuller family form Іван Остапович Лучич-Виговський, гербу Абданк. [T1: IEU; T3: uk.wikipedia]
- **Pseudonyms / aliases:** Ivan Vyhovsky/Vyhovskyi; гетьман Великого князівства Руського (in Hadiach context). Forbidden body-text forms: Иван Выговский; "польський запроданець" as factual label.
- **Born:** ca. **1608**, probably in the Ovruch/Vyhiv family region; exact birthplace uncertain. [T1: IEU; T3]
- **Died:** **17/27 March 1664** | Вільховець near Korsun/Right Bank | executed by Polish authorities after arrest on accusations around an anti-Polish uprising. IEU gives 19 March 1664 near Korsun; Ukrainian Wikipedia gives 17/27 March. [T1: IEU; T3]
- **Family / education key facts:** Orthodox Ruthenian noble family; likely educated in Kyiv Brotherhood/Kyiv-Mohyla milieu; became general chancellor and the administrative-diplomatic engine of Bohdan Khmelnytskyy's government. [T1: IEU; T3; primary: Velychko quote in §4]

**Source disagreement / correction note:**

1. **Rada date warning:** the **Korsun rada = 21 October 1657**. Do not write **4 September** for Korsun; that conflates an earlier Chyhyryn council/regency stage. The dossier uses "Chyhyryn earlier; Korsun 21 October 1657."
2. **Death date:** present 17/27 March 1664 with IEU's 19 March variant noted if needed. The core fact is execution by Polish authorities, not death by Moscow.
3. **Hadiach:** signed in 1658; ratified/altered in 1659. Keep treaty, war, and battle dates distinct.

## 2. Oppression / appropriation mechanism

**What happened:** Vyhovskyi's anti-Moscow course after the Hadiach Treaty triggered war with Muscovy; after his political defeat and the collapse of the Hadiach project, Moscow repression reached his family, with many relatives reportedly sent to Siberia. He himself was later executed by Polish authorities in **1664** after being accused of involvement in a Right-Bank anti-Polish uprising. [T1: IEU; T3]

**By whom:** Muscovite/Russian state power in the war and family-repression layer; Polish Commonwealth authorities in the execution layer. The dossier must tell the truth in both directions.

**Document references:** **Гадяцький договір 1658** as a source of the anti-Moscow break; NBUV institutional page confirms the treaty's idea of a **Велике князівство Руське** as a third component; treaty text page resolves and includes the "three nations" and "гетьман військ Руських" clauses. [T2: NBUV; primary/T5-hosted treaty text]

**Mechanism specifics:** the Russian-imperial memory move is to brand Vyhovskyi as a "traitor" because he rejected Moscow's post-Pereiaslav trajectory. The historical record is more complex: he pursued a Commonwealth federation project that also alienated many Cossacks and fed civil war. His **Konotop victory in 1659** over Muscovy was militarily significant, but it did not solve internal legitimacy. [T1: IEU; T2: NBUV; T3]

**What survived / what was distorted:** Hadiach and Konotop survived as powerful counter-memory to Russian inevitability; Soviet/Russian frames distorted him as a Polish puppet. Ukrainian hagiography can also distort him by ignoring Pushkar/Barabash, internal violence, and the treaty's limited realization.

## 3. Major works / legacy

- `1650-1657` — **General chancellor / military chancellery leadership**, building the diplomatic-administrative machinery of the Cossack state. [T1: IEU; T3]
- `1657` — **Chyhyryn regency/election stage**, followed by **Korsun rada on 21 October 1657** confirming hetmancy. [T3; audit correction]
- `1658` — **Suppression of Pushkar-Barabash revolt**, a bloody internal crisis that weakened his legitimacy. [T1: IEU; T3]
- `16 September 1658` — **Hadiach Treaty**, projecting the Grand Duchy of Rus' as a third component of the Commonwealth. [T1: IEU; T2: NBUV; treaty text]
- `1658-1659` — **Cossack-Muscovite war** after Hadiach. [T1: IEU; T3]
- `29 June (O.S.) = 9 July (N.S.) 1659` — **Konotop victory** over Muscovite forces with Crimean/Polish support (the decisive Sosnivka cavalry battle; the engagement spans 28–29 June O.S.); a tactical triumph without durable political settlement. [T3: uk.wikipedia — «9 липня 1659»; T1: IEU] **[Source/calendar note, flagged not smoothed: uk.wikipedia dates the decisive day 29.06 O.S. = 9.07 N.S.; an "8 July" form counts from 28.06 O.S.]**
- `September 1659` — resignation/flight after loss of support; Yurii Khmelnytskyy rises. [T1: IEU]
- `1664` — execution by Polish authorities; a tragic end by the side he had tried to use as counterweight to Moscow. [T1: IEU; T3]

## 4. Primary-source quotes (≥2 required)

**Quote 1 — Velychko on Vyhovskyi's education and chancery competence:**

> "вивчений вільним наукам"

Context: this supports the lesson's focus on Vyhovskyi as chancellor/diplomat, not merely military rival. `verify_quote(author="Величко")` returned **matched: true, best_confidence: 1.0**, works `wave12-velychko-litopys` and `wave2-velychko`.

**Quote 2 — Hadiach treaty political formula:**

> "ці три народи мають зіставатися"

Context: the treaty's federation logic matters more than a slogan about "returning to Poland." `verify_quote(author="Гадяцький договір")` returned **matched: false, best_confidence: 0.0, matched_lines: []** because the treaty text is outside the quote corpus.

**Quote 3 — treaty signature formula:**

> "Іван Виговський ... рукою власною"

Context: use this only as document-signature evidence from the resolved treaty text page. `verify_quote(author="Виговський")` returned **matched: false, best_confidence: 0.0, matched_lines: []**.

## 5. Language register

- **Register:** diplomatic, chancery, and treaty language; politically abstract terms need scaffolding.
- **CEFR readiness for full reading:** B2-C1 for adapted biography; C1-C2 for Hadiach treaty excerpts and Velychko.
- **Lexicon notes:** `генеральний писар`, `булава`, `Гадяцький договір`, `Велике князівство Руське`, `легітимність`, `Руїна`, `Конотопська битва`, `федерація`. VESUM batch verified `писар`, `булава`, `легітимність`, `князівство`; `search_text` aligned early-modern autonomy/institution vocabulary with textbook pedagogy.
- **Stylistic features:** dense legal-political syntax; useful for teaching modal verbs of political possibility ("мало бути", "передбачалося", "не відбулося").

## 6. Contested points

- **Hero or "traitor"?** Russian/Soviet framing treats the Hadiach turn as betrayal of Moscow. A decolonized reading starts from a different premise: Moscow was one possible alliance, not Ukraine's natural owner. But the lesson must still show why many Cossacks feared renewed Polish influence.
- **Hadiach as brilliant project or fatal mistake?** It imagined a Grand Duchy of Rus' and a three-part Commonwealth, but implementation was weakened by Polish ratification changes, internal opposition, and war. Teach both the idea and the failure.
- **Konotop:** a major victory over Muscovy in 1659. Do not let it become a meme detached from the fact that Vyhovskyi lost political support soon after.
- **Internal violence:** Pushkar-Barabash and anti-Hadiach opposition cannot be reduced to Russian manipulation only. Social, regional, and confessional fears mattered.
- **Execution by Poland:** tell the truth in every direction. Vyhovskyi fought Moscow, allied with Poland, and was later executed by Polish authorities. This is not a simple martyrdom script.
- **Modern disinformation:** "Polish puppet" remains an easy attack line. The corrective is not "perfect European hero," but "Cossack statesman attempting a risky alternative sovereignty model."

## 7. Cross-track links

> Every path under **Existing** below was verified with `test -e` on 2026-06-03.

- **Existing BIO plans (VERIFIED present):**
  - `curriculum/l2-uk-en/plans/bio/ivan-vyhovskyi.yaml`
  - `curriculum/l2-uk-en/plans/bio/bohdan-khmelnytskyy.yaml`
  - `curriculum/l2-uk-en/plans/bio/ivan-sirko.yaml`
  - `curriculum/l2-uk-en/plans/bio/yuriy-nemyrych.yaml`
- **Existing HIST modules (VERIFIED present):**
  - `curriculum/l2-uk-en/plans/hist/ruina-i.yaml`
  - `curriculum/l2-uk-en/plans/hist/ruina-ii.yaml`
  - `curriculum/l2-uk-en/plans/hist/andrusivske-peremyrya.yaml`
  - `curriculum/l2-uk-en/plans/hist/kozatska-derzhava.yaml`
- **Candidate cross-track connections (Phase 2+, NOT existing files):**
  - `hadiatskyi-dohovir-1658` — treaty source-reading module.
  - `konotopska-bytva-1659` — military victory and political failure case study.
- **Potential LIT additions surfaced by this research:**
  - A LIT/source module could compare Ivan Nechui-Levytskyi's historical novel imagery with scholarship, but no existing plan is asserted.

## 8. Naming-canonical

- **Slug:** `ivan-vyhovskyi`
- **EN canonical (BGN/PCGN-style project spelling):** Ivan Vyhovskyi
- **UA canonical (with patronymic):** Іван Остапович Виговський
- **Aliases (track these for `aliases:` YAML field):** Іван Виговський; Іван Остапович Лучич-Виговський; Ivan Vyhovsky; Ivan Vyhovskyi.
- **Forbidden forms (Russian-imperial transliterations to flag in body text):** Иван Выговский; польский ставленник/запроданец as factual label.

## 9. Image candidates

- **Best PD/CC portrait:** Wikimedia Commons category for Ivan Vyhovskyi; verify individual file license before selecting.
- **Backup candidates:** Hadiach treaty context/facsimile if rights-clear; Konotop battlefield/memorial context image; Vyhovskyi museum/memorial image if CC/PD.
- **If no PD/CC portrait exists:** use a treaty/Konotop context image with a clear caption.
- **Era-appropriate context image:** Hadiach treaty or Konotop battle context, not generic Cossack stock art.

## 10. Sources used

**Tier 1 (authoritative):**
- [T1] "Vyhovsky, Ivan" // Internet Encyclopedia of Ukraine. URL: https://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CV%5CY%5CVyhovskyIvan.htm | resolved HTTP 200, accessed 2026-06-03.
- [T1] Степанков В. С. "Виговський Іван Остапович" // Енциклопедія історії України, т. 1, pp. 502-503 (bibliographic use; stable URL not resolved in this pass, so no URL cited).
- [T1] Самійло Величко, *Літопис* corpus line verified by `verify_quote`.

**Tier 2 (institutional):**
- [T2] НБУВ, "Укладено Гадяцький договір між Україною та Річчю Посполитою." URL: https://nbuv.gov.ua/node/4283 | resolved HTTP 200, accessed 2026-06-03.

**Tier 3 (encyclopedic):**
- [T3] "Іван Виговський" // Ukrainian Wikipedia via `query_wikipedia`, URL resolved HTTP 200, accessed 2026-06-03.

**Tier 4 (modern scholarly post-1991):**
- [T4] Мицик Ю. *Іван Виговський* / *Володарі гетьманської булави*.
- [T4] Яковлева Т. *Гетьманщина в другій половині 50-х років XVII століття*.
- [T4] Сокирко О. *Конотопська битва 1659 р. Тріумф в час Руїни*.

**Tier 5 (general web):**
- [T5/primary-text host] Prostopravo text of the Hadiach Treaty. URL: https://prostopravo.com.ua/klub_yuristov/zakonodatelstvo/istoriko_pravovye_dokumenty/gadyachskiy_traktat_dogovor_06_09_1658 | resolved HTTP 200, accessed 2026-06-03. Used only for text excerpts, corroborated by NBUV/IEU.

**Primary-source documents accessed / verification notes:**
- Velychko excerpt: `verify_quote(author="Величко")` matched true, confidence 1.0.
- Hadiach treaty excerpt and Vyhovskyi signature formula: `verify_quote` returned 0.0.

---

## Decolonization self-check

- [x] No Russocentric framing; Moscow is one power in a multi-state field, not the natural center.
- [x] No Russian-imperial transliterations in body text except forbidden forms in §8.
- [x] Corsun/Korsun rada date corrected to 21 October 1657 and not conflated with Chyhyryn.
- [x] Execution by Poland is stated clearly; anti-imperial reading does not hide inconvenient facts.
- [x] Hadiach and Konotop are separated by event type and date.
