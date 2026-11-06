"""Template-slot respelling of mypy baseline messages after the machinery move (C-4761).

The ratchet runs from a copy of ``scripts/lint/mypy_ratchet.py`` placed under a
renamed package directory, so its unresolved file location gives the extracted
layout (design-v1 amendment 1). Real mypy runs on the case files; custom
baselines go through ``load_entries`` (the ``--baseline`` path) and ``compare``.

``fixtures/mypy_ratchet/rename-map.json`` holds every key under ``scripts/``
``agent_runtime``, ``fleet_comms``, ``orchestration``, ``audit``, ``review`` and
``launchers`` (plus ``scripts/__init__.py``) of the portcheck extraction map
with sha256 ``5888bbced5a633535f030bbefbb7e9b71abcad2a15854d7e5ae5027cd0dc2b9e``,
unchanged; module resolution under those packages equals the full map's.
``template-rows-6986c7b1.json`` lists the 39 baseline rows of the two templates
at ``6986c7b16b`` with their spelling under that map.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

from scripts.lint import mypy_ratchet as source_ratchet

_REPO = Path(__file__).resolve().parents[2]
_RATCHET = _REPO / "scripts" / "lint" / "mypy_ratchet.py"
_FIXTURES = Path(__file__).with_name("fixtures") / "mypy_ratchet"
_PKG = "lu_machinery"
_IDENTITY = "agent_runtime.agent_identity"

_CONFIG = '[tool.mypy]\npython_version = "3.12"\n'
_SUPPORT = {
    f"{_PKG}/__init__.py": "",
    f"{_PKG}/agent_runtime/__init__.py": "",
    f"{_PKG}/agent_runtime/agent_identity.py": "KNOWN_SEAT = 1\n",
    f"{_PKG}/orchestration/prompt_contracts.py": "_SafeLoaderBase: type[object] = object\n",
    f"{_PKG}/review/__init__.py": "",
    f"{_PKG}/zz_unknown.py": "Unrelated = 1\n",
    f"{_PKG}/cases/__init__.py": "",
    # The product tree beside the machinery package (a product checkout).
    "scripts/__init__.py": "",
    "scripts/audit/__init__.py": "",
    "scripts/audit/model_families.py": "unrelated_value = 1\n",
}
_TEMPLATES = """\
from lu_machinery.agent_runtime.agent_identity import absent_name
from lu_machinery.agent_runtime.agent_identity import KNOWN_SEET
from lu_machinery.orchestration.prompt_contracts import _SafeLoaderBase
from lu_machinery.review import absent_hook
from lu_machinery.zz_unknown import absent_thing
from scripts.audit.model_families import Family


def take(value: _SafeLoaderBase) -> None: ...
"""
_KEY = f"{_PKG}.{_IDENTITY}"
_DATA = f"""\
from typing import Literal, TypedDict

TD = TypedDict("TD", {{"{_KEY}": int}})
TWO = TypedDict("TWO", {{"{_KEY}": int, "{_KEY}.b": int}})
FIELD = TypedDict("FIELD", {{"{_KEY}:field": int}})
KEPT = TypedDict("KEPT", {{"scripts.{_IDENTITY}:field": int}})

