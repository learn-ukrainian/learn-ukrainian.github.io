#!/usr/bin/env python3
"""Rename machinery module invocations and resource paths outside Python code, failing closed.

Uses the ownership model in ``rename_python.py`` (same map, same module names). A
``scripts`` module name or path is rewritten only when it is a complete plain token: a whole
word, or a whole quoted word, with nothing glued to it and nothing that the shell or the file
format could expand or continue. Every other ``scripts`` module name or path is reported.
Python files belong to rename_python.py; files that ``rename_structured.py`` knows belong to it.

Invariant for run-time pieces (``scan_pieces`` is the one place every opening passes through): a ``$(``,
``${`` or backtick piece is read only when its text stays inside the readable subset (balanced quotes, nested
pieces of the same subset, none of ``#``, ``case``, ``<<``, ``;;``, ``((``, ``$[`` or a line continuation, no single
quote in ``${...}``, no backtick in a piece nested in backticks, at most ``MAX_PIECE`` characters and
``MAX_NESTING`` levels); every other opening is refused. A refused opening is never text: ``refused_glue``
reads it as a wildcard, like every unquoted glob and brace expansion in shell text, and reports every letter
run glued to a wildcard that could spell ``scripts`` with it (a prefix in front of it, a suffix after a place
where it may end, or a slice between two), and never rewrites it.
"""

from __future__ import annotations

import argparse
import bisect
import bz2
import gzip
import importlib.util
import io
import lzma
import os
import re
import sys
import zipfile
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from types import ModuleType


def _load(name: str, filename: str) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().with_name(filename))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rp = _load("machinery_move_rename_python", "rename_python.py")
rs = _load("machinery_move_rename_structured", "rename_structured.py")
AMBIGUOUS, MACHINERY, PRODUCT = rp.AMBIGUOUS, rp.MACHINERY, rp.PRODUCT
OLD_ROOT, NEW_ROOT = rp.OLD_ROOT, rp.NEW_ROOT
Finding, OwnershipMap, Report = rp.Finding, rp.OwnershipMap, rp.Report
WORD = rp.WORD

