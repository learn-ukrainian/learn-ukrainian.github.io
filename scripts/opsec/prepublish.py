"""Prevent accidental disclosure by cooperative agents before public GitHub writes.

Defense in depth, not universal enforcement: absolute gh paths, aliases,
extensions and raw HTTP clients can bypass shell interception. Direct project
publishers must call checked_run. The private matcher owns all matching logic;
this module owns destination admission, blocking policy and masked diagnostics.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
POLICY = Path(__file__).with_name("blocking.json")


class PublishBlocked(RuntimeError):
    """A safe diagnostic, with no source text or private exception detail."""


def publication_boundary(error_type):
    """Translate a safe policy refusal to a publisher's established typed failure."""

    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except PublishBlocked as exc:
                raise error_type(f"publish_blocked: {exc}") from None

        return wrapped

    return decorate


def publication_cli(*error_types):
    """Render publishing failures at CLI boundaries without a traceback."""

    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except (PublishBlocked, *error_types) as exc:
                print(f"publish_blocked: {exc}", file=sys.stderr)
                return 2

        return wrapped

    return decorate


def primary_root(cwd: Path = ROOT) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if result.returncode:
        raise PublishBlocked("OPSEC: repository context unavailable; use an explicit repository.")
    return Path(result.stdout.strip()).parent


def catalog() -> dict:
    import yaml

    try:
        return yaml.safe_load((ROOT / "scripts/config/fleet_repos.yaml").read_text())["repos"]
    except Exception:
        raise PublishBlocked("OPSEC: repository allowlist unavailable; write refused.") from None


def normalize_repository(value: str, host: str = "github.com") -> str:
    """Return a canonical host/owner/name, or unknown (never private by default)."""
    value = value.strip().removesuffix(".git")
    value = re.sub(r"^git@([^:]+):", r"\1/", value)
    value = re.sub(r"^https?://", "", value)
    parts = value.split("/")
    if len(parts) == 2:
        parts.insert(0, host.lower())
    if len(parts) >= 3 and all(re.fullmatch(r"[A-Za-z0-9_.-]+", x) for x in parts[:3]):
        return "/".join(parts[:3]).lower()
    return "unknown"


def is_private(destination: str) -> bool:
    return any(
        str(row.get("role", "")).startswith("private-")
        and not row.get("default")
        and normalize_repository(row["github"]) == destination
        for row in catalog().values()
    )


def private_tooling() -> Path:
    return primary_root().parent / catalog()["infra-private"]["local_name"] / "tools/public_opsec_scan"


def _load_matcher(tooling: Path):
    """Load the class scanner and validate public policy before scanning any text."""
    import contextlib
    import io

    try:
        rules = json.loads((tooling / "rules.json").read_bytes())
        policy = json.loads(POLICY.read_bytes())
        identities = {row["id"]: int(level) for level, group in rules.items() for row in group["patterns"]}
        blocked = set(policy["class6_block_ids"])
        if not blocked <= {rule for rule, level in identities.items() if level == 6}:
            raise PublishBlocked("OPSEC: configured policy IDs absent from class-6 rules; load refused.")
        spec = importlib.util.spec_from_file_location("_lu_private_opsec_matcher", tooling / "matcher.py")
        if spec is None or spec.loader is None:
            raise ValueError
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            source = (tooling / "matcher.py").read_bytes()
            exec(compile(source, "<private-opsec-matcher>", "exec"), module.__dict__)
            matcher = module.Matcher(rules)
        return matcher, identities, blocked
    except PublishBlocked:
        raise
    except Exception:
        raise PublishBlocked("OPSEC: private matcher or rules unavailable/incompatible; write refused.") from None


def _scan(text: str, loaded) -> list[dict]:
    import contextlib
    import io

    matcher, identities, _ = loaded
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            hits = matcher.scan(text)
        findings = []
        for hit in hits:
            rule, level, (start, end) = hit.rule_id, hit.class_id, hit.span
            if (
                not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", rule)
                or identities.get(rule) != level
                or level not in range(1, 7)
                or not 0 <= start <= end <= len(text)
            ):
                raise ValueError
            findings.append({"rule_id": rule, "class": level, "start": start})
        return findings
    except Exception:
        raise PublishBlocked("OPSEC: private matcher result incompatible; write refused.") from None


def _matches(text: str, tooling: Path) -> list[dict]:
    return _scan(text, _load_matcher(tooling))


def check_texts(
    destination: str,
    texts: list[str],
    *,
    environment: dict[str, str] | None = None,
    tooling: Path | None = None,
    log_path: Path | None = None,
    field_names: list[str] | None = None,
) -> None:
    """Scan final fields; an override permits policy hits only after a durable log."""
    environment = os.environ if environment is None else environment
    reason = environment.pop("LU_OPSEC_OVERRIDE", "")
    if is_private(destination):
        if reason.strip():
            _record_override(destination, [], reason, log_path)
        return
    loaded = _load_matcher(tooling or private_tooling())
    blocks = []
    locations = []
    for index, text in enumerate(texts):
        for finding in _scan(text, loaded):
            rule, level = finding["rule_id"], finding["class"]
            if level <= 5 or rule in loaded[2]:
                blocks.append((rule, level))
                # Names come from option/JSON keys, never from field values.
                name = field_names[index] if field_names and index < len(field_names) else f"text[{index + 1}]"
                if not re.fullmatch(r"[A-Za-z0-9_.\[\]-]{1,80}", name):
                    name = f"text[{index + 1}]"
                line = text.count("\n", 0, finding["start"]) + 1
                locations.append(f"rule={rule} class={level} field={name} line={line}")
    if reason.strip():
        _record_override(destination, blocks, reason, log_path)
        return
    if not blocks:
        return
    raise PublishBlocked(
        f"OPSEC blocked: {'; '.join(locations)}. Remove the flagged detail; for a false positive, "
        "set LU_OPSEC_OVERRIDE to a reason for this command only."
    )


