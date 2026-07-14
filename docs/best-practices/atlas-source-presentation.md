# Word Atlas source presentation — authoritative-source guideline

> **Origin (binding, user directive 2026-07-14):** УМІФ НАН України's official notice
> «КОРИСТУЙТЕСЬ ДОСТОВІРНИМИ ДЖЕРЕЛАМИ!»
> (https://www.ulif.org.ua/koristuities-dostovirnimi-dzhierielami) is the guideline
> for how the Word Atlas presents dictionary sources.

## What УМІФ states

- Sites such as **goroh.pp.ua, sum.in.ua, slovnyk.me** republish the electronic
  СУМ-11 and СУМ-20 **unlawfully, without crediting the authors**; they are not
  official academic editions and may contain inaccuracies.
- СУМ-20 is compiled by **УМІФ НАН України** and the **Інститут мовознавства
  ім. О. О. Потебні НАН України** under the state National Dictionary Base program.
- Official electronic editions: **sum20ua.com**, **services.ulif.org.ua/expl**
  (СУМ-20); **www.inmo.org.ua/sum.html** (СУМ-11). The authors take no
  responsibility for any other site's copies.

## Presentation rules (learner-facing Atlas pages, search, practice)

1. **Attribute works and authors, never aggregator mirrors.** A source line names
   the dictionary and its institutional/personal authors — e.g.
   «Словник української мови у 20 томах (УМІФ НАН України, Ін-т мовознавства
   ім. О. О. Потебні)» — never `slovnyk.me: …` or `goroh: …` as the visible authority.
2. **Official links only.** When a source line links out, it links the official
   electronic edition (sum20ua.com / services.ulif.org.ua/expl; publisher pages for
   non-СУМ dictionaries). Mirror URLs (slovnyk.me, goroh.pp.ua, sum.in.ua) never
   appear in learner-facing hrefs.
3. **Non-СУМ dictionaries reached via mirrors follow the same rule.** Rows obtained
   through slovnyk.me for Караванський's synonym dictionary, Балла (ukreng), ВТС etc.
   are attributed to the actual dictionary and author («Словник синонімів
   С. Караванського»), with mirror provenance kept internal only.
4. **СУМ-11 stays unsurfaced** (decision 2026-06-25 — compromised Soviet authority);
   this guideline does not reopen that.
5. **Internal use of mirror data is a pipeline concern, not a presentation one.**
   Mirror-derived rows may seed candidates and cross-checks, but (a) they carry an
   accuracy caveat internally, (b) СУМ-20 content surfaced to learners should be
   re-verified against the official electronic edition where feasible
   (`mcp__sources__query_ulif`, `query_sum20`, sum20ua.com), and (c) the manifest's
   internal `source`/`source_url` provenance fields must be MAPPED to compliant
   attribution at render/label-generation time.

## Why this also serves the mission

Attributing the actual Ukrainian academic institutions — not scraping mirrors — is
both the lawful posture УМІФ requests and the decolonized-authority posture of this
project: learners see that Ukrainian lexicography is a living state-academic
enterprise with named institutions, not an anonymous internet commons.

## Implementation status

Tracked in the issue referenced by this doc's introducing PR: source-label
generation in `scripts/lexicon/enrich_manifest.py` (e.g. `_relation_source_label`,
translation source lines) currently emits `slovnyk.me: …` strings that ship into
learner-visible section labels — these migrate to structured
`{dictionary, authors, official_url}` attribution.
