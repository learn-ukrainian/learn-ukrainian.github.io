# Atlas Encyclopedia Source Policy Verdict (agy lane)

**Date**: 2026-08-26  
**Advisor**: `agy`  
**Link**: #4387  

---

## 1. Executive Verdicts (Items 1–5)

1. **Item 1 (Easy slovnyk.me bucket):**  
   **VERDICT: ALLOW** `newsum` (СУМ-20), `vts`, `ukreng` (Балла), `synonyms`, `phraseology`, `orthography`, `orthoepy`, `holoskevych` (1929), and `davydov` as verified clean academic or anti-Soviet heritage sources in the easy slovnyk.me lane, while strictly **FORBIDDING** `sum` (СУМ-11) due to late-Soviet ideological framing and linguistic Russification.

2. **Item 2 (Hero gloss policy):**  
   **VERDICT: FORBID** leading any Atlas hero gloss with СУМ-11 text or obsolete dialect-only markers (`діал. Русалка`): when СУМ-20 exists, its primary standard modern sense must lead; when СУМ-20 is unpublished (letters С–Я), the hero gloss must be drawn from clean non-dialect VTS or vetted multi-source dig fallbacks (Wikipedia lead / e2u), never raw Soviet СУМ-11.

3. **Item 3 (VTS dialect-first articles):**  
   **VERDICT: FORBID** dialect-first or archaic-first VTS entries from taking top rank over standard СУМ-20 articles; when СУМ-20 provides standard contemporary senses, VTS must be treated as demoted and placed below СУМ-20 in both card ordering and hero gloss derivation.

4. **Item 4 (Wikipedia / Wikidata / e2u / Literary Corpus pipeline role):**  
   **VERDICT: ALLOW** Wikipedia, Wikidata, e2u, and the literary corpus as an automated **second easy lane** for baseline multi-dimensional encyclopedic enrichment across all entries, reserving the deep manual/agentic **dig** tier for resolving misses, polysemy collisions, and nuanced cultural vocabulary.

5. **Item 5 (Soviet dictionary policy & "Do not use Soviet shit"):**  
   **VERDICT: FORBID** rendering СУМ-11 anywhere in learner-facing Word Atlas pages—even as a footnote or secondary historical card—because Soviet ideological distortion cannot serve as legitimate heritage, whereas authentic historical attestation is already provided cleanly by pre-Soviet (Грінченко 1907, Голоскевич 1929), etymological (ЕСУМ), and post-Soviet academic sources.

---

## 2. Detailed Rationale & Architecture Alignment

### 2.1. Slovnyk.me Slugs Categorization (Easy Bucket)
- **`newsum` (СУМ-20, vols А–Р)** — **ALLOW**: Post-Soviet academic standard from NAS of Ukraine / ULIF. Primary explanatory source for letters А–Р.
- **`vts` (ВТС, Busel 2001–2009)** — **ALLOW**: Essential full-alphabet (А–Я) modern explanatory coverage; subject to rank demotion when flagged as dialect-first while СУМ-20 has standard senses.
- **`sum` (СУМ-11, 1970–1980)** — **FORBID**: Contaminated by Soviet ideological censorship and russified examples. Already excluded from `_definition_cards` (decision 2026-06-26).
- **`ukreng` (Балла)** — **ALLOW**: Authoritative modern English-Ukrainian bilingual dictionary by Mykola Balla.
- **`synonyms` (СУМ синонімів / Бурячок та ін.)** — **ALLOW**: Clean modern academic synonym sets.
- **`phraseology` (Фразеологічний словник)** — **ALLOW**: Academic phraseology repository for idioms and set expressions.
- **`orthography` (Орфографічний словник УМІФ НАНУ)** — **ALLOW**: Modern codified spelling and inflectional reference.
- **`orthoepy` (Орфоепічний словник)** — **ALLOW**: Modern academic pronunciation and phonetic transcription reference.
- **`holoskevych` (1929, «Правописний словник»)** — **ALLOW**: Pre-Soviet Kharkiv Orthography (Скрипниківка 1928–1929) heritage benchmark; documents authentic historical spelling prior to the 1933 Soviet linguistic purges.
- **`davydov` (Антоненко-Давидович «Як ми говоримо»)** — **ALLOW**: Foundational anti-Soviet decolonization guide written by dissident linguist Borys Antonenko-Davydovych; vital for usage notes, style warnings, and calque prevention.

