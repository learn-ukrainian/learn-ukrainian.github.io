#!/usr/bin/env python3
"""Lint repository files and git diffs for Operational Security (OPSEC) leaks.

Scans tracked files, staged files, or specified git ranges for sensitive
infrastructure metadata that MUST NOT appear in the public repository
(learn-ukrainian/learn-ukrainian.github.io), public PRs, or public docs.

Forbidden items:
1. Raw IPv4 addresses (excluding loopback 127.0.0.1, 0.0.0.0, RFC 5737 doc IPs, public DNS, section headers)
2. Private Key headers (PKCS#1, PKCS#8, OPENSSH, RSA, EC, DSA, ENCRYPTED)
3. Raw SSH password-less auth method disclosure

Safe exclusions:
- Loopback / Localhost (127.0.0.1, 0.0.0.0)
- Standard Public DNS Resolvers (1.1.1.1, 1.0.0.1, 8.8.8.8, 8.8.4.4, 9.9.9.9, 4.2.2.2)
- Standard RFC 5737 Documentation IPs (e.g. 203.0.113.7, 198.51.100.4)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Regex to match IPv4 addresses: X.X.X.X where each X is 1-3 digits
_IPV4_RE = re.compile(r"\b(?P<ip>(?:[0-9]{1,3}\.){3}[0-9]{1,3})\b")

# Keywords indicating section / document hierarchy citations rather than network IP addresses (exact whole-word tokens)
_SECTION_CITATION_KEYWORDS = {"§", "section", "standard_ref", "textbook_ref", "chapter", "paragraph", "ref:", "title:", "pages:", "version", "semver"}

# Line heading context pattern (e.g. "### 4.1.3.1", "- 4.2.4.1", "1.2.3.4 Section Title", "| 4.1.3.1 |")
_SECTION_LINE_RE = re.compile(r"^\s*(?:[§#\*|-]|\d+\.)\s*(?:\d+\.){3}\d+|\|\s*(?:\d+\.){3}\d+\s*\|")

# Safe allowlist of four-octet IPs (loopback, public DNS, standard testing)
_SAFE_IP_ALLOWLIST = {
    "127.0.0.1",
    "0.0.0.0",
    "1.1.1.1",
    "1.0.0.1",
    "8.8.8.8",
    "8.8.4.4",
    "9.9.9.9",
    "4.2.2.2",
}

# Forbidden Private Key & SSH / Auth / Credential patterns (dynamically built to avoid self-triggering)
_BEGIN_PRIV = "-----BEGIN " + "PRIVATE KEY-----"
_PWLESS_SSH = "passwordless " + "SSH"

_FORBIDDEN_PATTERNS = [
    (re.compile(r"-----BEGIN\s+(?:[A-Z0-9_-]+\s+)?PRIVATE\s+KEY-----", re.IGNORECASE), "Private Key Header (PKCS#1/PKCS#8/OpenSSH/RSA/EC/DSA/Encrypted)"),
    (re.compile(r"passwordless\s+SSH", re.IGNORECASE), "Raw SSH auth method disclosure"),
]

# File extensions to skip (strictly binary / generated / virtual environment files)
_SKIP_EXTENSIONS = {
    ".db", ".db-journal", ".sqlite", ".sqlite3", ".pyc", ".png", ".jpg", ".jpeg",
    ".gif", ".webp", ".zip", ".tar", ".gz", ".7z", ".pdf", ".mp3", ".wav", ".ogg",
    ".lock"
}

# Public content trees and test files scanned (F001 fix: preserve scripts/audit/ via filter_rel_paths)
_SKIP_PATH_SUBSTRINGS = [
    ".git/",
    ".venv/",
    "node_modules/",
    "data/sources.db",
    "data/vesum.db",
    "wiki/.state/",
    "docs/references/external/",
    "requirements-lock.txt",
    "requirements.lock",
    "audit/",
    "_archive/",
]


def is_rfc1918(p0: int, p1: int) -> bool:
    """Return True if IP is in RFC 1918 private address ranges."""
    if p0 == 10:
        return True
    if p0 == 172 and 16 <= p1 <= 31:
        return True
    return p0 == 192 and p1 == 168


def is_section_citation(line: str, filename: str, p0: int, p1: int, p2: int, p3: int) -> bool:
    """Return True if a 4-part number is a document section citation, network base address, or semver string."""
    # Network base address or major version block (e.g. 120.0.0.0, 131.0.0.0)
    if p1 == 0 and p2 == 0 and p3 == 0:
        return True

    # State Standard section codes / semver strings / outline numbering (e.g. 4.1.3.1, 1.4.1.2)
    if p0 <= 15 and p0 != 10 and p1 <= 30 and p2 <= 30 and p3 <= 30:
        line_lower = line.lower()
        if any(kw in line_lower for kw in _SECTION_CITATION_KEYWORDS):
            return True
        if _SECTION_LINE_RE.search(line):
            return True
        if "#" in line or '"""' in line or "'''" in line or "//" in line:
            return True
        if '"' in line or "'" in line or "`" in line or ":" in line or "-" in line or "(" in line or "[" in line:
            return True
        if filename.endswith(".md") or filename.endswith(".mdx") or filename.endswith(".yaml") or filename.endswith(".yml") or filename.endswith(".txt"):
            return True

    return False


