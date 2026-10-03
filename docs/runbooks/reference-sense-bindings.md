---
lifecycle: active
---

# Reference sense bindings

This procedure implements #9582 AC-04 and the approved #9546 design. A private
reference meaning selects an exact **open dictionary** atom. Only that atom is
published. A1 reference members without a valid binding retain a typed gap;
outside members keep the precision-first selector. This runbook does not change
plans, source decisions, or publication eligibility.

## Private extraction

Keep the owned PDF, the JSONL meanings, the commitment key and receipts outside
Git. Use a private destination and the prescribed project interpreter:

```bash
.venv/bin/python -m scripts.ingest.build_ohoiko_a1_reference \
  --pdf PRIVATE_PDF --inventory registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml \
  --private-meanings PRIVATE_JSONL
.venv/bin/python -m scripts.ingest.prove_ohoiko_a1_reference \
  --pdf PRIVATE_PDF --inventory registry/lexicon/source-inventory/ohoiko-oho-a1-reference.yaml \
  --meanings PRIVATE_JSONL
```

The private output uses each public page locator followed by `#N`, the one-based
row position across the inventory's sources/headwords. This distinguishes
entries sharing a page. Never alter inventory ordering independently of the
extraction and bindings. The extractor accounts for every physical line,
including continuation lines and shared meanings on multi-entry lines. The
proof uses raw character masks and physical columns independently of the
extractor, and reports counts and mismatch locators only.

## Exact selection and committed shape

```bash
.venv/bin/python -m scripts.curriculum.evidence sense-select a1 --private-input PRIVATE_JSONL
.venv/bin/python -m scripts.curriculum.evidence sense-select a1 --private-input PRIVATE_JSONL \
  --write --key-file PRIVATE_KEY --key-id build1
```

The first command only measures; diagnostics contain W-ids, row ids, span indexes
and reason codes. The second writes `_sense_bindings.yaml` and its integrity
lock in the level evidence directory. Schema:
`schemas/evidence-sense-bindings-v1.schema.json`. No real A1 bindings are committed
in the tooling PR; their publication belongs to the plan revision.

`a1_reference_meaning.v1` uses `reference_sense_v1` and the existing parser.
`span_index` enumerates `_sense_spans` over `_sub_senses`, across the row's
translation list in source order, **before** learner filtering. `atom_index`
identifies an atom within that parser span, before learner filtering. `span` is
the matched atom's exact source spelling, excluding surrounding whitespace,
notes and separators. The verifier re-derives both indices and text from the
hash-bound row; missing or stale indices produce `reference_binding_invalid`.
Normalisation is NFC, casefold, collapsed whitespace and terminal punctuation,
with leading `to` removed only for verbs. Display preserves source spelling.

Classification happens on the complete translation group **before** either the
existing parser or atom splitting can discard annotations. Closed constants in
`scripts/curriculum/evidence/reference_sense_v1.py` document every admitted label:

- `GRAMMATICAL_ANNOTATIONS`: grammatical labels, including possessive,
  countability, reflexive, proper noun and explicit `+ CASE` notes. Ignored
  wherever they appear.
- `RESTRICTING_LABELS`: register, time, attitude, region/country, figurative use,
  paganism and short/long scale. Exact aliases have one canonical label.
- `TOPIC_LABELS`: domains, including sports, medicine, music, furniture,
  anatomy/anatomical and mechanics/mechanical. These also restrict matching.

A trailing parenthetical with no recognised label is a definition (including
Latin taxonomic names). It is kept in the source sense signature and candidate
list, but is neither matched nor displayed. Recognised labels inside a trailing
or nested definition still restrict the whole group. Every restricting/domain
label must equal the reference's label set; a topic-labelled sense cannot match
a bare reference head. Leading unknown labels, partly recognised label lists
and uncertain internal scope are withheld. Unknown labels and uncertain scope
are counted as excluded **parser spans per reference-selection attempt**; a
record with multiple inventory entries can evaluate a row more than once.

