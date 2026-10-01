"""Scan the text a git push would publish before it reaches a public remote.

The agent git shim executes this file for push commands. A dry run asks git
which refs the push creates or updates and where it sends them. For every
public destination the published ref names, the messages of commits the
destination does not advertise as already reachable, and annotated tag
messages are scanned through check_texts. Local tracking refs are never
evidence. File contents are not scanned. Private remotes are exempt exactly as
is_private decides. The real push runs only after a clean scan, without the
command-scoped override. Git text from these steps is never replayed.
"""

from __future__ import annotations

import os
import re
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
PUBLISHING_FLAGS = {" ", "+", "*"}  # fast-forward, forced update, new ref
KNOWN_FLAGS = PUBLISHING_FLAGS | {"-", "!", "="}  # deleted, rejected, up to date
SUMMARY_RANGE = re.compile(r"([0-9a-f]{4,64})\.\.\.?([0-9a-f]{4,64})")


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
            flag, refs, *summary = line.split("\t", 2)
            source, separator, target = refs.rpartition(":")
            if not separator or not target:
                raise gate.PublishBlocked("OPSEC: push preview unparseable; push refused.")
            sections[-1]["updates"].append((flag, source, target, summary[0] if summary else ""))
        else:
            raise gate.PublishBlocked("OPSEC: push preview unparseable; push refused.")
    return sections


def _is_local(url: str) -> bool:
    """git's url_is_local_not_ssh: no colon, or a slash before the first colon."""
    colon, slash = url.find(":"), url.find("/")
    return colon < 0 or 0 <= slash < colon


def anonymize_url(url: str) -> str:
    """git's transport_anonymize_url: the form a push preview prints (userinfo removed)."""
    at = url.find("@")
    if at < 0 or _is_local(url):
        return url
    rest = url[at + 1 :]
    scheme = url.find("://")
    if scheme < 0:
        return rest if ":" in rest else url
    slash = url.find("/", scheme + 3)
    if not re.fullmatch(r"[A-Za-z0-9+.-]*", url[:scheme]) or 0 <= slash < at:
        return url
    return url[: scheme + 3] + rest


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


class Repository:
    """Read-only object queries through the real git with the caller's global options."""

    def __init__(self, real_git: str, global_options: list[str], environment: dict[str, str]):
        # Replacement objects change what readers see but not what a pack sends,
        # so every query reads the original objects (the flag outranks config).
        self.base = [real_git, "--no-replace-objects", *global_options]
        self.environment = {**environment, "GIT_NO_REPLACE_OBJECTS": "1"}

    def run(self, *args: str, stdin: str | None = None, timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [*self.base, *args],
            input=stdin.encode() if stdin is not None else None,
            stdin=subprocess.DEVNULL if stdin is None else None,
            capture_output=True,
            env=self.environment,
            check=False,
            timeout=timeout,
        )

    def text(self, *args: str, stdin: str | None = None) -> str:
        result = self.run(*args, stdin=stdin)
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

    def push_urls(self, rest: list[str]) -> list[str]:
        """Resolved push URLs of every remote, plus the push's own arguments."""
        urls = [arg.removeprefix("--repo=") for arg in rest if not arg.startswith("-") or arg.startswith("--repo=")]
        for name in self.text("remote").splitlines():
            result = self.run("remote", "get-url", "--push", "--all", name)
            if not result.returncode:
                urls += result.stdout.decode("utf-8", "replace").splitlines()
        return urls

    def advertised(self, url: str) -> list[str] | None:
        """Commits and tags the destination advertises that exist here; None if it cannot be queried."""
        try:
            result = self.run("ls-remote", "--", url, timeout=120)
        except subprocess.TimeoutExpired:
            return None
        if result.returncode:
            return None
        listed = {line.split("\t", 1)[0] for line in result.stdout.decode("ascii", "replace").splitlines()}
        if not listed:
            return []
        types = self.text("cat-file", "--batch-check=%(objectname) %(objecttype)", stdin="\n".join(listed) + "\n")
        return [
            sha for sha, _, kind in (line.partition(" ") for line in types.splitlines()) if kind in {"commit", "tag"}
        ]


