#!/usr/bin/env python3
"""Wiki dimensional review orchestrator — `docs/design/dimensional-review.md`.

Runs the 4 LLM dimensional reviewers (source_grounding, factual_accuracy,
ukrainian_perspective, register) on a compiled wiki article in parallel,
merges their surgical `<fixes>` via the deterministic fix-merger, applies
patches, and optionally re-reviews.

Invariants enforced here:

- **§6a** Unified runtime. Every agent call goes through
  `scripts.agent_runtime.runner.invoke()`. No bespoke subprocesses.
- **§6c** No centralized LLM patcher. Fix resolution is deterministic
  (`review_merger.py`). Each reviewer emits only its own dim's fixes.
- **§6d** Per-dimension gate logic. ALL dims must pass (score ≥ min). No
  weighted averaging. First dim to fail sets `verdict=NEEDS_FIXES`.
- **§7 / §4c** Thresholds are TBD pending seeded benchmark. The
  `UNCALIBRATED_THRESHOLDS` constant below is a placeholder; the report
  carries `thresholds_calibrated: False` until Phase 3 data exists.
- **§8** Shadow-mode default. Orchestrator runs review and writes a
  report, but does NOT block the pipeline — gating is a downstream
  decision.

Usage::

    # Review one article (shadow mode, default)
    .venv/bin/python scripts/wiki/review.py \\
        --article wiki/grammar/b1/aspect.md

    # Override primary agents
    .venv/bin/python scripts/wiki/review.py \\
        --article wiki/grammar/b1/aspect.md \\
        --agent ukrainian_perspective=gemini

    # Hard-gate mode (raise non-zero on any dim failing)
    .venv/bin/python scripts/wiki/review.py \\
        --article wiki/grammar/b1/aspect.md \\
        --hard-gate
"""
from __future__ import annotations

