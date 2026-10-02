"""Scan the text a git push would publish before it reaches a public remote.

The agent git shim executes this file for push commands. A dry run asks git
which refs the push names and where it sends them. For every public
destination the ref names, annotated tag names and messages and the whole raw
messages of every commit reachable from the pushed tips, with the tag names
and messages embedded in their mergetag headers, are scanned through
check_texts, except commits reachable from the head of the default branch of
the catalogue's canonical public repository (already public), and only when
every commit object reachable from it hashes to its id. That head comes
from one GitHub API read per push; nothing is cached between pushes, and
nothing the destination reports is evidence of what it already has.
Enumeration ignores replacement objects, grafts and commit-graph files, a
grafted repository is refused, a shallow one is refused when a boundary commit
is inside the scan set, an alternate shallow file is refused, and the scan's
own git calls run without tracing or prompts. File contents are not scanned.
Private remotes are exempt from the scan exactly as is_private decides.

A pre-push hook in the preview records the exact URL git pushes to. Every
destination, scanned public or exempt private, then receives its own push to
that URL with exactly the previewed objects and ref names (explicit <id>:<ref>
refspecs), without the command-scoped override, and a guard pre-push hook
refuses it unless git still resolves that URL, so no configuration change
after the preview (url, pushurl, insteadOf, mirror, push refspecs) can change
where or what is sent. The remote-tracking refs, upstreams and leases git
would derive from the remote name are applied explicitly. Git text from these
steps is never replayed.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Executed by the shim as a file, so imports do not depend on caller cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.opsec import prepublish as gate

# Global git options whose value may be the next argument (git.c handle_options).
GLOBAL_WITH_VALUE = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--config-env",
    "--attr-source",
    "--shallow-file",
}
# Push options whose value may be the next argument.
PUSH_WITH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec", "--recurse-submodules"}
# Every long option of git push (git push -h) and whether it takes a separate
# value. git also accepts unique abbreviations; the frozen push refuses them so
# the repository argument is found exactly.
PUSH_LONG = {
    "verbose": False,
    "quiet": False,
    "repo": True,
    "all": False,
    "branches": False,
    "mirror": False,
    "delete": False,
    "tags": False,
    "dry-run": False,
    "porcelain": False,
    "force": False,
    "force-with-lease": False,
    "force-if-includes": False,
    "recurse-submodules": True,
    "thin": False,
    "receive-pack": True,
    "exec": True,
    "set-upstream": False,
    "progress": False,
    "prune": False,
    "verify": False,
    "follow-tags": False,
    "signed": False,
    "atomic": False,
    "push-option": True,
    "ipv4": False,
    "ipv6": False,
}
PUSH_SHORT = set("vqdnfu46o")
# Options that choose refs or the repository: the preview already expanded them
# into the frozen refspecs. The upstream (-u) is recorded after the push, leases
# are frozen per ref, and the guard hook always runs (it chains the caller's).
FROZEN_AWAY = {
    "repo",
    "all",
    "branches",
    "mirror",
    "delete",
    "tags",
    "follow-tags",
    "prune",
    "set-upstream",
    "force-with-lease",
    "verify",
}
# Hooks paths of the preview (records the push URL) and of the delivered push (refuses any other URL).
HOOKS = Path(__file__).resolve().parent / "push_hooks"
# git's ref_rev_parse_rules: how a short name matches a full ref name.
REV_PARSE_RULES = ("{}", "refs/{}", "refs/tags/{}", "refs/heads/{}", "refs/remotes/{}", "refs/remotes/{}/HEAD")
# Fast-forward, forced update, new ref, up to date, rejected, deleted. Only a
# deletion publishes nothing: the others are the destination's verdict, which
# is not evidence of what the real push will send.
KNOWN_FLAGS = {" ", "+", "*", "=", "!", "-"}
COMMIT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# Hex length of a commit id per repository object format.
ID_LENGTH = {"sha1": 40, "sha256": 64}
# The canonical public repository's default branch and the id form GitHub reports for its head.
PUBLIC_DEFAULT_BRANCH = "main"
PUBLIC_HEAD = re.compile(r"[0-9a-f]{40}")
# Bound on the one public repository read of a push.
API_TIMEOUT = 10


def split_command(argv: list[str]) -> tuple[list[str], str | None, list[str]]:
    """Split git argv into global options, subcommand and its arguments."""
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in GLOBAL_WITH_VALUE:
            index += 2
        elif arg.startswith("-"):
            index += 1
        else:
            return argv[:index], arg, argv[index + 1 :]
    return argv, None, []


def _consumes_next(arg: str) -> bool:
    if arg in PUSH_WITH_VALUE:
        return True
    if arg.startswith("-") and not arg.startswith("--"):
        cluster = arg[1:]
        return cluster.find("o") == len(cluster) - 1 and bool(cluster)
    return False


def preview_arguments(rest: list[str]) -> list[str]:
    """Dry-run the same push; a trailing --verbose overrides any caller --quiet.

    A trailing --verify overrides any caller --no-verify, so the capture hook
    records every URL.
    """
    index = 0
    while index < len(rest):
        if rest[index] == "--":
            return ["--dry-run", "--porcelain", *rest[:index], "--verify", "--verbose", *rest[index:]]
        index += 2 if _consumes_next(rest[index]) else 1
    return ["--dry-run", "--porcelain", *rest, "--verify", "--verbose"]


@dataclass
class PushArguments:
    """git push arguments split for the frozen push."""

    kept: list[str] = field(default_factory=list)  # Options the frozen push keeps, values included.
    dry_run: bool = False
    quiet: bool = False
    force_if_includes: bool = False
    verify: bool = True
    receive_pack: bool = False  # --receive-pack or --exec given.
    # --force-with-lease values in order: None for the bare form, else <ref>[:<expect>].
    leases: list[str | None] = field(default_factory=list)


def _refuse_option() -> gate.PublishBlocked:
    return gate.PublishBlocked(
        "OPSEC: push option not recognised (abbreviated or unknown); spell git push options in full; push refused."
    )


def push_arguments(rest: list[str]) -> PushArguments:
    """Split git push arguments into kept options and the flag states that matter.

    The repository and refspecs are dropped (the frozen push names its own
    URL and refspecs), and so are the options in FROZEN_AWAY. Unknown or
    abbreviated options are refused.
    """
    parsed = PushArguments()
    index = 0
    while index < len(rest):
        arg = rest[index]
        index += 1
        if arg == "--":
            break
        if arg.startswith("--"):
            name, equals, _ = arg[2:].partition("=")
            negated = name.startswith("no-") and name[3:] in PUSH_LONG
            base = name[3:] if negated else name
            if base not in PUSH_LONG:
                raise _refuse_option()
            words = [arg]
            if PUSH_LONG[base] and not negated and not equals:
                if index >= len(rest):
                    raise _refuse_option()
                words.append(rest[index])
                index += 1
            if base == "force-with-lease":
                if negated:
                    parsed.leases.clear()
                else:
                    parsed.leases.append(arg.partition("=")[2] if equals else None)
            elif base in {"receive-pack", "exec"}:
                parsed.receive_pack = not negated
            elif base == "verify":
                parsed.verify = not negated
            elif base == "dry-run":
                parsed.dry_run = not negated
            elif base == "quiet":
                parsed.quiet = not negated
            elif base == "verbose" and not negated:
                parsed.quiet = False
            elif base == "force-if-includes":
                parsed.force_if_includes = not negated
            if base not in FROZEN_AWAY:
                parsed.kept += words
        elif arg.startswith("-") and arg != "-":
            keep = ""
            separate: list[str] = []
            for position, letter in enumerate(arg[1:], start=1):
                if letter not in PUSH_SHORT:
                    raise _refuse_option()
                if letter == "o":
                    keep += arg[position:]
                    if position == len(arg) - 1:
                        if index >= len(rest):
                            raise _refuse_option()
                        separate = [rest[index]]
                        index += 1
                    break
                if letter == "n":
                    parsed.dry_run = True
                elif letter in "qv":
                    parsed.quiet = letter == "q"
                if letter not in "du":
                    keep += letter
            if keep:
                parsed.kept += ["-" + keep, *separate]
    return parsed


def parse_porcelain(output: str) -> list[dict]:
    """Return one section per destination URL; unknown shapes refuse the push.

    upstreams counts the upstream settings git reports it would make (-u or
    push.autoSetupRemote), which the frozen push reproduces.
    """
    sections: list[dict] = []
    for line in output.splitlines():
        if line.startswith("To "):
            sections.append({"url": line[3:], "updates": [], "upstreams": 0})
        elif line.startswith("Would set upstream of "):
            if sections:
                sections[-1]["upstreams"] += 1
        elif line == "Done" or not line:
            continue
        elif sections and line.count("\t") >= 1 and line[:1] in KNOWN_FLAGS and line[1:2] == "\t":
            flag, refs, *_ = line.split("\t", 2)
            source, separator, target = refs.rpartition(":")
            if not separator or not target:
                raise gate.PublishBlocked("OPSEC: push preview unparseable; push refused.")
            sections[-1]["updates"].append((flag, source, target))
        else:
            raise gate.PublishBlocked("OPSEC: push preview unparseable; push refused.")
    return sections


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
    """The caller's environment for the scan's own git calls.

    No override, tracing, credential prompts or partial-clone object fetches;
    replacement objects and grafts disabled. A trace2 target of "0" in the environment outranks one set in
    system or global configuration. Messages are untranslated, so the preview
    parses in any locale.
    """
    scrubbed = {
        key: value
        for key, value in environment.items()
        if key != "LU_OPSEC_OVERRIDE" and not key.startswith("GIT_TRACE") and key != "GIT_CURL_VERBOSE"
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


class Repository:
    """Read-only object queries through the real git with the caller's global options."""

    def __init__(self, real_git: str, global_options: list[str], environment: dict[str, str]):
        # Replacement objects change what readers see but not what a pack sends,
        # and a commit-graph file is a local cache of parents that git trusts
        # without rehashing, so every query reads the original objects (the
        # flag and the trailing -c options outrank caller configuration).
        self.base = [
            real_git,
            "--no-replace-objects",
            *global_options,
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

    def object(self, revision: str) -> str | None:
        result = self.run("rev-parse", "--verify", "--quiet", revision)
        if result.returncode:
            return None
        return result.stdout.decode().strip() or None

    def ref(self, name: str) -> str | None:
        """The id the full ref name stores, without rev-parse's name expansion; None when absent."""
        result = self.run("show-ref", "--verify", "--hash", name)
        return (result.stdout.decode().strip() or None) if result.returncode == 0 else None

    def config(self) -> list[tuple[str, str | None]]:
        """Every configuration entry in reading order; a valueless entry has value None."""
        entries = []
        for entry in self.text("config", "--list", "-z").split("\0"):
            if entry:
                key, newline, value = entry.partition("\n")
                entries.append((key, value if newline else None))
        return entries

    def layout(self) -> tuple[bool, set[str], str]:
        """Whether grafts alter commit parents, the shallow boundary commits and the object format.

        git's own path resolution names both files, so a linked worktree reads
        the shallow file of the shared repository.
        """
        # Resolve the grafts path with the caller's GIT_GRAFT_FILE: the file the real push reads.
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
            "--show-object-format",
            environment=environment,
        )
        grafts, shallow, object_format = output.splitlines()
        if object_format not in ID_LENGTH:
            raise gate.PublishBlocked("OPSEC: repository object format unknown; push refused.")
        return _grafts_present(grafts), shallow_boundaries(shallow, ID_LENGTH[object_format]), object_format


