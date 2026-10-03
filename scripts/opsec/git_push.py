"""Scan the text a git push publishes, from Git's own pre-push hook (#9339).

The agent git shim runs every push with core.hooksPath pinned to push_hooks/,
so Git runs this scanner on the exact ref updates it is about to send: one
stdin line per update, "<local ref> <local id> <remote ref> <remote id>".
Every line is read and validated before anything is allowed, and objects are
read by the local id Git supplied, never by resolving a name again, so a ref
that moves during the scan changes nothing. For a public destination the
remote ref names, the names and messages of the annotated tags on the way from
each sent id (nested tags included) and the whole raw messages of every commit
reachable from the sent ids, with the tag names and messages embedded in their
mergetag headers, are scanned through check_texts, except commits reachable
from the head of the default branch of the catalogue's canonical public
repository (already public), and only when every commit object reachable from
it hashes to its id. That head comes from one GitHub API read per push;
nothing is cached between pushes, and nothing the destination reports is
evidence of what it already has. Enumeration ignores replacement objects,
grafts and commit-graph files, a grafted repository is refused, a shallow one
is refused when a boundary commit is inside the scan set, an alternate shallow
file is refused, and the scan's own git calls run without tracing or prompts.
File contents are not scanned. A deletion publishes no text.

A destination is exempt (private) only when is_private says so and Git reaches
it on the trusted transport route (trusted_route); otherwise it is scanned as
public. A malformed record, a scanner error, a missing matcher or the deadline
refuses the push. After a clean scan the caller's own pre-push hook runs with
the same arguments and input, and its status is the hook's status.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

# Executed by the hook as a file, so imports do not depend on the hook's cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.opsec import prepublish as gate

# The hooks directory the shim pins; chain runs the caller's own hook of a name.
HOOKS = Path(__file__).resolve().parent / "push_hooks"
COMMIT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# Hex length of an object id per repository object format.
ID_LENGTH = {"sha1": 40, "sha256": 64}
# The local ref Git names for a deletion, whose local id is all zeros.
DELETE = b"(delete)"
# The canonical public repository's default branch and the id form GitHub reports for its head.
PUBLIC_DEFAULT_BRANCH = "main"
PUBLIC_HEAD = re.compile(r"[0-9a-f]{40}")
# Bound on the one public repository read of a push.
API_TIMEOUT = 10
# Seconds the whole scan may take before the push is refused; LU_OPSEC_PUSH_SCAN_TIMEOUT overrides it.
SCAN_TIMEOUT = 300


class ScanTimeout(BaseException):
    """The deadline passed. Not an Exception, so no fail-soft handler on the way can absorb it."""


@contextmanager
def deadline(seconds: float):
    def expire(signum, frame):
        raise ScanTimeout

    previous = signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def scan_timeout(environment: dict[str, str]) -> float:
    value = environment.get("LU_OPSEC_PUSH_SCAN_TIMEOUT")
    if value is None:
        return SCAN_TIMEOUT
    try:
        seconds = float(value)
    except ValueError:
        seconds = 0
    if not 0 < seconds < float("inf"):
        raise gate.PublishBlocked("OPSEC: LU_OPSEC_PUSH_SCAN_TIMEOUT is not a positive number; push refused.")
    return seconds


def _is_local(url: str) -> bool:
    """git's url_is_local_not_ssh: no colon, or a slash before the first colon."""
    colon, slash = url.find(":"), url.find("/")
    return colon < 0 or 0 <= slash < colon


HOSTED_URL = re.compile(r"(?:https?|ssh|git|git\+ssh|ssh\+git)://(?:[^@/]+@)?([^/:@]+)(?::\d*)?/(.+)", re.I)
SCP_URL = re.compile(r"(?:[^@/]+@)?([^/:@]+):([^:].*)")


def destination(url: str) -> str:
    """Canonical host/owner/name for a push URL, or unknown (never private by default).

    Accepts the URL, ssh and scp-like ([user@]host:path) forms git uses, with or
    without userinfo. Local paths, file URLs, remote helpers and anything else
    without a hosted identity are unknown, which counts as public.
    """
    value = url.strip()
    if not value or _is_local(value):
        return "unknown"
    match = HOSTED_URL.fullmatch(value) or (None if "://" in value else SCP_URL.fullmatch(value))
    if not match:
        return "unknown"
    host, path = match.groups()
    return gate.normalize_repository(f"{host}/{path.strip('/')}")


