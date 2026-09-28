# Word cards C0 — identity contract (#8334, draft for review)

- **Decides (once approved):** what an Atlas entry *is*. A card is a lexeme, an MWE or a proper name, never a spelling. Spelling, stress, POS and source homonym numbers are attributes and matching evidence.
- **Companion docs:** [`schema.md`](schema.md) (card and assertion shape, states), [`worked-examples.md`](worked-examples.md), [`migration.md`](migration.md).
- **Status:** draft 2026-09-28, author Claude (Fable 5.1). Needs the #8334 stop-policy reads: an advisor design read (Astra) and a language-lane read (Gemini via AGY) on the linguistic model, then operator sign-off. No stress or meaning judgment below is the author's: every Ukrainian form is quoted from `data/sources.db`, `data/vesum.db` or `data/atlas.db` (read-only, 2026-09-28; §12).
- **Not in this doc:** the URL scheme (#8334 AC-02, open question) and the consumer inventory (in `migration.md` §6).

## 1. Operational definitions

| term | operational definition | key components (attributes, not identity) |
| --- | --- | --- |
| **lexeme** | one word = one paradigm (a VESUM `entry_id` or a ULIF paradigm table) + one stress pattern or one declared doublet set + one coarse POS + one sense family as divided by the homonym numbering of a tier-1 dictionary. Two rows that differ in any of paradigm, stress pattern or dictionary homonym division are two lexemes unless a source states they are the same word. | spelling (NFC, no accents), `stress_patterns`, `pos`, `paradigm_key`, namespaced `source_keys` |
| **sense** | one meaning unit under a lexeme, fed by one or more source sense units (`sense_map`); relations, definitions and examples target senses | order, `sense_map` |
| **multiword expression (MWE)** | a fixed expression with its own citation in a phraseological source (ULIF phraseology section, `frazeolohichnyi` row) or an admitted multiword article, keyed by `<first locator>|<normalised form>`, linked to its component lexemes with roles | normalised form, slots, components |
| **proper name** | a capitalised headword marked `:prop` in VESUM or capitalised in ULIF (`За́мок`, `Коса́`); its own card kind, never merged with the homographic common noun | as lexeme |

Attributes can change without changing the id: a 2019-orthography respelling, a corrected stress, a re-numbered homonym in a new ULIF harvest. Identity changes only by **split**, **merge** or **redirect** (§7).

## 2. Sources of identity evidence (measured)

### 2.1 VESUM (`data/vesum.db`, `vesum-reingest-v1`, canonical sha `53923150…`)
- 442,458 entries (`entry_id`), 422,656 distinct lemmas, 423,661 distinct (lemma, pos). 18,935 lemmas have more than one entry; 18,037 (lemma, pos) pairs do. Entries are the paradigm authority: `forms_all(entry_id, word_form, lemma, pos, tags, source_comment, source_location)`; `word_form` never carries a stress mark (0 rows with U+0301).
- Homonyms are told apart by the paradigm and by `:xp<n>` tags (1,528 entries) and by `source_comment`, which sometimes carries stress (1,090 entries) and, for 68 entries, a declared stress doublet (`xv2 броня́; бро́ня`, `а́дресний; адре́сний`, `xv2 а́тлас; атла́с`).
- `замок`: entry 128972 `noun:inanim:m:v_naz:xp1`, comment `замо́к (пристрій)`, genitive `замка`; entry 128973 `…:xp2`, comment `за́мок (будівля)`, genitive `замку`; entry 128971 `Замок` `noun:inanim:m:v_naz:prop:geo`.
- Aspect is a tag per lemma (`verb:imperf:inf`, `verb:perf:inf`); VESUM does not state which two lemmas form a pair.

### 2.2 ULIF «Словники України» (`data/sources.db`, `ulif_dictua_*`, parser `ulif-dictua-v2`)
- 262,788 checked entries (`homonym_checked=1`, all `status='ok'`), 250,712 distinct `normalized_query`, 10,570 spellings with more than one homonym. Per `homonym_index`: 1 → 250,712; 2 → 10,570; 3 → 1,252; 4 → 200; 5 → 38; 6 → 7; 7 → 3; 8 → 2; 9 → 2; 10 → 1; 11 → 1. The 6,449 legacy rows (`homonym_checked=0`) are never used.
- Per entry: `canonical_headword` with stress (`за́мок`, `по́ми́лка` with two marks for a doublet; 7,157 headwords carry ≥2 marks, 2,828 of them single tokens — mostly foreign place names such as `Ба́лтімо́р`, so a doublet is a *candidate* until a paradigm or a second source confirms it), `grammatical_label` (`іменник чоловічого роду`, `дієслово недоконаного виду`, `дієслово недоконаного і доконаного виду` for 1,260 biaspectual verbs, `прізвище`, `власна назва`, …), `sense_gloss` (non-empty for 51,182 entries; a parenthesised list, `;`-separated for polysemy: `ключ` homonym 1 lists six senses), `register_position` (`page:row`, e.g. `2795:9`), `content_sha256`, `raw_response_ref`.
- Sections (336,369): `paradigm` 250,183 (`rows` = the case table; verb tables start with an `Інфінітив` row, 49,953 sections), `synonyms` 75,952 (sense-bound groups with `terms`, `register_labels`, `citations`), `phraseology` 8,131, `antonyms` 2,103 (`paired_sense` rows). Anchors in the HTML carry ULIF's own entry ids (`dictua.aspx?uid=47336` = `ЗА́МОК` castle, `uid=47335` = `ЗАМО́К` lock), which are not stored as a column today (Q-I6).
- Header damage: 12,899 checked rows have `canonical_headword=''`; 12,095 of those have a paradigm whose first data row gives the stressed lemma (`замо́к`, `броня́`, `варе́ння`), 27 have nothing. Recovered headwords carry `extraction_confidence = medium`.
- A ULIF homonym row is **not** automatically a lexeme: `визволення` has homonym 1 (header empty, paradigm `ви́зволення`) and homonym 2 `визво́лення` glossed `(те ж саме, що ви́зволення)` — the source itself says one word, two stresses. This is the only such gloss among checked rows, so it is handled by a rule plus overlay, not by a heuristic.
- 815 checked queries contain a space (multiword headwords).

### 2.3 Other sources
- **ВТС** (inside today's `enrichment.definition_cards`): Roman-numbered homonyms with the stress mark written after the vowel: `I з`амок` (castle), `II зам`ок` (lock); `I в`ибігати … док.` / `II вибіг`ати … недок., в и бігти … док.`
- **СУМ-20** (`sum20_articles`, 100 rows): one `wordid` per homonym with `stressed_headword` (`ПО́КІЙ` wordid 82852, `ПОКІ́Й` 82853).
- **kaikki/Wiktionary, ukrainian-word-stress**: spelling-keyed stress (Atlas `enrichment.stress`: 18,448 + 695 rows); one form per spelling, so a homograph pair gets one of its stresses only (`замок` → `за́мок`).
- **PULS**: spelling-keyed CEFR (`замок` A2, `ключ` A2, `помилка` A2, `писати` A1, `написати` A1).
- **atlas0** (`articles.slug`): one article per spelling; 2,811 lemma articles have a spelling with more than one checked ULIF homonym; 877 have no checked ULIF entry at all.
- **Curated heteronyms** (`site/src/lib/lexicon/curated-heteronyms.ts`, 420 lemmas, hand-curated): `замок` → `за́мок` "castle, fortress, palace" and `замо́к` "lock (door lock, padlock)". These become `atlas0:heteronym:<spelling>/<stressed>` source keys and overlay `split` entries (`migration.md` M6).

## 3. Namespaced source homonym numbers

Homonym numbers are keys inside one source. They are never compared across sources and never used as identity. Measured for `замок`:

| source | key | what it denotes | evidence |
| --- | --- | --- | --- |
| VESUM | `vesum:entry:128972` (`xp1`) | lock | comment `замо́к (пристрій)`, genitive `замка` |
| VESUM | `vesum:entry:128973` (`xp2`) | castle | comment `за́мок (будівля)`, genitive `замку` |
| VESUM | `vesum:entry:128971` | settlement | `:prop:geo`, lemma `Замок` |
| ULIF | `ulif:entry:76791` (homonym 1) | settlement | `За́мок`, `(населений пункт в Україні)` |
| ULIF | `ulif:entry:76792` (homonym 2) | castle | `за́мок`, `(будівля)`, `родовий за́мку` |
| ULIF | `ulif:entry:76793` (homonym 3) | lock | header empty; paradigm `замо́к`, `родовий замка́` |
| ВТС | `vts:замок#I` | castle | `I з`амок-мка, ч. 1》 Укріплене житло феодала …` |
| ВТС | `vts:замок#II` | lock | `II зам`ок-мка, ч.` |

Three sources, three numberings, no two alike. The same holds for `вибігати`: VESUM `xp1` = `вибіга́ти` imperfective, `xp2` = `ви́бігати` perfective; ULIF homonym 1 = `ви́бігати` perfective, homonym 2 = `вибіга́ти` imperfective. A card records each source's key verbatim in `identity.source_keys`.

## 4. Matching VESUM ↔ ULIF: by stress and paradigm, never spelling alone

Inputs per candidate: VESUM entry (lemma, pos, tags, stripped form set, comment stress if any); ULIF checked entry (normalized_query, headword stress from `canonical_headword` or, if empty, from `paradigm.rows`, grammatical label, paradigm rows with accents stripped).

1. **Candidate set** = VESUM entries with `lemma = normalized_query` (case-sensitive: `Замок` ≠ `замок`) × ULIF checked entries with that `normalized_query`, filtered by **POS compatibility** (`noun` ↔ `іменник…`/`множинний іменник`/`прізвище`/`власна назва`; `verb` ↔ `дієслово …`; `adj` ↔ `прикметник…`/`дієприкметник`; `adv` ↔ `прислівник`; `advp` ↔ `дієприслівник`; proper names only with proper names).
2. **Paradigm signature**: the set of (case/number/person, stripped form) from ULIF rows compared with VESUM's form set for the same slots. `equal`, `subset` (ULIF gives fewer slots), `differs` (any slot with a different form: `замка` vs `замку`).
3. **Stress**: compare the ULIF stressed lemma with VESUM's comment stress when present (`за́мок (будівля)`); when VESUM has no stress (most entries: only 1,090 comments carry one), stress can only separate ULIF candidates from each other.
4. **Aspect** for verbs: VESUM `perf`/`imperf` must equal ULIF `доконаного`/`недоконаного`; biaspectual (`недоконаного і доконаного`) matches either.
5. **Decision** (`identity.method`, `identity.confidence`):

| situation | result |
| --- | --- |
| exactly one VESUM entry and one ULIF entry, paradigm `equal`/`subset`, stress agrees or VESUM has none | `unique_match`, **high** (`помилка`, `вряди-годи`, `вибігти`) |
| several on a side, and stress + paradigm pick exactly one partner for each | `stress_and_paradigm`, **high** (`замок` castle/lock, `вибігати`) |
| several on a side, paradigm alone separates them | `paradigm_only`, **high** |
| several on a side, stress alone separates them (paradigm identical or missing) | `stress_only`, **medium** (`броня`, `варення`) |
| several ULIF homonyms with identical stress and paradigm, one VESUM entry | dictionary-division split: one card per ULIF homonym, VESUM entry mapped to all, **medium** (`ключ`, `коса́` homonyms 4–6) — pending Q-I1 |
| unique VESUM entry, ULIF header empty and no paradigm (27 rows), or POS incompatible, or paradigm `differs` with no second candidate | VESUM card at **high** on its own; ULIF row held as `unresolved` (§6) |
| overlay `identity` entry | `overlay`, confidence as stated by the lane |

Spelling equality is a precondition of step 1, never sufficient by itself.

## 5. The cases, with measured examples

**A. Two words (homographs): `замок`.** VESUM 128972/128973 differ in genitive (`замка`/`замку`) and stress; ULIF 76793/76792 differ the same way (`замка́`/`за́мку`). Two lexeme cards (`high`), plus a proper-name card for `Замок`/`За́мок`. Today's single article (`gloss castle / lock`, stress `за́мок`, Караванський synonyms `фортеця, бастіон, цитадель, шато`) is split; the curated side file already says so.

**B. One word, two stresses (doublet): `помилка`.** ULIF headword `по́ми́лка` (one homonym) with the whole paradigm double-marked (`по́ми́лки`, `по́ми́лці`, plural `помилки́`); VESUM one entry 296174; Atlas `ukrainian-word-stress` also `по́ми́лка`. One card, `stress` state **`variant`**, both stresses correct, never split (#8334 stop policy).

**C. Proper name vs common noun: `Замок`/`замок`, `Коса́`/`коса́`.** VESUM `:prop:geo` entries and ULIF capitalised headwords (`Коса́` `(населений пункт в Україні)`, `Коса́` `(річка в Росії)`) are `proper_name` cards. Practice never uses them; pages link them as `homograph_of`.

**D. Dictionary homonymy with an identical paradigm: `ключ`.** VESUM has one entry (168409, comment `xv2`); ULIF has homonym 1 `ключ` (six senses: `знаряддя; засіб для розуміння; найважливіший пункт; вимикач у телеграфному апараті; знак на початку нотного рядка; ряд однорідних предметів …`) and homonym 2 `ключ` `(джерело)` with a byte-identical paradigm section (2,184 characters each); ВТС also numbers `I`/`II`. Proposed rule: follow the dictionaries' homonym division → two cards at **medium**, the VESUM entry mapped to both. Whether `medium` cards may feed meaning practice is Q-I1/Q7.

**E. An apparent stress conflict that is homonymy: `варення`.** Atlas (kaikki) `варе́ння`; ULIF homonym 1 `ва́рення` `(дія)` and homonym 2 (header empty) with paradigm `варе́ння`; VESUM one entry (35022, `xv2`); PULS B1. Spelling-keyed comparison reports a conflict; the contract yields two cards (`stress_only`, medium) and no conflict at all. Same pattern: `бере` (ULIF noun `бе́ре` vs kaikki verb form `бере́`), `всього` (ULIF adverb `всього́` vs `всьо́го`), `виносити` (ULIF 1 `ви́носити` perfective; VESUM `xp1 вино́сити` imperfective / `xp2 ви́носити` perfective).

**F. Sources disagree on identity: `броня`.** VESUM one lemma, comment `xv2 броня́; бро́ня` (a doublet on one word); ULIF two homonyms with different senses and stresses: 1 `бро́ня` `(закріплення; документ про закріплення)`, 2 (header empty) paradigm `броня́`; Wiktionary lists both meaning families under one spelling; kaikki stress `броня́`. Proposed rule: when the finer source gives distinct senses **and** distinct stress, follow the finer division (two cards, **medium**); the coarser source's doublet assertion is retained on both cards at `mapping.confidence = low` and does not vote. A language-lane read can raise this to `high` via an overlay `identity` entry.

**G. Two ULIF rows, one word: `визволення`.** Homonym 2 is glossed `(те ж саме, що ви́зволення)`; ULIF itself equates the rows. Rule: a `те ж саме, що` gloss (or an overlay `variant`) collapses the rows into one card with `stress` **`variant`** (`ви́зволення` / `визво́лення`).

**H. Aspect homonyms and aspect pairs: `вибігати`, `вибігти`.** VESUM `40937 verb:imperf:inf` (`:xp1 вибіга́ти`) and `40938 verb:perf:inf` (`:xp2 ви́бігати`); ULIF 34096 `ви́бігати` perfective and 34097 `вибіга́ти` imperfective; matched by stress + aspect (numbers are opposite). `вибігти` (VESUM 40942, ULIF 34099 `ви́бігти`) is a third card. The pair `вибіга́ти ↔ ви́бігти` is a typed `aspect_pair` link whose evidence is the ВТС header `II вибіг`ати … недок., в и бігти … док.`; 292 ULIF spellings have both a perfective and an imperfective checked homonym. Aspect pairs are always two cards plus one link, never one card with two aspects; biaspectual verbs (1,260) are one card with `aspect = both`.

**I. Many homonyms on one side: `коса`.** VESUM one entry (176043) plus `Коса` `:prop:geo`; ULIF seven: two proper names `Коса́`, homonym 3 `ко́са` (`іменник чоловічого або жіночого роду, істота`, different stress and gender), homonyms 4–6 `коса́` (`(волосся)`, `(про знаряддя)`, `(вузька смуга суходолу)`) with identical paradigms, homonym 7 header empty with a synonym group. Result: proper-name cards from 1–2; a `ко́са` card (`stress_only`, medium); three `коса́` cards by dictionary division (medium, Q-I1); homonym 7 `unresolved`.

## 6. Unresolved and uncertain matches

- A ULIF row (or any source unit) that cannot be attached at `high`/`medium` is kept in a **holding area** keyed by `(source_id, locator)` and by spelling, with `mapping.confidence = unresolved`. It appears on the disambiguation page as "unattached evidence" (thin cards are never hidden), never in practice, never in the dataset's card projection.
- A card with `identity.confidence = unresolved` is created only for the VESUM denominator (every VESUM entry gets a card) when the ULIF side is ambiguous; its ULIF-derived fields stay in the holding area.
- `low` mappings (e.g. VESUM's unsplit doublet on a split card) are retained as evidence and do not vote (`schema.md` §8).
- Detection at scale is code (this section); the decision on ambiguous candidates is a language lane, recorded as an overlay `identity` entry.

Expected volume from today's numbers: 10,570 ULIF spellings with several homonyms, 18,935 VESUM lemmas with several entries, 2,811 existing Atlas lemma articles whose spelling has several checked ULIF homonyms; these are the split candidates for the golden set (`migration.md` §5).

## 7. Splits, merges and redirects

- **Split** (one card → several): overlay `split` with `into` ids (minted at split time), evidence and lane. The old card becomes `redirected` with `merged_into` pointing at the card that keeps the majority of its assertions (rule: the one matching the old card's shown stress), and each assertion is re-mapped by the matching rules; assertions that do not map at ≥ medium go to the holding area. Learner progress keyed to the old id follows `merged_into` (Q-I4 on whether progress should instead be voided on a split).
- **Merge** (several → one): overlay `merge`; the losing card becomes `redirected`, its senses get `merged_into`, its assertions are re-subjected to the survivor, and duplicate assertions collapse (same content address).
- **Redirect** is the only visible effect of both: ids are never deleted or reused, and the mapping table keeps `key_at_creation` so a future harvest cannot re-mint the old key.
- **Re-harvest**: a new ULIF snapshot re-runs the matching; a homonym that changed number is re-attached by stress + paradigm, not by number; a changed `content_sha256` supersedes the old assertions.

## 8. Sense identity

Senses are card-owned rows. Source sense units (`ulif:section:<id>` synonym groups, ULIF `sense_gloss[i]`, `sum20:wordid/sense:k`, `vts:<spelling>#<n>/<k>`) are attached via `sense_map`. Automatic alignment only when a source has exactly one unit for the card; otherwise the unit is attached to an `unsplit` sense until an overlay `sense_map` aligns it (Q6 in `schema.md`). Relations are sense-bound: the ULIF group `ЛАНЦЮГО́М … КЛЮЧЕ́М, КЛЮЧА́МИ (перев. про птахів)` attaches to the "flock" sense of `ключ`, not to the card.

## 9. MWE identity

- Key: `<first source locator>|<normalised form>`; normalised form = NFC, accents stripped, lower-case, inner punctuation dropped, slot words (`кого, чого`, `що-н.`) and bracketed alternatives kept as `mwe_frame`. Sources: ULIF phraseology (8,131 sections; 4,820 distinct 60-char heads), `frazeolohichnyi` (24,683 rows), today's 639 multiword articles.
- The same idiom under several headwords is one card (`будувати повітряні замки` under `замок` and `повітряний`). Variant forms inside one ULIF section (`тримати (держати) за сімома замками`; `за сімома замками тримав`; `тримає за сімома замками`) are one card with `mwe_frame` variants, not several cards.
- Components: `component_of` links to lexeme cards, role `anchor` for the fixed non-optional word (ULIF `uid` anchors identify the component's homonym: `uid=47336` castle for `повітряні за́мки`, `uid=47335` lock for `за сімома замка́ми`).

## 10. Aspect pairs

Two cards, one `aspect_pair` link with roles, evidence cited on the link. Sources that can assert the pair today: ВТС headers (`недок. … док.`), СУМ-20 (100 articles), teacher lessons, PULS (both members rated: `писати` A1, `написати` A1, but no pairing). Not usable alone: identical ULIF synonym groups (91,385 imperfective/perfective lemma pairs share at least one group text; `писати/написати` and `вибігати/вибігти` are in the set, `брати/взяти` is not). The pair source for A1–B1 verbs is Q8 (`schema.md`).

## 11. Measured baseline (2026-09-28)

| measure | value |
| --- | --- |
| Atlas articles / distinct spellings | 27,128 / 27,128 (one per spelling) |
| Atlas lemma articles whose spelling has >1 checked ULIF homonym | 2,811 of 26,489 |
| Atlas lemma articles with no checked ULIF entry | 877 |
| Atlas stress rows / comparable to single-homonym ULIF polysyllables | 19,146 / 14,509 |
| … agree / ULIF doublet contains Atlas stress (`variant`) / differ | 14,419 / 12 / 78 (most of the 78 are identity artefacts, §5 E) |
| ULIF checked rows / distinct spellings / spellings with >1 homonym | 262,788 / 250,712 / 10,570 |
| ULIF checked rows with empty header / recoverable from paradigm / nothing | 12,899 / 12,095 / 27 |
| ULIF headwords with ≥2 stress marks / single-token ones | 7,157 / 2,828 |
| ULIF spellings with both perfective and imperfective homonyms | 292 |
| VESUM entries / lemmas / lemmas with >1 entry / `:xp` entries / declared doublets | 442,458 / 422,656 / 18,935 / 1,528 / 68 |
| Curated heteronyms in the side file | 420 lemmas |

Reproduction of the stress comparison (read-only):
```python
import sqlite3, json, unicodedata, re
a = sqlite3.connect("file:/home/ops/learn-ukrainian/data/atlas.db?mode=ro", uri=True)
s = sqlite3.connect("file:/home/ops/learn-ukrainian/data/sources.db?mode=ro", uri=True)
V = set("аеєиіїоуюя"); syl = lambda w: sum(ch in V for ch in w.lower())
atlas = {slug: unicodedata.normalize("NFC", json.loads(p)["form"]) for slug, p in a.execute("select slug,payload_json from enrichment where section='stress'") if json.loads(p).get("form")}
ulif, multi = {}, set()
for q, hw in s.execute("select normalized_query,canonical_headword from ulif_dictua_entries where homonym_checked=1 and canonical_headword!=''"):
    multi.add(q) if q in ulif else None; ulif.setdefault(q, []).append(unicodedata.normalize("NFC", hw))
agree = variant = conflict = 0
for slug, f in atlas.items():
    if slug not in ulif or slug in multi: continue
    hw, f = ulif[slug][0].lower(), f.lower(); bare = hw.replace("́", "")
    if bare != f.replace("́", "") or syl(bare) < 2 or "́" not in hw: continue
    pos = lambda w: {m.start() for m in re.finditer("́", w)}
    if hw == f: agree += 1
    elif hw.count("́") >= 2 and f.count("́") == 1 and pos(f) <= pos(hw): variant += 1
    else: conflict += 1
print(agree, variant, conflict)   # 14419 12 78
```

## 12. Open questions for the language lane (Gemini) and the design read (Astra)

- **Q-I1 (language)** Dictionary homonym division with an identical paradigm and stress (`ключ` 1/2, `коса́` 4–6): two cards at `medium` as proposed, or one card with senses until a lane confirms? What is the rule when ULIF and ВТС divisions differ in count?
- **Q-I2 (language)** ULIF headwords with two accents on a single token (2,828): treat all as doublet candidates, or only when the paradigm rows are double-marked too (`по́ми́лки`, `по́ми́лці`) as for `помилка`?
- **Q-I3 (language)** `броня`: confirm the two-card reading (VESUM unsplit doublet vs ULIF two homonyms), or rule that a VESUM-declared doublet always wins?
- **Q-I4 (design)** On a split, should learner progress follow `merged_into` (proposed) or be voided, given the old card mixed two words?
- **Q-I5 (design)** Denominator: every VESUM entry (442,458) gets a card even when ULIF is silent (proposed), versus VESUM lemma × pos (423,661).
- **Q-I6 (design + ULIF lane)** Extract ULIF's own `uid` per entry from the self-referencing anchors so `ulif:uid:<n>` can be the stable locator across harvests (numbers move, `uid` presumably does not).
- **Q-I7 (language)** Proper-name homonyms in ULIF with no VESUM `:prop` entry (`Коса́` river): create cards or hold?
- **Q-I8 (language)** Treat `прізвище` (5,787 checked rows) and `власна назва` (443) as `proper_name` cards by label alone?
