"""Scan the text a git push would publish before it reaches a public remote.

The agent git shim executes this file for push commands. A dry run asks git
which refs the push names and where it sends them. For every public
destination the ref names, annotated tag names and messages and the whole raw
messages of every commit reachable from the pushed tips, with the tag names
and messages embedded in their mergetag headers, are scanned through check_texts, except
commits that this machine's earlier push scans found clean (CleanCache, kept
in the repository's common git directory). A commit whose message has a
blocking finding is excused only when the catalogue's canonical public
repository reports it reachable from its default branch (already public);
those answers are cached as well, failures and unknown commits are not.
Nothing the destination reports is evidence of what it already has. Enumeration ignores replacement objects and
grafts, a grafted or shallow repository is refused, and the scan's own git
calls run without tracing or prompts. File contents are not scanned. Private
remotes are exempt exactly as is_private decides. The real push runs only
after a clean scan, without the command-scoped override. Git text from these
steps is never replayed.
"""

from __future__ import annotations

import contextlib
import fcntl
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
CACHE_NAME = "lu-push-scan-clean"
PUBLIC_CACHE_NAME = "lu-push-scan-public"
COMMIT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
# Bounds on asking the canonical public repository during one push.
API_TIMEOUT = 10
COMPARE_LIMIT = 20


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
        # so every query reads the original objects (the flag and the trailing
        # -c outrank caller configuration).
        self.base = [
            real_git,
            "--no-replace-objects",
            *global_options,
            "-c",
            "core.useReplaceRefs=false",
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

    def layout(self) -> tuple[Path, bool, bool]:
        """Common git directory, whether grafts alter commit parents, whether history is shallow."""
        # Resolve the grafts path with the caller's GIT_GRAFT_FILE: the file the real push reads.
        environment = {key: value for key, value in self.environment.items() if key != "GIT_GRAFT_FILE"}
        if "GIT_GRAFT_FILE" in self.caller:
            environment["GIT_GRAFT_FILE"] = self.caller["GIT_GRAFT_FILE"]
        output = self.text(
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
            "--git-path",
            "info/grafts",
            "--is-shallow-repository",
            environment=environment,
        )
        common, grafts, shallow = output.splitlines()
        return Path(common), _grafts_present(grafts), shallow == "true"


class CleanCache:
    """Commit ids whose messages this machine's push scans found clean.

    A header line binds the file to the matcher fingerprint, then one commit id
    per line. Commits are content-addressed, so an id always names the same
    message. An unreadable, malformed or foreign-matcher file holds nothing:
    every reachable commit is scanned, and a scan that skipped nothing replaces
    the file. Writers hold an exclusive lock on a sidecar file and readers a
    shared one, so concurrent pushes never interleave or read half a line.
    The same format under PUBLIC_CACHE_NAME holds hit commits the canonical
    public repository reported already public.
    """

    def __init__(self, directory: Path, fingerprint: str, name: str = CACHE_NAME):
        self.name = name
        self.path = directory / name
        self.lock_path = directory / f"{name}.lock"
        self.header = f"{name} 1 {fingerprint}"

    @contextlib.contextmanager
    def _locked(self, mode: int):
        descriptor = os.open(self.lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(descriptor, mode)
            yield
        finally:
            os.close(descriptor)

    def _load(self) -> set[str] | None:
        """Ids of a well-formed file for this matcher, else None; FileNotFoundError when absent."""
        descriptor = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        with os.fdopen(descriptor, "rb") as stream:
            data = stream.read()
        try:
            lines = data.decode("ascii").split("\n")
        except UnicodeError:
            return None
        if lines.pop() != "" or not lines or lines[0] != self.header:
            return None
        ids = lines[1:]
        return set(ids) if all(COMMIT_ID.fullmatch(line) for line in ids) else None

    def read(self) -> tuple[set[str], bool]:
        """(cached ids, unusable). An absent file is empty and usable; any defect is unusable."""
        try:
            with self._locked(fcntl.LOCK_SH):
                ids = self._load()
        except FileNotFoundError:
            return set(), False
        except OSError:
            return set(), True
        return (set(), True) if ids is None else (ids, False)

    def record(self, ids: list[str], *, full: bool) -> bool:
        """Append clean ids; an absent or unusable file is replaced only by a scan that skipped nothing."""
        with self._locked(fcntl.LOCK_EX):
            try:
                current = self._load()
            except OSError:
                current = None
            if current is not None:
                fresh = [sha for sha in dict.fromkeys(ids) if sha not in current]
                if fresh:
                    descriptor = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_CLOEXEC)
                    with os.fdopen(descriptor, "ab") as stream:
                        stream.write("".join(f"{sha}\n" for sha in fresh).encode("ascii"))
                        stream.flush()
                        os.fsync(stream.fileno())
                return True
            if not full:
                return False
            temporary = self.path.with_name(f"{self.name}.{os.getpid()}.tmp")
            try:
                descriptor = os.open(
                    temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600
                )
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write("".join(f"{line}\n" for line in [self.header, *dict.fromkeys(ids)]).encode("ascii"))
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            finally:
                temporary.unlink(missing_ok=True)
            return True


class CanonicalPublicRepository:
    """What the catalogue's public repository holds, read through the typed publisher reads.

    The repository comes from the catalogue, never from the push URL or local
    git configuration, and every answer comes from the GitHub API. Only a
    well-formed positive answer counts; a failure, timeout, rate limit,
    unknown commit or malformed body never does.
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

    def _read(self, operation: str, **fields) -> tuple[int, object]:
        from scripts.publish.github import read

        self.calls += 1
        result = read(
            operation,
            repo=self.repo,
            runner=self.runner,
            env=dict(self.environment),
            capture_output=True,
            text=True,
            timeout=self.timeout,
            **fields,
        )
        return result.returncode, json.loads(result.stdout)

    def default_head(self) -> str | None:
        """The commit the default branch names now, or None."""
        try:
            status, body = self._read("default-head")
            oid = body["data"]["repository"]["defaultBranchRef"]["target"]["oid"]
        except Exception:
            return None
        return oid if status == 0 and isinstance(oid, str) and COMMIT_ID.fullmatch(oid) else None

    def contains(self, head: str, sha: str) -> bool | None:
        """True if sha is head or its ancestor, False if not, None without an answer.

        GET /repos/{owner}/{repo}/compare/{base}...{head} (REST "Compare two
        commits", schema commit-comparison) reports the compare head relative to
        base: status (diverged, ahead, behind, identical), ahead_by, behind_by,
        and base_commit and merge_base_commit, each a commit with its sha. A yes
        must be about the question asked: base_commit is the queried public
        head, merge_base_commit is sha, ahead_by is 0, and either "behind" by at
        least one commit with sha not the head, or "identical" with sha the head
        and behind_by 0. Any other yes-shaped reply is no answer. The commits
        and files lists are paginated and capped, so they are never read. An
        unknown commit is a 404 and a definite no.
        """
        try:
            status, body = self._read("compare", base=head, head=sha)
        except Exception:
            return None
        if not isinstance(body, dict):
            return None
        if status:
            return False if body.get("status") == "404" and body.get("message") == "Not Found" else None
        verdict = body.get("status")
        if verdict in {"ahead", "diverged"}:
            return False
        if verdict not in {"behind", "identical"}:
            return None
        base, merge_base = body.get("base_commit"), body.get("merge_base_commit")
        ahead, behind = body.get("ahead_by"), body.get("behind_by")
        bound = (
            isinstance(base, dict)
            and base.get("sha") == head
            and isinstance(merge_base, dict)
            and merge_base.get("sha") == sha
        )
        counted = type(ahead) is int and ahead == 0 and type(behind) is int and behind >= 0
        identical = verdict == "identical"
        consistent = counted and (behind == 0) == identical and (sha == head) == identical
        return True if bound and consistent else None


def already_public(repository: Repository, hits: list[str], client) -> set[str]:
    """Hit commits reachable from the canonical public default branch; anything uncertain is excluded.

    hits are newest first. Commit ids name their parents, so once the public
    head or one public hit is known, plain local ancestry decides the rest.
    """
    found: set[str] = set()
    head = client.default_head() if hits and client is not None else None
    if head is not None and repository.object(f"{head}^{{commit}}") == head:
        stdin = "".join(f"{sha}\n" for sha in hits) + f"^{head}\n"
        outside = set(repository.text("rev-list", "--stdin", stdin=stdin).split())
        found = {sha for sha in hits if sha not in outside}
    elif head is not None:
        compares = 0
        for sha in hits:
            if sha in found:
                continue
            if compares == COMPARE_LIMIT:
                break
            compares += 1
            answer = client.contains(head, sha)
            if answer is None:
                break  # No answer (outage, rate limit, timeout): stop asking; the rest stay refused.
            if answer:
                ancestors = set(repository.text("rev-list", sha).split())
                found |= {other for other in hits if other in ancestors}
    return found


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
    fields: list[tuple[bytes, bytes]] = []
    for line in header[1:].split(b"\n"):
        if line.startswith(b" "):
            if not fields:
                raise gate.PublishBlocked(f"OPSEC: {position} headers malformed; push refused.")
            key, value = fields[-1]
            fields[-1] = (key, value + b"\n" + line[1:])
        elif line:
            key, _, value = line.partition(b" ")
            fields.append((key, value))
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
    scanned only up to it and then cached clean. Reading the raw object scans
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
    Only commit messages can ever be excused; these texts never are.
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


def scan_push(real_git: str, argv: list[str], environment: dict[str, str], *, public_repository=None) -> None:
    """Raise PublishBlocked unless every public text of this push is clean, already public or overridden.

    public_repository answers which hit commits the canonical public repository
    already has; by default it is built from the catalogue when first needed.
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
    commits: list[str] = []
    owners: list[str] = []  # The commit each commit text belongs to, from texts[first] on.
    excused: set[int] = set()
    excused_commits: set[str] = set()
    if tips:
        common_dir, grafted, shallow = repository.layout()
        if grafted:
            raise gate.PublishBlocked("OPSEC: grafted history present; push refused.")
        if shallow:
            raise gate.PublishBlocked("OPSEC: shallow history cannot be scanned in full; push refused.")
        fingerprint = gate.matcher_fingerprint()
        cache = CleanCache(common_dir, fingerprint)
        cached, unusable = cache.read()
        if unusable:
            print("OPSEC: push scan cache unusable; every reachable commit scanned.", file=sys.stderr)
        public_cache = CleanCache(common_dir, fingerprint, PUBLIC_CACHE_NAME)
        known_public, unusable = public_cache.read()
        if unusable:
            print("OPSEC: push scan public cache unusable; hit commits rechecked.", file=sys.stderr)
        reachable = repository.text("rev-list", "--stdin", stdin="".join(f"{sha}\n" for sha in tips)).split()
        # Messages already public need no scan; the two caches never share an id by construction.
        skipped_public = sum(sha in known_public for sha in reachable)
        pending = [sha for sha in reachable if sha not in cached and sha not in known_public]
        for sha, parts in commit_texts(repository, pending):
            commits.append(sha)
            for field, text in parts:
                texts.append(text)
                names.append(f"commit[{sha[:12]}].{field}")
                owners.append(sha)
    first = len(texts) - len(owners)

    def excuse(indices: set[int]) -> set[int]:
        """Indices of hit commit texts whose commit the canonical public repository already has."""
        owning = {owners[index - first] for index in indices if index >= first}
        # Newest first, as rev-list listed them.
        hits = [sha for sha in commits if sha in owning]
        if not hits:
            return set()
        nonlocal public_repository
        if public_repository is None:
            public_repository = CanonicalPublicRepository.from_catalog(environment)
        found = already_public(repository, hits, public_repository)
        if found:
            try:
                public_cache.record(sorted(found), full=True)
            except OSError:
                print("OPSEC: push scan public cache not updated.", file=sys.stderr)
        excused_commits.update(found)
        excused.update(index for index in indices if index >= first and owners[index - first] in found)
        return set(excused)

    label = ",".join(dict.fromkeys(public)) if public else private[0]
    try:
        blocked = gate.check_texts(label, texts, environment=environment, field_names=names, excuse=excuse)
    finally:
        if tips:
            calls = getattr(public_repository, "calls", 0)
            print(
                f"OPSEC: push scan: {len(pending)} commit message(s) scanned, "
                f"{len(reachable) - len(pending) - skipped_public} skipped as already scanned clean here, "
                f"{skipped_public + len(excused_commits)} hit(s) excused as already public "
                f"({calls} public repository call(s)).",
                file=sys.stderr,
            )
    if commits:
        # Only commits none of whose texts had a blocking finding; excused and overridden hits are never cached.
        dirty = {owners[index - first] for index in blocked | excused if index >= first}
        clean = [sha for sha in commits if sha not in dirty]
        try:
            # Commits skipped as public never belong in the clean cache, so they do not make the scan partial.
            cache.record(clean, full=len(pending) == len(reachable) - skipped_public)
        except OSError:
            print("OPSEC: push scan cache not updated.", file=sys.stderr)


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
