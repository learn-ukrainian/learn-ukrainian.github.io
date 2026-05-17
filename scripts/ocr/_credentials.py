"""File-backed credential loader for OCR (and other API) clients.

Why this exists (2026-05-17): #M-5 in MEMORY.md records two API-key leaks in
six weeks (GEMINI_API_KEY 2026-05-10, DAGGER_CLOUD_TOKEN 2026-05-12), both
from sloppy `env | grep` patterns or substring-name filters. To keep new
API keys (Mistral, future providers) out of shell env entirely, this module
reads credentials from a file the user owns, refuses world/group-readable
files, and never logs or returns the value alongside any metadata that might
end up in a stack trace or error report.

Threat model in scope:
    1. Accidental `echo $VAR` / `env` enumeration → mitigated by never
       loading into env.
    2. Multi-user host filesystem permissions → mitigated by mode check.
    3. Stack-trace leakage in error paths → mitigated by error messages
       that include the PATH only, never the contents.

Threat model OUT of scope:
    - Compromised orchestrator process (an attacker with code execution
      can always read the file the user gave us).
    - Backups / cloud sync of the credentials directory (user's
      operational concern; we don't manage their backups).
    - Memory inspection / process tracing (root or ptrace-equivalent
      always wins).

The credential file format is intentionally trivial: one line, the secret,
optional trailing newline. No JSON, no YAML, no env-file `KEY=value`
parsing. The simplest format is the easiest to audit.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path


class CredentialError(Exception):
    """Base class. Catches all expected credential-load failure modes."""


class CredentialNotFound(CredentialError):
    pass


class CredentialInsecure(CredentialError):
    """The file exists but its permissions allow group/world read or write."""


class CredentialEmpty(CredentialError):
    pass


# Owner-only permission masks we accept. Anything wider than "owner can rw"
# is rejected — including o+x or g+r, both of which make the secret
# casually readable by other accounts on a shared host.
_ALLOWED_MODES = frozenset({0o400, 0o600})


def load_credential(path: Path | str) -> str:
    """Read a single-line credential from a file.

    Errors raised by this function MUST NOT be allowed to print the file
    contents under any circumstance. They include the path so the user can
    fix it, and the kind of failure (missing / insecure / empty) — never the
    secret value.

    Caller responsibility:
        - Do NOT log the return value. Pass it directly into an HTTP header
          (`Authorization: Bearer ...`) or SDK constructor.
        - Do NOT pass the return value via argv or shell-expanded subprocess
          args (visible via `ps`).
        - Do NOT export the return value into env vars consumed by other
          subprocesses unless the subprocess is also under the same trust
          domain.
    """
    path = Path(path).expanduser()

    if not path.exists():
        raise CredentialNotFound(
            f"credential file not found: {path}\n"
            f"Create it with:  install -m 0600 /dev/stdin {path} <<< 'YOUR_KEY'\n"
            f"Or: touch {path} && chmod 600 {path} && $EDITOR {path}"
        )

    if not path.is_file():
        raise CredentialNotFound(
            f"credential path is not a regular file: {path} (got {stat.filemode(path.stat().st_mode)})"
        )

    file_stat = path.stat()
    mode = file_stat.st_mode & 0o777
    if mode not in _ALLOWED_MODES:
        raise CredentialInsecure(
            f"credential file {path} has mode {oct(mode)} — must be 0600 or 0400.\n"
            f"Fix with:  chmod 600 {path}"
        )

    # Ownership check: refuse if the file is owned by someone other than the
    # current uid. (On a shared host, root could chown a file into your perms
    # check; the uid match makes that pivot harder.)
    if file_stat.st_uid != os.getuid():
        raise CredentialInsecure(
            f"credential file {path} is owned by uid={file_stat.st_uid}, not current uid={os.getuid()}.\n"
            f"Refusing to load. Move or rewrite the file as your own user."
        )

    # NB: we read via Path.read_text rather than open()+f.read so the file
    # descriptor doesn't linger across a slow call.
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        # `exc.strerror` is the OS message ("Permission denied" etc.), safe.
        # Do NOT include `repr(exc)` — pathlib may include a partial buffer
        # in some implementations.
        raise CredentialError(f"failed to read credential file {path}: {exc.strerror}") from None

    value = raw.strip()
    if not value:
        raise CredentialEmpty(f"credential file {path} is empty after stripping whitespace")

    # Belt-and-suspenders: detect multi-line content. The format is one line.
    # If the user accidentally pasted a JSON blob or env-file fragment,
    # surface that rather than silently sending it as a Bearer token.
    if "\n" in value:
        raise CredentialError(
            f"credential file {path} contains multiple lines after strip(). "
            f"Expected a single line. Refusing to load."
        )

    return value


__all__ = [
    "CredentialEmpty",
    "CredentialError",
    "CredentialInsecure",
    "CredentialNotFound",
    "load_credential",
]