def check_content(content: str, filename: str) -> list[tuple[int, str, str]]:
    """Scan string content line by line for OPSEC leaks.

    Returns list of (line_num, match_str, description).
    """
    findings: list[tuple[int, str, str]] = []
    lines = content.splitlines()

    is_linter_itself = filename.replace("\\", "/").endswith("lint_opsec_leaks.py")

    for idx, line in enumerate(lines, 1):
        # Sol F001 / Fable F003: Precise self-scanning exemption on linter's own pattern definition constants
        if is_linter_itself and ("_FORBIDDEN_PATTERNS" in line or "_BEGIN_PRIV" in line or "_PWLESS_SSH" in line or "is_rfc1918" in line or "_SAFE_IP_ALLOWLIST" in line):
            continue

        # 1. Check for IPv4 addresses
        for match in _IPV4_RE.finditer(line):
            ip_str = match.group("ip")
            if ip_str in _SAFE_IP_ALLOWLIST:
                continue
            parts = ip_str.split(".")
            if all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                p0, p1, p2, p3 = (int(x) for x in parts)

                # RFC 1918 private IPs are ALWAYS flagged
                if is_rfc1918(p0, p1):
                    findings.append((idx, ip_str, "RFC 1918 Private IPv4 address"))
                    continue

                # Skip RFC 5737 documentation blocks (192.0.2.x, 198.51.100.x, 203.0.113.x)
                if (p0 == 192 and p1 == 0 and p2 == 2) or \
                   (p0 == 198 and p1 == 51 and p2 == 100) or \
                   (p0 == 203 and p1 == 0 and p2 == 113):
                    continue

                # Document section hierarchy / paragraph citation / semver check
                if is_section_citation(line, filename, p0, p1, p2, p3):
                    continue

                findings.append((idx, ip_str, "Raw IPv4 address"))

        # 2. Check forbidden key / credential patterns
        for pattern, desc in _FORBIDDEN_PATTERNS:
            if pattern.search(line):
                findings.append((idx, line.strip(), desc))

    return findings


def get_git_content(rel_path: str, rev: str = "") -> str | None:
    """Read exact blob content from git index or revision using 'git show <rev>:<path>'."""
    try:
        git_target = f":{rel_path}" if rev == "" else f"{rev}:{rel_path}"
        res = subprocess.run(
            ["git", "show", git_target],
            capture_output=True,
            cwd=REPO_ROOT,
            check=True
        )
        return res.stdout.decode("utf-8", errors="ignore")
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        return None


def run_git_nul_separated(cmd: list[str]) -> list[str]:
    """Sol F003: Run git command returning NUL-separated path bytes to handle quoted Unicode paths cleanly."""
    res = subprocess.run(cmd, capture_output=True, cwd=REPO_ROOT, check=True)
    raw_paths = res.stdout.split(b"\x00")
    decoded: list[str] = []
    for raw in raw_paths:
        if not raw:
            continue
        try:
            decoded.append(raw.decode("utf-8"))
        except UnicodeDecodeError:
            decoded.append(raw.decode("utf-8", errors="ignore"))
    return decoded


