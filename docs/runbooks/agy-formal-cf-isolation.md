# AGY sealed formal CF isolation (#5555)

## Status (2026-07-23 — v1 residual Option C)

Design spikes closed **Option C fail-closed residual** (not permanent wontfix for
future isolation engineering). For **fleet-comms v1 (#5512)**, AGY remains a live
**orchestrator** seat and is **not** a sealed formal CF reviewer.

| Capability | AGY (Antigravity / Gemini) | Formal CF sealed path |
| --- | --- | --- |
| Project instructions suppress | **Unproven** for sealed review | Fail-closed |
| Ambient MCP / hooks / nested reviewers | **Unproven** | Fail-closed |
| Sealed snapshot cwd only | Hard raise in `prepare_isolated_review_launch` | Refuse |
| `review-pr --reviewer agy` | Retired (#8520) | Replaced by direct `ask-* --type review` substitute seats |
| Registry `formal_review_eligible` | `false` for `agy` | **v1 complete residual** |
| Wire #5615 / enable #5616 | Residual closeout | Reopen only with Option A/B proof |

**Proof command (must stay green):**

```bash
.venv/bin/python -m pytest tests/test_review_isolation.py -k agy_isolated -q
# expect: ReviewIsolationError agy_isolated_review_unsupported
```

## Catalog seat vs formal reviewer (do not conflate)

AGY is a catalog seat (`orchestrator_seats.agy`) for bounded work and Ukrainian content review. It is **not** a planning, design or driver seat (operator decision 2026-10-03, #9584):

| Role | Model | Status |
| --- | --- | --- |
| Bounded worker / content review | `gemini-3.8-flash-high` @ high | **Live** (`orchestrator_seats.agy`); never a driver |
| Deep escalate | `gemini-3.8-flash-high` @ high | Same SKU escalation (`orchestrator_seats.agy`) |
| Sealed formal CF *reviewer* | — | **Blocked** until isolation proof (#5555) |

Formal CF for AGY-authored work is requested by the driver of record via direct `ask-<lane> --type review`
(codex|claude|glm|grok; sealed `review-pr` removed in #8520). Nobody may treat `ask-agy --review` as sealed formal CF.

## Live lane (non-formal / bounded work)

```bash
.venv/bin/python scripts/dispatch.py dispatch --agent agy --model gemini-3.8-flash-high \
  --mode workspace-write --worktree --task-id <task> --prompt-file BRIEF
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy - \
  --task-id agy-bounded --to-model gemini-3.8-flash-high
```

## Onboarding a new AGY model id (#12398)

A new id becomes usable only after every step below has passed, in order. A listing from the provider is not qualification, and no step adds a role or a ladder place. Adding those needs model-assignment approval.

1. **Provider listing.** Run `agy models` on the host. The exact id must appear in that listing. Record the id as the wire id, never a guessed slug.
2. **Catalog entry.** Add a row under `models` in `scripts/config/model_catalog.yaml` with `family`, `lifecycle`, `transports: [agy]` and `routing_wire_ids.agy: <listed id>`. Use `lifecycle: hold` and `roles: [inventory_only]` until approval, as `gemini-4-carbon` does. `transport_model` (`scripts/dispatcher/providers/agy.py`) reads the wire id from this row.
3. **Adapter selector.** Add the listed id to `_AGY_GENERAL_MODEL_SLUGS` (Gemini) in `scripts/agent_runtime/adapters/agy.py`. Claude ids go in `_AGY_MODEL_SLUGS` and `_AGY_CLAUDE_SLUGS` instead. Without this step, `check-model` reports the id as unrecognized.
4. **Runtime attestation.** Every run attests its model from AGY's `init` event. `identity_failure` (`providers/agy.py`) settles a run whose attested family differs from the catalog family as `agy_model_identity_unverified`, so the catalog `family` must be correct.
5. **Health and quota.** Before launch, `headroom.check_plan` and `headroom.check_runtime` (`scripts/dispatcher/headroom.py`) read model pauses and recent rate limits for `(agy, <id>)`. The new id shares the `agy` quota bucket of the AGY endpoint. A quota refusal settles as `rate_limited` with AGY's reset hint.
6. **Availability (region, account).** If an id is listed in the catalog but AGY does not offer it to this account, AGY refuses it before any turn. That run settles as the typed refusal `agy_model_unavailable: <AGY's text>`, never as a bare exit status. Treat that refusal as the provider's availability answer. Do not retry it, and do not reroute to it.
7. **Resolver eligibility.** Run `closeout_cli resolve-reviewer` (see the `review-loop` skill) for each profile the approval names. Confirm that the id appears only where its catalog `roles` and `review_profiles` allow.
8. **Dry run, then one live canary.** First run the dry run below, which creates nothing:

   ```bash
   .venv/bin/python scripts/dispatch.py dispatch --agent agy --model <id> --effort high \
     --mode read-only --worktree --task-id <task> --prompt-file BRIEF --dry-run
   ```

   The printed argv must carry `--model <listed id>` inside the read-only boundary launcher. Then run one live read-only canary, which must settle `done` with an attested model of the right family and a boundary receipt whose canary passed. A failed canary keeps the model on `hold`.

A terminal failure from AGY keeps AGY's own status and error in the task record, for example `agy: terminal result unsuccessful (ERROR): API error …: EOF`. Read that text to tell a transport fault from a model-output fault. When the text holds a credential-shaped value, the whole excerpt is withheld rather than partly masked.

## Substitute formal CF

```bash
# Direct ask-* cross-family review (replaces removed review-pr):
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude - --type review --pr <N> --task-id review-<N> < prompt.md
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex - --type review --pr <N> --task-id review-<N> < prompt.md
```

## Flip criteria (do not skip)

1. Isolation matrix: project-instruction / MCP / hooks / nested-reviewer suppression proven.
2. `prepare_isolated_review_launch(engine="agy")` positive + negative tests.
3. Sealed transport registration (`ask-agy --type review` or equivalent) with receipts.
4. Smoke formal CF on a non-Google-family-authored PR.
5. Flip `formal_review_eligible: true` via CF'd enablement PR.

Parent: #5555 · stream #4707 · product #5512.