# The characters a plain token may contain after ``scripts``.
TOKEN_CHARS = re.compile(r"[A-Za-z0-9_.\-/]*")
# An entry point after a module name: ``scripts.api.main:app``.
ENTRY_POINT = re.compile(r":[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
MODULE_NAME = re.compile(r"scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
# A prefix naming the repository root in front of a path: ``./``, ``../``, ``$ROOT/``, ``${ROOT}/``, ``@REPO_ROOT@/``.
ROOT_PREFIX = re.compile(r"(?:\$[A-Za-z_][A-Za-z0-9_]*|\$\{[A-Za-z_][A-Za-z0-9_]*\}|@[A-Za-z_][A-Za-z0-9_]*@|\.\.?)/$")
# Variables that name a place outside the repository by convention: a path under them is not renamed.
FOREIGN_VARIABLES = re.compile(r"\$\{?(?:HOME|TMPDIR|TMP|TEMP|XDG_[A-Z_]+)\}?/$")
# What may come right before a token (or its opening quote), and right after it (or its closing quote).
BEFORE_OK = frozenset(" \t\n=")
AFTER_OK = frozenset(" \t\n;&|)")  # ``<`` or ``>`` glued on may be a placeholder: ``<name>``
# Closing punctuation that may follow a name in a message without continuing it.
CLOSING = frozenset(".,:;!?)]}>'\"`")
HEREDOC = re.compile(
    r"<<(?!<)(?P<dash>-?)[ \t]*(?:(?P<q>[\"'])(?P<qword>[^\"'\n]+)(?P=q)|\\?(?P<word>(?:[^\s;&|<>()\"'`]|\"[^\"\n]*\"|'[^'\n]*')+))"
)
# Commands and settings that change the working directory to the path that follows.
CWD_BEFORE = re.compile(
    r"(?:(?:^|[\s;&|(`\"'])(?:cd|pushd)(?:\s+-{1,2}[\w-]*)*\s+|WorkingDirectory=|(?:^|\s)WORKDIR\s+|(?:^|\s)-C\s*"
    r"|(?:^|\s)--(?:directory|cwd|chdir|workdir|working-directory|prefix|rootdir)(?:=|\s+)|(?:^|\s)-w\s*"
    r"|(?:^|[\s{,\"'])(?i:cwd|chdir|workdir|working[-_]dir(?:ectory)?|changedir|rootdir)[\"']?\s*[:=]\s*)[\"']?$"
)
INTERPRETER_BEFORE = re.compile(
    r"(?:^|[\s;&|(\"'])(?:\S*python[0-9.]*|\"?\$\{?PY\w*\}?\"?|bash|sh|zsh|exec|source|\.|uv\s+run(?:\s+python[0-9.]*)?)\s+[\"']?$"
)
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
FROM_IMPORT_AFTER = re.compile(r"[ \t]+import\b")
INDENTED_CODE = re.compile(r"^(?: {4}|\t)\s*\S")
INLINE_CODE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)")
SHELL_FENCE_INFO = frozenset({"bash", "sh", "shell", "zsh", "console", "shell-session", "sh-session", "terminal"})
# A field that records a digest: the file's paths are bound to it and must not change by text edits.
# Escapes that can spell a name without its letters appearing: JSON/YAML/TOML/shell, XML entities, URLs. The
# shell's ``$'…'`` and printf read one to four (``\u``) or eight (``\U``) hex digits, as many as follow.
ESCAPE = re.compile(
    r"\\u[0-9a-fA-F]{1,4}|\\U[0-9a-fA-F]{1,8}|\\x[0-9a-fA-F]{2}|\\[0-7]{1,3}|&#[0-9]{1,7};|&#[xX][0-9a-fA-F]{1,6};|%[0-9a-fA-F]{2}"
)
# What a reader joins or removes before a name shows: line continuations, escapes, a backslash before a
# character, and the ``$`` that starts a ``$'…'`` or ``$"…"`` quote (the quotes go as quoted pieces). Run-time
# pieces are found by ``scan_pieces``, which balances nested ones.
HIDING = re.compile(r"\\[ \t]*\r?\n\s*|" + ESCAPE.pattern + r"|\\(?=\S)|\$(?=['\"])")
# Where a run-time piece starts: a substitution or expansion (``$(``, ``$((``, ``${``, backticks), which
# can nest, or a leaf that cannot: a variable (``$X``, ``$1``, ``$@``), a template field, or a ``$'…'`` quote with
# an escape in it, whose characters are known only once the shell reads the escapes.
PIECE_START = re.compile(
    r"\$\(|\$\{|`|\$'[^'\\]{0,4096}(?:\\[\s\S][^'\\]{0,4096}){1,256}'"
    r"|\$[A-Za-z_][A-Za-z0-9_]*|\$[0-9@*#?!]|\{\{[^}\n]*\}\}|\{%[^%\n]*%\}"
)
OPENINGS = {"$(": ")", "${": "}", "`": "`"}
# What may end, nest in or quote a piece body, outside double quotes and inside them.
BODY_STOPS = {")": re.compile(r"[\\'\"`$(){}]"), "}": re.compile(r"[\\'\"`$(){}]"), "`": re.compile(r"[\\`$]")}
DOUBLE_QUOTED_STOPS = re.compile(r"[\\\"`${]")
MAX_PIECE = 64 * 1024  # a longer piece is refused: the scanner does not know where it ends
MAX_NESTING = 64  # a piece nested deeper is refused, and so is every piece around it
# The readable subset: a piece is read only when its text holds none of these. A comment, a case clause, a heredoc,
# arithmetic (``((``, ``$[``) and a line continuation each change where a shell ends the piece, so a piece with one
# is refused.
OUTSIDE_SUBSET = re.compile(r"#|<<|;;|\(\(|\$\[|\\\r?\n|(?<![A-Za-z0-9_])case(?![A-Za-z0-9_])")
# A refused opening in the glue view: a wildcard of unknown length, never text.
WILDCARD = "\0"
# Other shell expansions the tool does not compute: a glob (``*``, ``?``, ``[...]``) and a brace expansion
# (``{a,b}``, ``{a..b}``). Their extent is known, so each is one wildcard that ends where its text ends.
GLOB_START = re.compile(r"[*?\[{]")
LETTERS = re.compile(r"[A-Za-z]+")
# A quoted piece glued to a word: the shell drops its quotes and joins it (``scr""ipts``, ``scr"i"pts``).
# A lone apostrophe (``script's``) is no quoted piece.
QUOTED_PIECE = re.compile(r"(?<=\S)([\"'])[^\"'\s]*\1|([\"'])[^\"'\s]*\2(?=\S)")
ANY_CASE = re.compile(r"(?i)scripts")
# The name in bytes: in any case, or as UTF-16 text (little or big endian).
ANY_BYTES_CASE = re.compile(rb"(?i)scripts|s\0c\0r\0i\0p\0t\0s|\0s\0c\0r\0i\0p\0t\0s")
MAX_UNPACKED = 64 * 1024 * 1024
DIGEST_FIELD = re.compile(
    r"(?i)(?:sha256|sha1|sha512|digest|fingerprint|checksum|hash)[\"']?\s*[:=]\s*[\"']?[0-9a-f]{40,}"
)

SHELL_SUFFIXES = (".sh", ".bash", ".zsh")
UNIT_SUFFIXES = (".service", ".timer", ".socket", ".path", ".target", ".mount")
PLIST_SUFFIXES = (".plist", ".plist.disabled")
JSON_SUFFIXES = (".json",)
TEXT_SUFFIXES = (
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".tsv", ".j2", ".jinja", ".txt", ".env", ".example",
)  # fmt: skip
# Pattern files where a leading "/" anchors at the repository root rather than the filesystem root.
ROOT_ANCHORED_NAMES = frozenset({".gitattributes", ".gitignore", ".dockerignore", ".trufflehogignore", "CODEOWNERS"})
SHELL_NAMES = frozenset({"Makefile", "Dockerfile", "justfile", "Procfile"})
MARKDOWN_SUFFIXES = (".md", ".markdown", ".mdx")
MAX_BYTES = 4 * 1024 * 1024

SHELL, TEXT, JSON, PLIST, MARKDOWN, PYTHON, OTHER = "shell", "text", "json", "plist", "markdown", "python", "other"


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    replacement: str


def classify(rel: str, head: bytes) -> str:
    name = PurePosixPath(rel).name
    if name.endswith(".py"):
        return PYTHON
    if name.endswith(MARKDOWN_SUFFIXES):
        return MARKDOWN
    if name.endswith(JSON_SUFFIXES):
        return JSON
    if name.endswith(PLIST_SUFFIXES):
        return PLIST
    if name.endswith(SHELL_SUFFIXES) or name in SHELL_NAMES:
        return SHELL
    if name.endswith(UNIT_SUFFIXES + TEXT_SUFFIXES) or name in ROOT_ANCHORED_NAMES:
        return TEXT
    if head.startswith(b"#!"):
        return PYTHON if b"python" in head.split(b"\n", 1)[0] else SHELL
    parts = PurePosixPath(rel).parts
    if "." not in name and any(part in (".githooks", "hooks") for part in parts[:-1]):
        return SHELL
    return OTHER


# -- the shell lexer -----------------------------------------------------------


@dataclass(frozen=True)
class Context:
    """Where a position sits: the innermost open quote or substitution (``top``, ``'``, ``"``, ``$(``,
    ``` ` ```, ``${``, ``$((``), where that one opened, and whether the position is in a comment or
    a heredoc body."""

    frame: str
    opened_at: int
    comment: bool = False
    heredoc: bool = False


class ShellLexer:
    """Track quotes, substitutions, comments and heredoc bodies across a text, as the shell reads them.

    It only has to be right where it says a word is plain. Anything it does not follow (an
    unparsable heredoc, a quote left open) makes later words look quoted or heredoc text, which
    the caller reports.
    """

    def __init__(self, text: str, regions: Sequence[tuple[int, int]]) -> None:
        self.text = text
        self.regions = regions

    def contexts(self, positions: Sequence[int]) -> dict[int, Context]:
        wanted = sorted(set(positions))
        result: dict[int, Context] = {}
        for start, end in self.regions:
            inside = [p for p in wanted if start <= p < end]
            if inside:
                result.update(self._scan(start, end, inside))
        return result

    def _scan(self, start: int, end: int, wanted: list[int]) -> dict[int, Context]:
        text = self.text
        stack: list[tuple[str, int]] = [("top", -1)]
        pending: list[tuple[str | None, bool]] = []  # heredoc words (None: unparsable) waiting for the line end
        result: dict[int, Context] = {}
        want = iter(wanted)
        next_wanted = next(want, None)
        heredoc_until = -1
        comment_until = -1
        i = start
        while i < end and next_wanted is not None:
            while next_wanted is not None and next_wanted <= i:
                frame, opened = stack[-1]
                result[next_wanted] = Context(frame, opened, next_wanted < comment_until, next_wanted < heredoc_until)
                next_wanted = next(want, None)
            if next_wanted is None:
                break
            char = text[i]
            frame = stack[-1][0]
            if char == "\n":
                i += 1
                if pending and frame in ("top", "$(", "`"):
                    words, pending = pending, []
                    i = heredoc_until = self._skip_heredocs(i, end, words)
                continue
            if frame == "'":
                if char == "'":
                    stack.pop()
                i += 1
                continue
            if char == "\\":
                i += 2
                continue
            if frame == '"':
                if char == '"':
                    stack.pop()
                elif text.startswith("$((", i):
                    stack.append(("$((", i))
                    i += 3
                    continue
                elif text.startswith("$(", i):
                    stack.append(("$(", i))
                    i += 2
                    continue
                elif text.startswith("${", i):
                    stack.append(("${", i))
                    i += 2
                    continue
                elif char == "`":
                    stack.append(("`", i))
                i += 1
                continue
            if frame == "${":
                if char == "}":
                    stack.pop()
                elif char in "'\"":
                    stack.append((char, i))
                elif text.startswith("${", i) or text.startswith("$(", i):
                    stack.append((text[i : i + 2], i))
                    i += 2
                    continue
                i += 1
                continue
            if frame == "$((":
                if text.startswith("))", i):
                    stack.pop()
                    i += 2
                    continue
                i += 1
                continue
            # top, $( and backtick: words, quotes, operators.
            if char in "'\"":
                stack.append((char, i))
            elif char == "`":
                if frame == "`":
                    stack.pop()
                else:
                    stack.append(("`", i))
            elif text.startswith("$((", i):
                stack.append(("$((", i))
                i += 3
                continue
            elif text.startswith("$(", i) or text.startswith("${", i):
                stack.append((text[i : i + 2], i))
                i += 2
                continue
            elif char == ")" and frame == "$(":
                stack.pop()
            elif char == "#" and (i == start or text[i - 1] in " \t\n;&|("):
                line_end = text.find("\n", i, end)
                comment_until = end if line_end < 0 else line_end
                i = comment_until
                continue
            elif char == "<" and (match := HEREDOC.match(text, i)):
                word = match.group("qword") or match.group("word")
                if match.group("word") and re.search(r"[\"'\\]", word):
                    word = None  # quotes or backslashes inside the word: not followed; the rest is its body
                pending.append((word, bool(match.group("dash"))))
                i = match.end()
                continue
            elif text.startswith("<<", i) and not text.startswith("<<<", i):
                pending.append((None, False))  # a heredoc whose word is not understood: the rest is its body
            i += 1
        while next_wanted is not None:
            frame, opened = stack[-1]
            result[next_wanted] = Context(frame, opened, next_wanted < comment_until, next_wanted < heredoc_until)
            next_wanted = next(want, None)
        return result

    def _skip_heredocs(self, i: int, end: int, words: list[tuple[str | None, bool]]) -> int:
        """Skip the bodies of the heredocs started on the line before ``i``; return where they end."""

        text = self.text
        for word, dash in words:
            if word is None:
                return end
            while i < end:
                line_end = text.find("\n", i, end)
                line_end = end if line_end < 0 else line_end
                line = text[i:line_end]
                i = min(end, line_end + 1)
                if (line.lstrip("\t") if dash else line) == word:
                    break
            else:
                return end
        return i


# -- tokens ----------------------------------------------------------------------


@dataclass(frozen=True)
class Occurrence:
    """One ``scripts`` word in a text, with the token around it."""

    start: int  # where ``scripts`` starts
    end: int  # where the token's name ends
    prefix_start: int  # where the root prefix (``$ROOT/``) starts; == start without one
    name: str


def occurrences(text: str) -> Iterator[Occurrence]:
    covered = -1  # the end of the last token: a ``scripts`` inside it (``scripts/a/scripts/b``) is part of it
    for match in rp.word_matches(text):
        start = match.start()
        if start < covered:
            continue
        tail = TOKEN_CHARS.match(text, match.end()).group(0)  # type: ignore[union-attr]
        end = match.end() + len(tail)
        name = text[start:end]
        if MODULE_NAME.fullmatch(name) and (entry := ENTRY_POINT.match(text, end)):
            end, name = entry.end(), text[start : entry.end()]
        prefix_start = start
        line_start = text.rfind("\n", 0, start) + 1
        for back in range(start - 1, max(line_start, start - 64) - 1, -1):
            if ROOT_PREFIX.fullmatch(text, back, start) and (back == line_start or text[back - 1] not in "./$@}"):
                prefix_start = back
                break
        covered = end
        yield Occurrence(start, end, prefix_start, name)


@dataclass
class Verdict:
    """What one token is: rewrite it, keep it, report it, or list it."""

    action: str  # rewrite, keep, unresolved, inventory
    kind: str = ""
    detail: str = ""
    target: str = ""


def name_target(ownership: OwnershipMap, name: str) -> tuple[str, str]:
    """(form, owner) of a complete token: module, path, glob or root, and machinery/product/ambiguous/unknown."""

    if name in (OLD_ROOT, OLD_ROOT + "/", OLD_ROOT + "."):
        return "root", AMBIGUOUS
    if name.startswith(OLD_ROOT + "/"):
        if set(name) & set("*?["):
            return "glob", glob_target(ownership, name)
        return "path", rp.path_target(ownership, name)
    module = name.partition(":")[0]
    if not MODULE_NAME.fullmatch(module) or module.endswith("."):
        return "module", "unknown"
    return "module", rp.module_target(ownership, module, exact=True)


def glob_target(ownership: OwnershipMap, pattern: str) -> str:
    owners = set()
    for key, owner in ownership.files.items():
        parents = [p.as_posix() for p in PurePosixPath(key).parents]
        if fnmatchcase(key, pattern) or any(fnmatchcase(p, pattern) for p in parents):
            owners.add(owner)
    return "unknown" if not owners else owners.pop() if len(owners) == 1 else AMBIGUOUS


@dataclass
class FileScan:
    """Context for one file: what kind it is and where its code regions are."""

    ownership: OwnershipMap
    rel: str
    text: str
    kind: str
    code_regions: list[tuple[int, int]] = field(default_factory=list)  # Markdown: code spans and fences
    shell_regions: list[tuple[int, int]] = field(default_factory=list)  # where the shell lexer applies
    contexts: dict[int, Context] = field(default_factory=dict)
    json_strings: list[tuple[int, int, str | None]] = field(default_factory=list)
    comment_regions: list[tuple[int, int]] = field(default_factory=list)  # INI ``;`` lines, Jinja ``{# #}``

    @property
    def root_anchored(self) -> bool:
        return PurePosixPath(self.rel).name in ROOT_ANCHORED_NAMES

    @property
    def file_owner(self) -> str | None:
        return self.ownership.file_owner(self.rel)


def judge(scan: FileScan, occ: Occurrence) -> Verdict:
    """Decide one occurrence. Only a complete plain token naming machinery is rewritten."""

    text = scan.text
    form, target = name_target(scan.ownership, occ.name)
    if scan.kind == MARKDOWN and not _in_regions(scan.code_regions, occ.start):
        if target == PRODUCT:
            return Verdict("keep")
        return Verdict("inventory", "prose_mention", "Markdown prose is left as written", target)
    if scan.kind in (OTHER, PYTHON):
        if target == PRODUCT and _ends_cleanly(text, occ.end):
            return Verdict("keep")
        detail = "a Python file without a .py suffix" if scan.kind == PYTHON else "no rewrite rule for this file type"
        return Verdict("unresolved", "unsupported_file_type", detail, target)
    context = scan.contexts.get(occ.start)
    if _in_regions(scan.comment_regions, occ.start):
        context = Context("top", -1, comment=True)
    if context is not None and context.comment:
        if target == PRODUCT:
            return Verdict("keep")
        return Verdict("inventory", "comment_mention", "comments are left as written", target)
    if context is not None and context.heredoc:
        return _unless_product(
            text, occ, target, "heredoc_text", "inside a heredoc body; its text is data or another program"
        )
    reason = plain_reason(scan, occ, context)
    if reason:
        # The bare root in running text is usually the English word; its own kind lets it be triaged apart.
        return _unless_product(text, occ, target, "root_in_text" if form == "root" else "not_plain", reason)
    if form == "root":
        return Verdict("unresolved", "root_reference", "the scripts/ root is split between both owners", AMBIGUOUS)
    if CWD_BEFORE.search(text[text.rfind("\n", 0, occ.prefix_start) + 1 : _quote_start(scan, occ, context)]):
        return Verdict(
            "unresolved", "cwd_into_scripts", "relative paths after a directory change depend on the old layout", target
        )
    if target == PRODUCT:
        return Verdict("keep")
    if form == "module" and FROM_IMPORT_AFTER.match(text, occ.end):
        # ``from scripts.x import y`` in documentation or a template: y may have the other owner.
        return Verdict("unresolved", "python_import_in_text", "a Python from-import; split it by hand", target)
    if target == MACHINERY:
        return Verdict("rewrite", "module_name" if form == "module" else "resource_path", target=MACHINERY)
    kinds = {"glob": "glob_path", "path": "unknown_path", "module": "unknown_module"}
    kind = "ambiguous_" + ("module" if form == "module" else "path") if target == AMBIGUOUS else kinds[form]
    details = {
        "ambiguous_module": "the module or its __main__ has more than one owner",
        "ambiguous_path": "the path or glob covers files of both owners",
        "glob_path": "the glob matches no mapped file",
        "unknown_path": "the map has no file or directory here",
        "unknown_module": "the map has no such module",
    }
    return Verdict("unresolved", kind, details[kind], target)


def _unless_product(text: str, occ: Occurrence, target: str, kind: str, detail: str) -> Verdict:
    """A name that is not plain is kept only when it is exactly a product file or module and nothing continues it."""

    if target == PRODUCT and _ends_cleanly(text, occ.end):
        return Verdict("keep")
    return Verdict("unresolved", kind, detail, target)


def _ends_cleanly(text: str, end: int) -> bool:
    """Only closing punctuation follows the name up to the next blank, so nothing can extend it."""

    i = end
    while i < len(text) and not text[i].isspace():
        if text[i] not in CLOSING:
            return False
        i += 1
    return True


def _quote_start(scan: FileScan, occ: Occurrence, context: Context | None) -> int:
    if context is not None and context.frame in ("'", '"') and context.opened_at == occ.prefix_start - 1:
        return occ.prefix_start - 1
    if scan.kind == JSON and occ.prefix_start > 0 and scan.text[occ.prefix_start - 1] == '"':
        return occ.prefix_start - 1
    return occ.prefix_start


def plain_reason(scan: FileScan, occ: Occurrence, context: Context | None) -> str:
    """Why this token is not a complete plain token, or "" when it is."""

    text = scan.text
    start, end = occ.prefix_start, occ.end
    if scan.root_anchored and start == occ.start and start > 0 and text[start - 1] == "/":
        start -= 1  # ``/scripts/x`` in a pattern file is anchored at the repository root
    if FOREIGN_VARIABLES.fullmatch(text, start, occ.start):
        return "the path is under a directory outside the repository"
    if scan.kind == JSON:
        return _json_plain_reason(scan, occ)
    if scan.kind == PLIST:
        if text[max(0, start - 8) : start] == "<string>" and text.startswith("</string>", end):
            return ""
        return "not the whole text of a plist <string>"
    after_char = _after(scan, end)
    if after_char in "*?[":
        return "a glob"
    frame = context.frame if context is not None else "top"
    if frame in ("top", "$(", "`"):
        before = _before(scan, start)
        allowed = (
            before in BEFORE_OK
            or (
                before == "m" and text[start - 2 : start] == "-m" and _before(scan, start - 2) in BEFORE_OK
            )  # -mscripts.x
            or (before == "(" and text[start - 2 : start] == "$(")
            or (scan.root_anchored and before == "!" and _before(scan, start - 1) in BEFORE_OK)  # !/scripts/x
        )
        if not allowed:
            return f"{before!r} is glued in front of it"
        if after_char not in AFTER_OK:
            return f"{after_char!r} continues it"
        if frame == "`":
            return "inside backticks"
        return ""
    if frame in ("'", '"'):
        assert context is not None
        if context.opened_at != start - 1:
            return "inside a longer quoted text"
        if after_char != frame:
            return "the quoted text goes on after it"
        outer_before = _before(scan, start - 1)
        if outer_before not in BEFORE_OK:
            return f"{outer_before!r} is glued in front of the quote"
        following = _after(scan, end + 1)
        if following not in AFTER_OK:
            return f"{following!r} continues the quoted word"
        return ""
    return "inside an expansion"


def _before(scan: FileScan, position: int) -> str:
    """The character before ``position``; the start of a Markdown code span counts as a line start."""

    if position <= 0 or (scan.kind == MARKDOWN and any(start == position for start, _ in scan.code_regions)):
        return "\n"
    text = scan.text
    if text[position - 1] == "\n":  # a line continuation joins the word to the end of the line before
        i = position - 2 - (position >= 2 and text[position - 2] == "\r")
        backslashes = 0
        while i - backslashes >= 0 and text[i - backslashes] == "\\":
            backslashes += 1
        if backslashes % 2:
            return "\\"
    return text[position - 1]


def _after(scan: FileScan, position: int) -> str:
    """The character at ``position``; the end of a Markdown code span counts as a line end."""

    if position >= len(scan.text) or (scan.kind == MARKDOWN and any(end == position for _, end in scan.code_regions)):
        return "\n"
    return scan.text[position]


def _json_plain_reason(scan: FileScan, occ: Occurrence) -> str:
    for start, end, value in scan.json_strings:
        if start < occ.start < end:
            if value is None:
                return "a JSON string with escapes"
            if start + 1 == occ.prefix_start and end - 1 == occ.end:
                return ""
            return "part of a longer JSON string"
    return "not inside a JSON string"


def json_strings(text: str) -> list[tuple[int, int, str | None]]:
    """(start, end, raw value or None when it has escapes) of every JSON string, quotes included."""

    spans: list[tuple[int, int, str | None]] = []
    i = 0
    while True:
        i = text.find('"', i)
        if i < 0:
            return spans
        j = i + 1
        escaped = False
        while j < len(text) and text[j] != '"':
            if text[j] == "\\":
                escaped = True
                j += 1
            j += 1
        if j >= len(text):
            spans.append((i, len(text), None))
            return spans
        spans.append((i, j + 1, None if escaped else text[i + 1 : j]))
        i = j + 1


_LINE_STARTS: dict[int, tuple[str, list[int]]] = {}


def line_number(text: str, offset: int) -> int:
    """The 1-based line of ``offset``; line starts are computed once per text."""

    cached = _LINE_STARTS.get(id(text))
    if cached is None or cached[0] is not text:
        _LINE_STARTS.clear()
        cached = (text, [0, *(m.end() for m in re.finditer("\n", text))])
        _LINE_STARTS[id(text)] = cached
    return bisect.bisect_right(cached[1], offset)


def extra_comment_regions(rel: str, text: str) -> list[tuple[int, int]]:
    """Comments the shell lexer does not know: ``;`` lines in INI-style files, ``{# … #}`` in Jinja templates."""

    regions: list[tuple[int, int]] = []
    name = PurePosixPath(rel).name
    if name.endswith((".ini", ".cfg", ".conf")):
        regions += [m.span() for m in re.finditer(r"(?m)^[ \t]*;.*$", text)]
    if name.endswith((".j2", ".jinja", ".html")):
        regions += [m.span() for m in re.finditer(r"(?<!\$)\{#.*?#\}", text, re.S)]
    return regions


def _in_regions(regions: Sequence[tuple[int, int]], position: int) -> bool:
    return any(a <= position < b for a, b in regions)


def markdown_regions(text: str) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """(code regions, shell regions) of a Markdown text.

    Code regions are inline code spans and fenced blocks tagged as shell; the shell regions are
    those fences and each code span. Other fences are reported: their language is not shell.
    """

    code: list[tuple[int, int]] = []
    shell: list[tuple[int, int]] = []
    offset = 0
    fence: str | None = None
    fence_start = 0
    shellish = False
    previous = ""
    indented = False
    for line in text.splitlines(keepends=True):
        match = FENCE.match(line)
        if fence is None and match:
            indented = False
            info = line[match.end() :].strip().split(None, 1)
            fence, fence_start = match.group(1), offset + len(line)
            shellish = (info[0].strip("{}.").lower() if info else "") in SHELL_FENCE_INFO
        elif (
            fence is not None
            and match
            and match.group(1)[0] == fence[0]
            and len(match.group(1)) >= len(fence)
            and not line[match.end() :].strip()  # a closing fence has no info string
        ):
            code.append((fence_start, offset))
            if shellish:
                shell.append((fence_start, offset))
            fence = None
        elif fence is None and INDENTED_CODE.match(line) and (not previous.strip() or indented):
            code.append((offset, offset + len(line)))  # an indented code block: code in no known language
            indented = True
        elif fence is None:
            indented = False
            for m in INLINE_CODE.finditer(line):
                code.append((offset + m.start(2), offset + m.end(2)))
                shell.append((offset + m.start(2), offset + m.end(2)))
        offset += len(line)
        previous = line
    if fence is not None:
        code.append((fence_start, len(text)))
        if shellish:
            shell.append((fence_start, len(text)))
    return code, shell


def _unescape_one(token: str) -> str:
    try:
        if token.startswith("&#"):
            code = int(token[3:-1], 16) if token[2] in "xX" else int(token[2:-1])
        elif token.startswith("%"):
            code = int(token[1:], 16)
        elif token[1] in "uUx":
            code = int(token[2:], 16)
        else:
            code = int(token[1:], 8)
        return chr(code)
    except (ValueError, OverflowError):
        return token


@dataclass
class JoinedView:
    """A text with every way of splitting or disguising a word undone, and where each part came from."""

    text: str
    segments: list[tuple[int, int, int, bool]]  # (start in the view, start in the source, length in the view, verbatim)
    starts: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.starts[:] = [segment[0] for segment in self.segments]

    def source_offset(self, position: int) -> int:
        index = bisect.bisect_right(self.starts, position) - 1
        view_start, source_start, _length, verbatim = self.segments[index]
        return source_start + (position - view_start if verbatim else 0)

    def verbatim(self, start: int, end: int) -> bool:
        """Whether ``[start, end)`` of the view is copied unchanged from one stretch of the source."""

        index = bisect.bisect_right(self.starts, start) - 1
        view_start, _source, length, verbatim = self.segments[index]
        return verbatim and end <= view_start + length


@dataclass(frozen=True)
class Piece:
    """A run-time piece in a text, with the pieces nested in its body.

    ``opening`` and ``closing`` are the lengths of its delimiters (``$(`` and ``)``); both are 0 for a leaf,
    a variable, a template field or an escaped ``$'…'`` quote (``escaped``), whose text is never a word of its own.
    ``refused`` says why a substitution that closes is still outside the readable subset ("" when it is read).
    """

    start: int
    end: int
    opening: int = 0
    closing: int = 0
    children: tuple[Piece, ...] = ()
    escaped: bool = False
    refused: str = ""


@dataclass(frozen=True)
class Refusal:
    """A refused opening: where it starts, the length of its delimiter and why the scanner refuses it."""

    start: int
    opening: int
    reason: str


@dataclass(frozen=True)
class PieceScan:
    """Every run-time piece of a text, and every opening the scanner refuses.

    ``pieces`` are the outermost pieces that close, read or refused, each with its nested pieces; the views
    use them as before. ``glue`` is what the glue rule reads: the same scan, except that it goes on inside a
    refused piece instead of after it, because a refused piece's end is not known; so every opening in the
    text that no read piece holds is in it. ``unclosed`` are the openings that do not close within
    ``MAX_PIECE`` and ``MAX_NESTING``.
    """

    pieces: list[Piece]
    glue: list[Piece]
    unclosed: list[Refusal]

    def refusals(self) -> list[Refusal]:
        """Every refused opening the glue rule reads as a wildcard."""

        refused = [Refusal(piece.start, piece.opening, piece.refused) for piece in self.glue if piece.refused]
        return sorted([*self.unclosed, *refused], key=lambda refusal: refusal.start)


def scan_pieces(text: str) -> PieceScan:
    """Find the run-time pieces of a text by a balanced scan, and every opening outside the readable subset.

    This is the one place every ``$(``, ``${`` and backtick opening passes through. An opening is read only
    when its piece closes within ``MAX_PIECE`` characters and ``MAX_NESTING`` levels, its quotes balance,
    every piece nested in it is read, and its text holds nothing in ``OUTSIDE_SUBSET`` (nor, for ``${``,
    a single quote, which a shell reads differently inside and outside double quotes, nor, for a backtick,
    a backtick inside a nested piece). Every other opening is refused. A refused opening that does not
    close is no piece: the scan goes on right after it, so the pieces in what would have been its body
    still count.
    """

    scanner = _PieceScanner(text)

    def scan(enter_refused: bool) -> tuple[list[Piece], list[Refusal]]:
        pieces: list[Piece] = []
        unclosed: list[Refusal] = []
        position = 0
        while (match := PIECE_START.search(text, position)) is not None:
            piece = scanner.piece_at(match.start(), 0)
            if isinstance(piece, Piece):
                pieces.append(piece)
                position = match.start() + 1 if enter_refused and piece.refused else piece.end
            else:
                if isinstance(piece, str):
                    unclosed.append(Refusal(match.start(), len(match.group(0)), piece))
                position = match.start() + 1
        return pieces, unclosed

    pieces = scan(enter_refused=False)[0]
    glue, unclosed = scan(enter_refused=True)
    return PieceScan(pieces, glue, unclosed)


def run_time_pieces(text: str) -> list[Piece]:
    """The outermost run-time pieces of a text that close, read or refused, each with its nested pieces."""

    return scan_pieces(text).pieces


class _PieceScanner:
    """Scans piece bodies as a shell does: nested pieces, quotes, backslashes and balanced brackets.

    ``piece_at`` returns the piece at an opening, or why the opening does not close (a string), or None when
    no piece starts there. Each opening is scanned once (``memo``), so the scan stays linear in the text
    times ``MAX_PIECE``.
    """

    def __init__(self, text: str) -> None:
        self.text = text
        self.memo: dict[int, Piece | str] = {}

    def piece_at(self, start: int, nesting: int) -> Piece | str | None:
        match = PIECE_START.match(self.text, start)
        if match is None:
            return None
        if match.group(0) not in OPENINGS:
            return Piece(start, match.end(), escaped=match.group(0).startswith("$'"))
        if start in self.memo:
            return self.memo[start]
        if nesting >= MAX_NESTING:
            return f"nested more than {MAX_NESTING} deep"  # not remembered: from a shallower start it may close
        piece = self.memo[start] = self._closed(start, match.group(0), nesting)
        return piece

    def _closed(self, start: int, opening: str, nesting: int) -> Piece | str:
        text, closer = self.text, OPENINGS[opening]
        limit = min(len(text), start + MAX_PIECE)
        unclosed = f"longer than {MAX_PIECE} characters" if limit < len(text) else "never closes"
        children: list[Piece] = []
        refused = ""  # why a nested piece puts this one outside the readable subset
        depth = 0  # open brackets of the closer's kind inside the body
        quoted = False  # inside double quotes (never in backticks, which end at the next unescaped backtick)
        position = start + len(opening)
        while True:
            stop = (DOUBLE_QUOTED_STOPS if quoted else BODY_STOPS[closer]).search(text, position, limit)
            if stop is None:
                return unclosed
            position, char = stop.start(), stop.group(0)
            if char == "\\":
                position += 2
            elif char == closer and not quoted and depth == 0:
                end = position + 1
                refused = refused or _outside_subset(text, start, end, opening)
                return Piece(start, end, len(opening), 1, tuple(children), refused=refused)
            elif char == closer and not quoted:
                depth -= 1
                position += 1
            elif quoted and text.startswith("$'", position):
                position += 1  # inside double quotes ``$'`` is no quote
            elif char in "$`" or text.startswith(("{{", "{%"), position):
                child = self.piece_at(position, nesting + 1)
                if isinstance(child, Piece):
                    children.append(child)
                    position = child.end
                    if child.refused:
                        refused = refused or "holds a refused piece"
                    elif closer == "`" and "`" in text[child.start : child.end]:
                        refused = refused or "a nested piece holds a backtick"  # a shell ends the backticks there
                elif isinstance(child, str):
                    return f"holds an opening that is refused ({child})"
                elif char == "$" and not quoted and text.startswith("$'", position):
                    close = _ansi_quote_end(text, position + 2, limit)
                    if close is None:
                        return unclosed
                    position = close
                else:
                    position += 1
            elif char == '"':
                quoted = not quoted
                position += 1
            elif char == "'":
                close = text.find("'", position + 1, limit)
                if close < 0:
                    return unclosed
                position = close + 1
            else:  # a bracket: only the closer's own kind nests
                depth += char == {")": "(", "}": "{"}[closer] and not quoted
                position += 1


def _outside_subset(text: str, start: int, end: int, opening: str) -> str:
    """Why a closed piece's text is outside the readable subset, or "" when it is inside."""

    if match := OUTSIDE_SUBSET.search(text, start, end):
        return f"holds {match.group(0)!r}"
    if opening == "${" and "'" in text[start:end]:
        return "a single quote inside ${...}"
    return ""


def _ansi_quote_end(text: str, position: int, limit: int) -> int | None:
    """The position after the quote that closes ``$'…'`` (a backslash escapes the next character)."""

    while position < limit:
        if text[position] == "\\":
            position += 2
        elif text[position] == "'":
            return position + 1
        else:
            position += 1
    return None


def _pieces_at_level(pieces: list[Piece], level: int, empty_quotes: bool) -> tuple[list[Piece], list[Piece]]:
    """The pieces ``level + 1`` deep that are taken as empty, and the substitutions above them whose delimiters
    go at that level. An escaped ``$'…'`` quote is taken as empty only with ``empty_quotes``; otherwise its
    escapes are read."""

    frontier, opened = pieces, []
    for _ in range(level):
        containers = [piece for piece in frontier if piece.opening]
        opened += containers
        frontier = [child for piece in containers for child in piece.children]
    return [piece for piece in frontier if empty_quotes or not piece.escaped], opened


def joined_view(text: str, pieces: list[Piece] | None = None, level: int = 0, empty_quotes: bool = False) -> JoinedView:
    r"""Undo line continuations, escapes, quote removal and run-time pieces, as a shell, a YAML or TOML
    reader or a template engine would, so that a name split by them shows.

    Level 0 takes each outermost run-time piece as empty. Level n (n >= 1) also opens the substitutions
    n deep or less: their delimiters go and their bodies stay, while the pieces n + 1 deep are taken as
    empty, so a name split inside a substitution body, at any depth, shows. Without ``pieces`` every
    piece stays as written, so a name hidden inside one (``$(cat $'scr\u0069pts/x.py')``) shows instead.
    Quotes glued to an emptied piece go with it (``scr"$(echo a b)"ipts``). With ``empty_quotes`` an escaped
    ``$'…'`` quote is taken as empty like any run-time piece; otherwise its escapes are read.
    """

    events = [(m.start(), m.end(), m.group(0)) for m in HIDING.finditer(text)]
    quoting = text
    if pieces is not None:
        emptied, opened = _pieces_at_level(pieces, level, empty_quotes)
        events += [(piece.start, piece.end, "") for piece in emptied]
        for piece in opened:
            events += [(piece.start, piece.start + piece.opening, ""), (piece.end - piece.closing, piece.end, "")]
        if emptied:  # an emptied piece is one glued character to the quotes around it
            chars = list(text)
            for piece in emptied:
                chars[piece.start : piece.end] = "x" * (piece.end - piece.start)
            quoting = "".join(chars)
    for match in QUOTED_PIECE.finditer(quoting):
        events += [(match.start(), match.start() + 1, ""), (match.end() - 1, match.end(), "")]  # the two quotes
    parts: list[str] = []
    segments: list[tuple[int, int, int, bool]] = []
    view = position = 0
    for start, end, token in sorted(events, key=lambda event: (event[0], -event[1])):  # a longer span covers
        if start < position:
            continue  # inside a piece already undone
        if start > position:
            segments.append((view, position, start - position, True))
            parts.append(text[position:start])
            view += start - position
        replacement = _unescape_one(token) if token and ESCAPE.fullmatch(token) else ""
        segments.append((view, start, len(replacement), False))
        parts.append(replacement)
        view += len(replacement)
        position = end
    segments.append((view, position, len(text) - position, True))
    parts.append(text[position:])
    return JoinedView("".join(parts), segments)


def joined_views(text: str, pieces: list[Piece] | None = None) -> Iterator[JoinedView]:
    """Every view ``hidden_references`` reads: each level that takes some piece as empty, with escaped
    ``$'…'`` quotes read and, when the text has one, taken as empty; then the pieces kept.

    A refused piece that closes is taken here like a read one, at the end the scan found; that can only add
    a report. A refused opening is read as a wildcard by ``refused_glue``, never as text."""

    pieces = run_time_pieces(text) if pieces is None else pieces
    for empty_quotes in (False, True) if _has_escaped_quote(pieces) else (False,):
        level = 0
        while level == 0 or _pieces_at_level(pieces, level, empty_quotes)[0]:
            yield joined_view(text, pieces, level, empty_quotes)
            level += 1
    yield joined_view(text)


def _has_escaped_quote(pieces: Sequence[Piece]) -> bool:
    return any(piece.escaped or _has_escaped_quote(piece.children) for piece in pieces)


def hidden_references(
    ownership: OwnershipMap,
    rel: str,
    text: str,
    view: JoinedView,
    seen_starts: set[int],
    report: Report,
    seen: set[int] | None = None,
) -> None:
    """A name that only shows once escapes, continuations, quotes or run-time pieces are undone is reported.

    Such a name is never rewritten.
    """

    seen = set() if seen is None else seen  # lines already reported
    for match in rp.word_matches(view.text, ignore_case=True):
        if view.verbatim(match.start(), match.end()) and view.source_offset(match.start()) in seen_starts:
            continue  # an ordinary occurrence; scan_text decides it
        line = line_number(text, view.source_offset(match.start()))
        if line in seen:
            continue
        tail = view.text[match.start() : match.start() + 200].split(None, 1)[0]
        mentions = [ref for ref in rp.text_references(ownership, tail.lower()) if ref.target != PRODUCT]
        if mentions:
            seen.add(line)
            report.unresolved.append(
                Finding(
                    rel,
                    line,
                    "hidden_reference",
                    ", ".join(ref.text for ref in mentions),
                    detail="spelled across escapes, quotes, line continuations or run-time pieces; rename it by hand",
                    target=rp.worst_target(mentions),
                )
            )


@dataclass(frozen=True)
class Wildcard:
    """A place in the glue view whose text a shell computes: a refused piece, a glob or a brace expansion."""

    view: int  # its position in the glue view
    closer: str  # the character after which it may end; "" when it ends right where it starts (``*``, ``?``)
    kind: str  # the finding kind: refused_piece or glob_split
    detail: str


def glue_view(
    text: str, scan: PieceScan, globs: Sequence[tuple[int, int]] = (), level: int = 0
) -> tuple[JoinedView, list[Wildcard], list[tuple[int, str]]]:
    """The text as a shell joins it around the parts it computes: (view, wildcards, ends).

    Every refused opening becomes ``WILDCARD``, and so does each glob or brace expansion in ``globs`` (its
    whole text); a refused piece's body stays, read the same way. A read substitution ``level`` or fewer
    deep is opened (its delimiters go, its body stays), as in ``joined_view``; every other read piece is
    taken as empty. An escaped ``$'…'`` quote is read, every quote character goes, and line continuations,
    escapes and backslashes are undone. ``ends`` are the view positions right after a read piece that a
    closer ends (with that closer), where a refused piece of the same kind may also end, since its own end
    is unknown.
    """

    # (start, rank, end, token, wildcard): at one start a piece goes before a glob character inside it.
    events: list[tuple[int, int, int, str, tuple[str, str, str] | None]] = [
        (m.start(), 1, m.end(), m.group(0), None) for m in HIDING.finditer(text)
    ]
    events += [(m.start(), 1, m.end(), "", None) for m in re.finditer(r"['\"]", text)]
    for start, end in globs:
        detail = f"glued to a glob or brace expansion ({text[start:end][:40]!r}) that may spell it; rename it by hand"
        events.append((start, 1, end, WILDCARD, ("", "glob_split", detail)))
    cut_closers: dict[int, str] = {}  # source end of a read piece -> its closer

    def refused(start: int, opening: str, reason: str) -> None:
        detail = f"glued to a run-time piece the scanner refuses to read ({reason}); rename it by hand"
        events.append((start, 0, start + len(opening), WILDCARD, (OPENINGS[opening], "refused_piece", detail)))

    stack = [(piece, 0) for piece in scan.glue]  # with the read substitutions around it
    while stack:
        piece, depth = stack.pop()
        if piece.refused:  # what it holds is in ``scan.glue`` on its own
            refused(piece.start, text[piece.start : piece.start + piece.opening], piece.refused)
        elif piece.escaped:
            continue  # an escaped ``$'…'`` quote is read: its ``$``, quotes and escapes go as everywhere else
        elif piece.opening and depth < level:
            events.append((piece.start, 0, piece.start + piece.opening, "", None))
            events.append((piece.end - piece.closing, 0, piece.end, "", None))
            stack.extend((child, depth + 1) for child in piece.children)
        else:
            events.append((piece.start, 0, piece.end, "", None))
            if piece.closing:
                cut_closers[piece.end] = text[piece.end - 1]
    for refusal in scan.unclosed:
        refused(refusal.start, text[refusal.start : refusal.start + refusal.opening], refusal.reason)
    parts: list[str] = []
    segments: list[tuple[int, int, int, bool]] = []
    wildcards: list[Wildcard] = []
    ends: list[tuple[int, str]] = []
    view = position = 0
    for start, _rank, end, token, wildcard in sorted(events, key=lambda event: event[:3]):
        if start < position:
            continue  # inside a piece already taken as empty
        if start > position:
            segments.append((view, position, start - position, True))
            parts.append(text[position:start])
            view += start - position
        if wildcard is not None:
            wildcards.append(Wildcard(view, *wildcard))
            replacement = WILDCARD
        else:
            replacement = _unescape_one(token) if token and ESCAPE.fullmatch(token) else ""
        segments.append((view, start, len(replacement), False))
        parts.append(replacement)
        view += len(replacement)
        if end in cut_closers:
            ends.append((view, cut_closers[end]))
        position = end
    segments.append((view, position, len(text) - position, True))
    parts.append(text[position:])
    return JoinedView("".join(parts), segments), wildcards, ends


def refused_glue(
    rel: str,
    text: str,
    report: Report,
    scan: PieceScan | None = None,
    span: tuple[int, int] | None = None,
    shell: bool = False,
    seen: set[int] | None = None,
) -> None:
    """Report every word where a part a shell computes may join letters of ``scripts`` into a name.

    Each refused piece is a wildcard of unknown text: it starts at its opening and may end after any later
    closer of its kind. In ``shell`` text, each glob or brace expansion is a wildcard that ends with its text. A
    letter run is reported when it is glued in front of a wildcard and, with the wildcard taken as the rest
    of the name, starts the word ``scripts`` (``rp.word_matches``); when it starts where a wildcard may end
    and is a suffix of ``scripts``; or when it lies between the two and is a slice of ``scripts``. Such a
    word is never rewritten. ``span`` limits the scan to one shell region of the text (a Markdown code span
    or fence); ``seen`` holds the lines already reported, shared across the regions of one file.
    """

    offset, end = span if span is not None else (0, len(text))
    region = text[offset:end]
    scan = scan_pieces(region) if scan is None else scan
    refusals = scan.refusals()
    globs: list[tuple[int, int]] = []
    if shell:
        # The lexer's quoting is trusted only before the first construct it may misread.
        untrusted = min([len(region), *(refusal.start for refusal in refusals[:1]), *_find(region, "$'")])
        globs = [
            (start - offset, stop - offset) for start, stop in glob_spans(text, [(offset, end)], offset + untrusted)
        ]
    if not globs and not refusals:
        return
    seen = set() if seen is None else seen  # lines already reported
    for level in range(_read_depth(scan.glue) + 1):
        joined, wildcards, cut_ends = glue_view(region, scan, globs, level)
        if wildcards:
            _report_glue(rel, text, offset, region, joined, wildcards, cut_ends, report, seen)


def _read_depth(pieces: Sequence[Piece]) -> int:
    """How deep read substitutions nest, through refused ones."""

    depth, stack = 0, [(piece, 0) for piece in pieces]
    while stack:
        piece, outer = stack.pop()
        inner = outer + bool(piece.opening and not piece.refused)
        depth = max(depth, inner)
        stack.extend((child, inner) for child in piece.children)
    return depth


def _report_glue(
    rel: str,
    text: str,
    offset: int,
    region: str,
    joined: JoinedView,
    wildcards: list[Wildcard],
    cut_ends: list[tuple[int, str]],
    report: Report,
    seen: set[int],
) -> None:
    view = joined.text
    first: dict[str, int] = {}  # the first wildcard each closer can end
    for wildcard in wildcards:
        first.setdefault(wildcard.closer, wildcard.view)
    at = {wildcard.view: wildcard for wildcard in wildcards}  # by position: an escape such as ``\0`` reads as NUL
    positions = [wildcard.view for wildcard in wildcards]
    ends = sorted(
        {p + 1 for p, char in enumerate(view) if char in first and first[char] < p}
        | {p for p, closer in cut_ends if closer in first and first[closer] < p}
        | {wildcard.view + 1 for wildcard in wildcards if not wildcard.closer}
    )
    for run in LETTERS.finditer(view):
        a, b = run.span()
        letters = run.group(0).lower()
        glued_front = b in at
        fragment = ""
        if glued_front:
            for k in range(min(len(letters), len(WORD)), 0, -1):
                if letters.endswith(WORD[:k]) and _starts_word(region, joined.source_offset(b - k)):
                    fragment = letters[-k:]
                    break
        for k in ends[bisect.bisect_left(ends, a) : bisect.bisect_left(ends, b)]:
            piece = letters[k - a :]
            if not fragment and ((piece in WORD) if glued_front else WORD.endswith(piece)):
                fragment = piece
        if not fragment:
            continue
        line = line_number(text, offset + joined.source_offset(a))
        if line in seen:
            continue
        seen.add(line)
        # The wildcard it is glued to: the one right after it, or else the last one before it.
        wildcard = at[b] if glued_front else wildcards[max(0, bisect.bisect_left(positions, a) - 1)]
        report.unresolved.append(Finding(rel, line, wildcard.kind, fragment, detail=wildcard.detail, target="unknown"))


def _find(text: str, needle: str) -> list[int]:
    index = text.find(needle)
    return [] if index < 0 else [index]


def glob_spans(text: str, regions: Sequence[tuple[int, int]], untrusted: int | None = None) -> list[tuple[int, int]]:
    """Every glob (``*``, ``?``, ``[...]``) and brace expansion (``{a,b}``, ``{a..b}``) a shell may expand in
    ``regions``: unescaped and, before ``untrusted``, unquoted and outside comments and heredoc bodies as the
    shell lexer reads them. From ``untrusted`` on the lexer may have misread the text, so every one counts."""

    candidates: list[tuple[int, int]] = []
    for start, end in regions:
        for match in GLOB_START.finditer(text, start, end):
            i = match.start()
            backslashes = i - start - len(text[start:i].rstrip("\\"))
            if backslashes % 2 or (match.group(0) in "*?{" and i > start and text[i - 1] == "$"):
                continue  # escaped, or the ``$*``, ``$?`` or ``${`` of a run-time piece
            close = i + 1 if match.group(0) in "*?" else _bracket_end(text, i, end, match.group(0))
            if close is not None:
                candidates.append((i, close))
    if not candidates:
        return []
    contexts = ShellLexer(text, regions).contexts([start for start, _ in candidates])
    return [
        (start, close)
        for start, close in candidates
        if (untrusted is not None and start >= untrusted)
        or (
            (context := contexts.get(start)) is not None
            and context.frame in ("top", "$(", "`")
            and not context.comment
            and not context.heredoc
        )
    ]


def _bracket_end(text: str, start: int, end: int, opening: str) -> int | None:
    """Where a ``[...]`` bracket expression or a ``{a,b}`` brace expansion ends, or None when it is neither."""

    if opening == "[":
        match = re.compile(r"\[[!^]?\]?[^\]\s/]*\]").match(text, start, end)
        return match.end() if match else None
    depth, expands, i = 0, False, start
    while i < end and not text[i].isspace():
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i + 1 if expands else None
        elif depth == 1 and (char == "," or text.startswith("..", i)):
            expands = True
        i += 1
    return None


def _starts_word(text: str, position: int) -> bool:
    """Whether ``scripts`` starting at ``position`` would start a word, as ``rp.word_matches`` reads it."""

    probe = text[max(0, position - 16) : position] + WORD
    return any(match.end() == len(probe) for match in rp.word_matches(probe, ignore_case=True))


def case_variants(ownership: OwnershipMap, rel: str, text: str, kind: str, report: Report) -> None:
    """``Scripts/x.py`` names scripts/x.py on a case-insensitive file system: reported, never rewritten."""

    prose = markdown_regions(text)[0] if kind == MARKDOWN else None
    for match in rp.CASE_VARIANT.finditer(text):
        tail = TOKEN_CHARS.match(text, match.end()).group(0)  # type: ignore[union-attr]
        target = rp.path_target(ownership, OLD_ROOT + tail)
        if target == PRODUCT:
            continue
        finding = Finding(
            rel,
            line_number(text, match.start()),
            "case_variant" if prose is None or _in_regions(prose, match.start()) else "prose_mention",
            match.group(0) + tail,
            detail="the scripts root in another case",
            target=target,
        )
        (report.unresolved if finding.kind == "case_variant" else report.inventory).append(finding)


def scan_text(ownership: OwnershipMap, rel: str, text: str, kind: str, report: Report) -> list[Edit]:
    """Rewrite or report every ``scripts`` word in a non-Python text."""

    pieces = scan_pieces(text)  # the choke point: every opening is read or refused here
    views = joined_views(text, pieces.pieces)
    view = next(views)  # level 0: every outermost piece taken as empty
    found = list(occurrences(text))
    covered = {o.start for o in found}
    covered |= {m.start() for m in rp.word_matches(text, ignore_case=True)}  # seen raw (case variants too)
    reported: set[int] = set()
    for joined in (view, *views):
        hidden_references(ownership, rel, text, joined, covered, report, reported)
    case_variants(ownership, rel, text, kind, report)
    scan = FileScan(ownership, rel, text, kind)
    if kind == MARKDOWN:
        # Markdown is shell only in its code spans and shell fences; its backticks are no substitutions.
        scan.code_regions, scan.shell_regions = markdown_regions(text)
        glued_lines: set[int] = set()
        for region in scan.shell_regions:
            refused_glue(rel, text, report, span=region, shell=True, seen=glued_lines)
    else:
        refused_glue(rel, text, report, scan=pieces, shell=kind in (SHELL, TEXT))
    if not found:
        return []
    if kind in (SHELL, TEXT):
        scan.shell_regions = [(0, len(text))]
    elif kind == JSON:
        scan.json_strings = json_strings(text)
    if scan.shell_regions:
        scan.contexts = ShellLexer(text, scan.shell_regions).contexts([o.start for o in found])
    scan.comment_regions = extra_comment_regions(rel, text)
    digest_bound = kind in (JSON, TEXT) and bool(DIGEST_FIELD.search(text) or DIGEST_FIELD.search(view.text))
    edits: list[Edit] = []
    for occ in found:
        line = line_number(text, occ.start)
        if (
            kind == MARKDOWN
            and _in_regions(scan.code_regions, occ.start)
            and not _in_regions(scan.shell_regions, occ.start)
        ):
            target = name_target(ownership, occ.name)[1]
            if not (target == PRODUCT and _ends_cleanly(text, occ.end)):
                report.unresolved.append(
                    Finding(
                        rel,
                        line,
                        "non_shell_fence",
                        occ.name,
                        detail="a fenced block in another language",
                        target=target,
                    )
                )
            continue
        verdict = judge(scan, occ)
        if verdict.action == "rewrite" and digest_bound:
            verdict = Verdict(
                "unresolved", "digest_bound_file", "the file records digests; regenerate it after the move", MACHINERY
            )
        shown = text[occ.prefix_start : occ.end]
        if verdict.action == "rewrite":
            after = NEW_ROOT + occ.name[len(OLD_ROOT) :]
            edits.append(Edit(occ.start, occ.start + len(OLD_ROOT), NEW_ROOT))
            report.rewrites.append(Finding(rel, line, verdict.kind, shown, text[occ.prefix_start : occ.start] + after))
            if verdict.kind == "resource_path" and _runs_file(text, occ):
                report.inventory.append(
                    Finding(rel, line, "direct_script_invocation", occ.name, after, "runs a machinery file by path")
                )
        elif verdict.action in ("unresolved", "inventory"):
            finding = Finding(rel, line, verdict.kind, shown, detail=verdict.detail, target=verdict.target)
            (report.unresolved if verdict.action == "unresolved" else report.inventory).append(finding)
    return edits


def _runs_file(text: str, occ: Occurrence) -> bool:
    if not occ.name.endswith((".py", ".sh")):
        return False
    start = occ.prefix_start
    if start > 0 and text[start - 1] in "'\"":
        start -= 1
    line_start = text.rfind("\n", 0, start) + 1
    return bool(INTERPRETER_BEFORE.search(text[line_start:start]))


def apply_edits(text: str, edits: list[Edit]) -> str:
    for edit in sorted(edits, key=lambda e: e.start, reverse=True):
        text = text[: edit.start] + edit.replacement + text[edit.end :]
    return text


def scan_file(ownership: OwnershipMap, rel: str, data: bytes, text: str, report: Report) -> str | None:
    """Report one file's references; return its rewritten text, or None when nothing changes."""

    kind = classify(rel, data[:256])
    if kind == PYTHON and rel.endswith(".py"):
        return None  # rename_python.py owns Python files
    edits = scan_text(ownership, rel, text, kind, report)
    if not edits:
        return None
    new_text = apply_edits(text, edits)
    # Post-condition: scanning the rewritten text finds nothing more to rewrite.
    second = Report("rename_nonpython", "check", "")
    scan_text(ownership, rel, new_text, kind, second)
    report.unresolved.extend(
        Finding(rel, f.line, "rewrite_not_applied", f.before, detail="still pending after the rewrite")
        for f in second.rewrites
    )
    return new_text


def run(ownership: OwnershipMap, root: Path, targets: Sequence[str], apply: bool) -> Report:
    report = Report("rename_nonpython", "apply" if apply else "check", ownership.sha256)
    skipped_binary = skipped_large = skipped_structured = 0
    for path, rel in rp.iter_files(root, targets, None):
        if ownership.original_path(rel) in rs.SCHEMAS:
            skipped_structured += 1
            continue
        size = path.stat().st_size
        if size > MAX_BYTES:
            # Too large to scan; any text may hold or hide the name, so every such file is listed.
            detail = f"{size} bytes, over the {MAX_BYTES}-byte scan limit; inspect by hand"
            report.unresolved.append(Finding(rel, 1, "skipped_large_file", rel, detail=detail, target="unknown"))
            skipped_large += 1
            continue
        data = path.read_bytes()  # every file is read: a split or escaped name has no fixed bytes
        try:
            if b"\0" in data:
                raise UnicodeDecodeError("utf-8", data, 0, 1, "binary")
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            kind, detail = binary_verdict(data)
            if kind:
                skipped_binary += 1
                report.unresolved.append(Finding(rel, 1, kind, rel, detail=detail, target="unknown"))
            continue
        report.files_scanned += 1
        file_report = Report(report.tool, report.mode, report.map_sha256)
        try:
            new_text = scan_file(ownership, rel, data, text, file_report)
        except Exception as exc:  # one unexpected input must not stop the run or half-write a file
            detail = f"the scan failed ({type(exc).__name__}: {exc}); file left unchanged"
            report.unresolved.append(Finding(rel, 1, "tool_error", rel, detail=detail))
            continue
        report.rewrites.extend(file_report.rewrites)
        report.unresolved.extend(file_report.unresolved)
        report.inventory.extend(file_report.inventory)
        if new_text is None:
            continue
        report.files_changed.append(rel)
        if apply:
            rp.write_atomically(path, new_text.encode("utf-8"))
    report.unresolved.extend(symlink_findings(root, targets))
    report.notes.append(f"binary or non-UTF-8 files that may name scripts (reported): {skipped_binary}")
    report.notes.append(f"skipped files over {MAX_BYTES} bytes: {skipped_large}")
    report.notes.append(f"skipped files that rename_structured.py owns: {skipped_structured}")
    return report


def _archive_names_scripts(data: bytes) -> bool | None:
    """Whether a gzip, bzip2, xz or zip file's contents name scripts; None when it is none of these.

    Contents are read in chunks, at most ``MAX_UNPACKED`` bytes in all, and the search stops at the
    first match. An archive that cannot be read, or holds more than that, counts as naming it.
    """

    def search(stream: object, budget: list[int]) -> bool:
        tail = b""
        while budget[0] > 0:
            chunk = stream.read(min(1 << 20, budget[0]))  # type: ignore[attr-defined]
            if not chunk:
                return False
            budget[0] -= len(chunk)
            if ANY_BYTES_CASE.search(tail + chunk):
                return True
            tail = chunk[-16:]
        return True  # too large to read in full

    budget = [MAX_UNPACKED]
    try:
        if data.startswith(b"\x1f\x8b"):
            return search(gzip.GzipFile(fileobj=io.BytesIO(data)), budget)
        if data.startswith(b"BZh"):
            return search(bz2.BZ2File(io.BytesIO(data)), budget)
        if data.startswith(b"\xfd7zXZ\x00"):
            return search(lzma.LZMAFile(io.BytesIO(data)), budget)
        if data.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for info in archive.infolist():
                    if ANY_BYTES_CASE.search(info.filename.encode("utf-8", "replace")):
                        return True
                    with archive.open(info) as member:
                        if search(member, budget):
                            return True
                return False
    except Exception:  # a damaged archive is listed whole
        return True
    return None


def binary_verdict(data: bytes) -> tuple[str, str]:
    """(kind, detail) for a file that is not UTF-8 text, or ("", "") when it cannot name scripts.

    Text escapes mean nothing in a binary file; the name itself does, also inside a compressed archive.
    """

    archive = _archive_names_scripts(data)
    if archive is not None:
        if archive:
            return "compressed_file", "a compressed archive whose contents may name scripts; inspect it by hand"
        return "", ""
    if ANY_BYTES_CASE.search(data):
        return "binary_file", "binary or not UTF-8; no rewrite rule; inspect it by hand"
    return "", ""


def symlink_findings(root: Path, targets: Sequence[str]) -> list[Finding]:
    """A symlink whose target names scripts breaks when machinery moves: reported, never changed."""

    root = root.resolve()
    wanted = [Path(t).as_posix().strip("/") for t in targets]
    findings: list[Finding] = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in rp.SKIPPED_DIRS)
        for name in sorted([*dirnames, *filenames]):
            path = Path(directory) / name
            if not path.is_symlink():
                continue
            rel = path.relative_to(root).as_posix()
            if wanted and not any(rel == w or rel.startswith(w + "/") for w in wanted):
                continue
            target = os.readlink(path)
            if ANY_CASE.search(target) or ANY_CASE.search(rel):
                detail = f"a symlink to {target}; links are not followed or changed"
                findings.append(Finding(rel, 1, "symlink_target", rel, detail=detail, target="unknown"))
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rename_nonpython.py",
        description=(
            "Rename `scripts.<machinery module>` names and `scripts/<machinery path>` paths to lu_machinery in shell,\n"
            "hooks, systemd and launchd units, configuration files and Markdown code, where the name is a complete\n"
            "plain token, and report every other scripts name or path. Use it on a disposable clone during the\n"
            "machinery move, after rename_python.py; never on the live product tree."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python packaging/machinery-move/rename_nonpython.py --map ownership.json --root "$CLONE" --check
  python packaging/machinery-move/rename_nonpython.py --map ownership.json --root "$CLONE" --apply --report np.json
  python packaging/machinery-move/rename_nonpython.py --map ownership.json --check .githooks packaging/systemd

Rules:
  A complete plain token is a whole word, or a whole word inside one pair of quotes, with a blank, the line
  start or `=` before it (or before its opening quote) and a blank, the line end or one of ; & | ) after it
  (or after its closing quote). It may start with one root prefix: ./, ../, $NAME/, ${NAME}/ or @NAME@/. JSON
  strings and plist <string> elements count when the name is their whole text. Such a token is renamed when
  the map says it names a machinery file, directory or module (`-m` also checks the package's __main__).
  Reported instead: names in heredoc bodies, in longer quoted text, inside ${...}, $(( )) or backticks, with
  anything glued to them, in fences of other languages, in files that record digests, in unsupported file
  types, directory changes into scripts/, the scripts/ root itself, globs, and unknown or mixed-owner names.
  A $(...), ${...} or backtick piece with a comment, case clause, heredoc, ((, $[, ;; or a line continuation in
  it, or longer than 64 KiB or nested over 64 deep, is refused: letters glued to it that could spell scripts
  are reported as refused_piece (README: "Pieces the scanner refuses"), and letters glued to an unquoted
  glob or brace expansion (scr*ipts, scr{,}ipts) as glob_split.
  Comments and Markdown prose are never changed; machinery mentions there go to the inventory.
  Python files (*.py) belong to rename_python.py; files rename_structured.py knows belong to it.

Outputs:
  stdout: a summary line, rewrite/inventory/unresolved counts by kind, then every unresolved reference as
  path:line: kind: text (detail). --apply rewrites files in place (atomic replace, mode kept).
  --report writes the same data as JSON with every rewrite and inventory entry.

Exit codes:
  0  no unresolved references (with --check, rewrites may still be pending: see the summary)
  1  at least one unresolved reference; --apply still wrote every resolved rewrite
  2  usage error, or an unreadable or malformed ownership map

Related:
  packaging/machinery-move/README.md, rename_python.py, rename_structured.py, contract v3 step 6 (items 3-4).
""",
    )
    rp.add_common_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ownership = OwnershipMap.from_file(args.map)
        report = run(ownership, args.root, args.paths, apply=args.apply)
    except rp.MapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return rp.EXIT_USAGE
    return rp.emit(report, args.report)


if __name__ == "__main__":
    sys.exit(main())