def get_files_to_check(diff_range: str | None = None, staged_only: bool = False, scan_all: bool = False) -> tuple[list[str], str, str]:
    """Return tuple of (list_of_relative_path_strings, mode_description, rev_target)."""
    if scan_all:
        cmd = ["git", "ls-files", "-z"]
        paths = run_git_nul_separated(cmd)
        return filter_rel_paths(paths), "all tracked files (--all)", "HEAD"

    if staged_only:
        cmd = ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACMRT"]
        paths = run_git_nul_separated(cmd)
        return filter_rel_paths(paths), "staged git index (:path)", ""

    if diff_range:
        rev_target = diff_range.split("..")[-1] if ".." in diff_range else "HEAD"
        cmd = ["git", "diff", "-z", "--name-only", "--diff-filter=ACMRT", diff_range]
        paths = run_git_nul_separated(cmd)
        return filter_rel_paths(paths), f"git diff ({diff_range})", rev_target

    # Sol F004 / Fable F007: Explicit pre-push ref environment check
    pre_push_local = os.environ.get("PRE_PUSH_LOCAL_REF") or os.environ.get("PRE_COMMIT_TO_REF", "")
    pre_push_remote = os.environ.get("PRE_PUSH_REMOTE_REF") or os.environ.get("PRE_COMMIT_FROM_REF", "")
    if pre_push_local and pre_push_remote and pre_push_remote != "0" * 40:
        range_spec = f"{pre_push_remote}..{pre_push_local}"
        cmd = ["git", "diff", "-z", "--name-only", "--diff-filter=ACMRT", range_spec]
        paths = run_git_nul_separated(cmd)
        return filter_rel_paths(paths), f"pre-push range ({range_spec})", pre_push_local

    # Default logic: staged > feature branch diff > HEAD~1..HEAD
    cmd_staged = ["git", "diff", "--cached", "-z", "--name-only", "--diff-filter=ACMRT"]
    staged_paths = run_git_nul_separated(cmd_staged)
    if staged_paths:
        return filter_rel_paths(staged_paths), "staged git index (:path)", ""

    # Feature branch diff mode
    try:
        branch_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT, check=True)
        curr_branch = branch_res.stdout.strip()
        if curr_branch and curr_branch != "main":
            cmd = ["git", "diff", "-z", "--name-only", "--diff-filter=ACMRT", "origin/main..HEAD"]
            paths = run_git_nul_separated(cmd)
            if paths:
                return filter_rel_paths(paths), "git diff (origin/main..HEAD)", "HEAD"
    except Exception:
        pass

    # Default commit range check for push/local
    cmd = ["git", "diff", "-z", "--name-only", "--diff-filter=ACMRT", "HEAD~1..HEAD"]
    paths = run_git_nul_separated(cmd)
    return filter_rel_paths(paths), "recent commit (HEAD~1..HEAD)", "HEAD"


def filter_rel_paths(paths: list[str]) -> list[str]:
    """Filter relative path strings by extension and skip patterns (F001: preserve scripts/audit/ via filter_rel_paths)."""
    valid_paths: list[str] = []
    for rel_str in paths:
        path_obj = Path(rel_str)
        if path_obj.suffix.lower() in _SKIP_EXTENSIONS:
            continue
        normalized = rel_str.replace("\\", "/")
        if normalized.startswith("scripts/audit/"):
            valid_paths.append(rel_str)
            continue
        if any(sub in normalized for sub in _SKIP_PATH_SUBSTRINGS):
            continue
        valid_paths.append(rel_str)
    return valid_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint repository for OPSEC leaks.")
    parser.add_argument("diff_range", nargs="?", help="Git diff range (e.g. origin/main..HEAD)")
    parser.add_argument("--staged", action="store_true", help="Inspect staged git index blobs")
    parser.add_argument("--all", action="store_true", help="Explicitly scan all tracked files in repo")
    args = parser.parse_args()

    try:
        rel_paths, mode_str, rev_target = get_files_to_check(args.diff_range, staged_only=args.staged, scan_all=args.all)
    except Exception as exc:
        print(f"💥 Fail-closed git error: {exc}", file=sys.stderr)
        return 1

    total_findings = 0

    print(f"🔒 Checking {len(rel_paths)} files for OPSEC leaks (mode: {mode_str})...")

    for rel_path in rel_paths:
        if "staged" in mode_str:
            content = get_git_content(rel_path, rev="")
        else:
            content = get_git_content(rel_path, rev=rev_target)

        if content is None:
            disk_path = REPO_ROOT / rel_path
            if not disk_path.is_file():
                continue
            try:
                content = disk_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

        findings = check_content(content, rel_path)

        if findings:
            total_findings += len(findings)
            print(f"\n❌ OPSEC LEAK DETECTED in [{rel_path}]:")
            for line_num, match_str, desc in findings:
                print(f"   Line {line_num}: [{desc}] -> {match_str!r}")

    if total_findings > 0:
        print(f"\n💥 Total OPSEC leaks found: {total_findings}")
        print("Please remove raw infrastructure IPs, host keys, and auth details before submitting!")
        return 1

    print("✅ OPSEC check passed. Zero leaks detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
