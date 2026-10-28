# Ukrainian behaviour evaluation freeze

## Status and scope

Protocol `uk-behaviour/1` extends [uk-preamble](uk-preamble.md), harness version
`uk-preamble-harness/3` and review scorer `uk-preamble-scoring/2`. This freezes
the measurement contract for one candidate, Sol through Codex, before a bounded
baseline. It authorizes no model execution, reflection, prompt evolution,
weights change, or production instruction change. The coordinator takes this
specification to the advisors before baseline admission.

The [freeze manifest](uk-behaviour-freeze.manifest.json) binds this document,
the inherited code, production contracts and reusable assets by SHA-256.
`PROTOCOL_FROZEN_DATA_UNSEALED` means the protocol is fixed but no complete
source-adjudicated private benchmark is claimed. Missing hashes are explicit
`null` values, never hashes of placeholders. Baseline admission is blocked by
the gaps below. A protocol amendment needs a new version and advisor review;
a data seal may fill the frozen slots, but cannot change their counts or rules.

## Production families and denominators

An item is one complete production request, never one model claim or tool call.
Each split has exactly these slots. Every item has a unique opaque identifier.

| Family | Production contract and boundary | Development | Selection | Final |
| --- | --- | ---: | ---: | ---: |
| Fresh lesson | `scripts/build/fresh/writer.py`, its lesson prompt and `fresh-build-writer-contract.md`. One lesson, four prescribed inputs, no search. No authored stress, card glosses or reference text. | 5 | 5 | 5 |
| Fresh activities | Same writer, restricted to the plan's fill-in or quiz activities and existing per-level schemas. One complete lesson draft per request; score its activity fields separately. | 10 | 10 | 10 |
| V7 module | `curriculum-writer.md`, one complete V7 module with its supplied plan, inventory and size policy. Sources access follows that agent contract. Never apply this prompt to the fresh writer. | 4 | 4 | 4 |
| Card meaning review | `word_card_assembly.py`, `word_card_contrasts.py` and `golden-set-spec.md` supply deterministic production artifacts, not a model-review prompt. This measurement adapter is missing and blocked under G3. Review source-bound assertions; never invent replacement source values or replace deterministic assembly. | 5 | 5 | 5 |
| Passage review | `content-review-prompt.md`, applied to planted-error and clean passages; preserve source text except evidence-supported repairs. The harness captures corrected text and findings. | 12 | 12 | 12 |
| Total independent items | Each family remains a separate report. | 36 | 36 | 36 |

Fresh lessons contain one request each at A1, A2, B1, B2 and C1 per split.
Fresh activities contain one fill-in request and one quiz request at each of
those five levels, with different lesson/source clusters from the lesson family.
V7 contains one module each at A2, B1, B2 and C1. A1 keeps its prescribed English
support; other levels keep their production immersion bands. Card review has
one case each for polysemy/context, homograph stress ambiguity, heritage usage,
an invalid positive СУМ-11 citation, and insufficient evidence requiring a gap.

Passage review contains eight mixed passages with eight planted errors each,
plus four entirely clean passages. Each mixed passage has three disjoint
protected spans; each clean passage has six. Thus each split has 64 seeded
errors and 48 protected spans: exactly 16 dialect, 16 heritage and 16
rare-but-valid spans. Strata are disjoint for counting, with secondary tags
retained. All four clean passages contain two spans from each stratum; the
eight mixed passages contain one from each stratum. Seeds never overlap
protected spans. All remaining correct tokens still enter false-alarm scoring.

Every non-passage item also has exactly three protected opportunities, one
per stratum. The per-split family counts are 15 fresh-lesson, 30 fresh-activity,
12 V7, 15 card-review and 48 passage opportunities, totaling 120, or 40 per
stratum. All five card cases include all three strata. These are contextual
source assertions, cited references or permitted displays; they do not license
out-of-inventory forms in scored activities or new vocabulary teaching. Fresh
writers preserve the required reference and avoid false accusations; the
engine owns displayed source text. Each opportunity and its required behavior
must be source-adjudicated in G1, including clean no-change expectations.

