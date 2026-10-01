"""Scan the text a git push would publish before it reaches a public remote.

The agent git shim executes this file for push commands. A dry run asks git
which refs the push names and where it sends them. For every public
destination the ref names, annotated tag names and messages and the whole raw
messages of every commit reachable from the pushed tips, with the tag names
and messages embedded in their mergetag headers, are scanned through
check_texts, except commits reachable from the head of the default branch of
the catalogue's canonical public repository (already public). That head comes
from one GitHub API read per push; nothing is cached between pushes, and
nothing the destination reports is evidence of what it already has.
Enumeration ignores replacement objects, grafts and commit-graph files, a
grafted or shallow repository is refused, and the scan's own git calls run
without tracing or prompts. File contents are not scanned. Private remotes are
exempt exactly as is_private decides. The real push runs only after a clean
scan, without the command-scoped override. Git text from these steps is never
replayed.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

# Executed by the shim as a file, so imports do not depend on caller cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.opsec import prepublish as gate

# Global git options whose value may be the next argument (git.c handle_options).
GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--attr-source"}
# Push options whose value may be the next argument.
PUSH_WITH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec", "--recurse-submodules"}
# Fast-forward, forced update, new ref, up to date, rejected, deleted. Only a
# deletion publishes nothing: the others are the destination's verdict, which
# is not evidence of what the real push will send.
KNOWN_FLAGS = {" ", "+", "*", "=", "!", "-"}
COMMIT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
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
    """Dry-run the same push; a trailing --verbose overrides any caller --quiet."""
    index = 0
    while index < len(rest):
        if rest[index] == "--":
            return ["--dry-run", "--porcelain", "--no-verify", *rest[:index], "--verbose", *rest[index:]]
        index += 2 if _consumes_next(rest[index]) else 1
    return ["--dry-run", "--porcelain", "--no-verify", *rest, "--verbose"]


def parse_porcelain(output: str) -> list[dict]:
    """Return one section per destination URL; unknown shapes refuse the push."""
    sections: list[dict] = []
    for line in output.splitlines():
        if line.startswith("To "):
            sections.append({"url": line[3:], "updates": []})
        elif line == "Done" or not line or line.startswith("Would set upstream of "):
            continue  # --set-upstream reports local configuration, not published text.
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
    system or global configuration.
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

    def layout(self) -> tuple[bool, bool]:
        """Whether grafts alter commit parents, whether history is shallow."""
        # Resolve the grafts path with the caller's GIT_GRAFT_FILE: the file the real push reads.
        environment = {key: value for key, value in self.environment.items() if key != "GIT_GRAFT_FILE"}
        if "GIT_GRAFT_FILE" in self.caller:
            environment["GIT_GRAFT_FILE"] = self.caller["GIT_GRAFT_FILE"]
        output = self.text(
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "info/grafts",
            "--is-shallow-repository",
            environment=environment,
        )
        grafts, shallow = output.splitlines()
        return _grafts_present(grafts), shallow == "true"


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
    output = repository.raw("cat-file", "--batch", stdin="".join(f"{sha}\n" for sha in shas))
    found: list[tuple[str, list[tuple[str, str]]]] = []
    position = 0
    try:
        for sha in shas:
            end = output.index(b"\n", position)
            name, kind, size = output[position:end].decode("ascii").split(" ")
            start = end + 1
            stop = start + int(size)
            if name != sha or kind != "commit" or output[stop : stop + 1] != b"\n":
                raise ValueError
            fields, message = split_object(output[start:stop], f"commit[{sha[:12]}]")
            parts = [("message", message)]
            embedded = [value for key, value in fields if key == b"mergetag"]
            for number, value in enumerate(embedded, start=1):
                field = f"mergetag[{number}]"
                tag_fields, tag_message = split_object(value, f"commit[{sha[:12]}].{field}")
                parts += [(f"{field}.tagname", tag_name(tag_fields)), (f"{field}.message", tag_message)]
            found.append((sha, parts))
            position = stop + 1
    except (ValueError, UnicodeError):
        raise gate.PublishBlocked("OPSEC: push scan commit read malformed; push refused.") from None
    if position != len(output):
        raise gate.PublishBlocked("OPSEC: push scan commit read malformed; push refused.")
    return found


def published_refs(repository: Repository, updates: list[tuple]) -> tuple[list[str], list[str], list[str]]:
    """Ref names and annotated tag names and messages one destination receives, and the commits its refs name.

    The name inside a tag object (its tag header) is published with it and can
    differ from the ref it is pushed to, so every tag object on the way from
    a pushed ref to its target, nested tags included, has its name scanned.
    Only commits are ever excluded as already public; these texts are always scanned.
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
        current = repository.object(source)
        if current is None:
            raise gate.PublishBlocked("OPSEC: pushed object unresolved; push refused.")
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


