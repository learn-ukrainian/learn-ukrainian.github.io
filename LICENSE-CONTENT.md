# License — Curriculum Content

**TL;DR**: The curriculum content (Ukrainian prose, dialogues, exercises, wiki articles, plans, translations, and explanations authored for this project) is licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**. The software that builds it (Python scripts, TypeScript components, CI, tooling) is licensed separately under MIT — see `LICENSE` at the repository root.

---

## What this file covers

This content license applies to everything in:

- `curriculum/**/*.md` — module prose
- `curriculum/**/activities/*.yaml` — activity definitions
- `curriculum/**/vocabulary/*.yaml` — per-module vocabulary
- `curriculum/**/plans/*.yaml` — module plans and outlines
- `curriculum/**/orchestration/**/*.md` — AI-generated orchestration notes
- `wiki/**/*.md` — compiled reference articles
- `starlight/src/content/docs/**/*.mdx` — rendered public site content
- `docs/l2-uk-en/*.md` — curriculum design docs (when they're teaching content, not tooling docs)

It does NOT cover:

- `scripts/**` — build tooling (MIT, see `LICENSE`)
- `starlight/src/components/**` — React component code (MIT, see `LICENSE`)
- `data/sources.db` and anything under `data/` — third-party source material under the licenses of the original authors (see "Third-party source material" below)
- `docs/references/private/` — copyrighted materials for the maintainer's personal verification only, NEVER redistributed
- `docs/resources/ukrainianlessons/**` — Ukrainian Lessons Podcast (ULP) commercial reference material, license-restricted, NEVER copy or redistribute

---

## The CC BY-SA 4.0 license in plain language

You are free to:

- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:

- **Attribution** — You must give appropriate credit to the learn-ukrainian project (a link to https://learn-ukrainian.github.io is sufficient), provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

No additional restrictions. You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

The full legal text: https://creativecommons.org/licenses/by-sa/4.0/legalcode

---

## Why CC BY-SA 4.0

- **Share-alike is the whole point.** This curriculum exists to be copied, translated, adapted, and built upon. A share-alike clause keeps derivative works open — a fork that adds better explanations for German learners should be available to everyone, just like the original.
- **Commercial use is explicitly allowed.** A Ukrainian language school that prints a workbook from our modules is welcome, provided they attribute us and distribute the printed content under the same license. We want the materials in classrooms, not just online.
- **Attribution matters.** The project took hundreds of hours of native speaker review, LLM reasoning, and research. "Based on learn-ukrainian" is the minimum acknowledgment we ask for.
- **CC BY-SA 4.0 is widely understood.** It's the license Wikipedia uses. Most people know what it means without reading the legal text.

---

## Third-party source material

The curriculum is built with extensive reference to third-party sources. The handling of each is specified below.

### Ukrainian school textbooks (RAG corpus)

The project maintains a SQLite FTS5 index at `data/sources.db` containing ~23,000 chunks from Ukrainian school textbooks (grades 1-11) published by Заболотний, Авраменко, Вашуленко, Карман, Літвінова, Глазова, Bolshakova, and others. These are copyrighted works owned by their respective publishers.

**Fair use boundaries** (applied during wiki compilation and module authoring):

1. **Internal retrieval only.** Full textbook chunks are used as context for LLM generation and are never copied verbatim into module content. The wiki compilation prompts explicitly require the writer to synthesize information across sources and cite chunks by ID, not quote them at length.
2. **Maximum 200 characters per direct quotation.** Any direct quotation from a textbook that exceeds ~200 characters is a copyright compliance violation and must be paraphrased. Longer quotes are permitted only from public-domain works (chronicles, legal documents, etc. — see the "Primary sources" category below).
3. **Transformative use.** Our modules are pedagogically different from the source textbooks — same grammar topic, different presentation, different examples, different audience (English-speaking L2 learners). The transformation is substantive, not cosmetic.
4. **Educational non-profit use.** The curriculum is distributed free-of-charge with no ads, subscriptions, or paywalls.
5. **Attribution.** Every wiki article cites its sources with textbook author + grade + chunk ID. Every module's Ресурси tab lists the referenced textbooks.

The fair-use analysis above is based on U.S. Section 107 factors. If you intend to redistribute this work in a jurisdiction with different fair-use laws, consult your own counsel first.

### Primary historical and literary sources

Works published before 1924 (or otherwise in the public domain) are freely quotable in full. These include:

- The Primary Chronicle (Повість минулих літ), Галицько-Волинський літопис, Козацькі літописи
- Shevchenko, Franko, Ukrainka (full texts)
- Pre-1924 legal documents (Статути Великого князівства Литовського, etc.)
- Bylyny, dumas, folk songs collected by 19th-century ethnographers

These materials are stored in `data/sources.db` and referenced via the `literary` and `external` tables. Module content may quote them at any length, with attribution (author + work + year + chunk ID).

### Wikipedia

The curriculum uses Ukrainian and English Wikipedia articles as background context for seminar tracks (HIST, BIO, LIT, etc.). Wikipedia content is CC BY-SA 4.0 (same license as ours), so wiki-to-wiki attribution is straightforward: any derived content carries the Wikipedia attribution link in the wiki article's source list.

Wikipedia is NEVER cited as the primary source for historical dates, names, or events in published modules. The writer prompts (see `scripts/wiki/prompts/compile_article.md`) explicitly require primary-source citations and mark Wikipedia-only claims with `<!-- VERIFY -->`.

### External blogs, podcasts, and YouTube

- **ukrainianlessons.com** (Ukrainian Lessons Podcast, Anna Ohoiko) — **commercial, all rights reserved.** We may reference their free blog articles as external resources (link out only) but NEVER copy content from the paid ULP membership. The relationship is understood by the ULP author; see `docs/resources/external_resources.yaml` for the referenced URL set.
- **Реальна Історія (Akím Galímov), imtgsh, Istoria-Movy, Speak Ukrainian, Red Purple Ukrainian** — YouTube channels with free-to-view content. Subtitle transcripts are used internally for wiki compilation as context, not republished. Links to the original videos appear in module Ресурси tabs for learners.
- **Dobra Forma (opentext.ku.edu)** — Creative Commons licensed by the University of Kansas. We reference the URLs; derivative teaching material is separately attributed.
- **Горох (goroh.pp.ua), VESUM** — linguistic dictionaries, freely available for educational use. Never redistributed in bulk; used only as query services.

### Dictionaries

The following dictionaries are ingested as SQLite FTS5 indices for internal linguistic verification only. They are NOT republished:

| Dictionary | License / Source | Use |
|---|---|---|
| **СУМ-11** | Public domain (Соглашение, Академія наук УРСР 1970-1980) | Definitions |
| **Грінченко 1907** | Public domain (100+ years old) | Etymology, historical forms |
| **VESUM** | [MIT-ish, morphological database](https://github.com/brown-uk/dict_uk) | Lemma verification, POS tagging |
| **Балла EN→UK** | Historical work (copyright expired) | Translation assistance |
| **Антоненко-Давидович «Як ми говоримо»** | Copyrighted (Антоненко-Давидович estate). Used under fair-use for linguistic verification; individual style-rule citations in module content are limited to <200 chars. | Calque / Russianism detection |
| **Фразеологічний словник** | Copyrighted. Same fair-use boundaries as textbooks. | Idiom verification |
| **Правопис 2019** | Public (Академія наук України) | Orthography rules |

---

## Contributions

Content contributed to this project (module text, exercise YAML, wiki article improvements, translations, corrections) is licensed under the same CC BY-SA 4.0 as the rest of the curriculum. By submitting a pull request, you agree that your contribution is CC BY-SA 4.0 licensed.

If you contribute code (not content), that's MIT — see `LICENSE`. The distinction matters: content goes out under CC BY-SA so forks stay open, code goes out under MIT so it can be freely integrated into other projects.

---

## Attribution boilerplate

When reusing material from this project, the following attribution line is sufficient:

> Based on the [learn-ukrainian curriculum](https://learn-ukrainian.github.io), licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

For modified derivative works:

> Derived from the [learn-ukrainian curriculum](https://learn-ukrainian.github.io) (CC BY-SA 4.0). Modified by {your name / org}.

---

## Questions

Licensing questions go to issues on GitHub or the maintainer directly. The above is a best-effort plain-language summary of the legal position — it is not legal advice. If you need formal permissions or have commercial redistribution questions beyond the standard CC BY-SA 4.0 terms, open an issue and we'll figure it out.

Last updated: 2026-04-11 (#1092)
