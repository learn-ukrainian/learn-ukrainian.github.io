# Іван Дмитрович Сірко — Research Dossier

**Slug:** `ivan-sirko`
**Block:** G (politically charged Cossack/Sich figure; Russian-imperial memory often folds him into loyal anti-Ottoman frontier myth)
**Tier:** 1a
**Issue:** #2535 (original-180 ghost-wiki dossier uplift — Wave H)
**Researcher:** GPT-5.5 (Codex)
**Completed:** 2026-06-03

**Acceptance self-check:**
- [x] All 10 sections completed
- [x] ≥3 Tier 1/Tier 2 sources cited (ЕІУ, IEU, Velychko corpus via `verify_quote`; Wikipedia as T3)
- [x] Oppression/appropriation mechanism is specific (§2: 1672 Moscow exile to Tobolsk, later Repin/Sultan-letter appropriation)
- [x] §4 includes 2 primary/near-primary excerpts; one Velychko quote verified at confidence 1.0, one Sirko-letter excerpt returned 0.0 and is flagged
- [x] The koshovyi-otaman count warning is resolved with explicit source disagreement
- [x] Cross-track links: every "Existing" path verified with `test -e` on 2026-06-03
- [x] Naming-canonical applied
- [x] Image candidate(s) identified
- [x] Decolonization checklist self-applied

---

## 1. Verified facts

- **Full name (UA, canonical):** Іван Дмитрович Сірко. [T1: ЕІУ — Горобець; T1: IEU]
- **Pseudonyms / aliases:** "Урус-Шайтан" in hostile Ottoman/Crimean legend; "характерник" in folklore; forbidden body-text forms: Иван Сирко, кошевой атаман as a normalized Russian label.
- **Born:** approximately **1605-1610** by Ukrainian Wikipedia's age-at-death discussion; ЕІУ gives "бл. 1618"; IEU gives ca. 1605-10 in Merefа. Birthplace remains disputed. [T1: ЕІУ; T1: IEU; T3: uk.wikipedia]
- **Died:** **1 August 1680 O.S. / 11 August 1680 N.S.** | Грушівка / near Chortomlyk Sich, now Dnipropetrovsk oblast region; buried near Chortomlyk Sich/Kapulivka. [T1: IEU; T3: uk.wikipedia; primary: Velychko quote in §4]
- **Family / education key facts:** probable Podilian or Sloboda Ukrainian шляхтич/Cossack background; served as Vinnytsia/Kalnyk colonel in 1658-1660; repeatedly elected кошовий отаман of the Zaporozhian Host. [T1: ЕІУ; T1: IEU; T3: uk.wikipedia]

**Source disagreement note (flagged, not smoothed):**

1. **Birthplace:** the Merefа tradition is old and appears in IEU, but modern Ukrainian discussion (Mytsyk/Borysenko/Masliychuk as summarized in uk.wikipedia) questions it and argues for East Podillia, possibly Мурафа near Kalnyk. Write "birthplace disputed," not a single confident location.
2. **Election count:** IEU says he was elected Kish otaman **eight** times in the 1660s-1670s. Ukrainian Wikipedia states: **"У 1660-1680 роках дванадцять разів його обирали кошовим отаманом."** For this Wave H warning, use **12 times** with the disagreement note, not vague "many times." [T1: IEU; T3: uk.wikipedia]
3. **Letter to the Ottoman Sultan:** present the famous reply as legend/tradition of contested authenticity, not as documented correspondence by Sirko. [T1: IEU; T3: uk.wikipedia]

## 2. Oppression / appropriation mechanism

**What happened:** in **1672**, Moscow authorities and Left-Bank political rivals had Sirko arrested/exiled to **Tobolsk**. He returned in **1673** because his military usefulness outweighed the earlier accusation. [T1: ЕІУ; T3: uk.wikipedia]

**By whom:** the Moscow tsarist government of **Alexei Mikhailovich**, in cooperation with Left-Bank starshyna politics around Ivan Samoilovych. [T1: ЕІУ; T3: uk.wikipedia]

**Mechanism specifics:** Sirko's career exposes the limits of imperial loyalty narratives. He could fight Ottomans and Crimean Tatars, cooperate tactically with Moscow, and still take anti-Muscovite positions after Andrusovo. The 1672 exile shows Moscow treating the Sich leader as controllable frontier manpower, not as a sovereign Ukrainian actor. ЕІУ states he was seized by Left-Bank starshyna and exiled to Tobolsk by order of the Russian tsar; he was restored after pressure and need. [T1: ЕІУ]

