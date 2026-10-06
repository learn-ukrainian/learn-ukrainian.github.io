# W0 round 2 selection handback — #9862

The three ordered foundation prerequisites are implemented in separate commits.
Selection resumed and retained **175 / 220 cases**, expanding to **626 literal
source records**. W0 remains stopped because the required total cannot be
expressed under the supported source contracts. No source-admission receipt,
frozen golden manifest, expected answers, card assembly or evaluation was authored.
The admission packet is explicitly partial and **not ready for admission**.
Source admission accepted **0 / 175 candidates**; all 175 candidates (626 rows)
remain withheld pending the distinct non-author gate. The 45 missing category
positions are unfilled, not sourced or adjudicated cases.
Accountable residual owner: `codex`, #6321 / #9862.

## Category accounting

| Category | Selected / target | Replay | Held-out |
| --- | ---: | ---: | ---: |
| homographs | 40 / 40 | 24 | 16 |
| stress doublets | 20 / 20 | 12 | 8 |
| proper common pairs | 20 / 20 | 12 | 8 |
| aspect pairs | 0 / 20 | 0 | 0 |
| aspect homographs | 5 / 5 | 3 | 2 |
| multi headword mwes | 20 / 20 | 12 | 8 |
| multi sense | 20 / 20 | 12 | 8 |
| stress disagreements | 20 / 20 | 12 | 8 |
| tier 3 only | 0 / 10 | 0 | 0 |
| ulif header damage | 10 / 10 | 6 | 4 |
| russification pairs | 0 / 15 | 0 | 0 |
| ordinary controls | 20 / 20 | 12 | 8 |
| **Total** | **175 / 220** | **105** | **70** |

The public selection and membership contain keys only. The literal selection
candidate and source-MCP diagnostics remain host-only; the packet identifies
them by artifact name and digest, never a deployment path. Cases are listed once;
source rows are deduplicated by their literal locators. No identities, recommended
forms, correct stress answers or sense alignments have been adjudicated.

## Measured source scopes and stopping basis

Read-only SQLite probes used URI `mode=ro` from the assigned dispatch worktree.
The reproducible host-only queries and candidate lists accompany the packet.
Structural counts are candidate scopes, not normative maxima or expected mappings.

| Scope | Raw count | Interpretation |
| --- | ---: | --- |
| Checked ULIF homograph query groups joined to Atlas lemma articles | 3271 | Current scope; historical 2811 is not reused |
| Checked ULIF proper/common query groups by explicit labels | 724 | Label-backed candidates |
| Checked ULIF perfective/imperfective homograph query groups | 428 | Aspect-label candidates; five selected |
| Identical nonblank ULIF phraseology text under multiple checked queries | 1994 | Source-section groups; selected groups also checked for matching citations |
| Checked single-row ULIF query groups with semicolon-separated glosses | 1890 | Unsplit multi-sense candidates |
| Damaged ULIF headers joined to Atlas articles | 27 | Missing headword or grammatical label |
| VESUM comments containing semicolon and accent mark | 73 | Broad declaration candidates, not automatically accepted doublets |
| Double-marked ULIF headers with source-declaration/paradigm corroboration | 6781 | Broad candidates; a bounded MCP-verified pool of 89 was available before final selection |
| UWS/ULIF stress differences under the documented same-letter, single-homonym, polysyllable comparison | 40 | Current disagreement scope; historical 78 is not reused |
| One VESUM entry, one checked ULIF row, matching UWS stress | 15795 | Control candidates before category overlap exclusion |
| Held VTS rows containing both aspect markers | 1069 | Structural pairing-evidence candidates, not 1069 adjudicated pairs |
| Structured Antonenko rows with nonblank Russianism pattern | 8 | Narrow indexed scope; not the book-wide or C7 denominator |
| Atlas spellings with only the five enumerated project/teacher labels and no ULIF/VESUM attestation | 0 | Explicit bounded tier-3-only census; no inference about all possible teaching sources |

The remaining category shortfalls are **20 aspect pairs, 10 tier-3-only cases,
and 15 Russification pairs**. The current foundation has no source-key contract
for VTS pairing rows, Antonenko contrast rows or project/teacher-only evidence.
`intrinsic` probes of literal VTS and Antonenko rows both returned
`Missing approved source-key contract`. The maximum representable cases from
those required evidence families is **0 under the present contracts**, regardless
of their structural candidate counts. Wiktionary was not added; the approved
schema assigns it tier 2, so it cannot fill the tier-3 category.

Every other category continued to its target. Missing categories were not filled
with weaker cases or extra controls. The preserved 175-case candidate declares
the required 220-case target and therefore intentionally fails the denominator
validator: `Golden denominator drift; require exactly 220 cases`. A VTS pairing
statement cannot be replaced with a shared ULIF synonym group. Antonenko evidence
cannot be replaced with a guessed recommendation. New evidence-family contracts
and any resolution of the zero tier-3-only source scope belong to the driver;
this worker did not expand the three ordered prerequisites.

## Source-MCP verification and isolation

`query_ulif_records(detail="compact")` resolved **205 / 205 selected word
queries** as verified; the quoted structural result was `"record_status":
{"ok":205}`. Fresh batch `verify_words`, `verify_stresses`, and a bounded `inspect_lemma`
lookup supplied VESUM/stress diagnostics. These author checks do not replace
independent source admission or held-out evaluation. A word absent from VESUM
was not promoted to an invalid word when checked ULIF attested it. A double-accent
header alone was not called a doublet: the selected cases require a source
`dual_stress` declaration or an MCP-inspected VESUM declaration. Fresh literal-row and source-MCP
checks for all **175 / 175 selected case categories** succeeded, including the
aspect homograph labels and identical MWE text/citations across their headwords.
These are category/provenance checks, not blind expected-answer adjudication.