import argparse
import functools
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Repo-root sys.path shim so this file runs standalone AND as a module.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from agent_runtime.errors import (
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from agent_runtime.runner import invoke
from wiki.config import PROMPTS_DIR, WIKI_DIR
from wiki.review_merger import (
    Fix,
    MergeReport,
    apply_fixes,
    merge_fixes,
)
from wiki.sources_schema import registry_path_for
from wiki.state import log_event

# ── Constants ──────────────────────────────────────────────────────

#: The four LLM dimensions. Order matters for report readability only.
DIMS: tuple[str, ...] = (
    "source_grounding",
    "factual_accuracy",
    "ukrainian_perspective",
    "register",
)

#: Default primary agent per dim (§3b). Pending seeded benchmark (§7b).
DEFAULT_PRIMARY: dict[str, str] = {
    "source_grounding": "codex",
    "factual_accuracy": "gemini",
    "ukrainian_perspective": "claude",
    "register": "gemini",
}

#: Fallback chain per dim. On primary failure (RateLimited, Timeout,
#: invalid JSON), orchestrator tries fallbacks in order. Resilience
#: requirement per user direction 2026-04-18 (§3b).
DEFAULT_FALLBACKS: dict[str, tuple[str, ...]] = {
    "source_grounding": ("claude", "gemini"),
    "factual_accuracy": ("claude", "codex"),
    "ukrainian_perspective": ("gemini",),
    "register": ("claude", "codex"),
}

#: Placeholder thresholds. §4c + §7b: real numbers come from seeded
#: benchmark. Report flags `thresholds_calibrated: False` until then.
UNCALIBRATED_THRESHOLDS: dict[str, int] = {
    "source_grounding": 8,
    "factual_accuracy": 8,
    "ukrainian_perspective": 8,
    "register": 8,
}

#: Prompt filenames (`.md`) per dim. Living at PROMPTS_DIR.
DIM_PROMPT_FILES: dict[str, str] = {
    "source_grounding": "review_source_grounding.md",
    "factual_accuracy": "review_factual_accuracy.md",
    "ukrainian_perspective": "review_ukrainian_perspective.md",
    "register": "review_register.md",
}

#: Project `.mcp.json` path — loaded for Claude tool-config. Relative to
#: repo root; callers running in a worktree should override or ensure
#: the worktree carries a `.mcp.json` symlink.
_MCP_CONFIG_PATH = _REPO_ROOT / ".mcp.json"

#: Max review rounds. ADR-001: if score doesn't improve, stop.
MAX_ROUNDS = 2

#: Per-call timeouts. Review prompts are bounded; 10 min is plenty.
HARD_TIMEOUT_S = 600

#: Verdicts a reviewer is allowed to emit. Anything else → treated as ERROR.
_VALID_VERDICTS: frozenset[str] = frozenset({"PASS", "REVISE", "REJECT"})

# ── Dataclasses ────────────────────────────────────────────────────


@dataclass
class Finding:
    """A single review finding from a dimensional reviewer."""

    location: str = ""
    quote: str = ""
    issue_type: str = ""
    severity: str = ""
    description: str = ""
    raw: dict = field(default_factory=dict)  # full finding dict


@dataclass
class DimResult:
    """One dimension's review outcome after one round."""

    dim: str
    agent: str
    model: str
    score: int
    verdict: str   # "PASS" | "REVISE" | "REJECT"
    findings: list[Finding]
    fixes: list[Fix]
    notes: str
    duration_s: float
    raw_response: str = ""
    error: str = ""  # empty if successful

    @property
    def ok(self) -> bool:
        return not self.error and self.verdict in ("PASS", "REVISE")


@dataclass
class RoundResult:
    round_num: int
    dim_results: dict[str, DimResult]
    merge_report: MergeReport | None = None
    article_text_after: str = ""


@dataclass
class ReviewReport:
    article_path: str
    rounds: list[RoundResult]
    final_verdict: str  # "PASS" | "NEEDS_FIXES" | "REJECT" | "ERROR"
    failing_dims: list[str]
    thresholds: dict[str, int]
    thresholds_calibrated: bool
    shadow_mode: bool
    started_at: float
    finished_at: float

    def to_jsonable(self) -> dict[str, Any]:
        """Return a JSON-serializable dict for on-disk persistence."""
        return {
            "article_path": self.article_path,
            "rounds": [
                {
                    "round": r.round_num,
                    "dims": {
                        dim: {
                            "agent": dr.agent,
                            "model": dr.model,
                            "score": dr.score,
                            "verdict": dr.verdict,
                            "findings_count": len(dr.findings),
                            "findings": [asdict(f) for f in dr.findings],
                            "fixes": [asdict(fx) for fx in dr.fixes],
                            "notes": dr.notes,
                            "duration_s": round(dr.duration_s, 2),
                            "error": dr.error,
                        }
                        for dim, dr in r.dim_results.items()
                    },
                    "merge": (
                        {
                            "applied_count": len(r.merge_report.applied),
                            "conflicts_count": len(r.merge_report.conflicts),
                            "applied": [asdict(f) for f in r.merge_report.applied],
                            "conflicts": [asdict(c) for c in r.merge_report.conflicts],
                            "skipped_missing": [
                                asdict(f) for f in r.merge_report.skipped_missing
                            ],
                        }
                        if r.merge_report is not None
                        else None
                    ),
                }
                for r in self.rounds
            ],
            "final_verdict": self.final_verdict,
            "failing_dims": self.failing_dims,
            "thresholds": self.thresholds,
            "thresholds_calibrated": self.thresholds_calibrated,
            "shadow_mode": self.shadow_mode,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_s": round(self.finished_at - self.started_at, 2),
        }


# ── Tool-config per agent (§3b dim 1+4 need MCP) ───────────────────


def _tool_config_for(agent: str, *, needs_mcp: bool) -> dict | None:
    """Build per-agent tool_config enabling MCP `sources` server.

    Shapes differ per adapter (see `scripts/agent_runtime/adapters/`):
      - Claude: `{"mcp_config_path": ".mcp.json", "allowed_tools": "..."}`
      - Gemini: `{"mcp_server_names": ["sources"]}`
      - Codex : `{"mcp_servers": {"sources": {"command": ..., "args": ...}}}`

    For factual_accuracy + register dims, MCP access is required — agents
    unable to serve MCP reviews must be skipped in favor of fallback.
    """
    if not needs_mcp:
        return None

    if agent == "claude":
        if not _MCP_CONFIG_PATH.exists():
            return None
        return {
            "mcp_config_path": str(_MCP_CONFIG_PATH),
            "allowed_tools": "mcp__sources__*",
        }

    if agent == "gemini":
        return {"mcp_server_names": ["sources"]}

    if agent == "codex":
        # Codex MCP via #1325 adapter fix — requires the sources server be
        # reachable (SSE 127.0.0.1:8766). Shape: nested mcp_servers dict.
        mcp = _load_mcp_config_for_codex()
        return {"mcp_servers": mcp} if mcp else None

    return None


@functools.lru_cache(maxsize=1)
def _load_mcp_config_for_codex() -> dict | None:
    """Translate repo .mcp.json → Codex's `-c mcp_servers.<k>=<v>` shape.

    Cached for process lifetime: `.mcp.json` is immutable during a
    review run; reading it per (round × dim × fallback) burned file I/O
    for no benefit.
    """
    if not _MCP_CONFIG_PATH.exists():
        return None
    try:
        data = json.loads(_MCP_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("mcpServers") or None


def _dim_needs_mcp(dim: str) -> bool:
    """Which dims REQUIRE live MCP access per the prompt contracts."""
    return dim in ("factual_accuracy", "register")


# ── Prompt assembly ────────────────────────────────────────────────


@functools.lru_cache(maxsize=len(DIM_PROMPT_FILES))
def _read_prompt_template(dim: str) -> str:
    """Prompt templates are static per-process — cache the file read."""
    path = PROMPTS_DIR / DIM_PROMPT_FILES[dim]
    return path.read_text(encoding="utf-8")


def _build_sources_block(article_path: Path) -> tuple[str, str]:
    """Load sibling sources YAML + raw chunk text for the prompt.

    Returns (sources_yaml_text, source_chunks_text).

    For dims that don't need source chunks inline (factual_accuracy,
    ukrainian_perspective, register), the chunks block is still passed
    but may be empty — reviewers that don't need it will ignore it per
    the prompt contract.
    """
    registry_path = registry_path_for(article_path)
    sources_yaml = (
        registry_path.read_text(encoding="utf-8")
        if registry_path.exists()
        else "# (no sibling sources file found)\n"
    )
    # Chunk retrieval against sources.db / external corpus is deferred
    # per design §3a (Phase 2 ships with YAML registry only). The
    # source_grounding reviewer handles a missing chunks block gracefully:
    # findings fall back to STALE_CITATION rather than OVERCLAIM when the
    # cited chunk text isn't resolvable. Calibration (Phase 3) will drive
    # whether live chunk loading is worth wiring.
    chunks_text = "# (source chunks not inlined in this build — sibling YAML only)\n"
    return sources_yaml, chunks_text


def _assemble_prompt(dim: str, article_path: Path, article_text: str) -> str:
    """Fill the prompt template with article + metadata + sources."""
    template = _read_prompt_template(dim)
    sources_yaml, source_chunks = _build_sources_block(article_path)

    # Domain is the path-parent under wiki/
    try:
        rel = article_path.relative_to(WIKI_DIR)
        domain = "/".join(rel.parts[:-1]) or "root"
    except ValueError:
        domain = "unknown"

    slug = article_path.stem
    # Level is best-effort inferred from domain prefix; orchestrator
    # does not require strict mapping. Reviewers use it for calibration
    # (register dim especially).
    level = _infer_level_from_domain(domain)

    substitutions = {
        "{ARTICLE_CONTENT}": article_text,
        "{SOURCES_YAML}": sources_yaml,
        "{SOURCE_CHUNKS}": source_chunks,
        "{SLUG}": slug,
        "{LEVEL}": level,
        "{DOMAIN}": domain,
    }
    out = template
    for placeholder, value in substitutions.items():
        out = out.replace(placeholder, value)
    return out


_LEVEL_FROM_DOMAIN = re.compile(r"(a1|a2|b1|b2|c1|c2)", re.IGNORECASE)


def _infer_level_from_domain(domain: str) -> str:
    match = _LEVEL_FROM_DOMAIN.search(domain)
    if match:
        return match.group(1).upper()
    # Seminar domains have no level
    return "seminar"


# ── Response parsing ───────────────────────────────────────────────


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_object(response: str) -> dict:
    """Pull the JSON object out of an agent response.

    Reviewers are instructed to emit bare JSON (no markdown fence, no
    preamble). Real-world CLIs sometimes ignore that. We strip a single
    leading fence and fall back to regex extraction.
    """
    text = response.strip()
    if text.startswith("```"):
        # Strip ```json … ``` fencing
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = _JSON_OBJECT_RE.search(response)
    if not match:
        raise ValueError("no JSON object found in reviewer response")
    return json.loads(match.group(0))


def _parse_dim_result(
    *,
    dim: str,
    agent: str,
    model: str,
    response: str,
    duration_s: float,
) -> DimResult:
    """Parse a reviewer's JSON response into a DimResult."""
    payload = _extract_json_object(response)

    # All four prompts share: dimension, findings[], fixes[], score,
    # verdict, notes. ukrainian_perspective adds strengths[] (ignored
    # for gating purposes; preserved in raw_response).
    findings_raw = payload.get("findings") or []
    findings = [
        Finding(
            location=str(f.get("location", "")),
            quote=str(
                f.get("claim_quote")
                or f.get("framing_quote")
                or f.get("quote", "")
            ),
            issue_type=str(f.get("issue_type", "")),
            severity=str(f.get("severity", "")),
            description=str(f.get("issue_description", "")),
            raw=f if isinstance(f, dict) else {},
        )
        for f in findings_raw
        if isinstance(f, dict)
    ]

    fixes_raw = payload.get("fixes") or []
    fixes = [
        Fix(dim=dim, find=str(f["find"]), replace=str(f.get("replace", "")))
        for f in fixes_raw
        if isinstance(f, dict) and f.get("find")
    ]

    score_val = payload.get("score", 0)
    try:
        score = int(score_val)
    except (TypeError, ValueError):
        score = 0

    verdict = str(payload.get("verdict", "REVISE")).upper()
    if verdict not in _VALID_VERDICTS:
        # Defensive: a reviewer going off-script shouldn't flow into
        # the gate logic with a verdict string nobody checks. Treat
        # unknown verdicts as ERROR so they surface in _failing_dims.
        return DimResult(
            dim=dim, agent=agent, model=model, score=0,
            verdict="ERROR", findings=findings, fixes=fixes, notes="",
            duration_s=duration_s, raw_response=response,
            error=f"reviewer emitted invalid verdict: {verdict!r}",
        )
    notes = str(payload.get("notes", ""))

    return DimResult(
        dim=dim,
        agent=agent,
        model=model,
        score=score,
        verdict=verdict,
        findings=findings,
        fixes=fixes,
        notes=notes,
        duration_s=duration_s,
        raw_response=response,
    )


# ── Single-dim runner with fallback chain ──────────────────────────


def _run_single_dim(
    *,
    dim: str,
    article_path: Path,
    article_text: str,
    primary: str,
    fallbacks: tuple[str, ...],
    cwd: Path,
) -> DimResult:
    """Run one dim; on primary failure, try fallbacks in order.

    Failures that trigger fallover:
      - `RateLimitedError` (hit headroom / provider)
      - `AgentTimeoutError` (hit HARD_TIMEOUT_S)
      - `AgentUnavailableError` (CLI missing, adapter import failed)
      - `ValueError` from JSON parse (reviewer emitted garbage)

    On total exhaustion, returns a DimResult with `error` populated and
    `verdict="ERROR"`.
    """
    agents_to_try = (primary, *fallbacks)
    needs_mcp = _dim_needs_mcp(dim)
    last_error = ""

    for agent in agents_to_try:
        tool_config = _tool_config_for(agent, needs_mcp=needs_mcp)
        if needs_mcp and tool_config is None:
            # Agent can't serve MCP-requiring dim — skip silently
            last_error = f"{agent}: MCP required but unavailable"
            continue

        prompt = _assemble_prompt(dim, article_path, article_text)
        start = time.monotonic()
        try:
            result = invoke(
                agent,
                prompt,
                mode="read-only",
                cwd=cwd,
                tool_config=tool_config,
                entrypoint="runtime",
                hard_timeout=HARD_TIMEOUT_S,
                task_id=f"wiki-review-{dim}-{article_path.stem}",
            )
        except (RateLimitedError, AgentTimeoutError, AgentUnavailableError) as exc:
            last_error = f"{agent}: {type(exc).__name__}: {exc}"
            continue
        except Exception as exc:  # defensive: any subprocess layer surprise
            last_error = f"{agent}: unexpected {type(exc).__name__}: {exc}"
            continue

        if not result.ok or not result.response:
            last_error = f"{agent}: invoke returned !ok ({result.stderr_excerpt})"
            continue

        duration = time.monotonic() - start
        try:
            return _parse_dim_result(
                dim=dim,
                agent=agent,
                model=result.model,
                response=result.response,
                duration_s=duration,
            )
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = f"{agent}: parse error: {exc}"
            continue

    # All agents exhausted
    return DimResult(
        dim=dim,
        agent=agents_to_try[0],
        model="",
        score=0,
        verdict="ERROR",
        findings=[],
        fixes=[],
        notes="",
        duration_s=0.0,
        error=last_error or "no agents attempted",
    )


# ── Parallel round ─────────────────────────────────────────────────


def _run_round(
    *,
    article_path: Path,
    article_text: str,
    agent_overrides: dict[str, str],
    cwd: Path,
) -> dict[str, DimResult]:
    """Fire all 4 dim reviews in parallel via ThreadPoolExecutor.

    §6b note: wiki only has 1 Claude-assigned dim (ukrainian_perspective).
    Cache prewarm-then-fan-out is N/A here (only 1 Claude call). True
    parallel fan-out on 4 subprocesses is fine — each adapter runs its
    own CLI process; threads just wait on subprocess completion.
    """
    results: dict[str, DimResult] = {}
    with ThreadPoolExecutor(max_workers=len(DIMS)) as pool:
        futures = {
            pool.submit(
                _run_single_dim,
                dim=dim,
                article_path=article_path,
                article_text=article_text,
                primary=agent_overrides.get(dim, DEFAULT_PRIMARY[dim]),
                fallbacks=DEFAULT_FALLBACKS[dim],
                cwd=cwd,
            ): dim
            for dim in DIMS
        }
        for future in as_completed(futures):
            dim = futures[future]
            # _run_single_dim swallows all per-agent exceptions and always
            # returns a DimResult — the outer catch is belt-and-suspenders
            # for a hypothetical future bug that lets one escape. Keeping
            # it guarantees every dim gets a result entry for _failing_dims.
            try:
                results[dim] = future.result()
            except Exception as exc:  # pragma: no cover
                results[dim] = DimResult(
                    dim=dim, agent="?", model="", score=0, verdict="ERROR",
                    findings=[], fixes=[], notes="", duration_s=0.0,
                    error=f"executor raised: {type(exc).__name__}: {exc}",
                )
    return results


# ── Orchestrator ──────────────────────────────────────────────────


def review_article(
    article_path: Path,
    *,
    agent_overrides: dict[str, str] | None = None,
    thresholds: dict[str, int] | None = None,
    max_rounds: int = MAX_ROUNDS,
    shadow_mode: bool = True,
    cwd: Path | None = None,
) -> tuple[ReviewReport, str]:
    """Run dimensional review on one article.

    Returns `(report, final_article_text)`. In shadow mode, fixes are
    still applied to an in-memory copy for the round-2 re-review, but
    the on-disk article is NOT touched — callers decide when to promote
    in-memory edits to disk.
    """
    if agent_overrides is None:
        agent_overrides = {}
    if thresholds is None:
        thresholds = dict(UNCALIBRATED_THRESHOLDS)
    if cwd is None:
        cwd = _REPO_ROOT

    started_at = time.time()
    article_text = article_path.read_text(encoding="utf-8")
    rounds: list[RoundResult] = []

    current_text = article_text
    for round_num in range(1, max_rounds + 1):
        dim_results = _run_round(
            article_path=article_path,
            article_text=current_text,
            agent_overrides=agent_overrides,
            cwd=cwd,
        )

        all_fixes: list[Fix] = []
        for dr in dim_results.values():
            all_fixes.extend(dr.fixes)

        merge_report = merge_fixes(all_fixes, current_text)
        new_text = apply_fixes(current_text, merge_report.applied)

        round_result = RoundResult(
            round_num=round_num,
            dim_results=dim_results,
            merge_report=merge_report,
            article_text_after=new_text,
        )
        rounds.append(round_result)

        # Stop if all dims PASS on threshold — no more rounds needed
        failing_now = _failing_dims(dim_results, thresholds)
        if not failing_now:
            break

        # Stop if no fixes were applied this round — more rounds won't help
        if not merge_report.applied:
            break

        # ADR-001 guard: if round N+1 scores are lower, stop.
        if round_num > 1:
            prev = rounds[-2].dim_results
            if _scores_regressed(prev, dim_results):
                break

        current_text = new_text

    # Compute final verdict on the last round's dim_results
    final_dim_results = rounds[-1].dim_results
    failing = _failing_dims(final_dim_results, thresholds)
    final_verdict = _final_verdict(final_dim_results, failing)

    finished_at = time.time()
    report = ReviewReport(
        article_path=str(article_path),
        rounds=rounds,
        final_verdict=final_verdict,
        failing_dims=failing,
        thresholds=thresholds,
        thresholds_calibrated=False,
        shadow_mode=shadow_mode,
        started_at=started_at,
        finished_at=finished_at,
    )
    return report, rounds[-1].article_text_after


def _failing_dims(
    dim_results: dict[str, DimResult],
    thresholds: dict[str, int],
) -> list[str]:
    """Return dims below their threshold OR with verdict REJECT/ERROR."""
    failing: list[str] = []
    for dim, dr in dim_results.items():
        if dr.verdict == "ERROR":
            failing.append(dim)
            continue
        if dr.verdict == "REJECT":
            failing.append(dim)
            continue
        if dr.score < thresholds.get(dim, 8):
            failing.append(dim)
    return failing


def _scores_regressed(
    prev: dict[str, DimResult],
    curr: dict[str, DimResult],
) -> bool:
    """True iff ANY dim's score dropped round-over-round (ADR-001)."""
    return any(
        dim in prev and dr.score < prev[dim].score
        for dim, dr in curr.items()
    )


def _final_verdict(
    dim_results: dict[str, DimResult],
    failing: list[str],
) -> str:
    """Compose the overall verdict (§6d)."""
    if any(dr.verdict == "ERROR" for dr in dim_results.values()):
        return "ERROR"
    if any(dr.verdict == "REJECT" for dr in dim_results.values()):
        return "REJECT"
    if failing:
        return "NEEDS_FIXES"
    return "PASS"


# ── Report persistence ─────────────────────────────────────────────


def _reports_dir_for(article_path: Path) -> Path:
    """Mirror the article's wiki/ subpath under wiki/.reviews/."""
    try:
        rel = article_path.relative_to(WIKI_DIR)
    except ValueError:
        rel = Path(article_path.name)
    reports_dir = WIKI_DIR / ".reviews" / rel.parent
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def write_report(report: ReviewReport, article_path: Path) -> Path:
    """Persist the review report as JSON next to the mirrored article key."""
    reports_dir = _reports_dir_for(article_path)
    out_path = reports_dir / f"{article_path.stem}.json"
    out_path.write_text(
        json.dumps(report.to_jsonable(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path


# ── CLI ────────────────────────────────────────────────────────────


def _parse_agent_overrides(pairs: list[str]) -> dict[str, str]:
    """Parse `--agent dim=agent` CLI pairs."""
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--agent expects dim=agent, got: {pair!r}")
        dim, agent = pair.split("=", 1)
        if dim not in DIMS:
            raise SystemExit(
                f"--agent unknown dim {dim!r}. Known: {', '.join(DIMS)}"
            )
        out[dim] = agent
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument(
        "--article",
        required=True,
        help="Path to wiki article .md file",
    )
    parser.add_argument(
        "--agent",
        action="append",
        default=[],
        metavar="DIM=AGENT",
        help=f"Override primary agent for a dim. DIM ∈ {{{', '.join(DIMS)}}}. "
             f"May be given multiple times.",
    )
    parser.add_argument(
        "--hard-gate",
        action="store_true",
        help="Exit nonzero if any dim below threshold (default: shadow mode, always exit 0)",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=MAX_ROUNDS,
        help=f"Max review rounds (default {MAX_ROUNDS})",
    )
    parser.add_argument(
        "--threshold",
        action="append",
        default=[],
        metavar="DIM=N",
        help="Override threshold for a dim (default 8). NOT calibrated (§7b).",
    )
    args = parser.parse_args(argv)

    article_path = Path(args.article).resolve()
    if not article_path.exists():
        print(f"error: article not found: {article_path}", file=sys.stderr)
        return 2

    overrides = _parse_agent_overrides(args.agent)
    thresholds = dict(UNCALIBRATED_THRESHOLDS)
    for pair in args.threshold:
        if "=" not in pair:
            raise SystemExit(f"--threshold expects dim=N, got: {pair!r}")
        dim, num = pair.split("=", 1)
        thresholds[dim] = int(num)

    if args.hard_gate:
        # Prominent warning — `UNCALIBRATED_THRESHOLDS` defaults to 8 for
        # every dim but NO real seeded-benchmark data backs that. Using
        # --hard-gate before Phase 3 calibration can brick builds on
        # borderline scores. Keep the orchestrator honest: shout it.
        # Surfaced in adversarial review 2026-04-18.
        print(
            "⚠️  --hard-gate WITH UNCALIBRATED THRESHOLDS: the per-dim minimum\n"
            "    is a placeholder (8) pending Phase 3 seeded-benchmark\n"
            "    calibration (§7b). A reviewer scoring 7.9 on genuinely-clean\n"
            "    content will block the pipeline. Prefer shadow mode until\n"
            "    thresholds_calibrated flips to True.\n",
            file=sys.stderr,
        )

    report, _ = review_article(
        article_path,
        agent_overrides=overrides,
        thresholds=thresholds,
        max_rounds=args.max_rounds,
        shadow_mode=not args.hard_gate,
    )
    out_path = write_report(report, article_path)

    log_event(
        track=_infer_level_from_domain(
            str(article_path.relative_to(WIKI_DIR).parent)
            if WIKI_DIR in article_path.parents
            else "unknown"
        ).lower(),
        slug=article_path.stem,
        event="dim_review",
        verdict=report.final_verdict,
        failing_dims=report.failing_dims,
        shadow_mode=report.shadow_mode,
        report=str(out_path),
    )

    print(json.dumps({
        "article": str(article_path),
        "verdict": report.final_verdict,
        "failing_dims": report.failing_dims,
        "rounds": len(report.rounds),
        "report_file": str(out_path),
    }, indent=2, ensure_ascii=False))

    if args.hard_gate and report.final_verdict != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
