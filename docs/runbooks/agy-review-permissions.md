# AGY review permission grants (#9625)

AGY supports per-tool `mcp(server/tool)` grants and token-prefix
`command(prefix)` grants in `settings.json`. See the upstream
[permission reference](https://antigravity.google/docs/permissions?tab=cli).
The adapter writes or verifies this file under the attempt's scoped
`AGY_APP_DATA_DIR`; it never edits the user's global settings.

| Route | Sources grants | Command grants |
| --- | --- | --- |
| Full content review | `review_tools("full")`, individually named | `cat`, `head`, `tail`, `wc`, `rg`, `git status`, `git diff`, `git log`, `git show`, `git ls-files` |
| Isolated content review | `review_tools("isolated")`, individually named | `cat`, `head`, `tail`, `wc`, `rg` |
| Scoped ad hoc review | Same isolated contract | Same isolated commands |

The shared review contract checks the behavior-audited Sources reader set;
writer tools remain outside both the exposed review catalog and the allow set.
`search_resources` is full-only. The common commands read and search evidence;
Git inspection is admitted only for the full checkout route. Shells,
interpreters, unrestricted Git, MCP wildcards, and the permission bypass are
never granted. Command grants are permission prefixes, **not a replacement for
the existing OS review boundary**; flags on a reader can have side effects.
The separate unsupported AGY code-review isolation route still refuses.

A caller can declare its known requirements using
`tool_config["agy_required_permissions"]`, a list of exact permission resources.
A resource outside the route's allow set raises `AgyReviewPermissionError` with
`reason="agy_review_permission_outside_allow_set"` before any CLI probe or
provider execution. Requested servers and `allowed_tools` are checked too.
Missing scoped homes, resumed sessions, and changed settings also refuse with
body-free reasons. An undeclared action chosen by the model cannot be predicted
at dispatch; native permissions and the OS boundary still govern it. Do not
claim that construction tests prove every future model-selected command.

## Driver canaries after independent implementation review

Run from the reviewed dispatch checkout, with its prescribed shared project
interpreter in `PROJECT_PYTHON`. Set `CANARY_MANIFEST` and `CANARY_INPUT_ROOT` to
an eligible, hash-pinned **trivial content-plan** fixture and its input checkout.
Set `CANARY_INITIATOR` to the driver's own trusted Source identity.
Use a public fixture whose first non-empty plan line is suitable for an output
comparison; never use private text. These are real provider calls, reserved for
the accountable driver. Each call has a 180-second hard timeout, and a failure
ends that canary without a retry or provider substitution.

Define the function once, then run the exact command for each route:

```bash
agy_review_canary() {
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

route, manifest_arg, root_arg = sys.argv[1:]
assert route in {"full", "isolated", "ad-hoc"}
manifest, root = Path(manifest_arg).resolve(), Path(root_arg).resolve()
access = "full" if route == "full" else "isolated"
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
    tc = {
        **prepared.adapter_options,
        "review_id": "canary-9625", "attempt_id": route,
        "review_manifest": str(manifest), "review_input_root": str(root),
        "agy_required_permissions": ["command(cat)", "mcp(sources/verify_words)"],
    }
    if route == "ad-hoc":
        tc.pop("review_access")  # Legacy/ad hoc callers use the isolated default.
    result = invoke(
        "agy", prompt, mode="read-only", cwd=root, model="gemini-3.8-flash-high",
        effort="high", task_id=f"canary-9625-{route}", tool_config=tc,
        initiator=os.environ["CANARY_INITIATOR"], hard_timeout=180, stall_timeout=60, entrypoint="runtime",
    )
    calls = [c for c in result.tool_calls if c["name"] == "mcp__sources__verify_words"]
    assert result.ok, result.stderr_excerpt
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
```

A passing canary needs a structurally complete native transcript, the actual
plan line in the reply, a successful Sources tool result, and the driver's
inspection of the one-sentence review and command result. Exit zero or the final
marker alone is insufficient. Confirm the transcript contains the requested
`cat` invocation and a successful result, and no permission auto-denial. Keep
any full transcript local. A permission failure remains a blocker owned by the
driver; do not widen the allow set to make an unapproved operation pass.

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
