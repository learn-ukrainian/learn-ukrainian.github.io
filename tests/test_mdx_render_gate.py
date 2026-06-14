"""Tests for the mdx_render gate + the template-literal escape fix (#3137).

The render gate uses Node (the real JS engine) to evaluate every JSON.parse(`…`)
island prop, so the Node-dependent tests skip cleanly where Node is unavailable.
"""

from __future__ import annotations

import json
import shutil

import pytest

from scripts.build.mdx_render_gate import check_mdx_render, iter_template_literals
from scripts.generate_mdx.utils import dump_json_for_jsx

node_required = pytest.mark.skipif(
    shutil.which("node") is None, reason="node not available"
)


# --- extraction (pure python, no node) ---------------------------------------

def test_iter_template_literals_extracts_each_inner():
    mdx = 'a <X p={JSON.parse(`[1,2]`)} /> b <Y q={JSON.parse(`{"k":1}`)} />'
    assert iter_template_literals(mdx) == ["[1,2]", '{"k":1}']


def test_iter_template_literals_respects_escaped_backtick():
    # an escaped backtick inside a correctly-escaped payload must not end it early
    mdx = r'<X p={JSON.parse(`["a\`b"]`)} />'
    assert iter_template_literals(mdx) == [r'["a\`b"]']


def test_iter_template_literals_none_when_absent():
    assert iter_template_literals("plain text, no islands") == []


def test_iter_template_literals_skips_unterminated():
    # truncated JSON.parse(` with no closing backtick → no phantom rest-of-file island
    assert iter_template_literals("x <X p={JSON.parse(`[1,2,3]") == []
    # a terminated island before an unterminated one is still captured
    assert iter_template_literals("<A p={JSON.parse(`[1]`)} /> <B q={JSON.parse(`[2") == ["[1]"]


# --- the #3137 escape bug: caught by the gate --------------------------------

@node_required
def test_canonical_escaper_round_trips_every_tricky_char():
    # " ` ${ \ and newline — each one breaks a naive template-literal embed
    payload = [{"w": 'ка"з"ка', "n": "back\\slash", "t": "x${y}", "k": "a`b", "m": "l1\nl2"}]
    mdx = f"<VocabCard words={{JSON.parse(`{dump_json_for_jsx(payload, compact=True)}`)}} />"
    report = check_mdx_render(mdx)
    assert report["passed"] is True, report
    assert report["islands_checked"] == 1


@node_required
def test_under_escaped_quote_is_caught():
    # the exact pre-#3137 resources.py bug: backtick/${-only escaping (NO backslash
    # doubling) on a value containing a literal " — must FAIL the render gate.
    bad = (
        json.dumps([{"w": 'a"b'}], ensure_ascii=False, separators=(",", ":"))
        .replace("`", "\\`")
        .replace("${", "\\${")
    )
    mdx = f"<VocabCard words={{JSON.parse(`{bad}`)}} />"
    report = check_mdx_render(mdx)
    assert report["passed"] is False
    assert report["failures"]


@node_required
def test_renderers_duplicate_escaper_round_trips():
    # the second (flat) dump_json_for_jsx, after dropping its un-escape line (#3137)
    from scripts.generate_mdx.generate_mdx_direct_renderers import (
        dump_json_for_jsx as flat_dump,
    )

    payload = [{"w": 'він "сказав"', "m": "рядок1\nрядок2", "p": "a`b"}]
    mdx = f"<X items={{JSON.parse(`{flat_dump(payload)}`)}} />"
    assert check_mdx_render(mdx)["passed"] is True


@node_required
def test_sentinel_catches_template_interpolation():
    # an unescaped ${...} that would run code (escaper bypass) must FAIL, not pass
    mdx = "<X p={JSON.parse(`${process.exit(0)}`)} />"
    assert check_mdx_render(mdx)["passed"] is False


@node_required
def test_clean_payload_passes():
    payload = [{"word": "коляда", "translation": "carol"}]
    mdx = f"<VocabCard words={{JSON.parse(`{dump_json_for_jsx(payload)}`)}} />"
    assert check_mdx_render(mdx)["passed"] is True


# --- graceful degradation -----------------------------------------------------

def test_escaper_rejects_nonfinite():
    # NaN/Infinity are invalid JSON — must fail fast at assembly, not emit bad JSON
    with pytest.raises(ValueError):
        dump_json_for_jsx([{"v": float("nan")}])
    with pytest.raises(ValueError):
        dump_json_for_jsx([{"v": float("inf")}], compact=True)


def test_node_absent_skips_not_fails(monkeypatch):
    import scripts.build.mdx_render_gate as g

    monkeypatch.setattr(g.shutil, "which", lambda *_: None)
    report = g.check_mdx_render("<X p={JSON.parse(`[1]`)} />")
    assert report["passed"] is None
    assert report["skipped"] is True