lit: Literal["{_KEY}"] = "other"
missing: TD = {{}}
missing_two: TWO = {{}}
wrong: TD = {{"{_KEY}": "s"}}
td: TD = {{"{_KEY}": 1}}
td["{_KEY}"] = "wrong"
field: FIELD = {{"{_KEY}:field": 1}}
field["{_KEY}:field"] = "wrong"
kept: KEPT = {{"scripts.{_IDENTITY}:field": 1}}
kept["scripts.{_IDENTITY}:field"] = "wrong"
quote: TD = {{"{_KEY}": 1, '{_KEY}"y': 2}}
lkey: TD = {{"{_KEY}": 1, "Literal['{_KEY}": 2}}
comma: TD = {{"{_KEY}": 1, "{_KEY},x": 2}}
pipe: TD = {{"{_KEY}": 1, "{_KEY}|x": 2}}
paren: TD = {{"{_KEY}": 1, "{_KEY})x": 2}}
space: TD = {{"{_KEY}": 1, "{_KEY} x": 2}}
colon: TD = {{"{_KEY}": 1, "{_KEY}:field": 2}}
nokey = td["{_PKG}.agent_runtime.zz"]
"""
_TEMPLATES_PATH = f"{_PKG}/cases/templates.py"
_DATA_PATH = f"{_PKG}/cases/data.py"


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _install_ratchet(root: Path, package: str = _PKG) -> Path:
    _write(root, {f"{package}/__init__.py": "", f"{package}/lint/__init__.py": ""})
    dest = root / package / "lint" / "mypy_ratchet.py"
    shutil.copyfile(_RATCHET, dest)
    return dest


def _install_map(root: Path) -> Path:
    dest = root / "packaging" / "machinery-move"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("rename-map.json", "rename-map.json.sha256"):
        shutil.copyfile(_FIXTURES / name, dest / name)
    return dest / "rename-map.json"


def _import(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def extracted(tmp_path: Path) -> Iterator[tuple[Path, ModuleType]]:
    """An extracted layout without mypy runs: the ratchet copy and the verified map."""

    root = tmp_path / "extract"
    _write(root, {"pyproject.toml": _CONFIG})
    name = f"_ratchet_{tmp_path.name}"
    module = _import(_install_ratchet(root), name)
    _install_map(root)
    yield root, module
    sys.modules.pop(name, None)


@pytest.fixture(scope="module")
def cases(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, ModuleType, list]]:
    """One real mypy run over the case files in the extracted layout."""

    root = tmp_path_factory.mktemp("cases")
    _write(root, {"pyproject.toml": _CONFIG, **_SUPPORT, _TEMPLATES_PATH: _TEMPLATES, _DATA_PATH: _DATA})
    name = "_ratchet_cases"
    module = _import(_install_ratchet(root), name)
    _install_map(root)
    errors, fatal = module.collect_errors(
        root, [f"{_PKG}/cases"], config_file=root / "pyproject.toml", incremental=False
    )
    assert fatal == []
    yield root, module, errors
    sys.modules.pop(name, None)


def _baseline(path: Path, rows: list[tuple[str, str, str]]) -> Path:
    payload = {
        "schema": source_ratchet.SCHEMA,
        "mypy": "fixture",
        "entries": [{"path": p, "code": c, "message": m} for p, c, m in rows],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _reported(errors: list, path: str, code: str, message: str) -> object:
    found = [error for error in errors if error.identity == (path, code, message)]
    assert found, f"mypy did not report {code}: {message}"
    return found[0]


def _respelled(message: str) -> str:
    return message.replace(f"{_PKG}.", "scripts.")


# (case, path, code, message mypy reports, baseline message, compares equal)
_EQUAL_CASES = [
    (
        "module-slot",
        _TEMPLATES_PATH,
        "attr-defined",
        f'Module "{_KEY}" has no attribute "absent_name"',
        f'Module "scripts.{_IDENTITY}" has no attribute "absent_name"',
    ),
    (
        "variable-slot-keeps-symbol",
        _TEMPLATES_PATH,
        "valid-type",
        f'Variable "{_PKG}.orchestration.prompt_contracts._SafeLoaderBase" is not valid as a type',
        'Variable "scripts.orchestration.prompt_contracts._SafeLoaderBase" is not valid as a type',
    ),
    (
        "product-module-preserved",
        _TEMPLATES_PATH,
        "attr-defined",
        'Module "scripts.audit.model_families" has no attribute "Family"',
        'Module "scripts.audit.model_families" has no attribute "Family"',
    ),
    (
        "unchanged-data-value",
        _DATA_PATH,
        "typeddict-item",
        f'Value of "scripts.{_IDENTITY}:field" has incompatible type "str"; expected "int"',
        f'Value of "scripts.{_IDENTITY}:field" has incompatible type "str"; expected "int"',
    ),
]
_VIOLATION_CASES = [
    # F1 round 1: a Literal value and TypedDict keys are data.
    (
        "r1-literal",
        _DATA_PATH,
        "assignment",
        f"Incompatible types in assignment (expression has type \"Literal['other']\", "
        f"variable has type \"Literal['{_KEY}']\")",
    ),
    ("r1-missing-key", _DATA_PATH, "typeddict-item", f'Missing key "{_KEY}" for TypedDict "TD"'),
    ("r1-missing-keys", _DATA_PATH, "typeddict-item", f'Missing keys ("{_KEY}", "{_KEY}.b") for TypedDict "TWO"'),
    # F1 round 2: Value-of and item messages, unescaped quotes, Literal[ inside a key.
    (
        "r2-item",
        _DATA_PATH,
        "typeddict-item",
        f'Incompatible types (expression has type "str", TypedDict item "{_KEY}" has type "int")',
    ),
    ("r2-value-of", _DATA_PATH, "typeddict-item", f'Value of "{_KEY}" has incompatible type "str"; expected "int"'),
    ("r2-embedded-quote", _DATA_PATH, "typeddict-unknown-key", f'Extra key "{_KEY}"y" for TypedDict "TD""'),
    ("r2-literal-in-key", _DATA_PATH, "typeddict-unknown-key", f'Extra key "Literal[\'{_KEY}" for TypedDict "TD"'),
    ("r2-no-key", _DATA_PATH, "typeddict-item", f'TypedDict "TD" has no key "{_PKG}.agent_runtime.zz"'),
    # F1 round 3: a value that only starts with a machinery module.
    ("r3-field", _DATA_PATH, "typeddict-item", f'Value of "{_KEY}:field" has incompatible type "str"; expected "int"'),
    # Delimiter suffixes after a module-like value.
    ("suffix-comma", _DATA_PATH, "typeddict-unknown-key", f'Extra key "{_KEY},x" for TypedDict "TD"'),
    ("suffix-pipe", _DATA_PATH, "typeddict-unknown-key", f'Extra key "{_KEY}|x" for TypedDict "TD"'),
    ("suffix-paren", _DATA_PATH, "typeddict-unknown-key", f'Extra key "{_KEY})x" for TypedDict "TD"'),
    ("suffix-space", _DATA_PATH, "typeddict-unknown-key", f'Extra key "{_KEY} x" for TypedDict "TD"'),
    ("suffix-field", _DATA_PATH, "typeddict-unknown-key", f'Extra key "{_KEY}:field" for TypedDict "TD"'),
    # Template-shaped messages the allowlist refuses.
    (
        "trailing-text",
        _TEMPLATES_PATH,
        "attr-defined",
        f'Module "{_KEY}" has no attribute "KNOWN_SEET"; maybe "KNOWN_SEAT"?',
    ),
    ("mixed-package", _TEMPLATES_PATH, "attr-defined", f'Module "{_PKG}.review" has no attribute "absent_hook"'),
    ("unknown-module", _TEMPLATES_PATH, "attr-defined", f'Module "{_PKG}.zz_unknown" has no attribute "absent_thing"'),
]


@pytest.mark.parametrize(("case", "path", "code", "reported", "census"), _EQUAL_CASES, ids=[c[0] for c in _EQUAL_CASES])
def test_template_slot_and_unchanged_values_compare_equal(
    cases: tuple[Path, ModuleType, list], tmp_path: Path, case: str, path: str, code: str, reported: str, census: str
) -> None:
    """A census-spelled template slot equals mypy's extracted spelling; product names and unchanged data stay."""

    _root, ratchet, errors = cases
    current = _reported(errors, path, code, reported)
    baseline = ratchet.load_entries(_baseline(tmp_path / f"{case}.json", [(path, code, census)]))
    assert ratchet.compare([current], baseline) == []