**Appropriation layer:** later memory centered the Repin painting and the famous Sultan-letter scene, making Sirko a laughing anti-Turkish hero in a broad "Russian" imperial art frame. That image is powerful but pedagogically dangerous if it replaces documented politics: his alliances shifted, and the Sultan letter's authenticity is contested. [T1: IEU; T3: uk.wikipedia]

**What survived / what was distorted:** Velychko's chronicle preserves his death memory; letters are known through Velychko/Rigelman/Markevych traditions. Distortion comes from flattening him into a folklore character or Muscovite frontier loyalist.

## 3. Major works / legacy

Sirko left no literary corpus; "works" means campaigns, offices, and preserved letters.

- `1653` — participation in the Zhvanets context of the Cossack-Polish war. [T3: uk.wikipedia]
- `1658-1660` — Vinnytsia/Kalnyk colonel, linking him to Right-Bank/Podilian politics. [T1: IEU; T3]
- `1660-1680` — **twelve elections as кошовий отаман** according to Ukrainian Wikipedia; older IEU says eight. [T3; T1]
- `1667-1668` — anti-Muscovite turn after Andrusovo; frontier politics become explicitly anti-partition. [T3]
- `1672-1673` — arrest/exile to Tobolsk and return from Moscow captivity. [T1: ЕІУ; T3]
- `1675` — major anti-Ottoman/Crimean campaign around Chyhyryn context. [T3]
- `1678` — actions against Ottoman supply lines during the Chyhyryn campaign; preserved letter excerpt in §4. [T3]
- `1679` — tradition connects him with the Sultan-letter legend; teach as contested memory, not fact. [T1: IEU; T3]

## 4. Primary-source quotes (≥2 required)

**Quote 1 — Sirko's letter to Ivan Samoilovych on the 1678 action:**

> "липня 12 числа ... оволоділи єсми ними"

Context: a rare first-person military report, useful for showing real correspondence rather than folklore. `verify_quote(author="Сірко")` returned **matched: false, best_confidence: 0.0, matched_lines: []**. Use only with source-context citation; do not claim corpus verification.

**Quote 2 — Velychko on Sirko's death:**

> "славний кошовий отаман Іван Сірко"

Context: Velychko's chronicle anchors the death date and posthumous reputation. `verify_quote(author="Величко")` returned **matched: true, best_confidence: 1.0**, work `wave12-velychko-litopys`, year 1720.

## 5. Language register

- **Register:** mixed Cossack military correspondence, chronicle prose, and folklore. Primary documents are C1-C2; modern lesson narration can be B2-C1.
- **CEFR readiness for full reading:** B2 for adapted biography; C1-C2 for Velychko or early-modern letters.
- **Lexicon notes:** `кошовий`, `отаман`, `Січ`, `ясир`, `невільник`, `булава`, `чамбули`, `рейдова війна`, `характерник`. VESUM batch verification found `кошовий`, `отаман`, `ясир`, `булава`; `search_heritage("паланка")` and `search_heritage("зимівник")` confirm authentic Ukrainian historical vocabulary.
- **Stylistic features:** contrast laconic military reports with heavily mythologized folk/Romantic representation.

## 6. Contested points

- **Count of elections:** the lesson must not hedge into "10+" or "many." State the warning explicitly: Ukrainian Wikipedia gives **12** elections in 1660-1680; IEU's older entry gives **eight**. The dossier uses **12** for the wiki-rebuild fact while teaching the discrepancy as source history.
- **Birthplace:** Merefа is a living local tradition, but the Podilian/Murafa argument has serious scholarly support. Avoid turning local commemoration into verified birthplace.
- **"Undefeated in 65 battles":** popular memory repeats impressive numbers; they should be introduced as traditional/reputational claims unless a specific campaign list is sourced.
- **The Sultan letter:** the famous obscene reply belongs in §6 as contested legend and memory-artifact, especially because Repin's painting shaped public imagination. Do not use it as proof of Sirko's diplomatic voice.
- **Violence and anti-hagiography:** Sirko's raids against Crimean/Tatar/Ottoman targets included brutal frontier warfare. Teaching him only as rescuer of captives erases the human cost and the volatile politics of the Ruin.
- **Russian disinformation / appropriation:** the easy imperial move is to make Sirko "anti-Turkish, therefore pro-Russian." His anti-Muscovite moments after Andrusovo and his Tobolsk exile disprove that flattening.

