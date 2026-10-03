# AGY review permission grants (#9625)

AGY supports per-tool `mcp(server/tool)` grants and token-prefix
`command(prefix)` grants in `settings.json`. See the upstream
[permission reference](https://antigravity.google/docs/permissions?tab=cli).
The adapter writes or verifies this file under the attempt's scoped
`AGY_APP_DATA_DIR`; it never edits the user's global settings.

| Route | Sources grants | Command grants |
| --- | --- | --- |
| Full content review | `review_tools("full")`, individually named | `cat`, `head`, `tail`, `wc` |
| Isolated content review | `review_tools("isolated")`, individually named | `cat`, `head`, `tail`, `wc` |
| Scoped ad hoc review | Same isolated contract | Same isolated commands |

The shared review contract checks the behavior-audited Sources reader set;
writer tools remain outside both the exposed review catalog and the allow set.
`search_resources` is full-only. The four command grants only read evidence.
Their documented flag surfaces and rejection of execute-program flags are tested for every granted binary.
Use AGY’s built-in search tool; `rg --pre` can execute a program. No Git
command is granted: `log`, `diff` and `show` accept `--output`, which can
overwrite scoped settings in the writable runtime directory; inspection can
also invoke Git helpers. Dropping the grants avoids relying on settings reload
behavior or introducing another sandbox bind. Shells,
interpreters, unrestricted Git, MCP wildcards, and the permission bypass are
never granted. Command grants are permission prefixes, **not a replacement for
the existing OS review boundary**; flags on a reader can have side effects.
The separate unsupported AGY code-review isolation route still refuses.

## Production plan prompt command decisions

The plan template's full-access paragraph previously promised "read access to
the repository checkout, its git history" and described "catalogue and git
reads" as context (`scripts/review/prompts/plan-review.md.j2`, section 3).
The review contract likewise permits "the full matching checkout, textbook
corpus, resource catalogue" and "git history"
(`docs/epics/fresh-build-review-contracts.md`, full-access review section).
Neither requires a command invocation; the plan checks ask to "Read the
plan-stage activity report" and "Compare" the mapped activity totals, already
included as manifest inputs. Isolated access supplies those same pinned inputs
without the full-access paragraph. No positive instruction in the template or
contract requires `ls`, `find`, `grep`, `rg`, a shell or Python.

| Command | AGY plan review decision (full and isolated) | Evidence / replacement |
| --- | --- | --- |
| `git diff`, `git log`, `git show` | No grant; explicitly unavailable in the prompt | `--output` and Git helpers make prefix grants unsafe; no additional read-only sandbox binds are introduced. Use supplied manifest inputs and built-in file reads; report an evidence gap when history is needed. |
| `ls` | No grant; do not invoke | Built-in file discovery covers permitted context. |
| `find` | No grant; do not invoke | `-exec`, `-delete` and `-fprint` can execute or write; use built-in discovery. |
| `grep`, `rg` | No grant; do not invoke | Built-in search covers permitted context; `rg --pre` executes a program. |
| Python, shells, scripts | No grant; do not invoke | Arbitrary execution is unnecessary for these content checks; deterministic reports are supplied. |
| `cat`, `head`, `tail`, `wc` | Retain existing audited grants; production plan prompt uses built-in readers | Existing per-route flag audit remains the gate; forced-reader driver canaries still exercise `cat`. |
| Listed Sources MCP tools | Retain exact per-tool grants | These issue the receipts required by the review contract. |

The template gives explicit AGY guidance in both access modes, before the
full-only context paragraph. Other harnesses retain permitted Git context.
The guidance is part of the rendered, hashed prompt, not an adapter-side
rewrite after attestation. It does not change the allow set or filesystem
boundary. Prompt render/check tests cover both access modes; live production
template success remains a driver canary requirement.

A caller can declare its known requirements using
`tool_config["agy_required_permissions"]`, a list of exact permission resources.
A resource outside the route's allow set raises `AgyReviewPermissionError` with
`reason="agy_review_permission_outside_allow_set"` before any CLI probe or
provider execution. Requested servers and `allowed_tools` are checked too.
Missing scoped homes, resumed sessions, and changed settings also refuse with
body-free reasons. An undeclared action chosen by the model cannot be predicted
at dispatch; native permissions and the OS boundary still govern it. The production
response parser recognizes the native `jetski: no output produced` headless
auto-denial notice before the transcript completion gate. It returns
`failure_code="provider_policy_refusal"`, with
`agy_headless_permission_denied` leading the diagnostic and JSON
`permission_kind` / `permission_target` details. An absent target is null; the
CLI’s literal `<target>` example is never an observed target. Do not
claim that construction tests prove every future model-selected command.

## Recorded denial evidence

The retained stderr logs for `plan-review-a1-p2-r3` and
`plan-review-a1-p3-r3` report kind `command`; `plan-review-a1-p2-full-2`
reports `mcp`. Each has empty stdout and only the literal `<target>` example.
Their runtime directories and temporary AGY logs are no longer retained;
the matching scoped review homes contain no conversation JSONL transcripts.
Neither denied command could be recovered. The allow set remains the four
simple readers above, with no guessed additions. These logs establish the
refusal shape, not successful recovery of the historical reviews. The earlier
MCP failures predate the per-tool grants from #9493; live success still needs
a driver canary.

## Driver canaries after independent implementation review

Run from the reviewed dispatch checkout, with its prescribed shared project
interpreter in `PROJECT_PYTHON`. Set `CANARY_MANIFEST` and `CANARY_INPUT_ROOT` to
an eligible, hash-pinned **trivial content-plan** fixture and its input checkout.
For `full` and `plan-template`, `CANARY_INPUT_ROOT` must be the Git checkout
top level containing the fixture, not its fixture subdirectory; otherwise the
boundary refuses with `full_review_checkout_missing`. Paths in the manifest
are relative to that root. The snippet's explicit `PYTHONPATH` supplies both
the checkout's `scripts` import root (for `ai_llm`) and the checkout itself.
Set `CANARY_INITIATOR` to the driver's own trusted Source identity.
Use a public fixture whose first non-empty plan line is suitable for an output
comparison; never use private text. These are real provider calls, reserved for
the accountable driver. Each call has a 180-second hard timeout, and a failure
ends that canary without a retry or provider substitution.

Define the function once, then run the exact command for each route:

```bash
CANARY_CHECKOUT="$(git rev-parse --show-toplevel)"
# Default to the reviewed checkout; override only with another eligible input checkout.
CANARY_INPUT_ROOT="${CANARY_INPUT_ROOT:-$CANARY_CHECKOUT}"
agy_review_canary() {
  PYTHONPATH="$CANARY_CHECKOUT/scripts:$CANARY_CHECKOUT" \
    "$PROJECT_PYTHON" - "$1" "$CANARY_MANIFEST" "$CANARY_INPUT_ROOT" <<'PY'
import json
import os
import shlex
import sys
import tempfile
from pathlib import Path

import yaml

from scripts.agent_runtime.runner import invoke
from scripts.agent_runtime.review_mcp import prepare_review_attempt
from scripts.review.prompts.render import render_prompt
from scripts.review.receipts.ledger import records
from scripts.review.validate import validate_review

route, manifest_arg, root_arg = sys.argv[1:]
assert route in {"full", "isolated", "ad-hoc", "plan-template"}
manifest, root = Path(manifest_arg).resolve(), Path(root_arg).resolve()
access = "full" if route in {"full", "plan-template"} else "isolated"
plan_path = yaml.safe_load(manifest.read_text())["inputs"]["plan"]["path"]
first_line = next(line for line in (root / plan_path).read_text().splitlines() if line.strip())
prompt = (
    f"Review only the trivial content plan at {plan_path}. "
    f"First execute cat -- {shlex.quote(plan_path)}; then call the Sources "
    "verify_words tool with words=['стіл']. Read both results before replying. "
    "Give one English sentence assessing the plan and include "
    "CANARY_READ: followed by the exact first non-empty plan line. "
    "Do not edit files, invoke other agents, or use other commands."
)
with tempfile.TemporaryDirectory(prefix="agy-9625-canary-") as temp:
    prepared = prepare_review_attempt(
        "canary-9625", route, manifest, "agy", receipts_root=Path(temp), review_access=access,
    )
    if route == "plan-template":
        # Exact production template, without a forced first command or tool.
        prompt, prompt_sha, _ = render_prompt(
            manifest, "plan-review.md.j2", repo_root=root,
            review_id=prepared.review_id, attempt_id=prepared.attempt_id,
            review_access=access,
        )
    tc = {
        **prepared.adapter_options,
        "review_id": "canary-9625", "attempt_id": route,
        "review_manifest": str(manifest), "review_input_root": str(root),
    }
    if route != "plan-template":
        tc["agy_required_permissions"] = ["command(cat)", "mcp(sources/verify_words)"]
    if route == "ad-hoc":
        tc.pop("review_access")  # Legacy/ad hoc callers use the isolated default.
    result = invoke(
        "agy", prompt, mode="read-only", cwd=root, model="gemini-3.8-flash-high",
        effort="high", task_id=f"canary-9625-{route}", tool_config=tc,
        initiator=os.environ["CANARY_INITIATOR"], hard_timeout=180, stall_timeout=60, entrypoint="runtime",
    )
    assert result.ok, result.stderr_excerpt
    if route == "plan-template":
        returned = Path(temp) / "plan-review.yaml"
        returned.write_text(result.response)
        checked = validate_review(
            returned, manifest_path=manifest, ledger_path=prepared.ledger_path,
            repo_root=root, review_access=access,
        )
        assert checked.ok, checked.rejections
        successful = [r for r in records(prepared.ledger_path) if r.get("status") == "ok"]
        assert successful, "No successful Sources receipt; permission success unproven"
        print(json.dumps({"route": route, "ok": result.ok, "prompt_sha256": prompt_sha,
                          "successful_receipts": len(successful), "return_valid": True}))
        sys.exit(0)
    calls = [c for c in result.tool_calls if c["name"] == "mcp__sources__verify_words"]
    assert "CANARY_READ:" + first_line in result.response.replace("CANARY_READ: ", "CANARY_READ:")
    assert any(c.get("arguments") == {"words": ["стіл"]}
               and "Found: 1/1" in json.dumps(c.get("result", []), ensure_ascii=False) for c in calls)
    print(json.dumps({"route": route, "ok": result.ok, "read_match": True,
                      "sources_calls": len(calls), "permission_canary": "PASS"}))
PY
}

# Full-access formal content review:
agy_review_canary full
# Isolated read-only content review:
agy_review_canary isolated
# Scoped ad hoc read-only review using the same isolated boundary:
agy_review_canary ad-hoc
# Full review using the production plan prompt; no forced command choice:
agy_review_canary plan-template
```

A passing canary needs a structurally complete native transcript, the actual
plan line in the reply, a successful Sources tool result, and the driver's
inspection of the one-sentence review and command result. Exit zero or the final
marker alone is insufficient. Confirm the transcript contains the requested
`cat` invocation and a successful result, and no permission auto-denial. Keep
any full transcript local. For `agy_review_canary plan-template`, the actual
`plan-review.md.j2` return must pass `validate_review`, contain successful
Sources receipts, and match the driver’s independently established expected
judgment and evidence for the pinned plan. A schema-valid verdict alone is
insufficient; record prompt hash, reviewed head, receipt identities and semantic
judgment without publishing input content. This run does not require `cat`
or `CANARY_READ`, and supplies no `agy_required_permissions` declaration.
A permission failure remains a blocker owned by the driver; do not widen the allow set to make an unapproved operation pass.

## Local verification

This explicitly named scope includes direct AGY adapter imports and consumers of
`review_mcp` and `attempt_boundary`; it does not collect the whole test tree.
Use the dispatch's prescribed shared interpreter as `PROJECT_PYTHON`.

```bash
"$PROJECT_PYTHON" -m pytest \
  tests/test_delegate.py \
  tests/test_agent_runtime.py \
  tests/test_coverage_bridge_audit.py \
  tests/test_rules_core_loading.py \
  tests/agent_runtime/test_full_review_access.py \
  tests/agent_runtime/test_attempt_boundary.py \
  tests/agent_runtime/test_attempt_safe_read.py \
  tests/agent_runtime/test_delegate_tool_config_contract.py \
  tests/agent_runtime/test_review_mcp.py \
  tests/agent_runtime/adapters/test_agy_review_permissions.py \
  tests/agent_runtime/adapters/test_agy_adapter.py \
  tests/agent_runtime/test_sibling_provider_signals.py \
  tests/review/test_full_review_access.py \
  tests/review/test_prompts.py \
  tests/review/test_prompt_structural_rules.py \
  tests/review/test_record.py \
  tests/review/seeds/test_manifest.py \
  tests/agent_runtime/test_review_contract.py \
  tests/agent_runtime/test_claude_permissions.py \
  tests/agent_runtime/test_sources_read_only.py \
  tests/agent_runtime/adapters/test_kimi_adapter.py \
  tests/review/test_template_admission.py \
  tests/review/test_attempt_artifact_binding.py \
  tests/agent_runtime/test_acpx_adapter.py \
  tests/test_delegate_review_admission.py \
  tests/ai_agent_bridge/test_review_worktree.py \
  -n 2 -q --tb=short
```
