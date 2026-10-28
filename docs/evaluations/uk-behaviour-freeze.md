# Ukrainian behaviour evaluation freeze

## Status and scope

Protocol `uk-behaviour/2` extends [uk-preamble](uk-preamble.md), harness version
`uk-preamble-harness/3` and review scorer `uk-preamble-scoring/2`. This freezes
the measurement contract for Sol and Terra through Codex on identical sets,
before a bounded baseline. Terra is a measured candidate under this protocol,
not a Ukrainian author, adjudicator or reviewer of record. This specification
authorizes no model execution, reflection, prompt evolution,
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
| Fresh lesson | `scripts/build/fresh/writer.py`, its lesson prompt and `fresh-build-writer-contract.md`. One lesson, four prescribed inputs, no search. No authored stress, card glosses or reference text. | 2 | 2 | 2 |
| Fresh activities | Same writer, restricted to the plan's fill-in or quiz activities and existing per-level schemas. One complete lesson draft per request; score its activity fields separately. | 2 | 2 | 2 |
| V7 module | `curriculum-writer.md`, one complete V7 module with its supplied plan, inventory and size policy. Sources access follows that agent contract. Never apply this prompt to the fresh writer. | 1 | 1 | 1 |
| Exercise review | A1 existing exercise requests, including one complete ordered exercise block for the answer-position case. Findings cover the stem, gloss, options, key and accepted alternatives. The adapter and prompt require G3 acceptance. | 12 | 12 | 12 |
| Card review | `word_card_assembly.py`, `word_card_contrasts.py` and `golden-set-spec.md` supply deterministic production artifacts, not a model-review prompt. The G3 adapter reviews A1 meaning, stress and form assertions; it cannot replace deterministic assembly or invent source values. | 7 | 7 | 7 |
| Passage review | `content-review-prompt.md`, applied to planted-error and clean A1/A2 passages; preserve source text except evidence-supported repairs. The harness captures corrected text and findings. | 12 | 12 | 12 |
| Pedagogy review | One lesson, plan or exercise snippet with its target, learner state, prerequisites and available listening resources. The G3 adapter assesses pedagogy in the labelled mode against the three norms below. No production lesson is rewritten by this review. | 16 | 16 | 16 |
| Total independent items | Each family remains a separate report. | 52 | 52 | 52 |

Each split has 46 A1 requests and six A2 requests. The 47 review requests
serve the A1 sweep first. Fresh lessons have one A1 and one A2 request,
fresh activities have one A1 fill-in and one A1 quiz request, and V7 has one
A2 module. B1–C1 authoring belongs to the later build phase and requires a
separately approved extension. A1 retains its prescribed English support.
A2 retains its production immersion band. Fresh activities forbid a stem,
translation, gloss, explanation or distractor that gives away the answer or
its required form. Labels list every accepted alternative, not just one key.

All 12 exercise requests are A1. Nine have one labelled defect each: a stem
that translates the answer, a stem that names it, a stem that describes its
form, a giveaway gloss, distractor agreement that reveals the answer, an
ambiguous key with a second defensible option, a wrong key, a stress error,
and a form error. One request has an ordered block with a planted
answer-position pattern, adjudicated against a frozen ordering rule and a
matched clean block. Two requests are entirely clean, including one with
multiple explicitly accepted answers. Pattern labels concern the whole block;
the block is one request, not extra denominator items. Sources receipts
verify the linguistic premises of every planted defect and every defensible
alternative. A model's intuition never establishes a seed or a key.

All seven card requests are fixed at A1, with one case each for a contextual
meaning error, a stress error, a form error, valid stress ambiguity, valid
heritage usage, an invalid positive СУМ-11 citation, and insufficient evidence
requiring a gap. Clean ambiguity, heritage and gap responses must preserve
attested alternatives and cannot invent a replacement. The A1 level refers
to the teaching target; protected contextual references are not new teaching.

Passage review contains eight mixed passages with eight planted errors each,
plus four entirely clean passages. Six mixed and two clean passages are A1;
two mixed and two clean passages are A2. Each mixed passage has three disjoint
protected spans; each clean passage has six. Thus each split has 64 seeded
errors and 48 protected spans: exactly 16 dialect, 16 heritage and 16
rare-but-valid spans. Strata are disjoint for counting, with secondary tags
retained. All four clean passages contain two spans from each stratum; the
eight mixed passages contain one from each stratum. Seeds never overlap
protected spans. All remaining correct tokens still enter false-alarm scoring.

Every non-passage item also has exactly three protected opportunities, one
per stratum. The per-split family counts are six fresh-lesson, six fresh-activity,
three V7, 36 exercise, 21 card, 48 passage and 48 pedagogy opportunities,
totaling 168, or 56 per stratum. Every card, exercise and pedagogy request
includes all three strata. These are contextual
source assertions, cited references or permitted displays; they do not license
out-of-inventory forms in scored activities or new vocabulary teaching. Fresh
writers preserve the required reference and avoid false accusations; the
engine owns displayed source text. Each opportunity and its required behavior
must be source-adjudicated in G1, including clean no-change expectations.