class CanonicalPublicRepository:
    """The default-branch head of the catalogue's public repository, read through the typed publisher reads.

    The repository comes from the catalogue, never from the push URL or local
    git configuration, and the answer comes from the GitHub API. Only a
    well-formed reply bound to the question counts; a failure, timeout, rate
    limit, 404 or malformed or inconsistent body is no answer.
    """

    def __init__(self, repo: str, environment: dict[str, str], *, runner=None, timeout: int = API_TIMEOUT):
        self.repo = repo
        self.environment = {key: value for key, value in environment.items() if key != "LU_OPSEC_OVERRIDE"}
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
    scanned only up to it. Reading the raw object scans
    every byte of the message at no more cost than refusing such messages,
    which would also need the raw object to see the NUL. A merge of a signed
    tag carries the whole tag object in a mergetag header, so its name and
    message are published with the commit and scanned as its fields.
    Identity lines and signatures are not.
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
    repository: Repository, updates: list[tuple], objects: dict[str, str]
) -> tuple[list[str], list[str], list[str]]:
    """Ref names and annotated tag names and messages the push publishes, and the commits its refs name.

    objects maps each pushed source to the object it resolved to, once; the
    frozen push sends exactly those objects. The name inside a tag object (its
    tag header) is published with it and can differ from the ref it is pushed
    to, so every tag object on the way from a pushed ref to its target, nested
    tags included, has its name scanned. Only commits are ever excluded as
    already public; these texts are always scanned.
    """
    texts: list[str] = []
    names: list[str] = []
    tips: list[str] = []
    seen_tags: set[str] = set()
    for number, (flag, source, target) in enumerate(updates, start=1):
        if flag == "-" or not source:
            continue  # A deletion publishes no text.
        kind, short = _short_ref(target)
        texts.append(short)
        names.append(f"{kind}[{number}].name")
        current = objects[source]
        while repository.text("cat-file", "-t", current).strip() == "tag":
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
        if repository.text("cat-file", "-t", current).strip() == "commit":
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


