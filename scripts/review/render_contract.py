"""What a rendered review prompt was rendered against, and whether a review attempt still matches it (#9163).

A review seat's sources MCP server launches from the primary checkout, while its prompt may be rendered in any
checkout. The prompt tells the seat what the server prints, so the prompt's templates and the server code that
answers the seat must come from the same code. At render time ``render_record`` records, beside the prompt, the
checkout that rendered it, the templates that render actually loaded and that checkout's server-code digest. At
dispatch ``check_render_contract`` compares that record with the server code the attempt would run and with the
render checkout's templates as they are now, and refuses on any difference.

The server-code digest covers the code the server runs, not a directory listing: the server entry plus every
repository module it imports, found by a static walk of its ``import`` statements resolved the way the server's
own ``sys.path`` resolves them (``scripts/``, then the repository root, then the server's directory). Files are
read from disk whatever git thinks of them (ignored, untracked or dirty), and a symlink contributes its target's
bytes. Imports made dynamically (``importlib``) are not seen; the server makes none.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: The sources server a review seat calls, relative to a checkout.
SERVER_ENTRY = ".mcp/servers/sources/server.py"
#: Key of the render record inside the prompt's ``<prompt>.files_read.json`` sidecar.
RENDER_RECORD_KEY = "render_contract"
RENDER_RECORD_VERSION = 1
_SERVER_DIGEST_VERSION = b"lu-review-server-code-digest-v1"
_TEMPLATE_DIGEST_VERSION = b"lu-review-template-digest-v1"
_MISSING = "missing"
_FIX = "pull the primary checkout to origin/main, then re-render and retry"
_RERENDER = (
    "re-render the prompt with `python -m scripts.review.prompts.render <manifest> --output <prompt> "
    "--review-id <id> --attempt-id <id>`, then retry with --prompt-file <prompt>"
)


class ReviewContractError(ValueError):
    """A review attempt's prompt cannot be tied to the code it was rendered against, or that code differs (#9163)."""


@dataclass(frozen=True)
class _Module:
    files: tuple[Path, ...]  # the file this module executes: an ``__init__.py``, a ``.py`` module, or none
    search: tuple[Path, ...]  # its submodule search path (a package's ``__path__``); empty for a plain module


class _ModuleFinder:
    """Resolves dotted names to repository files the way a path-based import would, over fixed roots."""

    def __init__(self, roots: Iterable[Path]):
        self.roots = tuple(roots)
        self._cache: dict[str, _Module | None] = {}

    def find(self, name: str) -> _Module | None:
        if name in self._cache:
            return self._cache[name]
        parent, _, leaf = name.rpartition(".")
        found: _Module | None = None
        if parent:
            owner = self.find(parent)
            if owner is not None and owner.search:
                found = self._scan(owner.search, leaf)
        elif name not in sys.builtin_module_names:
            found = self._scan(self.roots, leaf)
        self._cache[name] = found
        return found

    @staticmethod
    def _scan(directories: Iterable[Path], leaf: str) -> _Module | None:
        portions: list[Path] = []
        for directory in directories:
            package = directory / leaf
            if (package / "__init__.py").is_file():
                return _Module((package / "__init__.py",), (package,))
            if (directory / f"{leaf}.py").is_file():
                return _Module((directory / f"{leaf}.py",), ())
            if package.is_dir():
                portions.append(package)
        return _Module((), tuple(portions)) if portions else None