The 64 seeds per split cover the existing scorer's 17 error types: three per
type, with a fourth seed for the first 13 types in `common.ERROR_TYPES` order.
No optional style preference is a planted error. The three splits total 156
items, 192 passage seeds, 144 passage protected spans and 504 protected
opportunities across all families. Three repeats give 468 candidate outcomes,
including 576 passage seed opportunities and 1,512 protected opportunities,
of which 432 are passage spans.
Those are per-row totals across all splits, not authorization to run final now.
Sol and Terra each use the same items and repeats. Exercise defects and card
facets and pedagogy defects have their own labelled counts in addition to the
192 passage seeds. The existing six families keep every earlier slot.
These are small exploratory denominators, not evidence of general Ukrainian
competence. Safety results report raw counts and intervals per stratum.

## Pedagogy, learner and judging modes

Pedagogy is a separate judged dimension grounded in Ukrainian pedagogy, not
English-language-teaching norms. Its dedicated review requests and judgments
remain separate from language-review requests. These three norms bind its
labels, qualification and rubric:

| Norm | Role and frozen evidence |
| --- | --- |
| State Standard 2024 | Sets minimum coverage, including the A1 floor in [the mapping](../l2-uk-en/state-standard-2024-mapping.yaml) and [Standard text](../l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt), A1 lines 221–747. Use the sources table in [the A1 arc](../epics/fresh-build-a1-arc.md). The Standard is a floor, not a rigid lesson order or a ceiling; earlier teaching needs the arc's ULP evidence. A coverage omission is a defect at the point the plan promises that coverage. |
| Ukrainian school textbooks | Show how a point is taught. Read corpus pages through Sources, with [textbook reading notes](../l2-uk-direct/textbook-reading-notes/) as navigation. Retain the printed page, source file, chunk locator, exact relevant span and content hash. A chunk's title or a reading-note summary alone cannot prove a teaching claim. |
| Anna Ohoiko's method | Sets adult presentation and progression, grounded in ULP Seasons 1–2 and [the presentation pattern](../best-practices/ulp-presentation-pattern.md). Apply all seven practices with that document's fresh-A1 adaptations: Ukrainian before its English gloss; aligned bilingual passages; displayed stress supplied by the engine; Ukrainian dialogue before its breakdown; comprehension or practical recap with the prescribed early-A1 English support; translation practice in the workbook; direct teaching with Ukrainian cultural context and no borrowed narrator persona. Track the S1 through S6 progression without imposing later-season immersion on a beginner. S5–S6 trends described as unsampled in the reference are not calibrated thresholds. Use the method; never copy her text, scripts or persona. |

Where these disagree, the Standard sets coverage and Ohoiko sets presentation
and schedule. Textbook methods inform teaching, adapted to the learner.
They do not override adult presentation. This precedence and the arc's
chunk-first permission prevent a judge from treating any early case chunk or
different school-book ordering as an automatic error.

The learner in [north-star](../north-star.md) is a self-driven adult or older
teen who reads English and may know no Ukrainian or Cyrillic. Keep sound
before letter, Cyrillic decoding, a case first as a meaningful chunk and
later as a system, explicit prerequisites, manageable sequencing and load.
Do not import a primer's assumption that the learner is a six- or
seven-year-old learning literacy itself. Pre-literacy drills, handwriting
motor drills and childish framing are defects for this audience. Recognising
printed or handwritten Cyrillic and learning Ukrainian sound-letter relations
remain useful; merely being simple or appearing in a primer is not a defect.
For example, Захарійчук 2025 part 1, printed p. 13, chunk
`1-klas-bukvar-zaharijchuk-2025-1_s0012`, models identifying sounds. The
Большакова reading notes place sounds on pp. 14–18 before letters on p. 19.
Літвінова 2023 grade 6, p. 138, chunk
`6-klas-ukrmova-litvinova-2023_s0143`, moves from contextual forms to the case
system. These are teaching evidence, not instructions to copy child-facing
exercises or to teach all seven cases as A1 systems.

Every item, including existing families and clean controls, carries exactly
one candidate-visible `judging_mode`, `repair` or `authoring`, and a matching
private label. No judge infers mode from the candidate's output.
The accepted G3 adapter carries mode in request metadata within permitted
inputs. It adds no fifth fresh-writer input or production output field.

- `repair` applies to the published `/a1-v1/` course, which was not built on
  Ohoiko's method. Flag harm to the learner now: a wrong or ambiguous key,
  answer leakage, an incomplete or unsuitable section, child-level material,
  wrong stress or form, or contradiction of the Standard. A prerequisite or
  load finding needs the supplied learner state and a concrete learning
  failure. Deviation from Ohoiko's sequence alone is not a defect and cannot
  justify rewriting the course into her method.
- `authoring` applies to new-format `/a1/` and later levels. All three norms
  bind under the precedence above, with the learner's level and production
  contract. An approved chunk before its later grammatical system is valid.
  New V7 and fresh-writer requests are authoring even when their prompts use
  different production contracts.

| Family per split | Repair | Authoring |
| --- | ---: | ---: |
| Fresh lesson | 0 | 2 |
| Fresh activities | 0 | 2 |
| V7 module | 0 | 1 |
| Exercise review | 12 | 0 |
| Card review | 7 | 0 |
| Passage review | 8 | 4 |
| Pedagogy review | 6 | 10 |
| Total | 33 | 19 |