def _record_override(destination: str, blocks: list[tuple[str, int]], reason: str, log_path: Path | None) -> None:
    """Claim one parent-shell override and durably log it before sending."""
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "destination": destination,
        "rule_ids": sorted({rule for rule, _ in blocks}),
        "reason": reason,
    }
    claim = None
    try:
        target = log_path or primary_root() / "batch_state/opsec/overrides.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        parent = os.getppid()
        started = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(parent)], capture_output=True, text=True, check=True, timeout=5
        ).stdout.strip()
        if not started:
            raise ValueError
        key = hashlib.sha256(f"{parent}:{started}:{reason}".encode()).hexdigest()
        claim = target.parent / ("consumed-" + key)
        fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        fd = os.open(target, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a") as stream:
            stream.write(json.dumps(record, ensure_ascii=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        if claim is not None and exc.filename == str(claim):
            raise PublishBlocked("OPSEC: override already consumed; use a fresh command-scoped reason.") from None
        raise PublishBlocked("OPSEC: override log unavailable; write refused.") from None
    except Exception:
        raise PublishBlocked("OPSEC: override log unavailable; write refused.") from None


def real_gh(environment: Mapping[str, str]) -> str:
    """Pin an absolute executable excluding every copy of the agent shim."""
    pinned = environment.get("AGENT_REAL_GH")
    candidates = (
        [pinned]
        if pinned
        else [
            str(Path(entry) / "gh")
            for entry in environment.get("AGENT_ORIGINAL_PATH", environment.get("PATH", "")).split(os.pathsep)
            if entry
        ]
    )
    for item in candidates:
        if not item:
            continue
        path = Path(item).resolve()
        if (
            path.is_absolute()
            and path.is_file()
            and os.access(path, os.X_OK)
            and path != (ROOT / "scripts/agent_runtime/shims/gh").resolve()
            and path.parts[-4:] != ("scripts", "agent_runtime", "shims", "gh")
        ):
            return str(path)
    raise PublishBlocked("OPSEC: real gh executable unavailable; write refused.")


def publish_environment(source: Mapping[str, str], *, root: Path = ROOT) -> dict[str, str]:
    """Keep the publishing shim first without propagating command-scoped overrides."""
    env = dict(source)
    env.pop("LU_OPSEC_OVERRIDE", None)
    shim = str(root / "scripts/agent_runtime/shims")
    env["PATH"] = os.pathsep.join([shim, *[p for p in env.get("PATH", "").split(os.pathsep) if p and p != shim]])
    try:
        env["AGENT_REAL_GH"] = real_gh(source)
    except PublishBlocked:
        env.pop("AGENT_REAL_GH", None)
    return env


def checked_run(args, *, runner=None, **kwargs):
    """subprocess.run-compatible gateway for project publishers, including injected send spies."""
    runner = runner or subprocess.run
    if not args or Path(str(args[0])).name != "gh":
        return runner(args, **kwargs)
    from scripts.opsec.gh_snapshot import snapshot

    environment = dict(kwargs.get("env", os.environ))
    with snapshot(
        list(args[1:]),
        cwd=Path(kwargs.get("cwd") or Path.cwd()),
        environment=environment,
        stdin=kwargs.get("input"),
        reader=runner,
    ) as frozen:
        if frozen.write:
            reason = os.environ.pop("LU_OPSEC_OVERRIDE", "")
            if reason:
                environment["LU_OPSEC_OVERRIDE"] = reason
            check_texts(frozen.destination, frozen.texts, environment=environment, field_names=frozen.field_names)
            kwargs["env"] = environment
            if frozen.stdin is not None:
                kwargs["input"] = (
                    frozen.stdin.decode("utf-8") if kwargs.get("text") or kwargs.get("encoding") else frozen.stdin
                )
        elif "LU_OPSEC_OVERRIDE" in environment:
            # Reads do not consume the parent's next-write override, but the
            # read subprocess must not inherit it.
            read_environment = dict(environment)
            read_environment.pop("LU_OPSEC_OVERRIDE", None)
            kwargs["env"] = read_environment
        # Project publishers have already checked the immutable snapshot. Use
        # the existing helper with pinned gh, avoiding a second scan that would
        # consume the command override twice. Custom send spies keep argv intact.
        if (
            frozen.write
            and getattr(runner, "__module__", None) == "subprocess"
            and getattr(runner, "__name__", None) == "run"
        ):
            from scripts.opsec.gh_entry import guarded_command

            environment.pop("LU_OPSEC_OVERRIDE", None)
            kwargs["env"] = environment
            return runner(
                guarded_command(real_gh(environment), ROOT / "scripts/agent_runtime/shims/gh", frozen.argv), **kwargs
            )
        return runner([args[0], *frozen.argv], **kwargs)
