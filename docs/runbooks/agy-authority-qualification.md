# AGY authority qualification

Protocol version: **1.0**. Scope: #9619, devops stream #5703; role-migration
dependency: #9302. This implements the independently approved qualification
protocol; it does not change production eligibility, models, defaults, catalog
entries, or designated-approval policy.

The release operator can prepare an immutable evaluation now. Candidate
qualification waits for an actual provider-listed identity and all four AGY
prerequisites below. Passing a benchmark supplies capability-specific evidence;
it does not authorize admission. Issue #9619 closes only after all its readiness
criteria are verified. Actual new-candidate qualification is a separately
tracked release-dependent residual owned by devops, not a readiness-closeout
requirement.

## Authority, responsibilities and completion terms

The approved proposal has SHA-256
`24ad066f08a451945f53a087789cfbb9d659083f210877357b5ab4dc053817c0`;
its independent approval receipt has SHA-256
`952a6efe22145c0ee61b25c8c3fdb87b13e91517a4311a48e2f78f8d0f91325a`
and disposition `APPROVAL: APPROVE`. Retain those receipts privately. They
approve this protocol, not a candidate or a production policy change.

| Responsibility | Accountable participant |
| --- | --- |
| Scope, frozen packet, resources, sequencing, qualification decision and residuals | Devops driver of record; codex-devops owns this implementation's review and landing |
| Case preparation and evidence-backed gold | Curator, with qualified independent source verification; no candidate access to gold |
| Blind scoring and novel-finding adjudication | Independent non-candidate judges, domain-qualified and outside the candidate's family; language judges use Sources |
| Exact-head runbook and later implementation review | Qualified outside-author-family reviewer of record; authorship checks are not CF |
| Role migration and prerequisite implementation | Infra owner of #9302; devops owns qualification prerequisites and coordinates their fixes |
| Policy clearance and concrete admission | Operator or current designated authorities within their permitted decision boundary; candidate never votes on its own admission |

Use the current
[operator contract](../../agents_extensions/shared/rules/operator-expectations.md)
and [model assignment](../../agents_extensions/shared/rules/model-assignment.md)
for the designated participants and independence rules. Do not replace a
dissenting authority by shopping for another pair or accept self-approval.

Keep these outcomes separate:

1. **Preparation:** cases, gold, splits, scoring and commands are frozen.
2. **Readiness:** exact candidate/runtime prerequisites and dispatch preflight
   have current positive and negative proof. Preparation alone is insufficient.
3. **Qualification:** two independent held-out passes meet every applicable
   numerical and hard gate for the named capability.
4. **Admission:** a separate explicit decision approves that concrete identity,
   route and capability, including operator-policy clearance where required.
5. **Delivery:** independently reviewed changes land with same-head green CI,
   representative real-route proof and required hygiene. Merge, deployment and
   certification are distinct. The worker only returns a pushed branch.

The denominator is **all protocol gates and requested capability tracks**,
including clean cases, failed cases, tools and isolation; provider-call success
is not the denominator. Use the existing
[task-quality contract](../best-practices/task-quality.md) and
[lifecycle evidence contract](../../agents_extensions/shared/contracts/task-lifecycle-closeout.md).
No qualification calls, credential changes or host changes are authorized by
this runbook's implementation.

## Current Gemini admissions (2026-10-08 approval)

The 2026-10-08 approval sets these Gemini roles. They are recorded here so the
qualification gate below is read against them; they do not qualify Gemini 4.

| Role | Admission |
| --- | --- |
| Epic driver | Admitted. `start-gemini-driver.sh --epic <lane>` enters the shared driver path. The driver default is `gemini-3.1-pro-high`; `gemini-3.8-flash-high` is also certified. Every other Gemini model id is refused. |
| Low-risk and medium-risk code review | Admitted as formal review. The reviewer resolver and target admission still exclude Gemini from code and infra review; wiring this seat is a separate reviewed change. |
| Ukrainian review | Admitted as formal review when the reviewer uses the Sources MCP. |
| High-risk and critical code review | Not admitted. These stay with Opus 5.5 or Sol 6.1 until Gemini 4 passes this protocol's code/infra high and critical gates. |
| Design input and designated approval | Not admitted. Designated approval stays with Opus 5.5 and Sol 6.1. |

