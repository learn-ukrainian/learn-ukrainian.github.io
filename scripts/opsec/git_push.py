"""Scan the text a git push would publish before it reaches a public remote.

The agent git shim executes this file for push commands. A dry run asks git
which refs the push creates or updates and where it sends them. For every
public destination the published ref names, the messages of commits not
already reachable from the remote's old tip or tracking refs, and annotated
tag messages are scanned through check_texts. File contents are not scanned.
Private remotes are exempt exactly as is_private decides. The real push runs
only after a clean scan, without the command-scoped override.
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


def destination(url: str) -> str:
    """Canonical host/owner/name for a push URL, or unknown (never private by default)."""
    value = url.strip()
    scp = re.fullmatch(r"[^@/:]+@([^/:]+):(.+)", value)
    remote = re.fullmatch(r"(?:https?|ssh|git)://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+)", value)
    if not (scp or remote):
        return "unknown"  # Local paths and file URLs have no hosted identity.
    host, path = scp.groups() if scp else remote.groups()
    return gate.normalize_repository(f"{host}/{path}")


class Repository:
    """Read-only object queries through the real git with the caller's global options."""

    def __init__(self, real_git: str, global_options: list[str], environment: dict[str, str]):
        self.base = [real_git, *global_options]
        self.environment = environment

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
            raise gate.PublishBlocked("OPSEC: push contents unreadable; push refused.")
        return result.stdout.decode("utf-8", "replace")

    def object(self, revision: str) -> str | None:
        result = self.run("rev-parse", "--verify", "--quiet", revision)
        if result.returncode:
            return None
        return result.stdout.decode().strip() or None

    def tracking_tips(self, url: str, dest: str) -> list[str]:
        """Tips of tracking refs of remotes whose every URL is this destination."""
        result = self.run("config", "--get-regexp", r"^remote\..*\.(url|pushurl)$")
        urls: dict[str, list[str]] = {}
        for line in result.stdout.decode("utf-8", "replace").splitlines():
            key, _, value = line.partition(" ")
            name = re.sub(r"\.(?:url|pushurl)$", "", key.removeprefix("remote."))
            urls.setdefault(name, []).append(value)
        tips: list[str] = []
        for name, values in urls.items():
            if all(v == url or (dest != "unknown" and destination(v) == dest) for v in values):
                listing = self.text("for-each-ref", "--format=%(objectname)", f"refs/remotes/{name}/")
                tips.extend(listing.split())
        return tips


def _short_ref(target: str) -> tuple[str, str]:
    for prefix, kind in (("refs/heads/", "branch"), ("refs/tags/", "tag")):
        if target.startswith(prefix):
            return kind, target[len(prefix) :]
    return "ref", target


def published_texts(repository: Repository, url: str, dest: str, updates: list[tuple]) -> tuple[list[str], list[str]]:
    """Ref names, new commit messages and annotated tag messages one destination receives."""
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
        negatives += repository.tracking_tips(url, dest)
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
        sys.stderr.write(preview.stderr.decode("utf-8", "replace"))
        raise gate.PublishBlocked("OPSEC: push preview unavailable; push refused.")
    public: list[str] = []
    private: list[str] = []
    texts: list[str] = []
    names: list[str] = []
    for section in sections:
        dest = destination(section["url"])
        if gate.is_private(dest):
            private.append(dest)
            continue
        public.append(dest)
        found, labels = published_texts(repository, section["url"], dest, section["updates"])
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