def _imported_names(tree: ast.AST, package: str) -> list[str]:
    """Every module name an ``import``/``from … import`` in ``tree`` may load, with its parent packages."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                anchor = package.split(".") if package else []
                if not package or node.level - 1 >= len(anchor):
                    continue  # a relative import that could not run
                anchor = anchor[: len(anchor) - (node.level - 1)]
                base = ".".join([*anchor, *([node.module] if node.module else [])])
            if not base:
                continue
            # ``from pkg import name`` loads ``pkg.name`` when that is a submodule.
            targets = [base, *(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")]
        else:
            continue
        for target in targets:
            parts = target.split(".")
            names.extend(".".join(parts[: index + 1]) for index in range(len(parts)))
    return names


#: Import names by (content sha256, package): content-addressed, so a changed file can never hit a stale entry.
_IMPORTS_CACHE: dict[tuple[str, str], tuple[str, ...]] = {}


def _imports_of(sha256: str, package: str, data: bytes) -> tuple[str, ...]:
    key = (sha256, package)
    if key not in _IMPORTS_CACHE:
        try:
            tree = ast.parse(data)
        except (SyntaxError, ValueError):
            tree = None  # still hashed; a module that does not parse imports nothing
        _IMPORTS_CACHE[key] = tuple(dict.fromkeys(_imported_names(tree, package))) if tree else ()
    return _IMPORTS_CACHE[key]


def _logical(path: Path, checkout: Path) -> str:
    return path.relative_to(checkout).as_posix() if path.is_relative_to(checkout) else path.as_posix()


def server_code_files(checkout: Path) -> dict[str, str]:
    """sha256 of every file the sources server of ``checkout`` executes, by path (relative when inside it).

    The entry and each repository module it imports, recursively; a symlink is followed and its target's bytes
    hashed. Modules found outside the roots (the standard library, installed packages) are not the checkout's.
    """
    root = Path(checkout).resolve()
    entry = root / SERVER_ENTRY
    if not entry.is_file():
        raise ReviewContractError(f"review attempt refused: no sources server at {entry} (#9163)")
    finder = _ModuleFinder((root / "scripts", root, entry.resolve().parent))
    hashes: dict[str, str] = {}
    pending: list[tuple[Path, str]] = [(entry, "")]
    while pending:
        path, package = pending.pop()
        key = _logical(path, root)
        if key in hashes:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ReviewContractError(f"review attempt refused: cannot read {path}: {exc} (#9163)") from exc
        hashes[key] = hashlib.sha256(data).hexdigest()
        for name in _imports_of(hashes[key], package, data):
            module = finder.find(name)
            if module is None:
                continue
            for file in module.files:
                pending.append((file, name if file.name == "__init__.py" else name.rpartition(".")[0]))
    return dict(sorted(hashes.items()))


def server_code_digest(checkout: Path) -> str:
    """One deterministic digest of ``server_code_files``: what decides the sources server's behaviour."""
    hasher = hashlib.sha256(_SERVER_DIGEST_VERSION + b"\0")
    for name, sha in server_code_files(checkout).items():
        hasher.update(name.encode("utf-8", errors="surrogateescape") + b"\0" + sha.encode("ascii") + b"\n")
    return f"sha256:{hasher.hexdigest()}"


def template_digest(templates: Mapping[str, str]) -> str:
    """One digest of the templates a render loaded: each name with the sha256 of its bytes (or ``missing``)."""
    hasher = hashlib.sha256(_TEMPLATE_DIGEST_VERSION + b"\0")
    for name in sorted(templates):
        hasher.update(name.encode("utf-8") + b"\0" + templates[name].encode("ascii") + b"\n")
    return f"sha256:{hasher.hexdigest()}"