After classification, top-level `,`, `;` and `/` delimit atoms. Each inherits its
group's labels and definition. A complete atom must match exactly, with no fuzzy,
substring, stemming, synonym or model selection. Multiple heads must resolve to
the same source sense signature. Candidates with identical displayed atom text
and labels collapse to the lowest row id, then span/atom index, even when their
definitions differ; different visible text or labels is ambiguous. Lemma, POS
and homonym compatibility bind before selection. Kaikki-only matches remain
withheld. No reference-member fallback is permitted.

## Reviewed remainder

```bash
.venv/bin/python -m scripts.curriculum.evidence sense-bind a1 --word W-001 --candidates
.venv/bin/python -m scripts.curriculum.evidence sense-bind a1 --word W-001 \
  --row-id 1 --span-index 0 --atom-index 0 --review-task REVIEW_TASK --author-model gpt-6.1-sol
```

Send the complete public candidate list and its `candidates_sha256` to a
cross-family Ukrainian review dispatch with the sources MCP receipt ledger and recorded `review_author_model`.
The dispatch's result is a JSON object with `verdict: APPROVE` and `subject`:
`word`, `candidates_sha256`, `table`, `id`, `row_sha256`, `span_index`,
`atom_index`, `span`, `labels` and `definitions`.
The subject must exactly equal the selected candidate plus W-id and list digest.
The terminal task record must be `done`, profile `ukrainian`, have a recorded
review attempt and a digest-matching result. The attempt's sources ledger must
verify and contain successful `verify_words`, `query_cefr_level`, and
`check_russian_shadow` calls for this lemma. The binding CLI derives
model, family, harness, author identity and date from that record; it accepts no reviewer identity
flags or free-text gloss. Changed candidates, failed/incomplete dispatches,
unrelated subjects and non-approving verdicts are refused.

## Key management, verification and replacement

Use at least 32 cryptographically random bytes for a host-local key; retain the
key in private storage with access restricted to its owner. `key_id` is a public
identifier, never the secret itself. Each commitment is HMAC-SHA256 over the
canonical complete private entry. The local receipt is HMAC-sealed and binds the
bindings file digest, an HMAC of the entire private input, key id, matcher version
and exact Git head. Neither plain private hashes nor private paths are published.

After committing the public bindings, on a clean head:

```bash
.venv/bin/python -m scripts.curriculum.evidence sense-select a1 --private-input PRIVATE_JSONL \
  --check --key-file PRIVATE_KEY --key-id build1 --receipt PRIVATE_RECEIPT --pr PR_NUMBER
.venv/bin/python -m scripts.curriculum.evidence sense-select a1 --private-input PRIVATE_JSONL \
  --check --key-file PRIVATE_KEY --key-id build1 --receipt PRIVATE_RECEIPT \
  --verify-receipt --pr PR_NUMBER
```

`--check` reselects and recomputes commitments, scans committed files and new
commit messages and scans PR title/body/comments when
available. All committed HEAD files are scanned; `origin/main` bounds commit messages.
Only exact, current source-validated values at binding `span` and store `gloss_en`
locations are exempted; the same text in another location remains a suspected
leak. An unavailable PR is explicitly `unverified`. Resolve every suspected leak
before issuing the receipt. Never publish scan matches or private text in reports.
Any changed head, bindings, private input, key or matcher invalidates replay.

To replace a lost or rotated key: allocate a new key id and private key, re-extract
and independently prove the private input, rerun `--write`, commit the resulting
public commitments, then rerun `--check` on the new head. Review the new receipt
and bindings before use. Never reuse an old receipt or invent a replacement key
with the old id.

CI verifies public row hashes, parser/atom positions, exact atom text, learner bounds and
inventory locators, without the private file. It reports private commitments as
**unverifiable in CI (local receipt required)**. That warning is not verification
of the commitment; review of record requires the local receipt. Builder,
word-store verifier and pack gloss gate use bindings first. Rendering and
immersion counting both consume the selected `gloss_en`, never `sense_gloss`.