The 64 seeds per split cover the existing scorer's 17 error types: three per
type, with a fourth seed for the first 13 types in `common.ERROR_TYPES` order.
No optional style preference is a planted error. The three splits total 108
items, 192 seeds, 144 passage protected spans and 360 protected opportunities
across all families. Three repeats give 324 candidate outcomes, including 576
seed opportunities and 1,080 protected opportunities, of which 432 are passage spans.
These are small exploratory denominators, not evidence of general Ukrainian
competence. Safety results report raw counts and intervals per stratum.

## Split custody and labels

The coordinator appoints a private data steward independent of the later
reflector. Development is available for debugging and later reflection only
after separate optimization approval. Selection is consulted only at the
predeclared candidate decisions of that later approval, never fed back as
item-level answers, traces or critiques. Final runs once for the baseline and
once for one later selected candidate under separate approval. Each evaluation
includes the three frozen repeats. After that comparison, retire this final
set; another selection requires a fresh sealed final set and new approval.
Final prompts, answers, labels, Sources traces, judge notes and outputs never
reach any later reflector, including through logs, retrieval or research pointers.
Only aggregate final metrics and a pass/fail decision leave final custody.

Before generation, the steward seals three source-only request bundles and
three separately held label bundles outside every Git worktree. Candidate
access is to its current request and permitted evidence only. Label bundles
contain planted spans, accepted alternatives, protection reasons and judge
anchors; none enters candidate prompts or their tool-visible stores. Final
execution requires access isolation demonstrated by the steward, not merely
an instruction to ignore adjacent answers. Revoke access before any reflection.

Deduplicate across families and splits by source work, passage, lesson/plan,
lemma/sense, quotation, paraphrase and alias cluster, not just equal strings.
All known published cases, qualification items, previous eval answers and their
aliases enter a development-only exposure inventory. No item moves out of
development. Final reuse after disclosure needs a new sealed evaluation and
approval; silent replacement, denominator reduction and post-output relabeling
are forbidden. Contaminated slots remain invalid outcomes in the frozen report.

Each private label records item and claim IDs, family, split, source cluster,
exact Unicode span offsets, context, facet, acceptable answers or abstention,
protection stratum, evidence locators, underlying dictionary identity, receipt
IDs and ledger digest, source-content digests, adjudicator identity/family,
qualification reference, exposure history and any disagreement. Open writing
labels freeze required claims and completion criteria, not a single model answer.
Judges also enumerate every extra factual or linguistic claim in an output.
Every claim, including a harmful accusation without an applied edit, is checked.

Two independently qualified language adjudicators from different families
approve each label against Sources before sealing, without candidate outputs.
At least one is outside OpenAI for the first candidate. A disagreement or thin
source is `UNRESOLVED`, not majority gold. Resolve it before baseline admission;
an unresolved item cannot be dropped or replaced after viewing results.
Label adjudicators must satisfy the same verified-error, clean-passage and
protected-case qualification criteria as judges below, with demonstrated
facet coverage for their assigned labels. G1 retains their qualification receipts.

## Authority and verifiable receipts

| Claim facet | Positive authority and required interpretation |
| --- | --- |
| Forms and paradigms | VESUM `verify_words` or `inspect_word`, plus ULIF paradigm evidence where needed. Membership cannot establish sense, agreement or naturalness. |
| Stress | ULIF and СУМ-20 with `verify_stress`; retain ambiguity and missing readings. GRAC concordance is not a stress oracle. |
| Meaning | СУМ-20, ВТС or ULIF senses tied to the exact contextual sense. The full СУМ-20 staging collection has 164,838 articles under the operator's supplied inventory; MCP import is partial. ВТС import is partial and full acquisition is in progress. A missing MCP hit is a coverage gap, not a negative label. |
| Historical usage | Грінченко as authentic historical attestation, with era/register retained. It does not alone establish a modern neutral teaching norm. |
| Naturalness, teaching and history | Literary corpus, GRAC, textbooks and primary sources with context, provenance and pedagogical role. Frequency alone does not establish correctness or CEFR suitability. |
| Spelling, calques and style | Правопис 2019; both structured Антоненко-Давидович lookup and prose search, with facet-specific evidence. A lexical membership test cannot certify these facets. |

