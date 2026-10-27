"""Native Grok transport, reusing the legacy permissions and terminal parser."""

from dataclasses import dataclass, replace

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.grok_build import GrokBuildAdapter
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec


@dataclass(frozen=True)
class GrokInvocation(Invocation):
    adapter: GrokBuildAdapter
    plan: InvocationPlan

    def cleanup(self) -> None:
        self.adapter.cleanup_invocation(self.plan)

    def liveness_paths(self):
        return self.adapter.liveness_signal_paths(self.plan)

    def parse(self, stdout, stderr, returncode, final_text) -> ParsedResult:
        return parse(stdout, stderr, returncode, final_text, adapter=self.adapter, plan=self.plan)


@dataclass(frozen=True)
class GrokResult(ParsedResult):
    failure_code: str | None = None
    rate_limited: bool = False


def build(spec: TaskSpec, env: dict[str, str]) -> GrokInvocation:
    # The Cursor wire pin denotes the same model at high effort, never a route.
    model, effort = spec.model, spec.effort
    if model == "grok-4.7-high":
        model, effort = "grok-4.7", effort or "high"
    adapter = GrokBuildAdapter()
    plan = adapter.build_invocation(
        prompt=spec.prompt_file.read_text(encoding="utf-8"), mode=spec.mode,
        cwd=spec.worktree, model=model, effort=effort, task_id=spec.task_id,
        session_id=None, tool_config={"reviewer_tools": True} if spec.mode == "read-only" else {},
    )
    # Bind session lookups and permission-cancellation evidence to the child home.
    plan = replace(plan, env_overrides={**env, **plan.env_overrides})
    invocation = GrokInvocation(plan.cmd, plan.stdin_payload.encode(), dict(plan.env_overrides),
                                plan.output_file, adapter, plan)
    if spec.options.get("dry_run") == "True":
        invocation.cleanup()
    return invocation


def parse(stdout, stderr, returncode, final_text, *, adapter=None, plan=None) -> ParsedResult:
    result = (adapter or GrokBuildAdapter()).parse_response(
        stdout=stdout, stderr=stderr, returncode=returncode, output_file=None, plan=plan,
    )
    identity = result.substitution or {}
    error = None if result.ok else result.stderr_excerpt or result.failure_code or "grok: provider failed"
    return GrokResult(result.response or None, None, error, identity.get("actual_model"),
                      result.failure_code, result.rate_limited)