## 7. Cross-track links

> Every path under **Existing** below was verified with `test -e` on 2026-06-03.

- **Existing BIO plans (VERIFIED present):**
  - `curriculum/l2-uk-en/plans/bio/ivan-sirko.yaml`
  - `curriculum/l2-uk-en/plans/bio/ivan-vyhovskyi.yaml`
  - `curriculum/l2-uk-en/plans/bio/dmytro-yavornytskyi.yaml`
  - `curriculum/l2-uk-en/plans/bio/petro-kalnyshevskyy.yaml`
- **Existing HIST modules (VERIFIED present):**
  - `curriculum/l2-uk-en/plans/hist/ivan-sirko.yaml`
  - `curriculum/l2-uk-en/plans/hist/andrusivske-peremyrya.yaml`
  - `curriculum/l2-uk-en/plans/hist/zaporizka-sich.yaml`
- **Candidate cross-track connections (Phase 2+, NOT existing files):**
  - `letter-to-sultan-legend` — source criticism, Repin, and memory.
  - `chortomlyk-sich` — Sich leadership and the Ruin.
- **Potential LIT additions surfaced by this research:**
  - A folklore/source-criticism activity comparing Velychko, dumas, and Repin-derived popular memory.

## 8. Naming-canonical

- **Slug:** `ivan-sirko`
- **EN canonical (BGN/PCGN-style project spelling):** Ivan Sirko
- **UA canonical (with patronymic):** Іван Дмитрович Сірко
- **Aliases (track these for `aliases:` YAML field):** Іван Сірко; Урус-Шайтан; Ivan Sirko.
- **Forbidden forms (Russian-imperial transliterations to flag in body text):** Иван Сирко; кошевой атаман as the default label.

## 9. Image candidates

- **Best PD/CC portrait:** Wikimedia Commons category for Ivan Sirko portraits; check individual file license before selecting.
- **Backup candidates:** Repin's "Reply of the Zaporozhian Cossacks" as context image only, with authenticity caveat; Chortomlyk/Kapulivka grave context image if license permits.
- **If no PD/CC portrait exists:** use a CC/PD grave/context image and label it as memory site.
- **Era-appropriate context image:** Chortomlyk Sich / Zaporozhian Sich context, not a literal Sultan-letter illustration unless the legend caveat is visible.

## 10. Sources used

**Tier 1 (authoritative):**
- [T1] Горобець В. М. "Сірко Іван" // Енциклопедія історії України. URL: https://www.history.org.ua/?termin=Sirko_I | resolved HTTP 200, accessed 2026-06-03.
- [T1] "Sirko, Ivan" // Internet Encyclopedia of Ukraine. URL: https://www.encyclopediaofukraine.com/display.asp?linkpath=pages%5CS%5CI%5CSirkoIvan.htm | resolved HTTP 200, accessed 2026-06-03.
- [T1] Самійло Величко, *Літопис* corpus line verified by `verify_quote`.

**Tier 2 (institutional):**
- None used as load-bearing evidence.

**Tier 3 (encyclopedic):**
- [T3] "Іван Сірко" // Ukrainian Wikipedia via `query_wikipedia`, URL resolved HTTP 200, accessed 2026-06-03.

**Tier 4 (modern scholarly post-1991):**
- [T4] Мицик Ю. *Отаман Іван Сірко*. Запоріжжя, 2000.
- [T4] Маслійчук В. *Altera patria: Нотатки про діяльність Івана Сірка на Слобідській Україні*. Харків, 2004.

**Tier 5 (general web):**
- None used as load-bearing evidence.

**Primary-source documents accessed / verification notes:**
- Sirko letter excerpt in the Chyhyryn campaign narrative: `verify_quote` returned 0.0.
- Velychko death excerpt: `verify_quote` returned matched true, confidence 1.0.

---

## Decolonization self-check

- [x] No Russocentric framing; Moscow is a political actor, not default arbiter.
- [x] No Russian-imperial transliterations in body text except forbidden forms in §8.
- [x] The Sultan letter is treated as contested tradition, not fact.
- [x] Sirko's violence and shifting alliances are included; no saint/character-magic flattening.
- [x] Ukrainian place names and Cossack institutions are canonical.
