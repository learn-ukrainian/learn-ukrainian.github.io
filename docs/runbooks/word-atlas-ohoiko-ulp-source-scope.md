# Word Atlas Ohoiko / ULP Source Scope

This note defines what the Atlas source-inventory lane may use from Anna
Ohoiko / Ukrainian Lessons material without crossing into proprietary lesson
content.

## Current Safe Source

The only committed Anna Ohoiko lexical source currently approved for Atlas
headword intake is the local abetka material:

- `curriculum/l2-uk-direct/a1/abetka-1.yaml`
- `curriculum/l2-uk-direct/a1/abetka-2.yaml`
- `curriculum/l2-uk-direct/a1/abetka-3.yaml`
- `curriculum/l2-uk-direct/a1/abetka-4.yaml`

Those modules contain public YouTube pronunciation-video metadata and explicit
`key_word` rows. The matching inventory is:

- `data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml`

Current committed coverage is complete for that source: 4 abetka modules, 33
`key_word` rows, and 33 Ohoiko source-inventory headwords.

## Link-Only Sources

The Ukrainian Lessons resource indexes are useful for curriculum alignment and
for deciding which public articles or podcast episodes to recommend:

- `docs/resources/ukrainianlessons/blog_db.json`
- `docs/resources/ulp-article-mappings.yaml`
- `docs/resources/ulp-articles-index.yaml`
- `docs/resources/podcasts/raw/episode_021.html`
- `docs/resources/podcasts/raw/episode_022.html`

These files are not an approved lexical corpus. The resource policy says ULP is
inspiration-only and link-only: study patterns, sequence, and topics, but do not
copy lesson vocabulary or premium notes. Public episode pages advertise
vocabulary lists as premium material; the committed raw HTML does not expose the
lists themselves.

## Not In Scope Without A New Decision

Do not create Atlas headwords from these sources unless a separate reviewed
source decision explicitly approves the exact rows:

- premium ULP lesson notes, PDFs, flashcards, or transcripts
- Ohoiko books that are not committed as source-inventory-safe headword rows
- topic labels from resource metadata, such as `food`, `family`, or `cases`
- public article titles when the title only names a topic, not an explicit
  Ukrainian headword list

## Next Valid #3933 PR Shapes

A safe follow-up PR may do one of these:

- add a manually reviewed Ohoiko/ULP headword inventory where every row cites a
  public, non-premium source locator and includes review notes
- add reviewed decision-ledger rows for already-generated Ohoiko candidates
- publish an already-approved Ohoiko batch to Atlas browse/search only

Daily Word, Practice, and cloze admission must remain separate
`surface_admission` decisions. Missing `surface_admission` means Atlas
browse/search only.
