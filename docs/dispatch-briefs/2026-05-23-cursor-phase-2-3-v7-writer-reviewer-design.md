# Phase 2 + Phase 3 Design Spec: `cursor-agent` / `composer-2.5` as V7 Writer + Reviewer

> **Scope:** Add `cursor-tools` as a first-class V7 writer and wire Cursor-hosted models (e.g. `composer-2.5` writer, `grok-4.20-reasoning` reviewer) through the existing agent runtime + linear pipeline.
>
> **Phase split (matches existing dispatch plan):**
> - **Phase 2:** `scripts/agent_runtime/adapters/cursor.py`, registry, `delegate.py --agent cursor`, `tool_config.py`, adapter tests. Phase 1 bridge (`ab ask-cursor`) **done** — PR #2252 merged (`c6d4345119`).
> - **Phase 3:** `linear_pipeline.py` + `v7_build.py` writer/reviewer wiring, scoped MCP workspace, **`SELF_REVIEW_DETECTED` hardening (required)**, observability tests.
>
> Created: 2026-05-23 | Revised: 2026-05-23 (orchestrator review)

### Orchestrator review — incorporated before dispatch

Three pushbacks from main-agent review (do **not** dispatch Phase 3 without these):

1. **`_model_family` hardening is REQUIRED in Phase 3**, not optional. `composer-2.5` writer + `composer-2.5` reviewer both map to family `None` today → gate silently skips → violates `pipeline.md` ("An LLM must NEVER review its own work"). Ship either extended `_model_family` **or** exact-model-id equality when both families are `None`.
2. **Scoped workspace must be the V7 build worktree / `module_dir`**, never `PROJECT_ROOT`. Main checkout already has `.cursor/mcp.json`; writing there clobbers live config. Wire `module_dir` (or worktree root) through `_runtime_tool_config()` → `_ensure_cursor_writer_workspace()`.
3. **Phase 1 bridge dependency satisfied.** `scripts/ai_agent_bridge/_cursor.py` is on main via PR #2252 — Phase 2 does not re-implement the bridge.

---

## 1. Adapter shape: `scripts/agent_runtime/adapters/cursor.py`

### Target pattern

Mirror **`gemini.py`** (stdout-based, no `-o` file) for I/O, and **`codex.py`** for per-invocation MCP scoping via `tool_config` env/path overrides.

```python
class CursorAdapter:
    name: str = "cursor"
    default_model: str = "composer-2.5"
    supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})
    # resume_policy in registry: "never" (same rationale as codex — worktree isolation,
    # no cache win on subscription path)
```

### Registry entry (`scripts/agent_runtime/registry.py`)

Add alongside existing entries (~L37–157):

```python
"cursor": {
    "adapter": "scripts.agent_runtime.adapters.cursor:CursorAdapter",
    "default_model": "composer-2.5",
    "cost_tier": "low",
    "capabilities": frozenset({"content_writing", "content_review", "adversarial_review"}),
    "cli_available": True,
    "resume_policy": "never",
},
```

### `build_invocation()` — literal argv shape

Binary resolution (match bridge + judge calibrator):

```python
cursor_bin = shutil.which("agent") or shutil.which("cursor-agent") or "agent"
```

**Writer path** (`mode="workspace-write"`, V7 `invoke_writer`):

```text
agent -p <prompt via stdin> \
  --model <model or default composer-2.5> \
  --output-format stream-json \
  --trust \
  --approve-mcps \
  --mode plan \
  --sandbox enabled \
  --workspace <cwd>
```

**Reviewer path** (`mode="read-only"`, V7 `llm_qg` / wiki coverage):

```text
agent -p <prompt via stdin> \
  --model <e.g. grok-4.20-reasoning> \
  --output-format stream-json \
  --trust \
  --mode ask \
  --workspace <cwd>
```

**Do not pass `--yolo` / `--force` in either path.**

Implementation notes (mirror existing adapters):

