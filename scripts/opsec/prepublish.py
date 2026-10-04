"""Prevent accidental disclosure by cooperative agents before public GitHub writes.

Defense in depth, not universal enforcement: absolute gh paths, aliases,
extensions and raw HTTP clients can bypass shell interception. Direct project
publishers must call scripts.publish.github.publish. The private matcher owns all matching logic;
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
import unicodedata
from collections.abc import Mapping
from datetime import UTC, datetime
from functools import wraps
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
POLICY = Path(__file__).with_name("blocking.json")


class PublishBlocked(RuntimeError):
    """A safe diagnostic, with no source text or private exception detail.

    indices names the texts of a check_texts refusal that had a blocking finding.
    """

    indices: frozenset[int] = frozenset()


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
        return yaml.load(
            (ROOT / "scripts/config/fleet_repos.yaml").read_text(),
            Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader),
        )["repos"]
    except Exception:
        raise PublishBlocked("OPSEC: repository allowlist unavailable; write refused.") from None


def normalize_hostname(value: str) -> str | None:
    """Return a lowercase ASCII hostname, or None for malformed labels."""
    # Check ASCII before lowercasing: Unicode look-alikes must not normalize in.
    label = r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
    if value.isascii() and re.fullmatch(rf"{label}(?:\.{label})*", value.lower()):
        return value.lower()
    return None


def normalize_repository(value: str, host: str = "github.com") -> str:
    """Return a canonical host/owner/name, or unknown (never private by default)."""
    value = value.strip().removesuffix(".git")
    value = re.sub(r"^git@([^:]+):", r"\1/", value)
    value = re.sub(r"^https?://", "", value)
    parts = value.split("/")
    if len(parts) == 2:
        parts.insert(0, host)
    if len(parts) != 3:
        return "unknown"
    hostname = normalize_hostname(parts[0])
    if hostname is not None and all(re.fullmatch(r"[A-Za-z0-9_.-]+", part) for part in parts[1:]):
        return "/".join([hostname, *parts[1:]]).lower()
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


CREDENTIAL_TOKEN_PATTERN = re.compile(
    r"\b("
    r"ghp_[A-Za-z0-9]{20,}|"
    r"github_pat_[A-Za-z0-9_]{20,}|"
    r"gh[ours]_[A-Za-z0-9]{20,}|"
    r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}"
    r")\b|"
    r"(?<![\w-])xox[baprs]-[A-Za-z0-9-]{10,}\b|"
    r"(?<![\w-])(?:sk-(?:ant-|proj-)[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{20,})\b|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
)


def _is_ignorable_or_format(ch: str) -> bool:
    cp = ord(ch)
    if unicodedata.category(ch) == "Cf":
        return True
    if cp == 0x034F:  # Combining Grapheme Joiner (Mn)
        return True
    if 0x115F <= cp <= 0x1160 or cp == 0x3164 or cp == 0xFFA0:  # Hangul Fillers (Lo)
        return True
    if 0x17B4 <= cp <= 0x17B5:  # Khmer Vowel Inherent Aq / Aa (Mn)
        return True
    if 0x180B <= cp <= 0x180F:  # Mongolian Free Variation Selectors (Mn)
        return True
    if cp == 0x2065:  # Unassigned in General Punctuation / controls (Cn)
        return True
    if cp == 0x2800:  # Braille Pattern Blank (So)
        return True
    if 0xFE00 <= cp <= 0xFE0F:  # Variation Selectors 1..16 (Mn)
        return True
    if 0xFFF0 <= cp <= 0xFFF8:  # Specials unassigned (Cn)
        return True
    return 0xE0000 <= cp <= 0xE0FFF  # Tags, Variation Selectors, and Plane 14 ignorables


def _map_decimal_digit(ch: str) -> str:
    try:
        return str(unicodedata.decimal(ch))
    except (ValueError, TypeError):
        return ch


def normalize_for_scan(text: str) -> str:
    """Normalize text: map decimal digits, strip format/ignorable chars, apply NFKC."""
    if not text or text.isascii():
        return text
    mapped_digits = "".join(_map_decimal_digit(ch) for ch in text)
    stripped = "".join(ch for ch in mapped_digits if not _is_ignorable_or_format(ch))
    normalized = unicodedata.normalize("NFKC", stripped)
    return "".join(ch for ch in normalized if not _is_ignorable_or_format(ch))


def _load_matcher(tooling: Path):
    """Load the class scanner and validate public policy before scanning any text."""
    import contextlib
    import io

    try:
        rules = json.loads((tooling / "rules.json").read_bytes())
        policy = json.loads(POLICY.read_bytes())
        identities = {}
        for level, group in rules.items():
            for row in group["patterns"]:
                regex = row.get("regex", "")
                if normalize_for_scan(regex) != regex:
                    raise PublishBlocked(f"OPSEC: rule {row.get('id')} contains unnormalized characters; load refused.")
                identities[row["id"]] = int(level)
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


def _validated_matcher_hits(text: str, loaded) -> list[tuple[str, int, int, int]]:
    """Validate matcher identities and half-open offsets without exposing text."""
    import contextlib
    import io

    matcher, identities, _ = loaded
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            hits = list(matcher.scan(text))
        validated = []
        for hit in hits:
            rule, level, (start, end) = hit.rule_id, hit.class_id, hit.span
            if (
                not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", rule)
                or identities.get(rule) != level
                or type(level) is not int
                or level not in range(1, 7)
                or type(start) is not int
                or type(end) is not int
                or not 0 <= start < end <= len(text)
            ):
                raise ValueError
            validated.append((rule, level, start, end))
        return validated
    except Exception:
        raise PublishBlocked("OPSEC: private matcher result incompatible; write refused.") from None


def absolute_path_spans(text: str, *, tooling: Path | None = None) -> list[tuple[int, int]]:
    """Return validated absolute-path spans in normalized text; never tokenize locally."""
    loaded = _load_matcher(tooling or private_tooling())
    if loaded[1].get("3-absolute-path") != 3:
        raise PublishBlocked("OPSEC: absolute-path rule unavailable/incompatible; write refused.")
    spans = sorted(
        (start, end)
        for rule, _, start, end in _validated_matcher_hits(normalize_for_scan(text), loaded)
        if rule == "3-absolute-path"
    )
    if any(left[1] > right[0] for left, right in pairwise(spans)):
        raise PublishBlocked("OPSEC: private matcher result incompatible; write refused.")
    return spans


def _scan(text: str, loaded) -> list[dict]:
    text = normalize_for_scan(text)
    findings = [
        {"rule_id": rule, "class": level, "start": start, "line": text.count("\n", 0, start) + 1}
        for rule, level, start, _ in _validated_matcher_hits(text, loaded)
    ]
    try:
        for match in CREDENTIAL_TOKEN_PATTERN.finditer(text):
            start = match.start()
            findings.append(
                {
                    "rule_id": "5-credential-token",
                    "class": 5,
                    "start": start,
                    "line": text.count("\n", 0, start) + 1,
                }
            )
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
    claimant: int | None = None,
) -> None:
    """Scan final fields; an override permits policy hits only after a durable log.

    The override is dropped from environment on every call but claimed and
    logged only when a scan blocks, so a clean, empty or private publish
    leaves it for the one flagged publish it was set for. claimant is the
    process whose override is claimed once; by default the caller's parent
    (the shell that set it).
    """
    environment = os.environ if environment is None else environment
    reason = environment.pop("LU_OPSEC_OVERRIDE", "")
    if not texts or is_private(destination):
        return
    loaded = _load_matcher(tooling or private_tooling())
    blocks = []
    locations = []
    blocked = set()
    for index, text in enumerate(texts):
        for finding in _scan(text, loaded):
            rule, level = finding["rule_id"], finding["class"]
            if level <= 5 or rule in loaded[2]:
                blocks.append((rule, level))
                blocked.add(index)
                # Names come from option/JSON keys, never from field values.
                name = field_names[index] if field_names and index < len(field_names) else f"text[{index + 1}]"
                if not re.fullmatch(r"[A-Za-z0-9_.\[\]-]{1,80}", name):
                    name = f"text[{index + 1}]"
                line = finding["line"]
                location = f"rule={rule} class={level} field={name} line={line}"
                if location not in locations:
                    locations.append(location)
    if not blocks:
        return
    if reason.strip():
        _record_override(destination, blocks, reason, log_path, claimant)
        return
    error = PublishBlocked(
        f"OPSEC blocked: {'; '.join(locations)}. Remove the flagged detail; for a false positive, "
        "set LU_OPSEC_OVERRIDE to a reason for this command only."
    )
    error.indices = frozenset(blocked)
    raise error


def _record_override(
    destination: str,
    blocks: list[tuple[str, int]],
    reason: str,
    log_path: Path | None,
    claimant: int | None = None,
) -> None:
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
        parent = os.getppid() if claimant is None else claimant
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
    """Raw transport: closed read grammar or positively verified private write."""
    runner = runner or subprocess.run
    if not args or Path(str(args[0])).name != "gh":
        return runner(args, **kwargs)
    from scripts.opsec.gh_snapshot import admit

    environment = dict(kwargs.get("env", os.environ))
    frozen = admit(list(args[1:]), cwd=Path(kwargs.get("cwd") or Path.cwd()), environment=environment, reader=runner)
    environment.pop("LU_OPSEC_OVERRIDE", None)
    kwargs["env"] = environment
    return runner([args[0], *frozen.argv], **kwargs)
