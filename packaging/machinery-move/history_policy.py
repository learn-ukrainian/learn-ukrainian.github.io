#!/usr/bin/env python3
"""Enforce and verify a frozen (path, blob) history policy for the machinery extraction.

The policy lists every source (path, original blob) version the rewritten machinery history
may contain and what happens to it: retain, replace with approved sanitized bytes, or omit.
``callback`` prints a git-filter-repo 2.47.0 ``--file-info-callback`` body that applies the
policy during the rewrite and denies anything unlisted; ``verify`` independently re-reads the
rewritten history afterwards. See ``--help`` for formats and exit codes.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

EXIT_PASS = 0
EXIT_FINDING = 1
EXIT_UNUSABLE = 2

FILTER_REPO_VERSION = "2.47.0"
STATE_KEY = "lu_machinery_history_policy_v1"
NULL_OID = "0" * 40


# ---------------------------------------------------------------------------
# Shared core. These definitions are copied verbatim into the printed callback
# (see _CORE), so the rewrite and `verify` parse the policy and invert the rename
# with the same code. Keep them standard-library only, free of module-level
# names, and free of docstrings or other multi-line strings: git-filter-repo
# indents every line of a callback body by two spaces.
# ---------------------------------------------------------------------------


class PolicyError(Exception):
    pass


def parse_policy(data: bytes) -> tuple[dict, list]:
    # Returns ({(path, blob): (action, replacement_sha256 or '')}, [error, ...]).
    header = "source_path\tblob\taction\treplacement_sha256"
    hex40 = re.compile(r"[0-9a-f]{40}")
    hex64 = re.compile(r"[0-9a-f]{64}")
    entries = {}
    first_line = {}
    errors = []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return {}, [f"policy is not valid UTF-8: {exc}"]
    if "\r" in text or "\x00" in text:
        return {}, ["policy contains a carriage return or NUL byte"]
    if text and not text.endswith("\n"):
        errors.append("policy does not end with a newline")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for number, line in enumerate(lines, 1):
        if number == 1 and line == header:
            continue
        where = f"line {number}"
        fields = line.split("\t")
        if len(fields) not in (3, 4):
            errors.append(f"{where}: expected 3 or 4 tab-separated fields, found {len(fields)}")
            continue
        path, blob, action = fields[0], fields[1], fields[2]
        replacement = fields[3] if len(fields) == 4 else ""
        parts = path.split("/")
        if not path or path.startswith("/") or any(part in ("", ".", "..") for part in parts):
            errors.append(f"{where}: invalid source path {path!r}")
            continue
        if not hex40.fullmatch(blob):
            errors.append(f"{where}: blob must be 40 lowercase hex characters")
            continue
        if action not in ("retain", "omit", "replace"):
            errors.append(f"{where}: action must be retain, omit or replace, found {action!r}")
            continue
        if action == "replace" and not hex64.fullmatch(replacement):
            errors.append(f"{where}: replace needs a 64-hex replacement_sha256")
            continue
        if action != "replace" and replacement:
            errors.append(f"{where}: replacement_sha256 is only allowed for replace")
            continue
        key = (path, blob)
        if key in entries:
            errors.append(f"{where}: duplicate (path, blob) key, first listed on line {first_line[key]}")
            continue
        entries[key] = (action, replacement)
        first_line[key] = number
    if not entries and not errors:
        errors.append("policy lists no (path, blob) rows")
    return entries, errors


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def read_replacements(entries: dict, policy_dir: str) -> tuple[dict, list]:
    # Returns ({sha256: bytes}, [error, ...]) for every replace row's approved bytes.
    blobs = {}
    errors = []
    folder = os.path.join(policy_dir, "replacements")
    for (path, _blob), (action, digest) in sorted(entries.items()):
        if action != "replace" or digest in blobs:
            continue
        location = os.path.join(folder, digest)
        try:
            info = os.lstat(location)
        except OSError:
            errors.append(f"replacement {digest} for {path} is missing")
            continue
        if not stat.S_ISREG(info.st_mode):
            errors.append(f"replacement {digest} for {path} is not a regular file")
            continue
        with open(location, "rb") as handle:
            content = handle.read()
        if hashlib.sha256(content).hexdigest() != digest:
            errors.append(f"replacement {digest} for {path} does not hash to its declared sha256")
            continue
        blobs[digest] = content
    for (path, blob), (action, digest) in sorted(entries.items()):
        if action != "replace" or digest not in blobs:
            continue
        new_blob = git_blob_id(blobs[digest])
        denied = entries.get((path, new_blob), ("retain", ""))[0] != "retain"
        if new_blob == blob or denied:
            errors.append(
                f"replacement {digest} for {path} hashes to a blob that the policy omits, replaces or keeps "
                "unchanged at that path"
            )
    return blobs, errors


def load_frozen(policy_path: str, expected_sha256: str) -> tuple[dict, dict, str]:
    # Reads the policy once, checks its frozen digest, parses those exact bytes, and checks
    # every replacement file against the sha256 the policy declares for it.
    try:
        with open(policy_path, "rb") as handle:
            data = handle.read()
    except OSError as exc:
        raise PolicyError(f"cannot read policy {policy_path}: {exc}") from exc
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha256:
        raise PolicyError(f"policy sha256 {actual} does not match the frozen {expected_sha256}")
    entries, errors = parse_policy(data)
    if not errors:
        blobs, errors = read_replacements(entries, os.path.dirname(os.path.abspath(policy_path)))
    if errors:
        more = f" (+{len(errors) - 20} more)" if len(errors) > 20 else ""
        raise PolicyError("; ".join(errors[:20]) + more)
    return entries, blobs, actual


def parse_rename(spec: str) -> tuple[str, str]:
    # Accepts what git-filter-repo 2.47.0 accepts for --path-rename OLD:NEW, with both sides
    # required to be non-empty.
    sides = spec.split(":")
    if len(sides) != 2 or not sides[0] or not sides[1]:
        raise PolicyError("--path-rename must be OLD:NEW with one colon and two non-empty sides")
    old, new = sides
    if old.endswith("/") != new.endswith("/"):
        raise PolicyError("--path-rename sides must both end with '/' or neither")
    if old.startswith("/") or new.startswith("/"):
        raise PolicyError("--path-rename sides cannot begin with '/'")
    if any(part in (".", "..") for part in old.split("/") + new.split("/")):
        raise PolicyError("--path-rename sides cannot contain '.' or '..' components")
    return old, new


def path_matches(prefix: str, path: str) -> bool:
    # git-filter-repo's filename_matches(): prefix is the path or a leading directory of it.
    n = len(prefix)
    return path.startswith(prefix) and (prefix.endswith("/") or len(path) == n or path[n : n + 1] == "/")


def rename_forward(old: str, new: str, path: str) -> str:
    # git-filter-repo's single --path-rename step: replace the first occurrence of old.
    return path.replace(old, new, 1) if path_matches(old, path) else path


def build_inverse(entries: dict, old: str, new: str) -> dict:
    # Maps each output path back to the one policy source path that renames to it.
    inverse = {}
    for path in sorted({path for path, _blob in entries}):
        if path_matches(new, path):
            raise PolicyError(
                f"policy source path {path!r} is inside the rename target {new!r}; key the policy on source paths"
            )
        output = rename_forward(old, new, path)
        if output in inverse:
            raise PolicyError(f"policy source paths {inverse[output]!r} and {path!r} both rename to {output!r}")
        inverse[output] = path
    return inverse


_CORE = (
    PolicyError,
    parse_policy,
    git_blob_id,
    read_replacements,
    load_frozen,
    parse_rename,
    path_matches,
    rename_forward,
    build_inverse,
)


# ---------------------------------------------------------------------------
# callback
# ---------------------------------------------------------------------------

_CALLBACK_START = """
    try:
        _entries, _blobs, _digest = load_frozen(POLICY_PATH, POLICY_SHA256)
        _old, _new = parse_rename(PATH_RENAME)
        _inverse = build_inverse(_entries, _old, _new)
    except PolicyError as _exc:
        raise SystemExit("history-policy callback: refusing to start: %s" % _exc)
    _state = {"entries": _entries, "blobs": _blobs, "inverse": _inverse, "inserted": {}}
    value.data[STATE_KEY] = _state