@dataclass
class Push:
    """One inspected destination: its URL, the frozen push to it and the tracking refs a success updates."""

    url: str
    argv: list[str]
    tracking: list[tuple[str, str | None]] = field(default_factory=list)  # (tracking ref, id; None deletes).


@dataclass
class Delivery:
    """What runs after the scan: one frozen push per inspected destination, then the local bookkeeping."""

    git: list[str]  # The real git and the caller's global options.
    pushes: list[Push]  # Destinations the push names no refs for are left out.
    status: int = 0  # The preview's exit status, returned when nothing is sent.
    remote: str = ""  # The remote name git reported, as git push -u records it.
    hook: str = ""  # The caller's pre-push hook the guard runs; empty for none or --no-verify.
    ssh: str = "ssh"  # The ssh command git chose at the preview, pinned as GIT_SSH_COMMAND.
    upstreams: list[tuple[str, str]] = field(default_factory=list)  # (local branch, destination ref).
    rebase: bool = False
    quiet: bool = False
    dry_run: bool = False


def read_captures(path: str) -> list[tuple[str, str]]:
    """(remote name, URL) for each destination, in push order, as the capture hook recorded them."""
    with open(path, "rb") as handle:
        fields = handle.read().decode("utf-8", "surrogateescape").split("\0")
    if fields.pop() != "" or len(fields) % 2:
        raise gate.PublishBlocked("OPSEC: push destinations not recorded; push refused.")
    return list(zip(fields[::2], fields[1::2], strict=True))