## Current source evidence and unresolved prerequisites

Source inspection baseline: `bfe799371645705497ac2f58789b9c5e1ad2b1ab`.
Read-only CLI observation: 2026-10-06 UTC. Recheck these facts at execution;
they are not a provider forecast or lasting health attestation.

| Source or command | Observed behavior and evidential limit |
| --- | --- |
| `agy --help` | Lists `--model`, `--effort` (`low`, `medium`, `high`, `xhigh`, `max`), `--sandbox`, stream-JSON input/output, `--log-file` and `--disable-slash-commands`. A flag's existence does not prove adapter wiring or effective enforcement. |
| `agy models` | Lists Gemini 3.8 Flash, 3.7 Flash, 3.6 Flash and 3.1 Pro variants, plus non-Gemini models. No Gemini 4 identity was listed. Listing proves availability only, not permission, tool access or authority suitability. |
| [AGY adapter](../../scripts/agent_runtime/adapters/agy.py), `build_invocation` and `_resolve_model_flag` | Emits a resolved `--model` slug and rejects unknown explicit models. Effort remains a no-op with the `not yet wired through CLI` diagnostic. `entire_fleet.actual_model` is constructed from configured/resolved values before launch; it is not observed backend identity. Historical docstrings about display-label-only invocation are not current argv evidence. |
| Same adapter, native `review_isolation` branch | Raises `agy_isolated_review_unsupported` without `review_attempt_boundary`. Existing content attempts with that boundary are a distinct route; their success cannot establish native formal code/infra isolation. |
| [AGY permission runbook](agy-review-permissions.md), [attempt isolation runbook](formal-review-attempt-isolation.md), [review MCP provisioner](../../scripts/agent_runtime/review_mcp.py) and [receipt ledger](../../scripts/review/receipts/ledger.py) | Source implements scoped Sources exposure, exact tool grants and attempt boundaries for content review. Configuration, unit tests and fixture success do not prove all required tools work for a new candidate/runtime. |
| [Formal AGY isolation runbook](agy-formal-cf-isolation.md), [catalog](../../scripts/config/model_catalog.yaml), [catalog validation](../../scripts/review/model_catalog.py), [resolver](../../scripts/review/reviewer_resolver.py) and [target admission](../../scripts/agent_runtime/target_admission.py) | AGY formal eligibility is false; Gemini/AGY code/infra review is excluded, including explicit pins and injected ladders. The 2026-10-08 approval of low-risk and medium-risk code review is not yet wired into these gates. Qualification cannot override these production gates. |
| [Historical benchmark](../../scripts/audit/code_review_benchmark.py), case fields, `score_case` and `aggregate` | Prior art for case/gold structure and TP/FP/FN accounting only. Its historical model/transport matrix, heuristic matching and lack of blind adjudication do not implement this qualification protocol. Do not execute that matrix. |

Four prerequisite proof rows must be complete **before any AGY qualification
run**, including calibration through AGY. Missing evidence is `unknown` and a
blocker. Do not discover prerequisites by spending the held-out benchmark.

| Prerequisite | Falsifiable proof required on the actual route | Refusal or negative control |
| --- | --- | --- |
| Sources exposure | Effective scoped server/tool catalog; actual candidate calls returning independently checked results for every needed facet; invocation-bound successful ledger receipts and server/config digests | Remove a required tool or its exact permission in an expendable fixture: the invocation must refuse or produce a typed missing-evidence failure; no invented correction or alternate provider |
| Native review isolation | Demonstrate suppression of project instructions, ambient MCP, hooks and nested reviewers; read-only pinned inputs, fresh session/home, protected gold and other attempts; actual launch and denial output from the same runtime | Plant distinct public fixture sentinels in each forbidden surface and retain outside-boundary positive controls. Attempts to read, write, execute hooks or invoke a nested reviewer must be denied; inability to start a CLI is not proof of denial |
| Actual runtime identity | Invocation-owned provider/runtime identity event naming the concrete model, bound to the exact prompt, input and result; independently verify against the listing and frozen requested/configured identities | Missing event, ambiguity, alias-only identity, mismatch or mixed identities refuses. Model prose, a tool response, `--model` argv and configured `actual_model` are insufficient |
| Enforced actual effort | Adapter argv/config demonstrates requested effort reaching the CLI; provider/runtime-owned evidence demonstrates the actual effective effort on that invocation | Change the effort in a controlled probe and verify the attested change; unsupported or contradictory values refuse before work. A high-suffixed model, CLI help, TUI default or request metadata alone is insufficient |

