# Source permissions register (#8979)

For every source that feeds word cards, the Word Atlas, practice and the open dataset: who the
rights holder is, how to reach them, what their terms say (quoted, with URL and read date), and
the status of each use. **Unknown uses are held.**

- **Machine-readable register (authoritative):** [`permissions-register.yaml`](permissions-register.yaml)
  — schema [`schemas/permissions-register.schema.json`](../../schemas/permissions-register.schema.json),
  validated by `tests/validate/test_permissions_register.py`. The per-source sections at the end of
  this file mirror the YAML; if they differ, the YAML wins.
- **Outreach drafts (not sent):** [`outreach/`](outreach/).
- **Spec:** #8979, approved proposal #8976 (advisor reads by Fable and Astra, operator sign-off 2026-09-27).
- **Read date of every quoted term:** 2026-09-27. This register is the project's own reading, not legal advice.

## How to read it

Permission is recorded per **(source, fields, scale)** and per **use**.

| Use | Meaning |
| --- | --- |
| `acquire` | Fetch or download it. |
| `store` | Keep a copy in our private stores (`sources.db`, caches, `atlas.db`). |
| `transform` | Parse, join, compare, derive our own values from it. |
| `display` | Show it on a learner-facing page (Word Atlas, practice, lessons). |
| `redistribute` | Ship it in the open dataset **or** the off-site Atlas export/API. |

| Status | Meaning |
| --- | --- |
| `permitted` | The rights holder's own licence/terms (quoted) or direct permission grants it. |
| `assessed` | No grant; we rely on the stated basis — a quoted statute, public domain, our own work, or (for internal preparation only) the operator's recorded decision to prepare in advance (#8976). |
| `unknown` | Nobody granted or assessed it. **Held** — the use does not happen. |
| `refused` | The rights holder's terms or answer forbid it. **Held.** |

| Scale | Meaning |
| --- | --- |
| `lookup` | Per-entry reads to check something. |
| `quotation` | One short, attributed, marked excerpt in our own commentary — not repeated across the lexicon. |
| `bulk` | A substantial part, **or** the same per-entry use repeated across the whole lexicon. Ukrainian law forbids "багаторазове та систематичне вилучення і повторне використання незначних частин вмісту бази даних" (Law 2811-IX Art. 26(4)), so a field shown on every card is bulk. |

**Gates.** `site_display` publishes a field only if its `display` status is `permitted` or
`assessed`. `dataset_and_atlas_export` is **one gate for both** the open dataset and the off-site
Atlas export/API (bulk-downloadable, therefore redistribution): a field ships only if its
`redistribute` status is `permitted` or `assessed`. The gates are specified here; wiring them into
the builds is #8979 AC-02 (not in this change).