def scan_environment(environment: dict[str, str]) -> dict[str, str]:
    """The hook's environment for the scan's own git calls.

    Git's repository variables stay, so the scan reads the repository and
    object stores the push reads. GIT_CONFIG goes: it narrows what git config
    reports to one file, while the push reads every configuration source, so
    the scan's configuration reads see what the push uses. No override,
    tracing, credential prompts or partial-clone object fetches; replacement
    objects and grafts disabled. A trace2 target of "0" in the environment
    outranks one set in system or global configuration. Messages are
    untranslated.
    """
    scrubbed = {
        key: value
        for key, value in environment.items()
        if key not in (gate.OVERRIDE, gate.OVERRIDE_ANCHOR, "GIT_CONFIG", "GIT_CURL_VERBOSE")
        and not key.startswith("GIT_TRACE")
    }
    scrubbed.update(
        GIT_TRACE2="0",
        GIT_TRACE2_EVENT="0",
        GIT_TRACE2_PERF="0",
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_LAZY_FETCH="1",
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_GRAFT_FILE=os.devnull,
        LC_ALL="C",
    )
    return scrubbed


def _grafts_present(path: str) -> bool:
    """Whether git would read graft lines from path; anything unreadable counts as present."""
    try:
        info = os.stat(path)
    except FileNotFoundError:
        return False
    except OSError:
        return True
    if stat.S_ISCHR(info.st_mode) and os.path.samefile(path, os.devnull):
        return False
    return not stat.S_ISREG(info.st_mode) or info.st_size > 0


