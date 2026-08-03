# Public Corpus Source-Capability Evidence Map

> **Snapshot:** 2026-08-03
> **Owner:** [#6327](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/6327)
> **Scope:** Evidence needed to decide preparation, model-learning, and
> publication capabilities for the 189,150-record public/external corpus
> **Not:** Legal advice, a family-wide license declaration, source-text
> publication, or model-training authorization

## Why this map exists

Public availability proves that a source could be located and acquired. It
does not by itself prove that a project or downstream consumer may use the
text for model learning, redistribute raw or derived text, publish a dataset,
or publish model weights.

Those capabilities also cannot be answered by one global IP flag. The
underlying work, the selected edition, the transcription or digitization, the
host website, and the planned output may each have different evidence and
rightsholders. Phase 2 therefore records them separately and leaves a decision
unresolved when one layer is missing.

The broader project decision that retained human-authored material may be used
for operator-approved local research after preprocessing is preserved as a
project decision. It is not silently converted into a general permission for
an external consumer or into permission to release source bytes, a dataset, or
weights.

## Reconciled source map

The current SQLite inventory and retained raw-source audit reconcile to four
families:

| Family | Records | Source structure | Current capability evidence |
| --- | ---: | --- | --- |
| Literary | 137,723 | 89,498 Litopys/Izbornyk rows from 170 source files; 46,884 UKRLIB rows from 55 files; 52 Ukrainian Wikisource rows from two files; 1,289 retained Hrushevsky rows from two files | Raw locators and bibliographic metadata are substantially recovered, but the underlying work, edition, transcription/digitization, and host terms are not normalized per work. |
| Public textbooks | 49,193 | 158 raw chunk files, 170 retained PDFs, and 93 landing-page mappings; private ULP/Ohoiko references remain excluded | Acquisition and edition locators are partial. Publisher, author, edition, digital-file, and permitted-use evidence is unresolved per textbook. Two raw lineage sources also remain unmatched. |
| External articles | 1,205 | Eight source-file groups. The normalized domain field is absent on 960 rows; named domains cover 245 rows. | URLs are retained, but author/speaker, transcript provenance, publication terms, and permitted use are not normalized per item. |
| Ukrainian Wikipedia | 1,029 | Article URL, title, capture time, exact stored-content hash, and acquisition-code cohort | The only family with a completed primary rights packet and accepted admission. Article-history, imported-content, and additional-attribution checks remain publication-time gates. |

Named external domains are not capability decisions. They are inventory keys:

| Domain value | Rows |
| --- | ---: |
| Missing | 960 |
| `ukrainianlessons.com` | 164 |
| `opentext.ku.edu` | 32 |
| `uk.wikipedia.org` | 26 |
| `talkukrainian.com` | 9 |
| `youtube.com` | 8 |
| `verba.school` | 3 |
| `lcorp.ulif.org.ua` | 2 |
| `ukrlib.com.ua` | 1 |

## Primary-source findings

### Ukrainian Wikipedia

The frozen evidence packet binds the historical MediaWiki API capture to exact
stored bytes. The current
[Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use/en)
and [CC BY-SA 4.0 legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode)
support the existing license and attribution analysis. Wikimedia also warns
that imported material can carry different or additional attribution
requirements. Before source-text or dataset publication, each article still
needs its revision/history, talk-page or banner state, footer license, and
imported-content notices captured.

Required keys include `mediawiki_revision_id`, `page_history_url`,
`talk_page_url`, `page_footer_license`, `imported_content_banner`, and
`additional_attribution_notice`.

### Ukrainian Wikisource

The official Ukrainian Wikisource
[copyright help](https://uk.wikisource.org/wiki/Довідка:Авторські_права)
describes licensing of community contributions and uploader responsibility.
Its [collection policy](https://uk.wikisource.org/wiki/Вікіджерела:Що_містять_Вікіджерела)
requires source verification and a free-license or public-domain basis. This
supports per-page evidence collection; it does not create one automatic
decision for both retained source files.

Required keys include the page URL and permanent revision, page history,
source scan or edition, underlying-work status, displayed license template,
and any translator, editor, or digitization rights.

### UKRLIB and Litopys/Izbornyk

UKRLIB, Litopys, and Izbornyk are provenance locators for the retained
literary sources. No authoritative site-wide reuse license was verified in the
bounded 2026-08-03 check. The current evidence must therefore be resolved per
work and edition rather than by assuming that the host domain licenses every
underlying work, edition, or transcription.

The official Ukrainian
[Copyright and Related Rights Act](https://zakon.rada.gov.ua/laws/show/2811-20)
states the general life-plus-70 term in Article 31 and describes public-domain
use in Article 32. Applying those rules requires author and publication facts
and review of exceptions. It also does not settle later edition, translation,
editorial, first-publication, transcription, database, or host-site rights.

Required keys include canonical source URL, work and author identity, author
death date or other underlying-work basis, edition/publisher/year, translator
or editor, transcription/digitization status, explicit license or permission,
retrieval date, and exact stored-content hash.

### Public textbooks

The retained `data/pidruchnyk_urls.yaml` maps 93 source stems to public
`pidruchnyk.com.ua` landing pages. The site currently describes free online
viewing for familiarization, but no authoritative site-wide reuse license was
verified. That is acquisition evidence, not model-learning or publication
permission.

The Ministry of Education and Science confirms that electronic textbooks are
made available online, including through the IMZO library. Its current
[state-procurement explanation](https://mon.gov.ua/news/yak-vidbuvaietsia-zakupivlia-pidruchnykiv-za-derzhavni-koshty)
also says that textbooks are copyright objects and that the author chooses the
publisher under an author-publisher agreement. The Ministry page itself may be
CC BY 4.0; that does not automatically license the linked textbook editions.
Therefore the corpus cannot be classified as one state-open educational
resource family without per-edition evidence.

Required keys include landing-page and PDF URLs, authors, publisher,
edition/year/ISBN, official catalogue or approval record, host terms,
publisher license or permission, digital-file rights, exact hash, and raw
lineage status. OCR and mojibake treatment remain separate quality evidence.

### External articles and transcripts

The database retains source URLs, but 960 rows still lack a normalized domain.
Articles, video recordings, human transcripts, and third-party transcripts can
be separate works. Domain terms alone cannot settle author, speaker, publisher,
channel, transcript, or item-level licensing.

Required keys include canonical URL, normalized domain, publication date,
author or speaker, publisher or channel, content type, transcript provenance,
terms version and retrieval date, work-level license or permission, and exact
stored-content hash.

## Evidence-resolution order

Two orders must not be confused:

1. **Lowest-risk control work:** refresh Wikipedia article-level evidence,
   because it already has stable identifiers and a completed primary packet.
2. **First new non-Wikipedia canary:** reconstruct the 52 Wikisource rows
   page-by-page. This is deliberately a contract canary, not the promised data
   contribution.
3. **First volume target:** split the literary collection by work and edition,
   then resolve candidate public-domain or explicitly licensed strata. A
   host-domain assumption is not sufficient.
4. **External articles:** repair the 960 missing domains and resolve repeated
   publication regimes while retaining item-level author and transcript
   evidence.
5. **Textbooks:** bind each retained edition to author, publisher, official
   catalogue, and digital-file evidence. The Ministry evidence rules out a
   blanket assumption that state purchase or free learner access makes every
   edition an unrestricted OER.

The 52-row Wikisource canary proves the resolution machinery. It is not the end
goal. The completed Phase 2 ledger now covers every source family and identifies
the exact missing evidence for materially useful literary or textbook volume.
Resolving those tasks, rather than merely locating the files, is the remaining
source-evidence work.

## Reproducible Phase 2 output

The public, text-free locator index contains 42,302 semantic records: 3,309 literary,
36,759 textbook, 1,205 external-article, and 1,029 Wikipedia source/work
mappings. Its self-describing compact UTF-8 transport occupies 11,523,406
bytes and is bound by SHA-256
`ca9fb9e88f7520d77bafb9139b2ba20c652a47395c94d416ad575a1ac0801ee6`.
Strict expansion produces 32,991,831 canonical JSONL bytes with SHA-256
`1d3f85ae6bb4241b9691c18cf855ec71e3e2ab7c97d18bf52e522f9d2ae07a60`.
It contains no source chunks or text. Canonical URLs are emitted only when the
retained metadata supports them; a missing URL remains missing rather than
being guessed.
The transport derives `locator_id` from the retained canonical family,
source/work identifiers, and source/work locator maps using the declared
production formula. Strict expansion proves that this removes no semantic
field from the full-object representation.

The full complement covers all 189,150 records, and the source-level worklist
contains 3,511 evidence-resolution items. Two full builds and an independent
rebuild verifier produced exact output matches. Only the compact receipt and
text-free locator are committed; the 958,068,153-byte complement and
67,845,464-byte worklist remain local. This proves deterministic routing and
alignment, not permission to publish the underlying corpus.

## Deterministic evidence keys

Every unresolved decision must name one or more machine-readable missing keys,
not a prose-only request such as "review rights":

- `underlying_work_status`
- `underlying_work_evidence_url`
- `edition_identity`
- `edition_rights_status`
- `transcription_or_digitization_status`
- `host_terms_url`
- `host_terms_version`
- `terms_retrieved_on`
- `explicit_license_or_permission`
- `canonical_source_url`
- `source_revision_or_snapshot_id`
- `content_sha256`
- `actor_scope`
- `destination_scope`
- `jurisdiction_scope`

The capability ledger may use these facts to produce `evidenced`,
`unresolved`, `blocked`, or `excluded`. It must not convert a missing fact into
either permission or prohibition, and it must never infer one capability from
another.

## Local evidence sources

- `docs/corpus-inventory.md`
- `docs/research/EXISTING_CORPUS_ASSET_RECOVERY_AND_LINEAGE_AUDIT.md`
- `docs/research/UKRAINIAN_CORPUS_TRAINING_USABILITY_DECISION.md`
- `data/projects/open_model_data/inventory/corpus_training_usability_decision_v1.json`
- `data/projects/open_model_data/admission/public_external_operator_decision_packet_v1.json`
- `data/projects/open_model_data/admission/wikipedia_primary_rights_evidence_v1.json`
- `data/projects/open_model_data/profiles/public_external_full_corpus_v1.json`
- `data/pidruchnyk_urls.yaml`
