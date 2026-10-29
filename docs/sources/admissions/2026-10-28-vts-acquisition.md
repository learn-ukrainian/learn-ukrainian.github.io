# ВТС acquisition source snapshot

This snapshot binds the unattended ВТС acquisition to the source-published
article index observed on 2026-10-28. It does not establish equivalence between
the digital mirror and every entry in the printed edition.

## Source and denominator

[NBUV record UKR0000989](https://irbis-nbuv.gov.ua/ulib/item/UKR0000989)
identifies the 2005 Бусел/Перун edition, VIII + 1,728 pages, and links fourteen
alphabet sections covering А–Я. A direct viewer request returned HTTP 403.
That access attempt stopped. No NBUV article structure was acquired or verified.

[The digital ВТС](https://slovnyk.me/dict/vts) publishes five sitemap files
through its robots.txt sitemap index. Together they enumerate **202,270 unique
article URLs**. All 33 initial letters are represented, including the single
entry under ь. The advertised approximately 250,000 words and phrases is a
bibliographic description, not an exact article count.

| Sitemap | URLs | SHA-256 of downloaded gzip bytes |
| --- | ---: | --- |
| [words-vts-indx1.xml.gz](https://slovnyk.me/sitemap/words-vts-indx1.xml.gz) | 50,000 | `7e5b39176f30cd0010e0148a911ae5d3d3ece2d3aca07d3dadcb8551bca0b07f` |
| [words-vts-indx2.xml.gz](https://slovnyk.me/sitemap/words-vts-indx2.xml.gz) | 50,000 | `acc09108243d763e6b37c49ca699ba7b58915be69e9cead5a480774d832b394f` |
| [words-vts-indx3.xml.gz](https://slovnyk.me/sitemap/words-vts-indx3.xml.gz) | 50,000 | `12cc12439a6e567e8a750c51536877d7d2ffbd30a4dcf9ac57577e65dd610fb6` |
| [words-vts-indx4.xml.gz](https://slovnyk.me/sitemap/words-vts-indx4.xml.gz) | 2,270 | `78999aa20f9b10008684759d1e35d7d57e44e6b3c9be103ea568e7fd32a77f6b` |
| [words-vts.xml.gz](https://slovnyk.me/sitemap/words-vts.xml.gz) | 50,000 | `f77d86ae9e22823b2ddefd3c40fbded3ca52cee6243171c7ab5da938e9df43ad` |

The frozen manifest uses `source_headwords: true` and contains every decoded
article suffix exactly once. All 202,270 suffixes round-trip to their sitemap
URLs and contain no slash, query or fragment characters, surrounding whitespace,
or control and format characters. Its first 117 targets exercise differences
from learner-lemma normalization: 55 closing-parenthesis cases and 62 case
differences. Twenty additional targets follow, selected by ascending SHA-256
of their UTF-8 suffix. The remaining targets retain sitemap order.

The uncompressed manifest SHA-256 is:

`066fe4f1455ada3fddea25d4975651c0e38f5c45baa5f2bf6ad5b5c7d814c46b`

The manifest and its gzip copy remain in the operator-owned acquisition root.
They are acquisition inputs, not learner content. Review binds the complete
manifest bytes by this hash. Use the same root for all companion jobs.

At a four-second quiet interval, 202,270 network targets require at least
**809,080 seconds**, or **9 days, 8 hours, 44 minutes, 40 seconds**, plus
request time, retries, local processing and other traffic sharing the host lock.
Use the runbook supervisor with delay 4, timeout 30, backoff 4, four attempts
and three no-progress restarts. Keep identifying headers and all terminal stops.
Sitemap targets returning 404 remain coverage gaps even when the job completes.

## СУМ-20 import boundary

The existing mirror has 164,838 articles, all with outcome `ok`, and a complete
checkpoint dated 2026-10-12. Its final URL is the article ґуґля. Preserve the
artifact without downloading it again. The SQLite file SHA-256 observed for
this snapshot is:

`32e77a09e004a7ad740fa8acd350d0f5a743cb13f751e9d134ffcec5db595194`

The mirror store has no tracked producer or promotion writer. The catalogue
and backup allowlist retain it as staging. `resolve_sum20_articles` already
reads it on an official-key miss and labels results `mirror_candidate`.
`lookup_sum20_articles` uses this resolver. The strict `query_sum20` reader and
the word-card source inventory read official `sum20_articles`. A mirror lookup
does not establish official verification or word-card sense readiness.

Reproduce the read-only inventory comparison with:

```bash
"$ACQ_PY" -m scripts.lexicon.reconcile_sum20 \
  --repository-root "$PRIMARY_CHECKOUT" \
  --staging "$PRIMARY_CHECKOUT/data/sum20_slovnyk_staging.db" \
  --official "$PRIMARY_CHECKOUT/data/sources.db"
```

The snapshot has 2,380 official records with 2,340 identities. Of 2,196 shared
identities, 2,004 match after transport normalization and 192 differ. The mirror
has 162,642 additional identities and lacks 144 official identities. Forty
official identity groups contain multiple records. Reconciliation reports
differences only and has no apply mode.

Eleven official rows remain quarantined, with wordids 300044, 300051, 300052,
300053, 300054, 300055, 300059, 300060, 300061, 300064 and 300066. Preserve their
marks and the existing quarantine and reconciliation tests.

`scripts.ingest.slovnyk_me_ingest --cache-dir` imports per-lemma cache JSON
into `slovnyk_me_entries`, preserving its `newsum` source role. It does not
import the staged mirror SQLite file or write official `sum20_articles`.
The documented official writer is `scripts.ingest.sum20_official_ingest`,
which acquires official articles and writes their official wordids and provenance.
The detached companion writes staging only. There is no documented import
from this mirror into the official store. Do not fabricate official wordids
or relabel mirror rows to bypass that boundary.

The source-acquisition coordinator owns the separate import disposition after
the acquisition stops. Official population must use the documented official
writer. Importing either mirror or companion staging into another collection
needs its own reviewed writer change and reconciliation proof. No live store
is written by this acquisition change.
