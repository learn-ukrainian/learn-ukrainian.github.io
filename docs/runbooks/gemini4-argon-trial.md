# Gemini 4 Argon trial selectors

Issue #10568. This records model-name compatibility only. It does not qualify
Argon for critical review, security review, or advice, and it does not change
launcher certification.

## Listed selectors

`agy models` on 2026-10-14 UTC listed these Gemini selectors and no Gemini 3.1 Pro:

| Selector | CLI display label |
| --- | --- |
| `gemini-4-argon-high` | Gemini 4 Argon (High) |
| `gemini-4-argon-medium` | Gemini 4 Argon (Medium) |
| `gemini-4-argon-low` | Gemini 4 Argon (Low) |
| `gemini-3.8-flash-high` | Gemini 3.8 Flash (High) |
| `gemini-3.8-flash-medium` | Gemini 3.8 Flash (Medium) |
| `gemini-3.8-flash-low` | Gemini 3.8 Flash (Low) |

The adapter accepts each Argon slug and its display label and passes that same
slug to `agy --model`. Effort stays unwired. `gemini-4-argon` plus an effort
value is not a selector and is refused. Unknown names are refused before a
subprocess. A provider listing is availability only. It does not prove
advisor-level quality. Qualification remains DevOps #9619
(`docs/runbooks/agy-authority-qualification.md`).

## Provider identity

For Argon stream output, the adapter requires the provider's `init.model` or
top-level init `model` to equal the selected concrete slug. Low and medium
remain distinct from high despite the catalog's existing aliases. A display
label is accepted as a request but is insufficient as runtime attestation.
Conflicting or unrecognized identities produce `agy_model_event_mismatch`.
A successful response without identity produces `agy_model_identity_missing`.
Both refuse with `provider_policy_refusal` and return no accepted response.
Provider errors retain their existing classification. Flash behavior stays
unchanged. Fixture tests exercise this contract without a provider call.

## Advanced routing remains blocked

The ordered #10568 defaults are Argon high for B1+ Ukrainian and Ukrainian-data
authoring, with Sol fallback. A1 and A2 authors retain Sol and Flash. Argon joins
their planning when that work starts. Gemini-authored Ukrainian output requires
independent Sol or Opus review with Sources. Argon has no formal code-review,
security, critical-review, or advisor qualification.

This preparation does not implement those defaults. `execution_routing` has
only `sol_advised_bounded`. `scripts/review/model_catalog.py` validates its fixed
envelope fields. `scripts/delegate.py::_admit_dispatch_target` admits the supplied
agent and model but has no CEFR-based author selection. The current catalog has
no advanced Ukrainian-author role. Adding unused fields or a separate selector
would not prove a production default. The advanced route stops pending a
supported consumer contract owned by codex-monitor.

Catalog and core integration waits for merged #10622. Its policy and fixture
overlay remain owned by that publication unit. No historical capture, input,
fixture, or checksum is regenerated here. The driver must integrate the merged
base before final exact-head review and publication.

After admission is merged and installed, the driver owns one read-only delegated
Argon-high `mcp__sources__verify_word` call. Its evidence must contain the actual
MCP result, trace, exact runtime identity, and unchanged tracked-checkout digest.
That proof does not certify model quality or repair the separately owned #10563
hook-mutation issue. This worker makes no provider call.

## Catalog schema

`models.*.lifecycle` accepts `active`, `fallback`, `hold`, and `retired`.
There is no trial lifecycle and no trial role id. Inventing either would be a
policy change.

The catalog entry `gemini-4-argon-high` uses lifecycle `hold` and the existing
role `explicit_bakeoff_only`. Medium and low are aliases of that entry, matching
the Flash selector convention, while the adapter still emits each listed slug.
`explicit_bakeoff_only` is not in `review_scheduler.activity_roles` for review
or consult, so the entry is refused for review, critique, approval, and ACP
consult. It is not a review candidate and it is not on a review ladder. It has
no `critical_review`, `security_review`, or advisor role. `require_execution_model`
refuses it for execution.

`review_scheduler.activity_roles` still names `architecture_support` and
`factual_review`. The retired `gemini-3.1-pro-high` entry is their only holder,
so those role strings stay on that retired entry. Admission refuses the retired
id before roles are read. They are not copied onto Argon.

## Absent Pro selectors

`gemini-3.1-pro-high` is retired, with `replaced_by: gemini-3.8-flash-high`
and no transport. Aliases `gemini-3.1-pro-preview`, `gemini-3.1-pro`, and
`gemini-3.1-pro-low` resolve to that retirement refusal. The accepted AGY id
list no longer names them. An unknown name containing "pro" is told that no
Gemini Pro selector is listed. It is not told to use `gemini-3.1-pro-high`.

The Gemini registry seat default is `gemini-3.8-flash-high`. The AGY seat
default was already that Flash pin.

## Routing receipts

`tests/review/fixtures/routing-10568.json.gz` records this data change on top of
the frozen routing baseline. Historical baseline bytes are unchanged. The
overlay adds the Argon catalog entry, retires `gemini-3.1-pro-high`, moves the
Gemini registry default to `gemini-3.8-flash-high`, and updates only the
captured rows whose model text follows that data. Existing reviewer verdicts
are unchanged. Thirty-two new author rows cover the three Argon selectors and
the `gemini-3.1-pro-low` alias. A provider listing is still not qualification.

## Left for the launcher owner

These still name `gemini-3.1-pro-high` and are outside this packet:

- `scripts/lib/launcher_core.sh` (`LC_GEMINI_DRIVER_MODELS` and the Gemini driver default)
- `scripts/agent_runtime/adapters/gemini.py` `GeminiAdapter.default_model`

An explicit launcher pin of the retired id is refused by the AGY adapter.
The captured Gemini driver default still asks for `gemini-3.1-pro-high`, and
catalog retirement now makes that row exit 2. This packet does not edit the
launcher. Retargeting certification belongs to the qualified launcher change
on this same issue.