"""

_CALLBACK_DISPATCH = """
_name = filename.decode("utf-8", "surrogateescape")
_blob = blob_id.decode("ascii", "replace") if isinstance(blob_id, bytes) else repr(blob_id)
if len(_blob) != 40 or _blob.strip("0123456789abcdef"):
    raise SystemExit("history-policy callback: %r has no original blob id (%s); refusing" % (_name, _blob))
_source = _state["inverse"].get(_name)
if _source is None:
    raise SystemExit("history-policy callback: output path %r does not invert to a policy source path" % _name)
_entry = _state["entries"].get((_source, _blob))
if _entry is None:
    raise SystemExit("history-policy callback: (%r, %s) is not in the policy; default deny" % (_source, _blob))
if _entry[0] == "retain":
    return (filename, mode, blob_id)
if _entry[0] == "omit":
    # mode None makes git-filter-repo emit a deletion of this path in this commit, so the
    # commit never inherits an earlier retained version from its parent.
    return (filename, None, blob_id)
_mark = _state["inserted"].get(_entry[1])
if _mark is None:
    _mark = value.insert_file_with_contents(_state["blobs"][_entry[1]])
    _state["inserted"][_entry[1]] = _mark
return (filename, mode, _mark)
"""


def render_callback(policy_path: str, policy_sha256: str, path_rename: str) -> str:
    lines = [
        f"# git-filter-repo {FILTER_REPO_VERSION} --file-info-callback body, printed by",
        "# packaging/machinery-move/history_policy.py callback. Default deny: any (path, blob)",
        "# the frozen policy does not list aborts the rewrite.",
        f"STATE_KEY = {STATE_KEY!r}",
        f"POLICY_PATH = {policy_path!r}",
        f"POLICY_SHA256 = {policy_sha256!r}",
        f"PATH_RENAME = {path_rename!r}",
        "_state = value.data.get(STATE_KEY)",
        "if _state is None:",
        "    # First call: load and check the frozen inputs once, before any content is written.",
        "    import hashlib, os, re, stat",
    ]
    for item in _CORE:
        lines.extend(("    " + line).rstrip() for line in inspect.getsource(item).rstrip("\n").splitlines())
    lines.extend(_CALLBACK_START.strip("\n").splitlines())
    lines.extend(_CALLBACK_DISPATCH.strip("\n").splitlines())
    body = "\n".join(lines) + "\n"
    if any(marker in body for marker in ('"""', "'''")):
        raise AssertionError("callback body must not contain multi-line strings")
    return body


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