@pytest.mark.parametrize(("case", "path", "code", "reported"), _VIOLATION_CASES, ids=[c[0] for c in _VIOLATION_CASES])
def test_changed_data_and_refused_templates_are_violations(
    cases: tuple[Path, ModuleType, list], tmp_path: Path, case: str, path: str, code: str, reported: str
) -> None:
    """The census spelling of a data value or a refused template never equals the extracted spelling."""

    _root, ratchet, errors = cases
    current = _reported(errors, path, code, reported)
    census = _respelled(reported)
    assert census != reported
    loaded = ratchet.load_entries(_baseline(tmp_path / f"{case}.json", [(path, code, census)]))
    assert [entry.message for entry in loaded] == [ratchet._normalize_message(census)]
    violations = ratchet.compare([current], loaded)
    assert any(": new " in item for item in violations), violations
    assert any(": stale baseline " in item for item in violations), violations


def test_a_whole_machinery_module_name_in_data_is_compared_exactly(cases: tuple[Path, ModuleType, list]) -> None:
    """A data value equal to a moved module's name is data, not a template slot."""

    _root, ratchet, errors = cases
    message = f'Value of "{_KEY}" has incompatible type "str"; expected "int"'
    current = _reported(errors, _DATA_PATH, "typeddict-item", message)
    baseline = ratchet._entries_from_rows(
        [{"path": _DATA_PATH, "code": "typeddict-item", "message": _respelled(message)}], "fixture"
    )
    assert baseline[0].message == _respelled(message)
    assert ratchet.compare([current], baseline)