Devops owns unresolved candidate availability, full prerequisite evidence and
actual qualification. Infra owns #9302 role migration. The installed CLI has an
effort flag but the inspected adapter does not wire it; actual identity proof
has not been established here. Content-review tooling is not a substitute for
the missing native authority-review proof. The 2026-10-08 approval lifts the
driver exclusion and admits low-risk and medium-risk code review. The design
input, designated approval, and high-risk and critical code/infra exclusions
remain binding until Gemini 4 qualifies here, the necessary explicit policy
clearance is given, and the implementation is reviewed. No fallback, guessed model ID, release
date, synthetic pass or prototype capability proof closes these gaps.

## 1. Prepare and freeze the packet

Work in the assigned dispatch checkout. Set `PROJECT_PYTHON` to the
task-prescribed shared interpreter; do not create a worktree virtualenv or
change `PYTHONPATH` to make a probe pass. Set `QUALIFICATION_ROOT` to an approved
ignored/private evidence directory, with access-controlled gold and holdouts.
Use the existing receipt stores and task lifecycle; do not introduce a new
orchestrator, engine or message bus. Public fixture cases may be versioned;
generated qualification reports and traces must not be staged.

Record the source commit and UTC timestamp, inspect supported command shapes,
and hash the exact frozen files. These are preparation commands, not model calls:

```bash
date -u
git rev-parse HEAD
git status --porcelain
agy --help
agy models
"$PROJECT_PYTHON" scripts/delegate.py dispatch --help
"$PROJECT_PYTHON" scripts/delegate.py wait --help
sha256sum "$QUALIFICATION_ROOT/cases.json" \
  "$QUALIFICATION_ROOT/gold.json" "$QUALIFICATION_ROOT/splits.json" \
  "$QUALIFICATION_ROOT/prompt.txt" "$QUALIFICATION_ROOT/scoring.md" \
  "$QUALIFICATION_ROOT/freeze.json"
```

The filenames above are operator-prepared packet files, not outputs of an
existing qualification CLI. Hash any additional prompts, context inputs,
source-receipt bundles and parser files individually, and hash the ordered
manifest of their names and hashes. Keep gold separate from candidate-readable
inputs. Do not include a ledger's own hash inside its hashed bytes; retain its
digest in the approval receipt. A working-tree mismatch invalidates the freeze.

Before execution, the driver obtains independent domain-fit and adversarial
scope/circularity review of the exact frozen packet, binds verdicts to its
digest, and reconciles material findings. This implements the approved
pre-dispatch review requirement; it is not admission or implementation CF.

### Freeze ledger fields

Use a private record labelled `agy-authority-qualification.v1`. Its minimum
fields below are evidence requirements, not a new production catalog schema.
Before provider availability, identity/runtime fields remain explicitly unknown
and the packet is preparation-only. Complete and refreeze them before calls.

