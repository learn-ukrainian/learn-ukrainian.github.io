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

This worker-admission unit publishes independently of #10622. Only the later
advanced-routing and core P2 policy unit waits for merged #10622. That follow-up
also owns launcher changes, Pro retirement, author defaults and effort policy.
This unit's `routing-10568` overlay records only its Argon model-data additions.
Historical captures, inputs, fixtures and checksums stay unchanged.

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
The AGY worker path admits the three listed selectors through the adapter
allowlist. `delegate.py::_admit_dispatch_target` and `resolve_and_admit` do not
consult lifecycle for these worker requests. The adapter preserves the requested
tier and requires the exact provider identity on a successful stream.

`require_execution_model` separately refuses lifecycle `hold`. Its consumers
include the native Gemini, Hermes and Google API paths; it is not the AGY worker
admission gate. Catalog helper refusal does not make an AGY worker request
undispatchable.

The admission unit grants no review or advice eligibility:

- Formal code review is refused for every Argon tier at all four risk levels.
  Argon is not a review candidate or a review-ladder entry.
- Review, critique, approval and ACP consult are refused because
  `explicit_bakeoff_only` is outside their activity roles.
- Critical review, security review and advisor roles remain absent. Selector
  admission does not qualify Argon for security work or consequential advice.

## Preserved Pro compatibility

The baseline `gemini-3.1-pro-high` catalog entry remains active with transport
`agy` and aliases `gemini-3.1-pro-preview` and `gemini-3.1-pro`. The adapter's
existing Pro slug handling and guidance remain unchanged. The Gemini registry
seat retains its Pro default; the AGY seat retains its Flash default. Core P2,
launcher certification and other consumers keep their baseline behavior.

Preserving this configuration is not evidence that Pro is currently available
from the provider. The supplied listing omitted Pro. This unit makes no live
provider call and does not use a configuration or execution claim to establish
availability. Coordinated retirement remains follow-up work.

## Routing receipts

`tests/review/fixtures/routing-10568.json.gz` records this data change on top of
the frozen routing baseline. Historical baseline bytes are unchanged. The
overlay adds the Argon catalog entry and its approval-contract rows. Twenty-four
new reviewer-author rows cover the three Argon selectors. Existing model entries,
reviewer verdicts, registry defaults, launcher results and adapter results remain
at their literal baseline values. Dispatch decisions are unchanged; twelve
refusal messages add the Argon slugs to their accepted-id lists. Reconciliation prunes
the earlier Pro changes from the existing overlay; it does not derive a new
expected result from candidate captures. A provider listing is still not
qualification.