@pytest.mark.parametrize(
    ("case", "code", "census", "reported"),
    [
        (
            "changed-attribute",
            "attr-defined",
            f'Module "scripts.{_IDENTITY}" has no attribute "other_name"',
            f'Module "{_KEY}" has no attribute "absent_name"',
        ),
        (
            "changed-symbol",
            "valid-type",
            'Variable "scripts.orchestration.prompt_contracts._OtherBase" is not valid as a type',
            f'Variable "{_PKG}.orchestration.prompt_contracts._SafeLoaderBase" is not valid as a type',
        ),
        (
            "wrong-code",
            "misc",
            f'Module "scripts.{_IDENTITY}" has no attribute "absent_name"',
            f'Module "{_KEY}" has no attribute "absent_name"',
        ),
    ],
)
def test_changed_template_content_is_a_violation(
    cases: tuple[Path, ModuleType, list], tmp_path: Path, case: str, code: str, census: str, reported: str
) -> None:
    """Only the slot is respelled: a changed attribute or symbol, or another code, still differs."""

    _root, ratchet, errors = cases
    current = [error for error in errors if error.message == reported]
    assert len(current) == 1
    loaded = ratchet.load_entries(_baseline(tmp_path / f"{case}.json", [(_TEMPLATES_PATH, code, census)]))
    if code == "misc":
        assert loaded[0].message == census  # a template text under another code is not respelled
    violations = ratchet.compare(current, loaded)
    assert any(": new " in item for item in violations), violations
    assert any(": stale baseline " in item for item in violations), violations


@pytest.mark.parametrize(
    "message",
    [
        f'Module "scripts.{_IDENTITY}" has no attribute "absent_name" ',
        f'Module "scripts.{_IDENTITY}" has no attribute "absent_name" (extra)',
        f' Module "scripts.{_IDENTITY}" has no attribute "absent_name"',
        f'Module "scripts.{_IDENTITY}"x" has no attribute "absent_name"',
        f'Module "scripts.{_IDENTITY}" has no attribute "a"b"',
        f'Module "scripts.{_IDENTITY}" has no attribute "absent_name"; maybe "KNOWN_SEAT"?',
        f'Module "scripts.{_IDENTITY}" does not explicitly export attribute "absent_name"',
        f'Module "scripts.{_IDENTITY}" has no attribute "absent_name" on line 3',
        'Module "scripts.launchers" has no attribute "x"',
        'Module "scripts" has no attribute "x"',
        f'Module "scripts.{_IDENTITY}.KNOWN_SEAT" has no attribute "x"',
    ],
)
def test_near_templates_are_never_respelled(extracted: tuple[Path, ModuleType], message: str) -> None:
    """Trailing or leading text, quotes, other forms and non-module slots keep the census spelling."""

    _root, ratchet = extracted
    loaded = ratchet._entries_from_rows([{"path": "p.py", "code": "attr-defined", "message": message}], "fixture")
    assert loaded[0].message == ratchet._normalize_message(message)