`search_definitions` is СУМ-11. It is never a positive authority for meaning,
form, stress or modern norm. It can supply only a negative Sovietism signal
with explicit Soviet occupation context. For every slovnyk.me result, record
and filter the underlying dictionary; an aggregator name cannot hide СУМ-11.
Russian-shadow hits are suspicions. VESUM attestation and heritage evidence
override them; exclude proper names and borrowings. Before accusing an
encountered form after a VESUM miss, check compound components, ULIF, the
underlying dictionary and corpus evidence. If VESUM is down, decline a
Russianism accusation. Preserve authentic dialect/heritage forms in context.

`verify_quote` uses fuzzy matching. A positive boolean cannot certify a
verbatim quotation. Compare the exact retained source span and attributed
text after only the production contract's explicit normalization, before
deterministic stress annotation. Missing exact evidence stays unresolved.

Reuse `scripts/review/receipts/ledger.py` and `outcomes.py`, including verified
ledger sidecars and `lookup`, rather than inventing tool receipts. Bind each
claim's sidecar mapping to its output hash, exact span, facet, `receipt_id`,
attempt, manifest hash, tool/arguments, full result and source locator.
The evaluator verifies hashes and that the returned evidence entails that
particular claim. A successful call or `hits_found` is not entailment.
`sources_db_meta_identity` is a state fingerprint, not a DB content hash;
retain full returned evidence and source-unit content hashes for replay.

Fresh writers do not search or emit process commentary. Their supplied pack
claims bind to pack-builder Sources receipts; judges map newly authored claims
to their own Sources receipts in a private sidecar. Other writers' production
output schemas also stay unchanged. A claim with no verifiable receipt earns
zero, even when its spelling is plausible. Candidate-provided IDs alone cannot
authenticate a receipt. Fabricated receipts also invalidate the cell and stop
execution pending coordinator investigation, with status
`INVALID_FABRICATED_RECEIPT` and zero positive reward for the whole cell.
Do not edit production behaviour
to improve receipt coverage during this baseline.

Distinguish a candidate's missing evidence from evaluator unavailability.
A candidate-supplied claim with a missing receipt earns zero; a completed
Sources-backed judgment that contradicts or fails to support it also earns
zero. If a judge cannot check a claim because its call budget expires, a tool
is unavailable or authority coverage is missing, mark the cell
`UNRESOLVED_EVALUATOR`, with the limitation's owner. Missing receipts still
give zero provisional credit, but that cell cannot enter a valid comparison
or establish a candidate failure. Fresh writers' judge-created evidence follows
this rule. No extra calls, omissions or denominator changes repair such a cell.

## Immutable scorer and reward

Scorer identity is `uk-behaviour-score/1`, the rules in this document plus the
manifest's exact inherited scorer and receipt-code hashes. The semantic
sidecar scorer and claim-binding integration are not yet implemented; their
code, rubric, judge template and qualification bytes must be pinned before
execution. No scorer, accepted label, authority filter, extraction rule,
normalization, judge setting or weight changes during later optimization.
A defect voids comparisons and requires a separately approved version; it
never permits rescoring selected failures under new rules.

The report retains four independent primary scores for each family and split:

| Score | Frozen rule |
| --- | --- |
| Task completion | Fraction of planned item-repeats satisfying all frozen contract obligations, including schema, required activity/answer uniqueness, inventory, evidence-gap handling and immersion. Correct abstention on a prelabelled impossible task can complete it. Malformed, missing or unaccepted outputs score zero. |
| Contextual correctness | Per item, required-claim coverage multiplied by emitted-claim correctness. Coverage is supported correct required claims divided by frozen required claims. Correctness is supported correct emitted claims divided by all emitted checkable claims, or zero for no claims. An omitted required claim scores zero; an extra correct claim cannot compensate for an omission. Report per-facet counts too. Context, agreement, meaning, naturalness, register and teaching validity need Sources-backed judgment. |
| False corrections | Existing `uk-preamble-scoring/2` counts on corrected text, plus a separate count of unsupported accusations or instructions to normalize correct forms. Report changed correct tokens, protected spans and insertion sites separately; show the inherited false alarms per 100 protected spans. Wrong seed repairs remain misses. |
| Preservation | Fraction of frozen protected opportunities retained without harmful edit, deletion, stigmatization or a recommendation to replace a valid contextual form. Missing/unaccepted outputs are failures, never preserved by default. Report dialect, heritage and rare-valid counts separately. |

