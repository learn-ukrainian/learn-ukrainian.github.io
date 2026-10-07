# Decolonization source withholding

The builder conserves the existing 250-case catalog, then emits only cases that
pass source binding and independent review integrity checks. Withholding is the
stop outcome specified by #9858. Missing evidence never licenses reconstruction,
paraphrase, source acquisition, or an admission quota.

Every emitted `supporting_passage` must occur literally in an admitted source
row for the credited authority. Comparison preserves case, stress and whitespace;
normalized text and line-split approximations cannot authenticate a quotation.
The binding records the table, row identity, text field, resolving locator,
source provenance and SHA-256 of the raw field and passage. Selection considers
all eligible witnesses, so an earlier headword hit, homonym or row limit cannot
hide a later literal witness. Catalog citation metadata stays bound to its
existing review; the resolving held-row locator is additional proof.

Source identities come from explicit provenance:

- Official СУМ-20 rows use their admitted table, official URL and shared live-row
  predicate. Slovnyk cache rows require matching recognized URL and dictionary
  slug. ULIF and generic `external_articles` rows cannot authenticate a СУМ-20 or
  ВТС credit; a title mentioning a dictionary grants no identity.
- UA-GEC binds its independently mapped correction record and metadata. The
  passage must occur in that row's raw `error` or `correct` field.
- Правопис binds `pravopys_paragraphs` for the existing official source ID, with
  its locator and verified `text_sha256`, rather than generic articles.
- Антоненко-Давидович binds the admitted structured index with its explicit
  source identity, or the approved full-book source file with agreeing author
  metadata. Both `text` and `excerpt_full` are eligible raw index fields.
- Other book witnesses require exact cited author and book metadata, or explicit
  full authority attribution in an admitted external record with source-file
  provenance. Titles, body anchors, co-authors and invented book aliases cannot
  substitute for the credited authority.

Project-authored external rows cannot be witnesses: `channel_id=omd`,
`domain=codification`, a `codification-` source file, or a decolonization tag
identifying any catalog case disqualifies the row. A direct case-tag lookup also
cannot authenticate it. These rows remain unchanged in storage. A separately
admitted non-project witness containing the same literal passage remains eligible.
Detailed affected-case accounting stays in private author evidence with the
accountable driver under #6321.

Committed dictionary passages are historical candidates, not authorities by
virtue of their URLs. `committed_record_dispositions()` requires both article and
definition literally in an admitted held row, with matching lookup/provenance and
resolving locator. Quarantine takes precedence. Only the existing connection-local
projection is refreshed; persistent source tables are never modified.

Unsupported source bindings produce typed withholding. Review receipts, dossier
verdicts, passage/locus agreement and content digests are checked before source
availability, so an unavailable source cannot conceal review tampering. Required
schema and query faults abort. The build/CLI validates dictionary, UA-GEC,
structured-index, external-article, textbook, textbook FTS and official Pravopys
contracts before withholding. Textbook witnesses resolve from stored rows; FTS
cannot provide replacement provenance. No query failure is caught as healthy
absence. The optional Slovnyk cache may be absent; an existing malformed cache
aborts, including when another dictionary witness is available. Direct quarantine
refusals preserve the existing precedence; CLI schema faults still abort first.

`build_all_cases(withheld=dispositions)` returns retained cases and appends
withheld accounting. The CLI prints each withheld ID and reason. Export manifests
include `candidate_cases` and `withheld_cases`; withheld cases have no training or
evaluation records. Each withheld entry names its acquisition owner and #6321.

| Reason | Meaning |
| --- | --- |
| `quarantined_headword` | The shared quarantine rule excludes the candidate. |
| `unrecognized_provenance` | Candidate URL does not identify an admitted dictionary. |
| `held_source_unproven` | Available rows cannot authenticate literal passage, authority and locator. |
| `held_source_missing` | No admitted related source row resolves for the case. |

Regression tests use synthetic witnesses and independently stored expectations
for literal positives, normalized/placeholder/foreign-source refusals,
project-authored rows, schema/query failures, quarantine and review integrity.
Held-data tests separately pin all withheld dispositions and every observed
positive's row, field and digest without putting source passages in Git. The
private full-catalog audit independently searches admitted rows, including alternate
witnesses for previously unproved cases. This repair does not regenerate or
publish dataset artifacts.
