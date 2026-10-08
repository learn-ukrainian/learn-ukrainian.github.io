# Collector transport behavior (#8999)

This is a source-code inventory, not a declaration that every collector is compliant.
The denominator is **29 direct transport modules, 7 transport consumers/wrappers,
and 4 matching local builders: 40 modules** in the original inventory. Packet A
repairs seven of those direct-transport rows and the SUM-20 ingest wrapper. The
glossary collector now delegates its former direct curl operation to the owned
filler helper; its original inventory slot is retained. The local blog builder
needs no transport change. Every other row below records a code-level residual,
its owner and the follow-up condition. No crawl or paid call was used as proof.

The inventory includes dictionary, learning, textbook and literary/heritage source
collectors. Operational APIs, model providers, repository artifact hydration,
link-audit diagnostics and local-only dictionary/data readers are outside this
collector denominator. A source URL in a record is not a network operation.

## Reproduce the inventory

Search tracked source code and follow wrappers/importers, rather than relying on
script names alone:

```sh
rg -n 'requests\.(get|post|head|Session)|httpx\.|urlopen|urllib.request|"curl"|yt_dlp' scripts
rg -n 'slovnyk\.me|sum20ua\.com|ulif\.org|ukrainianlessons\.com|goroh\.pp|e2u\.org|kaikki\.org' scripts
rg -n 'sum20_lookup|_fetch_slovnyk_entry|_fetch_slovnyk_outcome|crawl_ulp|fetch_sum20_wordid' scripts tests
```

The first search includes false positives such as ordinary mapping `.get()` calls;
read the call site and classify actual external source transport. Named iTunes
calls are inside `crawl_ulp.py`; E2U/Wikidata/GRAC enrichment call sites share an
inventory row with the Slovnyk collector but do not share its host stop state.

## Direct transport inventory

All unresolved rows are owned for triage by **codex-atlas**. The condition for
completion is an explicitly bound ownership packet, implementation evidence and
exact-head cross-family review; this worker does not edit those paths or declare
whole-issue completion.