def refname_match(short: str, full: str) -> bool:
    """git's refname_match: whether short names full under the rev-parse rules."""
    return any(rule.format(short) == full for rule in REV_PARSE_RULES)


def _glob(pattern: str, name: str) -> str | None:
    """The part of name the single * of a refspec pattern matches; name itself for an exact match."""
    if "*" not in pattern:
        return name if pattern == name else None
    prefix, _, suffix = pattern.partition("*")
    if len(name) < len(prefix) + len(suffix) or not (name.startswith(prefix) and name.endswith(suffix)):
        return None
    return name[len(prefix) : len(name) - len(suffix)]


def tracking_ref(fetch: list[str], name: str) -> str | None:
    """The remote-tracking ref for remote ref name under the remote's fetch refspecs (remote_find_tracking).

    A negative refspec (^<pattern>) matching name omits it; otherwise the
    first refspec with a destination whose source matches decides.
    """
    specs = [spec.removeprefix("+") for spec in fetch]
    if any(spec.startswith("^") and _glob(spec[1:], name) is not None for spec in specs):
        return None
    for spec in specs:
        source, colon, target = spec.partition(":")
        if spec.startswith("^") or not colon or not target:
            continue
        middle = _glob(source, name)
        if middle is not None:
            return target.replace("*", middle, 1) if "*" in source else target
    return None