@pytest.mark.parametrize(
    "message",
    [
        'Variable "scripts.orchestration.prompt_contracts" is not valid as a type',
        'Variable "scripts.zz_unknown.X" is not valid as a type',
        'Module "scripts.orchestration.prompt_contracts" is not valid as a type',
        'Function "scripts.orchestration.prompt_contracts.f" is not valid as a type',
        'Variable "scripts.orchestration.prompt_contracts._SafeLoaderBase" is not valid as a type; x',
    ],
)
def test_variable_slot_needs_a_known_module_and_a_symbol(extracted: tuple[Path, ModuleType], message: str) -> None:
    _root, ratchet = extracted
    loaded = ratchet._entries_from_rows([{"path": "p.py", "code": "valid-type", "message": message}], "fixture")
    assert loaded[0].message == message


def test_duplicate_counts_stay_significant(cases: tuple[Path, ModuleType, list], tmp_path: Path) -> None:
    _root, ratchet, errors = cases
    reported = f'Module "{_KEY}" has no attribute "absent_name"'
    current = _reported(errors, _TEMPLATES_PATH, "attr-defined", reported)
    census = (_TEMPLATES_PATH, "attr-defined", f'Module "scripts.{_IDENTITY}" has no attribute "absent_name"')
    twice = ratchet.load_entries(_baseline(tmp_path / "twice.json", [census, census]))
    assert ratchet.compare([current], twice) == [f"{_TEMPLATES_PATH}: stale baseline attr-defined: {reported}"]
    once = ratchet.load_entries(_baseline(tmp_path / "once.json", [census]))
    assert ratchet.compare([current, current], once) == [f"{_TEMPLATES_PATH}: new attr-defined: {reported}"]


