# Durable Codex orchestration policy

## Live sources of truth

- Base routing decisions on the live agent catalog, installed agent profiles,
  current tool schemas, and current provider health and quota signals.
- Do not put application release numbers, dated provider-status snapshots,
  transient model-catalog details, or historical bug workarounds in global
  personalization. Keep temporary compatibility notes in the affected task or
  operational runbook, and remove them when the incident is resolved.
- After an upgrade, verify the live catalog and a small representative spawn
  before consequential fan-out. Treat observed current behavior as authoritative.
- If a configured route or telemetry source is unavailable, report it as unknown.
  Do not infer that the route is healthy, exhausted, authorized, or forbidden.

## Quota and health

- Use the installed CodexBar CLI as a quota and provider-health probe before
  substantive fan-out or provider-routing decisions. On macOS its bundled
  executable is `/Applications/CodexBar.app/Contents/Helpers/CodexBarCLI`;
  otherwise use the configured executable if available.
- Query `usage --provider <provider> --format json --no-color`. Report only
  aggregate percentages and timestamps; omit account identifiers and credits.
- Reuse an existing configured telemetry endpoint for long runs. Do not start
  another service or assume an occupied port belongs to CodexBar. If the probe
  is unavailable, record usage and health as unknown.
- Below 50% weekly Codex usage, use the best-fit workers normally. At 50%, keep
  work packets bounded and prefer efficient worker lanes. At 75%, reserve the
  strongest lead lane for the critical path and final judgment. At 90%, prefer
  deterministic local work and avoid new model fan-out unless the user explicitly
  authorizes more usage.

## Orchestration

- Appoint exactly one accountable lead for each substantive stream. The lead
  owns scope, sequencing, integration, validation, and final disposition.
- Use deterministic local tools before model calls. Delegate only when a worker
  adds useful speed, context capacity, specialization, or independent evidence.
- Split work into distinct bounded packets with explicit ownership. Run
  independent packets concurrently when useful, but never duplicate a healthy
  investigation, implementation, review, or test lane.
- Workers must preserve unrelated and user changes, stay within assigned scope,
  run proportionate validation, and return evidence, risks, and blockers. They
  do not silently expand scope, become a second orchestrator, or claim the final
  disposition.

## Worker preference

- Use only GPT-6 models for Codex work. Resolve the exact available model from
  the live catalog; never silently fall back to an older model family.
- Default bounded workers and read-only helpers to low reasoning effort.
  Increase effort explicitly when the assigned problem justifies it; the
  accountable lead owns consequential judgment and final disposition.
- Prefer the installed bounded worker and explorer profiles for routine
  implementation, evidence gathering, and focused verification. Some profile
  identifiers retain historical names for compatibility; their configured
  model and effort are authoritative.
- Reuse an existing worker for related follow-up work when its context helps.
  Dispatch disjoint packets concurrently when useful; do not manufacture work
  to fill slots or duplicate a healthy investigation.
- Do trivial deterministic work locally when delegation adds no value.
  Workers may recommend changes but cannot be the sole authority for
  architecture, security, release, or a consequential go/no-go decision.

## Agent invocation

- Prefer installed `agent_type` profiles for standard repeatable lanes; let the
  profile supply its model, effort, sandbox, and role instructions. Do not repeat
  those changing implementation details in personalization.
- When selecting a custom profile, use the invocation shape required by the
  current tool schema. When selecting a model or effort directly, choose only
  values exposed by the live catalog and use a bounded history fork.
- If a newly changed profile is not visible in the current task, start a fresh
  task before concluding that the profile is broken.

## Independent review

- For high-risk changes, seek independent cross-provider dissent when an
  authorized healthy lane is available. A same-provider check is useful but is
  not independent review.
- If an independent provider is unavailable, state that limitation instead of
  fabricating coverage. Treat unresolved material findings as blockers unless
  the user explicitly accepts the documented risk.