| Field group | Required values |
| --- | --- |
| Identity and scope | Protocol version, #9619/#5703/#9302, qualification/run IDs, UTC timestamp, source/reviewed SHA, driver, outcome, requested capabilities and risk coverage, denominator, non-goals |
| Authority | Proposal/approval digests, author/reviewer concrete model, family and harness, frozen-packet review receipts, policy-clearance references or explicit unresolved state; no candidate self-approval |
| Candidate and incumbents | Exact provider-listed concrete IDs, listing time/digest, configured/requested IDs separately from observed runtime IDs; family, route, harness, CLI/build digest, current catalog digest and calibration-holder decision references |
| Runtime and tools | Prompt/template/input hashes; tokenizer identity/version or attested provider binding; parser/scorer digest; requested and actual effort; tool catalog/server/config hashes, isolation profile/probe receipts, invocation preconditions and compatibility proof |
| Corpus and gold | Stable opaque case/finding IDs, track, severity/facet, defective/clean status, pinned input/source revision, evidence locator/digest and independent verifier; seeded/post-cutoff provenance, cutoff evidence or seeded substitution, exposure history |
| Splits and blinding | Disjoint calibration/pass-1/pass-2 membership, selection/order seed and digest, per-pass counts/coverage, sealed-gold commitments, judge identities and access boundary; case classification/model identity withheld from blind outputs |
| Scoring and resources | Matching/deduplication rules, thresholds/hard gates, uncertainty method, novel-findings procedure, timeouts, finite call/token/time budget, resource/health preflight receipts, two-round stop/residual policy |
| Per invocation and disposition | Case/pass/task/attempt IDs, exact argv and configuration receipt, own-session identity binding, input/prompt/result/tool-receipt digests, actual identity/effort events, terminal outcome including missing/cancelled/timeout, blinded judgment and adjudication digest, aggregate decision, residual owner and unblock condition |

Provider-managed tokenizer/runtime details may lack local visibility. Record
that limitation and the provider binding; do not invent a version or claim
unobserved invariance. If exact-artifact binding cannot be established, remain
blocked. Material changes to model, prompt, tokenizer, parser, runtime or tools
invalidate prior proof: refreeze, recalibrate and repeat independent heldouts;
never relabel predecessor evidence for a successor.

## 2. Construct independent gold and heldouts

Use mostly seeded or demonstrably post-cutoff cases. If reliable cutoff
evidence is unavailable, use seeded cases. A historical PR's familiarity is
not proof of generalization. Retire exposed cases from subsequent qualification
attempts; keep an exposure ledger and do not quietly rename or reshuffle them.

Gold requires an independently reproducible later fix/revert, CI failure,
seeded defect, or authority-verified language error. An incumbent review,
agreement between models or the candidate's output alone is never gold.
For fixes/reverts record before/after commits and the behavior proof; for CI
retain the reproducible failure plus passing control, not merely a red badge.
For seeds retain the mutation, reproducer and clean original. Adequate/clean
controls receive the same independent inspection and provenance checks.

Each gold finding has a stable ID, location/context, severity, facet/category,
expected observable failure, acceptable equivalent descriptions, critical or
blocker designation, and source/reproduction receipts. Predefine critical
sets before candidates see inputs. Remove ambiguous gold before freezing;
withhold unsupported language claims rather than manufacture certainty.

Prepare a separate calibration split and two sealed held-out splits. For this
procedure each independent pass has its own disjoint cases and the full floor
below; no calibration case or feedback enters either pass. Thus the minimum
held-out total across both passes is 80 code cases, 80 language cases with
96 gold findings, and 24 design briefs with 48 gold blockers, plus separate
calibration material. Larger corpora preserve the minimum defective and clean
counts in **each** pass. Do not combine passes to meet a floor or average away
a failed pass.

| Track | Minimum in each held-out pass | Required coverage |
| --- | --- | --- |
| Code/infra review | 40 cases: 24 defective, 16 clean | Security/admission, concurrency, routing and semantic regressions; high-risk coverage for high admission, critical cases and findings for critical admission |
| Ukrainian review | 40 cases: 24 defective, 16 clean; 48 gold findings | Morphology, spelling, stress, meaning, Russianisms/calques, heritage and pedagogical/CEFR judgments; every predefined blocker |
| Design critique | 12 briefs: 8 defective, 4 adequate; 24 gold blockers | Trust boundaries, missing outcome/denominator, circular evaluation, dependencies, acceptance/stop/residual gaps; designated critical trust-boundary defects |

### Verify language gold and negative controls

Follow [Sources authority rules](../../agents_extensions/shared/rules/mcp-sources-and-dictionaries.md)
and [linguistic rules](../../agents_extensions/shared/rules/ukrainian-linguistics.md).
Retain facet-specific receipts and source locators, not model-written gold:

