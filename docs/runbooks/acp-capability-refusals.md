# ACP capability refusals

Ordinary `ask-*` calls use ACP shadow adapters. Native implementation dispatch
and toolful review calls use separate adapters. A failed ACP prerequisite does
not establish that native dispatch is unavailable.

Before choosing an ordinary ask lane, request the ACP routing snapshot:

```bash
curl -fsS 'http://localhost:8765/api/state/routing-budget?transport=acp'
/home/ops/learn-ukrainian/.venv/bin/python -m scripts.fleet.capacity_pick --transport acp --strict
```

The default routing snapshot and capacity picker remain scoped to native
`dispatch`; responses identify their `transport`. The ACP snapshot runs only
version/help checks, preserves native health as `dispatch_health`, and exposes
`health.scope=acp_cli_compatibility`. `eligible=false` excludes a lane from ACP
recommendations and numbered picks, including when every ACP lane is excluded.
An unavailable probe is unknown and ineligible. A successful compatibility
probe proves command compatibility, not provider authentication or quota.

Diagnose the first prerequisite error, not just the final missing command:

- `node_runtime_unavailable`: no installed Node runtime matches the repository
  `.nvmrc` contract. The adapter preserves this refusal instead of misreporting
  missing `root help`, `codex exec`, or provider `acp` capabilities.
- `cli_incompatible`: the resolved project-local ACPX or provider command does
  not expose the required flags. ACPX requires `json-one-shot-v1`; AGY requires
  `text-plan-sandbox-v1`; OpenCode-backed seats require `native-acp-pure-v1`.
- `adapter_refused`: another adapter prerequisite, such as a missing binary or
  pinned wrapper, failed. The ask command supplies the actionable stderr.

Inspect the resolved project-local dependency, not a global `acpx` on PATH.
Versions are telemetry; admission still requires the actual command surface.
Provisioning the required runtime or compatible CLI is an operator environment
action. Do not relax confinement flags or switch transports to conceal failure.
Each ACP snapshot probes again, so repaired dependencies can recover without
waiting for historical failure records to expire. Verify recovery with a bounded
ordinary ask and inspect its response before claiming the provider works.

Related: #7812. Ask parser option consistency is tracked separately in #7814.