| Module | External source/transport | Evidence and disposition |
| --- | --- | --- |
| `scripts/lexicon/fill_slovnyk_sum20_cache.py` | slovnyk.me / curl | Fixed in owned scope: identity, robots floor, immediate stop; existing JSON payloads retained. |
| `scripts/lexicon/enrich_manifest.py` | slovnyk.me; GRAC; E2U; Wikidata | Slovnyk transport fixed; all configured agents include public contact. GRAC/E2U/Wikidata transport remains a scope delta below. |
| `scripts/lexicon/sum20_lookup.py` | official SUM-20 | Fixed in owned scope: identity, robots floor, search/article stops, no sibling fetch after denial. |
| `scripts/crawl/crawl_ulp.py` | iTunes; Ukrainian Lessons | Fixed in owned scope: identity, robots floor, terminal stop before output replacement or catalog fallback. |
| `scripts/lexicon/admit_textbook_book_glossary.py` | slovnyk.me / curl | Fixed in Packet A: reuses honest curl/robots/stop transport; partial successful cache saved, denial never stored as a miss; CLI exit 1. |
| `scripts/lexicon/runner/fetch_ulif_20k.py` | ULIF | Noncompliant: 403/429 classified RetryableFetch; resumable 429 ledger. Packet C; coordinate #10111 and active ULIF ownership before repair. |
| `scripts/lexicon/runner/fetch_ulif_homonyms.py` | ULIF | Noncompliant: 403 stops, but 429 retries up to exhaustion; no robots preflight at the fetch boundary. Packet C; coordinate active ULIF ownership. |
| `scripts/lexicon/tools/dump_ulif.py` | ULIF | Noncompliant: 403/429 enters backoff loop. Packet C; coordinate #10111 and active ULIF ownership. |
| `scripts/lexicon/mine_wikipedia_relations.py` | Wikipedia API | Noncompliant: _api_get retries 429; no robots preflight. Remaining harvester packet. |
| `scripts/wiki/slovnyk_me.py` | slovnyk.me | Outside A: direct requests.get follows redirects and has no robots preflight; does not latch process access stops. Packet B; coordinate sources owner. |
| `scripts/wiki/sum20_official.py` | official SUM-20 | Fixed in Packet A: honest identity/contact, shared observed robots floor, immediate 403/429/challenge stop; 404/network/5xx and numeric terminal evidence retained. |
| `scripts/wiki/fetch_wikipedia.py` | Wikipedia API | Noncompliant: _api_get retries 429; no robots preflight. Remaining harvester packet. |
| `scripts/wiki/fetch_external_sources.py` | YouTube metadata/transcripts | Noncompliant: browser identity on metadata GET, 429 retries in yt-dlp path; no observed robots floor. Remaining harvester packet. |
| `scripts/ingest/dictionary_acquisition.py` | slovnyk.me; official SUM-20 | Fixed in Packet A: existing helper preflight/pacing and challenge pre-parser; 429 blocked for both dictionaries; durable blocked-job state retained. |
| `scripts/ingest/goroh_etymology_ingest.py` | Goroh | Outside A: 429 raises StopIngest, other HTTP errors raise; no observed robots floor or process-wide challenge stop. Remaining harvester packet. |
| `scripts/ingest/grac_frequency_ingest.py` | GRAC | Outside A: terminal 403/429 already halt; identity lacks public contact and no observed robots floor/challenge pre-parser. Remaining harvester packet. |
| `scripts/ingest/pravopys_2019_ingest.py` | Pravopys | Outside A: one PDF GET raises on HTTP failure; identity lacks public contact, no robots preflight/challenge detection. Remaining harvester packet. |
| `scripts/ingest/resource_catalogue_ingest.py` | learning-resource URL probes | Outside A: HEAD/GET link probes follow redirects, use default library identity and lack robots preflight/challenge detection. Remaining harvester packet. |
| `scripts/ingest/vps_dialect_ingest_standalone.py` | dialect source snapshots | Noncompliant: fetch_page retries 429/503; no observed robots floor. Remaining harvester packet. |
| `scripts/ingest/wiktionary_etymology_ingest.py` | Wiktionary API | Outside A: single dump urlopen with project identity; no observed robots floor or explicit process access/challenge latch. Remaining harvester packet. |
| `scripts/ingest/zno_ingest.py` | exam-source documents | Noncompliant: browser User-Agent in document urlopen; no observed robots floor/challenge latch. Packet D. |
| `scripts/rag/source_query.py` | Wikipedia; GRAC; ULIF; R2U; E2U; Goroh; Wiktionary; Wikidata; Pravopys; slovnyk.me | Noncompliant: shared browser identity and long-lived MCP transport semantics require separately approved handling. Packet B; sources owner and #9628 coordination. |
| `scripts/rag/scrape_diasporiana.py` | Diasporiana | Outside A: shared project Session, no robots preflight/challenge latch. Remaining harvester packet. |
| `scripts/rag/scrape_litopys.py` | Litopys / curl | Noncompliant: curl -sL with referer, no project/contact identity or observed robots floor/status stop. Remaining harvester packet. |
| `scripts/rag/scrape_puls.py` | PULS | Outside A: project/contact urlopen, no robots preflight/challenge latch. Remaining harvester packet. |
| `scripts/rag/scrape_ukrlib.py` | UkrLib / curl | Noncompliant: browser User-Agent and curl redirect/retry flags; no observed robots floor/status stop. Packet D. |
| `scripts/rag/scrape_wikisource.py` | Wikisource API | Noncompliant: API transport retries 429; no observed robots floor. Remaining harvester packet. |
| `scripts/crawl/download_textbooks.py` | textbook repositories | Noncompliant: browser User-Agent; no observed robots floor or process access/challenge latch. Packet D. |
| `scripts/crawl/crawl_saint_sophia.py` | heritage-resource API | Noncompliant: _fetch_with_retries retries CrawlError from HTTP failures; identity lacks contact, no observed robots floor/challenge latch. Remaining harvester packet. |

## Consumers and local builders

| Module | Disposition |
| --- | --- |
| `scripts/lexicon/build_slovnyk_mirror.py` | Uses enrich_manifest strict outcomes; blocked remains a stop. |
| `scripts/lexicon/fix_esum_garbled_etymologies.py` | Uses Goroh ingest transport. |
| `scripts/lexicon/enrich_heteronyms.py` | Uses sum20_lookup; default read-only cache lookup remains local. |
| `scripts/ingest/slovnyk_me_ingest.py` | Uses wiki/slovnyk_me; optional cached snapshot mode is offline. |
| `scripts/ingest/sum20_official_ingest.py` | Fixed in Packet A: passes its configured 2s floor to the shared transport; observed crawl-delay always raises it. |
| `scripts/rag/batch_scrape_izbornyk.py` | Uses Litopys scraping transport. |
| `scripts/rag/batch_scrape_pdfs.py` | Source PDF batch wrapper; transport behavior delegated to source scraper. |
| `scripts/crawl/crawl_ulp_blog.py` | Builds local ARTICLES metadata; no HTTP. |
| `scripts/crawl/crawl_dobraforma.py` | Builds local chapter catalog; no HTTP. |
| `scripts/crawl/crawl_talkukrainian.py` | Builds local catalog; no HTTP. |
| `scripts/lexicon/build_kaikki_lookup.py` | Reads local Kaikki JSONL; explicitly does not download. |

