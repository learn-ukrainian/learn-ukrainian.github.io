"""Scan the text a git push would publish before it reaches a public remote.

The agent git shim executes this file for push commands. A dry run asks git
which refs the push names and where it sends them. For every public
destination the ref names, annotated tag messages and the messages of every
commit reachable from the pushed tips are scanned through check_texts, except
commits that this machine's earlier push scans found clean (CleanCache, kept
in the repository's common git directory). Nothing the destination reports is
evidence of what it already has. Enumeration ignores replacement objects and
grafts, a grafted or shallow repository is refused, and the scan's own git
calls run without tracing or prompts. File contents are not scanned. Private
remotes are exempt exactly as is_private decides. The real push runs only
after a clean scan, without the command-scoped override. Git text from these
steps is never replayed.
"""

from __future__ import annotations

import contextlib
import fcntl
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
CACHE_VERSION = "lu-push-scan-clean 1"
COMMIT_ID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


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

    No override, tracing or credential prompts; replacement objects and grafts
    disabled. A trace2 target of "0" in the environment outranks one set in
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

    def text(self, *args: str, stdin: str | None = None, environment: dict[str, str] | None = None) -> str:
        result = self.run(*args, stdin=stdin, environment=environment)
        if result.returncode:
            # Fixed text only: git output can quote ref names and messages.
            raise gate.PublishBlocked(
                f"OPSEC: push scan step git {args[0]} failed (exit {result.returncode}); push refused."
            )
        return result.stdout.decode("utf-8", "replace")

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
    """

    def __init__(self, directory: Path, fingerprint: str):
        self.path = directory / CACHE_NAME
        self.lock_path = directory / f"{CACHE_NAME}.lock"
        self.header = f"{CACHE_VERSION} {fingerprint}"

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
            temporary = self.path.with_name(f"{CACHE_NAME}.{os.getpid()}.tmp")
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


def _short_ref(target: str) -> tuple[str, str]:
    for prefix, kind in (("refs/heads/", "branch"), ("refs/tags/", "tag")):
        if target.startswith(prefix):
            return kind, target[len(prefix) :]
    return "ref", target


def published_refs(repository: Repository, updates: list[tuple]) -> tuple[list[str], list[str], list[str]]:
    """Ref names and annotated tag messages one destination receives, and the commits its refs name."""
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
            raw = repository.text("cat-file", "tag", current)
            header, _, message = raw.partition("\n\n")
            if current not in seen_tags:
                seen_tags.add(current)
                texts.append(message)
                names.append(f"tag[{current[:12]}].message")
            current = re.search(r"^object ([0-9a-f]+)$", header, re.M)[1]
        if repository.text("cat-file", "-t", current).strip() == "commit":
            tips.append(current)
    return texts, names, tips


def scan_push(real_git: str, argv: list[str], environment: dict[str, str]) -> None:
    """Raise PublishBlocked unless every public text of this push is clean or overridden."""
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
    if tips:
        common_dir, grafted, shallow = repository.layout()
        if grafted:
            raise gate.PublishBlocked("OPSEC: grafted history present; push refused.")
        if shallow:
            raise gate.PublishBlocked("OPSEC: shallow history cannot be scanned in full; push refused.")
        cache = CleanCache(common_dir, gate.matcher_fingerprint())
        cached, unusable = cache.read()
        if unusable:
            print("OPSEC: push scan cache unusable; every reachable commit scanned.", file=sys.stderr)
        reachable = repository.text("rev-list", "--stdin", stdin="".join(f"{sha}\n" for sha in tips)).split()
        pending = [sha for sha in reachable if sha not in cached]
        print(
            f"OPSEC: push scan: {len(pending)} commit message(s) scanned, "
            f"{len(reachable) - len(pending)} skipped as already scanned clean here.",
            file=sys.stderr,
        )
        if pending:
            output = repository.text(
                "rev-list",
                "--no-walk=unsorted",
                "--no-commit-header",
                "--format=%x00%H%x00%B",
                "--stdin",
                stdin="".join(f"{sha}\n" for sha in pending),
            )
            fields = output.split("\x00")[1:]
            for sha, message in zip(fields[0::2], fields[1::2], strict=True):
                commits.append(sha)
                texts.append(message)
                names.append(f"commit[{sha[:12]}].message")
    label = ",".join(dict.fromkeys(public)) if public else private[0]
    blocked = gate.check_texts(label, texts, environment=environment, field_names=names)
    if commits:
        # Only commits whose own message had no blocking finding; an overridden hit is never cached.
        first = len(texts) - len(commits)
        clean = [sha for index, sha in enumerate(commits, start=first) if index not in blocked]
        try:
            cache.record(clean, full=len(pending) == len(reachable))
        except OSError:
            print("OPSEC: push scan cache not updated.", file=sys.stderr)


def main(argv: list[str] | None = None, *, execute=os.execve) -> int:
    real_git, *args = sys.argv[1:] if argv is None else argv
    environment = dict(os.environ)
    try:
        scan_push(real_git, args, environment)
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