| Concern | Pattern to copy | Where |
|--------|------------------|-------|
| Prompt delivery | stdin payload, not argv (yargs-length bugs) | `gemini.py` L302–313 |
| Tool trace | `--output-format stream-json` + `parse_json_events` | `claude.py` L274–349 |
| Rate limits | stderr/stdout pattern match + `ok = bool(response) and not rate_limited` | `gemini.py` L405–439 |
| `tool_config` surface | Document keys in adapter docstring; ignore unknown keys | `codex.py` L291–338 |
| `effort` | Log + no-op until Cursor exposes flag | `gemini.py` L220–224 |
| Liveness | Return `()` — rely on stdout streaming (like Hermes) unless empirical testing shows mtime files under `~/.cursor/` | `hermes_qwen.py` L235–238 |

### `tool_config` keys for CursorAdapter

```python
{
    "output_format": "stream-json",          # required for writer telemetry
    "cursor_workspace": str,                 # cwd containing scoped .cursor/mcp.json
    "approve_mcps": True,                    # writer only
    "cursor_mode": "plan" | "ask",           # plan=writer, ask=reviewer
    "sandbox": "enabled" | "disabled",       # writer default: enabled
}
```

`parse_response()`: parse stdout as JSONL via `parse_json_events(..., source="cursor")`, normalize tool calls via `normalize_tool_calls`, return `ParseResult` with `tool_calls` populated (unlike Hermes black-box adapters).

---

## 2. `--trust` / `--approve-mcps` / `--yolo` security boundary

### Problem (from Cursor CLI help, verified locally)

```
-p, --print     … Has access to all tools, including write and shell.
--yolo          Alias for --force (Run Everything)
--approve-mcps  Automatically approve all MCP servers
--mode plan     read-only/planning, no edits
--mode ask      Q&A style, read-only
--sandbox       enabled | disabled
```

`--yolo` auto-approves **shell + write + MCP**. Writer prompts forbid file edits, but Composer can still emit shell tools.

### Recommended flag combination

#### V7 writer (`cursor-tools`, needs MCP)

**Primary (recommended):**

```bash
agent -p - \
  --model composer-2.5 \
  --output-format stream-json \
  --trust \
  --approve-mcps \
  --mode plan \
  --sandbox enabled \
  --workspace "$MODULE_CWD"
```

Rationale:

- **`--mode plan`**: Cursor's read-only/planning mode — blocks file edits without `--yolo`.
- **`--approve-mcps`**: auto-approves MCP **without** `--yolo` (MCP-only approval path).
- **`--sandbox enabled`**: extra guard on shell side-effects if model tries `run_terminal_cmd`.
- **No `--yolo`**: shell/write not force-approved.
- **Defense in depth:** `classify_writer_trace()` still flags non-`mcp__sources__*` tools (`linear_pipeline.py` L2278–2287).

**Empirical gate before merge:** Run one dry writer call and confirm MCP tools work in `--mode plan`. If plan blocks MCP, fall back to:

```bash
agent -p - \
  --model composer-2.5 \
  --output-format stream-json \
  --trust \
  --approve-mcps \
  --sandbox enabled \
  --workspace "$MODULE_CWD"
```

(still **no** `--yolo`; accept stall-timeout kill if model tries shell without approval).

#### V7 reviewer (read-only, no MCP needed)

```bash
agent -p - \
  --model grok-4.20-reasoning \
  --output-format stream-json \
  --trust \
  --mode ask \
  --workspace "$MODULE_CWD"
```

No `--approve-mcps` (review prompts are self-contained prose/JSON).

#### Bridge Q&A (`ab ask-cursor`, Phase 1 — already specified)

```bash
agent -p PROMPT --model composer-2.5 --output-format text --trust
```

No `--yolo`, no `--approve-mcps` (no MCP needed for judge/Q&A).

### What **not** to use

| Approach | Verdict |
|----------|---------|
| `--yolo --approve-mcps` | Reject for V7 writer — over-broad auto-approval |
| `CURSOR_DISABLE_TOOLS` env | **Not in CLI help** — do not invent |
| `.cursor/mcp.json` "tricks" alone | Necessary but insufficient without mode/sandbox layering |
| Gemini-style `--allowed-mcp-server-names` | **Cursor has no equivalent flag** — scope via workspace-local `.cursor/mcp.json` |

---

## 3. MCP discipline at writer invocation: scoped workspace

### Yes — per-build workspace scoping is required