- Verify forms and morphology with VESUM via `verify_words`; use ULIF paradigms
  where required. VESUM does not establish stress, meaning or cultural facts.
- Check stress with `verify_stress` and the appropriate modern headword/paradigm
  authority; disambiguate the intended meaning and grammatical context.
- Check spelling with `query_pravopys`; meaning with `query_sum20` and applicable
  contemporary authorities. Use heritage evidence in its attestation role.
- For every Russianism check use both `search_style_guide` and `search_text`
  with `source_file='antonenko-davydovych-yak-my-hovorymo'`, plus `query_r2u`
  where relevant. Check `search_heritage` before rejecting a form;
  `check_russian_shadow` alone is suspicion, not a verdict. Distinguish calques,
  surzhyk and paronyms; do not condemn proper nouns or borrowings by resemblance.
- Include required `query_cefr_level`, `verify_words` and `check_russian_shadow`
  calls for language-review evidence. Verify actual required tool availability;
  a tool available to the curator may be absent from the scoped review catalog.
  A missing needed facet tool blocks readiness; do not widen grants ad hoc.
- Include authentic heritage forms, justified uncertainty/withholding and A1
  English support as clean negative controls. Apply `IMMERSION_POLICIES` and
  `compute_immersion_band()` in [config](../../scripts/config.py); do not turn
  intended A1 scaffolding into an error. Unsupported modern meaning stays
  unresolved. СУМ-11 is occupation-context evidence, never modern normative gold.

Keep classification, source gold, expected corrections and severity keys out
of candidate inputs. Supply enough authentic context to judge the case, with
the same permitted evidence access for both passes. Gold validators and blind
judges must be distinct from candidate authorship and approval.

## 3. Establish runtime readiness, then calibrate

The driver records current task/infra, disk, capacity, health and quota evidence
using the existing preflight. Unknown telemetry remains unknown, never green.
Use the installed quota probe where available; public receipts contain only
aggregate percentages and UTC times. Freeze budgets and explicit hard/silence
timeouts before any paid run. No new telemetry service or lease operation is
part of this protocol.

Repeat `agy --help` and `agy models` and inspect the actual adapter invocation,
not its older comments. Select only a concrete listed identity allowed by the
current catalog, route and policy. Availability is not permission. Unavailable
or unadmitted candidates remain a dependency; do not force admission or bypass
the catalog to run the experiment.

Run the four-row prerequisite matrix with public, expendable fixtures, keeping
literal command, exit status, semantic output and private evidence digests.
The following existing **offline** probes verify the current refusal and model
selection mechanisms; passing them does not qualify a candidate:

```bash
"$PROJECT_PYTHON" -m pytest \
  tests/test_review_isolation.py::test_agy_isolated_review_is_explicitly_unsupported \
  tests/test_review_isolation.py::test_f12_agy_requires_active_enforcement_not_assertion \
  tests/agent_runtime/adapters/test_agy_adapter.py::test_build_invocation_maps_model_slug \
  tests/agent_runtime/adapters/test_agy_adapter.py::test_build_invocation_unknown_explicit_model_is_rejected -q
```

For actual scoped Sources calls and attempt-boundary positive/negative probes,
use the driver canary procedure in [AGY permissions](agy-review-permissions.md)
and the verification/proof procedures in
[attempt isolation](formal-review-attempt-isolation.md). Those live commands
make provider calls: execute only in the separately authorized readiness run.
Record exact commands and outputs for the tested route. A full-mode content
fixture cannot discharge native formal code-review isolation; a permission
canary's fixed token cannot prove semantic review competence. The linked driver
canary hardcodes `gemini-3.8-flash-high` and its forced-reader probe calls
`verify_words` on one word; it supports only that limited probe. Release
prerequisite proof requires the actual candidate and every required Sources
facet, with independently verified invocation-bound receipts. Current identity
and effort gaps require reviewed implementation and real attestation proof;
there is no existing command in this runbook that claims to fill them.