def leased(repository: Repository, leases: list[str | None], updates: list[tuple], fetch: list[str]) -> dict[str, str]:
    """The expected id of each updated ref a caller's lease covers, as git applies --force-with-lease.

    git's apply_cas: the first <ref>[:<expect>] entry whose ref names the
    destination ref decides, and a bare --force-with-lease covers the rest. An
    entry without <expect> expects the remote-tracking ref. Both are read now,
    so the frozen push to a URL (which has no tracking refs) enforces the same
    lease; an empty expected id means the ref must not exist.
    """
    expected_ids = {}
    for _, _, target in updates:
        entry = next(
            (lease for lease in leases if lease is not None and refname_match(lease.split(":")[0], target)), ""
        )
        if not entry and None not in leases:
            continue
        _, colon, expect = entry.partition(":")
        if colon:
            expected = repository.object(expect) if expect else ""
            if expected is None:
                raise gate.PublishBlocked("OPSEC: --force-with-lease expected value unresolved; push refused.")
        else:
            tracking = tracking_ref(fetch, target)
            expected = (repository.ref(tracking) if tracking else None) or ""
        expected_ids[target] = expected
    return expected_ids


def upstream_branches(repository: Repository, updates: list[tuple]) -> list[tuple[str, str]]:
    """(local branch, destination ref) pairs git push -u would record, by git's set_upstreams rule.

    Both sides must be branches, a symbolic source (HEAD) counts as the branch
    it names, and deletions and rejected updates record nothing.
    """
    found = []
    for flag, source, target in updates:
        if flag in {"-", "!"} or not source or not target.startswith("refs/heads/"):
            continue
        symbolic = repository.run("symbolic-ref", "-q", source)
        local = symbolic.stdout.decode("utf-8", "replace").strip() if symbolic.returncode == 0 else source
        if local.startswith("refs/heads/"):
            found.append((local[len("refs/heads/") :], target))
    return found