## Owned boundary and proof

The project User-Agent describes automated educational collection and contains the
public repository contact: `https://github.com/learn-ukrainian/learn-ukrainian.github.io`.
It does not claim to be Chrome or send browser navigation headers.

Owned source requests read robots with the same identity, honor target disallow
rules and use `max(configured floor, observed crawl-delay)`. The robots request
also participates in spacing. Fractional observed delays round upward because the
standard-library parser accepts integer delays. Missing robots (404) uses the local
floor; denied/challenged, redirected or unavailable robots stops content access.
No redirects are followed automatically. A 404 article is a miss; 401/403/407/429,
challenge HTML or a `cf-mitigated: challenge` header is an access stop. Challenge
recognition precedes parsing and transient HTTP retry classification. Generic
JavaScript detection script paths, captcha widgets and human-verification prose
alone do not identify a challenge. Established interstitial markers or the
case-insensitive `cf-mitigated: challenge` response header do. Enrichment
still bounds genuine network/408/425/5xx failures; a challenge on those statuses
stops immediately. Existing cache format and parsed successful payloads are retained.

Process stop state prevents another lookup or dictionary from laundering a denial
through tolerant exceptions. A second CLI invocation in the same process cannot
make requests after a stop unless an explicit run-boundary reset occurs. The
existing test autouse pattern resets only already-imported collector modules at
test boundaries; it never clears stops before requests. Enrichment, filler,
glossary and ULP commands report the stop and exit 1; official ingest and acquisition
retain their established terminal access exit 3 and durable outcome contracts. The curl filler retains its old single-denial CLI
flag, but accepts only `1`. SUM-20 stops between search and articles or sibling
articles. ULP closes its clients and stops the command before local fallback,
FMU fetch or replacement of existing output. The blog catalog remains offline.

Hermetic tests: `tests/test_fill_slovnyk_sum20_cache.py`,
`tests/test_sum20_lookup.py`, `tests/test_crawl_ulp.py`, `tests/test_crawl_ulp_blog.py` and the collector tests in
`tests/test_lexicon_enrich_manifest.py`. They exercise fake responses and a clock
starting at zero, with integer/fractional robots delays, disallows, HTTP and
challenge stops, missing robots, cache reuse, sibling preservation and output
preservation. Driver-held challenge/status and fake-clock cases are independent
proof still required before disposition; author tests do not replace that proof.

## Remaining ownership and closeout

Packet A covers seven original direct rows and one wrapper; 22 original direct
rows and six wrapper rows remain under **codex-atlas**, with the dispositions
above. The four local-builder rows have no external source transport. GRAC,
E2U and Wikidata within the enrichment row remain separately owned transport
work even though the Slovnyk boundary is repaired. These counts describe the
original inventory, not a whole-issue compliance pass.

- Packet B: `source_query.py` and `wiki/slovnyk_me.py`, with sources-server
  ownership agreed and long-lived MCP stop semantics separately approved.
- Packet C: the three ULIF collectors, after #10111 and active ULIF runs are
  reconciled by the driver.
- Packet D and remaining harvester work: browser identities and the remaining
  direct-row defects recorded above, with their consuming wrapper tests.
- Exact-head independent cross-family review, same-head CI/merge queue, merged
  product proof and common cleanup remain the driver's closeout duties.

The fingerprint is a versioned build input, regenerated by
`scripts/pre_commit/regen_lexicon_fingerprint.py`; only changed lexicon-script
hashes may differ. The tracked fingerprint test hygiene in
`test_reenrich_thin_manifest_entries.py` is not changed by this packet. Conservation
proof records the source database byte hash and cache size/mtime digest before
and after author checks. Author tests are not the driver's independent held-out proof.

No new neutral network module or long-lived MCP design is introduced.

## Existing cached source content (AC-03)

The existing-content decision is settled by #8977 and the task's current policy:
authentic Ukrainian source use is approved. This transport repair preserves cached
content and provenance; it introduces no rights gate, quarantine, deletion, source
disabling, outreach or account/security work. A robots or access stop controls future
requests; it is not a new judgment about rights to already cached content.

Technical references: [Python robotparser](https://docs.python.org/3/library/urllib.robotparser.html)
for `can_fetch` and `crawl_delay`, [Cloudflare JavaScript Detections](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/javascript-detections/)
for ordinary HTML script injection, [Cloudflare challenge responses](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/detect-response/)
for the response header, and [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html)
for crawler identity and robots semantics. These establish transport behavior, not
source-use authority. Tests do not claim live endpoint behavior or source availability.