After prerequisites pass, run **both current incumbent authority holders** on
the separate calibration split, using their admitted transports and frozen
prompts/scoring. Identify holders from the current approved catalog/rules;
do not copy a historical benchmark matrix. Apply the track thresholds and
hard gates below to each incumbent separately. A calibration failure stops
candidate execution while independent judges investigate cases, gold, scoring
or protocol. Never lower thresholds, select only easier cases or promote
incumbent findings into gold to make calibration pass. Refreeze and re-review
material repairs before continuing.

## 4. Run two bounded independent held-out passes

After readiness and calibration, the driver follows the frozen per-case
invocation commands through the existing admitted runtime/attempt boundary.
There is no `qualify-agy` CLI. Do not use a plain `agy --print` call to bypass
scoped receipts, runtime admission or isolation. Current code/infra and design
exclusions block those runs until separately cleared and implemented.

For content fixtures, the existing API sequence is
`prepare_review_attempt(review_id, attempt_id, manifest_path, "agy", ...)`,
then `scripts.agent_runtime.runner.invoke("agy", prompt, mode="read-only",
model=concrete_id, effort=frozen_effort, session_id=None, tool_config=...)`.
Carry the prepared adapter options and exact manifest/input-root binding,
own initiator identity and finite `hard_timeout`/`stall_timeout` into `invoke`;
use the complete canary recipe linked above rather than inventing tool-config
keys. A curriculum manifest is not a generic code/design qualification input.
Freeze and independently verify the supported invocation for each requested
capability before execution; a missing supported path remains blocked.

Where an admitted task dispatch is used, inspect `dispatch --help` as above,
set explicit model/effort/timeouts and bind the permitted review inputs. Arm
`"$PROJECT_PYTHON" scripts/delegate.py wait "$TASK_ID"` immediately after
dispatch. Do not poll or spawn a substitute on failure. No paid dispatch is
authorized by the preparation or offline probe commands here.

For each pass:

1. Verify every frozen digest, input pin, listing, prerequisite receipt and
   preflight before launch. Start a fresh non-resumed attempt for each case,
   with no other case output, previous verdict, gold or calibration feedback.
2. Give the candidate only the case inputs and frozen prompt. Retain original
   result bytes and terminal evidence, including identity, effort and Sources
   receipts. Do not repair an answer, extract a favorable fragment or substitute
   a response from another invocation.
3. Blind judges to candidate identity and pass outcome. Present opaque case and
   finding IDs with the evidence necessary to assess correctness. Hide model,
   harness and provider-identifying metadata until judgments are sealed.
4. Complete scoring and independently adjudicate unmatched findings using the
   rules below. Keep pass-1 results and feedback away from pass 2. Seal both
   pass judgments before unblinding identities and deciding qualification.
5. Publish safe per-pass aggregates with the complete frozen denominator and
   failure counts. A stop leaves unrun cases recorded as not executed; it
   cannot become a passing incomplete denominator. Retire exposed cases.

## 5. Score and decide per capability

Match findings by independently verified behavior, source facet and location,
using the frozen equivalence rules. One gold finding earns at most one true
positive; repeated paraphrases do not increase recall. Seal deduplication and
severity rules before calls. Review unmatched findings blind: a valid novel
finding is not automatically a false positive. Require independent reproduction
or facet-appropriate authority proof, record the adjudication, amend the gold
version visibly and rescore all affected outputs consistently, including
calibration if applicable. Do not let the candidate adjudicate its own finding.
If new gold reveals an unsafe clean control or ambiguous protocol, stop and
refreeze; do not silently change the clean denominator mid-run.

For each track in **each pass**, report raw TP, FP and FN, with
`precision = TP / (TP + FP)` and `recall = TP / (TP + FN)`. Design recall uses
gold blockers. Zero denominators cannot pass. Use unrounded ratios for gates;
display rounding is not threshold clearance. Report case-level defective/clean
counts, coverage, critical/blocker matches, clean false positives, source
violations, missing/cancelled/timeout counts and justified uncertainty.
Report sampling uncertainty alongside point estimates using the frozen method,
and acknowledge case-cluster dependence and the small floors; do not claim
precise population performance or invent a confidence-bound admission bar.

