"""Prompt additions ported from delegate.py 11366-11443 and 11566-11606."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

from scripts.lib import rules_core


class _PromptPath(type(Path())):
    """Let builders read submitted bytes while dry-run leaves the filesystem untouched."""

    def read_bytes(self):
        return self.content

    def read_text(self, encoding=None, errors=None):
        return self.content.decode(encoding or "utf-8", errors or "strict")


_REPO_ROOT = Path(__file__).resolve().parents[2]

def _load_task_lifecycle_carrier(raw_path: str | None) -> tuple[dict[str, Any] | None, str]:
    """Validate one canonical lifecycle ledger before dispatch side effects."""
    if not raw_path:
        return None, ""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.orchestration import task_lifecycle

    path = Path(raw_path).expanduser().resolve()
    ledger = task_lifecycle.load_lifecycle(path)
    carrier = task_lifecycle.carrier_projection(ledger, state_file=str(path))
    return carrier, task_lifecycle.render_carrier_prompt(carrier)


class ResearchContextError(ValueError):
    """A --research-* flag violated a request-side bound (mirrors the API 422s)."""


def _build_research_context(args: argparse.Namespace):
    """Return a normalized research ``Context`` from the explicit --research-* flags.

    Returns ``None`` when no flag was given (the no-flags path stays byte-identical
    to a pre-P3 dispatch). Never infers a value from the prompt, agent, provider, or
    branch — ADR-011 P3 requires explicit dimensions and fails closed on the rest.
    Validates the same request-side caps the FastAPI query layer enforces so a
    direct CLI caller cannot smuggle an oversize/over-count context past the API.
    """
    role = getattr(args, "research_role", None)
    family = getattr(args, "research_task_family", None)
    track = getattr(args, "research_track", None)
    owned = getattr(args, "research_owned_path", None) or []
    if not (role or family or track or owned):
        return None

    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.research import registry as reg

    for label, value in (
        ("--research-role", role),
        ("--research-task-family", family),
        ("--research-track", track),
    ):
        if value is not None and len(value) > reg.MAX_QUERY_VALUE_LEN:
            raise ResearchContextError(f"{label} value too long (max {reg.MAX_QUERY_VALUE_LEN} chars)")
    if len(owned) > reg.MAX_OWNED_PATHS:
        raise ResearchContextError(f"too many --research-owned-path values ({len(owned)} > {reg.MAX_OWNED_PATHS})")
    for path in owned:
        if len(path) > reg.MAX_OWNED_PATH_LEN:
            raise ResearchContextError(f"--research-owned-path value too long (max {reg.MAX_OWNED_PATH_LEN} chars)")
    return reg.normalize_context(role, family, track, owned)


def _render_research_prompt_block(pointers: list[dict[str, Any]]) -> str:
    """Render the bounded, POINTER-ONLY research block appended to a delegated prompt.

    Never contains a digest body/summary/source — only ids, states, and content
    hashes plus the on-demand fetch instruction. The pointer set is already capped
    (top-5 / ≤1.5 KB) by the selector.
    """
    lines = [
        "",
        "[project research pointers — ADR-011 P3]",
        "These research-registry records match this task's context. Bodies are NOT",
        "included; fetch one on demand only if you need it:",
        "  GET /api/knowledge/record/{id}?task={your-task-id}",
    ]
    for ptr in pointers:
        lines.append(f"- {ptr['id']} [{ptr['state']}] content_hash={ptr['content_hash']}")
    lines.append("")
    return "\n".join(lines)


def _with_optional_research_state(state: dict[str, Any], research_state: dict[str, Any] | None) -> dict[str, Any]:
    """Add ``"research"`` to ``state`` only when ``research_state`` is non-``None``.

    ADR-011 P3 default-compatibility: a no-flags dispatch, a disabled registry, or
    a degraded/failed injection must persist byte-identical pre-P3 state — the key
    is OMITTED, never present as ``"research": null``. Pointer ids / filtered ETag
    / dropped ids / context fingerprint only when present — never raw owned paths,
    digest/source/prompt text, role, or task family.
    """
    if research_state is not None:
        state["research"] = research_state
    return state


def _resolve_research_injection(ctx, task_id: str) -> tuple[str, dict[str, Any] | None]:
    """Fail-open pointer resolution for a dispatch context.

    Returns ``(prompt_block, persist_state)``. ``persist_state`` records ONLY the
    pointer ids, filtered projection ETag, dropped ids, and a context fingerprint —
    never raw owned paths, digest/source/prompt text, role, or task family. Any
    disabled/malformed/unexpected registry condition degrades to ``("", None)`` so a
    dispatch is never blocked by the research surface. Emits one surface (not
    consumption) telemetry event per injected pointer, attributed to ``task_id``.
    """
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.research import consumption
    from scripts.research import registry as reg

    try:
        if not reg.is_enabled(root=_REPO_ROOT):
            return "", None
        runtime = reg.load_runtime_safe(root=_REPO_ROOT)
        if runtime is None:
            return "", None
        pointers, dropped = reg.select_pointers(runtime, ctx)
        etag = reg.filtered_manifest(runtime, ctx).etag_hex
        persist_state = {
            "pointer_ids": [ptr["id"] for ptr in pointers],
            "filtered_etag": etag,
            "dropped_ids": list(dropped),
            "context_fingerprint": reg.context_fingerprint(ctx),
        }
        if not pointers:
            return "", persist_state
        for ptr in pointers:
            consumption.emit_surface(
                research_id=ptr["id"],
                surface=consumption.SURFACE_DISPATCH,
                task_id=task_id,
            )
        return _render_research_prompt_block(pointers), persist_state
    except Exception as exc:  # fail-open: research never blocks a dispatch
        print(
            f"[delegate] WARNING: research pointer injection skipped: {type(exc).__name__}",
            file=sys.stderr,
        )
        return "", None


def lifecycle(args):
    try:
        carrier, block = _load_task_lifecycle_carrier(args.lifecycle_file)
        if carrier is not None and args.mode == 'workspace-write':
            from scripts.orchestration.task_identity import _github_url

            identity = carrier['identity']
            for url_key, number_key in (
                ('github_issue_url', 'github_issue_number'), ('stream_epic_url', 'stream_epic'),
            ):
                if identity[url_key] != _github_url(identity['repository'], 'issues', identity[number_key]):
                    raise ValueError(f'{url_key} does not match the repository and exact number')
        return carrier, block
    except (OSError, ValueError) as exc:
        raise ValueError(f'invalid --lifecycle-file: {exc}') from exc


def effective(args, task_id, prompt, lifecycle_block):
    ctx = _build_research_context(args)
    block, research = _resolve_research_injection(ctx, task_id) if ctx is not None else ('', None)
    text = prompt.decode('utf-8') + lifecycle_block + block
    cored = rules_core.with_core(text, args.rules_seat)
    fields = {'effective_prompt_sha256': hashlib.sha256(cored.encode('utf-8')).hexdigest(),
              'prompt_blocks': (['rules_core'] if cored != text else [])
              + (['lifecycle'] if lifecycle_block else []) + (['research'] if block else [])}
    return cored.encode('utf-8'), _with_optional_research_state(fields, research)