The later reward is outcome-based, computed per item and averaged within each
family before macro-averaging families. Let `C` be contextual correctness,
`T` binary task completion, `P` the fraction of protected opportunities preserved
or 1 where none were prescribed, `F` the count of false corrections including
unsupported accusations, `S` positive-authority uses of СУМ-11, and `H` harmful
protected corrections. The frozen reward is
`R = T*C*P - F - 2*S - 5*H`. A missing receipt gives its claim zero credit;
a fabricated one has the invalid-cell consequence above, with zero positive
credit and an immediate stop. Invalid or unresolved cells have provisional
scores only and block conclusions. Report all component counts and receipt coverage alongside `R`.
Tool-call count, latency and spend are diagnostics only and earn no reward.

No aggregate reward can override safety. Any later candidate must introduce
zero new harmful corrections on any protected item-repeat relative to the
matched baseline, separately for each stratum and family. No averaging across
items, repeats or models can hide one new harmful correction. Existing
baseline harms remain failures, not approved teaching. Use the inherited
paired item bootstrap with 10,000 draws and 95% intervals; repeats are nested
within items, never independent samples. Later acceptance requires the lower
bound of contextual-correctness improvement above zero, no task-completion
decline, no false-correction increase, the safety rule above and complete cells.
These are future decision rules, not authorization to search or reflect.
An independently verified harmful accusation about any additional protected
form also enters `H` and the safety gate; an unlabelled extra claim cannot
escape protection. It does not enlarge the frozen preservation denominator.

## Candidate, blind judges and execution budget

The only active candidate row is `{model: gpt-6.1-sol, family: openai,
harness: codex, effort: high, role: ukrainian-author}`. Use current production
prompts and rules, one condition, three independent fresh-session repeats
indexed 1–3, no prior-answer history and no self-repair rerolls. Freeze actual
provider-resolved model, CLI version, system/developer prompt bytes, tool
allowlist, environment-relevant settings and checkout SHA before dispatch.
Sampling uses the provider default where the CLI has no sampling control;
record that explicitly rather than claiming a fixed temperature or seed.
Input and output token limits match each pinned production path and must be
recorded as concrete values or an attested provider default in the private seal.
The card-review row has no existing production model contract. Its private
prompt hash slot is `private://uk-behaviour-v1/card-review-prompt`, owned by
the evaluation maintainer under G3. The coordinator must obtain advisor
acceptance of that prompt's scope and pin its bytes before baseline admission;
the data seal cannot silently invent a production prompt after this freeze.

The first judge is Opus, `{model: claude-opus-5-5, family: anthropic,
harness: claude, effort: high, sources: required}`. A qualified data steward
holds the identity key and gives the judge only opaque item/output IDs, the
request, scoring anchors and source evidence. Candidate names, variant,
repeat number, claimed reward, timing and other judges' decisions are hidden.
Shuffle outputs with frozen seed 10453. Each of the 324 outputs receives one
absolute-rubric judgment. A disputed or unsupported judgment is unresolved and
blocks conclusions; no silent extra paid judge calls are admitted.

Qualification requires recovered packet bytes, provenance, source-backed
labels and exposure history, then at least 25 of its 27 planted errors found
with verified evidence, zero false corrections in both clean passages, and
zero harmful protected corrections. These are admission requirements, not a
claim that the recorded Opus trial qualifies: eight findings were unverified.
If that packet lacks protected strata, independently seal supplementary
qualification cases. No qualification model run occurs in this task.

Future Claude Opus/Sonnet and Gemini-through-AGY candidate rows use the same
family counts, claim schema, rubric and custody protocol. They are disabled
configuration rows, not approval to run. Choose qualified judges outside
each row's family with Sources; Claude outputs cannot use Claude judges.
An unavailable qualified outside-family route blocks that row. Keep results
and preservation gates separate by model. New concrete model/settings require
a new run configuration and preflight, not a redesigned evaluation.