The eight A1 passage requests use repair; the four A2 requests use authoring.
All 16 pedagogy requests are A1. Each split therefore has 33 A1 repair
requests and 19 authoring requests, 13 A1 and six A2. Mode is fixed before
labels and identical for both candidates. Report completion, correctness,
false corrections, preservation and pedagogy results by family and mode.
Keep mode failures visible alongside aggregates. G1 freezes applicable pedagogy obligations
for authoring outputs and concrete learner harms for repair outputs.

### Listening input and video

Collected video is listening input to plan into lessons, as the published A1
does with its alphabet videos. Authoring-mode plans name each chosen video,
its listening skill and where it is used. Lessons execute that plan. Ignoring
an available, level-appropriate video for the stated listening skill is a
pedagogy defect. Available means a retained resource with verified content,
level, access and skill suitability in the sealed bundle. A catalogue tag or
HTTP success alone is insufficient. No available suitable video means no
missing-video accusation; an evidence gap remains explicit.

The [2026-10-04 decision on the pilot](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/8425#issuecomment-5977822358)
requires videos shown whole with sound and picture. No hidden player,
audio-only extraction, blocked or overlaid player, or hiding title, captions,
thumbnail or letter until an answer. Use an unscored watch, listen and repeat
activity where that is the approved format. This is a project presentation
decision, not a linguistic inference. The immutable evidence bundle retains
the decision bytes and locator; live video fetching during evaluation is
forbidden. A missing-video item provides the candidate the relevant resource
inventory and learner state, without revealing the planted label.

### Frozen pedagogy item roster

One row below can allocate several independent requests; each planted request
has exactly one primary defect. Controls have zero defects. Every snippet
includes enough lesson or plan context to judge the claimed target and
prerequisites. The counts apply independently to development, selection and
final; sources and alias clusters remain disjoint between splits.

| Defect kind or control | Repair | Authoring | Snippet and required source anchor |
| --- | ---: | ---: | --- |
| Standard coverage or sequencing contradiction | 1 | 0 | Plan that omits or defers promised A1 coverage beyond its completion. Cite the exact Standard lines, for example 678–699 for case functions, plus the coverage map. A different order alone is not sufficient. |
| Textbook sequencing failure | 0 | 1 | Lesson requiring letter decoding before the sound-letter preparation. Cite the actual primer pages and explain the prerequisite, using Большакова pp. 14–19 or corresponding Sources pages. |
| Point before prerequisite or excessive load | 1 | 1 | Repair lesson and authoring plan. Cite learner-state evidence and the textbook page or Ohoiko chunk-to-system pattern that establishes the missing step. The repair case must demonstrate present learner harm. |
| Child-level material | 1 | 1 | Repair lesson and authoring exercise. Cite the primer page from which the pre-literacy, motor drill or childish framing was imported, and the adult adaptation rule above. Do not label Cyrillic decoding itself as childish. |
| Exercise does not practise stated target | 1 | 1 | Exercises whose required action bypasses the declared Ukrainian skill. Cite the target's Standard lines or textbook teaching page and explain the mismatch. |
| Incomplete or unsuitable section | 1 | 0 | Lesson section missing the explanation or practice needed for its promised point. Cite its Standard or textbook anchor and the missing learner action. |
| Answer given away | 0 | 1 | Exercise with its answer exposed before the attempt. Cite the Ohoiko practice 6 separation of teaching and workbook recall, the stated task and the exact leak. The existing repair exercise family retains all five leakage cases. |
| Missing planned video | 0 | 1 | Plan ignoring a supplied suitable video for its listening skill. Cite Standard listening lines 233–277, the Ohoiko exposure-before-breakdown pattern, the retained video and the decision above. |
| Hidden-player audio-only video use | 0 | 1 | Plan using a supplied video contrary to the decision. Cite the same pedagogy anchor and the retained decision and video locators. |
| Ohoiko presentation failure | 0 | 1 | Lesson suppressing the supported Ukrainian encounter in favour of an English-first explanation or premature loss of English scaffolding. Cite the applicable numbered practice and S1/S2 progression, with the learner-state adaptation. |
| Clean control | 1 | 2 | Repair lesson with harmless non-Ohoiko sequencing; authoring plan with a whole visible listening video; authoring exercise practising its target without leakage. Each carries positive source anchors and a no-change expectation. |
| Total requests | 6 | 10 | Six lesson, five plan and five exercise snippets. |

Thus each split has 13 planted pedagogy defects, five repair and eight
authoring, plus three controls. Across three splits these are 39 defects and
nine controls; three repeats yield 117 defect and 27 control opportunities
per candidate row. Across the roster, controls also demonstrate useful
teaching of sounds before letters and permitted chunk-before-system use.
Keep false-correction counts on controls, including attempts to impose the
Ohoiko sequence on repair material. Kind counts never replace request counts.
Overlapping tags, such as leakage, remain secondary; do not double-count
the same request as an existing exercise-family case.

Every planted defect needs a source-entailing anchor before G1 can seal it:
Standard file/hash and exact lines, textbook source/hash and printed page
with retained Sources span, or Ohoiko numbered pattern/season and retained
ULP S1–S2 evidence. The table fixes scenarios and required anchor types, not
already-adjudicated gold. Record why the source entails the finding, its
pedagogical role, mode applicability and adult adaptation. Video cases also
retain the decision and resource locators. A reading note, model preference
or corpus occurrence alone is insufficient. Unresolved source support blocks
admission, with no replacement after outputs. Private Ohoiko text remains
grounding-only and never enters candidate-authored lessons or public gold.
The public examples above can seed development only. Selection and final use
unexposed snippet clusters and source-entailing anchors. Shared normative
references such as the Standard are evidence, not evaluated snippet clusters;
reusing a norm never permits reusing an evaluated lesson, plan or exercise.

## Split custody and labels

The coordinator appoints a private data steward independent of the later
reflector. Development is available for debugging and later reflection only
after separate optimization approval. Selection has at most three consultations
for the entire programme: one joint baseline consultation for Sol and Terra,
then at most two predeclared joint variant decisions under separate approval
and budget. A consultation is one sealed batch, at most one variant per model,
with three repeats; partial reports count and cannot be re-queried. Only
aggregate metrics and typed counts leave custody, never item-level answers,
traces or critiques. No adaptive subset queries or replacement consultations.

The initial baseline runs development and selection only. Final is deferred
until selection nominates at most one variant per model. The steward then runs
the frozen Sol and Terra baselines and both selected variants together, in
interleaved matched blocks against the same Sources snapshot and provider
configuration. An unchanged selected row reuses that simultaneous baseline
output, never duplicates it. Up to four rows have three repeats each. Both
models therefore receive a direct final comparison, and each changed variant
has a simultaneous baseline. Provider-resolved identity and settings must match
within each model's pair; a drift invalidates that comparison and stops it.
No earlier final outputs are retained as a months-old baseline. After that comparison, retire this final
set; another selection requires a fresh sealed final set and new approval.
Final prompts, answers, labels, Sources traces, adjudication and judge
transcripts, notes, disputes and outputs never
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

Each private label records item and claim IDs, family, split, judging mode,
learner state, stated target, prerequisites, primary defect kind or clean
status, pedagogy norm and source-entailment/adaptation rationale, source cluster,
exact Unicode span offsets, context, facet, acceptable answers or abstention,
protection stratum, evidence locators, underlying dictionary identity, receipt
IDs and ledger digest, source-content digests, adjudicator identity/family,
qualification reference, exposure history and any disagreement. Open writing
labels freeze required claims and completion criteria, not a single model answer.
Judges enumerate every extra factual or linguistic claim. Only claims within
the frozen facets, and every proposed or applied edit, enter positive
correctness. G1 fixes the positive-credit assertion slots within those facets.
Each slot earns credit at most once. Extra assertions beyond those slots,
including easy true assertions within a facet, earn no credit and incur the
padding penalty below. Every proposed edit enters correctness and safety
checks, even without a matching slot. Every accusation receives a safety check.

Two independently qualified language adjudicators from different families
approve each label against Sources before sealing, without candidate outputs.
For final, neither adjudicator nor either judge nor a dispute adjudicator may
belong to any family scored on that set. With Sol and Terra, OpenAI is excluded
from every final label and judgment. Adding a Claude or Gemini candidate later
requires a new final seal with qualified judges and adjudicators outside all
scored families; it cannot reuse labels or judgments its family has seen.
A disagreement or thin
source is `UNRESOLVED`, not majority gold. Resolve it before baseline admission;
an unresolved item cannot be dropped or replaced after viewing results.
Label adjudicators must satisfy the same verified-error, clean-passage and
protected-case qualification criteria as judges below, with demonstrated
facet coverage for their assigned labels. G1 retains their qualification receipts.

## Authority and verifiable receipts

Before any labels are adjudicated, the Sources custodian seals one immutable,
read-only Sources snapshot for the whole programme, including VESUM, ULIF,
СУМ-20, ВТС, corpus/textbook evidence and tool implementations/configuration.
Include the Standard, mapping, arc, learner profile, Ohoiko patterns and S1–S2
evidence, reading notes, video catalogue, retained video content evidence and
the dated public video decision. Seal all evidence used for pedagogy labels.
The private seal records content hashes for every backing data artifact,
source unit, tool code and index, plus snapshot ID and access-isolation proof.
Every label, candidate tool call, pack receipt and judge uses that snapshot.
Live network fallback, mutable imports and current production DB reads are
disabled for evaluation. Retained external evidence enters the seal before
labels, never mid-run. Verify hashes before each phase and final repeat.
A changed or unavailable artifact stops execution; it cannot be repaired by
refreshing a receipt. Snapshot replacement requires a new approved protocol
and label seal, not just a new runtime fingerprint. Provider drift is recorded
separately and never attributed to improved Sources coverage.

| Claim facet | Positive authority and required interpretation |
| --- | --- |
| Forms and paradigms | VESUM `verify_words` or `inspect_word`, plus ULIF paradigm evidence where needed. Membership cannot establish sense, agreement or naturalness. |
| Stress | ULIF and СУМ-20 with `verify_stress`; retain ambiguity and missing readings. GRAC concordance is not a stress oracle. |
| Meaning | СУМ-20, ВТС or ULIF senses tied to the exact contextual sense. The full СУМ-20 staging collection has 164,838 articles under the operator's supplied inventory; MCP import is partial. ВТС import is partial and full acquisition is in progress. A missing MCP hit is a coverage gap, not a negative label. |
| Historical usage | Грінченко as authentic historical attestation, with era/register retained. It does not alone establish a modern neutral teaching norm. |
| Naturalness, teaching and history | Literary corpus, GRAC, textbooks and primary sources with context, provenance and pedagogical role. Frequency alone does not establish correctness or CEFR suitability. |
| Pedagogy | Standard coverage, Sources textbook pages and Ohoiko method/progression under the learner and mode rules above. Retain the target, prerequisites, adult adaptation and source-entailment rationale; a sequence preference alone cannot establish repair harm. Video judgments also require the sealed decision and suitable resource evidence. |
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
execution pending investigation, with status
`INVALID_FABRICATED_RECEIPT` and zero positive reward for the whole cell.
The coordinator owns non-final investigations. Final investigations stay with
the final steward and an isolated qualified investigator who cannot later
reflect on candidates; only the aggregate typed outcome leaves final custody.
Do not edit production behaviour
to improve receipt coverage during this baseline.

Distinguish a candidate's missing evidence from evaluator unavailability.
A candidate-supplied claim with a missing receipt earns zero; a completed
Sources-backed judgment that contradicts or fails to support it also earns
zero. If a judge cannot check an in-contract claim because its call budget
expires, a tool is unavailable or authority coverage is missing, mark the cell
`UNRESOLVED_EVALUATOR`, with the limitation's owner. Missing receipts still
give zero provisional credit, and the cell cannot enter a valid comparison.
Only unchecked claims remain unresolved; evaluator limits cannot erase verified
candidate failures in that same cell. Retain every verified incorrect claim,
false accusation and protected harm, including their `F` and `H` counts.
Fabrication is always a candidate integrity failure, even if other claims
remain unchecked. Cell-status precedence is `INVALID_FABRICATED_RECEIPT`
before `INVALID_OVERPRODUCTION`, before `UNRESOLVED_EVALUATOR`, before a complete scored outcome. Precedence
never discards already verified claim-level failures. Fresh writers'
judge-created evidence follows this rule. No extra calls, omissions or
denominator changes repair such a cell.

## Immutable scorer and reward

Scorer identity is `uk-behaviour-score/2`, the rules in this document plus the
manifest's exact inherited scorer and receipt-code hashes. The semantic
sidecar scorer and claim-binding integration are not yet implemented; their
code, rubric, judge template and qualification bytes must be pinned before
execution. No scorer, accepted label, authority filter, extraction rule,
normalization, judge setting or weight changes during later optimization.
A defect voids comparisons and requires a separately approved version; it
never permits rescoring selected failures under new rules.

The report retains four independent primary scores for each family and split.
Pedagogy findings enter the same frozen assertion-slot, receipt and penalty
rules as linguistic findings; missed planted defects reduce required-claim
coverage, invented defects enter false corrections, and unsupported method
claims earn no credit. A correct clean pedagogy review earns full credit.
The dedicated pedagogy dimension also reports detection numerator/denominator
by defect kind and mode, control false alarms and source-entailment coverage.
No additional blended pedagogy average can offset a failed primary gate.
Applicable pedagogy obligations also bind authoring completion labels; repair
completion cannot require an Ohoiko rewrite. This changes no production
reviewer prompts or dimension-call boundaries.

| Score | Frozen rule |
| --- | --- |
| Task completion | Fraction of planned item-repeats satisfying all frozen contract obligations, including schema, required activity/answer uniqueness, inventory, evidence-gap handling and immersion. Correct abstention on a prelabelled impossible task can complete it. Malformed, missing or unaccepted outputs score zero. |
| Contextual correctness | Per item, required-claim coverage multiplied by emitted-claim correctness. Coverage is supported correct required claims divided by frozen required claims, or 1 when there are none. Correctness is supported correct emitted assertion slots divided by all emitted assertion slots plus unsupported extra claims and incorrect edits. Correct extra assertions beyond the frozen slots never enlarge either positive-credit count. With none emitted, correctness is 1 only for a source-verified correct clean no-change or prelabelled evidence-gap response, otherwise 0. Missing required claims receive zero coverage credit. Extra true claims cannot compensate for omissions. Report per-facet counts too. Context, agreement, meaning, naturalness, register and teaching validity need Sources-backed judgment. |
| False corrections | Existing `uk-preamble-scoring/2` counts on corrected text, plus a separate count of unsupported accusations or instructions to normalize correct forms. Report changed correct tokens, protected spans and insertion sites separately; show the inherited false alarms per 100 protected spans. Wrong seed repairs remain misses. |
| Preservation | Fraction of frozen protected opportunities retained without harmful edit, deletion, stigmatization or a recommendation to replace a valid contextual form. Missing/unaccepted outputs are failures, never preserved by default. Report dialect, heritage and rare-valid counts separately. |

For binary `T`, completion requires an accepted response that addresses every
required facet and output slot. Its linguistic accuracy is measured by `C`;
one erroneous answer does not become an omission. A source-verified clean or
gap response can satisfy every slot without emitting a positive claim.

The reward is computed per item, then averaged within each family before an
equal-weight macro-average of the seven families. Let `C` be contextual
correctness, `T` binary task completion and `P` the fraction of protected
opportunities preserved, or 1 when none were prescribed. `F` counts false
corrections, including unsupported accusations; `S` counts positive-authority
uses of СУМ-11; `H` counts harmful protected corrections; `X` counts extra
checkable assertions outside the frozen positive-credit slots, including
off-facet claims. Semantic duplicates count once for credit and every
repetition counts toward size limits. G1 freezes a positive opportunity count
`O` per item before outputs, covering required facets, correct-token checks
and protected spans without duplication. A candidate cannot enlarge `O`.
Define `f = min(1, F/O)`, `s = min(1, S/O)`, `x = min(1, X/O)` and
`Q = C*P*(1-f)*(1-s)*(1-x)`, which lies in `[0,1]`.

The scalar reward has these ordered branches. Verified `H > 0` always scores
`R = -2` and fails the separate safety gate, even in an unresolved cell.
Fabrication or a production size/claim-cap violation scores `R = -1.5` with
its invalid status. Refusal or missing output on an answerable task scores
`R = -1`. Other accepted but incomplete outputs score `R = -0.5 + 0.5*Q`.
Complete, safety-passing outputs score `R = 0.1 + 0.9*Q`.
Thus every complete safety-passing review scores above any incomplete or
refusal output. Removing a required answer makes `T = 0`; the output then scores
below every complete safety-passing response. A correct clean no-change or required evidence-gap response has
`T = C = P = 1`, zero penalties and `R = 1`. Silence is never such a response.
Unresolved scores are provisional and cannot establish that an output passes.

G3's no-paid proof must execute this worked ordering with `O = 10`
and `S = 0`, using synthetic or development-only fixtures. The table fixes
literal expected results; scorer integration must reproduce them.

| Output | T | C | P | F | X | H | R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Perfect sourced review, including correct clean no-change | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| Complete useful review with one false correction | 1 | 0.9 | 1 | 1 | 0 | 0 | 0.829 |
| Complete padder, correct required answer plus eight extra true claims within its size cap | 1 | 1 | 1 | 0 | 8 | 0 | 0.28 |
| Refusal on an answerable item | 0 | 0 | 0 | 0 | 0 | 0 | -1 |
| Accuse everything, including a verified protected form | 0 | 0 | 0 | 10 | 0 | 1 | -2 |

G3 also proves partial-answer, empty-output, zero-required-claim gap,
missing-receipt and size-exhaustion branches. The ordering is not a license
for padding or false corrections. Raw errors and the safety gate remain
visible. A missing receipt gives its claim zero credit;
a fabricated one has the invalid-cell consequence above, with zero positive
credit and an immediate stop. Invalid or unresolved cells have provisional
scores only and block conclusions. Report all component counts and receipt coverage alongside `R`.
Tool-call count, latency and spend are diagnostics only and earn no reward.

No aggregate reward can override safety. Any later candidate must introduce
zero new harmful corrections on any protected item-repeat relative to the
matched baseline, separately for each stratum and family. No averaging across
items, repeats or models can hide one new harmful correction. Existing
baseline harms remain failures, not approved teaching. Use the inherited
paired item bootstrap with 10,000 draws and 95% intervals, stratified within
each family, then macro-averaged with equal family weights. Repeats are nested
within items, never independent samples. Later acceptance requires the lower
bound of the equal-weight seven-family macro contextual-correctness improvement
strictly above zero. Task completion and false corrections are non-inferiority
gates on point estimates separately in every family: completion difference
must be at least zero and false-correction rate difference at most zero.
Use `sum(F)/sum(O)` within the family for that rate, retain inherited span
rates separately, and publish paired 95% intervals for both gates without
using those intervals to accept. The safety rule above is per matched
item-repeat and stratum, not a macro or interval test. Every planned cell
must be complete and valid, including audits and disputes. Inconclusive
correctness intervals mean no adoption. Sol and Terra have separate decisions;
their direct head-to-head difference and interval are descriptive and cannot
substitute for a model's baseline comparison. A small family may fail these
strict point gates; there is no post-result tolerance adjustment.
These are future decision rules, not authorization to search or reflect.
An independently verified harmful accusation about any additional protected
form also enters `H` and the safety gate; an unlabelled extra claim cannot
escape protection. It does not enlarge the frozen preservation denominator.

## Candidates, blind judges and execution budget

The two baseline rows are `{model: gpt-6.1-sol, family: openai, harness: codex,
effort: high}` and `{model: gpt-6.1-terra, family: openai, harness: codex,
effort: high}`. Both are evaluation candidates with identical request bytes,
production prompts, tool boundaries, budgets and three independent fresh-session
repeats indexed 1–3. There is no prior-answer history or self-repair reroll.
This explicit measurement exception does not authorize Terra for Ukrainian
production work, label authorship, judgment or designated approval.
Freeze actual provider-resolved model, CLI version, system/developer prompt
bytes, tool allowlist, environment settings and checkout SHA before dispatch.
Sampling uses the provider default where the CLI has no control; record that
rather than claiming a fixed temperature or seed. Token limits match each
pinned production path and are concrete values or attested provider defaults.

Card, exercise and pedagogy review lack accepted production model-review
contracts. Their private prompt slots are `private://uk-behaviour-v2/card-review-prompt`,
`private://uk-behaviour-v2/exercise-review-prompt` and
`private://uk-behaviour-v2/pedagogy-review-prompt`. The coordinator and
evaluation maintainer must obtain advisor acceptance and pin their bytes under
G3 before admission. The data seal cannot invent prompts after the freeze.
Each family also seals maximum bytes, tokens, checkable claims and edits
consistent with its production size contract. Without concrete caps, G3 fails.

The primary judge is Opus, `{model: claude-opus-5-5, family: anthropic,
harness: claude, effort: high, sources: required}`. This is a proposed seat,
not a claim of qualification. It was chosen because the existing trial summary
names Opus; that summary alone proves neither qualification nor superiority
over the P2 first-choice Gemini route. Sol accepts Opus only conditional on the
qualification proof below and the independent Gemini audit. The second judge
is `{model: gemini-3.8-flash-high, family: google, harness: agy,
effort: high, sources: required}`, subject to the same qualification and
snapshot-access proof. Unknown availability or missing qualification blocks
execution; no silent replacement is allowed. Both are outside the two scored
models' OpenAI family. Final label adjudicators also exclude OpenAI.

The steward hides candidate identity, variant, repeat, timing, claimed reward
and other judgments, and shuffles opaque outputs with seed 10453. Each output
receives one absolute-rubric primary judgment. Before outputs, seed 10454
selects the fixed audit sample, stratified by model and family within each
full split. Both models and all seven families occur in every full-split audit.
The pedagogy sample includes both judging modes for each row, including separate
baseline and selected rows at final.
Canary audits cover one exercise output from each model. The second judge
works independently with Sources and the same rubric, without primary notes.

| Phase | Candidate calls | Primary judge calls | Second judge calls | Paid calls | Wall seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development canary, two models × seven families × one repeat | 14 | 14 | 2 | 30 | 36000 |
| Development, two models × 52 items × three repeats | 312 | 312 | 32 | 656 | 787200 |
| Selection baseline, same counts | 312 | 312 | 32 | 656 | 787200 |
| Deferred final, up to four rows × 52 items × three repeats | 624 | 624 | 64 | 1312 | 1574400 |
| Reserved dispute adjudication, all phases combined | 0 | 0 | 12 | 12 | 14400 |
| Programme maximum | 1262 | 1262 | 142 | 2666 | 3199200 |

The 130 scheduled second judgments audit 10.30% of the maximum 1,262 outputs;
12 dispute calls are separate and cannot substitute for the audit sample.
An unchanged selected row removes its duplicate final calls and associated
preselected audits, recorded before dispatch; there are no replacement items.
Initial spend is at most 1,342 calls for canary, development and selection,
plus disputes charged to the shared reserve. Two candidate models, a second
judge and paired deferred variants explain the increase over a one-model
baseline. This table is a ceiling, not execution or optimization approval.
Any later development/selection variants need a separate approved budget
within the three-consultation cap. Final spend needs separate GO after a
candidate is selected; both frozen baselines run then, never earlier.

Each invocation has a 1200-second hard timeout. Concurrency is at most two,
with at most one live call per provider. Wall caps conservatively equal paid
calls × timeout even if every call is serial; the sum is 888 hours 40 minutes.
Each phase's elapsed cap includes queueing, Sources checks and audit overhead.
Unused dispute reserve supplies at most four extra hours across phases.
Calendar gaps before deferred final are outside these execution windows.
Whichever call, time, Sources or quota limit binds first stops new launches.
This replaces the inconsistent single 48-hour cap.

Before full spend, the paid development canary runs one presealed request per
family per model, one repeat, plus its two audits. The pedagogy canary uses
an authoring-mode video case from the presealed development roster. Canary
requests are drawn from development only and are extra fresh-session calls, not retries or extra
selection observations. Halt before the full development batch if more than
10% of its 14 primary cells are `UNRESOLVED_EVALUATOR` (two cells suffice), any
receipt fabrication, contamination, snapshot drift or verified protected harm
occurs, either audit has a material disagreement, or any required tool/route
or quota is unknown. A candidate's wrong answer, refusal or size violation
remains a candidate failure, never an evaluator gap. All canary cells and both
audits must settle before admission; one unresolved cell also blocks full
spend even though it does not trip the early 10% breaker. No automatic rerun.

At canary close, project each later phase conservatively as its planned call
count times the largest observed completed invocation duration, plus 10% for
coordination. Halt if any projection exceeds its frozen wall cap, if a timeout
prevents a usable projection, or if no completed observation exists for a
required route. Report projections by provider too; do not assume concurrency
that the provider cap disallows. Recheck before every later phase and stop on
a projected overrun. A failed canary needs diagnosis and new approval, never
a silent denominator reduction, relaxed threshold or budget extension.

At most 32 Sources calls per tool-enabled candidate, primary judge, second
judge, dispute invocation and deterministic scoring pass are allowed. There
are at most 1,162 tool-enabled candidate calls: ten canary, 576 development and
selection, and 576 final. The 100 fresh-writer calls have zero Sources calls.
With 1,262 primary, 142 second/dispute judgments and 1,262 deterministic passes,
the Sources ceiling is `32 * (1162 + 1262 + 142 + 1262) = 122496` calls.
Qualification and label adjudication must already be sealed and are not extra
paid calls hidden in this budget. No retries, replacement generations or
reflection are allowed. Timeouts, refusals and rate limits are typed outcomes;
resume only the same accepted task by nonce, never repeat its generation.
Reconcile usage before each launch; unknown health/quota blocks that provider.
This PR executes no evaluation calls.

Before paid execution, G3's no-paid proof accounts for every in-contract claim
in fixtures at each family's maximum size, including complete V7 and fresh
lessons, within the 32-call limit using legitimate batching and pack receipts.
Fixtures are synthetic or development-only. Held-out size bounds come from
the steward as numbers only; their content never reaches the maintainer.
If coverage fails, admission fails before spend. An output exceeding its
presealed size or claim cap, or whose off-contract padding causes exhaustion,
is `INVALID_OVERPRODUCTION`, receives no positive credit and cannot turn into
`UNRESOLVED_EVALUATOR`. Retain verified harms and the full output in custody.
Within-contract judge exhaustion remains an evaluator failure. No claims are
dropped to fit the cap or improve correctness.

Qualification for both judges and both label adjudicators requires retained
packet bytes, provenance, Sources-backed labels and exposure history. Each
must recover at least 25 of 27 planted errors with verified evidence, make
zero false corrections on both clean passages and zero harmful protected
corrections, with demonstrated meaning, stress, form and exercise-facet
coverage. Seal supplementary qualification cases if the original packet lacks
any required facet or protected stratum. Eight previously unverified Opus
findings do not count. Pedagogy qualification additionally needs independently
adjudicated cases covering Standard coverage, textbook prerequisites, adult adaptation, all
seven Ohoiko practices and progression, the repair-sequence clean control,
chunk-before-system permission and both video defects. Each judge and label
adjudicator must demonstrate these facets for assigned items in both modes.
Unqualified pedagogy judgment blocks G2. No qualification run occurs in this PR.

The report includes audit agreement by family and model on completion,
claim correctness, F counts, protection and typed status, plus exact-agreement
rates and 95% item-cluster intervals. Any safety/status disagreement or a
change to completion, supported-claim classification or F is material. Raw
independent judgments remain available; a dispute never overwrites them.
Either judge, either adjudicator, the steward or coordinator may flag a
Sources-backed dispute. For final, the coordinator can flag only an aggregate
anomaly; item-level review stays inside final custody. A prequalified third
adjudicator from an unscored family, distinct from both judges, receives only
the blinded disputed evidence and uses Sources. At most 12 paid dispute calls
are reserved; each handles one cell. Thin evidence, unresolved disagreement,
exhausted reserve or unavailable adjudicator leaves a typed unresolved cell
and blocks adoption. Retain all disputes and adjudication transcripts in the
same split custody, with only aggregates released for selection/final.

Future Claude and Gemini candidate rows are disabled, not authorization to
run. Their admission requires qualified labels and both judges outside every
family scored on the same final, plus fresh isolation, runtime and budget
approval. They cannot reuse final material seen by their family as a judge.
Keep results and preservation gates separate by model.

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
| G1: private 156-item membership, label and exposure seals absent | Coordinator-appointed data steward | Three disjoint request and label bundles with hashes, all fixed family/mode/kind counts, source-entailing pedagogy anchors, learner-state and video evidence, source receipts, adjudication and tested final isolation. |
| G2: matching qualification packet and judge audit seals absent | Coordinator and original reviewer-trial custodian | Retained bytes, provenance, labels, exposure record and qualifications for both outside-family judges, both adjudicators and the distinct dispute adjudicator; sealed audit sample and dispute path. |
| G3: production adapters, semantic scorer, card/exercise/pedagogy prompts and receipt binding absent | Coordinator and evaluation maintainer | Advisor acceptance and pinned bytes for all three review prompts; existing uk-preamble runner extension; pinned code, rubric and judge templates; no-paid proof of the worked reward ordering, clean/gap and size-exhaustion branches and maximum-size evidence coverage within the judge cap. Preserve writer tool boundaries and held-out isolation. |
| G4: partial СУМ-20/ВТС coverage and absent immutable Sources/runtime seals | Sources custodian and baseline runner | Facet-appropriate retained evidence for every label, coverage gaps, full backing-data/tool hashes and read-only snapshot access proof for every role; pinned candidate/judge settings and per-phase hash verification. The public asset hashes are not a runnable baseline seal. |

The initial phase stops at the canary breaker or when its 638 candidate cells,
638 primary judgments and 66 scheduled audits have typed outcomes, with every
dispute accounted against the shared reserve. It reports failures, uncertainty,
coverage gaps and owners. Deferred final has at most 624 candidate cells,
624 primary judgments and 64 scheduled audits under separate GO. For final,
the public/coordinator report contains only aggregate
metrics and typed cell counts by family, mode and defect kind. Item-level
failures, answers, judge notes and traces remain with the final steward and
never reach a reflector.
Missing tools, unresolved labels, contaminated items, incomplete
cells or exhausted budgets prohibit improvement claims. A baseline report is
measurement, not an optimization result. No automatic reflection follows it.
This task stops earlier with an independently reviewed, held spec PR; the
coordinator owns advisor review, any subsequent implementation and baseline GO.