def _short_ref(target: str) -> tuple[str, str]:
    for prefix, kind in (("refs/heads/", "branch"), ("refs/tags/", "tag")):
        if target.startswith(prefix):
            return kind, target[len(prefix) :]
    return "ref", target


def published_texts(repository: Repository, url: str, updates: list[tuple]) -> tuple[list[str], list[str]]:
    """Ref names, new commit messages and annotated tag messages one destination receives.

    Commits are excluded only on the destination's own evidence: the old tip the
    preview reports and the refs it advertises to ls-remote at the push URL.
    Without that evidence the whole reachable history is scanned.
    """
    texts: list[str] = []
    names: list[str] = []
    positives: list[str] = []
    negatives: list[str] = []
    seen_tags: set[str] = set()
    for number, (flag, source, target, summary) in enumerate(updates, start=1):
        if flag not in PUBLISHING_FLAGS:
            continue
        kind, short = _short_ref(target)
        texts.append(short)
        names.append(f"{kind}[{number}].name")
        new = repository.object(source)
        if new is None:
            raise gate.PublishBlocked("OPSEC: pushed object unresolved; push refused.")
        old = SUMMARY_RANGE.fullmatch(summary.split(" ", 1)[0]) if flag in {" ", "+"} else None
        if old and (resolved := repository.object(old[1] + "^{commit}")):
            negatives.append(resolved)
        current = new
        while repository.text("cat-file", "-t", current).strip() == "tag":
            raw = repository.text("cat-file", "tag", current)
            header, _, message = raw.partition("\n\n")
            if current not in seen_tags:
                seen_tags.add(current)
                texts.append(message)
                names.append(f"tag[{current[:12]}].message")
            current = re.search(r"^object ([0-9a-f]+)$", header, re.M)[1]
        if repository.text("cat-file", "-t", current).strip() == "commit":
            positives.append(current)
    if positives:
        advertised = repository.advertised(url)
        if not advertised:
            reason = "unavailable" if advertised is None else "shares no local history"
            print(f"OPSEC: destination refs {reason}; full reachable history scanned.", file=sys.stderr)
        negatives += advertised or []
        revisions = "\n".join([*positives, *("^" + sha for sha in negatives)]) + "\n"
        output = repository.text("rev-list", "--no-commit-header", "--format=%x00%H%x00%B", "--stdin", stdin=revisions)
        fields = output.split("\x00")[1:]
        for sha, message in zip(fields[0::2], fields[1::2], strict=True):
            texts.append(message)
            names.append(f"commit[{sha[:12]}].message")
    return texts, names


def scan_push(real_git: str, argv: list[str], environment: dict[str, str]) -> None:
    """Raise PublishBlocked unless every public text of this push is clean or overridden."""
    global_options, command, rest = split_command(argv)
    if command != "push":
        return
    internal = {k: v for k, v in environment.items() if k != "LU_OPSEC_OVERRIDE"}
    repository = Repository(real_git, global_options, internal)
    preview = repository.run("push", *preview_arguments(rest), timeout=300)
    sections = parse_porcelain(preview.stdout.decode("utf-8", "replace"))
    if not sections:
        # git's own error text can quote the refspec; name only the phase.
        raise gate.PublishBlocked(f"OPSEC: push preview failed (exit {preview.returncode}); push refused.")
    candidates = repository.push_urls(rest)
    public: list[str] = []
    private: list[str] = []
    texts: list[str] = []
    names: list[str] = []
    for section in sections:
        # The preview prints the push URL without userinfo; recover the full URL.
        url = next((c for c in candidates if anonymize_url(c) == section["url"]), section["url"])
        dest = destination(url)
        if gate.is_private(dest):
            private.append(dest)
            continue
        public.append(dest)
        found, labels = published_texts(repository, url, section["updates"])
        texts += found
        names += labels
    label = ",".join(dict.fromkeys(public)) if public else private[0]
    gate.check_texts(label, texts, environment=environment, field_names=names)


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
