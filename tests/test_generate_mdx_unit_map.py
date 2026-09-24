"""Unit->output mapping carried through generate_mdx (scripts/generate_mdx/unit_map.py)."""

from __future__ import annotations

import pytest

from scripts.generate_mdx.core import generate_mdx
from scripts.generate_mdx.unit_map import (
    CODEC_JS_JSON_STRING,
    LOST_REMOVED,
    LOST_REWRITTEN,
    LessonUnitMap,
    UnitMapError,
    decode_js_json_string,
    encode_js_json_string,
    equal_regions,
)


def test_equal_regions_identity_prefix_suffix_and_middle() -> None:
    assert equal_regions("abc", "abc") == [(0, 0, 3)]
    assert equal_regions("", "") == []
    # Insertion in the middle: prefix and suffix survive as two regions.
    assert equal_regions("ab\ncd\n", "ab\nX\ncd\n") == [(0, 0, 3), (3, 5, 3)]
    # A line replaced inside: the line-level diff pairs the changed lines and the character
    # diff inside them finds the bytes that stayed.
    regions = equal_regions("> [!note]\n> слово\nend\n", ":::note[Note]\nслово\n:::\nend\n")
    assert (12, 14, 5) in regions  # "слово" kept its bytes
    # Blank lines never anchor the alignment: three callouts in a row stay paired in order even
    # though every content line changes (the r5 reproduction that misattributed the tip).
    before = "".join(f"> [!{k}]\n> слово {k}\n\n" for k in ("note", "tip", "summary"))
    after = "".join(f":::{k}[T]\nслово {k}\n:::\n\n" for k in ("note", "tip", "summary"))
    for k in ("note", "tip", "summary"):
        b = before.index(f"слово {k}")
        assert any(
            bs <= b and b + 5 <= bs + n and after[a_s + b - bs : a_s + b - bs + 5] == "слово"
            for bs, a_s, n in equal_regions(before, after)
        )


def test_carry_shifts_removes_and_rewrites_units() -> None:
    text = "# t\n\nслово\n\nдва\n"
    m = LessonUnitMap(text)
    m.track(0, 0, 3, "# t")
    m.track(1, 5, 10, "слово")
    m.track(2, 12, 15, "два")
    after = "слово\n\nдв\n"
    m.carry(text, after, "edit")
    assert (m.units[0].lost_kind, m.units[0].lost_by) == (LOST_REMOVED, "edit")
    assert (m.units[1].start, m.units[1].end) == (0, 5)
    assert (m.units[2].lost_kind, m.units[2].lost_by) == (LOST_REWRITTEN, "edit")
    with pytest.raises(UnitMapError) as exc_info:
        m.verify(after)
    assert exc_info.value.kind == LOST_REMOVED and exc_info.value.key == 0
    assert "transform 'edit' removed the bytes of unit 0 ('# t')" in exc_info.value.message


def test_carry_rejects_text_it_was_not_carried_to() -> None:
    m = LessonUnitMap("abc")
    m.track("u", 0, 3, "abc")
    with pytest.raises(ValueError):
        m.carry("xyz", "abc", "t")
    with pytest.raises(ValueError):
        m.verify("abd")
    with pytest.raises(ValueError):
        m.track("u", 0, 1, "a")
    with pytest.raises(ValueError):
        m.track("v", 0, 2, "ac")


def test_js_json_string_codec_round_trips_and_is_verified() -> None:
    text = "а'б\"в\\г\nд `е` ${ж}"
    encoded = encode_js_json_string(text)
    assert decode_js_json_string(encoded) == text
    assert encode_js_json_string("а") + encode_js_json_string("'б") == encode_js_json_string("а'б")
    page = 'x={JSON.parse(\'[{"text":"' + encoded + "\"}]')}"
    m = LessonUnitMap(page)
    start = page.index(encoded)
    m.track(7, start, start + len(encoded), text, CODEC_JS_JSON_STRING)
    assert m.verify(page) == {7: text}
    # Bytes appended after the unit leave it in place; bytes changed inside it lose it.
    m.carry(page, page.replace(encoded, encoded + "!"), "append")
    assert m.verify(page.replace(encoded, encoded + "!")) == {7: text}
    m.carry(page.replace(encoded, encoded + "!"), page.replace(encoded, encoded[:-1] + "!"), "edit")
    with pytest.raises(UnitMapError) as exc_info:
        m.verify(page.replace(encoded, encoded[:-1] + "!"))
    assert exc_info.value.kind == LOST_REWRITTEN and exc_info.value.transform == "edit"


def test_adopt_merges_maps_in_the_same_coordinates() -> None:
    a = LessonUnitMap("one two")
    a.track("a", 0, 3, "one")
    b = LessonUnitMap("one two")
    b.track("b", 4, 7, "two")
    a.adopt(b)
    assert a.verify("one two") == {"a": "one", "b": "two"}
    c = LessonUnitMap("other")
    with pytest.raises(ValueError):
        a.adopt(c)


def test_generate_mdx_carries_units_and_tracks_activity_jsx() -> None:
    from scripts.yaml_activities import ActivityParser

    parser = ActivityParser()
    act = parser._parse_activity(
        {
            "type": "quiz",
            "id": "q1",
            "instruction": "Pick",
            "items": [{"question": "слово?", "options": ["слово", "слова"], "correct": 0, "explanation": "E"}],
        }
    )
    md = "# Title\n\nслово один\n\n> [!tip]\n> слово два\n\n<!-- INJECT_ACTIVITY: q1 -->\n\nслово три"
    m = LessonUnitMap(md)
    m.track("h", 0, 7, "# Title")
    m.track(1, md.index("слово один"), md.index("слово один") + 10, "слово один")
    m.track(2, md.index("слово два"), md.index("слово два") + 9, "слово два")
    m.track(3, md.index("слово три"), md.index("слово три") + 9, "слово три")
    meta = {"title": "T", "subtitle": "", "prev": "/a1/", "next": "/a1/", "lesson": 1, "module_slug": "s"}
    mdx = generate_mdx(md, 1, yaml_activities=[act], meta_data=meta, level="a1", fresh=True, unit_map=m)
    with pytest.raises(UnitMapError) as exc_info:
        m.verify(mdx)
    assert exc_info.value.key == "h" and exc_info.value.transform == "remove_duplicate_h1"
    del m.units["h"]
    found = m.verify(mdx)
    assert found[1] == "слово один" and found[2] == "слово два" and found[3] == "слово три"
    assert found[("activity", "q1", 0)] == parser._activity_to_mdx(act, True)
    assert ":::tip[" in mdx and "> [!tip]" not in mdx
    # The Lesson-tab block is the one carrying learner text; the workbook tab has a cross-ref.
    assert ("activity", "q1", "vpravy") not in found
    assert mdx.index(found[2]) < mdx.index(found[("activity", "q1", 0)]) < mdx.index(found[3])
