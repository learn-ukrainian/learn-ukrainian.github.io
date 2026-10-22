"""Speed and coverage guards for the whole-repository temp-path lint (#11402).

The scan now skips ``ast.parse`` for Python sources that cannot yield a
finding. These tests fix the pre-change finding set on a fixture tree that
covers every finding kind, prove the prefilter keeps each flaggable kind, and
bound the number of files that are parsed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.hygiene import lint_tmp_paths as lint

LITERAL = "/" + "tmp/fixture"
MANAGED = "/" + "var/tmp/lu"
VAR_ROOT = "/var" + "/" + "tmp"
PRIVATE_ROOT = "/private" + "/" + "tmp"
DEV_ROOT = "/" + "dev" + "/" + "shm"

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


FLAGGABLE_SOURCES = [
    ("scripts/plain.py", f'ROOT = "{LITERAL}/plain"\n'),
    ("scripts/var.py", f'ROOT = "{VAR_ROOT}/x"\nALT = "{PRIVATE_ROOT}/x"\nDEV = "{DEV_ROOT}/x"\n'),
    ("scripts/escaped.py", 'ROOT = "\\x2f\\x74\\x6d\\x70\\x2fx"\n'),
    ("scripts/escaped_octal.py", 'ROOT = "\\057\\164\\155\\160/x"\n'),
    ("scripts/escaped_unicode.py", 'ROOT = "\\u002ftmp/x"\n'),
    ("scripts/bytes_escaped.py", 'ROOT = b"\\x2ftmp/x"\n'),
    ("scripts/fstring.py", f'NAME = "x"\nROOT = f"{LITERAL}/{{NAME}}"\n'),
    ("scripts/split.py", 'ROOT = "/t" "mp/x"\n'),
    ("scripts/continuation.py", 'ROOT = "/t" \\\n"mp/x"\n'),
    ("scripts/prefix_split.py", 'ROOT = "/t" r"mp/x"\n'),
    ("scripts/comment_split.py", 'ROOT = ("/t"  # join\n    "mp/x")\n'),
    ("scripts/multiline.py", 'VALUE = """\n' + f"{LITERAL}/multi\n" + '"""\n'),
    ("scripts/alias.py", "import tempfile as tf\ntf.mkdtemp()\n"),
    ("scripts/star.py", "from tempfile import *\nNamedTemporaryFile()\n"),
    ("scripts/from_alias.py", "from tempfile import mkstemp as create\ncreate()\n"),
]


@pytest.mark.parametrize("name, source", FLAGGABLE_SOURCES)
def test_prefilter_keeps_every_flaggable_kind(name, source):
    assert lint._may_produce_python_findings(source) is True
    assert lint.scan_python(source, name)


def test_prefilter_skips_sources_without_findings():
    assert lint._may_produce_python_findings("VALUE = 1\n") is False
    assert lint._may_produce_python_findings('VALUE = "("\n') is False


def test_scan_parses_only_files_that_can_yield_findings(tmp_path, monkeypatch):
    for index in range(20):
        clean = tmp_path / "scripts" / f"clean{index}.py"
        clean.parent.mkdir(parents=True, exist_ok=True)
        clean.write_text(f"VALUE = {index}\n")
    # Brackets inside strings make the crude balance count unequal; the precision
    # recheck must drop this file from the parse set.
    (tmp_path / "scripts" / "string_bracket.py").write_text('VALUE = "("\n')
    flaggable = {
        "literal.py": f'ROOT = "{LITERAL}/x"\n',
        "producer.py": "import tempfile\ntempfile.mkdtemp()\n",
        "escaped.py": 'ROOT = "\\x2ftmp/x"\n',
        "split.py": 'ROOT = "/t" "mp/x"\n',
        "multiline.py": 'VALUE = """\n' + f"{LITERAL}/multi\n" + '"""\n',
    }
    for name, text in flaggable.items():
        (tmp_path / "scripts" / name).write_text(text)

    parsed: list[str] = []
    original_parse = lint.ast.parse

    def tracking_parse(source, *args, **kwargs):
        parsed.append(kwargs.get("filename", ""))
        return original_parse(source, *args, **kwargs)

    monkeypatch.setattr(lint.ast, "parse", tracking_parse)
    lint.scan_lines(tmp_path)

    assert sorted(parsed) == sorted(f"scripts/{name}" for name in flaggable)
