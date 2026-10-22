"""Equivalence and speed guards for the whole-repository temp-path lint (#11402).

The scan must produce the same rows and the same CLI exit status as the base
scanner for every scannable file, including malformed source and identifiers
that Python normalizes. These tests fix the finding set on a fixture tree,
prove the single-walk rewrite matches the base two-walk scanner on a generated
differential corpus, and freeze the node types whose traversal is skipped.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.hygiene import lint_tmp_paths as lint

LITERAL = "/" + "tmp/fixture"
TMP_ROOT = "/" + "tmp"
MANAGED = "/" + "var/tmp/lu"
VAR_ROOT = "/var" + "/" + "tmp"
PRIVATE_ROOT = "/private" + "/" + "tmp"
DEV_ROOT = "/" + "dev" + "/" + "shm"
BASE_SOURCE = "scripts/hygiene/lint_tmp_paths.py"

# Captured with the pre-change implementation over the fixture tree below.
# Literal rows are identified by digest so this module stays free of temp literals.
GOLDEN_ROWS = [
    ("scripts/alias.py", 2, "9006ccc735e1a8c1c4572426a153945da43c8ac5cefb5c2af74ea95b27858785"),
    ("scripts/bytes_escaped.py", 1, "ccb7df6064a33f8150c2a597a200d64a836fd529fb20d64ea9f87cf5aa5156d3"),
    ("scripts/comment_only.py", 1, "639953c2c8533b6e388919f0605df6a7541864aab1654affcd5009617dd674c2"),
    ("scripts/comment_split.py", 1, "883b21ebe92ae44257c9348e1d4854bafd3c6dad493e248b947bfe25940b7739"),
    ("scripts/continuation.py", 1, "46ad9a7e25515422a04164ba20e81b1499ceb9e62c9c4ded69a1cc4381b7984d"),
    ("scripts/escaped.py", 1, "a41f11b23cac679f21ff77588071fb0ff866104bee24aac6f32e8ae40dccacb5"),
    ("scripts/escaped_octal.py", 1, "3780c256dba9a036a94b179929c8486a8b161880ff177ebbe18373e361afd6af"),
    ("scripts/escaped_unicode.py", 1, "ccd97b2ffd2eab29601e86e9b7efdaa896c5872b87de6476c58410f16c4a0339"),
    ("scripts/from_alias.py", 2, "e172fa0c4b8ea412b910acba76a929bd0d0b21fd086ab5094c9f0219442cdd4c"),
    ("scripts/fstring.py", 2, "30439b39bb68ef35e4ba2c9f41c5cd0ec5fc02b280f89d3e05de38edc40fe1da"),
    ("scripts/multiline.py", 1, "5022e401f35de043a882a3fdab2af1d4b7c5e600e7f85ba9e849982fe45067d5"),
    ("scripts/multiline.py", 2, "e323404d9a5f9c26d23dd20afb682632d00dc3b710bb3dc494f7a83693afa557"),
    ("scripts/plain.py", 1, "c208c41f900c27542fbf5c0461ada98cf2a7cd0389a7ec148bb2b6fc77641456"),
    ("scripts/prefix_split.py", 1, "ec893fee90c86cfb0a2d24f66489120578b5c76f348bc09ddb4945754ea652a4"),
    ("scripts/probe.sh", 1, "c56cfefbf063a967029718ef699daba75bc10766c62bdf4bde8f1b09e00d62cc"),
    ("scripts/probe.sh", 2, "eaefc11c6088dc5f81ee56cc08df8bcd8101b2439f5a4662b9334f5fc44911f7"),
    ("scripts/split.py", 1, "8a2ce364788014c2e426d135698d6a967ff15a96bb00e28194ede57029fef7f1"),
    ("scripts/star.py", 2, "13e1c85b5e56202a489b19ee30616f8b42bdc21097cf8586a4880226cc014564"),
    ("scripts/var.py", 1, "91d44a5e4c8ef463baff15a170a53c4f480c7d0e7fc6cc77a29d47b8934abc72"),
    ("scripts/var.py", 2, "011a37168305d0011f916341018a29677670dde0be273001a9a0295f4d6d8898"),
    ("scripts/var.py", 3, "2a01a948b4c89ff312764d0afbdd97baf4e98c2611f053e6f8812b6d0263e94e"),
    ("tests/basic.py", 1, "be249c4aa3ba6b721d00fe7ba2da4ee3e2a7d32ab2d0f4b0ee2cd56131f5e4c0"),
]

GOLDEN_FINDINGS = [
    ("scripts/alias.py", 2),
    ("scripts/bytes_escaped.py", 1),
    ("scripts/comment_only.py", 1),
    ("scripts/comment_split.py", 1),
    ("scripts/continuation.py", 1),
    ("scripts/escaped.py", 1),
    ("scripts/escaped_octal.py", 1),
    ("scripts/escaped_unicode.py", 1),
    ("scripts/from_alias.py", 2),
    ("scripts/fstring.py", 2),
    ("scripts/multiline.py", 1),
    ("scripts/multiline.py", 2),
    ("scripts/plain.py", 1),
    ("scripts/prefix_split.py", 1),
    ("scripts/probe.sh", 1),
    ("scripts/probe.sh", 2),
    ("scripts/split.py", 1),
    ("scripts/star.py", 2),
    ("scripts/var.py", 1),
    ("scripts/var.py", 2),
    ("scripts/var.py", 3),
    ("tests/basic.py", 1),
]


def _fixture_sources() -> dict[str, str]:
    return {
        "scripts/plain.py": f'ROOT = "{LITERAL}/plain"\n',
        "scripts/var.py": (f'ROOT = "{VAR_ROOT}/x"\nALT = "{PRIVATE_ROOT}/x"\nDEV = "{DEV_ROOT}/x"\n'),
        "scripts/escaped.py": 'ROOT = "\\x2f\\x74\\x6d\\x70\\x2fx"\n',
        "scripts/escaped_octal.py": 'ROOT = "\\057\\164\\155\\160/x"\n',
        "scripts/escaped_unicode.py": 'ROOT = "\\u002ftmp/x"\n',
        "scripts/bytes_escaped.py": 'ROOT = b"\\x2ftmp/x"\n',
        "scripts/fstring.py": f'NAME = "x"\nROOT = f"{LITERAL}/{{NAME}}"\n',
        "scripts/split.py": 'ROOT = "/t" "mp/x"\n',
        "scripts/continuation.py": 'ROOT = "/t" \\\n"mp/x"\n',
        "scripts/prefix_split.py": 'ROOT = "/t" r"mp/x"\n',
        "scripts/comment_split.py": 'ROOT = ("/t"  # join\n    "mp/x")\n',
        "scripts/multiline.py": 'VALUE = """\n' + f"{LITERAL}/multi\n" + '"""\n',
        "scripts/alias.py": "import tempfile as tf\ntf.mkdtemp()\n",
        "scripts/star.py": "from tempfile import *\nNamedTemporaryFile()\n",
        "scripts/from_alias.py": "from tempfile import mkstemp as create\ncreate()\n",
        "scripts/approved.py": "import tempfile\ntempfile.mkdtemp(dir=TMPDIR)\n",
        "scripts/managed.py": f'ROOT = "{MANAGED}/child"\n',
        "scripts/comment_only.py": f"# {LITERAL}/comment\n",
        "scripts/clean.py": "VALUE = 1\n",
        "tests/basic.py": f'ROOT = "{LITERAL}/test"\n',
        "scripts/probe.sh": 'mktemp -d\nROOT="' + LITERAL + '/shell"\n',
    }


def _build_fixture_tree(root: Path) -> None:
    for name, text in _fixture_sources().items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)


def test_golden_finding_set_matches_pre_change_implementation(tmp_path):
    _build_fixture_tree(tmp_path)
    rows = [(path, number, lint.line_digest(text)) for path, number, text in lint.scan_lines(tmp_path)]
    assert rows == GOLDEN_ROWS
    assert lint.find_literal_tmp_paths(tmp_path) == GOLDEN_FINDINGS


def test_scan_parses_every_python_file(tmp_path, monkeypatch):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    sources = {f"clean{index}.py": f"VALUE = {index}\n" for index in range(20)}
    sources.update(
        {
            "string_bracket.py": 'VALUE = "("\n',
            "literal.py": f'ROOT = "{LITERAL}/x"\n',
            "producer.py": "import tempfile\ntempfile.mkdtemp()\n",
            "escaped.py": 'ROOT = "\\x2ftmp/x"\n',
            "split.py": 'ROOT = "/t" "mp/x"\n',
        }
    )
    for name, text in sources.items():
        (scripts / name).write_text(text)

    parsed: list[str] = []
    original_parse = lint.ast.parse

    def tracking_parse(source, *args, **kwargs):
        parsed.append(kwargs.get("filename", ""))
        return original_parse(source, *args, **kwargs)

    monkeypatch.setattr(lint.ast, "parse", tracking_parse)
    lint.scan_lines(tmp_path)
    assert sorted(parsed) == sorted(f"scripts/{name}" for name in sources)

    (scripts / "aaa_invalid.py").write_text("x = ([)]\n")
    parsed.clear()
    with pytest.raises(SyntaxError):
        lint.scan_lines(tmp_path)
    assert parsed == ["scripts/aaa_invalid.py"]


EXPECTED_SKIPPED_NODES = {
    "Load",
    "Store",
    "Del",
    "Name",
    "alias",
    "Pass",
    "Break",
    "Continue",
    "Global",
    "Nonlocal",
    "Add",
    "Sub",
    "Mult",
    "MatMult",
    "Div",
    "Mod",
    "Pow",
    "LShift",
    "RShift",
    "BitOr",
    "BitXor",
    "BitAnd",
    "FloorDiv",
    "And",
    "Or",
    "Not",
    "Invert",
    "UAdd",
    "USub",
    "Eq",
    "NotEq",
    "Lt",
    "LtE",
    "Gt",
    "GtE",
    "Is",
    "IsNot",
    "In",
    "NotIn",
}
SAFE_SKIPPED_FIELDS = {"id", "ctx", "name", "asname", "names"}


def test_skipped_ast_nodes_cannot_hold_findings():
    assert {cls.__name__ for cls in lint.SKIPPED_AST_NODES} == EXPECTED_SKIPPED_NODES
    for cls in lint.SKIPPED_AST_NODES:
        # Only identifier tokens, name contexts and operator singletons may be
        # skipped; a new field such as ``value`` would re-admit findings.
        assert set(cls._fields) <= SAFE_SKIPPED_FIELDS, cls.__name__


def _load_base_lint(tmp_path: Path) -> object:
    """Load the base scanner from ``origin/main`` into a private module."""
    if shutil.which("git") is None:
        pytest.skip("git is unavailable, so the base scanner cannot be loaded")
    result = subprocess.run(
        ["git", "-C", str(lint.REPO_ROOT), "show", f"origin/main:{BASE_SOURCE}"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 or not result.stdout:
        shallow = subprocess.run(
            ["git", "-C", str(lint.REPO_ROOT), "rev-parse", "--is-shallow-repository"],
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout.strip()
        pytest.skip(f"origin/main scanner is unavailable in this checkout (shallow={shallow or 'unknown'})")
    target = tmp_path / "base_lint_tmp_paths.py"
    target.write_text(result.stdout)
    spec = importlib.util.spec_from_file_location("base_lint_tmp_paths_11402", target)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base_lint(tmp_path_factory) -> object:
    return _load_base_lint(tmp_path_factory.mktemp("base-lint"))


def _finding_fields(findings) -> list[tuple[str, int, str]]:
    return [(finding.path, finding.line, finding.message) for finding in findings]


def _run_cli(module, root: Path, path: Path) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(["--repo", str(root), str(path)])
    return code, out.getvalue(), err.getvalue()


ALIAS_ORDER_CASES = [
    ("use_before_import", "t.mkdtemp()\nimport tempfile as t\n", [1]),
    ("nested_import", "def f():\n    import tempfile as t\nt.mkdtemp()\n", [3]),
    ("nested_shadow", "import tempfile as t\ndef f():\n    import other as t\nt.mkdtemp()\n", []),
    ("top_level_overwrite", "import other as t\nimport tempfile as t\nt.mkdtemp()\n", [3]),
    (
        "nested_import_before_later_top_level",
        "def f():\n    import tempfile as t\nimport other as t\nt.mkdtemp()\n",
        [4],
    ),
    ("star_after_use", "NamedTemporaryFile()\nfrom tempfile import *\n", [1]),
    ("nested_shadow_then_top_level", "def f():\n    import tempfile as t\nt.mkdtemp()\nimport other as t\n", [3]),
]


@pytest.mark.parametrize("name, source, lines", ALIAS_ORDER_CASES)
def test_alias_resolution_order(name, source, lines):
    del name
    assert [finding.line for finding in lint.scan_python(source, "scripts/probe.py")] == lines


@pytest.mark.parametrize("name, source, lines", ALIAS_ORDER_CASES)
def test_alias_resolution_matches_two_pass_scanner(base_lint, name, source, lines, tmp_path):
    del name, lines
    assert _finding_fields(lint.scan_python(source, "scripts/probe.py")) == _finding_fields(
        base_lint.scan_python(source, "scripts/probe.py")
    )
    path = tmp_path / "scripts" / "probe.py"
    path.parent.mkdir()
    path.write_text(source)
    assert lint.scan_lines(tmp_path) == base_lint.scan_lines(tmp_path)


REVIEW_COUNTEREXAMPLES = [
    # F1: a quoted hash must not erase adjacent literals that the parser folds.
    ("quoted_hash", 'tag="#"; root="/t" "mp/x"\n'),
    # F2: Python NFKC-normalizes identifiers; U+FF54 is a fullwidth ASCII "t".
    ("normalized_identifier", "import \uff54empfile as t\nt.mkdtemp()\n"),
]


EXPECTED_COUNTEREXAMPLE_ROWS = {
    "quoted_hash": [("scripts/probe.py", 1, 'tag="#"; root="/t" "mp/x"')],
    "normalized_identifier": [("scripts/probe.py", 2, "tempfile-call: requires approved dir=: t.mkdtemp()")],
}


@pytest.mark.parametrize("name, source", REVIEW_COUNTEREXAMPLES)
def test_review_counterexamples_keep_their_findings(name, source, tmp_path):
    path = tmp_path / "scripts" / "probe.py"
    path.parent.mkdir()
    path.write_text(source)
    assert lint.scan_lines(tmp_path) == EXPECTED_COUNTEREXAMPLE_ROWS[name]
    assert _run_cli(lint, tmp_path, path)[0] == 1


@pytest.mark.parametrize("name, source", REVIEW_COUNTEREXAMPLES)
def test_review_counterexamples_match_base_byte_for_byte(base_lint, name, source, tmp_path):
    del name
    path = tmp_path / "scripts" / "probe.py"
    path.parent.mkdir()
    path.write_text(source)
    assert lint.scan_lines(tmp_path) == base_lint.scan_lines(tmp_path)
    assert _run_cli(lint, tmp_path, path) == _run_cli(base_lint, tmp_path, path)


MALFORMED_SOURCES = [
    "x=([)]\n",
    'x=(\ns=")"\n',
    "x =\n",
    'x = "unterminated\n',
    "def broken(:\n",
    "x = (1\n",
    "if True\n    pass\n",
]


@pytest.mark.parametrize("source", MALFORMED_SOURCES)
def test_malformed_source_keeps_parse_error_exit(source, tmp_path):
    path = tmp_path / "scripts" / "probe.py"
    path.parent.mkdir()
    path.write_text(source)
    code, _, err = _run_cli(lint, tmp_path, path)
    assert code == 2
    assert "cannot read or parse source" in err


@pytest.mark.parametrize("source", MALFORMED_SOURCES)
def test_malformed_source_matches_base_byte_for_byte(base_lint, source, tmp_path):
    path = tmp_path / "scripts" / "probe.py"
    path.parent.mkdir()
    path.write_text(source)
    assert _run_cli(lint, tmp_path, path) == _run_cli(base_lint, tmp_path, path)


def _indented(text: str, prefix: str = "    ") -> str:
    return "".join(prefix + line if line.strip() else line for line in text.splitlines(keepends=True))


def _fuzz_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    counter = 0

    def add(label: str, text: str) -> None:
        nonlocal counter
        sources[f"{counter:03d}_{label}.py"] = text
        counter += 1

    roots = [LITERAL, TMP_ROOT, VAR_ROOT, DEV_ROOT, PRIVATE_ROOT, MANAGED]
    shapes = [
        "plain",
        "single",
        "raw",
        "bytes",
        "split",
        "continuation",
        "comment_split",
        "hash_same_line",
        "hash_in_string",
        "fstring",
        "docstring",
        "comment_only",
        "dir_keyword",
    ]
    for root in roots:
        head, tail = root[:2], root[2:]
        for shape in shapes:
            if shape == "plain":
                text = f'ROOT = "{root}/x"\n'
            elif shape == "single":
                text = f"ROOT = '{root}/x'\n"
            elif shape == "raw":
                text = f'ROOT = r"{root}/x"\n'
            elif shape == "bytes":
                text = f'ROOT = b"{root}/x"\n'
            elif shape == "split":
                text = f'ROOT = "{head}" "{tail}/x"\n'
            elif shape == "continuation":
                text = f'ROOT = "{head}" \\\n    "{tail}/x"\n'
            elif shape == "comment_split":
                text = f'ROOT = ("{head}"  # join\n    "{tail}/x")\n'
            elif shape == "hash_same_line":
                text = f'tag = "#"; ROOT = "{head}" "{tail}/x"\n'
            elif shape == "hash_in_string":
                text = f'tag = "# {root}/x"\n'
            elif shape == "fstring":
                text = f'NAME = "x"\nROOT = f"{root}/{{NAME}}"\n'
            elif shape == "docstring":
                text = f'"""\n{root}/x\n"""\n'
            elif shape == "comment_only":
                text = f"# {root}/comment/x\n"
            else:
                text = f'import tempfile\ntempfile.mkdtemp(dir="{root}/x")\n'
            add(shape, text)
            pad = "    pass\n" if shape == "comment_only" else ""
            add(f"function_{shape}", "def probe():\n" + _indented(text) + pad)
            add(f"class_{shape}", "class Probe:\n" + _indented(text) + pad)

    for escape in [r"\x2f\x74\x6d\x70\x2fx", r"\057\164\155\160/x"]:
        add("escape", f'ROOT = "{escape}"\n')
        add("escape_bytes", f'ROOT = b"{escape}"\n')
        add("escape_raw", f'ROOT = r"{escape}"\n')
    for escape in [r"\u002ftmp/x", r"\N{SOLIDUS}tmp/x"]:
        # \u and \N are not valid bytes escapes in Python 3.12.
        add("escape_unicode", f'ROOT = "{escape}"\n')
        add("escape_unicode_raw", f'ROOT = r"{escape}"\n')

    add("unicode_import", "import \uff54empfile as t\nt.mkdtemp()\n")
    add("unicode_import_after_use", "t.mkdtemp()\nimport \uff54empfile as t\n")
    add("unicode_from", "from \uff54empfile import mkdtemp\nmkdtemp()\n")
    add("unicode_bare", "\uff54empfile.mkdtemp()\n")
    add("unicode_fullwidth", "import \uff54\uff45\uff4d\uff50\uff46\uff49\uff4c\uff45 as t\nt.mkdtemp()\n")
    add("unicode_shadow", "import other as t\nimport \uff54empfile as t\nt.mkdtemp()\n")
    add("unicode_attribute", "\uff54empfile.\uff4d\uff4b\uff44\uff54\uff45\uff4d\uff50()\n")

    for invalid in [
        "x=([)]\n",
        'x=(\ns=")"\n',
        "x =\n",
        'x = "unterminated\n',
        "def broken(:\n",
        "x = (1\n",
        "if True\n    pass\n",
        "class:\n",
        'x = f"{"\n',
    ]:
        add("invalid", invalid)

    calls = [
        "mkdtemp",
        "mkstemp",
        "mktemp",
        "TemporaryDirectory",
        "TemporaryFile",
        "NamedTemporaryFile",
        "SpooledTemporaryFile",
    ]
    for call in calls:
        add("producer_attribute", f"import tempfile\ntempfile.{call}()\n")
        add("producer_alias", f"import tempfile as tf\ntf.{call}()\n")
        add("producer_from", f"from tempfile import {call}\n{call}()\n")
        add("producer_from_alias", f"from tempfile import {call} as make\nmake()\n")
        add("producer_star", f"from tempfile import *\n{call}()\n")
        add("producer_approved", f"import tempfile\ntempfile.{call}(dir=TMPDIR)\n")
        add("producer_managed", f'import tempfile\ntempfile.{call}(dir="{MANAGED}/dir")\n')
        add("producer_use_before_import", f"tf.{call}()\nimport tempfile as tf\n")
        add("producer_nested_import", f"def f():\n    import tempfile as tf\ntf.{call}()\n")
        add("producer_nested_shadow", f"import tempfile as tf\ndef f():\n    import other as tf\ntf.{call}()\n")
        add("producer_nested_late_shadow", f"def f():\n    import tempfile as tf\nimport other as tf\ntf.{call}()\n")

    add("clear", "VALUE = 1\n")
    add("chr_construction", 'ROOT = chr(47) + "tmp/x"\n')
    add("plus_construction", 'ROOT = "/" + "tmp/x"\n')
    add("getattr_producer", 'import tempfile\ngetattr(tempfile, "mkdtemp")()\n')
    add("crlf_literal", 'BASE = 1\r\nROOT = "/t" "mp/x"\r\n')
    add("cr_only_literal", 'BASE = 1\rROOT = "/t" "mp/x"\r')
    add("no_trailing_newline", f'ROOT = "{LITERAL}/x"')
    add("nested_constant", f'ROOT = dict(items=[("{LITERAL}/x",), {{"k": f"{LITERAL}/y"}}])\n')
    add("shell_managed", 'mktemp -d "$TMPDIR/x"\n')
    add("shell_literal", 'ROOT="' + LITERAL + '/shell"\n')
    add("shell_heredoc", "cat <<'EOF'\n" + LITERAL + "/body\nEOF\n")
    return sources


def _scan_result(module, root: Path, path: Path):
    try:
        return ("rows", module.scan_lines(root, [path]))
    except (SyntaxError, UnicodeError) as exc:
        return ("error", type(exc).__name__, getattr(exc, "lineno", None), str(exc))


def test_differential_fuzz_matches_base_scanner(base_lint, tmp_path):
    sources = _fuzz_sources()
    assert len(sources) >= 300
    root = tmp_path / "tree"
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    for name, text in sources.items():
        (scripts / name).write_text(text, newline="")

    for name in sources:
        path = scripts / name
        assert _scan_result(lint, root, path) == _scan_result(base_lint, root, path), name
        assert _run_cli(lint, root, path) == _run_cli(base_lint, root, path), name
