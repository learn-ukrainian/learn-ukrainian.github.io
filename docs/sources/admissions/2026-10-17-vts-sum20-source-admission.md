# Source Admission Record: ВТС and СУМ-20 (Word-Card Sense Seeding)

- **Date**: 2026-10-17
- **Authority**: CTO Order `message_d91c2393a03a4df397e097bf278db355` / Operator Directive (22:4xZ)
- **Programme**: [#8977](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8977) (Word Cards), [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321) (Open-Model-Data), [#10512](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/10512) (Source Completeness)
- **Scope**: Admission of digital copies of **СУМ-20** and **ВТС** as primary and secondary meaning sources for Word-Card sense seeding (amending `WORD_CARDS_DATA_PLAN.md` §6 Decision 1, §7 Residuals, §8 Counts).

---

## 1. Context & Operational Motivation

In `WORD_CARDS_DATA_PLAN.md` §6 Decision 1, sense seeding order was originally specified as:
> СУМ-20 (unquarantined, mapped to the lexeme) → ВТС numbered senses → ULIF sense_gloss

However, Decision 1 blocked ВТС from active seeding because:
> "ВТС is held locally (13,181 slovnyk_me_entries rows...) but its edition, permission-register row and sense parsing are not established; until a source-admission round establishes them, ВТС seeds nothing and the order falls through to ULIF."

On 2026-10-17, the Operator observed:
> "we already have СУМ-20 and ВТС on Atlas, why not use them?"

Verified database facts establish that live Atlas (`data/atlas.db:enrichment`) already serves definition cards for 12,468 words:
- **ВТС definitions**: 7,849 words
- **СУМ-20 definitions**: 5,844 words
- **Грінченко (1907) heritage cards**: 4,309 words

Furthermore, the persistent per-word slovnyk.me cache (`data/lexicon/slovnyk_cache/`, 38,190 JSON files, 456.4 MB) contains:
- **31,688 words** with valid, non-empty ВТС entries
- **22,075 words** with valid, non-empty СУМ-20 entries
- **32,306 words** with at least one modern dictionary definition (21,457 with both)

Because СУМ-20's published print volumes currently stop at Volume 16 (entry range А — РЯХТЛИВИЙ), СУМ-20 alone cannot cover the entire modern Ukrainian lexicon. ВТС is therefore required as the secondary explanatory dictionary to provide definition coverage for the post-РЯХТЛИВИЙ alphabet (С — Я) and unquarantined lexemes absent from СУМ-20.

---

## 2. Edition Records

### A. СУМ-20 (Словник української мови у 20 томах)
- **Work Title**: «Словник української мови: у 20 т.»
- **Institutions**: Український мовно-інформаційний фонд НАН України (УМІФ), Інститут мовознавства ім. О. О. Потебні НАН України
- **Published Scope**: Томи 1–16 (літери А — РЯХТЛИВИЙ), Київ: Наукова думка, 2010–2025+
- **Digital Platform / Aggregator**: slovnyk.me (`dictionary_slug='newsum'`)
- **Digital Label**: `Словник української мови у 20 томах (УМІФ НАН України, Ін-т мовознавства ім. О. О. Потебні)`
- **URL Schema**: `https://slovnyk.me/dict/newsum/{word}`
- **Held In Cache**: 22,075 words with verified non-empty definition text in `data/lexicon/slovnyk_cache/*.json`
- **Retrieval Dates**: 2026-08-06 to 2026-10-15 (with 33,623 files having filesystem mtime >= 2026-10-10)

### B. ВТС (Великий тлумачний словник сучасної української мови)
- **Work Title**: «Великий тлумачний словник сучасної української мови» (ВТС-СУМ)
- **Editor / Compiler**: В. Т. Бусел (головний редактор)
- **Print Edition**: 5-те видання, з дод. і допов., Київ; Ірпінь: ВТФ «Перун», 2005 (перевидання 2009); 1728 с., ISBN 966-569-013-2
- **Digital Platform / Aggregator**: slovnyk.me (`dictionary_slug='vts'`)
- **Digital Label**: `Великий тлумачний словник сучасної української мови` (Academic label: `Великий тлумачний словник сучасної української мови`)
- **URL Schema**: `https://slovnyk.me/dict/vts/{word}`
- **Held In Cache**: 31,688 words with verified non-empty definition text in `data/lexicon/slovnyk_cache/*.json`
- **Retrieval Dates**: 2026-08-06 to 2026-10-15

---

## 3. Permission-Register & Legal Basis

The permissions register (`docs/sources/permissions-register.yaml`) is updated to formally admit ВТС under the exact same legal and operational basis that Atlas already relies on for its live definition cards:

1. **Governing Law**: Art. 22(2)(1) of the Law of Ukraine No. 2811-IX «Про авторське право і суміжні права» (Right of quotation without author consent for educational, critical, scientific, or informational purposes, with attribution to the author and source).
2. **Attribution Display**: All rendered definition cards cite the full academic label:
   - For ВТС: `Великий тлумачний словник сучасної української мови` (short pill: `ВТС`)
   - For СУМ-20: `Словник української мови у 20 томах` (short pill: `СУМ-20`)
3. **Operator IP Responsibility**: Covered under Operator Decision 1 (`d1_content_stays`) and Plan v3.5.0 O1 (verbatim use of in-copyright reference sources is the operator's IP responsibility).
4. **Licensing Status & Dataset Boundary**:
   - For internal word cards and live Atlas presentation: **Admitted**.
   - For open public dataset export (Phase 7): Commercial/redistribution licence status remains **unknown / pending rights-holder confirmation**. As explicitly directed by the CTO and Operator, this limitation blocks ONLY the Phase 7 public dataset release; it does NOT block internal word card building or site display.

---

## 4. Sense Parsing: Reuse of Atlas Definition Cards Pipeline

Rather than constructing an unverified parser from scratch, word-card sense extraction reuses the exact, tested parser pipeline that compiles Atlas definition cards:

- **Primary Source Code**: [`scripts/lexicon/enrich_manifest.py`](file:///home/ops/learn-ukrainian/scripts/lexicon/enrich_manifest.py)
  - `_SlovnykArticleParser` (lines 1481–1549): Clean DOM parser extracting canonical URLs, `<h1 class="entry-title">`, `<p>` blocks, and stripping boilerplate.
  - `_parse_slovnyk_entry` (lines 1551–1595): Parses raw HTML into structured dictionary row (`text`, `paragraphs`, `title`, `source_url`, `word`).
  - `_definition_body` (lines 4529–4568): Cleans definition body, strips redundant leading headwords, normalizes punctuation and HTML entities.
  - `_vts_definition_card` (lines 4571–4633): Assembles VTS card payload with academic attribution, attaches official/mirror URLs, and resolves cross-references via `_resolve_definition_xref`.
  - `_sum20_definition_card` (lines 4668–4735): Assembles СУМ-20 card payload with academic attribution and official URL attachment.
  - `_definition_cards` (lines 4739–4768): Establishes priority sorting: modern definitions first, dialect/archaic demotion, and Грінченко (1907) heritage card last.
  - `_dictionary_definition_rows` (lines 4792–4830): Read-only extractor returning structured rows for gate verification.

### Empirical Parsing Quality Measurement
Measured against the full 38,190-entry local cache:
- **Total cache files parsed**: 38,190
- **Valid, non-empty СУМ-20 extractions**: 22,075 (100% of available newsum articles)
- **Valid, non-empty ВТС extractions**: 31,688 (100% of available vts articles)
- **At least one modern definition extracted**: 32,306 words
- **Parser crash or corruption rate**: 0.00% across the full cache corpus.

---

## 5. Hierarchy & Meanings Coverage Across Lexical Universes

Applying the hierarchy **СУМ-20 (first) → ВТС (second) → ULIF gloss (third)** yields the following verified coverage results:

### Universe 1: Atlas Live Articles (`data/atlas.db:articles`, N = 27,128)
- **Step 1: Covered by СУМ-20 first**: 21,428 entries (78.99%)
- **Step 2: Covered by ВТС second**: 4,428 entries (16.32%)
- **Step 3: Covered by ULIF gloss third**: 1 entry (0.00%)
- **Total covered with modern meaning**: **25,857 entries (95.31%)**
- **Real gap (neither)**: **1,271 entries (4.69%)**
- *(With VESUM base-lemma fallback for inflected headwords, total coverage rises to 26,111 entries (96.25%), leaving only 1,017 entries (3.75%) lacking a definition — predominantly multi-word idiomatic phrases, hyphenated spellings, or rare participles).*

### Universe 2: PULS CEFR Pedagogical Register (`data/sources.db:puls_cefr`, N = 5,839)
- **Step 1: Covered by СУМ-20 first**: 4,072 entries (69.74%)
- **Step 2: Covered by ВТС second**: 865 entries (14.81%)
- **Step 3: Covered by ULIF gloss third**: 4 entries (0.07%)
- **Total covered with modern meaning**: **4,941 entries (84.62%)**
- **Real gap (neither)**: **898 entries (15.38%)** (primarily comparatives, passive participles, modern loanwords, and compound terms whose base lemmas are covered).
- *(With VESUM base-lemma fallback, total coverage rises to 4,958 entries (84.91%), leaving 881 entries (15.09%) neither).*

### Universe 3: Slovnyk Cache Corpus (N = 38,190)
- **Step 1: Covered by СУМ-20 first**: 22,075 entries (57.80%)
- **Step 2: Covered by ВТС second**: 10,231 entries (26.79%)
- **Step 3: Covered by ULIF gloss third**: 6 entries (0.02%)
- **Total covered with modern meaning**: **32,312 entries (84.61%)**
- **Real gap (neither)**: **5,878 entries (15.39%)**

---

## 6. Formal Admission Verdict

1. **ВТС is hereby ADMITTED** as a required secondary source for Word-Card sense seeding under `WORD_CARDS_DATA_PLAN.md` §6 Decision 1.
2. The sense seed sequence is formally confirmed as:
   $$\text{СУМ-20 (unquarantined)} \longrightarrow \text{ВТС (numbered senses)} \longrightarrow \text{ULIF sense\_gloss}$$
3. Residual in §7 is formally closed.
4. Independent Cross-Family review routed to **GPT Sol 6.1**.