def freeze(
    repository: Repository, global_options: list[str], rest: list[str], sections: list[dict], remote: str, status: int
) -> tuple[dict[str, str], Delivery]:
    """The object each pushed source resolves to, and one frozen push per inspected destination.

    Each push goes to the URL the preview's hook recorded (section["push_url"])
    and names every update as an explicit <id>:<ref> refspec (with + when the
    preview reported a forced update, :<ref> for a deletion), so a ref moved by
    another process, a destination that gains a matching branch, or a remote
    reconfigured after the preview cannot change what is sent or where; the
    guard hook refuses the push if git resolves that URL to another one.
    Ref-selecting options are dropped (the refspecs replace them),
    --no-follow-tags stops push.followTags adding tags, and leases are frozen
    per ref (leased; a leased ref is never sent with +, which would defeat the
    lease, so a caller's own +refspec under a lease keeps the lease). What git
    derives from the remote name is applied explicitly: the remote's
    receivepack, the ssh command, the remote-tracking refs a success updates,
    and the upstreams git reported (recorded after the push; git records none
    for an id source). Forms that cannot be carried to a URL are refused:
    --force-if-includes (it needs the local branch as the source), a remote
    with a vcs helper or proxy, and abbreviated options.
    """
    arguments = push_arguments(rest)
    if arguments.force_if_includes:
        raise gate.PublishBlocked(
            "OPSEC: --force-if-includes cannot apply to the frozen push; use "
            "--force-with-lease=<ref>:<expected id>; push refused."
        )
    entries = repository.config()

    def setting(key: str) -> list[str | None]:
        return [value for name, value in entries if name == key]

    if setting(f"remote.{remote}.vcs") or setting(f"remote.{remote}.proxy"):
        raise gate.PublishBlocked(
            "OPSEC: the remote's vcs or proxy setting cannot be carried to the inspected URL; push refused."
        )
    fetch = [value for value in setting(f"remote.{remote}.fetch") if value]
    receive = setting(f"remote.{remote}.receivepack")
    options = list(arguments.kept)
    if receive and receive[-1] and not arguments.receive_pack:
        options.append(f"--receive-pack={receive[-1]}")
    objects: dict[str, str] = {}
    for section in sections:
        for flag, source, _ in section["updates"]:
            if flag != "-" and source and source not in objects:
                resolved = repository.object(source)
                if resolved is None:
                    raise gate.PublishBlocked("OPSEC: pushed object unresolved; push refused.")
                objects[source] = resolved
    upstreams: dict[str, str] = {}
    if any(section["upstreams"] for section in sections):
        for section in sections:
            found = upstream_branches(repository, section["updates"])
            if len(found) != section["upstreams"]:
                raise gate.PublishBlocked(
                    "OPSEC: the upstream git would set cannot be reproduced for the frozen push; push without "
                    "-u and set it with git branch --set-upstream-to; push refused."
                )
            upstreams.update(found)
    git = [repository.base[0], *global_options]
    pushes = []
    for section in sections:
        updates = section["updates"]
        if not updates:
            continue  # A push without refspecs would fall back to the default selection.
        leases = leased(repository, arguments.leases, updates, fetch)
        # A + refspec overrides a lease in git, and a held lease allows the forced update itself.
        refspecs = [
            f":{target}"
            if flag == "-" or not source
            else f"{'+' if flag == '+' and target not in leases else ''}{objects[source]}:{target}"
            for flag, source, target in updates
        ]
        argv = [
            *git,
            "-c",
            f"core.hooksPath={HOOKS / 'guard'}",
            "push",
            *options,
            *(f"--force-with-lease={target}:{expected}" for target, expected in leases.items()),
            "--verify",
            "--no-follow-tags",
            "--",  # Before the URL too: a URL starting with - is never read as an option.
            section["push_url"],
            *refspecs,
        ]
        tracking = [
            (ref, None if flag == "-" or not source else objects[source])
            for flag, source, target in updates
            if (ref := tracking_ref(fetch, target))
        ]
        pushes.append(Push(url=section["push_url"], argv=argv, tracking=[] if arguments.dry_run else tracking))
    hook = ""
    if arguments.verify:
        path = repository.text("rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-push").strip()
        hook = path if os.path.isfile(path) and os.access(path, os.X_OK) else ""
    rebase = (setting("branch.autosetuprebase") or [""])[-1] or ""
    # git's order (connect.c): GIT_SSH_COMMAND, core.sshCommand, GIT_SSH, ssh. Pinned so a
    # core.sshCommand written after the preview cannot route an unchanged ssh URL elsewhere.
    caller = repository.caller
    configured = (setting("core.sshcommand") or [None])[-1]
    ssh = caller.get("GIT_SSH_COMMAND") or configured or shlex.quote(caller.get("GIT_SSH") or "ssh")
    delivery = Delivery(
        git=git,
        pushes=pushes,
        status=status,
        remote=remote,
        hook=hook,
        ssh=ssh,
        upstreams=[] if arguments.dry_run else list(upstreams.items()),
        rebase=rebase.lower() in {"always", "remote"},
        quiet=arguments.quiet,
        dry_run=arguments.dry_run,
    )
    return objects, delivery