Seed: `9862-w0-r2-20261006`. Within each category, order keys by SHA-256 of UTF-8
seed + NUL + case key, after forcing pilot-closure cases to replay. Choose exactly
40% of each selected category as held-out. **12** cases were forced to replay by
the existing pilot closure. The resulting provisional split is **105 replay /
70 held-out**. Recovery replayed all 175 per-case pilot-closure
probes, reproduced the 12 forced cases and the exact seeded 70-case membership.
Recorded seed, algorithm and counts live in `w0-selection-keys.json`;
`w0-heldout-membership.json` contains only `heldout` and `replay` arrays.

The production `isolation([pilot, candidate, registry], membership,
("manifest", "registry"), pilot=pilot)` call returned **`checked`** on this partial
selection. It proves conservative closure isolation for these 175 cases only.
It does not validate a 220-case freeze, source admission, independent held-out
accuracy, or evaluation readiness.

## Interrupted-packet recovery

Recovery preserved the original commits and staged key inventories. The mutable
host-only candidate and prior category proof no longer matched their packet
fingerprints. A separate candidate was reconstructed from the staged keys and
current read-only literal rows; its bytes exactly reproduce the original packet
SHA-256 `5537167bf51e56e095db7b96570663aa59786f1e5fd7778feb2d178ca4158ade`.
The preserved host-only originals were not reset, moved or deleted. The packet
now points to the reconstructed candidate and fresh recovery proof artifacts.
All **626 / 626 literal rows** match current source rows and canonical digests.
Fresh ULIF MCP lookup verified **205 / 205 queries**; category checks cover the
exact staged **175 / 175 cases**. The VESUM batch found 169 / 205 forms;
checked ULIF remains the cited authority for the remaining source queries. The
stress batch returned 152 `ok`, 33 `ambiguous`, and 20 `invalid_input` diagnostics;
these are recorded without promoting them to expected answers or admission.
The doublet checks found 19 source-declared
ULIF lemma doublets and one VESUM comment declaration through `inspect_lemma`.

There is also an explicit required-example residual within the filled homograph
category: only **4 / 5 named required examples** are present. The omitted example
is available in the measured query scope, but its four-record entry/paradigm inventory
refuses `Invalid paradigm matrix` for a child section. Forty selected homograph cases do not satisfy
that named-example requirement. Its source-key inventory accompanies the packet;
the driver owns the correction, alongside the 45 unfilled category positions.
This recovery preserves the selected inventory and reports the failure.

## CLI validation and open gates

All project commands used the prescribed shared interpreter from the assigned
worktree. `PROJECT_PYTHON` below means that interpreter, not a new worktree venv.

- `PROJECT_PYTHON -m scripts.atlas.word_card_foundation verify --manifest registry/atlas/pilot/pilot-v1.json --registry registry/atlas/identity/registry.json`:
  exit 0; 150 units, 272 source records, 114 legacy articles, 140 legacy aliases;
  `heldout_isolation: unverified`, `evaluation_readiness: unknown`, 22 unresolved
  card mappings. This is pilot consistency only.
- The same pilot command with `--heldout-manifest registry/atlas/golden/w0-heldout-membership.json`:
  exit 1, **`REFUSED: Unresolved membership keys; isolation cannot be checked`**.
  Golden keys are not silently discarded or treated as checked against the pilot alone.
- Joint `verify --manifest <pilot> --manifest <host-only selection candidate> --registry <registry> --heldout-manifest <membership>`:
  exit 1, **`REFUSED: Invalid object fields`**. An unadmitted selection is not a
  frozen manifest. No fake manifest/admission object was constructed to claim CLI success.
- `freeze --selection <host-only candidate> ... --heldout-manifest <membership>`:
  exit 1, **`REFUSED: Place one driver source-admission-receipt.json beside selection`**;
  no output was written. Receipt creation remains a non-author step.
- `PROJECT_PYTHON -m pytest -q -n 2 tests/test_word_card_foundation.py`:
  exit 0; **471 passed in 309.84s (0:05:09)**. The checkout guard passed; the
  process guard reported zero survivors attributed to this session.
- The initial coverage run (`-q tests/test_word_card_foundation.py
  --cov=scripts.atlas.word_card_foundation --cov-report=term-missing`) exercised
  all 471 assertions successfully with **99% statement coverage** (564 statements,
  3 missed), but exited 1 because this recovery edited the two report files while
  the checkout guard was active and coverage created `.coverage` in the checkout.
  That was a recovery execution error. Its coverage evidence is preserved
  host-only; the newly created checkout scratch file was removed. The clean rerun
  above kept the checkout static and passed without disabling any guard.
- `PROJECT_PYTHON -m ruff check scripts/atlas/word_card_foundation.py
  tests/test_word_card_foundation.py`: exit 0, **`All checks passed!`**.

AC1–AC4 remain open (**4**). No PR was opened. Independent non-author admission,
exact-head cross-family implementation review, PR CI, a valid 220-case golden
freeze and merged/shipped proof remain absent. Blind held-out evaluation remains
W7 work. The driver owns all **45 missing cases** and the four open criteria;
the next concrete condition is approved evidence-family key support and sufficient
tier-3-only source candidates, followed by the full 220-case non-author admission.
This is a pushed worker handback, not task/issue completion.
