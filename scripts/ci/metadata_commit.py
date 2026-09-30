"""A commit that carries only another commit's metadata, for a metadata-only secret scan.

When the merge queue reuses a pull_request run's file-content secret scan
(scripts/ci/reuse_green_run.py), the queue commit's own metadata (message,
author, committer) is still new: the queue writes PR-derived text into the
message. TruffleHog's git source scans each commit's metadata and its diff.
This writes a commit with the same author, committer and message as
``--commit``, its first parent as the only parent and that parent's tree, so
the diff is empty and scanning ``parent..<new commit>`` scans the metadata
alone. The new commit is written to ``--branch`` (TruffleHog clones the local
repository, which copies branches but not loose commits).

Prints ``parent=<sha>`` and ``commit=<sha>`` lines (``$GITHUB_OUTPUT`` format).
"""

from __future__ import annotations

import argparse
import subprocess
import sys

_HEADERS_KEPT = ("author ", "committer ", "encoding ")


def git(*args: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["git", *args], input=stdin, capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()


def metadata_only_object(raw: str, parent: str, parent_tree: str) -> str:
    """``raw`` (``git cat-file commit`` output) with its tree and parents replaced.

    Keeps the author, committer, encoding and message byte for byte; drops the
    rest of the header (other parents, signatures), which TruffleHog does not scan.
    """
    header, separator, message = raw.partition("\n\n")
    if not separator:
        raise ValueError("commit object has no message separator")
    kept = [line for line in header.split("\n") if line.startswith(_HEADERS_KEPT)]
    if sum(line.startswith(("author ", "committer ")) for line in kept) != 2:
        raise ValueError("commit object needs exactly one author and one committer")
    return "\n".join([f"tree {parent_tree}", f"parent {parent}", *kept]) + "\n\n" + message


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--branch", default="ci-queue-metadata")
    args = parser.parse_args(argv)

    commit = git("rev-parse", "--verify", f"{args.commit}^{{commit}}")
    parent = git("rev-parse", "--verify", f"{commit}^1")
    # rstrip("\n") in git() would drop the message's final newline; read it raw.
    raw = subprocess.run(
        ["git", "cat-file", "commit", commit], capture_output=True, text=True, check=True, timeout=30
    ).stdout
    obj = metadata_only_object(raw, parent, git("rev-parse", f"{parent}^{{tree}}"))
    new = git("hash-object", "-t", "commit", "-w", "--stdin", stdin=obj)
    git("branch", "--force", args.branch, new)
    print(f"parent={parent}\ncommit={new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