Codex solves desktop MCP leakage via scoped `$CODEX_HOME` (`linear_pipeline.py` L2942–3051). Cursor's parallel is **workspace-local** `.cursor/mcp.json`, not a global home override.

Repo already has a minimal global config at `.cursor/mcp.json` (sources only). **Do not write scoped MCP config there** — that clobbers the live checkout. V7 builds run in **worktrees** (`v7_build.py` `--worktree`); scoped config belongs under the build's **`module_dir`** (artifact dump) or worktree root, same isolation intent as `_ensure_codex_writer_home()` using `$TMPDIR`, not the main tree.

### Sketch: `_ensure_cursor_writer_workspace()`

Add near `_ensure_codex_writer_home()` (`linear_pipeline.py` ~L2942):

```python
def _ensure_cursor_writer_workspace(
    cwd: Path,
    *,
    event_sink: Callable[..., None] | None = None,
) -> Path:
    """Materialize scoped .cursor/mcp.json for V7 cursor-tools writer.

    Cursor loads MCP from the workspace directory (--workspace / cwd),
    not from repo-root .mcp.json (Claude/Codex path). Only the sources
    server may be registered — same contract as _ensure_codex_writer_home.
    """
    cursor_dir = cwd / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    config_path = cursor_dir / "mcp.json"
    desired = (
        '{\n'
        '  "mcpServers": {\n'
        '    "sources": {\n'
        '      "url": "http://127.0.0.1:8766/mcp"\n'
        '    }\n'
        '  }\n'
        '}\n'
    )
    if not config_path.exists() or config_path.read_text(encoding="utf-8") != desired:
        config_path.write_text(desired, encoding="utf-8")

    _emit(
        event_sink,
        "cursor_writer_workspace_resolved",
        workspace=str(cwd.resolve()),
        mcp_config=str(config_path),
    )
    return cwd.resolve()
```

### Wire into `_runtime_tool_config()` (~L3054–3162)

**Signature change (required):** add `*, workspace_dir: Path` — no `PROJECT_ROOT` fallback, no env-var escape hatch in production code.

```python
def _runtime_tool_config(
    agent_label: str,
    *,
    workspace_dir: Path,
    event_sink: Callable[..., None] | None = None,
) -> dict[str, Any]:
    ...
    elif agent_label == "cursor-tools":
        agent_kwargs = {"mcp_servers": ["sources"]}
        cursor_workspace = _ensure_cursor_writer_workspace(
            workspace_dir,
            event_sink=event_sink,
        )
        tool_config.update({
            "cursor_workspace": str(cursor_workspace),
            "approve_mcps": True,
            "cursor_mode": "plan",
            "sandbox": "enabled",
        })
```

**Call-site change (required):** `invoke_writer()` passes the same `cwd` it already uses for the subprocess — in V7 that is **`module_dir`** under the build worktree (`v7_build.py` writer phase). `_ensure_cursor_writer_workspace(module_dir)` writes `{module_dir}/.cursor/mcp.json`; CursorAdapter passes `--workspace {module_dir}`.

Tests must assert scoped config path is **under `tmp_path` / fake module_dir**, never repo root (mirror `test_runtime_tool_config_codex_tools_scoped_codex_home`).

Also extend `_runtime_tool_config`'s unknown-writer error string (L3122–3126) and `WRITER_CHOICES` (L69–77).

### `tool_config.py` extension

Add to `_canonical_agent_name()` (~L23–39):

```python
if agent.startswith("cursor"):
    return "cursor"
```

Add Cursor branch in `build_mcp_tool_config()` (~L171+) returning:

```python
{"cursor_workspace": "<path>", "approve_mcps": True, "cursor_mode": "plan", "sandbox": "enabled"}
```

(diagnostics `config_path` should point at `{workspace}/.cursor/mcp.json`, not repo `.mcp.json`).

---

## 4. Writer-isolation gate compatibility (`SELF_REVIEW_DETECTED`)

### Audit gate logic (post-build, review markdown)

The gate lives in `scripts/audit/checks/review_gaming.py`:

```python
# L671–686
if builder_model:
    reviewer_family = _model_family(reviewed_by)
    builder_family = _model_family(builder_model)

    if reviewer_family and builder_family and reviewer_family == builder_family:
        violations.append({
            'type': 'SELF_REVIEW_DETECTED',
            ...
        })
```