**Legal basis used for `assessed`.** Law of Ukraine «Про авторське право і суміжні права»
No. 2811-IX (https://zakon.rada.gov.ua/laws/show/2811-20/print, read 2026-09-27): the sui generis
database right (Art. 21(4)), free use of databases (Art. 26: normal use, insubstantial parts,
**extraction** — not re-use — of a substantial part "для цілей ілюстрації в освітній або науковій
діяльності" with the source cited), quotation (Art. 22(2)(1)), term (Art. 31) and public domain
(Art. 32(3)). The TDM exception (Art. 22(2)(14)) is limited to research tied to scientific
publications and is not relied on. Exact quotes are in the YAML `legal_references`.

## Status summary

Per source and row (details and quotes in § Per source below).

| Source | Fields @ scale | acquire | store | transform | display | redistribute |
| --- | --- | --- | --- | --- | --- | --- |
| `ulif` | corroboration_reference @ bulk | assessed | assessed | assessed | assessed | assessed |
| `ulif` | headword, stress, grammatical_label, paradigm, homonym_sense_gloss, synonym_groups, antonym_pairs, phraseology @ bulk | assessed | assessed | assessed | unknown | unknown |
| `ulif` | headword, stress, grammatical_label, paradigm, homonym_sense_gloss, synonym_groups, antonym_pairs, phraseology @ lookup | assessed | assessed | assessed | assessed | unknown |
| `sum20` | definition_text, sense_structure, stressed_headword, literary_citations @ bulk | assessed | assessed | assessed | unknown | unknown |
| `sum20` | definition_text, sense_structure, stressed_headword, literary_citations @ quotation | assessed | assessed | assessed | assessed | unknown |
| `vesum` | lemma, word_forms, pos, morph_tags, markers @ bulk | permitted | permitted | permitted | permitted | permitted |
| `slovnyk_me` | verification_outcome @ lookup | assessed | assessed | assessed | assessed | assessed |
| `slovnyk_me` | definition_text, usage_essay, en_gloss_ukreng @ bulk | refused | refused | refused | refused | refused |
| `grinchenko` | headword, entry_text @ bulk | assessed | assessed | assessed | assessed | assessed |
| `sum11` | russification_quote, russification_pair @ quotation | assessed | assessed | assessed | assessed | unknown |
| `sum11` | russification_quote, russification_pair @ bulk | assessed | assessed | assessed | unknown | unknown |
| `grac` | example_sentence @ quotation | assessed | assessed | assessed | assessed | unknown |
| `grac` | frequency_count @ bulk | assessed | assessed | assessed | unknown | unknown |
| `grac` | frequency_tier @ bulk | assessed | assessed | assessed | assessed | unknown |
| `ua_gec` | error_text, correction_text, error_type @ bulk | permitted | permitted | permitted | permitted | permitted |
| `ukrajinet` | synset_members @ bulk | permitted | permitted | permitted | permitted | permitted |
| `wiktionary` | definition_text, synonyms, antonyms, etymology_text @ bulk | permitted | permitted | permitted | permitted | permitted |
| `kaikki` | en_gloss, ipa, etymology_text @ bulk | permitted | permitted | permitted | permitted | permitted |
| `dmklinger` | en_gloss @ bulk | permitted | permitted | permitted | permitted | permitted |
| `goroh` | en_gloss, etymology_text @ lookup | assessed | assessed | assessed | unknown | unknown |
| `goroh` | en_gloss, etymology_text @ bulk | unknown | unknown | unknown | unknown | unknown |
| `mphdict` | etymology_text, synonym_groups @ bulk | permitted | permitted | permitted | unknown | unknown |
| `balla` | en_uk_translation @ bulk | assessed | assessed | assessed | unknown | unknown |
| `puls` | cefr_level @ bulk | assessed | assessed | assessed | unknown | unknown |
| `ubertext_freq` | frequency_count @ bulk | assessed | assessed | assessed | unknown | unknown |
| `ubertext_freq` | frequency_tier @ bulk | assessed | assessed | assessed | assessed | unknown |
| `r2u_e2u` | en_gloss @ lookup | assessed | assessed | assessed | unknown | unknown |
| `wikidata` | en_gloss @ bulk | permitted | permitted | permitted | permitted | permitted |
| `ukrainian_word_stress` | stress @ bulk | permitted | permitted | permitted | permitted | permitted |
| `teacher_materials` | vocabulary_list, en_meaning_teacher, lesson_sentence @ bulk | permitted | permitted | permitted | permitted | unknown |
| `course_authored` | en_gloss_course, course_usage, curation_overlay, russification_commentary @ bulk | permitted | permitted | permitted | permitted | permitted |
| `wikipedia` | article_extract @ bulk | permitted | permitted | permitted | permitted | permitted |
| `esum` | etymology_text, cognate_forms @ bulk | assessed | assessed | assessed | unknown | unknown |
| `esum` | etymology_text @ quotation | assessed | assessed | assessed | assessed | unknown |
| `textbooks` | example_sentence @ quotation | assessed | assessed | assessed | assessed | unknown |
| `textbooks` | textbook_chunk @ bulk | assessed | assessed | assessed | unknown | unknown |
| `frazeolohichnyi` | idiom, idiom_definition @ bulk | assessed | assessed | assessed | unknown | unknown |
| `antonenko_style_guide` | style_rule_quote @ quotation | assessed | assessed | assessed | assessed | unknown |
| `antonenko_style_guide` | style_entry_text @ bulk | assessed | assessed | assessed | unknown | unknown |
| `ulp_private` | reference_text @ bulk | assessed | assessed | assessed | refused | refused |

## Findings — current state vs. this register (report, not fixed here)

These are uses happening today whose status in the register is `unknown` or `refused`. #8979's
stop policy says to report them; the operator decides whether to pause them before the gates land.

1. **The Atlas already displays and exports held fields.** `scripts/atlas/export_runtime_shards.py`
   writes each entry's whole `payload_json` into the site shards, including ULIF synonyms,
   antonyms and idioms, СУМ-20 definitions, mphdict ЕСУМ etymology, slovnyk.me usage essays, and
   Горох / Балла / e2u glosses. On this register their `display` (at bulk) and `redistribute` are
   `unknown` or `refused`. The shards are public files, so they are also redistribution.
2. **The open-dataset exporter lists held sources.** `scripts/lexicon/export_open_dataset.py`
   (`ATTRIBUTION_MD`) names СУМ-11, СУМ-20, ЕСУМ and Горох without terms, and calls the
   Kaikki/Wiktionary data CC BY-SA 3.0 (it is 4.0 per https://kaikki.org/dictionary/ →
   https://en.wiktionary.org/wiki/Wiktionary:Copyrights).
3. **`LICENSE-CONTENT.md` and `scripts/audit/source_license_map.json` are wrong in places:**
   VESUM is "MIT-ish" there, but its data is CC BY-NC-SA 4.0 (dict_uk README); СУМ-11 is "public
   domain" there, but it is a co-authored 1970–1980 work still in copyright (Art. 31(4)); Балла is
   "copyright expired" there, with no support (editions of 1996 and 2007 are in circulation);
   Kaikki is CC BY-SA 3.0 there, 4.0 in fact. `scripts/ingest/ua_gec_ingest.py` says UA-GEC is
   "MIT licensed"; its LICENSE is CC BY 4.0.
4. **slovnyk.me is used beyond verification.** `scripts/lexicon/build_slovnyk_mirror.py` pre-fills
   a cache for every Atlas lemma, and `scripts/lexicon/fill_slovnyk_sum20_cache.py` says it
   "Bypasses Cloudflare automated client challenges". The site's terms forbid copying without
   permission (quoted below), and ULIF names slovnyk.me an unlawful copy of СУМ.
5. **Crawl etiquette.** `scripts/ingest/sum20_official_ingest.py` crawled sum20ua.com with a 2-second
   delay; its robots.txt asks for `Crawl-delay: 10` and blocks AI crawlers by name.
   `scripts/rag/source_query.py` sends a desktop-Chrome user agent on live lookups (r2u, e2u,
   Горох, GRAC, ULIF, slovnyk.me, pravopys) instead of identifying the project.
   The Ukrainian Lessons terms forbid crawling ("spider, crawl, or scrape"), and
   `scripts/crawl/crawl_ulp.py` / `crawl_ulp_blog.py` fetch site pages for a catalogue.
6. **Aggregator copies.** Our СУМ-11, Грінченко, Балла and phraseology copies come from
   `bakustarver/ukr-dictionaries-list-opensource`, a repository marked AGPL-3.0 that states no
   grant from the dictionaries' rights holders. Грінченко is public domain regardless; the others
   are internal-only on this register.
7. **Teacher materials:** site publication is allowed by the operator (#8843); inclusion in the
   open dataset under an open licence was never asked (held).

## Recommendation — the dataset's own licence (operator decides)

**Recommend: CC BY-NC-SA 4.0 for the core dataset, with Wiktionary-family fields in a separate
CC BY-SA 4.0 file set of the same release (or left out).**

Reasoning:

- **VESUM forces it.** VESUM is the backbone of every card, and its data licence is CC BY-NC-SA
  4.0. CC: "Your contributions to adaptations of material under BY-NC-SA 4.0 may only be licensed
  under: BY-NC-SA 4.0, or a later version of the BY-NC-SA license"
  (https://creativecommons.org/share-your-work/licensing-considerations/compatible-licenses/,
  read 2026-09-27). The project is permanently non-commercial (CLAUDE.md policy 2026-04-19), so NC
  costs nothing.
- **Compatible inputs.** CC BY 4.0 (UA-GEC), CC0 (Wikidata), MIT (ukrainian-word-stress) and
  public-domain (Грінченко) data can go into a BY-NC-SA adaptation with attribution.
- **Incompatible inputs.** CC BY-SA material (Вікісловник, Kaikki, dmklinger, ukrajinet,
  Вікіпедія) must stay BY-SA when adapted: "Your contributions to adaptations of BY-SA 4.0
  materials may only be licensed under: BY-SA 4.0 … GPLv3" (same page). So a single record may not
  merge a VESUM form with a Wiktionary gloss. Ship BY-SA-derived fields as their own files joined
  by card id — CC allows combining unadapted works as long as each keeps its licence ("you may
  combine any CC-licensed content so long as you provide attribution and comply with the
  NonCommercial restriction if it applies", https://creativecommons.org/faq/, read 2026-09-27).
- **Our own content** (course glosses, curation overlay, russification commentary) is CC BY-SA
  4.0 under `LICENSE-CONTENT.md`. The maintainer, as rights holder, can additionally license it
  CC BY-NC-SA 4.0 so it sits in the core files.
- **Held sources** (ULIF, СУМ-20, ЕСУМ, PULS, GRAC sentences, …) join the core under BY-NC-SA 4.0
  only if their answers allow it — each outreach draft proposes exactly that licence.
- **Not recommended:** CC BY-SA 4.0 or CC BY 4.0 for the whole dataset (would drop VESUM);
  ODbL (mphdict) — its share-alike does not map onto CC BY-NC-SA; keep mphdict out until the
  ЕСУМ question is answered.

## Open questions for the operator

1. Pause the held fields that the Atlas displays/exports today (Findings 1–2), or keep them until
   the gates (AC-02) land? The register says held.
2. Approve the dataset licence recommendation above?
3. Confirm with the teacher, in writing, both site publication and dataset inclusion.
4. Send order for the outreach drafts (suggested: ULIF first, then the Інститут мовознавства,
   PULS, GRAC, lang-uk, r2u/e2u), after a language-lane review of the Ukrainian text and filling
   the placeholders (working-result link, takedown contact).
5. Which takedown contact to publish (the drafts leave a placeholder; the repository's GitHub
   issues are the only public route today).
6. ULIF's robots.txt cannot be read (access-restricted page): continue the #8400 harvest at one
   request per second until ULIF answers? The register treats the harvest as extraction for
   educational use (Art. 26(3)(2)), which covers acquiring and storing, not publishing.

## Outreach drafts

| Rights holder | Covers | Draft |
| --- | --- | --- |
| Український мовно-інформаційний фонд НАН України | `ulif`, `sum20` | [`outreach/ulif.md`](outreach/ulif.md) |
| Інститут мовознавства ім. О. О. Потебні НАН України | `esum`, `mphdict` (ЕСУМ), `sum11` (russification quotations), `sum20` (co-compiler) | [`outreach/inmo.md`](outreach/inmo.md) |
| ПУЛЬС, УКУ | `puls` | [`outreach/puls.md`](outreach/puls.md) |
| ГРАК | `grac` | [`outreach/grac.md`](outreach/grac.md) |
| lang-uk | `ubertext_freq` | [`outreach/lang_uk.md`](outreach/lang_uk.md) |
| r2u / e2u maintainers | `r2u_e2u` | [`outreach/r2u_e2u.md`](outreach/r2u_e2u.md) |

No draft for: `slovnyk_me`, `goroh` (mirrors — use the original works instead); `balla`,
`antonenko_style_guide` (no rights-holder contact found; open sources or quotation cover the
need); `frazeolohichnyi` (ULIF phraseology is the planned idiom source); `textbooks` (quotation
only); `teacher_materials` (via the operator); openly licensed sources.

The Ukrainian text of every draft is model-written. It needs a sanctioned language-lane review
outside the author's family before anything is sent.

## Per source

### «Словники України» online (DictUA) — paradigm, synonym, antonym and phraseology tabs — `ulif`

- **Organisation:** Український мовно-інформаційний фонд НАН України (УМІФ / ULIF)
- **Role:** Stress, paradigms, grammar labels, homonym/sense hints, synonyms, antonyms and phraseology for word cards; the harvest is #8400.
- **Fields:** corroboration_reference, headword, stress, grammatical_label, paradigm, homonym_sense_gloss, synonym_groups, antonym_pairs, phraseology
- **Stored in:** data/sources.db ulif_dictua_entries, ulif_dictua_sections; data/lexicon/cache/ulif_raw.sqlite ulif_dictua_raw_responses; data/atlas.db / site lexicon shards (synonyms, antonyms, idioms already exported — see md § Findings)
- **Licence as found:** All rights reserved (© ULIF); no open licence found
- **Conditions:** attribution — «Словники України online», Український мовно-інформаційний фонд НАН України, https://lcorp.ulif.org.ua/dictua/ (entry reference and retrieval date per field) Share-alike: unknown. Non-commercial: unknown.
  - Sui generis database right (Law 2811-IX Art. 21) applies to extraction and re-use of substantial parts.
  - Harvest runs at one request per second with an identifying non-commercial user agent (fetch_ulif_homonyms.py).
- **Terms as found:**
  - «"Словники України online" розроблено на основі CD-версії 3.2 (2008р.) © ULIF, 2001-2026» — Copyright notice only; no licence or terms-of-use page is linked from the portal. (https://lcorp.ulif.org.ua/dictua/, read 2026-09-27)
  - «ШАНОВНІ КОРИСТУВАЧІ! Вебсайти на кшталт goroh.pp.ua, sum.in.ua, slovnyk.me використовують електронні версії "Словника української мови" та "Словника української мови в 20 томах" неправомірно, не вказуючи авторів!» — ULIF states that goroh.pp.ua, sum.in.ua and slovnyk.me use СУМ and СУМ-20 unlawfully, without naming the authors. (https://www.ulif.org.ua/koristuities-dostovirnimi-dzhierielami, read 2026-09-27)
- **Also searched:** https://lcorp.ulif.org.ua/dictua/ (footer; only links Pro_Systemu.pdf, Instruction_Dict_Of_Ukraine_3.2.pdf, the notice); https://lcorp.ulif.org.ua/robots.txt (returned an access-restricted page); https://www.ulif.org.ua/contacts; services.ulif.org.ua (timed out)
- **Per use:**
  - *corroboration_reference @ bulk* — ULIF as corroboration: a fact carried by an open source (e.g. VESUM stress/POS) is published under that source's licence, and the card only records "ULIF agrees" with the ULIF entry reference. No ULIF content is re-used.
    - acquire: **assessed** — Extraction for educational illustration, source cited, non-commercial.
    - store: **assessed** — Private store of the extracted copy; same basis as acquire.
    - transform: **assessed** — Comparison against open sources to produce our own agreement flag.
    - display: **assessed** — Only a citation and our own agree/disagree flag are shown; no ULIF content is re-used.
    - redistribute: **assessed** — Only the citation and our own flag ship; the underlying fact ships under the open source's licence.
  - *headword, stress, grammatical_label, paradigm, homonym_sense_gloss, synonym_groups, antonym_pairs, phraseology @ bulk* — ULIF-only data at scale — the whole harvest, or per-card display across the lexicon (Art. 26(4)).
    - acquire: **assessed** — Extraction of a substantial part for educational illustration, source cited, no independent economic significance; operator sign-off 2026-09-27 (#8976) to prepare in advance.
    - store: **assessed** — Private store only (sources.db, raw cache); same basis as acquire.
    - transform: **assessed** — Internal card assembly and joins; nothing leaves the private store under this row.
    - display: **unknown** — Showing ULIF content on every Atlas card is re-use of a substantial part (Art. 21(4)) or systematic re-use of insubstantial parts (Art. 26(4)); no permission yet. HELD until ULIF answers (outreach/ulif.md).
    - redistribute: **unknown** — Bulk re-use in the dataset / Atlas export needs ULIF's permission. HELD.
  - *headword, stress, grammatical_label, paradigm, homonym_sense_gloss, synonym_groups, antonym_pairs, phraseology @ lookup* — Per-entry live reads for checking a word (MCP query_ulif, reviewers).
    - acquire: **assessed** — Normal use of a public dictionary portal by a lawful user.
    - store: **assessed** — Transient/insubstantial parts only.
    - transform: **assessed** — Insubstantial part, used to check our own text.
    - display: **assessed** — An individual lesson or review may quote one entry with attribution (not systematic).
    - redistribute: **unknown** — Not needed at this scale; any dataset use is bulk (row above). HELD.
- **Open questions:**
  - Will ULIF permit display of synonyms, antonyms, phraseology and paradigms on Atlas pages, and their inclusion in the dataset under CC BY-NC-SA 4.0?
  - Which attribution form does ULIF want, and does it want links to lcorp.ulif.org.ua entries?
  - lcorp.ulif.org.ua/robots.txt returns an access-restricted page, so no crawl policy can be read; ask ULIF whether the one-request-per-second harvest (#8400) is acceptable.
  - Is the published contact email (alexandr.yeroshenko@hotmail.com, "про нас" sidebar) the right route, or the director's office by phone/post?
- **Contact:** Director's office (Надутенко Максим Вікторович); adviser to the directorate academician Широков Володимир Анатолійович · `alexandr.yeroshenko@hotmail.com` · https://www.ulif.org.ua/contacts (published at: https://www.ulif.org.ua/contacts — «Тел.: +38044 525 81 65 (директор) ... Адреса: 03039, Україна, м.Київ, пр-т. Голосіївський, 3»; email from the site's "про нас" sidebar («Контактна інформація alexandr.yeroshenko@hotmail.com»); legacy ulif@ulif.org.ua in the 2008 CD manual.)
- **Outreach draft:** [`ulif.md`](outreach/ulif.md)

### «Словник української мови у 20 томах» (СУМ-20), official electronic edition — `sum20`

- **Organisation:** Український мовно-інформаційний фонд НАН України (publisher, © of sum20ua.com) with the Інститут мовознавства ім. О. О. Потебні НАН України (co-compiler). Not the Інститут української мови, as the #8979 brief assumed — see the quotes.
- **Role:** Modern Ukrainian definitions, sense structure, stressed headwords and citations for cards.
- **Fields:** definition_text, sense_structure, stressed_headword, literary_citations
- **Stored in:** data/sources.db sum20_articles, sum20_senses, sum20_citations (crawled from sum20ua.com); site lexicon shards (definition cards; see md § Findings)
- **Licence as found:** All rights reserved (© ULIF); no open licence found
- **Conditions:** attribution — Словник української мови у 20 томах (Український мовно-інформаційний фонд НАН України, Інститут мовознавства ім. О. О. Потебні НАН України), https://sum20ua.com/ — official edition only, never a mirror (docs/best-practices/atlas-source-presentation.md). Share-alike: unknown. Non-commercial: unknown.
  - Definitions are copyrighted text and the dictionary is also a protected database.
  - robots.txt asks for a 10-second crawl delay; the ingest crawler (scripts/ingest/sum20_official_ingest.py, delay_s=2.0) used 2 seconds — see md § Findings.
- **Terms as found:**
  - «Словник української мови. Томи 1-16 (А-РЯХТЛИВИЙ) © Український мовно-інформаційний фонд НАН України, 2015 - 2026» (https://sum20ua.com/, read 2026-09-27)
  - «Для посилання на наш Словник ... можна використовувати URL-адресу форми: https://sum20ua.com/expl/entry/search/слово» — The only reuse the site offers is linking (and embedding its search form). (https://sum20ua.com/, read 2026-09-27)
  - «User-agent: ClaudeBot Disallow: / ... User-agent: * Allow: / ... Crawl-delay: 10» — AI crawlers are blocked by name; all other agents allowed with a 10-second crawl delay. (https://sum20ua.com/robots.txt, read 2026-09-27)
  - «"Словник української мови в 20 томах" укладається науковцями Українського мовно-інформаційного фонду НАН України та Інституту мовознавства ім. О.О. Потебні НАН України» (https://www.ulif.org.ua/koristuities-dostovirnimi-dzhierielami, read 2026-09-27)
- **Also searched:** https://sum20ua.com/Home/About (404); https://sum20ua.com/robots.txt; https://iul-nasu.org.ua/pro-instytut/kontaktna-informatsiya.html (Інститут української мови — not the compiler)
- **Per use:**
  - *definition_text, sense_structure, stressed_headword, literary_citations @ bulk*
    - acquire: **assessed** — Extraction for educational illustration, source cited, non-commercial; operator sign-off 2026-09-27 (#8976). Crawl-delay compliance is an open question.
    - store: **assessed** — Private store only; same basis as acquire.
    - transform: **assessed** — Internal comparison and card assembly.
    - display: **unknown** — A definition on every Atlas card is systematic re-use of a protected database and copyrighted text. HELD until ULIF answers (covered by outreach/ulif.md).
    - redistribute: **unknown** — Class C (dictionary-authored text): held out of the dataset and Atlas export until the rights holder agrees (#8976). HELD.
  - *definition_text, sense_structure, stressed_headword, literary_citations @ quotation* — One attributed definition quoted in a lesson or review, marked as a quotation — not the Atlas at scale.
    - acquire: **assessed** — Normal use of a public dictionary site.
    - store: **assessed** — Insubstantial part.
    - transform: **assessed** — Quoted, not altered; boundaries marked.
    - display: **assessed** — Quotation with author and source named, informational purpose, boundaries marked.
    - redistribute: **unknown** — Quotation in a bulk dataset is systematic; HELD.
- **Open questions:**
  - Is СУМ-20 display/dataset permission granted by ULIF alone, or also by the Інститут мовознавства ім. О. О. Потебні as co-compiler?
  - Re-crawl or top-up must honour Crawl-delay 10 (current crawler used 2 s).
- **Contact:** Same as ULIF (publisher of sum20ua.com); co-compiler Інститут мовознавства ім. О. О. Потебні НАН України · `alexandr.yeroshenko@hotmail.com` · https://www.ulif.org.ua/contacts (published at: https://sum20ua.com/ footer names ULIF as © holder)
- **Outreach draft:** [`ulif.md`](outreach/ulif.md)

### ВЕСУМ — Великий електронний словник української мови (dict_uk) — `vesum`

- **Organisation:** Андрій Рисін, Василь Старко, команда БрУК (brown-uk)
- **Role:** Lemmas, all word forms, POS and grammatical tags — the open backbone of every card.
- **Fields:** lemma, word_forms, pos, morph_tags, markers
- **Stored in:** data/vesum.db (forms_all, form_markers, vesum_build_metadata) from dict_corp_vis.txt.bz2 v6.8.0 (scripts/config/vesum_source.lock.json)
- **Licence as found:** CC BY-NC-SA 4.0 (dictionary data); GPL-3.0-or-later (software)
- **Conditions:** attribution — Рисін А., Старко В. Великий електронний словник української мови (ВЕСУМ). Версія <used version>. 2005-2026. URL: https://vesum.nlp.net.ua/ — licence CC BY-NC-SA 4.0, changes indicated. Share-alike: yes. Non-commercial: yes.
  - Adaptations may only be licensed under BY-NC-SA 4.0 or later (CC compatibility page) — this sets the dataset licence.
  - LICENSE-CONTENT.md currently calls VESUM "MIT-ish" — wrong; fix in the follow-up (md § Findings).
- **Terms as found:**
  - «Дані словника доступні для використання згідно з умовами ліцензії "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" (https://creativecommons.org/licenses/by-nc-sa/4.0/)» (https://github.com/brown-uk/dict_uk/blob/master/README.md, read 2026-09-27)
  - «Dictionary data are distributed under "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" (https://creativecommons.org/licenses/by-nc-sa/4.0/) Software is distributed under GPL 3.0 or above. Note: derivative projects have different licenses» (https://github.com/brown-uk/dict_uk/blob/master/README.md, read 2026-09-27)
  - «GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007» — The root LICENSE file is the GPL-3.0 text and covers the software only; the README assigns data to CC BY-NC-SA 4.0. (https://github.com/brown-uk/dict_uk/blob/master/LICENSE, read 2026-09-27)
  - «Rysin, A., Starko, V. Large Electronic Dictionary of Ukrainian (VESUM). Version 6.7.8. 2005-2026. Available at: https://vesum.nlp.net.ua/» (https://github.com/brown-uk/dict_uk/blob/master/README.md, read 2026-09-27)
  - «NonCommercial — You may not use the material for commercial purposes. ShareAlike — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.» (https://creativecommons.org/licenses/by-nc-sa/4.0/, read 2026-09-27)
- **Per use:**
  - *lemma, word_forms, pos, morph_tags, markers @ bulk*
    - acquire: **permitted** — CC BY-NC-SA 4.0 data licence.
    - store: **permitted** — CC BY-NC-SA 4.0.
    - transform: **permitted** — Adaptation allowed; result stays BY-NC-SA 4.0.
    - display: **permitted** — Non-commercial display with the citation.
    - redistribute: **permitted** — Non-commercial redistribution under BY-NC-SA 4.0 with attribution.
- **Open questions:**
  - The README cites version 6.7.8; we pin 6.8.0 (latest release 6.8.6). Cite the version actually used.
- **Contact:** Андрій Рисін (maintainer), GitHub issues at brown-uk/dict_uk · `arysin@gmail.com` · https://github.com/brown-uk/dict_uk (published at: https://github.com/brown-uk/dict_uk/blob/master/README.md ("Copyright (c) 2026 Andriy Rysin (arysin@gmail.com), Vasyl Starko, BrUK team"))

### slovnyk.me (aggregator of dictionaries incl. СУМ-11 and СУМ-20 copies) — `slovnyk_me`

- **Organisation:** Slovnyk.me (operator not named on the site)
- **Role:** Verification only (#8976) — check that an entry exists or a fact agrees; never a displayed source.
- **Fields:** verification_outcome, definition_text, usage_essay, en_gloss_ukreng
- **Stored in:** data/sources.db slovnyk_me_entries (snippets capped at 200–500 chars); data/lexicon/slovnyk_cache/ (pre-filled cache for Atlas lemmas — see md § Findings)
- **Licence as found:** No licence; site terms forbid copying without permission. Underlying dictionaries belong to their publishers (ULIF says the СУМ copies are unlawful).
- **Conditions:** attribution — Never shown as an authority on learner pages; attribute the underlying work and its official edition (atlas-source-presentation.md rules 1–3). Share-alike: unknown. Non-commercial: unknown.
  - scripts/lexicon/fill_slovnyk_sum20_cache.py states it "Bypasses Cloudflare automated client challenges" — see md § Findings.
- **Terms as found:**
  - «Пользователь соглашается не воспроизводить, не повторять и не копировать, не продавать и не перепродавать, а также не использовать для каких-либо коммерческих целей какие-либо части Сайта ... кроме тех случаев, когда такое разрешение дано Пользователю Администрацией Сайта.» — The user agrees not to reproduce, repeat or copy, sell or resell, or use commercially any part of the site unless the site administration permits it. (Archived 2024-03-20; the live /terms is blocked by Cloudflare and disallowed in robots.txt.) (https://web.archive.org/web/20240320103142id_/https://slovnyk.me./terms, read 2026-09-27)
  - «User-agent: * Disallow: /feedback Disallow: /terms Disallow: /search» (https://slovnyk.me/robots.txt, read 2026-09-27)
- **Also searched:** https://slovnyk.me/ (live: Cloudflare 403); footer via Wayback 2026-08-25 «Контакти © 2026 Slovnyk.me»
- **Per use:**
  - *verification_outcome @ lookup* — We store only our own result (agrees / disagrees / not found), the URL and the date.
    - acquire: **assessed** — Reading a public page is normal use; per-need lookups, not a systematic pre-fill.
    - store: **assessed** — Only our own outcome flag, URL and date are kept; no site text.
    - transform: **assessed** — Comparison yields our own flag.
    - display: **assessed** — Only our flag, never slovnyk.me text or URL on learner pages.
    - redistribute: **assessed** — Only our flag; no slovnyk.me content.
  - *definition_text, usage_essay, en_gloss_ukreng @ bulk*
    - acquire: **refused** — Site terms forbid copying any part without permission; ULIF names slovnyk.me an unlawful copy of СУМ.
    - store: **refused** — Same terms.
    - transform: **refused** — Same terms.
    - display: **refused** — Same terms; use the underlying work's own row instead.
    - redistribute: **refused** — Same terms.
- **Open questions:**
  - The live terms could not be read (Cloudflare 403; robots.txt disallows /terms). The 2024 archived Russian-language terms are the latest seen.
- **Contact:** Web form only (/feedback); no email, organisation or address published · https://slovnyk.me/feedback (published at: https://web.archive.org/web/20260825161137id_/https://slovnyk.me/feedback)

### Грінченко Б. Д. «Словарь української мови» (1907–1909) — `grinchenko`

- **Organisation:** Public domain (compiler Борис Грінченко, d. 1910). Our digital copy comes from the bakustarver/ukr-dictionaries-list-opensource aggregator; its digitiser is not named.
- **Role:** Pre-Soviet attestation of words and senses.
- **Fields:** headword, entry_text
- **Stored in:** data/sources.db grinchenko(word, definition, source) from a Lingvo-format JSON (scripts/rag/prepare_grinchenko.py)
- **Licence as found:** Public domain (Law 2811-IX Art. 31(2), 32(3)) — the project's reading
- **Conditions:** attribution — Грінченко Б. Д. Словарь української мови. Київ, 1907–1909. (Moral right of attribution survives, Art. 32(3).) Share-alike: no. Non-commercial: no.
  - A digitiser's own database right (Art. 21, 15 years) could exist for a recent digitisation; the digitiser is unknown.
- **Terms as found:**
  - «Борис Дмитрович Грінче́нко (27 листопада [9 грудня] 1863 … — 23 квітня [6 травня] 1910, Оспедалетті, Королівство Італія)» — The compiler died in 1910, so the life+70 term ended on 31 December 1980. (https://uk.wikipedia.org/wiki/Грінченко_Борис_Дмитрович, read 2026-09-27)
  - «Матеріали для словника зібрала редакція журналу «Кіевская старина», а упорядкував його … Борис Грінченко» — The journal's editors gathered the material; Hrinchenko compiled it. (https://uk.wikipedia.org/wiki/Словарь_української_мови, read 2026-09-27)
- **Also searched:** https://github.com/bakustarver/ukr-dictionaries-list-opensource (AGPL-3.0 repo; no provenance for the digitisation)
- **Per use:**
  - *headword, entry_text @ bulk*
    - acquire: **assessed** — Public domain: compiler died 1910.
    - store: **assessed** — Public domain
    - transform: **assessed** — Public domain
    - display: **assessed** — Public domain, with attribution.
    - redistribute: **assessed** — Public domain, with attribution; residual risk: an unknown digitiser's database right.
- **Open questions:**
  - Death dates of the other early editors (Науменко, Тимченко) were not verified.
  - Who digitised this copy? A copy made from the public-domain scans ourselves would remove the digitiser question.
- **Contact:** n/a (public domain)

### «Словник української мови» в 11 томах (СУМ-11, 1970–1980) — `sum11`

- **Organisation:** Інститут мовознавства ім. О. О. Потебні НАН України (compiled by over 50 lexicographers; official electronic edition at inmo.org.ua)
- **Role:** ONLY russification evidence (rule #M-6, operator 2026-09-27): what СУМ-11 imposed, shown red-flagged beside the modern Ukrainian norm with both sources cited. Never a modern meaning, form, example or practice answer.
- **Fields:** russification_quote, russification_pair
- **Stored in:** data/sources.db sum11(word, definition, text, source) from the bakustarver/ukr-dictionaries-list-opensource JSON (scripts/rag/convert_dictionaries.py)
- **Licence as found:** In copyright — co-authored work, 70 years after the last co-author's death (Art. 31(4)); LICENSE-CONTENT.md and scripts/audit/source_license_map.json call it public domain, which is wrong.
- **Conditions:** attribution — Словник української мови: в 11 томах. АН УРСР, Інститут мовознавства ім. О. О. Потебні. Київ: Наукова думка, 1970–1980. Т. <vol>, с. <page> — quoted, red-flagged, always with the modern norm in the same sentence. Share-alike: unknown. Non-commercial: unknown.
  - Our copy comes from an aggregator of the sum.in.ua text, which ULIF names as unlawful; verify each quoted passage against the official edition (inmo.org.ua/sum.html) before display.
- **Terms as found:**
  - «Створений кількома поколіннями лексикографів Інституту мовознавства ім. О. О. Потебні (А. А. Бурячок … Л. А. Юрчук та ін. – загалом понад 50 укладачів і редакторів). Паперовий оригінал вийшов у 11-ти томах (1970–1980).» (https://www.inmo.org.ua/sum.html, read 2026-09-27)
  - «© 2011 Інститут мовознавства ім. О.О. Потебні Національної академії наук України» (https://www.inmo.org.ua/sum.html, read 2026-09-27)
- **Also searched:** https://www.inmo.org.ua/sum.html (no licence text); https://sum.in.ua/ (unreachable; Wayback 2026-01-03 footer «© 2023, Webmezha», no terms page)
- **Per use:**
  - *russification_quote, russification_pair @ quotation* — One short quoted СУМ-11 passage per flagged entry, inside our critical commentary.
    - acquire: **assessed** — Normal use of the official edition for checking each quoted passage.
    - store: **assessed** — The passage is kept with its citation as part of our commentary.
    - transform: **assessed** — Quoted verbatim inside our own contrastive analysis; boundaries marked.
    - display: **assessed** — Quotation for a critical/polemical purpose (exposing russification), author and source named, boundaries marked.
    - redistribute: **unknown** — An opt-in dataset subset of quotations is systematic re-use; HELD until the Інститут мовознавства answers (outreach/inmo.md).
  - *russification_quote, russification_pair @ bulk* — The full sum11 table used to find candidates.
    - acquire: **assessed** — Extraction for research into russification, source cited, non-commercial; copy from an unauthorised aggregator is a residual risk.
    - store: **assessed** — Private store only.
    - transform: **assessed** — Internal comparison with modern sources to find candidates.
    - display: **unknown** — Never displayed at bulk scale (rule #M-6). HELD.
    - redistribute: **unknown** — Never redistributed at bulk scale. HELD.
- **Open questions:**
  - Will the Інститут мовознавства permit the opt-in russification-evidence dataset subset (contrastive pairs with short quotations)?
  - Replace the aggregator copy with passages checked against the official edition.
- **Contact:** Інститут мовознавства ім. О. О. Потебні НАН України — email or quick contact form · `inmo2006@ukr.net` · https://www.inmo.org.ua/sum.html (published at: https://www.inmo.org.ua/sum.html — «Інститут мовознавства ім. О.О. Потебні Національної академії наук України 01001, Київ, вул. Грушевського, 4 (044) 279-0292 (телефон) ... inmo2006@ukr.net»)
- **Outreach draft:** [`inmo.md`](outreach/inmo.md)

### ГРАК — Генеральний регіонально анотований корпус української мови — `grac`

- **Organisation:** Марія Шведова, Ruprecht von Waldenfels, Сергій Яригін, Андрій Рисін, Василь Старко та ін. (Kyiv, Lviv, Jena)
- **Role:** Modern example sentences and frequency for level gating.
- **Fields:** example_sentence, frequency_count, frequency_tier
- **Stored in:** live queries (scripts/rag/source_query.py, sketch.uacorpus.org corpus grac19a); data/lexicon/cache/grac_frequency.json
- **Licence as found:** No licence published; citation requested; texts remain under their authors' copyright
- **Conditions:** attribution — GRAC citation above, plus the author and title of the text each sentence comes from. Share-alike: unknown. Non-commercial: unknown.
- **Terms as found:**
  - «The corpus can be used for advanced study of the language as well as for writing textbooks, learner's dictionaries and exercises using examples from real texts» (https://uacorpus.org/en, read 2026-09-27)
  - «Просимо посилатися на ГРАК: Генеральний регіонально анотований корпус української мови (ГРАК) / М. Шведова, Р. фон Вальденфельс, С. Яригін, А. Рисін, В. Старко, Т. Ніколаєнко, А. Лукашевський та ін. — Київ, Львів, Єна, 2017–. — uacorpus.org.» (https://uacorpus.org/, read 2026-09-27)
- **Also searched:** https://uacorpus.org/informaciya-pro-grak, /rozrobniki, /poshuk-u-graku, /korpus-dlya-zavantazhennya-plug, /versiyi-korpusu, /slovniki, /en, https://sketch.uacorpus.org — no licence or redistribution statement
- **Per use:**
  - *example_sentence @ quotation* — One or a few short sentences per card, each attributed to its text and author.
    - acquire: **assessed** — Normal corpus use; GRAC states it is for writing learner's dictionaries and exercises with real examples.
    - store: **assessed** — Only the selected sentences with citation.
    - transform: **assessed** — Selection and cloze blanks; the sentence text is not altered.
    - display: **assessed** — Short attributed quotation for an informational/educational purpose; GRAC's stated purpose.
    - redistribute: **unknown** — No published redistribution terms; texts under authors' copyright. HELD until GRAC answers (outreach/grac.md).
  - *frequency_count @ bulk*
    - acquire: **assessed** — Per-lemma queries; extraction for educational use, source cited.
    - store: **assessed** — Private cache.
    - transform: **assessed** — Converted into our own coarse tiers.
    - display: **unknown** — Raw counts for every card are re-use of corpus data; not needed. HELD.
    - redistribute: **unknown** — HELD until GRAC answers.
  - *frequency_tier @ bulk* — Our own coarse tier (e.g. top-1k, top-5k) computed from the counts.
    - acquire: **assessed** — Derived by us from the counts row.
    - store: **assessed** — Our own derived value.
    - transform: **assessed** — Our own computation.
    - display: **assessed** — Our own classification, cited as based on GRAC; no corpus content shown.
    - redistribute: **unknown** — Tiers for the whole lexicon mirror the frequency ranking; ask GRAC before shipping. HELD.
- **Open questions:**
  - May attributed example sentences (and our frequency tiers) be redistributed in the dataset under CC BY-NC-SA 4.0?
- **Contact:** Марія Шведова, project lead (communication) · `corpus.textiv@gmail.com` · https://uacorpus.org/informaciya-pro-grak/rozrobniki (published at: https://uacorpus.org/informaciya-pro-grak/rozrobniki — «Марія Шведова – Керівниця проєкту… комунікацію (corpus.textiv@gmail.com)»)
- **Outreach draft:** [`grac.md`](outreach/grac.md)

### UA-GEC — Ukrainian grammatical error correction corpus — `ua_gec`

- **Organisation:** Grammarly (Syvokon, Nahorna, Kuchmiichuk, Osidach)
- **Role:** Error→correction pairs (calques, case, gender) for common-mistake notes.
- **Fields:** error_text, correction_text, error_type
- **Stored in:** data/sources.db ua_gec_errors, ua_gec_errors_fts
- **Licence as found:** CC BY 4.0
- **Conditions:** attribution — UA-GEC (Syvokon, Nahorna, Kuchmiichuk, Osidach, UNLP 2023), https://github.com/grammarly/ua-gec, CC BY 4.0, changes indicated. Share-alike: no. Non-commercial: no.
  - scripts/ingest/ua_gec_ingest.py says "MIT licensed" — wrong; fix in the follow-up.
- **Terms as found:**
  - «Attribution 4.0 International» — The repository LICENSE is the CC BY 4.0 legal code (no ShareAlike, no NonCommercial). (https://github.com/grammarly/ua-gec/blob/main/LICENSE, read 2026-09-27)
- **Per use:**
  - *error_text, correction_text, error_type @ bulk*
    - acquire: **permitted** — CC BY 4.0
    - store: **permitted** — CC BY 4.0
    - transform: **permitted** — CC BY 4.0
    - display: **permitted** — CC BY 4.0 with attribution
    - redistribute: **permitted** — CC BY 4.0; may sit inside a BY-NC-SA dataset with attribution.
- **Contact:** Authors listed in the README · `oleksiy.syvokon@gmail.com` · https://github.com/grammarly/ua-gec (published at: https://github.com/grammarly/ua-gec README (also nastasiya.osidach@grammarly.com, olena.nahorna@grammarly.com, pavlo.kuchmiichuk@gmail.com))

### Ukrajinet (Ukrainian WordNet) — `ukrajinet`

- **Organisation:** Melanie Siegel, Maksym Vakulenko (Hochschule Darmstadt)
- **Role:** Synonym candidates (quality caveat — largely auto-translated from Open English WordNet).
- **Fields:** synset_members
- **Stored in:** data/sources.db ukrajinet(synset_id, words, text)
- **Licence as found:** CC BY-SA 4.0
- **Conditions:** attribution — Ukrajinet, Melanie Siegel & Maksym Vakulenko, https://github.com/hdaSprachtechnologie/ukrajinet, CC BY-SA 4.0. Share-alike: yes. Non-commercial: no.
  - BY-SA adaptations must stay BY-SA — ship in a separately licensed file, never merged into BY-NC-SA records.
- **Terms as found:**
  - «This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/» (https://github.com/hdaSprachtechnologie/ukrajinet, read 2026-09-27)
- **Per use:**
  - *synset_members @ bulk*
    - acquire: **permitted** — CC BY-SA 4.0
    - store: **permitted** — CC BY-SA 4.0
    - transform: **permitted** — CC BY-SA 4.0; adaptation stays BY-SA.
    - display: **permitted** — CC BY-SA 4.0 with attribution
    - redistribute: **permitted** — CC BY-SA 4.0 — only in a BY-SA-licensed file of the release.
- **Contact:** Melanie Siegel (email in the ukrajinet.xml header) · `melanie.siegel@h-da.de` · https://github.com/hdaSprachtechnologie/ukrajinet (published at: ukrajinet.xml header email="melanie.siegel@h-da.de")

### Вікісловник (Ukrainian Wiktionary) dumps — `wiktionary`

- **Organisation:** Wiktionary contributors / Wikimedia Foundation
- **Role:** Definitions, synonyms, antonyms, etymology hints.
- **Fields:** definition_text, synonyms, antonyms, etymology_text
- **Stored in:** data/sources.db wiktionary, wiktionary_etymology (dumps.wikimedia.org/ukwiktionary)
- **Licence as found:** CC BY-SA 4.0 (and GFDL)
- **Conditions:** attribution — Link to the reused page(s) or list of authors, plus a CC BY-SA 4.0 licence notice (Terms of Use). Share-alike: yes. Non-commercial: no.
  - BY-SA — separate licensed file in the release.
- **Terms as found:**
  - «Creative Commons Attribution-ShareAlike 4.0 International License ("CC BY-SA 4.0"), and GNU Free Documentation License ("GFDL") ... Reusers may comply with either license or both.» (https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use, read 2026-09-27)
  - «all original textual content is licensed under the GNU Free Documentation License (GFDL) and the Creative Commons Attribution-Share-Alike 4.0 License. Some text may be available only under the Creative Commons license» (https://dumps.wikimedia.org/legal.html, read 2026-09-27)
- **Also searched:** https://uk.wiktionary.org/wiki/Вікісловник:Авторське_право (404)
- **Per use:**
  - *definition_text, synonyms, antonyms, etymology_text @ bulk*
    - acquire: **permitted** — CC BY-SA 4.0
    - store: **permitted** — CC BY-SA 4.0
    - transform: **permitted** — CC BY-SA 4.0; adaptation stays BY-SA.
    - display: **permitted** — With page link and licence notice.
    - redistribute: **permitted** — CC BY-SA 4.0 — only in a BY-SA-licensed file of the release.
- **Contact:** n/a (community licence); Wikimedia Foundation legal contact via the Terms of Use page · https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use

### Kaikki.org Wiktextract extract (English Wiktionary, Ukrainian entries) — `kaikki`

- **Organisation:** Tatu Ylonen (Wiktextract) / English Wiktionary contributors
- **Role:** Second English-gloss source, IPA and fallback etymology (commit ca2c3a50e1).
- **Fields:** en_gloss, ipa, etymology_text
- **Stored in:** data/lexicon/kaikki_uk_lookup.json, data/lexicon/side/kaikki.sqlite
- **Licence as found:** CC BY-SA 4.0 (and GFDL)
- **Conditions:** attribution — English Wiktionary (via kaikki.org / Wiktextract, Ylonen 2022), CC BY-SA 4.0, link to the entry page. LICENSE-CONTENT.md says CC BY-SA 3.0 — update to 4.0. Share-alike: yes. Non-commercial: no.
- **Terms as found:**
  - «This data is made available under the same licenses as Wiktionary - both CC-BY-SA and GFDL. See Wiktionary copyright page for more information.» (https://kaikki.org/dictionary/, read 2026-09-27)
  - «The original texts of Wiktionary entries are dual-licensed to the public under both the Creative Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA) and the GNU Free Documentation License (GFDL).» (https://en.wiktionary.org/wiki/Wiktionary:Copyrights, read 2026-09-27)
- **Per use:**
  - *en_gloss, ipa, etymology_text @ bulk*
    - acquire: **permitted** — CC BY-SA 4.0
    - store: **permitted** — CC BY-SA 4.0
    - transform: **permitted** — Adaptation stays BY-SA.
    - display: **permitted** — With attribution and licence notice.
    - redistribute: **permitted** — Only in a BY-SA-licensed file of the release.
- **Contact:** n/a (community licence); Wiktextract issues on GitHub · https://kaikki.org/dictionary/rawdata.html

### dmklinger/ukrainian dictionary (UK→EN) — `dmklinger`

- **Organisation:** GitHub user dmklinger
- **Role:** First-choice English gloss for Atlas and lesson evidence.
- **Fields:** en_gloss
- **Stored in:** data/sources.db dmklinger_uk_en, data/lexicon/side/dmklinger.sqlite
- **Licence as found:** CC BY-SA 3.0 Unported
- **Conditions:** attribution — dmklinger/ukrainian (from Wiktionary and DBnary), https://github.com/dmklinger/ukrainian, CC BY-SA 3.0. Share-alike: yes. Non-commercial: no.
  - BY-SA 3.0 adaptations may be licensed BY-SA 4.0 (CC compatibility page); never use its ULIF-derived forms.
- **Terms as found:**
  - «This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.» (https://github.com/dmklinger/ukrainian/blob/main/license.txt, read 2026-09-27)
  - «All data scraped from wiktionary and [dbnary]… Forms filled in from [here](https://lcorp.ulif.org.ua/dictua/dictua.aspx)» — Glosses come from Wiktionary/DBnary; word forms from ULIF (we do not use the forms). (https://github.com/dmklinger/ukrainian, read 2026-09-27)
- **Per use:**
  - *en_gloss @ bulk*
    - acquire: **permitted** — CC BY-SA 3.0
    - store: **permitted** — CC BY-SA 3.0
    - transform: **permitted** — Adaptation stays BY-SA (3.0 or later).
    - display: **permitted** — With attribution
    - redistribute: **permitted** — Only in a BY-SA-licensed file of the release.
- **Open questions:**
  - DBnary's own licence was not checked; confirm before the dataset release.
- **Contact:** GitHub issues only (no contact published) · https://github.com/dmklinger/ukrainian/issues

### Горох (goroh.pp.ua) — `goroh`

- **Organisation:** Горох (operator not named on the site)
- **Role:** Live English-gloss fallback and a small etymology stub table.
- **Fields:** en_gloss, etymology_text
- **Stored in:** data/sources.db goroh_etymology (41 rows), live lookups in scripts/rag/source_query.py
- **Licence as found:** No reuse licence; ULIF names goroh.pp.ua as an unlawful СУМ copy
- **Conditions:** attribution — Never shown as an authority; attribute the underlying work (atlas-source-presentation.md). Share-alike: unknown. Non-commercial: unknown.
- **Terms as found:**
  - «ми готові вилучати з бібліотечного фонду ті твори авторів, щодо вільного поширення яких є заперечення законних власників авторського права … Для цього автору чи правовласнику необхідно в довільній письмовій електронній формі повідомити про це нас.» — Goroh relies on the library law and removes works on the rights holder's objection; it grants no reuse licence. (https://web.archive.org/web/20260730145350id_/https://goroh.pp.ua/Copyright, read 2026-09-27)
- **Also searched:** https://goroh.pp.ua/ (live Cloudflare 403; Wayback 2026-09-24 used)
- **Per use:**
  - *en_gloss, etymology_text @ lookup*
    - acquire: **assessed** — Reading a public page.
    - store: **assessed** — Insubstantial parts.
    - transform: **assessed** — Checking only.
    - display: **unknown** — The site grants nothing and its content belongs to other publishers. HELD — use the original work's row.
    - redistribute: **unknown** — HELD.
  - *en_gloss, etymology_text @ bulk*
    - acquire: **unknown** — No reuse grant; systematic per-lemma fetching. HELD.
    - store: **unknown** — HELD (goroh_etymology table: replace with the original source).
    - transform: **unknown** — HELD.
    - display: **unknown** — HELD.
    - redistribute: **unknown** — HELD.
- **Open questions:**
  - Which original works does Горох's etymology and translation content come from? Use those rows instead.
- **Contact:** Feedback form, Instagram goroh_ua, Telegram @goroh_bot; no email, operator or address published · https://goroh.pp.ua/feedback (published at: https://web.archive.org/web/20260730145350id_/https://goroh.pp.ua/Copyright («Пишіть через форму зворотного зв'язку чи в інстаграм»))

### mphdict — «Цифрові лексикографічні системи української мови» (etym.db, synsets_ua.db) — `mphdict`

- **Organisation:** uSofTrod (LinguisticAndInformationSystems/mphdict)
- **Role:** Atlas etymology (ЕСУМ-derived database) and synonym chips (Словник синонімів).
- **Fields:** etymology_text, synonym_groups
- **Stored in:** data/mphdict/etym.db, data/mphdict/synsets_ua.db
- **Licence as found:** ODbL 1.0 (database) / DbCL 1.0 (contents) as far as uSofTrod holds rights; ЕСУМ text rights stay with the Інститут мовознавства
- **Conditions:** attribution — mphdict, uSofTrod (ODbL 1.0 / DbCL 1.0), https://github.com/LinguisticAndInformationSystems/mphdict; ЕСУМ © Інститут мовознавства ім. О. О. Потебні НАН України. Share-alike: yes. Non-commercial: no.
  - ODbL share-alike applies to derived databases; its compatibility with a CC BY-NC-SA dataset is not settled — keep in a separate file if ever permitted.
- **Terms as found:**
  - «База даних "etym.db" доступна під ліцензією Open Database License http://opendatacommons.org/licenses/odbl/1.0/. Будь-які права на вміст (контент) цієї бази даних ліцензовано під ліцензією Database Contents License https://opendatacommons.org/licenses/dbcl/1.0/.» — The same ODbL/DbCL sentence is given for synsets_ua.db. (https://github.com/LinguisticAndInformationSystems/mphdict, read 2026-09-27)
  - «Ми не надаємо доступ до твору Етимологічний словник української мови Інституту мовознавства ім. О.О. Потебні НАН України, а в освітніх цілях демонструємо можливість роботи зі складноструктурованою БД етимологічної системи, яка є нашою оригінальною розробкою.» — "We do not provide access to the work ЕСУМ of the Potebnia Institute; for educational purposes we demonstrate working with the database structure, which is our original development." — the ODbL covers uSofTrod's database, not the ЕСУМ text. (https://github.com/LinguisticAndInformationSystems/mphdict, read 2026-09-27)
- **Per use:**
  - *etymology_text, synonym_groups @ bulk*
    - acquire: **permitted** — ODbL/DbCL for uSofTrod's database.
    - store: **permitted** — ODbL/DbCL
    - transform: **permitted** — ODbL/DbCL
    - display: **unknown** — uSofTrod itself says it does not give access to the ЕСУМ work; the synonym groups come from a dictionary whose rights holder is not named. HELD until the Інститут мовознавства answers (outreach/inmo.md).
    - redistribute: **unknown** — Same. HELD.
- **Open questions:**
  - Which printed synonym dictionary is synsets_ua.db built from, and who holds its rights?
- **Contact:** uSofTrod by email · `uSofTrod@outlook.com` · https://github.com/LinguisticAndInformationSystems/mphdict (published at: README — «Copyright © 2016-2021 uSofTrod. Contacts: uSofTrod@outlook.com»)
- **Outreach draft:** [`inmo.md`](outreach/inmo.md)

### Балла М. І. «Англо-український словник» — `balla`

- **Organisation:** Author М. І. Балла and publishers (Освіта 1996; Чумацький Шлях 2007); digital copy via the bakustarver aggregator
- **Role:** English-gloss fallback (reverse lookup) and EN→UK translation help.
- **Fields:** en_uk_translation
- **Stored in:** data/sources.db balla_en_uk, data/lexicon/side/balla_reverse.sqlite
- **Licence as found:** All rights reserved (in-print modern dictionary); LICENSE-CONTENT.md "copyright expired" is unsupported
- **Conditions:** attribution — Балла М. І. Англо-український словник. Share-alike: unknown. Non-commercial: unknown.
- **Also searched:** https://github.com/bakustarver/ukr-dictionaries-list-opensource (AGPL-3.0 repo; no grant from the dictionary's rights holders); https://archive.org/details/enukr1996 (no rights field); https://knygy.com.ua/index.php?productID=9789668272172 (2007 edition on sale)
- **Per use:**
  - *en_uk_translation @ bulk*
    - acquire: **assessed** — Internal research copy, operator decision 2026-09-27 (#8976) to prepare in advance; aggregator copy, residual risk.
    - store: **assessed** — Private store only.
    - transform: **assessed** — Internal lookups only.
    - display: **unknown** — No grant; rights holder not identified. HELD — prefer open gloss sources.
    - redistribute: **unknown** — HELD.
- **Open questions:**
  - Who holds the rights today (author's heirs or publisher)? Not needed if open gloss sources cover the words.
- **Contact:** unknown — no rights holder contact found

### ПУЛЬС — Профіль української лексики — `puls`

- **Organisation:** Школа української мови та культури УКУ (О. Синчак, В. Старко, М. Бурак, М. Свистун та ін.)
- **Role:** CEFR level per word for level gating.
- **Fields:** cefr_level
- **Stored in:** data/sources.db puls_cefr, data/puls/entries.jsonl (scraped by scripts/rag/scrape_puls.py)
- **Licence as found:** All rights reserved
- **Conditions:** attribution — PULS citation above. Share-alike: unknown. Non-commercial: unknown.
- **Terms as found:**
  - «© 2026 Пульс. Всі права захищено.» (https://puls.peremova.org/, read 2026-09-27)
  - «Просимо посилатися на ПУЛЬС: Профіль української лексики (ПУЛЬС) / О. Синчак, В. Старко, М. Бурак, М. Свистун та ін. Львів: Школа української мови та культури УКУ, 2026. — puls.peremova.org» (https://puls.peremova.org/, read 2026-09-27)
- **Also searched:** https://jakelawrence.xyz/research/ukrainian-frequency (secondhand "by permission, CC BY-NC-SA 4.0" for another project — not a grant to us)
- **Per use:**
  - *cefr_level @ bulk*
    - acquire: **assessed** — Extraction for educational use, source cited; operator decision 2026-09-27 to prepare in advance.
    - store: **assessed** — Private store.
    - transform: **assessed** — Internal level gating of practice.
    - display: **unknown** — A PULS level on every card is systematic re-use of an all-rights-reserved database. HELD until PULS answers (outreach/puls.md).
    - redistribute: **unknown** — HELD.
- **Open questions:**
  - PULS reportedly licenses levels to another project under BY-NC-SA 4.0 by permission — ask for the same.
- **Contact:** Олена Синчак (cooperation) · `o_synchak@ucu.edu.ua` · https://puls.peremova.org/p/contacts (published at: https://puls.peremova.org/p/contacts — «З питань співпраці, будь ласка, пишіть сюди: o_synchak@ucu.edu.ua (Олена Синчак)»)
- **Outreach draft:** [`puls.md`](outreach/puls.md)

### UberText 2.0 frequency dictionary (ubertext_freq.csv.xz) — `ubertext_freq`

- **Organisation:** lang-uk (Дмитро Чаплинський)
- **Role:** Frequency for level gating.
- **Fields:** frequency_count, frequency_tier
- **Stored in:** data/ubertext-freq/frequency.db
- **Licence as found:** Not found
- **Conditions:** attribution — Chaplynskyi D. Introducing UberText 2.0: A Corpus of Modern Ukrainian at Scale. UNLP 2023. Share-alike: unknown. Non-commercial: unknown.
- **Also searched:** https://lang.org.ua/en/ubertext/ (no licence statement); https://lang.org.ua/en/corpora/ (its CC BY-NC-SA line belongs to the NER corpus, not UberText); https://aclanthology.org/2023.unlp-1.1.pdf (paper lists "Freely available for download under a permissive license" as a design goal; no licence named); huggingface.co/datasets/lang-uk/UberText-2.0 (auth error)
- **Per use:**
  - *frequency_count @ bulk*
    - acquire: **assessed** — Public download for research/education, source cited.
    - store: **assessed** — Private store.
    - transform: **assessed** — Converted into our own tiers.
    - display: **unknown** — Not needed; HELD.
    - redistribute: **unknown** — No licence found. HELD until lang-uk answers (outreach/lang_uk.md).
  - *frequency_tier @ bulk*
    - acquire: **assessed** — Derived by us from the counts row.
    - store: **assessed** — Our own derived value.
    - transform: **assessed** — Our own computation.
    - display: **assessed** — Our own coarse classification, cited as based on UberText 2.0.
    - redistribute: **unknown** — Tiers for the whole lexicon mirror the ranking; ask first. HELD.
- **Open questions:**
  - Which licence covers ubertext_freq.csv.xz?
- **Contact:** lang-uk via GitHub (email on lang.org.ua is obfuscated) · https://github.com/lang-uk
- **Outreach draft:** [`lang_uk.md`](outreach/lang_uk.md)

### r2u.org.ua / e2u.org.ua bilingual dictionary portals — `r2u_e2u`

- **Organisation:** Андрій Рисін, Василь Старко, Ю. Марченко, О. Телемко та ін. (constituent dictionaries by their own authors)
- **Role:** Live RU/EN↔UK lookups and a short English-gloss fallback (e2u).
- **Fields:** en_gloss
- **Stored in:** live lookups only (scripts/rag/source_query.py); nothing stored in bulk
- **Licence as found:** All rights reserved (© r2u.org.ua; per-dictionary author permissions)
- **Conditions:** attribution — Name the constituent dictionary and its authors, and the portal. Share-alike: unknown. Non-commercial: unknown.
- **Terms as found:**
  - «© 2026 r2u.org.ua» (https://r2u.org.ua/, read 2026-09-27)
  - «Дякуємо авторському колективу за наданий текст словника й дозвіл на його електронну публікацію» — The authors permitted e2u's electronic publication — a grant to e2u, not to us. (https://e2u.org.ua/, read 2026-09-27)
- **Also searched:** https://r2u.org.ua/contacts, https://e2u.org.ua/contacts
- **Per use:**
  - *en_gloss @ lookup*
    - acquire: **assessed** — Reading a public page.
    - store: **assessed** — Insubstantial parts.
    - transform: **assessed** — Checking only.
    - display: **unknown** — A short gloss on many cards is systematic re-use. HELD until the maintainers answer (outreach/r2u_e2u.md).
    - redistribute: **unknown** — HELD.
- **Open questions:**
  - Would the maintainers (also VESUM's) allow short e2u glosses on cards, per constituent dictionary?
- **Contact:** GitHub issues or forum · https://github.com/brown-uk/e2u.org.ua/issues (published at: https://e2u.org.ua/contacts (Форум https://r2u.org.ua/forum; github https://github.com/brown-uk/e2u.org.ua/issues); r2u contacts page lists https://github.com/brown-uk/r2u.org.ua/issues)
- **Outreach draft:** [`r2u_e2u.md`](outreach/r2u_e2u.md)

### Wikidata (lexemes and items) — `wikidata`

- **Organisation:** Wikidata contributors / Wikimedia Foundation
- **Role:** English-gloss fallback.
- **Fields:** en_gloss
- **Stored in:** live lookups only
- **Licence as found:** CC0 1.0
- **Conditions:** attribution — Courtesy credit "Wikidata" (not required). Share-alike: no. Non-commercial: no.
- **Terms as found:**
  - «structured data in the main, Property, Lexeme, and EntitySchema namespaces are waived using the Creative Commons Zero (CC0)» (https://dumps.wikimedia.org/legal.html, read 2026-09-27)
- **Per use:**
  - *en_gloss @ bulk*
    - acquire: **permitted** — CC0
    - store: **permitted** — CC0
    - transform: **permitted** — CC0
    - display: **permitted** — CC0
    - redistribute: **permitted** — CC0
- **Contact:** n/a (CC0)

### lang-uk/ukrainian-word-stress (stress dictionary trie) — `ukrainian_word_stress`

- **Organisation:** lang-uk
- **Role:** Stress marks on forms where VESUM/ULIF are silent.
- **Fields:** stress
- **Stored in:** installed Python package (bundled trie)
- **Licence as found:** MIT
- **Conditions:** attribution — ukrainian-word-stress (lang-uk), MIT licence notice. Share-alike: no. Non-commercial: no.
- **Terms as found:**
  - «MIT License Copyright (c) 2022 lang-uk» (https://github.com/lang-uk/ukrainian-word-stress/blob/main/LICENSE, read 2026-09-27)
- **Also searched:** README gives no origin for the bundled stress dictionary
- **Per use:**
  - *stress @ bulk*
    - acquire: **permitted** — MIT
    - store: **permitted** — MIT
    - transform: **permitted** — MIT
    - display: **permitted** — MIT
    - redistribute: **permitted** — MIT with the licence notice.
- **Open questions:**
  - Where does the bundled stress data come from? If from a non-open dictionary, the MIT grant may not reach it.
- **Contact:** GitHub issues · https://github.com/lang-uk/ukrainian-word-stress/issues

### The operator's teacher's materials (Combined Master Vocabulary Table, lesson texts) — `teacher_materials`

- **Organisation:** The operator's Ukrainian teacher (author); private DOCX supplied by the operator
- **Role:** Teacher vocabulary deck, the teacher's English meanings, reviewed lesson sentences for cloze.
- **Fields:** vocabulary_list, en_meaning_teacher, lesson_sentence
- **Stored in:** data/sources.db textbooks rows with source_file=private-teacher-lessons-a (scripts/ingest/private_teacher_lessons_ingest.py); site/src/data/lexicon-teacher-table-deck.json (scripts/lexicon/sync_teacher_table_deck.py)
- **Licence as found:** No licence; publication on the site allowed by operator decision 2026-09-27 (relayed)
- **Conditions:** attribution — No personal names in public (docs/practice/curated-membership-and-sources.md); credit form to be chosen by the teacher. Share-alike: unknown. Non-commercial: unknown.
  - Lesson sentences publish only after language review and the operator's privacy scan (#8843) — lesson logs may contain the learner's own attempts.
- **Terms as found:**
  - «cloze: 'sentences from the teacher''s lesson texts (operator 2026-09-27: allowed, including publication)'» — Operator decision recorded on the teacher-deck task card. (https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8843, read 2026-09-27)
  - «the word list is public by operator decision; example sentences may come from her lessons or from books» (https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8843, read 2026-09-27)
- **Per use:**
  - *vocabulary_list, en_meaning_teacher, lesson_sentence @ bulk*
    - acquire: **permitted** — Supplied by the operator for this use.
    - store: **permitted** — Operator decision.
    - transform: **permitted** — Light adaptation into practice items (operator direction 2026-09-26, #8843).
    - display: **permitted** — Publication allowed (word list; reviewed, privacy-scanned sentences).
    - redistribute: **unknown** — Site publication was allowed; open licensing in the dataset (CC BY-NC-SA 4.0, reusable by anyone) was not asked. HELD — operator to confirm with the teacher.
- **Open questions:**
  - Has the teacher personally agreed in writing? The register records the operator's relayed decision.
  - May the teacher's list, English meanings and reviewed sentences go into the open dataset under CC BY-NC-SA 4.0?
- **Contact:** Through the operator (the teacher's details are private)

### Learn Ukrainian project — course-authored glosses, classifications and curation overlay — `course_authored`

- **Organisation:** Learn Ukrainian project (maintainer Krisztian Koos)
- **Role:** Headline English glosses from curriculum vocabulary files, CEFR/course usage, curation decisions, russification commentary.
- **Fields:** en_gloss_course, course_usage, curation_overlay, russification_commentary
- **Stored in:** curriculum/l2-uk-en/*/vocabulary.yaml, data/atlas.db, site lexicon shards
- **Licence as found:** CC BY-SA 4.0 (project content)
- **Conditions:** attribution — Learn Ukrainian project, https://github.com/learn-ukrainian/learn-ukrainian.github.io Share-alike: yes. Non-commercial: no.
  - The maintainer can also license this content under CC BY-NC-SA 4.0 for the dataset (a rights holder may dual-license); an operator decision.
- **Terms as found:**
  - «The curriculum content (Ukrainian prose, dialogues, exercises, wiki articles, plans, translations, and explanations authored for this project) is licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).» (https://github.com/learn-ukrainian/learn-ukrainian.github.io/blob/main/LICENSE-CONTENT.md, read 2026-09-27)
- **Per use:**
  - *en_gloss_course, course_usage, curation_overlay, russification_commentary @ bulk*
    - acquire: **permitted** — Own work
    - store: **permitted** — Own work
    - transform: **permitted** — Own work
    - display: **permitted** — Own work
    - redistribute: **permitted** — Own work, CC BY-SA 4.0 (or dual-licensed for the dataset).
- **Contact:** GitHub repository issues · https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues

### Українська Вікіпедія (cached articles) — `wikipedia`

- **Organisation:** Wikipedia contributors / Wikimedia Foundation
- **Role:** Background for encyclopedic words (listed in the current dataset attribution).
- **Fields:** article_extract
- **Stored in:** data/sources.db wikipedia
- **Licence as found:** CC BY-SA 4.0 (and GFDL)
- **Conditions:** attribution — Link to the article (history) and CC BY-SA 4.0 notice. Share-alike: yes. Non-commercial: no.
- **Terms as found:**
  - «Creative Commons Attribution-ShareAlike 4.0 International License ("CC BY-SA 4.0"), and GNU Free Documentation License ("GFDL") ... Reusers may comply with either license or both.» (https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use, read 2026-09-27)
- **Per use:**
  - *article_extract @ bulk*
    - acquire: **permitted** — CC BY-SA 4.0
    - store: **permitted** — CC BY-SA 4.0
    - transform: **permitted** — Adaptation stays BY-SA.
    - display: **permitted** — With link and licence notice
    - redistribute: **permitted** — Only in a BY-SA-licensed file of the release.
- **Contact:** n/a (community licence) · https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use

### «Етимологічний словник української мови» (ЕСУМ), vols 1–6 (1982–2012) — `esum`

- **Organisation:** Інститут мовознавства ім. О. О. Потебні НАН України (publisher Наукова думка); co-authored by many compilers
- **Role:** Etymology notes and cognate forms on cards.
- **Fields:** etymology_text, cognate_forms
- **Stored in:** data/sources.db esum_etymology, esum_etymology_meta, esum_cognate_forms (OCR of archive.org items etslukrmov1–6; scripts/ingest/esum_ingest.py, scripts/etymology/)
- **Licence as found:** In copyright (co-authored, vol. 6 published 2012 — Art. 31(4)); rights holder not confirmed (Institute and/or Наукова думка)
- **Conditions:** attribution — Етимологічний словник української мови / Інститут мовознавства ім. О. О. Потебні НАН України. Т. <vol>, с. <page>. Share-alike: unknown. Non-commercial: unknown.
  - Our text is our own OCR of a third-party upload; the TDM exception (Art. 22(2)(14)) is narrow and does not cover a learner product.
- **Terms as found:**
  - «Етимологічний словник української мови: В 7 т. / Редкол.: О. С. Мельничук (гол. ред.) та ін. – К.: Наук. думка, 1982–2006.» — The Institute lists ЕСУМ as its publication; no reuse statement anywhere on its site. (https://www.inmo.org.ua/library.html, read 2026-09-27)
  - «Укладачі: Г. П. Півторак, О. Д. Пономарів, І. A. Стоянов, О. Б. Ткаченко, A. M. Шамота … — К.: Наукова думка, 2012» — Volume 6 (2012) on archive.org — a user upload in the folkscanomy collection with empty rights fields. (https://archive.org/details/etslukrmov6, read 2026-09-27)
- **Also searched:** https://www.inmo.org.ua/ (no licence or reuse statement); https://archive.org/about/terms (JavaScript-only; not read)
- **Per use:**
  - *etymology_text, cognate_forms @ bulk*
    - acquire: **assessed** — Extraction for educational/research use, source cited, non-commercial; operator decision 2026-09-27 (#8976) to prepare in advance; third-party scans are a residual risk.
    - store: **assessed** — Private store only.
    - transform: **assessed** — Internal parsing and cognate extraction.
    - display: **unknown** — ЕСУМ text on every card is systematic re-use of a copyrighted work. HELD until the Institute answers (outreach/inmo.md).
    - redistribute: **unknown** — HELD.
  - *etymology_text @ quotation* — A lesson or article quoting one ЕСУМ entry, attributed and marked — not the Atlas at scale.
    - acquire: **assessed** — Checked against the published volume.
    - store: **assessed** — Insubstantial part.
    - transform: **assessed** — Quoted, not altered.
    - display: **assessed** — Quotation for a scientific/informational purpose, author and source named.
    - redistribute: **unknown** — Not needed at this scale. HELD.
- **Open questions:**
  - Who holds the economic rights in ЕСУМ today — the Institute, Наукова думка, or the compilers?
- **Contact:** Інститут мовознавства ім. О. О. Потебні НАН України · `inmo2006@ukr.net` · https://www.inmo.org.ua/ (published at: https://www.inmo.org.ua/ — «01001, Київ, вул. Грушевського, 4 (044) 279-0292 ( телефон ) (044) 278-7182 ( факс ) inmo2006@ukr.net»)
- **Outreach draft:** [`inmo.md`](outreach/inmo.md)

### Ukrainian school textbooks (grades 1–11) in sources.db — `textbooks`

- **Organisation:** Individual authors and publishers (e.g. Заболотний, Авраменко, Вашуленко, Карман, Літвінова, Глазова); PDFs via pidruchnyk.com.ua and lib.imzo.gov.ua
- **Role:** Short modern example sentences (class B — short quotations only,
- **Fields:** example_sentence, textbook_chunk
- **Stored in:** data/sources.db textbooks (public rows), textbook_sections; bulk root textbook_chunks/grade-*
- **Licence as found:** In copyright (authors/publishers); free public access by law, no reuse licence
- **Conditions:** attribution — Author(s), title, grade, publisher, year, page — for every quoted sentence. Share-alike: unknown. Non-commercial: unknown.
  - LICENSE-CONTENT.md caps direct quotations at ~200 characters.
- **Terms as found:**
  - «на якому у вільному доступі в повному обсязі розміщуються безкоштовні електронні версії підручників» — lib.imzo.gov.ua exists under Art. 75 of the Law on Education to publish full free electronic textbooks — free ACCESS, not a reuse licence (Wayback snapshot 2026-01-03). (https://web.archive.org/web/20260103144939id_/https://lib.imzo.gov.ua/, read 2026-09-27)
  - «Файли надані для ознайомлення.» — pidruchnyk.com.ua (third-party mirror) — "files provided for familiarisation". (https://pidruchnyk.com.ua/, read 2026-09-27)
- **Also searched:** https://shkola.in.ua/polityka/ (privacy policy only); https://zakon.rada.gov.ua/laws/show/2145-19/print (Law on Education, Art. 75(6)-(7))
- **Per use:**
  - *example_sentence @ quotation* — At most a few short attributed sentences per card.
    - acquire: **assessed** — Free public access by law.
    - store: **assessed** — Only the selected sentence with its citation.
    - transform: **assessed** — Cloze blank only; text not rewritten.
    - display: **assessed** — Short quotation, informational/educational purpose, author and source named, boundaries marked.
    - redistribute: **unknown** — Thousands of textbook quotations in a downloadable dataset go beyond quotation for a purpose. HELD.
  - *textbook_chunk @ bulk* — Internal retrieval context only; never published.
    - acquire: **assessed** — Free public access by law.
    - store: **assessed** — Private retrieval index; operator decision (LICENSE-CONTENT.md fair-use boundaries); no statutory exception fits exactly — residual risk.
    - transform: **assessed** — Chunking and indexing for retrieval, internal only.
    - display: **unknown** — Never displayed. HELD.
    - redistribute: **unknown** — Never redistributed. HELD.
- **Open questions:**
  - Does any textbook publisher grant a reuse licence (e.g. for NUS textbooks funded by the state budget)?
- **Contact:** Per publisher (no single rights holder); pidruchnyk.com.ua feedback form for mirror issues · https://pidruchnyk.com.ua/index.php?do=feedback

### «Український фразеологічний словник» (aggregator copy; probably «Словник фразеологізмів української мови», Наукова думка 2003) — `frazeolohichnyi`

- **Organisation:** Compilers (Білоноженко В. М. та ін.) / publisher Наукова думка — rights holder not confirmed
- **Role:** Idiom verification; ULIF phraseology is the planned idiom source (#8985).
- **Fields:** idiom, idiom_definition
- **Stored in:** data/sources.db frazeolohichnyi (bakustarver file fl.frasesUkUk.json)
- **Licence as found:** In copyright (co-authored, 2003); no licence found
- **Conditions:** attribution — Словник фразеологізмів української мови / відп. ред. В. О. Винник. Київ: Наукова думка, 2003 (to be confirmed). Share-alike: unknown. Non-commercial: unknown.
- **Also searched:** https://github.com/bakustarver/ukr-dictionaries-list-opensource (AGPL-3.0 repo; no provenance; Info names «Український Фразелогічний Словник»); https://archive.org/details/slov557 (sample entries match the 2003 edition; no rights field)
- **Per use:**
  - *idiom, idiom_definition @ bulk*
    - acquire: **assessed** — Internal research copy, operator decision 2026-09-27 (#8976); aggregator copy, residual risk.
    - store: **assessed** — Private store only.
    - transform: **assessed** — Internal cross-checks only.
    - display: **unknown** — No grant. HELD — use ULIF phraseology once permitted.
    - redistribute: **unknown** — HELD.
- **Open questions:**
  - Confirm the edition; if the Інститут української мови is the rights holder, route via ukrmov@gmail.com (https://iul-nasu.org.ua/pro-instytut/kontaktna-informatsiya.html).
- **Contact:** Probably the Інститут української мови НАН України (not confirmed) · `ukrmov@gmail.com` · https://iul-nasu.org.ua/pro-instytut/kontaktna-informatsiya.html

### Антоненко-Давидович Б. «Як ми говоримо» — `antonenko_style_guide`

- **Organisation:** Heirs of Борис Антоненко-Давидович (d. 9 May 1984) — no contact found
- **Role:** Authority on russianisms and calques for correction notes.
- **Fields:** style_rule_quote, style_entry_text
- **Stored in:** data/sources.db style_guide(word, section, text); full text in textbooks (scripts/ingest/antonenko_full_book_ingest.py)
- **Licence as found:** In copyright until 31 Dec 2054 (Art. 31(2)); rights with the heirs
- **Conditions:** attribution — Антоненко-Давидович Б. Як ми говоримо. <edition, year, page>. Share-alike: unknown. Non-commercial: unknown.
- **Terms as found:**
  - «(…23. 07(05. 08). 1899, с. Засулля … — 09. 05. 1984, Київ)» — The author died in 1984; protection runs to the end of 2054 (Art. 31(2)). (https://esu.com.ua/article-42948, read 2026-09-27)
  - «УкрЛіб © 2000 — 2026, Євген Васильєв При використанні матеріалів сайту, посилання на УкрЛіб обов'язкове.» — The ukrlib.com.ua copy asks for a link; it grants nothing for the author's rights. (https://www.ukrlib.com.ua/books/printit.php?tid=4002, read 2026-09-27)
- **Also searched:** https://archive.org/details/hovorymo1970 (1970 edition, user upload, no rights field); https://r2u.org.ua/yak-my-hovorymo/ (404)
- **Per use:**
  - *style_rule_quote @ quotation* — One short attributed rule quoted in a correction note (≤200 characters, LICENSE-CONTENT.md).
    - acquire: **assessed** — Reading a lawfully published work.
    - store: **assessed** — Only the quoted passage with citation.
    - transform: **assessed** — Quoted, not altered.
    - display: **assessed** — Quotation for a critical/informational purpose, author and source named.
    - redistribute: **unknown** — A dataset of quotations is systematic. HELD.
  - *style_entry_text @ bulk*
    - acquire: **assessed** — Internal reference copy, operator decision 2026-09-27; residual risk (copy provenance unrecorded).
    - store: **assessed** — Private store only.
    - transform: **assessed** — Internal lookups only.
    - display: **unknown** — HELD.
    - redistribute: **unknown** — HELD.
- **Open questions:**
  - Who represents the heirs? No contact found.
- **Contact:** unknown — heirs not identified

### Ukrainian Lessons Podcast notes and Anna Ohoiko's books (private references) — `ulp_private`

- **Organisation:** Anna Ohoiko (Ukrainian Lessons)
- **Role:** Private reference for pedagogy only; never quoted, never a card field source.
- **Fields:** reference_text
- **Stored in:** data/sources.db textbooks rows ulp-*-lesson-notes, anna-ohoiko-* (from the operator's private files under docs/references/private/, gitignored)
- **Licence as found:** All rights reserved (Anna Ohoiko)
- **Conditions:** attribution — n/a — not published. Share-alike: unknown. Non-commercial: unknown.
  - The website terms forbid crawling; scripts/crawl/crawl_ulp.py and crawl_ulp_blog.py fetch site metadata — see md § Findings.
- **Terms as found:**
  - «This Agreement does not transfer to you any intellectual property owned by Ogoiko, Anna or third parties, and all rights, titles, and interests in and to such property will remain (as between the parties) solely with Ogoiko, Anna.» (https://www.ukrainianlessons.com/terms-and-conditions/, read 2026-09-27)
  - «(h) to spam, phish, pharm, pretext, spider, crawl, or scrape» — Listed among prohibited uses of the website. (https://www.ukrainianlessons.com/terms-and-conditions/, read 2026-09-27)
- **Per use:**
  - *reference_text @ bulk*
    - acquire: **assessed** — The operator's own purchased copies, for personal study (LICENSE-CONTENT.md all-rights-reserved tier); never crawled.
    - store: **assessed** — Private local store only, gitignored.
    - transform: **assessed** — Internal retrieval only.
    - display: **refused** — All rights reserved; the project's own rule forbids verbatim use.
    - redistribute: **refused** — All rights reserved.
- **Contact:** Contact form (email obfuscated on the page) · https://www.ukrainianlessons.com/contact/