class InputError(Exception):
    pass


def _git(repo: str, *args: str, stdin: bytes | None = None) -> bytes:
    result = subprocess.run(["git", "-C", repo, *args], input=stdin, capture_output=True, check=False, timeout=3600)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise InputError("git {} failed: {}".format(" ".join(args[:2]), message))
    return result.stdout


def _read_commit_map(path: str) -> list[tuple[str, str]]:
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError(f"cannot read commit map {path}: {exc}") from exc
    if not lines or lines[0].split() != ["old", "new"]:
        raise InputError(f"commit map {path} does not start with git-filter-repo's 'old new' header")
    pairs = []
    for number, line in enumerate(lines[1:], 2):
        fields = line.split(" ")
        if len(fields) != 2 or not all(re.fullmatch(r"[0-9a-f]{40}", field) for field in fields):
            raise InputError(f"commit map line {number} is not '<old-oid> <new-oid>'")
        pairs.append((fields[0], fields[1]))
    if not pairs:
        raise InputError(f"commit map {path} lists no commits")
    return pairs


def _missing_commits(repo: str, oids: list[str]) -> list[str]:
    if not oids:
        return []
    output = _git(repo, "cat-file", "--batch-check=%(objecttype)", stdin="".join(o + "\n" for o in oids).encode())
    kinds = output.decode().splitlines()
    return [oid for oid, kind in zip(oids, kinds, strict=True) if kind != "commit"]


def _history_pairs(repo: str, rev: str) -> tuple[set[tuple[str, str]], int]:
    # Every distinct (path, object id) a tree entry holds in any commit reachable from rev.
    tip = _git(repo, "rev-parse", "--verify", "--end-of-options", rev + "^{commit}").decode().strip()
    listing = _git(repo, "rev-list", "--format=%T", tip).decode().split()
    # rev-list --format prints "commit <oid>" then the formatted tree id for each commit.
    trees = {listing[i + 2] for i in range(0, len(listing), 3)}
    commits = len(listing) // 3
    pairs: set[tuple[str, str]] = set()
    for tree in sorted(trees):
        for record in _git(repo, "ls-tree", "-r", "-z", "--full-tree", tree).split(b"\0"):
            if not record:
                continue
            meta, raw_path = record.split(b"\t", 1)
            _mode, kind, oid = meta.decode().split(" ")
            if kind in ("blob", "commit"):
                pairs.add((raw_path.decode("utf-8", "surrogateescape"), oid))
    return pairs, commits