Family extraction (`_model_family`, L691–702) **only** maps:

| Substrings | Family |
|------------|--------|
| `gemini`, `google`, `palm` | `google` |
| `claude`, `anthropic`, `sonnet`, `opus`, `haiku` | `anthropic` |
| `gpt`, `openai`, `o1`, `o3` | `openai` |
| everything else | **`None`** |

### Answer for `composer-2.5` writer + `grok-4.20-reasoning` reviewer (both via Cursor)

**Gate sees them as different → no `SELF_REVIEW_DETECTED`.**

- `Reviewed-By: grok-4.20-reasoning` → `_model_family` → **`None`**
- `builder_model: composer-2.5` (from `state-v3.json`) → **`None`**
- Condition requires **both** families non-None **and** equal → **skipped**

Existing tests confirm unrelated unknown families pass (`tests/test_coverage_audit_pipeline.py` L414–424).

### REQUIRED Phase 3: `_model_family` / self-review hardening

**Acceptance criterion:** `composer-2.5` builder + `composer-2.5` reviewer **must** emit `SELF_REVIEW_DETECTED` (or equivalent build-time fatal) before merge.

Implement **one** of these (or both — belt + suspenders):

**Option A — extend `_model_family()`** (`review_gaming.py` L691–702):

```python
if any(k in model_lower for k in ("composer", "cursor")):
    return "cursor-composer"  # or normalize composer-* ids to a stable family
if "grok" in model_lower:
    return "cursor-grok"  # distinct from composer even when both via Cursor CLI
```

**Option B — exact-model fallback** (when both families are `None`):

```python
if builder_model and reviewed_by:
    norm_builder = builder_model.lower().strip()
    norm_reviewer = reviewed_by.lower().strip()
    if norm_builder == norm_reviewer:
        violations.append({... 'type': 'SELF_REVIEW_DETECTED' ...})
    elif reviewer_family is None and builder_family is None:
        # same-model self-review caught above; different unknown ids still pass
        pass
```

Add tests in `tests/test_coverage_audit_pipeline.py` (`TestCheckCrossAgentReview` / `TestModelFamily`):

- `composer-2.5` + `grok-4.20-reasoning` → **no** violation (cross-model via Cursor)
- `composer-2.5` + `composer-2.5` → **violation** (same model — currently a hole)

Also add V7 **build-time** assert (in `_run_llm_qg` / `_run_wiki_coverage_review`):

```python
assert WRITER_DEFAULTS[writer]["model"] != REVIEWER_DEFAULTS[reviewer]["model"]
```

### Other gaps to fix in Phase 3

1. **Cursor-hosted OpenAI models may false-positive**
   If reviewer `Reviewed-By: gpt-5.5` and builder used a `gpt-*` writer, both map to `openai` → **`SELF_REVIEW_DETECTED`** even across different agents. Document or refine if Cursor routes OpenAI models through subscription.

2. **V7 runtime pairing is separate from audit gate**
   Current V7 reviewer map (`v7_build.py` L651–656):

   ```python
   def _reviewer_for_writer(writer: str) -> str:
       if writer == "claude-tools":
           return "gemini-tools"
       if writer == "grok-tools":
           return "claude-tools"
       return "claude-tools"
   ```

   **`cursor-tools` is unhandled** → defaults to `claude-tools` reviewer today. Phase 3 must add explicit mapping, e.g.:

   ```python
   if writer == "cursor-tools":
       return "cursor-tools"  # same agent label, different model via REVIEWER_DEFAULTS
   ```

3. **Policy doc vs code drift**
   `claude_extensions/rules/pipeline.md` L18–24 says Codex primary reviewer; V7 code currently routes most writers to `claude-tools`. Update policy doc when cursor reviewer lands.

---

## 5. `PROMPT_BY_WRITER` entry

### Recommendation: **share `linear-write.md` initially** (no variant file)

Evidence from current maps (`linear_pipeline.py` L90–95):

```python
PROMPT_BY_WRITER = {
    "grok-tools": "linear-write-grok.md",
}
CORRECTION_PROMPT_BY_WRITER = {
    "grok-tools": "linear-writer-correction-grok.md",
}
```