| Capability evidence | Gate in each of two independent passes | Hard failure regardless of aggregate |
| --- | --- | --- |
| Code/infra high review | Precision ≥90%; recall ≥85%; required high-risk coverage | Any critical finding missed; any critical false positive on a clean case |
| Code/infra critical review | Same numerical gates, with critical-case coverage | Any critical finding missed; any critical false positive on a clean case |
| Ukrainian review | Precision ≥95%; recall ≥90%; at least 48 gold findings per pass | Any predefined blocker missed; any fabricated or unsupported citation, or unsupported normative correction |
| Design input / designated approval | Precision ≥90%; blocker recall ≥90%; at least 24 gold blockers per pass | Any designated critical trust-boundary defect missed |

Missing output, cancellation and timeout **fail the affected case**, including
a clean case; do not drop them as missing data. Unreturned defective gold
counts as FN. Numerical scores alone cannot hide terminal case failures.
An incomplete pass cannot qualify. Every relied-on language correction or
approval-critical clean claim needs an actual facet-appropriate Sources receipt;
a plausible citation label without supporting output fails the source gate.
Justified uncertainty is correct on the predefined uncertainty controls; an
abstention on a resolvable gold defect is a miss, not a denominator reduction.

Passing language does not infer design or code competence. Passing design does
not infer code review or give an approval vote. Passing high-risk code coverage
does not infer critical eligibility. Record a separate disposition and receipt
for every requested capability, bound to the concrete identity, runtime,
artifact and two pass results. Incumbents retain existing approved eligibility;
this protocol does not retrospectively requalify them.

For a **new family**, actual qualification is mandatory before capability
admission. A same-family holder rotation instead requires the concrete
operator-decision receipt, compatibility and representative transport proof,
unless the operator requires full qualification. Never reuse another model's
qualification as replacement evidence.

## 6. Stop, retain evidence and hand back

Stop immediately on identity mismatch, missing tool/isolation/effort proof,
privacy failure or a critical miss. Unknown proof remains a blocker; timeout,
cancellation, unavailable route or partial output never triggers another
provider call or a weaker route. Calibration failure also stops candidate work.
After two failed qualification rounds, require a changed candidate/runtime or
an independently approved protocol revision, with fresh unexposed holdouts.
After two review rounds on an artifact, the driver records what still blocks
and what is a non-blocking residual; thresholds and hard gates never weaken.

Retain raw prompts, outputs, runtime logs, source results, gold, judgments and
literal commands only in approved private/ignored evidence. Public receipts
contain opaque IDs, repo-relative links/commands, UTC times, model/family/harness,
reviewed SHA, digests, aggregate counts and typed disposition. Do not publish
host/account details, credentials, private source text or operator transcripts.
Redact diagnostics before sharing. Public evidence must link to the safe
receipt/digest, not a private host path; raw-trace availability is a privately
verifiable commitment, not an assertion that the trace may be made public.

The driver's handback includes each gate and capability/pass disposition,
counts against the frozen denominator, uncertainty and held-out judgment
receipt, exact reviewed artifact, admission/policy decision or explicit lack
of one, and every residual's owner and concrete unblock condition:

- **Devops:** separately tracked release-dependent actual qualification → wait
  for actual provider availability, all four AGY prerequisite proofs and
  required policy clearance; then separately authorize and execute qualification.
- **Infra, #9302:** generic role migration not delivered → complete its approved
  migration and equivalence evidence before #9619 readiness closeout and
  production role admission.
- **Devops driver of record:** protocol branch awaiting independent exact-head
  CF, same-head CI and landing → finish those gates and hygiene; no worker
  self-approval or PR/merge action.

Close #9619 only when all readiness criteria are verified: completed #9302
migration, full authority-reference inventory disposition, placeholder
test-catalog fixture proof through resolver, admission and approval discovery
without family-specific code changes or changes to existing production routing
and eligibility, an independently reviewed protocol, exact-head cross-family
approval, same-head green CI, merged behavior/fixture or artifact proof, and
common worktree/branch hygiene. Issue #9619 remains open because migration and
readiness proof are incomplete; actual new-candidate qualification remains the
separately tracked devops residual above.

Preparation, fixture tests, transport completion, synthetic catalog discovery,
CI success and this runbook's merge are not proof that a candidate is qualified
or admitted.