def _run_main(ratchet: ModuleType, argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    code = ratchet.main(argv)
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def test_custom_baseline_end_to_end(
    cases: tuple[Path, ModuleType, list], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``main`` with ``--baseline``: respelled slots pass; the round-3 changed key is reported."""

    root, ratchet, errors = cases
    rows = []
    for error in errors:
        message = error.message
        if error.path == _TEMPLATES_PATH and error.code in ("attr-defined", "valid-type"):
            respelled = _respelled(message)
            # The allowlist respells exactly these two slots; the rest stay as mypy writes them.
            if "absent_name" in message or "_SafeLoaderBase" in message:
                message = respelled
        rows.append((error.path, error.code, message))
    templates = _baseline(tmp_path / "templates.json", rows)
    argv = ["--root", str(root), "--no-incremental", "--baseline", str(templates)]
    code, output = _run_main(ratchet, [*argv, _TEMPLATES_PATH, _DATA_PATH], capsys)
    assert code == 0, output
    field = f'Value of "{_KEY}:field" has incompatible type "str"; expected "int"'
    changed = [(p, c, _respelled(m) if m == field else m) for p, c, m in rows]
    code, output = _run_main(
        ratchet,
        [
            "--root",
            str(root),
            "--no-incremental",
            "--baseline",
            str(_baseline(tmp_path / "f1.json", changed)),
            _DATA_PATH,
        ],
        capsys,
    )
    assert code == 1
    assert f"{_DATA_PATH}: new typeddict-item: {field}" in output
    assert f"{_DATA_PATH}: stale baseline typeddict-item: {_respelled(field)}" in output


def _map_dir(root: Path) -> Path:
    return root / "packaging" / "machinery-move"


def _break_missing_map(root: Path) -> None:
    (_map_dir(root) / "rename-map.json").unlink()


def _break_missing_digest(root: Path) -> None:
    (_map_dir(root) / "rename-map.json.sha256").unlink()


def _break_mismatch(root: Path) -> None:
    path = _map_dir(root) / "rename-map.json"
    path.write_bytes(path.read_bytes().replace(b'"product"', b'"machinery"', 1))


def _record(root: Path, raw: bytes) -> None:
    (_map_dir(root) / "rename-map.json").write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (_map_dir(root) / "rename-map.json.sha256").write_text(f"{digest}  rename-map.json\n", encoding="ascii")


def _break_digest_format(root: Path) -> None:
    path = _map_dir(root) / "rename-map.json.sha256"
    path.write_text(path.read_text(encoding="ascii").upper(), encoding="ascii")


def _break_digest_name(root: Path) -> None:
    path = _map_dir(root) / "rename-map.json.sha256"
    path.write_text(path.read_text(encoding="ascii").split()[0] + "\n", encoding="ascii")


def _break_not_json(root: Path) -> None:
    _record(root, b"{not json")


def _break_not_object(root: Path) -> None:
    _record(root, b'["scripts/a.py"]')


def _break_owner(root: Path) -> None:
    _record(root, b'{"scripts/a.py": "shared"}')


def _break_key(root: Path) -> None:
    _record(root, b'{"../scripts/a.py": "machinery"}')


_BROKEN = {
    "missing-map": (_break_missing_map, "required for machinery package 'lu_machinery'; unreadable"),
    "missing-digest": (_break_missing_digest, "required for machinery package 'lu_machinery'; unreadable"),
    "mismatched-digest": (_break_mismatch, "does not match the recorded"),
    "uppercase-digest": (_break_digest_format, "expected one line"),
    "digest-without-name": (_break_digest_name, "expected one line"),
    "not-json": (_break_not_json, "not valid JSON"),
    "not-an-object": (_break_not_object, "non-empty JSON object"),
    "unknown-owner": (_break_owner, "has owner 'shared'"),
    "unnormalized-key": (_break_key, "normalized relative path"),
}


@pytest.mark.parametrize("case", sorted(_BROKEN))
def test_missing_or_broken_map_fails_explicitly(
    extracted: tuple[Path, ModuleType], tmp_path: Path, capsys: pytest.CaptureFixture[str], case: str
) -> None:
    """The extracted layout never falls back to the source spelling, with any --root or --baseline."""

    root, ratchet = extracted
    breaker, expected = _BROKEN[case]
    breaker(root)
    baseline = _baseline(tmp_path / "custom.json", [("p.py", "misc", "x")])
    with pytest.raises(ValueError, match=expected):
        ratchet.load_entries(baseline)
    elsewhere = tmp_path / "elsewhere"
    _write(elsewhere, {"pyproject.toml": _CONFIG})
    _install_map(elsewhere)  # a valid map under --root is not this checkout's map
    code, output = _run_main(ratchet, ["--root", str(elsewhere), "--baseline", str(baseline), "absent.py"], capsys)
    assert code == 1
    assert "mypy ratchet could not run: " in output
    assert expected in output
    written = tmp_path / "written.json"
    default = Path(ratchet.BASELINE_PATH)
    for argv in (
        ["--write-baseline", "--no-incremental"],
        ["--root", str(elsewhere), "--baseline", str(written), "--write-baseline", "--no-incremental"],
    ):
        code, output = _run_main(ratchet, argv, capsys)
        assert code == 1, output
        assert expected in output
    assert not written.exists()
    assert not default.exists()


def test_source_layout_needs_no_map_and_respells_nothing() -> None:
    spelling = source_ratchet._baseline_spelling()
    assert (spelling.package, spelling.rename_map) == ("scripts", None)
    rows = json.loads((_FIXTURES / "template-rows-6986c7b1.json").read_text(encoding="utf-8"))["rows"]
    assert all(spelling.message(row["code"], row["message"]) == row["message"] for row in rows)
    assert source_ratchet.DEFAULT_TARGET == "scripts"


def test_the_39_template_rows_respell_37_and_keep_2_product_names(extracted: tuple[Path, ModuleType]) -> None:
    """At 6986c7b16b: 38 attr-defined and one valid-type rows; 37 move, two name a product module."""

    _root, ratchet = extracted
    fixture = json.loads((_FIXTURES / "template-rows-6986c7b1.json").read_text(encoding="utf-8"))
    rows = fixture["rows"]
    assert len(rows) == 39
    assert sorted(row["code"] for row in rows).count("attr-defined") == 38
    spelling = ratchet._baseline_spelling()
    assert spelling.package == _PKG
    respelled = [spelling.message(row["code"], row["message"]) for row in rows]
    assert respelled == [row["extracted"] for row in rows]
    kept = [row["message"] for row, new in zip(rows, respelled, strict=True) if new == row["message"]]
    assert sorted(kept) == [
        'Module "scripts.audit.model_families" has no attribute "Family"',
        'Module "scripts.audit.model_families" has no attribute "normalize_family"',
    ]
    assert sum(new != row["message"] for row, new in zip(rows, respelled, strict=True)) == 37


def test_committed_baseline_respells_only_template_rows(extracted: tuple[Path, ModuleType]) -> None:
    """Every other committed row loads unchanged; the template rows are a subset of the 39."""

    _root, ratchet = extracted
    fixture = json.loads((_FIXTURES / "template-rows-6986c7b1.json").read_text(encoding="utf-8"))
    expected = {(row["path"], row["code"], row["message"]): row["extracted"] for row in fixture["rows"]}
    raw = json.loads(source_ratchet.BASELINE_PATH.read_text(encoding="utf-8"))["entries"]
    source = source_ratchet.load_entries(source_ratchet.BASELINE_PATH)
    loaded = ratchet.load_entries(source_ratchet.BASELINE_PATH)
    assert len(source) == len(loaded) == len(raw)
    for row, before, after in zip(raw, source, loaded, strict=True):
        identity = (row["path"], row["code"], row["message"])
        template = ratchet._SLOT_TEMPLATES.get(row["code"])
        if template is not None and template[0].fullmatch(row["message"]):
            assert identity in expected
            assert after.message == ratchet._normalize_message(expected[identity])
        else:
            assert after.identity == before.identity


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Ratchet Fixture",
            "-c",
            "user.email=ratchet@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )


def test_shrink_against_head_parent_and_origin_main_survives_respelling(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--write-baseline in the extracted spelling is no growth; an added identity or a duplicate is."""

    root = tmp_path / "repo"
    _write(
        root,
        {
            "pyproject.toml": _CONFIG,
            f"{_PKG}/agent_runtime/__init__.py": "",
            f"{_PKG}/agent_runtime/agent_identity.py": "KNOWN_SEAT = 1\n",
            f"{_PKG}/probe.py": "from lu_machinery.agent_runtime.agent_identity import absent_name\n",
        },
    )
    name = f"_ratchet_{tmp_path.name}"
    ratchet = _import(_install_ratchet(root), name)
    try:
        _install_map(root)
        baseline = root / _PKG / "lint" / "mypy_baseline.json"
        code, output = _run_main(ratchet, ["--root", str(root), "--write-baseline", "--no-incremental"], capsys)
        assert code == 0, output
        written = json.loads(baseline.read_text(encoding="utf-8"))
        reported = f'Module "{_KEY}" has no attribute "absent_name"'
        assert [row["message"] for row in written["entries"]].count(reported) == 1
        census = dict(written, entries=[dict(row, message=_respelled(row["message"])) for row in written["entries"]])
        baseline.write_text(json.dumps(census, indent=2) + "\n", encoding="utf-8")
        _git(root, "init", "-q", "-b", "main")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "census")
        _git(root, "commit", "-q", "--allow-empty", "-m", "head")
        _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")

        code, output = _run_main(ratchet, ["--root", str(root), "--no-incremental"], capsys)
        assert code == 0, output
        code, output = _run_main(ratchet, ["--root", str(root), "--write-baseline", "--no-incremental"], capsys)
        assert code == 0, output
        assert baseline.read_text(encoding="utf-8") != json.dumps(census, indent=2) + "\n"
        entries = ratchet.load_entries(baseline)
        assert ratchet.shrink_violations(root, baseline, entries) == []
        code, output = _run_main(ratchet, ["--root", str(root), "--no-incremental"], capsys)
        assert code == 0, output

        rel = f"{_PKG}/lint/mypy_baseline.json"
        growth = [f"{rel}: baseline may only shrink; freeze/growth differs from {ref}" for ref in ratchet._SHRINK_REFS]
        added = [*entries, ratchet.MypyError(f"{_PKG}/probe.py", "misc", "added identity")]
        assert ratchet.shrink_violations(root, baseline, added) == growth
        duplicated = [*entries, next(entry for entry in entries if entry.message == reported)]
        assert ratchet.shrink_violations(root, baseline, duplicated) == growth
        ratchet.write_baseline(baseline, duplicated)
        code, output = _run_main(ratchet, ["--root", str(root), "--no-incremental"], capsys)
        assert code == 1
        for line in growth:
            assert line in output
    finally:
        sys.modules.pop(name, None)