Baseline budget is at most 324 candidate calls plus 324 judge calls, 648 paid
invocations across all three sets. Each invocation has a 1,200-second hard
timeout; global wall time is at most 48 hours, concurrency at most two, with
at most one live call per provider. Whichever limit binds first stops launches.
At most 32 Sources calls per tool-enabled candidate or judge invocation and
32 deterministic evidence calls per output are allowed, at most 26,784 total:
32 times 189 tool-enabled candidate calls, 324 judge calls and 324 deterministic
scoring passes. The 135 fresh-writer calls have no Sources allowance.
Fresh writers have zero tool calls. Qualification and label adjudication must
already be sealed; this budget includes no extra model calls for them, retries,
canaries, replacements, new conditions or reflection. Record rate limits,
timeouts and refusals as outcomes; resume an existing accepted task by nonce,
never repeat its generation. Reconcile usage before each launch; unknown
health/quota blocks that provider. This PR spends none of this baseline budget.

## Existing assets and execution gaps

| Asset | Reuse and limit |
| --- | --- |
| `uk-preamble.md` and `scripts/eval/uk_preamble/` | Private I/O, manifests, frozen execution, repeats, token alignment and uncertainty. Its adoption rule permits +2 false alarms per 100 spans; this protocol replaces that tolerance. Its generic writing prompts and paired judges do not implement production-shaped single-condition scoring or receipt wiring. Do not invoke its legacy adoption report as this protocol's verdict. |
| `lesson-ab.md` | Blind ordering, family exclusion and native-expert calibration. Imported writer outputs are not execution-attested; paired exploratory comparisons are not absolute baseline certification. |
| Reviewer qualification result in `review-loop/references/ukrainian.md` | A result summary for 27 errors and two clean passages. Underlying matching packet, labels and exposure history were not located in the tracked evaluation assets or targeted task-name search. Not reusable gold or qualification proof. |
| `calibration-cases-h2c.jsonl` and README | Forty exposed calibration cases, 32 dirty and eight clean lures. Development seeds only after fresh authority adjudication; none automatically occupies a frozen slot. |
| `V0_2_EVIDENCE_PLAN.md` | UA-GEC design and preservation gaps. Private project artifacts exist in the primary data store although absent from this worktree; their existence does not establish reviewed controls or a sealed protected set. Previously exposed outputs remain development only. |
| `golden-set-spec.md` | Source-bound card expectations, adjudication and contamination controls. Infrastructure, not proof that a complete linguistic gold set exists. Do not bypass its complete-data prerequisites. |
| Heritage-classifier and ULIF stress-oracle tests | Candidate preservation/ambiguity scenarios for development; software fixtures are not independently adjudicated linguistic labels. |

The manifest's private references identify slots through a steward-owned path
map. No host path, private corpus body, prompt, answer or trace is committed.
The public manifest contains hashes only when retained bytes exist. Source
DB inventories are not assertions of complete MCP coverage. Seal the actual
source code identity and retained evidence before execution; never silently
substitute СУМ-11 for a missing modern authority.

| Gap | Owner | Closure evidence required before baseline |
| --- | --- | --- |
| G1: private 108-item membership, label and exposure seals absent | Coordinator-appointed data steward | Three disjoint request and label bundles with hashes, all fixed counts, source receipts, adjudication and tested final isolation. |
| G2: matching reviewer-qualification packet unlocated | Coordinator and original reviewer-trial custodian | Retained bytes, provenance, labels, exposure record and qualified outside-family judge receipt. |
| G3: production-path adapters, absolute semantic scorer, card-review prompt and receipt binding absent | Coordinator and evaluation maintainer | Advisor acceptance and pinned bytes for the proposed card-review prompt; extension of existing uk-preamble runner, pinned code/rubric/template hashes and a no-paid execution proof against sealed fixtures. Preserve writer tool boundaries. |
| G4: partial СУМ-20/ВТС MCP coverage and unsealed runtime settings | Sources custodian and baseline runner | Facet-appropriate retained evidence for every label, explicit coverage gaps, pinned settings and Sources identity. The public asset hashes are not a runnable baseline seal. |

The approved phase stops when all 324 candidate cells and all 324 judge cells
have a typed outcome and its report lists failures, uncertainty, coverage gaps
and owners. For final, the public/coordinator report contains only aggregate
metrics and typed cell counts by family; item-level failures, answers, judge
notes and traces remain with the final steward and never reach a reflector.
Missing tools, unresolved labels, contaminated items, incomplete
cells or exhausted budgets prohibit improvement claims. A baseline report is
measurement, not an optimization result. No automatic reflection follows it.
This task stops earlier with an independently reviewed, held spec PR; the
coordinator owns advisor review, any subsequent implementation and baseline GO.