Only `grok-tools` has a variant — added after empirical tool-naming / behavior divergence. Default fallback:

```python
# L1704–1706
def writer_prompt_path(writer_family: str) -> Path:
    prompt_filename = PROMPT_BY_WRITER.get(writer_family, "linear-write.md")
```

**Do not add** `PROMPT_BY_WRITER["cursor-tools"]` in Phase 3 unless bakeoff proves a need.

### Do add `WRITER_SPECIFIC_DIRECTIVES["cursor-tools"]`

Mirror `agy-tools` block (L96–107): explicit "MCP only, no shell, no repo edits, emit fenced artifacts in stdout".

Example sketch:

```python
"cursor-tools": """\
## cursor-tools writer directives
- Use ONLY `mcp__sources__*` tools for verification. Do NOT run shell commands or edit files.
- Emit all artifacts as fenced blocks in your final message (`markdown file=…`, `json file=…`).
- If MCP is unavailable, emit `<!-- VERIFY: … -->` and continue — do not improvise with Bash/Write.
""",
```

Correction prompt: default `linear-writer-correction.md` (same as claude/gemini/codex).

---

## 6. Tests that must be updated

Use this as the Phase 2/3 dispatch regression checklist (PR #2250 → #2253 class).

### Phase 2 — adapter + registry + delegate

| File | Why |
|------|-----|
| **`tests/agent_runtime/adapters/test_cursor_adapter.py`** | **NEW** — argv assembly (writer vs reviewer modes), `--yolo` absent, `tool_config` translation, parse_response on fixture stdout |
| **`tests/test_agent_runtime.py`** | `test_registry_has_known_agents` (L168–179) hard-coded agent set; add `"cursor"`; add `test_load_adapter_cursor`; extend `test_validate_agent_name_rejects_tools_suffix` parametrize (~L233) with `("cursor-tools", "cursor")` |
| **`tests/test_grok_integration.py`** | **NEW `tests/test_cursor_integration.py` mirroring this** — registry exposes `cursor`; `delegate.py dispatch --agent cursor --dry-run` parses |
| **`tests/bridge/test_ask_cursor.py`** | Phase 1 (PR #2252) — if Phase 2 touches bridge, keep green |

### Phase 3 — pipeline wiring

| File | Why |
|------|-----|
| **`tests/test_v7_writer_dispatch.py`** | Parametrize lists L44–53, L109–111 — add `("cursor-tools", "cursor")`, alias `("cursor", "cursor-tools")`; writer cwd tests L123–128 |
| **`tests/test_mcp_init_observability.py`** | `_runtime_tool_config` suite — add `cursor-tools` success path; extend `test_runtime_tool_config_non_codex_tools_no_disable_features` loop (L381); update unknown-writer message test (L579–584); **NEW** scoped-workspace test mirroring `test_runtime_tool_config_codex_tools_scoped_codex_home` (L249+) |
| **`tests/build/test_linear_pipeline.py`** | `test_invoke_writer_routes_supported_writers` parametrize (L113–118) only covers claude/gemini — add cursor-tools |
| **`tests/test_writer_isolation.py`** | If Cursor emits different MCP tool names (e.g. `mcp_sources_*` vs `mcp__sources__*`), add prefix acceptance tests mirroring L62–82 |
| **`tests/build/test_v7_build_e2e.py`** | Dry-run writer alias acceptance — add `--writer cursor-tools` / `--writer cursor` |
| **`tests/test_resume_default.py` / `tests/build/test_v7_build_resume.py`** | Only if new phases/artifacts added (unlikely) |

### Phase 3 — prompt / directives (if variant added)

| File | Why |
|------|-----|
| **`tests/build/test_linear_write_grok_prompt.py`** | Template for prompt routing tests — extend or add `test_linear_write_cursor_prompt.py` **only if** variant prompt is introduced |
| **`tests/build/test_implementation_map_render.py`** | Parametrized writer render (uses `grok-tools`) — add `cursor-tools` if directive block must appear |
| **`tests/agent_runtime/adapters/test_agy_adapter.py`** | Pattern for `WRITER_SPECIFIC_DIRECTIVES` appearing in rendered prompt (L134–137) — replicate for cursor |

### Phase 3 — reviewer / self-review policy

| File | Why |
|------|-----|
| **`tests/test_determine_reviewer.py`** | Pins v6 `_determine_reviewer` — update if v6 map gains `cursor-tools` |
| **`tests/test_coverage_audit_pipeline.py`** | **REQUIRED** — `TestCheckCrossAgentReview` / `TestModelFamily` (L392–455): `composer-2.5` + `grok-4.20-reasoning` pass; `composer-2.5` + `composer-2.5` **must fail** (Phase 3 blocker) |

### Files touched in implementation (grep-driven — update if modified)

| Production file | Maps / functions |
|-----------------|------------------|
| `scripts/agent_runtime/adapters/cursor.py` | **new** |
| `scripts/agent_runtime/registry.py` | `AGENTS` |
| `scripts/agent_runtime/tool_config.py` | `_canonical_agent_name`, `build_mcp_tool_config` |
| `scripts/delegate.py` | `--agent` choices (~L1552–1554) |
| `scripts/build/linear_pipeline.py` | `WRITER_CHOICES` L69–77, `WRITER_DEFAULTS` L78–89, `REVIEWER_CHOICES` L109–117, `REVIEWER_DEFAULTS` L118–126, `WRITER_SPECIFIC_DIRECTIVES` L96–107, `_runtime_tool_config` L3054–3162, `_ensure_cursor_writer_workspace` (new), `invoke_writer` L3204+ |
| `scripts/build/v7_build.py` | `WRITER_ALIASES` L34–42, `_reviewer_for_writer` L651–656, `_run_llm_qg` L663+ (use `REVIEWER_DEFAULTS`, not `WRITER_DEFAULTS` at L674) |
| `scripts/audit/checks/review_gaming.py` | `_model_family` L691–702 + exact-model fallback (**required** Phase 3) |

### Explicitly **not** requiring changes unless you touch them

- `WRITER_JSON_SCHEMAS` / `CORRECTION_PROMPT_BY_WRITER` — no cursor-specific schema changes expected
- `tests/build/test_config_tables.py` — activity configs, not writer agents
- Seminar-specific tests — **only** if Phase 3 accidentally changes shared reviewer defaults used in seminar builds (regression class from #2250 → #2253)

---

## Suggested PR split

| PR | Contents | LOC budget |
|----|----------|------------|
| **Phase 2** | `cursor.py` adapter, registry, `tool_config`, `delegate --agent cursor`, integration tests | ~250 LOC |
| **Phase 3** | `cursor-tools` in `WRITER_*` / `REVIEWER_*`, `_ensure_cursor_writer_workspace(module_dir)`, `_reviewer_for_writer`, `_runtime_tool_config(..., workspace_dir=module_dir)`, v7 aliases, **`_model_family` hardening (required)**, observability + dispatch tests | ~250 LOC |

**Pre-merge smoke (Phase 3):**

```bash
# venv symlinked from main checkout
.venv/bin/python scripts/build/v7_build.py a1 my-morning --dry-run --writer cursor-tools
.venv/bin/python -m pytest tests/test_v7_writer_dispatch.py tests/test_mcp_init_observability.py tests/test_writer_isolation.py tests/test_coverage_audit_pipeline.py::TestCheckCrossAgentReview tests/test_coverage_audit_pipeline.py::TestModelFamily -q
```

**Phase 3 merge gate:** same-model composer self-review test must fail in `test_coverage_audit_pipeline.py` before PR merges.

---

## Related docs

- [`2026-05-23-cursor-phase-1-bridge-gemini.md`](2026-05-23-cursor-phase-1-bridge-gemini.md) — Phase 1 bridge subcommand
- [`../agent-runtime-guide.md`](../agent-runtime-guide.md) — `runner.invoke()` mental model
- [`../../claude_extensions/rules/pipeline.md`](../../claude_extensions/rules/pipeline.md) — writer/reviewer policy
- [`../session-state/2026-05-23-judge-cal-leaderboard-cursor-wired-issues-sweep.md`](../session-state/2026-05-23-judge-cal-leaderboard-cursor-wired-issues-sweep.md) — cursor integration queue context
