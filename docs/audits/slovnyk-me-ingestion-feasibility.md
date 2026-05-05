# slovnyk.me ingestion feasibility

**Issue:** #1715
**Date:** 2026-05-05
**Decision:** Do not bulk-ingest slovnyk.me full text. Implement bounded per-word
URL-reference/snapshot ingestion plus live direct-entry lookup. Robots
permission is treated only as crawl permission, not as a copyright license.

## Checks performed

- `https://slovnyk.me/robots.txt` allows `/dict/...` direct dictionary pages,
  but disallows `/search`, `/terms`, and `/feedback`. The ingester and MCP
  lookup use only `/dict/{slug}/{word}` and do not call `/search`. This is a
  robots compliance finding, not a reuse-license finding.
- `https://slovnyk.me/` lists the hosted dictionaries and exposes stable
  dictionary slugs such as `newsum`, `sum`, `hrinchenko`, `holoskevych`,
  `obsolete_words`, `bukovina`, `franko`, `slang_lviv`, `davydov`,
  `synonyms_karavansky`, `phraseology`, `engukr`, `rusukr`, and `ukrrus`.
- No public slovnyk.me data dump, API, or upstream GitHub repository was found
  during web/GitHub search. The site publishes a gzip sitemap, but using that
  as a crawl seed would amount to bulk mirroring and is out of scope.
- The `/terms` path returns HTTP 200 to `HEAD`, but it is disallowed by
  `robots.txt`, so I did not crawl or parse it.
- ULIF/NAS Ukraine publicly warns that sites including `slovnyk.me` use
  electronic versions of СУМ and СУМ-20 without authorization and that those
  are not official academic editions. Technolex summarizes the same warning and
  points to official `sum20ua.com` / `services.ulif.org.ua/expl` routes for
  СУМ-20.

## Ingestion decision

Bulk text ingestion is rejected for this PR. The legal/source-integrity posture
is stronger than a normal "no explicit terms" site: the official СУМ-20 owner
has explicitly objected to redistributed copies on slovnyk.me. Non-commercial
educational use does not automatically create a general redistribution license,
and Ukrainian copyright exceptions are narrower than US-style fair use.

Dictionary copyright posture is mixed:

- `holoskevych` (1929) and some older author-work dictionaries are lower risk
  / likely public-domain or public-domain-adjacent, but still cited.
- `newsum` (СУМ-20, 2010–), `slang_lviv` (2009), and other modern dictionaries
  remain copyright-sensitive.
- Overlap dictionaries already available through canonical local tools are
  blocked in the new slovnyk.me search/ingest path: `sum`, `hrinchenko`,
  `davydov`, `phraseology`, and `engukr`.

This PR therefore implements:

- `scripts/ingest/slovnyk_me_ingest.py` for explicit per-word fetching only.
- `slovnyk_me_entries` rows in `data/sources.db` with source URL, dictionary
  slug, bounded snippet/text, modern/dialect/Russianism flags, and
  `sovietization_risk`.
- A conservative default storage cap of 200 text characters per fetched row.
- No sitemap crawl, no `/search` crawl, no full-dictionary mirror.
- MCP live fallback that fetches only direct `/dict/{slug}/{word}` pages for the
  requested headword or a known spelling alias.

## Dictionary scope

Default `search_slovnyk_me` scope targets gaps instead of duplicating existing
local tools:

- `newsum` / `vts` for modern explanatory attestation.
- `holoskevych`, `obsolete_words`, `bukovina`, `franko`, `slang_lviv` for
  heritage, regional, historical, and dialect attestation.

Existing local tools remain independent and are not reingested:

- Грінченко 1907: `search_grinchenko_1907`
- ЕСУМ vol. 1: `search_esum`
- Балла EN to UK: `translate_en_uk`
- Антоненко-Давидович partial index: `search_style_guide`

The merger `search_heritage` calls those existing functions and merges their
results with slovnyk.me rows. It does not copy existing Грінченко/ЕСУМ/Балла/
Антоненко-Давидович data into the slovnyk.me table.

## Sovietization scan on СУМ-20 sample

The same `sovietization_risk` classifier used for СУМ-11 is applied to
slovnyk.me rows, including СУМ-20 rows. A direct-entry spot check was run
against `newsum` on 2026-05-05:

| Word | Result |
| --- | --- |
| `блакитний` | risk 0 |
| `кобіта` | risk 0 |
| `гаразд` | risk 0 |
| `ленінізм` | no СУМ-20 row found |
| `більшовик` | risk 1, keyword `більшов` |
| `радянський` | risk 1, keywords `радянськ`, `срср` |
| `національний` | risk 0 |
| `прапор` | risk 0 |
| `школа` | risk 0 |
| `центр` | risk 0 |
| `шлях` | risk 0 |

Conclusion: СУМ-20 is much cleaner than СУМ-11 on the sampled neutral words,
but it is not treated as categorically clean. Ideological headwords can still
carry Soviet-era markers, so rows preserve `sovietization_risk` and
`sovietization_keywords` for reviewers.

## Heritage-defense behavior

`search_heritage` ranks evidence as follows:

1. Грінченко 1907 exact/prefix rows: strong pre-Soviet Ukrainian attestation.
2. ЕСУМ rows, with a bonus when Proto-Slavic markers appear.
3. slovnyk.me regional/historical rows, then modern explanatory rows.
4. Style-guide Russianism/calque warnings are included but demoted.

This ranking is designed for writer/reviewer prompts: if a word appears in
pre-Soviet, etymological, or regional Ukrainian sources, it should not be
rejected merely because it looks unfamiliar or has Polish contact history. The
`кобета` user-facing spelling is normalized to the attested `кобіта` row so the
Lviv/regional evidence is surfaced and not classified as Russianism.