def verify(args: argparse.Namespace) -> int:
    try:
        entries, blobs, digest = load_frozen(args.policy, args.policy_sha256)
        old, new = parse_rename(args.path_rename)
        inverse = build_inverse(entries, old, new)
    except PolicyError as exc:
        print(f"verify: unusable policy: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    try:
        if not Path(args.repo).is_dir():
            raise InputError(f"repository {args.repo} does not exist")
        object_format = _git(args.repo, "rev-parse", "--show-object-format").decode().strip()
        if object_format != "sha1":
            raise InputError(f"repository object format is {object_format}; the policy holds sha1 blob ids")
        commit_map = _read_commit_map(args.commit_map)
        rewritten = sorted({new_oid for _old, new_oid in commit_map if new_oid != NULL_OID})
        missing = _missing_commits(args.repo, rewritten)
        pairs, commits = _history_pairs(args.repo, args.rev)
    except (InputError, subprocess.TimeoutExpired) as exc:
        print(f"verify: unusable input: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE

    replacement_ids = {}
    for (path, _blob), (action, sha) in entries.items():
        if action == "replace":
            replacement_ids.setdefault(path, set()).add(git_blob_id(blobs[sha]))
    findings = [f"commit-map-names-missing-commit new={oid}" for oid in missing]
    retained = replaced = 0
    for output, oid in sorted(pairs):
        source = inverse.get(output)
        if source is None:
            findings.append(f"path-does-not-invert path={output!r} blob={oid}")
            continue
        action = entries.get((source, oid), ("", ""))[0]
        if action == "retain":
            retained += 1
        elif oid in replacement_ids.get(source, ()):
            replaced += 1
        elif action == "omit":
            findings.append(f"omitted-version-survives path={output!r} blob={oid}")
        elif action == "replace":
            findings.append(f"replaced-original-survives path={output!r} blob={oid}")
        else:
            findings.append(f"unlisted-pair path={output!r} source={source!r} blob={oid}")
    omitted = sum(1 for action, _sha in entries.values() if action == "omit")
    if not pairs:
        findings.append(f"zero-pairs-checked rev={args.rev}")
    for finding in findings:
        print(f"FINDING {finding}")
    verdict = "FAIL" if findings else "PASS"
    print(
        f"verify: {verdict} policy_sha256={digest} commits={commits} checked={len(pairs)} retained={retained} "
        f"replaced={replaced} omitted={omitted} findings={len(findings)}"
    )
    return EXIT_FINDING if findings else EXIT_PASS


# ---------------------------------------------------------------------------
# check-policy and callback commands
# ---------------------------------------------------------------------------


def check_policy(args: argparse.Namespace) -> int:
    try:
        data = Path(args.policy).read_bytes()
        include = None
        if args.include:
            include_text = Path(args.include).read_text(encoding="utf-8")
            include = set(include_text.splitlines())
    except (OSError, UnicodeDecodeError) as exc:
        print(f"check-policy: unusable input: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    digest = hashlib.sha256(data).hexdigest()
    entries, errors = parse_policy(data)
    _blobs, replacement_errors = read_replacements(entries, os.path.dirname(os.path.abspath(args.policy)))
    errors += replacement_errors
    if include is not None:
        errors += [f"path {p} is not in the include list" for p in sorted({p for p, _b in entries} - include)]
    for error in errors:
        print(f"FINDING {error}")
    actions = [action for action, _sha in entries.values()]
    dispositions: dict[str, set[str]] = {}
    for (_path, blob), (action, _sha) in entries.items():
        dispositions.setdefault(blob, set()).add(action)
    mixed = sum(1 for seen in dispositions.values() if len(seen) > 1)
    print(
        f"check-policy: {'FAIL' if errors else 'PASS'} policy_sha256={digest} rows={len(entries)} "
        f"retain={actions.count('retain')} omit={actions.count('omit')} replace={actions.count('replace')} "
        f"mixed_disposition_blobs={mixed}"
    )
    return EXIT_FINDING if errors else EXIT_PASS


def callback(args: argparse.Namespace) -> int:
    policy_path = os.path.abspath(args.policy)
    try:
        entries, _blobs, _digest = load_frozen(policy_path, args.policy_sha256)
        old, new = parse_rename(args.path_rename)
        build_inverse(entries, old, new)
    except PolicyError as exc:
        print(f"callback: unusable policy: {exc}", file=sys.stderr)
        return EXIT_UNUSABLE
    sys.stdout.write(render_callback(policy_path, args.policy_sha256, args.path_rename))
    return EXIT_PASS


def _sha256_arg(value: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise argparse.ArgumentTypeError("expected 64 lowercase hex characters")
    return value


EPILOG = """\
Policy format (TSV, UTF-8, LF line endings, one row per source (path, blob)):
  source_path<TAB>blob<TAB>action<TAB>replacement_sha256
  - source_path: the path in the SOURCE history, before --path-rename.
  - blob: the 40-hex (lowercase) original blob id of that version.
  - action: retain | omit | replace.
      retain   keep the version unchanged.
      omit     the version never appears; the rewritten commit that held it does not
               contain the path at all (it is deleted in that commit, so the commit does
               not inherit an earlier retained version from its parent).
      replace  the version is swapped for approved sanitized bytes.
  - replacement_sha256: only for replace (omit the column or leave it empty otherwise);
    the sha256 of the approved bytes, stored as <policy-dir>/replacements/<sha256>.
  An optional first line equal to the four column names is a header. No comments or blank
  lines. Each (source_path, blob) key appears once. The sha256 of the policy file is its
  freeze identity; the replacement digests it declares freeze the replacement files.
  Dispositions apply per (path, blob): identical bytes under another path follow that
  path's own row (check-policy counts such blobs as mixed_disposition_blobs).

Include list (check-policy --include): one literal source path per line, as given to
git filter-repo --paths-from-file.

Path rename: --path-rename takes the same OLD:NEW given to git filter-repo (one rename,
both sides non-empty). git-filter-repo 2.47.0 renames paths before calling
--file-info-callback, so the callback and verify map each output path back through the
rename to the one policy source path that renames to it. A policy source path inside
NEW, or two source paths renaming to one output path, is refused.

Subcommands:
  check-policy  Validate format, duplicate keys, replacement files and (with --include)
                include-list membership. Prints the policy sha256 and row counts.
  callback      Print the --file-info-callback body. At rewrite time it refuses to start
                unless the policy and every replacement file match their frozen digests;
                retains retain pairs, deletes omit pairs from the commit, substitutes the
                approved bytes for replace pairs, and aborts the rewrite (nonzero exit,
                refs unchanged) on any unlisted (path, blob) or any output path that does
                not invert to a policy source path. Deletions carry no content and pass
                through unchanged. Discard the clone after an aborted rewrite.
  verify        Refuse (exit 2) unless the policy and every replacement file match their
                frozen digests; then walk every commit reachable from --rev in the
                rewritten repository, without reading any callback output, and fail if a
                (path, blob) present is neither a retain version nor the exact replacement
                blob of its path, if an omitted version survives, if an output path does
                not invert to a policy source path, or if the commit map names a rewritten
                commit that does not exist (all-zero pruned entries are skipped).
                Zero checked pairs fails.

Examples:
  .venv/bin/python packaging/machinery-move/history_policy.py check-policy \\
      --policy "$WORK/history/policy.tsv" --include "$INCLUDE"
  .venv/bin/python packaging/machinery-move/history_policy.py callback \\
      --policy "$WORK/history/policy.tsv" --policy-sha256 "$POLICY_SHA256" \\
      --path-rename scripts/:lu_machinery/ > "$WORK/file-policy.callback"
  git-filter-repo --paths-from-file "$INCLUDE" --path-rename scripts/:lu_machinery/ \\
      --file-info-callback "$(cat "$WORK/file-policy.callback")"
  .venv/bin/python packaging/machinery-move/history_policy.py verify \\
      --repo "$EXTRACT" --rev "$FILTER_TIP" --policy "$WORK/history/policy.tsv" \\
      --policy-sha256 "$POLICY_SHA256" --commit-map "$EXTRACT/.git/filter-repo/commit-map" \\
      --path-rename scripts/:lu_machinery/

Outputs:
  check-policy and verify print FINDING lines, then one summary line with the policy
  sha256 and counts (verify: commits, checked, retained, replaced, omitted). callback
  prints the callback body to stdout. Nothing is written to disk; verify only reads.

Exit codes:
  0  pass
  1  a finding (invalid policy row, unlisted or surviving version, missing commit, ...)
  2  unusable or missing input (unreadable file, digest mismatch for callback/verify,
     invalid policy for callback/verify, bad --path-rename, bad repository or commit map)

Related:
  Machinery move step 6, plan-v1 section 4 step 3 (STEP6-PLAN C-4674);
  git-filter-repo 2.47.0 --file-info-callback; packaging/machinery-move/README.md.
"""


_SUB_EPILOG = """\
Example:
  .venv/bin/python packaging/machinery-move/history_policy.py {example}

Exit codes: 0 pass; 1 a finding; 2 unusable or missing input{extra}.
Policy format, path-rename semantics and all examples: history_policy.py --help
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="history_policy.py",
        description=(
            "Enforce a frozen (path, blob) retain/omit/replace policy while git-filter-repo 2.47.0 rewrites\n"
            "the machinery history, and verify the rewritten history against it. Use for the machinery\n"
            "extraction rewrite only; it does not derive paths, produce dispositions or run the rewrite."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="{check-policy,callback,verify}")

    check = commands.add_parser(
        "check-policy",
        help="validate a policy and print its sha256",
        description="Validate the policy format, duplicate keys, replacement files and include-list membership.",
        epilog=_SUB_EPILOG.format(
            example='check-policy --policy "$WORK/history/policy.tsv" --include "$INCLUDE"', extra=""
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    check.add_argument("--policy", required=True, help="policy TSV file, e.g. $WORK/history/policy.tsv")
    check.add_argument(
        "--include",
        help="optional include list (one source path per line); every policy path must be in it. Default: unchecked",
    )
    check.set_defaults(func=check_policy)

    frozen = argparse.ArgumentParser(add_help=False)
    frozen.add_argument("--policy", required=True, help="frozen policy TSV file; its directory holds replacements/")
    frozen.add_argument(
        "--policy-sha256", required=True, type=_sha256_arg, help="frozen sha256 of the policy file (64 lowercase hex)"
    )
    frozen.add_argument(
        "--path-rename",
        required=True,
        metavar="OLD:NEW",
        help="the --path-rename given to git filter-repo, e.g. scripts/:lu_machinery/",
    )

    cb = commands.add_parser(
        "callback",
        parents=[frozen],
        help="print the git-filter-repo --file-info-callback body",
        description="Print a default-deny git-filter-repo 2.47.0 --file-info-callback body for the frozen policy.",
        epilog=_SUB_EPILOG.format(
            example='callback --policy "$POLICY" --policy-sha256 "$POLICY_SHA256" \\\n'
            '      --path-rename scripts/:lu_machinery/ > "$WORK/file-policy.callback"',
            extra=" (including a policy or replacement that does not match its frozen digest)",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    cb.set_defaults(func=callback)

    ver = commands.add_parser(
        "verify",
        parents=[frozen],
        help="verify a rewritten history against the frozen policy",
        description="Walk every commit reachable from --rev and check each (path, blob) against the frozen policy.",
        epilog=_SUB_EPILOG.format(
            example='verify --repo "$EXTRACT" --rev "$FILTER_TIP" --policy "$POLICY" \\\n'
            '      --policy-sha256 "$POLICY_SHA256" --commit-map "$EXTRACT/.git/filter-repo/commit-map" \\\n'
            "      --path-rename scripts/:lu_machinery/",
            extra=" (including a policy or replacement that does not match its frozen digest)",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ver.add_argument("--repo", required=True, help="the rewritten extraction repository")
    ver.add_argument(
        "--rev",
        default="HEAD",
        help="tip whose ancestry is checked (default: HEAD); pass the git-filter-repo output tip",
    )
    ver.add_argument(
        "--commit-map",
        required=True,
        help="git-filter-repo commit map, e.g. $EXTRACT/.git/filter-repo/commit-map",
    )
    ver.set_defaults(func=verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    func: Callable[[argparse.Namespace], int] = args.func
    return func(args)


if __name__ == "__main__":
    sys.exit(main())