def scan_push(
    real_git: str, argv: list[str], environment: dict[str, str], *, public_repository=None
) -> Delivery | None:
    """The frozen pushes to run, or None when the command is not a push.

    Raises PublishBlocked unless every public text of this push is clean,
    already public or overridden. public_repository reports the canonical
    public default-branch head; by default it is built from the catalogue, and
    only when the push sends commits.
    """
    global_options, command, rest = split_command(argv)
    if command != "push":
        return None
    index = 0
    while index < len(global_options):
        if global_options[index] == "--shallow-file":
            # The scan reads the repository's own shallow file; another one would go unchecked.
            raise gate.PublishBlocked("OPSEC: --shallow-file is not supported for a scanned push; push refused.")
        index += 2 if global_options[index] in GLOBAL_WITH_VALUE else 1
    if "GIT_SHALLOW_FILE" in environment:
        # git walks the file this names, while git rev-parse --git-path still names the repository's own.
        raise gate.PublishBlocked("OPSEC: GIT_SHALLOW_FILE is not supported for a scanned push; push refused.")
    repository = Repository(real_git, global_options, environment)
    if not all(os.access(HOOKS / name / "pre-push", os.X_OK) for name in ("capture", "guard")):
        raise gate.PublishBlocked("OPSEC: push hooks not executable; push refused.")
    descriptor, capture = tempfile.mkstemp(prefix="lu-opsec-push-")
    os.close(descriptor)
    try:
        # The capture hook records the remote name and the exact URL of every destination, in push order.
        preview = repository.run(
            "-c",
            f"core.hooksPath={HOOKS / 'capture'}",
            "push",
            *preview_arguments(rest),
            timeout=300,
            environment={**repository.environment, "LU_OPSEC_PUSH_CAPTURE": capture},
        )
        captures = read_captures(capture)
    finally:
        os.unlink(capture)
    sections = parse_porcelain(preview.stdout.decode("utf-8", "replace"))
    if not sections:
        # git's own error text can quote the refspec; name only the phase.
        raise gate.PublishBlocked(f"OPSEC: push preview failed (exit {preview.returncode}); push refused.")
    # git prints each destination's To line (its URL without userinfo) in the order it ran the hook.
    if (
        len(captures) != len(sections)
        or len({remote for remote, _ in captures}) != 1
        or any(
            destination(url) != destination(section["url"])
            for (_, url), section in zip(captures, sections, strict=True)
        )
    ):
        raise gate.PublishBlocked("OPSEC: push destinations disagree with the preview; push refused.")
    public: list[str] = []
    private: list[str] = []
    for section, (_, url) in zip(sections, captures, strict=True):
        section["push_url"] = url
        dest = destination(url)
        section["public"] = not gate.is_private(dest)
        (public if section["public"] else private).append(dest)
    objects, delivery = freeze(repository, global_options, rest, sections, captures[0][0], preview.returncode)
    if not public:
        gate.check_texts(private[0], [], environment=environment)  # Records a supplied override.
        return delivery
    updates = [update for section in sections if section["public"] for update in section["updates"]]
    texts, names, tips = published_refs(repository, updates, objects)
    owners: list[str] = []  # The commit each commit text belongs to, from texts[first] on.
    head, state = None, "unavailable"
    if tips:
        grafted, boundaries, object_format = repository.layout()
        if grafted:
            raise gate.PublishBlocked("OPSEC: grafted history present; push refused.")
        if public_repository is None:
            public_repository = CanonicalPublicRepository.from_catalog(environment)
        head, state = public_history(repository, public_repository, object_format)
        exclusion = f"^{head}\n" if state == "present" else ""
        stdin = "".join(f"{sha}\n" for sha in tips) + exclusion
        pending = repository.text("rev-list", "--stdin", stdin=stdin).split()
        # git walks a shallow boundary commit as parentless. That truncates the
        # excluded history as much as the scanned one, so the excluded set is
        # never larger than the true public history, and a forged entry cannot
        # shrink the scan set. A commit the push sends but this walk misses
        # therefore sits behind a boundary that is itself in the scan set: on a
        # path from a pushed tip to that commit, the first boundary is reached
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
        gate.check_texts(",".join(dict.fromkeys(public)), texts, environment=environment, field_names=names)
    except gate.PublishBlocked as error:
        older = {owners[index - first] for index in error.indices if index >= first} - set(tips)
        if state == "absent here" and older:
            raise gate.PublishBlocked(
                f"{error} Hits are in history older than the pushed tips and the public default-branch "
                "head is not in this repository: fetching the public default branch lets the scan skip "
                "history that is already public."
            ) from None
        raise
    return delivery


