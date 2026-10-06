# Source citation and provenance register (#8979)

For every source that feeds word cards, the Word Atlas, practice and the open dataset: who holds
the rights, what we use, where it comes from, the terms as found (quoted, with URL and read date),
the citation we show, and how a rights holder asks for removal.

**This register is a citation record, not a publication gate.** No build reads it to withhold
content. IP is the operator's responsibility (decisions below).

- **Machine-readable register (authoritative):** [`permissions-register.yaml`](permissions-register.yaml)
  — schema [`schemas/permissions-register.schema.json`](../../schemas/permissions-register.schema.json),
  validated by `tests/validate/test_permissions_register.py`. The per-source sections below mirror
  the YAML; if they differ, the YAML wins.
- **Spec:** #8979. This is the project's own record, not legal advice.

**Register date:** 2026-10-06. Schema version: 2.

## Operator decisions (binding)

Recorded on [#8979](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8979):

1. IP is the operator's responsibility. All current content stays on the site and in exports, including СУМ-20, ЕСУМ, ULIF (synonyms, antonyms, idioms), Горох/Балла; nothing is removed or held. (`d1_content_stays`)
2. The teacher agrees to her material being used (site and dataset). (`d2_teacher_consent`)
3. Takedown requests come as GitHub issues; no contact email. (`d3_takedown_via_issues`)
4. No outreach: nothing is sent to rights holders; the outreach drafts are dropped. (`d4_no_outreach`)

5. Plan v3.5.0 O1: verbatim use of in-copyright sources: YES, as the operator's IP responsibility. (2026-10-03; `o1_verbatim_use`; [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321))
6. Plan v3.5.0 O3: school and university textbooks are used as record sources (component C9). (2026-10-03; `o3_textbooks_used`; [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321))
7. Permissions for ULIF and СУМ-20 are being sought with help from Ukrainian experts. ULIF gave verbal permission in 2026-10, per the operator; written confirmation pending. This updates the practice described in d4_no_outreach only for these permissions. (2026-10-06; `d5_permissions_sought`; [#6321](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6321))

## Removal on request

A rights holder opens a GitHub issue naming the source and the content; the maintainer removes it from the site and the dataset export. There is no contact email (operator decision 3). Route: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues

Each source's entry says what a removal covers (`removal.scope`): the fields carrying its label on
the site, the same fields in the dataset export, and the stored copies listed under *Stored in*.

## How to read an entry

| Field | Meaning |
| --- | --- |
| Organisation | The rights holder, or who stands behind the source. |
| Fields | What we use from it. |
| Appears in | `internal` (private stores and tooling), `site` (learner pages and their public data files), `dataset` (the open dataset export). |
| Where from | Origin URL(s) and the retrieval date of our copy; when no date was recorded, the entry says so and gives the nearest evidence. |
| Permission status | Recorded permission status; scope and pending confirmation appear in the permission note. Not a publication gate. |
| Terms as found | Licence name, quoted terms with URL and read date; for openly licensed sources the licence text is quoted verbatim. |
| Citation | The citation form we use and the label learner pages show. |

Statutory text the entries refer to (Law of Ukraine No. 2811-IX, read 2026-09-27) is quoted once in
the YAML `legal_references`: sui generis database right (Art. 21(4)), quotation (Art. 22(2)(1)),
term of protection (Art. 31) and public domain (Art. 32(3)).

## Summary

| Source | Organisation | Appears in | Licence as found | Label shown |
| --- | --- | --- | --- | --- |
| `ulif` | Український мовно-інформаційний фонд НАН України (УМІФ / ULIF) | internal, site, dataset | All rights reserved (© ULIF); no open licence found | «Словники України» (Український мовно-інформаційний фонд НАН України) |
| `sum20` | Український мовно-інформаційний фонд НАН України (publisher, © of sum20ua.com) with the Інститут мовознавства ім. О. О. Потебні НАН України (co-compiler). Not the Інститут української мови, as the #8979 brief assumed — see the quotes. | internal, site, dataset | All rights reserved (© ULIF); no open licence found | Словник української мови у 20 томах (УМІФ НАН України, Ін-т мовознавства ім. О. О. Потебні) |
| `vesum` | Андрій Рисін, Василь Старко, команда БрУК (brown-uk) | internal, site, dataset | CC BY-NC-SA 4.0 (dictionary data); GPL-3.0-or-later (software) | VESUM |
| `slovnyk_me` | Slovnyk.me (operator not named on the site) | internal, site, dataset | No licence; site terms forbid copying without permission. Underlying dictionaries belong to their publishers (ULIF says the СУМ copies are unlawful). | — |
| `synonyms_dictionary` | Not established (see the entry) | internal, site, dataset | Not established — the underlying edition and its rights holder are not recorded; slovnyk.me's own terms (see the slovnyk_me entry) forbid copying without permission. | Словник синонімів української мови |
| `grinchenko` | Public domain (compiler Борис Грінченко, d. 1910). Our digital copy comes from the bakustarver/ukr-dictionaries-list-opensource aggregator; its digitiser is not named. | internal, site, dataset | Public domain (Law 2811-IX Art. 31(2), 32(3)) — the project's reading | Словарь української мови Б. Грінченка (1907–1909) |
| `sum11` | Інститут мовознавства ім. О. О. Потебні НАН України (compiled by over 50 lexicographers; official electronic edition at inmo.org.ua) | internal, site, dataset | In copyright — co-authored work, 70 years after the last co-author's death (Art. 31(4)). | СУМ-11 |
| `grac` | Марія Шведова, Ruprecht von Waldenfels, Сергій Яригін, Андрій Рисін, Василь Старко та ін. (Kyiv, Lviv, Jena) | internal, site, dataset | No licence published; citation requested; texts remain under their authors' copyright | Генеральний регіонально анотований корпус української мови (ГРАК) |
| `ua_gec` | Grammarly (Syvokon, Nahorna, Kuchmiichuk, Osidach) | internal, site, dataset | CC BY 4.0 | UA-GEC |
| `ukrajinet` | Melanie Siegel, Maksym Vakulenko (Hochschule Darmstadt) | internal, site, dataset | CC BY-SA 4.0 | Ukrajinet WordNet |
| `wiktionary` | Wiktionary contributors / Wikimedia Foundation | internal, site, dataset | CC BY-SA 4.0 (and GFDL) | Вікісловник |
| `kaikki` | Tatu Ylonen (Wiktextract) / English Wiktionary contributors | internal, site, dataset | CC BY-SA 4.0 (and GFDL) | kaikki |
| `dmklinger` | GitHub user dmklinger | internal, site, dataset | CC BY-SA 3.0 Unported | dmklinger |
| `goroh` | Горох (operator not named on the site) | internal, site, dataset | No reuse licence; ULIF names goroh.pp.ua as an unlawful СУМ copy | Горох (переклад) |
| `mphdict` | uSofTrod (LinguisticAndInformationSystems/mphdict) | internal, site, dataset | ODbL 1.0 (database) / DbCL 1.0 (contents) as far as uSofTrod holds rights; ЕСУМ text rights stay with the Інститут мовознавства | mphdict (ODbL/DbCL): Словник синонімів української мови та Орфографічний словник |
| `balla` | Author М. І. Балла and publishers (Освіта 1996; Чумацький Шлях 2007); digital copy via the bakustarver aggregator | internal, site, dataset | All rights reserved (in-print modern dictionary; editions of 1996 and 2007). | Українсько-англійський словник (М. Балла) |
| `puls` | Школа української мови та культури УКУ (О. Синчак, В. Старко, М. Бурак, М. Свистун та ін.) | internal, site, dataset | CC BY-NC-SA 4.0 | PULS CEFR |
| `ubertext_freq` | lang-uk (Дмитро Чаплинський) | internal | Not found | — |
| `r2u_e2u` | Андрій Рисін, Василь Старко, Ю. Марченко, О. Телемко та ін. (constituent dictionaries by their own authors) | internal, site, dataset | All rights reserved (© r2u.org.ua; per-dictionary author permissions) | e2u.org.ua (Rysin, Starko et al.) |
| `wikidata` | Wikidata contributors / Wikimedia Foundation | internal, site, dataset | CC0 1.0 | Wikidata |
| `ukrainian_word_stress` | lang-uk (code); Український мовно-інформаційний фонд НАН України (ULIF, underlying stress data) | internal, site, dataset | Code: MIT; data: derived from ULIF «Словники України», follows ULIF rights; no licence in the stress data repository | ukrainian-word-stress |
| `teacher_materials` | The operator's Ukrainian teacher (author); private DOCX supplied by the operator | internal, site, dataset | No licence; the teacher agrees to use on the site and in the dataset (operator decision 2, 2026-09-27). | — |
| `course_authored` | Learn Ukrainian project (maintainer Krisztian Koos) | internal, site, dataset | CC BY-SA 4.0 (project content) | Learn Ukrainian |
| `wikipedia` | Wikipedia contributors / Wikimedia Foundation | internal, site, dataset | CC BY-SA 4.0 (and GFDL) | Вікіпедія |
| `esum` | Інститут мовознавства ім. О. О. Потебні НАН України (publisher Наукова думка); co-authored by many compilers | internal, site, dataset | In copyright (co-authored, vol. 6 published 2012 — Art. 31(4)); rights holder not confirmed (Institute and/or Наукова думка) | «Етимологічний словник української мови» (ЕСУМ, Ін-т мовознавства ім. О. О. Потебні НАН України; mphdict ODbL/DbCL) |
| `textbooks` | Individual authors and publishers (e.g. Заболотний, Авраменко, Вашуленко, Карман, Літвінова, Глазова); PDFs via pidruchnyk.com.ua and lib.imzo.gov.ua | internal, site, dataset | In copyright (authors/publishers); free public access by law, no reuse licence | — |
| `frazeolohichnyi` | Compilers (Білоноженко В. М. та ін.) / publisher Наукова думка — rights holder not confirmed | internal, site, dataset | In copyright (co-authored, 2003); no licence found | Фразеологічний словник української мови |
| `antonenko_style_guide` | Heirs of Борис Антоненко-Давидович (d. 9 May 1984) — no contact found | internal, site, dataset | In copyright until 31 Dec 2054 (Art. 31(2)); rights with the heirs | «Як ми говоримо» Антоненка-Давидовича |
| `ulp_private` | Anna Ohoiko (Ukrainian Lessons) | internal | All rights reserved (Anna Ohoiko) | — |

## Open questions

1. The open dataset's own licence. VESUM data is CC BY-NC-SA 4.0 and CC allows adaptations of it only under BY-NC-SA 4.0 or later; CC BY-SA inputs (Вікісловник, Kaikki, dmklinger, Ukrajinet, Вікіпедія) must stay BY-SA. Recommendation on #8979: CC BY-NC-SA 4.0 for the core, BY-SA-derived fields in separate CC BY-SA 4.0 files. Not decided. O1/O3 (2026-10-03, plan v3.5.0 on #6321) decided use, not the dataset's licence; plan step E6 (dataset licence choice) remains an operator decision.
2. Sources shown in the Atlas with no entry here yet (labels from scripts/lexicon/source_attribution.py, counted in atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28): Великий тлумачний словник сучасної української мови (ВТС, 8,422), Словник синонімів С. Караванського (2,727), Орфографічний словник української мови (5,534), Правописний словник Голоскевича (3,396), Орфоепічний словник української мови (1,912), Приповідки або українсько-народня філософія (555), МійКлас relation pairs (704), «Уроки державної мови» з газети «Хрещатик» (27), Словник чужослів Павла Штепи (33), Культура слова (3), and the literary corpus (literary_texts, e.g. izbornyk.org.ua, ukrlib.com.ua). Each needs its own entry.

Per-source open questions are listed in each entry below.

## Record corrections elsewhere

`LICENSE-CONTENT.md`, `scripts/audit/source_license_map.json` and the dataset exporter's
`ATTRIBUTION_MD` state some licences differently from the terms quoted here: VESUM data is
CC BY-NC-SA 4.0 (not "MIT-ish"); СУМ-11 is a co-authored 1970–1980 work still in copyright (not
public domain); Балла is an in-print dictionary (no support for "copyright expired"); Kaikki is
CC BY-SA 4.0 (not 3.0); UA-GEC is CC BY 4.0 (`scripts/ingest/ua_gec_ingest.py` says MIT).
Correcting those texts is #9000.

## Per source

### «Словники України» online (DictUA) — paradigm, synonym, antonym and phraseology tabs — `ulif`

- **Permission status:** `verbal-granted-written-pending` — ULIF gave verbal permission (2026-10, per the operator); written confirmation pending.
- **Organisation:** Український мовно-інформаційний фонд НАН України (УМІФ / ULIF)
- **Role:** Stress, paradigms, grammar labels, homonym/sense hints, synonyms, antonyms and phraseology for word cards; the harvest is #8400.
- **Fields:** corroboration_reference, headword, stress, grammatical_label, paradigm, homonym_sense_gloss, synonym_groups, antonym_pairs, phraseology
- **Appears in:** internal, site, dataset — scripts/lexicon/enrich_manifest.py fills synonyms, antonyms and stress from ulif_dictua_* with ULIF_DICTUA_LABEL; the 2026-09-11 manifest predates most of the harvest (one ULIF-labelled payload in the atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db ulif_dictua_entries, ulif_dictua_sections; data/lexicon/cache/ulif_raw.sqlite ulif_dictua_raw_responses; data/atlas.db / site lexicon shards (scripts/atlas/export_runtime_shards.py writes each public payload_json into the shards; the 2026-09-11 build carries one ULIF-labelled payload and no ULIF-labelled synonym, antonym or idiom section — see appears_note)
- **Where from:** https://lcorp.ulif.org.ua/dictua/ · retrieved 2026-09-27 — sources.db ulif_dictua_entries.retrieved_at spans 2026-07-15 to 2026-09-27 (harvest #8400, ongoing).
- **Licence as found:** All rights reserved (© ULIF); no open licence found. Share-alike: not stated. Non-commercial: not stated.
  - Sui generis database right (Law 2811-IX Art. 21) applies to extraction and re-use of substantial parts.
  - Harvest runs at one request per second with an identifying non-commercial user agent (fetch_ulif_homonyms.py).
- **Terms as found:**
  - «"Словники України online" розроблено на основі CD-версії 3.2 (2008р.) © ULIF, 2001-2026» — Copyright notice only; no licence or terms-of-use page is linked from the portal (https://lcorp.ulif.org.ua/dictua/, read 2026-09-27)
  - «ШАНОВНІ КОРИСТУВАЧІ! Вебсайти на кшталт goroh.pp.ua, sum.in.ua, slovnyk.me використовують електронні версії "Словника української мови" та "Словника української мови в 20 томах" неправомірно, не вказуючи авторів!» — ULIF states that goroh.pp.ua, sum.in.ua and slovnyk.me use СУМ and СУМ-20 unlawfully, without naming the authors (https://www.ulif.org.ua/koristuities-dostovirnimi-dzhierielami, read 2026-09-27)
- **Also searched:** https://lcorp.ulif.org.ua/dictua/ (footer; only links Pro_Systemu.pdf, Instruction_Dict_Of_Ukraine_3.2.pdf, the notice); https://lcorp.ulif.org.ua/robots.txt (returned an access-restricted page); https://www.ulif.org.ua/contacts; services.ulif.org.ua (timed out)
- **Statute referred to:** `law_art21_sui_generis`
- **Citation:** «Словники України online», Український мовно-інформаційний фонд НАН України, https://lcorp.ulif.org.ua/dictua/ (entry reference and retrieval date per field) Label shown: «Словники України» (Український мовно-інформаційний фонд НАН України) — scripts/lexicon/source_attribution.py ULIF_DICTUA_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### «Словник української мови у 20 томах» (СУМ-20), official electronic edition — `sum20`

- **Permission status:** `pending-expert-contact` — Permission is being sought; the operator is collecting it personally with help from Ukrainian experts.
- **Organisation:** Український мовно-інформаційний фонд НАН України (publisher, © of sum20ua.com) with the Інститут мовознавства ім. О. О. Потебні НАН України (co-compiler). Not the Інститут української мови, as the #8979 brief assumed — see the quotes.
- **Role:** Modern Ukrainian definitions, sense structure, stressed headwords and citations for cards.
- **Fields:** definition_text, sense_structure, stressed_headword, literary_citations
- **Appears in:** internal, site, dataset — 6,483 public payloads carry the СУМ-20 label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28); also reached via the slovnyk.me 'newsum' copy.
- **Stored in:** data/sources.db sum20_articles, sum20_senses, sum20_citations (crawled from sum20ua.com); site lexicon shards (definition cards; scripts/atlas/export_runtime_shards.py writes each public payload_json, including the СУМ-20-labelled ones counted in appears_note, into the shards)
- **Where from:** https://sum20ua.com/ · retrieved 2026-09-22 — sources.db sum20_articles.fetched_at spans 2026-09-15 to 2026-09-22 (scripts/ingest/sum20_official_ingest.py).
- **Licence as found:** All rights reserved (© ULIF); no open licence found. Share-alike: not stated. Non-commercial: not stated.
  - Definitions are copyrighted text and the dictionary is also a protected database.
- **Terms as found:**
  - «Словник української мови. Томи 1-16 (А-РЯХТЛИВИЙ) © Український мовно-інформаційний фонд НАН України, 2015 - 2026» (https://sum20ua.com/, read 2026-09-27)
  - «Для посилання на наш Словник ... можна використовувати URL-адресу форми: https://sum20ua.com/expl/entry/search/слово» — The only reuse the site offers is linking (and embedding its search form) (https://sum20ua.com/, read 2026-09-27)
  - «User-agent: ClaudeBot Disallow: / ... User-agent: * Allow: / ... Crawl-delay: 10» — AI crawlers are blocked by name; all other agents allowed with a 10-second crawl delay (https://sum20ua.com/robots.txt, read 2026-09-27)
  - «"Словник української мови в 20 томах" укладається науковцями Українського мовно-інформаційного фонду НАН України та Інституту мовознавства ім. О.О. Потебні НАН України» (https://www.ulif.org.ua/koristuities-dostovirnimi-dzhierielami, read 2026-09-27)
- **Also searched:** https://sum20ua.com/Home/About (404); https://sum20ua.com/robots.txt; https://iul-nasu.org.ua/pro-instytut/kontaktna-informatsiya.html (Інститут української мови — not the compiler)
- **Statute referred to:** `law_art21_sui_generis`
- **Citation:** Словник української мови у 20 томах (Український мовно-інформаційний фонд НАН України, Інститут мовознавства ім. О. О. Потебні НАН України), https://sum20ua.com/ — official edition only, never a mirror (docs/best-practices/atlas-source-presentation.md). Label shown: Словник української мови у 20 томах (УМІФ НАН України, Ін-т мовознавства ім. О. О. Потебні) — scripts/lexicon/source_attribution.py SUM20_ACADEMIC_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### ВЕСУМ — Великий електронний словник української мови (dict_uk) — `vesum`

- **Permission status:** `open-licence`
- **Organisation:** Андрій Рисін, Василь Старко, команда БрУК (brown-uk)
- **Role:** Lemmas, all word forms, POS and grammatical tags — the open backbone of every card.
- **Fields:** lemma, word_forms, pos, morph_tags, markers
- **Appears in:** internal, site, dataset — 26,743 public payloads carry the VESUM label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/vesum.db (forms_all, form_markers, vesum_build_metadata) from dict_corp_vis.txt.bz2 v6.8.0 (scripts/config/vesum_source.lock.json)
- **Where from:** https://github.com/brown-uk/dict_uk/releases/download/v6.8.0/dict_corp_vis.txt.bz2 · Retrieval date not recorded; scripts/config/vesum_source.lock.json pins release v6.8.0 (upstream commit bcb5ccd9585a79dbbbb7c8c5e241adcd8a64f824, sha256 e3380378…) instead.
- **Licence as found:** CC BY-NC-SA 4.0 (dictionary data); GPL-3.0-or-later (software) (`CC-BY-NC-SA-4.0`). Share-alike: yes. Non-commercial: yes.
  - Adaptations may only be licensed under BY-NC-SA 4.0 or later (CC compatibility page) — see the dataset-licence open question.
- **Terms as found:**
  - https://github.com/brown-uk/dict_uk/blob/5e6c53b5c1e5764caffb73f69a133634a858adeb/README.md, read 2026-09-28 — Verbatim licence section (Ukrainian) of the dict_uk README at commit 5e6c53b5c1e5764caffb73f69a133634a858adeb:

    > ### Ліцензія ###
    >
    > Дані словника доступні для використання згідно з умовами ліцензії "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" (https://creativecommons.org/licenses/by-nc-sa/4.0/)
    >
    > Програмні засоби вільно розповсюджується за умов ліцензії GPL 3.0 або вище.
    >
    > Зауваження: [похідні проекти](distr/) мають свої ліцензії
    >
    > Окрім цього матеріали цього проєкту дозволено використовувати у проєктах https://voice.mozilla.org/uk і https://common-voice.github.io/sentence-collector/#/ відповідно до їх ліцензій.
    >
    > Copyright (c) 2023 Андрій Рисін (arysin@gmail.com), Василь Старко, команда БрУК

  - https://github.com/brown-uk/dict_uk/blob/5e6c53b5c1e5764caffb73f69a133634a858adeb/README.md, read 2026-09-28 *(licence text, verbatim)* — Verbatim licence section (English) of the same README:

    > ### License ###
    >
    > Dictionary data are distributed under "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License" (https://creativecommons.org/licenses/by-nc-sa/4.0/)
    >
    > Software is distributed under GPL 3.0 or above.
    >
    > Note: [derivative projects](distr/) have different licenses
    >
    > Besides that materials in this project are allowed to be used in https://voice.mozilla.org/uk and https://common-voice.github.io/sentence-collector/#/ according to their licenses.
    >
    > Copyright (c) 2026 Andriy Rysin (arysin@gmail.com), Vasyl Starko, BrUK team

  - «GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007» — The root LICENSE file is the GPL-3.0 text and covers the software only; the README assigns data to CC BY-NC-SA 4.0 (https://github.com/brown-uk/dict_uk/blob/master/LICENSE, read 2026-09-27)
  - «Rysin, A., Starko, V. Large Electronic Dictionary of Ukrainian (VESUM). Version 6.7.8. 2005-2026. Available at: https://vesum.nlp.net.ua/» (https://github.com/brown-uk/dict_uk/blob/master/README.md, read 2026-09-27)
  - «NonCommercial — You may not use the material for commercial purposes. ShareAlike — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.» (https://creativecommons.org/licenses/by-nc-sa/4.0/, read 2026-09-27)
- **Citation:** Рисін А., Старко В. Великий електронний словник української мови (ВЕСУМ). Версія <used version>. 2005-2026. URL: https://vesum.nlp.net.ua/ — licence CC BY-NC-SA 4.0, changes indicated. Label shown: VESUM.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - The README's citation names version 6.7.8; we pin 6.8.0. Cite the version actually used.

### slovnyk.me (aggregator of dictionaries incl. СУМ-11 and СУМ-20 copies) — `slovnyk_me`

- **Permission status:** `none`
- **Organisation:** Slovnyk.me (operator not named on the site)
- **Role:** Verification, and the retrieval route for several dictionaries (СУМ-20, ВТС, synonyms, phraseology, proverbs, Балла, Штепа, orthography, orthoepy, Голоскевич, Антоненко-Давидович) shown under the underlying work's own label.
- **Fields:** verification_outcome, definition_text, usage_essay, en_gloss_ukreng
- **Appears in:** internal, site, dataset — Retrieval route for several dictionaries shown under the underlying work's label (scripts/lexicon/source_attribution.py SLUG_ACADEMIC_LABELS: СУМ-20, ВТС, synonyms, phraseology, proverbs, Балла, Антоненко-Давидович, Штепа, orthography, orthoepy, Голоскевич); the mirror URL stays in internal mirror_source_url fields. 12,370 public payloads mention slovnyk.me (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db slovnyk_me_entries (snippets capped at 200–500 chars); data/lexicon/slovnyk_cache/ (per-lemma cache pre-filled for every manifest lemma by scripts/lexicon/build_slovnyk_mirror.py, per its module docstring)
- **Where from:** https://slovnyk.me/ · retrieved 2026-09-09 — data/lexicon/slovnyk_cache/*.json fetched_at, sample of 527 files: 2026-08-06 to 2026-09-09 (scripts/lexicon/build_slovnyk_mirror.py).
- **Licence as found:** No licence; site terms forbid copying without permission. Underlying dictionaries belong to their publishers (ULIF says the СУМ copies are unlawful). Share-alike: not stated. Non-commercial: not stated.
- **Terms as found:**
  - «Пользователь соглашается не воспроизводить, не повторять и не копировать, не продавать и не перепродавать, а также не использовать для каких-либо коммерческих целей какие-либо части Сайта ... кроме тех случаев, когда такое разрешение дано Пользователю Администрацией Сайта.» — The user agrees not to reproduce, repeat or copy, sell or resell, or use commercially any part of the site unless the site administration permits it. (Archived 2024-03-20; the live /terms is blocked by Cloudflare and disallowed in robots.txt.) (https://web.archive.org/web/20240320103142id_/https://slovnyk.me./terms, read 2026-09-27)
  - «User-agent: * Disallow: /feedback Disallow: /terms Disallow: /search» (https://slovnyk.me/robots.txt, read 2026-09-27)
- **Also searched:** https://slovnyk.me/ (live: Cloudflare 403); footer via Wayback 2026-08-25 «Контакти © 2026 Slovnyk.me»
- **Citation:** The underlying work's academic label and official edition (docs/best-practices/atlas-source-presentation.md rules 1–3); slovnyk.me is never named as the authority on learner pages. Label shown: not named on learner pages.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### «Словник синонімів української мови» as served by slovnyk.me (dictionary slug `synonyms`) — edition not established — `synonyms_dictionary`

- **Permission status:** `unknown`
- **Organisation:** Not established. slovnyk.me names no author, editor, publisher or year for this dictionary in any record we hold. The title matches the two-volume «Словник синонімів української мови» (1999–2000) that ULIF's system description names as the base of its own synonym module (docs/research/UKRAINIAN_DATA_FOUNDRY_LANGUAGE_SPAN_AND_LEXICAL_EVIDENCE.md § ULIF evidence, citing https://lcorp.ulif.org.ua/pdf/Pro_Systemu.pdf), and a 2026-06-11 brief lists that work as «А. А. Бурячок та ін., 2 т., 1999–2000» (docs/dispatch-briefs/2026-06-11-ua-lexicon-source-research.md, a seed list to verify, not a verification). Nothing we hold ties slovnyk.me's copy to that edition.
- **Role:** Synonym chips and synonym groups (synsets with sense glosses) on Atlas word cards.
- **Fields:** synonym_groups, sense_gloss
- **Appears in:** internal, site, dataset — 4,835 public synonym sections name this work in their source, and every one of them carries a slovnyk.me/dict/synonyms/ URL; atlas.db enrichment has 2,469 synonym rows with this label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28). Filled by scripts/lexicon/enrich_manifest.py under scripts/lexicon/source_attribution.py SYNONYMS_LABEL; scripts/atlas/export_runtime_shards.py writes each public payload_json into the site shards.
- **Stored in:** data/lexicon/slovnyk_cache/<lemma>.json lookups.synonyms (4,937 cached lookups, dictionary_slug synonyms); data/atlas.db enrichment (section synonyms) and article_payloads
- **Where from:** https://slovnyk.me/dict/synonyms/ · retrieved 2026-08-25 — data/lexicon/slovnyk_cache/*.json: the 4,937 files with a synonyms lookup have fetched_at from 2026-08-06 to 2026-08-25 (scripts/lexicon/build_slovnyk_mirror.py). The cached records carry only dictionary_slug, dictionary_label, word, source_url, title and text — no edition data.
- **Licence as found:** Not established — the underlying edition and its rights holder are not recorded; slovnyk.me's own terms (see the slovnyk_me entry) forbid copying without permission. Share-alike: not stated. Non-commercial: not stated.
- **Also searched:** data/lexicon/slovnyk_cache/*.json synonyms lookups (4,937 records; no author, editor, publisher or year field); scripts/wiki/slovnyk_me.py SLOVNYK_ME_DICTS (slug synonyms → title only); scripts/lexicon/source_attribution.py SYNONYMS_LABEL (title only); docs/research/UKRAINIAN_DATA_FOUNDRY_LANGUAGE_SPAN_AND_LEXICAL_EVIDENCE.md § ULIF evidence (edition of ULIF's module, not of slovnyk.me's copy)
- **Citation:** Словник синонімів української мови (edition not established; retrieved via slovnyk.me). Once the edition is established, cite its compilers, place, publisher and year per docs/best-practices/atlas-source-presentation.md rules 1–3. Label shown: Словник синонімів української мови — scripts/lexicon/source_attribution.py SYNONYMS_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Which edition does slovnyk.me serve under this title (the 1999–2000 two-volume dictionary or another), who compiled it, and who holds its rights?

### Грінченко Б. Д. «Словарь української мови» (1907–1909) — `grinchenko`

- **Permission status:** `public-domain` — The digitiser's database right is unknown.
- **Organisation:** Public domain (compiler Борис Грінченко, d. 1910). Our digital copy comes from the bakustarver/ukr-dictionaries-list-opensource aggregator; its digitiser is not named.
- **Role:** Pre-Soviet attestation of words and senses.
- **Fields:** headword, entry_text
- **Appears in:** internal, site, dataset — 4,755 public payloads mention Грінченко (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db grinchenko(word, definition, source) from a Lingvo-format JSON (scripts/rag/prepare_grinchenko.py)
- **Where from:** https://github.com/bakustarver/ukr-dictionaries-list-opensource · Retrieval date not recorded; scripts/rag/prepare_grinchenko.py was added in a37f56d568 (2026-03-25).
- **Licence as found:** Public domain (Law 2811-IX Art. 31(2), 32(3)) — the project's reading. Share-alike: no. Non-commercial: no.
  - A digitiser's own database right (Art. 21, 15 years) could exist for a recent digitisation; the digitiser is unknown.
- **Terms as found:**
  - «Борис Дмитрович Грінче́нко (27 листопада [9 грудня] 1863 … — 23 квітня [6 травня] 1910, Оспедалетті, Королівство Італія)» — The compiler died in 1910, so the life+70 term ended on 31 December 1980 (https://uk.wikipedia.org/wiki/Грінченко_Борис_Дмитрович, read 2026-09-27)
  - «Матеріали для словника зібрала редакція журналу «Кіевская старина», а упорядкував його … Борис Грінченко» — The journal's editors gathered the material; Hrinchenko compiled it (https://uk.wikipedia.org/wiki/Словарь_української_мови, read 2026-09-27)
- **Also searched:** https://github.com/bakustarver/ukr-dictionaries-list-opensource (AGPL-3.0 repo; no provenance for the digitisation)
- **Statute referred to:** `law_art31_term`, `law_art32_public_domain`
- **Citation:** Грінченко Б. Д. Словарь української мови. Київ, 1907–1909. (Moral right of attribution survives, Art. 32(3).) Label shown: Словарь української мови Б. Грінченка (1907–1909) — scripts/lexicon/source_attribution.py GRINCHENKO_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Death dates of the other early editors (Науменко, Тимченко) were not verified.
  - Who digitised this copy? The digitiser is not named in the aggregator.

### «Словник української мови» в 11 томах (СУМ-11, 1970–1980) — `sum11`

- **Permission status:** `none`
- **Organisation:** Інститут мовознавства ім. О. О. Потебні НАН України (compiled by over 50 lexicographers; official electronic edition at inmo.org.ua)
- **Role:** Russification evidence only (see usage_restriction).
- **Usage restriction:** Rule #M-6 (operator 2026-09-27): СУМ-11 is used ONLY as evidence of russification — what it imposed, shown red-flagged beside the modern Ukrainian norm with both sources cited. It is never modern evidence: never a modern meaning, form, example or practice answer.
- **Fields:** russification_quote, russification_pair
- **Appears in:** internal, site, dataset — 4,886 public payloads mention СУМ-11 and atlas.db enrichment labels 3,583 synonym and 387 antonym rows СУМ-11 (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28). That build predates the rule #M-6 enforcement (edfaa5ebd0, 2026-09-27). Known mismatch with rule #M-6 in that build: it cites СУМ-11 as ordinary synonym and antonym evidence. The public `абрикос` payload's sections.synonyms.source reads «Словник синонімів української мови + … + СУМ-11: Те саме, що → абрикоса» with no russification flag or modern-norm pair anywhere in the payload; 4,121 public synonym sections and 297 public antonym sections name СУМ-11 in their source, and 1 of those 4,418 sections contains any russification marker (evidence query, read-only on atlas.db: SELECT slug, payload_json FROM article_payloads WHERE is_public_route = 1; for sections.synonyms / sections.antonyms whose source contains «СУМ-11», search the section JSON for russif|русиф|русизм|sovietiz|red_flag; run 2026-09-28).
- **Stored in:** data/sources.db sum11(word, definition, text, source) from the bakustarver/ukr-dictionaries-list-opensource JSON (scripts/rag/convert_dictionaries.py)
- **Where from:** https://github.com/bakustarver/ukr-dictionaries-list-opensource; https://www.inmo.org.ua/sum.html · Retrieval date not recorded; scripts/rag/convert_dictionaries.py (aggregator import) was added in b82002a582 (2026-03-24).
- **Licence as found:** In copyright — co-authored work, 70 years after the last co-author's death (Art. 31(4)). Share-alike: not stated. Non-commercial: not stated.
  - Our copy comes from an aggregator of the sum.in.ua text, which ULIF names as unlawful; verify each quoted passage against the official edition (inmo.org.ua/sum.html) before display.
- **Terms as found:**
  - «Створений кількома поколіннями лексикографів Інституту мовознавства ім. О. О. Потебні (А. А. Бурячок … Л. А. Юрчук та ін. – загалом понад 50 укладачів і редакторів). Паперовий оригінал вийшов у 11-ти томах (1970–1980).» (https://www.inmo.org.ua/sum.html, read 2026-09-27)
  - «© 2011 Інститут мовознавства ім. О.О. Потебні Національної академії наук України» (https://www.inmo.org.ua/sum.html, read 2026-09-27)
- **Also searched:** https://www.inmo.org.ua/sum.html (no licence text); https://sum.in.ua/ (unreachable; Wayback 2026-01-03 footer «© 2023, Webmezha», no terms page)
- **Statute referred to:** `law_art31_term`, `law_art22_quotation`
- **Citation:** Словник української мови: в 11 томах. АН УРСР, Інститут мовознавства ім. О. О. Потебні. Київ: Наукова думка, 1970–1980. Т. <vol>, с. <page> — quoted, red-flagged, always with the modern norm in the same sentence. Label shown: СУМ-11.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Do Atlas builds after the #8969 enforcement (edfaa5ebd0) still cite СУМ-11 as ordinary synonym, antonym or sense evidence? The remaining scripts/lexicon uses are tracked in #8990; the 2026-09-11 build's mismatch is recorded in appears_note.
  - Replace the aggregator copy with passages checked against the official edition.

### ГРАК — Генеральний регіонально анотований корпус української мови — `grac`

- **Permission status:** `none`
- **Organisation:** Марія Шведова, Ruprecht von Waldenfels, Сергій Яригін, Андрій Рисін, Василь Старко та ін. (Kyiv, Lviv, Jena)
- **Role:** Modern example sentences and frequency for level gating.
- **Fields:** example_sentence, frequency_count, frequency_tier
- **Appears in:** internal, site, dataset — 4,192 public payloads mention GRAC (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** live queries (scripts/rag/source_query.py, sketch.uacorpus.org corpus grac19a); data/lexicon/cache/grac_frequency.json
- **Where from:** https://uacorpus.org/; https://sketch.uacorpus.org/ · Live queries (scripts/rag/source_query.py, corpus grac19a); per-query dates are not stored.
- **Licence as found:** No licence published; citation requested; texts remain under their authors' copyright. Share-alike: not stated. Non-commercial: not stated.
- **Terms as found:**
  - «The corpus can be used for advanced study of the language as well as for writing textbooks, learner's dictionaries and exercises using examples from real texts» (https://uacorpus.org/en, read 2026-09-27)
  - «Просимо посилатися на ГРАК: Генеральний регіонально анотований корпус української мови (ГРАК) / М. Шведова, Р. фон Вальденфельс, С. Яригін, А. Рисін, В. Старко, Т. Ніколаєнко, А. Лукашевський та ін. — Київ, Львів, Єна, 2017–. — uacorpus.org.» (https://uacorpus.org/, read 2026-09-27)
- **Also searched:** https://uacorpus.org/informaciya-pro-grak, /rozrobniki, /poshuk-u-graku, /korpus-dlya-zavantazhennya-plug, /versiyi-korpusu, /slovniki, /en, https://sketch.uacorpus.org — no licence or redistribution statement
- **Citation:** GRAC citation above, plus the author and title of the text each sentence comes from. Label shown: Генеральний регіонально анотований корпус української мови (ГРАК) — scripts/lexicon/source_attribution.py GRAC_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### UA-GEC — Ukrainian grammatical error correction corpus — `ua_gec`

- **Permission status:** `open-licence`
- **Organisation:** Grammarly (Syvokon, Nahorna, Kuchmiichuk, Osidach)
- **Role:** Error→correction pairs (calques, case, gender) for common-mistake notes.
- **Fields:** error_text, correction_text, error_type
- **Appears in:** internal, site, dataset — 5 public payloads mention UA-GEC (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28); also practice error corrections.
- **Stored in:** data/sources.db ua_gec_errors, ua_gec_errors_fts
- **Where from:** https://github.com/grammarly/ua-gec · Retrieval date not recorded; scripts/ingest/ua_gec_ingest.py was added in 7290caee21 (2026-05-17).
- **Licence as found:** CC BY 4.0 (`CC-BY-4.0`). Share-alike: no. Non-commercial: no.
- **Terms as found:**
  - «Attribution 4.0 International» *(licence text, verbatim)* — The repository LICENSE is the CC BY 4.0 legal code (no ShareAlike, no NonCommercial) (https://github.com/grammarly/ua-gec/blob/main/LICENSE, read 2026-09-27)
- **Citation:** UA-GEC (Syvokon, Nahorna, Kuchmiichuk, Osidach, UNLP 2023), https://github.com/grammarly/ua-gec, CC BY 4.0, changes indicated. Label shown: UA-GEC.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### Ukrajinet (Ukrainian WordNet) — `ukrajinet`

- **Permission status:** `open-licence`
- **Organisation:** Melanie Siegel, Maksym Vakulenko (Hochschule Darmstadt)
- **Role:** Synonym candidates (quality caveat — largely auto-translated from Open English WordNet).
- **Fields:** synset_members
- **Appears in:** internal, site, dataset — 796 public payloads carry the Ukrajinet label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db ukrajinet(synset_id, words, text)
- **Where from:** https://github.com/hdaSprachtechnologie/ukrajinet · Retrieval date not recorded; scripts/rag/convert_phase2.py (ukrajinet.xml import) was added in cb2f8df7f1 (2026-03-24).
- **Licence as found:** CC BY-SA 4.0 (`CC-BY-SA-4.0`). Share-alike: yes. Non-commercial: no.
  - BY-SA adaptations must stay BY-SA — ship in a separately licensed file, never merged into BY-NC-SA records.
- **Terms as found:**
  - «This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/» *(licence text, verbatim)* (https://github.com/hdaSprachtechnologie/ukrajinet, read 2026-09-27)
- **Citation:** Ukrajinet, Melanie Siegel & Maksym Vakulenko, https://github.com/hdaSprachtechnologie/ukrajinet, CC BY-SA 4.0. Label shown: Ukrajinet WordNet.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### Вікісловник (Ukrainian Wiktionary) dumps — `wiktionary`

- **Permission status:** `open-licence`
- **Organisation:** Wiktionary contributors / Wikimedia Foundation
- **Role:** Definitions, synonyms, antonyms, etymology hints.
- **Fields:** definition_text, synonyms, antonyms, etymology_text
- **Appears in:** internal, site, dataset — 5,158 public payloads carry the Вікісловник label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db wiktionary, wiktionary_etymology (dumps.wikimedia.org/ukwiktionary)
- **Where from:** https://dumps.wikimedia.org/ukwiktionary/ · retrieved 2026-06-11 — sources.db wiktionary_etymology: dump_date 20260601, retrieved_at 2026-06-11.
- **Licence as found:** CC BY-SA 4.0 (and GFDL) (`CC-BY-SA-4.0`). Share-alike: yes. Non-commercial: no.
  - BY-SA — separate licensed file in the release.
- **Terms as found:**
  - «Creative Commons Attribution-ShareAlike 4.0 International License ("CC BY-SA 4.0"), and GNU Free Documentation License ("GFDL") ... Reusers may comply with either license or both.» *(licence text, verbatim)* (https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use, read 2026-09-27)
  - «all original textual content is licensed under the GNU Free Documentation License (GFDL) and the Creative Commons Attribution-Share-Alike 4.0 License. Some text may be available only under the Creative Commons license» (https://dumps.wikimedia.org/legal.html, read 2026-09-27)
- **Also searched:** https://uk.wiktionary.org/wiki/Вікісловник:Авторське_право (404)
- **Citation:** Link to the reused page(s) or list of authors, plus a CC BY-SA 4.0 licence notice (Terms of Use). Label shown: Вікісловник.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### Kaikki.org Wiktextract extract (English Wiktionary, Ukrainian entries) — `kaikki`

- **Permission status:** `open-licence`
- **Organisation:** Tatu Ylonen (Wiktextract) / English Wiktionary contributors
- **Role:** Second English-gloss source, IPA and fallback etymology (commit ca2c3a50e1).
- **Fields:** en_gloss, ipa, etymology_text
- **Appears in:** internal, site, dataset — 13,644 public payloads carry the kaikki / Wiktionary label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/lexicon/kaikki_uk_lookup.json, data/lexicon/side/kaikki.sqlite
- **Where from:** https://kaikki.org/dictionary/rawdata.html · Retrieval date not recorded; scripts/lexicon/build_kaikki_lookup.py was added in 124a1dee1f (2026-06-12); the local lookup was rebuilt 2026-09-27.
- **Licence as found:** CC BY-SA 4.0 (and GFDL) (`CC-BY-SA-4.0`). Share-alike: yes. Non-commercial: no.
- **Terms as found:**
  - «This data is made available under the same licenses as Wiktionary - both CC-BY-SA and GFDL. See Wiktionary copyright page for more information.» *(licence text, verbatim)* (https://kaikki.org/dictionary/, read 2026-09-27)
  - «The original texts of Wiktionary entries are dual-licensed to the public under both the Creative Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA) and the GNU Free Documentation License (GFDL).» (https://en.wiktionary.org/wiki/Wiktionary:Copyrights, read 2026-09-27)
- **Citation:** English Wiktionary (via kaikki.org / Wiktextract, Ylonen 2022), CC BY-SA 4.0, link to the entry page. Label shown: kaikki.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### dmklinger/ukrainian dictionary (UK→EN) — `dmklinger`

- **Permission status:** `open-licence`
- **Organisation:** GitHub user dmklinger
- **Role:** First-choice English gloss for Atlas and lesson evidence.
- **Fields:** en_gloss
- **Appears in:** internal, site, dataset — 15,009 public payloads carry the dmklinger label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db dmklinger_uk_en, data/lexicon/side/dmklinger.sqlite
- **Where from:** https://github.com/dmklinger/ukrainian · Retrieval date not recorded; scripts/rag/convert_phase2.py (words.json import) was added in cb2f8df7f1 (2026-03-24).
- **Licence as found:** CC BY-SA 3.0 Unported (`CC-BY-SA-3.0`). Share-alike: yes. Non-commercial: no.
  - BY-SA 3.0 adaptations may be licensed BY-SA 4.0 (CC compatibility page). We use its glosses, not its ULIF-derived forms.
- **Terms as found:**
  - «This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License.» *(licence text, verbatim)* (https://github.com/dmklinger/ukrainian/blob/main/license.txt, read 2026-09-27)
  - «All data scraped from wiktionary and [dbnary]… Forms filled in from [here](https://lcorp.ulif.org.ua/dictua/dictua.aspx)» — Glosses come from Wiktionary/DBnary; word forms from ULIF (we do not use the forms) (https://github.com/dmklinger/ukrainian, read 2026-09-27)
  - «Dbnary is derived from Wiktionary and is distributed under Creative Commons Attribution-ShareAlike 3.0» (https://kaiko.getalp.org/about-dbnary/, read 2026-10-06)
- **Citation:** dmklinger/ukrainian (from Wiktionary and DBnary), https://github.com/dmklinger/ukrainian, CC BY-SA 3.0. Label shown: dmklinger.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### Горох (goroh.pp.ua) — `goroh`

- **Permission status:** `none`
- **Organisation:** Горох (operator not named on the site)
- **Role:** Live English-gloss fallback and a small etymology stub table.
- **Fields:** en_gloss, etymology_text
- **Appears in:** internal, site, dataset — 379 public payloads mention Горох (translation 277, etymology 76 enrichment rows; atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db goroh_etymology (41 rows), live lookups in scripts/rag/source_query.py
- **Where from:** https://goroh.pp.ua/ · retrieved 2026-06-19 — sources.db goroh_etymology.retrieved_at spans 2026-06-10 to 2026-06-19; live lookups are not dated.
- **Licence as found:** No reuse licence; ULIF names goroh.pp.ua as an unlawful СУМ copy. Share-alike: not stated. Non-commercial: not stated.
- **Terms as found:**
  - «ми готові вилучати з бібліотечного фонду ті твори авторів, щодо вільного поширення яких є заперечення законних власників авторського права … Для цього автору чи правовласнику необхідно в довільній письмовій електронній формі повідомити про це нас.» — Goroh relies on the library law and removes works on the rights holder's objection; it grants no reuse licence (https://web.archive.org/web/20260730145350id_/https://goroh.pp.ua/Copyright, read 2026-09-27)
- **Also searched:** https://goroh.pp.ua/ (live Cloudflare 403; Wayback 2026-09-24 used)
- **Citation:** Горох (переклад), https://goroh.pp.ua/ — with the underlying work named where known. Label shown: Горох (переклад) — scripts/lexicon/source_attribution.py GOROH_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Which original works does Горох's etymology and translation content come from?

### mphdict — «Цифрові лексикографічні системи української мови» (etym.db, synsets_ua.db) — `mphdict`

- **Permission status:** `open-licence` — The ODbL/DbCL grant covers the database structure; it does not license the ЕСУМ text inside it.
- **Organisation:** uSofTrod (LinguisticAndInformationSystems/mphdict)
- **Role:** Atlas etymology (ЕСУМ-derived database) and synonym chips (Словник синонімів).
- **Fields:** etymology_text, synonym_groups
- **Appears in:** internal, site, dataset — Shown under scripts/lexicon/source_attribution.py MPHDICT_SYNONYMS_LABEL and ESUM_LABEL.
- **Stored in:** data/mphdict/etym.db, data/mphdict/synsets_ua.db
- **Where from:** https://github.com/LinguisticAndInformationSystems/mphdict · Retrieval date not recorded; scripts/mphdict/query.py was added in 35c85b0e46 (2026-07-15); the databases live outside the repo (MPHDICT_DATA_DIR).
- **Licence as found:** ODbL 1.0 (database) / DbCL 1.0 (contents) as far as uSofTrod holds rights; ЕСУМ text rights stay with the Інститут мовознавства (`ODbL-1.0`). Share-alike: yes. Non-commercial: no.
  - ODbL share-alike applies to derived databases; its fit with a CC BY-NC-SA dataset is part of the dataset-licence open question.
- **Terms as found:**
  - «База даних "etym.db" доступна під ліцензією Open Database License http://opendatacommons.org/licenses/odbl/1.0/. Будь-які права на вміст (контент) цієї бази даних ліцензовано під ліцензією Database Contents License https://opendatacommons.org/licenses/dbcl/1.0/.» *(licence text, verbatim)* — The same ODbL/DbCL sentence is given for synsets_ua.db (https://github.com/LinguisticAndInformationSystems/mphdict, read 2026-09-27)
  - «Ми не надаємо доступ до твору Етимологічний словник української мови Інституту мовознавства ім. О.О. Потебні НАН України, а в освітніх цілях демонструємо можливість роботи зі складноструктурованою БД етимологічної системи, яка є нашою оригінальною розробкою.» — "We do not provide access to the work ЕСУМ of the Potebnia Institute; for educational purposes we demonstrate working with the database structure, which is our original development." — the ODbL covers uSofTrod's database, not the ЕСУМ text (https://github.com/LinguisticAndInformationSystems/mphdict, read 2026-09-27)
- **Citation:** mphdict, uSofTrod (ODbL 1.0 / DbCL 1.0), https://github.com/LinguisticAndInformationSystems/mphdict; ЕСУМ © Інститут мовознавства ім. О. О. Потебні НАН України. Label shown: mphdict (ODbL/DbCL): Словник синонімів української мови та Орфографічний словник.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Which printed synonym dictionary is synsets_ua.db built from, and who holds its rights?

### Балла М. І. «Англо-український словник» — `balla`

- **Permission status:** `none`
- **Organisation:** Author М. І. Балла and publishers (Освіта 1996; Чумацький Шлях 2007); digital copy via the bakustarver aggregator
- **Role:** English-gloss fallback (reverse lookup) and EN→UK translation help.
- **Fields:** en_uk_translation
- **Appears in:** internal, site, dataset — 1,005 public payloads mention Балла (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28); also via the slovnyk.me 'ukreng' copy.
- **Stored in:** data/sources.db balla_en_uk, data/lexicon/side/balla_reverse.sqlite
- **Where from:** https://github.com/bakustarver/ukr-dictionaries-list-opensource · Retrieval date not recorded; scripts/rag/convert_dictionaries.py (--balla) was added in b82002a582 (2026-03-24).
- **Licence as found:** All rights reserved (in-print modern dictionary; editions of 1996 and 2007). Share-alike: not stated. Non-commercial: not stated.
- **Also searched:** https://github.com/bakustarver/ukr-dictionaries-list-opensource (AGPL-3.0 repo; no grant from the dictionary's rights holders); https://archive.org/details/enukr1996 (no rights field); https://knygy.com.ua/index.php?productID=9789668272172 (2007 edition on sale)
- **Citation:** Балла М. І. Англо-український словник / Українсько-англійський словник (edition of our copy). Label shown: Українсько-англійський словник (М. Балла) — scripts/lexicon/source_attribution.py BALLA_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Who holds the rights today (the author's heirs or the publisher)?

### ПУЛЬС — Профіль української лексики — `puls`

- **Permission status:** `open-licence`
- **Organisation:** Школа української мови та культури УКУ (О. Синчак, В. Старко, М. Бурак, М. Свистун та ін.)
- **Role:** CEFR level per word for level gating.
- **Fields:** cefr_level
- **Appears in:** internal, site, dataset — 4,048 public payloads carry the PULS CEFR label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db puls_cefr, data/puls/entries.jsonl (scraped by scripts/rag/scrape_puls.py)
- **Where from:** https://puls.peremova.org/ · Retrieval date not recorded; scripts/rag/scrape_puls.py was added in a905c72dfd (2026-03-24).
- **Licence as found:** CC BY-NC-SA 4.0. Share-alike: yes. Non-commercial: yes.
  - For commercial use, contact the PULS team, School of Ukrainian Language and Culture at UCU.
  - The homepage footer reads «© 2026 ПУЛЬС.» and links to the terms page, which grants CC BY-NC-SA 4.0 for the data.
- **Terms as found:**
  - «PULS data are distributed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).» *(licence text, verbatim)* (https://puls.peremova.org/terms, read 2026-10-06)
  - «© 2026 ПУЛЬС.» (https://puls.peremova.org/, read 2026-10-06)
  - «Просимо посилатися на ПУЛЬС: Профіль української лексики (ПУЛЬС) / О. Синчак, В. Старко, М. Бурак, М. Свистун та ін. Львів: Школа української мови та культури УКУ, 2026. — puls.peremova.org» (https://puls.peremova.org/, read 2026-09-27)
- **Citation:** PULS citation above. Label shown: PULS CEFR.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### UberText 2.0 frequency dictionary (ubertext_freq.csv.xz) — `ubertext_freq`

- **Permission status:** `unknown`
- **Organisation:** lang-uk (Дмитро Чаплинський)
- **Role:** Frequency for level gating.
- **Fields:** frequency_count, frequency_tier
- **Appears in:** internal — No UberText label in the public payloads (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28); the local data/ubertext-freq/ holds no data file today.
- **Stored in:** data/ubertext-freq/frequency.db
- **Where from:** https://lang.org.ua/en/ubertext/ · Retrieval date not recorded; the import lives in scripts/rag/convert_phase2.py.
- **Licence as found:** Not found. Share-alike: not stated. Non-commercial: not stated.
- **Also searched:** https://lang.org.ua/en/ubertext/ (no licence statement); https://lang.org.ua/en/corpora/ (its CC BY-NC-SA line belongs to the NER corpus, not UberText); https://aclanthology.org/2023.unlp-1.1.pdf (paper lists "Freely available for download under a permissive license" as a design goal; no licence named); huggingface.co/datasets/lang-uk/UberText-2.0 (auth error)
- **Citation:** Chaplynskyi D. Introducing UberText 2.0: A Corpus of Modern Ukrainian at Scale. UNLP 2023. Label shown: not named on learner pages.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Which licence covers ubertext_freq.csv.xz?

### r2u.org.ua / e2u.org.ua bilingual dictionary portals — `r2u_e2u`

- **Permission status:** `none`
- **Organisation:** Андрій Рисін, Василь Старко, Ю. Марченко, О. Телемко та ін. (constituent dictionaries by their own authors)
- **Role:** Live RU/EN↔UK lookups and a short English-gloss fallback (e2u).
- **Fields:** en_gloss
- **Appears in:** internal, site, dataset — 2,646 public payloads mention e2u.org.ua (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** live lookups only (scripts/rag/source_query.py); nothing stored in bulk
- **Where from:** https://e2u.org.ua/; https://r2u.org.ua/ · Live lookups (scripts/rag/source_query.py); dates are not stored.
- **Licence as found:** All rights reserved (© r2u.org.ua; per-dictionary author permissions). Share-alike: not stated. Non-commercial: not stated.
- **Terms as found:**
  - «© 2026 r2u.org.ua» (https://r2u.org.ua/, read 2026-09-27)
  - «Дякуємо авторському колективу за наданий текст словника й дозвіл на його електронну публікацію» — The authors permitted e2u's electronic publication — a grant to e2u, not to us (https://e2u.org.ua/, read 2026-09-27)
- **Also searched:** https://r2u.org.ua/contacts, https://e2u.org.ua/contacts
- **Citation:** Name the constituent dictionary and its authors, and the portal. Label shown: e2u.org.ua (Rysin, Starko et al.) — scripts/lexicon/source_attribution.py E2U_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### Wikidata (lexemes and items) — `wikidata`

- **Permission status:** `open-licence`
- **Organisation:** Wikidata contributors / Wikimedia Foundation
- **Role:** English-gloss fallback.
- **Fields:** en_gloss
- **Appears in:** internal, site, dataset — 70 public payloads carry the Wikidata label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** live lookups only
- **Where from:** https://www.wikidata.org/ · Live lookups; dates are not stored.
- **Licence as found:** CC0 1.0 (`CC0-1.0`). Share-alike: no. Non-commercial: no.
- **Terms as found:**
  - «structured data in the main, Property, Lexeme, and EntitySchema namespaces are waived using the Creative Commons Zero (CC0)» *(licence text, verbatim)* (https://dumps.wikimedia.org/legal.html, read 2026-09-27)
- **Citation:** Courtesy credit "Wikidata" (not required). Label shown: Wikidata.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### lang-uk/ukrainian-word-stress (stress dictionary trie) — `ukrainian_word_stress`

- **Permission status:** `verbal-granted-written-pending` — The data is ULIF-derived and follows the ULIF permission: verbal permission in 2026-10, per the operator; written confirmation pending. lang-uk's MIT licence covers only the code.
- **Organisation:** lang-uk (code); Український мовно-інформаційний фонд НАН України (ULIF, underlying stress data)
- **Role:** ULIF-derived stress marks on forms via the bundled lang-uk trie.
- **Fields:** stress
- **Appears in:** internal, site, dataset — 19,613 public payloads carry the ukrainian-word-stress label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** installed Python package (bundled trie)
- **Where from:** https://github.com/lang-uk/ukrainian-word-stress; https://github.com/lang-uk/ukrainian-word-stress-dictionary; https://lcorp.ulif.org.ua/dictua/ · Installed Python package; the version in use is the one pinned by the project environment. The operator confirms that the project's stress data comes from the ULIF dictionary; upstream CONTRIBUTING.md and the data repository README document ULIF provenance.
- **Licence as found:** Code: MIT; data: derived from ULIF «Словники України», follows ULIF rights; no licence in the stress data repository. Share-alike: not stated. Non-commercial: not stated.
  - lang-uk's MIT licence covers only the code, not the ULIF-derived stress data.
  - The data's rights and permission follow ULIF; verbal permission in 2026-10, per the operator; written confirmation pending.
- **Terms as found:**
  - «MIT License Copyright (c) 2022 lang-uk» *(licence text, verbatim)* — MIT applies to lang-uk's code only. (https://github.com/lang-uk/ukrainian-word-stress/blob/main/LICENSE, read 2026-10-06)
  - «The stress dictionary shipped with this package (`ukrainian_word_stress/data/stress.trie`) covers about 2.9 million word forms derived from the "Dictionaries of Ukraine" (https://lcorp.ulif.org.ua/dictua/) by ULIF.» (https://github.com/lang-uk/ukrainian-word-stress/blob/main/CONTRIBUTING.md, read 2026-10-06)
  - «Словник наголосів сформовано на основі "Словників України" Українського мовно-інформаційного фонду НАН України» (https://github.com/lang-uk/ukrainian-word-stress-dictionary, read 2026-10-06)
- **Also searched:** https://github.com/lang-uk/ukrainian-word-stress-dictionary (no licence found; licence audit 2026-10-06)
- **Citation:** ULIF «Словники України» stress data, via ukrainian-word-stress / ukrainian-word-stress-dictionary (lang-uk); MIT notice for the code only. Label shown: ukrainian-word-stress.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### The operator's teacher's materials (Combined Master Vocabulary Table, lesson texts) — `teacher_materials`

- **Permission status:** `granted` — Consent recorded in operator decision d2_teacher_consent; the licence is not yet named.
- **Organisation:** The operator's Ukrainian teacher (author); private DOCX supplied by the operator
- **Role:** Teacher vocabulary deck, the teacher's English meanings, reviewed lesson sentences for cloze.
- **Fields:** vocabulary_list, en_meaning_teacher, lesson_sentence
- **Appears in:** internal, site, dataset — Teacher deck (site/src/data/lexicon-teacher-table-deck.json) and reviewed cloze sentences; operator decision 2 covers the site and the dataset.
- **Stored in:** data/sources.db textbooks rows with source_file=private-teacher-lessons-a (scripts/ingest/private_teacher_lessons_ingest.py); site/src/data/lexicon-teacher-table-deck.json (scripts/lexicon/sync_teacher_table_deck.py)
- **Where from:** Private DOCX supplied by the operator (not public) · Supplied by the operator; scripts/ingest/private_teacher_lessons_ingest.py was added in 8e50855c7d (2026-09-05).
- **Licence as found:** No licence; the teacher agrees to use on the site and in the dataset (operator decision 2, 2026-09-27). Share-alike: not stated. Non-commercial: not stated.
  - Lesson sentences publish only after language review and the operator's privacy scan (#8843) — lesson logs may contain the learner's own attempts.
- **Terms as found:**
  - «cloze: 'sentences from the teacher''s lesson texts (operator 2026-09-27: allowed, including publication)'» — Operator decision recorded on the teacher-deck task card (https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8843, read 2026-09-27)
  - «the word list is public by operator decision; example sentences may come from her lessons or from books» (https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8843, read 2026-09-27)
  - «(2) The teacher agrees to her material being used (site and dataset).» — Operator decision 2026-09-27 on #8979 (https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8979, read 2026-09-28)
- **Citation:** Credit in the form the teacher chooses; no personal names in public today (docs/practice/curated-membership-and-sources.md). Label shown: not named on learner pages.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Which credit form does the teacher want (no personal names in public today)?

### Learn Ukrainian project — course-authored glosses, classifications and curation overlay — `course_authored`

- **Permission status:** `open-licence`
- **Organisation:** Learn Ukrainian project (maintainer Krisztian Koos)
- **Role:** Headline English glosses from curriculum vocabulary files, CEFR/course usage, curation decisions, russification commentary.
- **Fields:** en_gloss_course, course_usage, curation_overlay, russification_commentary
- **Appears in:** internal, site, dataset — Course glosses, course usage and curation overlay on every card.
- **Stored in:** curriculum/l2-uk-en/*/vocabulary.yaml, data/atlas.db, site lexicon shards
- **Where from:** https://github.com/learn-ukrainian/learn-ukrainian.github.io · Our own work; the repository history is the record.
- **Licence as found:** CC BY-SA 4.0 (project content) (`CC-BY-SA-4.0`). Share-alike: yes. Non-commercial: no.
  - The maintainer can also license this content under CC BY-NC-SA 4.0 for the dataset (a rights holder may dual-license); an operator decision.
- **Terms as found:**
  - «The curriculum content (Ukrainian prose, dialogues, exercises, wiki articles, plans, translations, and explanations authored for this project) is licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).» *(licence text, verbatim)* (https://github.com/learn-ukrainian/learn-ukrainian.github.io/blob/main/LICENSE-CONTENT.md, read 2026-09-27)
- **Citation:** Learn Ukrainian project, https://github.com/learn-ukrainian/learn-ukrainian.github.io Label shown: Learn Ukrainian.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### Українська Вікіпедія (cached articles) — `wikipedia`

- **Permission status:** `open-licence`
- **Organisation:** Wikipedia contributors / Wikimedia Foundation
- **Role:** Background for encyclopedic words (listed in the current dataset attribution).
- **Fields:** article_extract
- **Appears in:** internal, site, dataset — 24 public payloads carry the Вікіпедія label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db wikipedia
- **Where from:** https://uk.wikipedia.org/ · retrieved 2026-07-07 — sources.db wikipedia.fetched_at spans 2026-04-11 to 2026-07-07.
- **Licence as found:** CC BY-SA 4.0 (and GFDL) (`CC-BY-SA-4.0`). Share-alike: yes. Non-commercial: no.
- **Terms as found:**
  - «Creative Commons Attribution-ShareAlike 4.0 International License ("CC BY-SA 4.0"), and GNU Free Documentation License ("GFDL") ... Reusers may comply with either license or both.» *(licence text, verbatim)* (https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use, read 2026-09-27)
- **Citation:** Link to the article (history) and CC BY-SA 4.0 notice. Label shown: Вікіпедія.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).

### «Етимологічний словник української мови» (ЕСУМ), vols 1–6 (1982–2012) — `esum`

- **Permission status:** `none`
- **Organisation:** Інститут мовознавства ім. О. О. Потебні НАН України (publisher Наукова думка); co-authored by many compilers
- **Role:** Etymology notes and cognate forms on cards.
- **Fields:** etymology_text, cognate_forms
- **Appears in:** internal, site, dataset — 1,604 public payloads mention ЕСУМ (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db esum_etymology, esum_etymology_meta, esum_cognate_forms (OCR of archive.org items etslukrmov1–6; scripts/ingest/esum_ingest.py, scripts/etymology/)
- **Where from:** https://archive.org/details/etslukrmov1; https://archive.org/details/etslukrmov2; https://archive.org/details/etslukrmov3; https://archive.org/details/etslukrmov4; https://archive.org/details/etslukrmov5; https://archive.org/details/etslukrmov6 · Retrieval date not recorded; scripts/ingest/esum_ingest.py (our OCR of the archive.org scans) was added in a8ebd95366 (2026-05-04).
- **Licence as found:** In copyright (co-authored, vol. 6 published 2012 — Art. 31(4)); rights holder not confirmed (Institute and/or Наукова думка). Share-alike: not stated. Non-commercial: not stated.
  - Our text is our own OCR of a third-party upload (archive.org, folkscanomy collection, empty rights fields).
- **Terms as found:**
  - «Етимологічний словник української мови: В 7 т. / Редкол.: О. С. Мельничук (гол. ред.) та ін. – К.: Наук. думка, 1982–2006.» — The Institute lists ЕСУМ as its publication; no reuse statement anywhere on its site (https://www.inmo.org.ua/library.html, read 2026-09-27)
  - «Укладачі: Г. П. Півторак, О. Д. Пономарів, І. A. Стоянов, О. Б. Ткаченко, A. M. Шамота … — К.: Наукова думка, 2012» — Volume 6 (2012) on archive.org — a user upload in the folkscanomy collection with empty rights fields (https://archive.org/details/etslukrmov6, read 2026-09-27)
- **Also searched:** https://www.inmo.org.ua/ (no licence or reuse statement); https://archive.org/about/terms (JavaScript-only; not read)
- **Statute referred to:** `law_art31_term`
- **Citation:** Етимологічний словник української мови / Інститут мовознавства ім. О. О. Потебні НАН України. Т. <vol>, с. <page>. Label shown: «Етимологічний словник української мови» (ЕСУМ, Ін-т мовознавства ім. О. О. Потебні НАН України; mphdict ODbL/DbCL) — scripts/lexicon/source_attribution.py ESUM_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Who holds the economic rights in ЕСУМ today — the Institute, Наукова думка, or the compilers?

### Ukrainian school textbooks (grades 1–11) in sources.db — `textbooks`

- **Permission status:** `none`
- **Organisation:** Individual authors and publishers (e.g. Заболотний, Авраменко, Вашуленко, Карман, Літвінова, Глазова); PDFs via pidruchnyk.com.ua and lib.imzo.gov.ua
- **Role:** Short modern example sentences (class B — short quotations only,
- **Fields:** example_sentence, textbook_chunk
- **Appears in:** internal, site, dataset — Short attributed example sentences (practice, a few Atlas attestations); O3 (2026-10-03, plan v3.5.0 on #6321) makes textbook sections component C9 of the dataset, as the operator's IP responsibility; no reuse licence.
- **Stored in:** data/sources.db textbooks (public rows), textbook_sections; bulk root textbook_chunks/grade-*
- **Where from:** https://lib.imzo.gov.ua/; https://pidruchnyk.com.ua/ · Retrieval dates are not stored per textbook; each row records its source_file.
- **Licence as found:** In copyright (authors/publishers); free public access by law, no reuse licence. Share-alike: not stated. Non-commercial: not stated.
  - LICENSE-CONTENT.md caps direct quotations at ~200 characters.
- **Terms as found:**
  - «на якому у вільному доступі в повному обсязі розміщуються безкоштовні електронні версії підручників» — lib.imzo.gov.ua exists under Art. 75 of the Law on Education to publish full free electronic textbooks — free ACCESS, not a reuse licence (Wayback snapshot 2026-01-03) (https://web.archive.org/web/20260103144939id_/https://lib.imzo.gov.ua/, read 2026-09-27)
  - «Файли надані для ознайомлення.» — pidruchnyk.com.ua (third-party mirror) — "files provided for familiarisation" (https://pidruchnyk.com.ua/, read 2026-09-27)
- **Also searched:** https://shkola.in.ua/polityka/ (privacy policy only); https://zakon.rada.gov.ua/laws/show/2145-19/print (Law on Education, Art. 75(6)-(7))
- **Statute referred to:** `law_art22_quotation`
- **Citation:** Author(s), title, grade, publisher, year, page — for every quoted sentence. Label shown: not named on learner pages.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Does any textbook publisher grant a reuse licence (e.g. for NUS textbooks funded by the state budget)?

### «Український фразеологічний словник» (aggregator copy; probably «Словник фразеологізмів української мови», Наукова думка 2003) — `frazeolohichnyi`

- **Permission status:** `none`
- **Organisation:** Compilers (Білоноженко В. М. та ін.) / publisher Наукова думка — rights holder not confirmed
- **Role:** Idiom verification; ULIF phraseology is the planned idiom source (#8985).
- **Fields:** idiom, idiom_definition
- **Appears in:** internal, site, dataset — 4,059 public payloads carry scripts/lexicon/source_attribution.py PHRASEOLOGY_LABEL; those rows may come from this table or the slovnyk.me 'phraseology' copy.
- **Stored in:** data/sources.db frazeolohichnyi (bakustarver file fl.frasesUkUk.json)
- **Where from:** https://github.com/bakustarver/ukr-dictionaries-list-opensource · Retrieval date not recorded; scripts/rag/convert_dictionaries.py (--frazeolohichnyi) was added in b82002a582 (2026-03-24).
- **Licence as found:** In copyright (co-authored, 2003); no licence found. Share-alike: not stated. Non-commercial: not stated.
- **Also searched:** https://github.com/bakustarver/ukr-dictionaries-list-opensource (AGPL-3.0 repo; no provenance; Info names «Український Фразелогічний Словник»); https://archive.org/details/slov557 (sample entries match the 2003 edition; no rights field)
- **Citation:** Словник фразеологізмів української мови / відп. ред. В. О. Винник. Київ: Наукова думка, 2003 (to be confirmed). Label shown: Фразеологічний словник української мови — scripts/lexicon/source_attribution.py PHRASEOLOGY_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Confirm the edition (probably «Словник фразеологізмів української мови», Наукова думка 2003) and its rights holder.

### Антоненко-Давидович Б. «Як ми говоримо» — `antonenko_style_guide`

- **Permission status:** `none`
- **Organisation:** Heirs of Борис Антоненко-Давидович (d. 9 May 1984) — no contact found
- **Role:** Authority on russianisms and calques for correction notes.
- **Fields:** style_rule_quote, style_entry_text
- **Appears in:** internal, site, dataset — 57 public payloads carry the Антоненко-Давидович label (atlas.db public-route payloads of the 2026-09-11 manifest, published as the atlas-manifest release asset; counted 2026-09-28).
- **Stored in:** data/sources.db style_guide(word, section, text); full text in textbooks (scripts/ingest/antonenko_full_book_ingest.py)
- **Where from:** https://www.ukrlib.com.ua/books/printit.php?tid=4002; https://archive.org/details/hovorymo1970 · Retrieval date not recorded; scripts/ingest/antonenko_full_book_ingest.py was added in f6cafb6cae (2026-05-14).
- **Licence as found:** In copyright until 31 Dec 2054 (Art. 31(2)); rights with the heirs. Share-alike: not stated. Non-commercial: not stated.
- **Terms as found:**
  - «(…23. 07(05. 08). 1899, с. Засулля … — 09. 05. 1984, Київ)» — The author died in 1984; protection runs to the end of 2054 (Art. 31(2)) (https://esu.com.ua/article-42948, read 2026-09-27)
  - «УкрЛіб © 2000 — 2026, Євген Васильєв При використанні матеріалів сайту, посилання на УкрЛіб обов'язкове.» — The ukrlib.com.ua copy asks for a link; it grants nothing for the author's rights (https://www.ukrlib.com.ua/books/printit.php?tid=4002, read 2026-09-27)
- **Also searched:** https://archive.org/details/hovorymo1970 (1970 edition, user upload, no rights field); https://r2u.org.ua/yak-my-hovorymo/ (404)
- **Statute referred to:** `law_art31_term`, `law_art22_quotation`
- **Citation:** Антоненко-Давидович Б. Як ми говоримо. <edition, year, page>. Label shown: «Як ми говоримо» Антоненка-Давидовича — scripts/lexicon/source_attribution.py DAVYDOV_LABEL.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the Atlas/practice fields carrying this source's label; the same fields in the open dataset export; the stored copies listed in stored_in (deleted only with the operator's authorisation).
- **Open questions:**
  - Which edition is our copy, and who represents the author's heirs?

### Ukrainian Lessons Podcast notes and Anna Ohoiko's books (private references) — `ulp_private`

- **Permission status:** `none`
- **Organisation:** Anna Ohoiko (Ukrainian Lessons)
- **Role:** Private reference for pedagogy only; never quoted and never a card field source.
- **Fields:** reference_text
- **Appears in:** internal — Private pedagogy reference; its text is not on the site or in the dataset.
- **Stored in:** data/sources.db textbooks rows ulp-*-lesson-notes, anna-ohoiko-* (from the operator's private files under docs/references/private/, gitignored)
- **Where from:** The operator's own purchased copies under docs/references/private/ (gitignored) · Supplied by the operator; not fetched from the website.
- **Licence as found:** All rights reserved (Anna Ohoiko). Share-alike: not stated. Non-commercial: not stated.
- **Terms as found:**
  - «This Agreement does not transfer to you any intellectual property owned by Ogoiko, Anna or third parties, and all rights, titles, and interests in and to such property will remain (as between the parties) solely with Ogoiko, Anna.» (https://www.ukrainianlessons.com/terms-and-conditions/, read 2026-09-27)
  - «(h) to spam, phish, pharm, pretext, spider, crawl, or scrape» — Listed among prohibited uses of the website (https://www.ukrainianlessons.com/terms-and-conditions/, read 2026-09-27)
- **Citation:** Not shown; cited only in internal notes as Ukrainian Lessons (Anna Ohoiko). Label shown: not named on learner pages.
- **Removal:** [GitHub issue](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues) — the stored copies listed in stored_in (deleted only with the operator's authorisation).