def public_history(repository: Repository, client) -> tuple[str | None, bool]:
    """(head, present): the canonical public default-branch head, and whether its commit is here.

    Object ids are content addressed and a commit id covers its parents' ids,
    so every commit reachable from the authoritative public head is public, and
    no local ref, URL rewrite or object can make a commit look reachable from
    it without a hash collision (replacement objects, grafts and commit-graph
    files are off; shallow repositories are refused). No answer, or a head
    that is not here (never fetched, as GIT_NO_LAZY_FETCH holds), excludes
    nothing.
    """
    head = client.default_head() if client is not None else None
    present = head is not None and repository.object(f"{head}^{{commit}}") == head
    return head, present


def scan_push(real_git: str, argv: list[str], environment: dict[str, str], *, public_repository=None) -> None:
    """Raise PublishBlocked unless every public text of this push is clean, already public or overridden.

    public_repository reports the canonical public default-branch head; by
    default it is built from the catalogue, and only when the push sends commits.
    """
    global_options, command, rest = split_command(argv)
    if command != "push":
        return
    repository = Repository(real_git, global_options, environment)
    preview = repository.run("push", *preview_arguments(rest), timeout=300)
    sections = parse_porcelain(preview.stdout.decode("utf-8", "replace"))
    if not sections:
        # git's own error text can quote the refspec; name only the phase.
        raise gate.PublishBlocked(f"OPSEC: push preview failed (exit {preview.returncode}); push refused.")
    public: list[str] = []
    private: list[str] = []
    texts: list[str] = []
    names: list[str] = []
    tips: list[str] = []
    for section in sections:
        # git prints its own push URL (after insteadOf and pushInsteadOf) without userinfo.
        dest = destination(section["url"])
        if gate.is_private(dest):
            private.append(dest)
            continue
        public.append(dest)
        found, labels, pushed = published_refs(repository, section["updates"])
        texts += found
        names += labels
        tips += pushed
    owners: list[str] = []  # The commit each commit text belongs to, from texts[first] on.
    head, present = None, False
    if tips:
        grafted, shallow = repository.layout()
        if grafted:
            raise gate.PublishBlocked("OPSEC: grafted history present; push refused.")
        if shallow:
            raise gate.PublishBlocked("OPSEC: shallow history cannot be scanned in full; push refused.")
        if public_repository is None:
            public_repository = CanonicalPublicRepository.from_catalog(environment)
        head, present = public_history(repository, public_repository)
        exclusion = f"^{head}\n" if present else ""
        stdin = "".join(f"{sha}\n" for sha in tips) + exclusion
        pending = repository.text("rev-list", "--stdin", stdin=stdin).split()
        for sha, parts in commit_texts(repository, pending):
            for field, text in parts:
                texts.append(text)
                names.append(f"commit[{sha[:12]}].{field}")
                owners.append(sha)
        state = "present" if present else "absent here" if head else "unavailable"
        print(
            f"OPSEC: push scan: {len(pending)} commit(s) scanned; public default-branch head {state} "
            f"({getattr(public_repository, 'calls', 0)} public repository call(s)).",
            file=sys.stderr,
        )
    first = len(texts) - len(owners)
    label = ",".join(dict.fromkeys(public)) if public else private[0]
    try:
        gate.check_texts(label, texts, environment=environment, field_names=names)
    except gate.PublishBlocked as error:
        older = {owners[index - first] for index in error.indices if index >= first} - set(tips)
        if head is not None and not present and older:
            raise gate.PublishBlocked(
                f"{error} Hits are in history older than the pushed tips and the public default-branch "
                "head is not in this repository: fetching the public default branch lets the scan skip "
                "history that is already public."
            ) from None
        raise


def main(argv: list[str] | None = None, *, execute=os.execve, public_repository=None) -> int:
    real_git, *args = sys.argv[1:] if argv is None else argv
    environment = dict(os.environ)
    try:
        scan_push(real_git, args, environment, public_repository=public_repository)
    except gate.PublishBlocked as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("OPSEC: push scan unavailable; push refused.", file=sys.stderr)
        return 2
    environment.pop("LU_OPSEC_OVERRIDE", None)
    execute(real_git, [real_git, *args], environment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