def record_upstreams(delivery: Delivery, environment: dict[str, str], run) -> None:
    """Record each upstream as git push -u does (install_branch_config), once the whole push succeeded."""
    for local, merge in delivery.upstreams:
        settings = [(f"branch.{local}.remote", delivery.remote), (f"branch.{local}.merge", merge)]
        if delivery.rebase:
            settings.append((f"branch.{local}.rebase", "true"))
        if any(
            run([*delivery.git, "config", "--replace-all", key, value], env=environment, check=False).returncode
            for key, value in settings
        ):
            print("OPSEC: pushed; an upstream branch configuration was not written.", file=sys.stderr)
        elif not delivery.quiet:
            short = merge[len("refs/heads/") :]
            suffix = " by rebasing" if delivery.rebase else ""
            print(f"branch '{local}' set up to track '{delivery.remote}/{short}'{suffix}.")


def deliver(delivery: Delivery, environment: dict[str, str], run) -> int:
    """Run each frozen push with its guard, then update tracking refs and record upstreams as git push does.

    git updates a destination's remote-tracking refs when its push succeeds;
    the upstreams are recorded once every push succeeded. The first failing
    push's status is returned.
    """
    status = 0
    for push in delivery.pushes:
        guarded = {
            **environment,
            "LU_OPSEC_PUSH_URL": push.url,
            "LU_OPSEC_PUSH_REMOTE": delivery.remote,
            "LU_OPSEC_PUSH_HOOK": delivery.hook,
            "GIT_SSH_COMMAND": delivery.ssh,
        }
        guarded.pop("LU_OPSEC_PUSH_CAPTURE", None)
        result = run(push.argv, env=guarded, check=False).returncode
        if result:
            status = status or result
            continue
        for ref, sha in push.tracking:
            update = ["update-ref", "-d", ref] if sha is None else ["update-ref", "-m", "update by push", ref, sha]
            if run([*delivery.git, *update], env=environment, check=False).returncode:
                print("OPSEC: pushed; a remote-tracking ref was not updated.", file=sys.stderr)
    if status == 0:
        record_upstreams(delivery, environment, run)
    return status


def main(argv: list[str] | None = None, *, execute=os.execve, run=subprocess.run, public_repository=None) -> int:
    real_git, *args = sys.argv[1:] if argv is None else argv
    environment = dict(os.environ)
    try:
        delivery = scan_push(real_git, args, environment, public_repository=public_repository)
    except gate.PublishBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("OPSEC: push scan unavailable; push refused.", file=sys.stderr)
        return 2
    environment.pop("LU_OPSEC_OVERRIDE", None)
    if delivery is None:
        execute(real_git, [real_git, *args], environment)
        return 0
    if not delivery.pushes:
        print("OPSEC: the push names no refs; nothing sent.", file=sys.stderr)
        return delivery.status
    return deliver(delivery, environment, run)


if __name__ == "__main__":
    raise SystemExit(main())
