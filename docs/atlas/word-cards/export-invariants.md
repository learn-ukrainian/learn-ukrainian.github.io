# Word-card acceptance and export invariants

Reference for #10513, with source-census obligations retained under #9401.

`load_certified_card_for_export` is the shared certification check. An accepted
card or exported card must match its authoritative review record, public card
version, complete build, implementation fingerprint, rules fingerprint and live
input snapshots. A review grants only its listed projections. Dataset approval
does not grant site approval. Draft rules cannot certify a card.

The committed review ledger starts with `approved_reviews: []`. It certifies no
real cards. Tests redirect `REVIEW_EVIDENCE_PATH` and `PERMISSIONS_REGISTER_PATH`
to temporary files. Neither fixture approvals nor generated PASS receipts belong
in this ledger.

An admitted review record contains `card_id`, `status: active`, `record`, `lane`,
`approved_for`, `card_version`, `build_sha256`, `implementation_sha256` and
`rules_sha256`. These digests bind the exact reviewed artifact. Withdrawals remove
the record or change its status. A copied review label, citation, pilot receipt,
manifest entry or successful download grants no approval.

The ledger's `snapshot_bindings` maps each input category and name to a
repository-relative `path`. The verifier hashes that authority file, once per
run. For a lock file, `json_keys` may select its canonical data digest, for
example the VESUM lock's `expected.canonical_jsonl_sha256`. The implementation
fingerprint also covers that lock. Every nonempty S, V, I and O input must match
its live binding; VESUM, overlays, suppressions, normaliser and the current
permissions register are mandatory. Rules and implementation file inventories
are defined in `word_card_certification.py`.

Authority caches last for one call to an acceptance or export entry point.
Separate reimports, hydrations and exports reload current authority. A cached
package or old card cannot restore a withdrawn assertion against current
suppression snapshots. Restoring the authority repository itself to an older
revision is outside this check's trust boundary; this code grants no rollback
or publication authorization.

Runtime database columns are projections, never additional card facts. The
mapping is `lexeme -> lemma`, `mwe -> multiword_term`, and
`proper_name -> proper_name`. A form route cannot carry a full certified card.
Head, gloss and CEFR must match the reviewed card. Schema-conformant cards need
no additional `entry_type` field. Runtime verification checks search agreement
against the certified entry payload as well. Outer aliases, relations, provenance
and practice metadata cannot add facts: card assertions retain their own source
provenance, and unreviewed database additions are refused.

Dataset packaging permits JSON, JSONL and gzip-compressed JSON or JSONL. The
three named attribution documents are the only text-file exceptions. Temporary
files and extra Markdown files are refused. Each data object is certified again,
including files outside `dataset/`. Hydration validates certification before
creating its destination or staging directory. Existing provenance and quarantine
checks remain mandatory. Card manifests permit only their inventories, version,
generation timestamp and build fingerprint. Dataset metadata permits only
version, timestamp, counters, shard integrity and the three eligibility flags.
Extra properties cannot carry unchecked assertions beside a certified card.

`--draft-mechanics` writes only `draft/mechanics.json`, marked uncertified and
export-ineligible. It writes no dataset shards. Foundation allocation, resolver
projections, assembly, batch-1 and withdrawal rehearsals remain engineering
artifacts; their successful execution never accepts cards or certifies language.
Legacy manifest and generator output remains candidate evidence. Card-bearing
manifests are checked on read, migration and publication. Legacy Atlas article
compatibility remains distinct from word-card certification; the dataset exporter
refuses legacy rows even when their manifest claims certification.

The path census names the public boundaries and their regression tests. These
tests use synthetic authority and prove guard mechanics only. Independent
exact-head review, held-out outcome proof, source-census completion under #9401,
and authorization for any real certification or release remain separate gates.

The [versioned assertion projection](../../datasets/word-cards.md) also checks
exact-artifact dataset certification before producing release bytes. It then
filters assertion scope and rebuilds cited fields without copying cached
resolutions. Its implementation is included in the certification fingerprint.
Its local release schema is separate from the Atlas shard package schema.