### 2.2. Hero Gloss Resolution
- The hero gloss is the learner's first point of contact with an entry.
- A hero gloss must represent contemporary standard codified Ukrainian.
- PR #7349 fixed the `берегиня` regression where a leftover Soviet/dialect gloss («діал. Русалка») was replaced by СУМ-20 sense 1 («мати всього живого, богиня родючості...»).
- Policy rule: If an existing or incoming gloss begins with `діал.` or `заст.`, or contains archaic markers while СУМ-20 or modern standard definitions exist, the engine must extract the first non-dialect sense from СУМ-20 / VTS, or rely on a curated dig source.

### 2.3. VTS vs. СУМ-20 Ordering Hierarchy
- For headwords where VTS opens with a dialectal or archaic definition (e.g. `берегиня` → `діал. Русалка`) but СУМ-20 opens with standard modern senses, VTS is treated as demoted.
- Presentation order must strictly be: `[СУМ-20, ВТС, Грінченко (heritage optional)]`.
- For letters where СУМ-20 is absent (С–Я), VTS is allowed as primary explanatory card, provided leading dialect tags are not promoted to hero status if broader standard senses follow.

### 2.4. Two-Lane Enrichment Architecture (Easy vs. Dig)
To deliver a "rich all-around encyclopedia" rather than bare one-lemma pages:
1. **Easy Lane 1 (slovnyk.me multi-dictionary scrape & mirror):**
   Automated per-lemma cache fetch of 9 allowed slugs (`newsum`, `vts`, `ukreng`, `synonyms`, `phraseology`, `orthography`, `orthoepy`, `holoskevych`, `davydov`).
2. **Easy Lane 2 (Automated Encyclopedic Enrichment):**
   Systematic parallel automated extraction:
   - **Wikidata / Wikipedia**: Entity identification (QIDs, theonyms, cultural categories), Wikipedia lead extract, and direct encyclopedia URL link.
   - **e2u / Balla**: Reverse and forward terminological English translations.
   - **Literary Corpus (125K chunks)**: FTS5 automated attestation matching.
3. **Dig Lane (Targeted Deep Enrichment & Disambiguation):**
   Triggered on slovnyk.me misses, polysemy collisions, or culturally dense words:
   - Curated chunk pinning for literary attestations (e.g. `feaa5fa7_c0557` for *Енциклопедія українознавства* on `берегиня`).
   - Wikidata theonym / domain allowlist filtering (preventing bad synset attachments like water-nymph/mermaid to protective deities).
   - Historical dictionary excavation (ЕСУМ, Грінченко 1907).

### 2.5. Decolonization & Strict Prohibition of Soviet Relics
- "Do not use Soviet shit" means complete exclusion of СУМ-11 from public Atlas pages.
- Distinguishing authentic heritage vs. Soviet distortion:
  - **Authentic Ukrainian Heritage (Permitted & Celebrated)**: Грінченко (1907–1909), Голоскевич (1929), ЕСУМ, Антоненко-Давидович. These document authentic historical vocabulary before or outside Soviet Russification policy.
  - **Soviet Institutional Distortion (Strictly Forbidden)**: СУМ-11 (1970–1980). It introduced artificial Russian calques, suppressed authentic Ukrainian lexical items, and framed definitions through Marxist-Leninist ideology.
- Keeping СУМ-11 even as a footnote creates noise, misleads learners, and contradicts the repo's established decolonization mandate.

---

## 3. Residual Risks & Mitigations

1. **Unpublished Range Coverage (Letters С–Я in СУМ-20):**
   - *Risk*: СУМ-20 covers letters А–Р. For letters С–Я, VTS is the sole modern explanatory dictionary on slovnyk.me. If VTS contains poorly structured or idiosyncratic entries for a letter in С–Я, no СУМ-20 fallback exists.
   - *Mitigation*: Fallback to Ukrainian Wikipedia lead extracts, e2u definitions, and corpus examples via the Dig pipeline; never fall back to СУМ-11.

2. **Automated Wikidata Polysemy & False Synsets:**
   - *Risk*: Automated Wikidata / Wikipedia matching can conflate distinct concepts (e.g. mythic theonym vs. modern homonym).
   - *Mitigation*: Maintain P31 instance-of filters (e.g. `_WIKIDATA_THEONYM_P31`) and synset sanity guards in `enrich_manifest.py`.

3. **Strict Prohibition of Invented Ukrainian Glosses:**
   - *Requirement*: Under no circumstances should ungrounded LLM generation synthesize fictitious Ukrainian glosses or definitions.
   - *Mitigation*: All glosses and definition cards must be directly grounded in vetted dictionary records (СУМ-20, VTS, Wikipedia, e2u, or curated corpus chunks). If a word has no source, it remains flagged for the manual Dig lane rather than receiving hallucinated text.