def shallow_boundaries(path: str, length: int) -> set[str]:
    """The commit ids the shallow file at path lists; none when it is absent.

    git reads one id per line and treats each as parentless. Anything git might
    read differently (a non-regular or unreadable file, a line that is not
    exactly one lowercase id of this repository's length) refuses the push.
    """
    try:
        # Non-blocking: a FIFO here must not stall the scan; fstat then refuses it.
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except FileNotFoundError:
        return set()
    except OSError:
        raise gate.PublishBlocked("OPSEC: shallow file unreadable; push refused.") from None
    try:
        with os.fdopen(descriptor, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise gate.PublishBlocked("OPSEC: shallow file unreadable; push refused.")
            data = handle.read()
    except OSError:
        raise gate.PublishBlocked("OPSEC: shallow file unreadable; push refused.") from None
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()  # The newline ending the last id.
    identity = re.compile(rb"[0-9a-f]{%d}" % length)
    if not all(identity.fullmatch(line) for line in lines):
        raise gate.PublishBlocked("OPSEC: shallow file malformed; push refused.")
    return {line.decode("ascii") for line in lines}


def real_git(environment: dict[str, str]) -> str:
    """The git the shim pushed with; otherwise git from PATH, which Git starts with its own exec path."""
    pinned = environment.get("LU_OPSEC_REAL_GIT", "")
    return pinned if os.path.isabs(pinned) and os.access(pinned, os.X_OK) else "git"


class Repository:
    """Read-only object queries through the real git in the hook's repository."""

    def __init__(self, git: str, environment: dict[str, str]):
        # Replacement objects change what readers see but not what a pack sends,
        # and a commit-graph file is a local cache of parents that git trusts
        # without rehashing, so every query reads the original objects (the
        # flag and these -c options outrank caller configuration).
        self.base = [
            git,
            "--no-replace-objects",
            "-c",
            "core.useReplaceRefs=false",
            "-c",
            "core.commitGraph=false",
            "-c",
            "advice.graftFileDeprecated=false",
        ]
        self.caller = environment
        self.environment = scan_environment(environment)

    def run(
        self, *args: str, stdin: str | None = None, timeout: int = 60, environment: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [*self.base, *args],
            input=stdin.encode() if stdin is not None else None,
            stdin=subprocess.DEVNULL if stdin is None else None,
            capture_output=True,
            env=self.environment if environment is None else environment,
            check=False,
            timeout=timeout,
        )

    def raw(self, *args: str, stdin: str | None = None, environment: dict[str, str] | None = None) -> bytes:
        result = self.run(*args, stdin=stdin, environment=environment)
        if result.returncode:
            # Fixed text only: git output can quote ref names and messages.
            raise gate.PublishBlocked(
                f"OPSEC: push scan step git {args[0]} failed (exit {result.returncode}); push refused."
            )
        return result.stdout

    def text(self, *args: str, stdin: str | None = None, environment: dict[str, str] | None = None) -> str:
        return self.raw(*args, stdin=stdin, environment=environment).decode("utf-8", "replace")

    def config(self) -> list[tuple[str, str | None]]:
        """Every configuration entry in reading order; a valueless entry has value None."""
        entries = []
        for entry in self.text("config", "--list", "-z").split("\0"):
            if entry:
                key, newline, value = entry.partition("\n")
                entries.append((key, value if newline else None))
        return entries

    def object_format(self) -> str:
        found = self.text("rev-parse", "--show-object-format").strip()
        if found not in ID_LENGTH:
            raise gate.PublishBlocked("OPSEC: repository object format unknown; push refused.")
        return found

    def layout(self, object_format: str) -> tuple[bool, set[str]]:
        """Whether grafts alter commit parents, and the shallow boundary commits.

        git's own path resolution names both files, so a linked worktree reads
        the shallow file of the shared repository.
        """
        # Resolve the grafts path with the caller's GIT_GRAFT_FILE: the file the push reads.
        environment = {key: value for key, value in self.environment.items() if key != "GIT_GRAFT_FILE"}
        if "GIT_GRAFT_FILE" in self.caller:
            environment["GIT_GRAFT_FILE"] = self.caller["GIT_GRAFT_FILE"]
        output = self.text(
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "info/grafts",
            "--git-path",
            "shallow",
            environment=environment,
        )
        grafts, shallow = output.splitlines()
        return _grafts_present(grafts), shallow_boundaries(shallow, ID_LENGTH[object_format])


class CanonicalPublicRepository:
    """The default-branch head of the catalogue's public repository, read through the typed publisher reads.

    The repository comes from the catalogue, never from the push URL or local
    git configuration, and the answer comes from the GitHub API. Only a
    well-formed reply bound to the question counts; a failure, timeout, rate
    limit, 404 or malformed or inconsistent body is no answer.
    """

    def __init__(self, repo: str, environment: dict[str, str], *, runner=None, timeout: int = API_TIMEOUT):
        self.repo = repo
        self.environment = gate.internal_environment(environment)
        self.runner = runner
        self.timeout = timeout
        self.calls = 0

    @classmethod
    def from_catalog(cls, environment: dict[str, str]) -> CanonicalPublicRepository | None:
        rows = [row for row in gate.catalog().values() if row.get("role") == "public-monorepo"]
        repo = gate.normalize_repository(rows[0]["github"]) if len(rows) == 1 else "unknown"
        return None if repo == "unknown" else cls(repo, environment)

    def default_head(self) -> str | None:
        """The commit the public default branch names now, or None without a bound answer.

        The reply must name this repository (nameWithOwner), the default branch
        by its expected name, and a 40-character lowercase hex commit id, with
        no GraphQL errors.
        """
        self.calls += 1
        try:
            from scripts.publish.github import read

            result = read(
                "default-head",
                repo=self.repo,
                runner=self.runner,
                env=dict(self.environment),
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            body = json.loads(result.stdout)
            repository = body["data"]["repository"]
            branch = repository["defaultBranchRef"]
            oid = branch["target"]["oid"]
            bound = (
                result.returncode == 0
                and "errors" not in body
                and isinstance(repository["nameWithOwner"], str)
                and gate.normalize_repository(repository["nameWithOwner"]) == self.repo
                and branch["name"] == PUBLIC_DEFAULT_BRANCH
                and isinstance(oid, str)
                and PUBLIC_HEAD.fullmatch(oid) is not None
            )
        except Exception:
            return None
        return oid if bound else None


def parse_updates(data: bytes, length: int) -> list[tuple[bytes, str, str, str]]:
    """(local ref, local id, remote ref, remote id) for every line Git wrote; anything malformed refuses.

    The local ref can be any expression the caller typed, spaces included, so
    the line is split from the right; ref names have no spaces. Ids are
    lowercase hex of this repository's length, a remote ref starts with refs/,
    and a deletion is exactly the (delete) local ref with the all-zero local id.
    Input that does not end with a newline is cut short and refuses as well.
    """
    if not data:
        return []
    malformed = gate.PublishBlocked("OPSEC: pre-push input malformed; push refused.")
    if not data.endswith(b"\n"):
        raise malformed
    identity = re.compile(rb"[0-9a-f]{%d}" % length)
    zero = b"0" * length
    updates = []
    for line in data[:-1].split(b"\n"):
        fields = line.rsplit(b" ", 3)
        if len(fields) != 4:
            raise malformed
        local_ref, local_id, remote_ref, remote_id = fields
        if (
            not local_ref
            or not identity.fullmatch(local_id)
            or not identity.fullmatch(remote_id)
            or not remote_ref.startswith(b"refs/")
            or any(byte < 0x20 or byte == 0x7F for byte in remote_ref)
            or (local_id == zero) != (local_ref == DELETE)
        ):
            raise malformed
        updates.append((local_ref, local_id.decode(), remote_ref.decode("utf-8", "replace"), remote_id.decode()))
    return updates


def trusted_route(repository: Repository, remote: str, url: str) -> bool:
    """Whether Git reaches url on the route the private exemption trusts.

    That is https with certificate verification, or ssh (URL or scp-like form)
    through the default ssh program, with Git's own exec path and no remote
    helper. A configured ssh program (GIT_SSH_COMMAND, GIT_SSH, core.sshCommand),
    a remote helper (<transport>::<address>, remote.<name>.vcs), another exec
    path or disabled certificate verification can deliver elsewhere, so such a
    destination is scanned as public.
    """
    caller = repository.caller
    value = url.strip()
    lowered = value.lower()
    https = lowered.startswith("https://")
    ssh = lowered.startswith(("ssh://", "git+ssh://", "ssh+git://")) or ("://" not in value and not _is_local(value))
    if "::" in value or not (https or ssh):
        return False
    git = repository.base[0]
    if not os.path.isabs(git):
        return False
    default = {key: item for key, item in repository.environment.items() if key != "GIT_EXEC_PATH"}
    standard = repository.text("--exec-path", environment=default).strip()
    if "GIT_EXEC_PATH" in caller and os.path.realpath(caller["GIT_EXEC_PATH"]) != os.path.realpath(standard):
        return False
    keys = {key for key, _ in repository.config()}
    if f"remote.{remote}.vcs" in keys:
        return False
    if ssh:
        return not ({"GIT_SSH_COMMAND", "GIT_SSH"} & caller.keys() or "core.sshcommand" in keys)
    if "GIT_SSL_NO_VERIFY" in caller:
        return False
    verify = repository.run("config", "--type=bool", "--get-urlmatch", "http.sslverify", value)
    if verify.returncode not in (0, 1):
        return False
    return verify.returncode == 1 or verify.stdout.strip() == b"true"


def _short_ref(target: str) -> tuple[str, str]:
    for prefix, kind in (("refs/heads/", "branch"), ("refs/tags/", "tag")):
        if target.startswith(prefix):
            return kind, target[len(prefix) :]
    return "ref", target


def split_object(raw: bytes, position: str) -> tuple[list[tuple[bytes, bytes]], str]:
    """Header fields and the whole message of a raw commit or tag object.

    The message is everything after the first empty line, as git reads it,
    NUL bytes included. It is decoded as UTF-8 and, when an encoding header
    names another codec that decodes it differently, that reading follows, so
    the scan covers what either kind of reader shows. A continuation line (one
    leading space) is unfolded into the value of the field it continues, as
    git reads a mergetag header. An object without that empty line, or whose
    headers open with a continuation, would deliver text no reader calls a
    message, so it is refused naming only position.
    """
    # A leading newline lets an object that opens with the empty line split like any other.
    header, separator, body = (b"\n" + raw).partition(b"\n\n")
    if not separator:
        raise gate.PublishBlocked(f"OPSEC: {position} has no header/body separator; push refused.")
    # Lines are collected and joined once per field, so unfolding stays linear in the object size.
    folded: list[tuple[bytes, list[bytes]]] = []
    for line in header[1:].split(b"\n"):
        if line.startswith(b" "):
            if not folded:
                raise gate.PublishBlocked(f"OPSEC: {position} headers malformed; push refused.")
            folded[-1][1].append(line[1:])
        elif line:
            key, _, value = line.partition(b" ")
            folded.append((key, [value]))
    fields = [(key, b"\n".join(lines)) for key, lines in folded]
    message = body.decode("utf-8", "replace")
    declared = next((value for key, value in fields if key == b"encoding"), None)
    if declared is not None:
        try:
            other = body.decode(declared.decode("ascii"))
        except (LookupError, UnicodeError, ValueError):
            other = message
        if other != message:
            message += "\n" + other
    return fields, message


def tag_name(fields: list[tuple[bytes, bytes]]) -> str:
    """Every tag header value of a split tag object."""
    return "\n".join(value.decode("utf-8", "replace") for key, value in fields if key == b"tag")


def commit_texts(repository: Repository, shas: list[str]) -> list[tuple[str, list[tuple[str, str]]]]:
    """(id, [(field, text)]) of each commit, read from the raw objects.

    %B in a --format stops at the first NUL, so a message with a NUL would be
    scanned only up to it. Reading the raw object scans every byte of the
    message. A merge of a signed tag carries the whole tag object in a mergetag
    header, so its name and message are published with the commit and scanned
    as its fields. Identity lines and signatures are not.
    """
    found: list[tuple[str, list[tuple[str, str]]]] = []
    for sha, raw in zip(shas, read_commits(repository, shas), strict=True):
        fields, message = split_object(raw, f"commit[{sha[:12]}]")
        parts = [("message", message)]
        embedded = [value for key, value in fields if key == b"mergetag"]
        for number, value in enumerate(embedded, start=1):
            name = f"mergetag[{number}]"
            tag_fields, tag_message = split_object(value, f"commit[{sha[:12]}].{name}")
            parts += [(f"{name}.tagname", tag_name(tag_fields)), (f"{name}.message", tag_message)]
        found.append((sha, parts))
    return found


def read_commits(repository: Repository, shas: list[str]) -> list[bytes]:
    """The raw bytes of each commit, in order, from one cat-file batch; anything else refuses."""
    output = repository.raw("cat-file", "--batch", stdin="".join(f"{sha}\n" for sha in shas))
    found: list[bytes] = []
    position = 0
    try:
        for sha in shas:
            end = output.index(b"\n", position)
            name, kind, size = output[position:end].decode("ascii").split(" ")
            start = end + 1
            stop = start + int(size)
            if name != sha or kind != "commit" or output[stop : stop + 1] != b"\n":
                raise ValueError
            found.append(output[start:stop])
            position = stop + 1
    except (ValueError, UnicodeError):
        raise gate.PublishBlocked("OPSEC: push scan commit read malformed; push refused.") from None
    if position != len(output):
        raise gate.PublishBlocked("OPSEC: push scan commit read malformed; push refused.")
    return found


def history_verified(repository: Repository, head: str, object_format: str) -> bool:
    """Whether every commit the walk from head reaches has bytes that hash to its id.

    git trusts stored bytes without rehashing them, and a local or alternate
    object store can hold altered bytes under a genuine id. A commit whose bytes
    match its id records its parents' true ids, so when every commit reached
    from the authoritative head verifies, the walk is the true public history.
    A missing or unreadable commit counts as unverified.
    """
    try:
        shas = repository.text("rev-list", head).split()
        objects = read_commits(repository, shas)
    except gate.PublishBlocked:
        return False
    return bool(shas) and all(
        hashlib.new(object_format, b"commit %d\0" % len(raw) + raw).hexdigest() == sha
        for sha, raw in zip(shas, objects, strict=True)
    )


def published_refs(
    repository: Repository, updates: list[tuple[bytes, str, str, str]]
) -> tuple[list[str], list[str], list[str]]:
    """Ref names and annotated tag names and messages the push publishes, and the commits its updates send.

    Objects are read by the local id Git supplied. The name inside a tag object
    (its tag header) is published with it and can differ from the ref it is
    pushed to, so every tag object on the way from a sent id to its target,
    nested tags included, has its name and message scanned. Only commits are
    ever excluded as already public; these texts are always scanned.
    """
    texts: list[str] = []
    names: list[str] = []
    tips: list[str] = []
    seen_tags: set[str] = set()
    for number, (local_ref, current, remote_ref, _) in enumerate(updates, start=1):
        if local_ref == DELETE:
            continue  # A deletion publishes no text.
        kind, short = _short_ref(remote_ref)
        texts.append(short)
        names.append(f"{kind}[{number}].name")
        while (kind_of := repository.text("cat-file", "-t", current).strip()) == "tag":
            fields, message = split_object(repository.raw("cat-file", "tag", current), f"tag[{current[:12]}]")
            if current not in seen_tags:
                seen_tags.add(current)
                texts.append(tag_name(fields))
                names.append(f"tag[{current[:12]}].tagname")
                texts.append(message)
                names.append(f"tag[{current[:12]}].message")
            targets = [value.decode("ascii", "replace") for key, value in fields if key == b"object"]
            if len(targets) != 1 or not COMMIT_ID.fullmatch(targets[0]):
                raise gate.PublishBlocked("OPSEC: pushed tag object malformed; push refused.")
            current = targets[0]
        if kind_of == "commit":
            tips.append(current)
    return texts, names, tips


def public_history(repository: Repository, client, object_format: str) -> tuple[str | None, str]:
    """(head, state): the canonical public default-branch head, and whether it may exclude history.

    Only "present" excludes: the head's commit is here and every commit
    reachable from it hashes to its id (history_verified). Object ids are
    content addressed and a commit id covers its parents' ids, so that walk is
    the public history, and no local ref, URL rewrite, altered object or
    alternate object store can put a commit inside it without a hash collision
    (replacement objects, grafts and commit-graph files are off). A shallow
    boundary only removes parents, so it can only make the excluded history
    smaller and the scan set larger (see scan_push). No answer ("unavailable"),
    a head that is not here ("absent here"; never fetched, as GIT_NO_LAZY_FETCH
    holds) or history whose bytes do not match their ids ("unverified here")
    excludes nothing.
    """
    head = client.default_head() if client is not None else None
    if head is None:
        return None, "unavailable"
    # cat-file -t reads the stored type without rehashing, so altered bytes report unverified, not absent.
    if repository.run("cat-file", "-t", head).stdout.strip() != b"commit":
        return head, "absent here"
    return head, "present" if history_verified(repository, head, object_format) else "unverified here"


def isolate_scanner(repository: Repository) -> None:
    """Keep Git's repository variables away from the scanner's own lookups.

    The hook runs with the pushed repository's GIT_DIR and related variables
    (a submodule push sets them). The scan's git calls keep them through
    Repository; the catalogue, matcher and override log belong to the
    scanner's checkout, so this process drops every variable git rev-parse
    --local-env-vars names.
    """
    for name in repository.text("rev-parse", "--local-env-vars").split():
        os.environ.pop(name, None)


def claimant(environment: dict[str, str], reason: str) -> int:
    """The process an override is claimed for: the command's carried anchor, else the caller of the push.

    The agent git shim names the caller of a push as its anchor unless a
    publisher above it already named the command's, and Git hands the anchor
    to recursive submodule pushes, so every publication of one command claims
    the same single use (#9681). Without an anchor it is the parent of the git
    running this hook: the hook runs as a child of git, and git as a child of
    the caller (the shim execs git).
    """
    anchor = gate.override_anchor(environment, reason)
    if anchor is not None:
        return anchor
    try:
        result = subprocess.run(
            ["ps", "-o", "ppid=", "-p", str(os.getppid())],
            env=gate.internal_environment(),
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return int(result.stdout.strip())
    except Exception:
        raise gate.PublishBlocked("OPSEC: override log unavailable; push refused.") from None


def scan_push(arguments: list[str], data: bytes, environment: dict[str, str], *, public_repository=None) -> None:
    """Raise PublishBlocked unless every public text of this push is clean, already public or overridden.

    arguments are the hook's (remote name, URL) and data its whole input.
    public_repository reports the canonical public default-branch head; by
    default it is built from the catalogue, and only when the push sends
    commits.
    """
    if len(arguments) != 2:
        raise gate.PublishBlocked("OPSEC: pre-push hook arguments malformed; push refused.")
    remote, url = arguments
    if "GIT_SHALLOW_FILE" in environment:
        # git walks the file this names, while git rev-parse --git-path still names the repository's own.
        raise gate.PublishBlocked("OPSEC: GIT_SHALLOW_FILE is not supported for a scanned push; push refused.")
    repository = Repository(real_git(environment), environment)
    object_format = repository.object_format()
    updates = parse_updates(data, ID_LENGTH[object_format])
    isolate_scanner(repository)
    reason = environment.get(gate.OVERRIDE, "")
    dest = destination(url)
    if gate.is_private(dest):
        if trusted_route(repository, remote, url):
            return  # Nothing public is sent, so the override is neither used nor claimed.
        dest += "#untrusted-route"  # Never private: scanned as public.
    texts, names, tips = published_refs(repository, updates)
    owners: list[str] = []  # The commit each commit text belongs to, from texts[first] on.
    state = "unavailable"
    if tips:
        grafted, boundaries = repository.layout(object_format)
        if grafted:
            raise gate.PublishBlocked("OPSEC: grafted history present; push refused.")
        if public_repository is None:
            public_repository = CanonicalPublicRepository.from_catalog(dict(os.environ))
        head, state = public_history(repository, public_repository, object_format)
        exclusion = f"^{head}\n" if state == "present" else ""
        stdin = "".join(f"{sha}\n" for sha in tips) + exclusion
        pending = repository.text("rev-list", "--stdin", stdin=stdin).split()
        # git walks a shallow boundary commit as parentless. That truncates the
        # excluded history as much as the scanned one, so the excluded set is
        # never larger than the true public history, and a forged entry cannot
        # shrink the scan set. A commit the push sends but this walk misses
        # therefore sits behind a boundary that is itself in the scan set: on a
        # path from a sent tip to that commit, the first boundary is reached
        # and is not public, or the hidden commit, its ancestor, would be public
        # too. A boundary outside the scan set hides nothing the push sends.
        inside = sorted(boundaries.intersection(pending))
        if inside:
            positions = ",".join(f"commit[{sha[:12]}]" for sha in inside)
            raise gate.PublishBlocked(
                f"OPSEC: shallow boundary inside the scanned range ({positions}): history behind it "
                "cannot be scanned; deepen the clone (git fetch --deepen=<n>) or unshallow it "
                "(git fetch --unshallow); push refused."
            )
        for sha, parts in commit_texts(repository, pending):
            for part, text in parts:
                texts.append(text)
                names.append(f"commit[{sha[:12]}].{part}")
                owners.append(sha)
        print(
            f"OPSEC: push scan: {len(pending)} commit(s) scanned; public default-branch head {state} "
            f"({getattr(public_repository, 'calls', 0)} public repository call(s)).",
            file=sys.stderr,
        )
    first = len(texts) - len(owners)
    try:
        gate.check_texts(dest, texts, environment={}, field_names=names)
    except gate.PublishBlocked as error:
        if reason.strip() and error.indices:
            # Only a flagged push uses the override: its claimant is looked up
            # here, and the blocked texts are checked again with the reason so
            # the override is claimed once and logged before anything is sent.
            # A clean push never reaches this, so a failed lookup cannot refuse it.
            flagged = sorted(error.indices)
            gate.check_texts(
                dest,
                [texts[index] for index in flagged],
                environment={gate.OVERRIDE: reason},
                field_names=[names[index] for index in flagged],
                claimant=claimant(environment, reason),
            )
            return
        older = {owners[index - first] for index in error.indices if index >= first} - set(tips)
        if state == "absent here" and older:
            raise gate.PublishBlocked(
                f"{error} Hits are in history older than the pushed tips and the public default-branch "
                "head is not in this repository: fetching the public default branch lets the scan skip "
                "history that is already public."
            ) from None
        raise


def exec_caller_hook(arguments: list[str], data: bytes, environment: dict[str, str]) -> int:
    """Become the caller's own pre-push hook, as Git runs it without the pinned hooks path.

    The hook reads the same input from an unlinked temporary file, and its
    exit status goes to Git unchanged; like Git, nothing bounds its run time.
    Returns only when the hook cannot be started.
    """
    chain = str(HOOKS / "chain")
    try:
        with tempfile.TemporaryFile() as records:
            records.write(data)
            records.seek(0)
            os.dup2(records.fileno(), 0)
        os.execve(chain, [chain, "pre-push", *arguments], environment)
    except OSError:
        print("OPSEC: the caller's pre-push hook could not be started; push refused.", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None, *, stdin: bytes | None = None, public_repository=None, chain=None) -> int:
    """The pre-push hook: scan, then run the caller's hook; any failure refuses the push (non-zero)."""
    arguments = sys.argv[1:] if argv is None else argv
    environment = dict(os.environ)
    data = b""
    try:
        with deadline(scan_timeout(environment)):
            data = sys.stdin.buffer.read() if stdin is None else stdin
            scan_push(arguments, data, environment, public_repository=public_repository)
    except ScanTimeout:
        print("OPSEC: push scan timed out; push refused.", file=sys.stderr)
        return 1
    except gate.PublishBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception:
        print("OPSEC: push scan unavailable; push refused.", file=sys.stderr)
        return 1
    return (chain or exec_caller_hook)(arguments, data, gate.internal_environment(environment))


if __name__ == "__main__":
    raise SystemExit(main())
