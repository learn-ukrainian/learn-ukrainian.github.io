# Pinned public preview

The optional `/lexicon-v2/` preview consumes the published `word-cards-v0.1`
release. It leaves the current Atlas and publication pointers unchanged.
This candidate preview does not certify language data or authorize a switch.

## Public build inputs

Download `word-cards.jsonl` and `manifest.json` from the
[published release](https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/tag/word-cards-v0.1)
into managed scratch. Verify these immutable inputs before building:

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| word-cards.jsonl | 2879813 | `45bd9c9325a3b4221c86d1663d784e96a7edc096674415445d37113f793189e6` |
| manifest.json | 3292 | `ca182bf5829f3ed4daa80c2394eb87e28879c3f1dc5088eef689f495b97e4f75` |

Set `ATLAS_WORD_CARD_PREVIEW=1` and `ATLAS_WORD_CARD_RELEASE_PATH` to that
directory. Leave `PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS` unset.
The public selector freezes release version `v0.1.0-pilot` and both hashes.
An optional `ATLAS_WORD_CARD_RELEASE_PIN` must match all frozen fields.
Missing or invalid artifacts produce refusal summaries, never fixture fallback.
Public mode refuses synthetic provenance. No runtime download occurs.

With Delivery's supported build artifacts prepared, run the existing Astro
build from `site/` with those variables. Delivery owns artifact preparation,
publication wiring, deployment and deployed noindex proof. Local route-only
browser builds use the same route, components and Astro configuration without
reading protected stores or hydrating the rest of the site.

## Pages publication

Every `deploy-pages.yml` run publishes this preview with the ordinary site;
automatic-deployment eligibility is unchanged. The committed pin
`site/src/data/word-card-preview-release.pointer.json` records the release tag and
both byte sizes and digests above. `scripts/deploy/prepare_word_card_preview.py
prepare` downloads only those two public assets, without a token, into runner
scratch. It refuses a size or digest mismatch, a manifest that disagrees with
the pin, synthetic provenance, and any `PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS`
value, including an empty one. The tag only locates the assets.

`Build Site` then sets `ATLAS_WORD_CARD_PREVIEW=1` with the verified directory
and pin, and refuses to start if the controls flag is set. After the build,
`verify-dist` reads Atlas's committed route inventory
`site/src/lib/lexicon/word-card-preview-route-inventory.json`
(`word-card-preview-route-inventory.v1`). Atlas owns the route set; Delivery
freezes no route count. The inventory's release must equal the pin, including
both byte sizes. Its card dispositions must cover every verified release card
exactly once, with the release's card kind. Every declared count is recomputed:
source cards and citations from the release rows, and pages, entries,
proper-name dispositions, routes and routes per class from the inventory's own
cards and routes. Each route must be a unique `/lexicon-v2/` path whose `href`
is its percent-encoding.

The built site must then contain exactly the inventoried routes, each with a
single `noindex, nofollow` robots meta. No emitted sitemap may list a preview
URL, and no page may contain refusal text or a committed synthetic-fixture
identifier. A missing, malformed or stale inventory fails, as does any
disagreement. Any failure stops the job before the size gate and upload. The
inventory is Atlas's file, so a build of a tree without it fails closed.

Changing the pin is content drift, so a new release needs the manual
`workflow_dispatch` route. `robots.txt` remains unchanged (`Allow: /`); page
metadata and sitemap exclusion keep the preview out of indexes.

The public configuration emits the routes and per-class counts recorded in
that inventory's `counts`. Every preview route has `noindex, nofollow`;
sitemap generation excludes them.
With `ATLAS_WORD_CARD_PREVIEW` unset, no preview routes are generated.

## Values, coverage and unresolved dependencies

All 150 rows are producer-declared `CANDIDATE`, with 0 `CERTIFIED` and 2978
field citations. Values and citation strings remain literal, and assertions
stay separate. Report links open a user-controlled issue draft containing only
release, dataset, card, version, assertion and field identifiers.

Every producer-declared `known_gaps` array is empty. The UI separately measures
absent canonical field classes, including definitions and examples. Summaries
also show manifest filtering counts: 29 PULS assertions and 156 ULIF assertions.
Empty declared gaps do not establish completeness.

The 105 `PULS citation above.` strings and 977 VESUM `<used version>` strings
remain unchanged and have visible attribution-gap states owned by Data.
Readable credits come directly from each citation. Links use only existing
authoritative URLs in those strings. The preview invents no bibliographic
metadata or source-register associations.

The existing `pairCurrent` rule is unchanged. The release has no eligible
explicit `atlas0:slug` keys: 0/150 paired, 150/150 explicitly unpaired and
0 actual comparisons. The historical controlled snapshot is not the public
baseline. Data owns an authoritative identity relation; Atlas owns subsequent
current-page integration. PP-03, PV-02 and the full section 9 comparison gate
remain open. No equality, better/worse or switch-readiness verdict is inferred.

## Reproduce local proof

Run the three focused Vitest files `word-card-preview.test.tsx`,
`word-card-release.test.ts` and `word-card-preview-inputs.test.ts` in
`site/tests/unit/`. For historical browser controls, explicitly set
`PUBLIC_ATLAS_WORD_CARD_PREVIEW_CONTROLS=1` while building the local test server
and run `site/e2e/word-card-preview.spec.ts`. This flag is only for controlled
test builds and must be absent from public builds.

For actual-release browser proof, additionally set
`ATLAS_WORD_CARD_PUBLIC_PROOF_PATH` to the verified asset directory and
`ATLAS_WORD_CARD_EXPECTATIONS_PATH` to the driver's independently frozen
expectations file, digest
`1e86726fb4244c2e31b7a2f67ef7d52fc78ef3fc1de3d1659d1c9b06c8d7a68a`.
The spec checks both presentations of all 2978 assertions against those hashes,
every emitted preview route, noindex, attribution gaps, summaries, report links and complete
built HTML/JS/XML fixture-sentinel scans. It freezes sentinels before building
and records markers shared with real data separately. Refusal and flag-off
tests use scratch copies, preserving historical producer inputs.

These author checks are local mechanical proof. Atlas retains independent
exact-head review, same-head branch and merge-group CI, merge, merged browser
proof, typed lifecycle evidence and common cleanup. Delivery retains the
supported public build and deployed noindex proof. Data/Atlas pairing and Data
attribution dependencies remain required; the broader issue stays open.