def current_templates(prompts_dir: Path, names: Iterable[str]) -> dict[str, str]:
    """The sha256 of each named template in ``prompts_dir`` as it is on disk now; ``missing`` when it is gone."""
    current: dict[str, str] = {}
    for name in names:
        path = Path(prompts_dir) / name
        try:
            current[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            current[name] = _MISSING
    return current


def render_record(
    render_checkout: Path, prompts_dir: Path, loaded_templates: Mapping[str, str], prompt_sha256: str
) -> dict[str, Any]:
    """The record a render writes beside its prompt: where it rendered, what it loaded, the server it matched."""
    checkout = Path(render_checkout).resolve()
    return {
        "version": RENDER_RECORD_VERSION,
        "render_checkout": str(checkout),
        "prompts_dir": str(Path(prompts_dir).resolve()),
        "templates": dict(sorted(loaded_templates.items())),
        "template_digest": template_digest(loaded_templates),
        "server_digest": server_code_digest(checkout),
        "prompt_sha256": prompt_sha256,
    }


def render_record_path(prompt_file: Path) -> Path:
    return prompt_file.with_name(f"{prompt_file.name}.files_read.json")


def _read_render_record(prompt_file: Path | None) -> dict[str, Any]:
    if prompt_file is None:
        raise ReviewContractError(
            "review attempt refused: review_render_record_missing: a --review-attempt prompt must come from "
            f"--prompt-file, whose render record says what it was rendered against; {_RERENDER} (#9163)"
        )
    sidecar = render_record_path(Path(prompt_file))
    try:
        record = json.loads(sidecar.read_text(encoding="utf-8")).get(RENDER_RECORD_KEY)
    except (OSError, ValueError, AttributeError) as exc:
        raise ReviewContractError(
            f"review attempt refused: review_render_record_missing: cannot read {sidecar}: {exc}; {_RERENDER} (#9163)"
        ) from exc
    fields = ("render_checkout", "prompts_dir", "template_digest", "server_digest", "prompt_sha256")
    if (
        not isinstance(record, dict)
        or record.get("version") != RENDER_RECORD_VERSION
        or not all(isinstance(record.get(field), str) for field in fields)
        or not isinstance(record.get("templates"), dict)
        or not record["templates"]
    ):
        raise ReviewContractError(
            f"review attempt refused: review_render_record_missing: {sidecar} holds no version "
            f"{RENDER_RECORD_VERSION} {RENDER_RECORD_KEY} record; {_RERENDER} (#9163)"
        )
    return record


def check_render_contract(prompt_file: Path | None, prompt_text: str, server_checkout: Path) -> dict[str, Any]:
    """Refuse a review attempt whose prompt was rendered against other code than the attempt would run (#9163).

    ``server_checkout`` is where the attempt's sources server launches. Compares the render record's server
    digest with that checkout's server code now, and its template digest with the render checkout's loaded
    templates now. Returns the record the task stores, naming the digests compared.
    """
    recorded = _read_render_record(prompt_file)
    prompt_sha256 = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    if prompt_sha256 != recorded["prompt_sha256"]:
        raise ReviewContractError(
            "review attempt refused: review_render_record_stale: the prompt file hashes to "
            f"{prompt_sha256}, its render record names {recorded['prompt_sha256']}; {_RERENDER} (#9163)"
        )
    server = Path(server_checkout).resolve()
    templates_now = current_templates(Path(recorded["prompts_dir"]), recorded["templates"])
    contract = {
        "render_checkout": recorded["render_checkout"],
        "server_checkout": str(server),
        "render_server_digest": recorded["server_digest"],
        "server_digest": server_code_digest(server),
        "render_template_digest": recorded["template_digest"],
        "template_digest": template_digest(templates_now),
        "templates": sorted(recorded["templates"]),
        "prompt_sha256": prompt_sha256,
    }
    differing = [
        what
        for what, then, now in (
            ("server code", contract["render_server_digest"], contract["server_digest"]),
            ("templates", contract["render_template_digest"], contract["template_digest"]),
        )
        if then != now
    ]
    if differing:
        raise ReviewContractError(
            "review attempt refused: review_contract_mismatch: the prompt was rendered against different "
            f"{' and '.join(differing)} than this attempt would run\n"
            f"  rendered in: {contract['render_checkout']} server digest {contract['render_server_digest']} "
            f"template digest {contract['render_template_digest']}\n"
            f"  sources server (primary checkout): {contract['server_checkout']} server digest {contract['server_digest']}\n"
            f"  templates now (render checkout): {recorded['prompts_dir']} template digest {contract['template_digest']}\n"
            f"  fix: {_FIX} (#9163)"
        )
    return contract
