"""Unit->output mapping carried through generate_mdx (scripts/generate_mdx/unit_map.py)."""

from __future__ import annotations

import pytest

from scripts.generate_mdx import converters, resources, utils
from scripts.generate_mdx.core import generate_mdx
from scripts.generate_mdx.unit_map import (
    CODEC_JS_JSON_STRING,
    LOST_REMOVED,
    LOST_REWRITTEN,
    Edit,
    EditLog,
    LessonUnitMap,
    UnitMapError,
    apply_edits,
    decode_js_json_string,
    encode_js_json_string,
)

# ---------------------------------------------------------------------------
# Edit records
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# The map
# ---------------------------------------------------------------------------


def test_carry_shifts_removes_and_rewrites_units() -> None:
    text = "# t\n\nслово\n\nдва\n"
    m = LessonUnitMap(text)
    m.track(0, 0, 3, "# t")
    m.track(1, 5, 10, "слово")
    m.track(2, 12, 15, "два")
    after = "слово\n\nдв\n"
    m.carry(text, after, "edit", [Edit(0, 5, ""), Edit(14, 15, "")])
    assert (m.units[0].lost_kind, m.units[0].lost_by) == (LOST_REMOVED, "edit")
    assert (m.units[1].start, m.units[1].end) == (0, 5)
    assert (m.units[2].lost_kind, m.units[2].lost_by) == (LOST_REWRITTEN, "edit")
    with pytest.raises(UnitMapError) as exc_info:
        m.verify(after)
    assert exc_info.value.kind == LOST_REMOVED and exc_info.value.key == 0
    assert "transform 'edit' removed the bytes of unit 0 ('# t')" in exc_info.value.message


def test_carry_moves_units_by_position_only() -> None:
    # Reviewer reproduction (r5 BLOCKER): two identical lines, the first tracked and removed.
    # The unit is lost; it is never re-attached to the identical surviving line.
    text = "# слово\n# слово\n\nrest"
    m = LessonUnitMap(text)
    m.track("first", 0, 7, "# слово")
    m.carry(text, "# слово\n\nrest", "remove_duplicate_h1", [Edit(0, 8, "")])
    assert (m.units["first"].lost_kind, m.units["first"].lost_by) == (LOST_REMOVED, "remove_duplicate_h1")
    # A duplicate paragraph whose second copy is removed: the first stays at its offset, the
    # second is lost; duplicates in an untouched region stay mapped at their shifted offsets.
    text = "слово\n\nслово\n\nдва\nдва\n"
    m = LessonUnitMap(text)
    m.track(1, 0, 5, "слово")
    m.track(2, 7, 12, "слово")
    m.track(3, 14, 17, "два")
    m.track(4, 18, 21, "два")
    after = "слово\n\nдва\nдва\n"
    m.carry(text, after, "strip", [Edit(7, 14, "")])
    assert (m.units[1].start, m.units[1].end) == (0, 5)
    assert (m.units[2].lost_kind, m.units[2].lost_by) == (LOST_REMOVED, "strip")
    assert (m.units[3].start, m.units[3].end) == (7, 10)
    assert (m.units[4].start, m.units[4].end) == (11, 14)
    del m.units[2]
    assert m.verify(after) == {1: "слово", 3: "два", 4: "два"}
    # Insertions: at the unit's start it shifts, inside it the unit is rewritten (split).
    m = LessonUnitMap("ab cd")
    m.track("ab", 0, 2, "ab")
    m.track("cd", 3, 5, "cd")
    m.carry("ab cd", "Xab cXd", "ins", [Edit(0, 0, "X"), Edit(4, 4, "X")])
    assert (m.units["ab"].start, m.units["ab"].end) == (1, 3)
    assert m.units["cd"].lost_kind == LOST_REWRITTEN


def test_carry_rejects_edits_that_do_not_produce_the_output() -> None:
    m = LessonUnitMap("abc")
    m.track("u", 0, 3, "abc")
    with pytest.raises(ValueError):
        m.carry("xyz", "abc", "t", [])
    with pytest.raises(ValueError):
        m.carry("abc", "ab", "t", [])  # no edits reported, but the text changed
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
    end = start + len(encoded)
    appended = page[:end] + "!" + page[end:]
    m.carry(page, appended, "append", [Edit(end, end, "!")])
    assert m.verify(appended) == {7: text}
    edited = appended[: end - 1] + "!" + appended[end:]
    m.carry(appended, edited, "edit", [Edit(end - 1, end, "!")])
    with pytest.raises(UnitMapError) as exc_info:
        m.verify(edited)
    assert exc_info.value.kind == LOST_REWRITTEN and exc_info.value.transform == "edit"


# ---------------------------------------------------------------------------
# Transforms report their edits; the recorded path equals the plain one byte for byte
# ---------------------------------------------------------------------------

_TRANSFORMS = {
    "convert_folk_content_blocks": (
        converters.convert_folk_content_blocks,
        converters.edit_convert_folk_content_blocks,
    ),
    "convert_callouts": (
        lambda t: converters.convert_callouts(t, True),
        lambda log: converters.edit_convert_callouts(log, True),
    ),
    "convert_bad_form_markers": (converters.convert_bad_form_markers, converters.edit_convert_bad_form_markers),
    "fix_html_for_jsx": (utils.fix_html_for_jsx, utils.edit_fix_html_for_jsx),
    "process_story_sections": (converters.process_story_sections, converters.edit_process_story_sections),
    "process_dialogues": (converters.process_dialogues, converters.edit_process_dialogues),
    "embed_youtube_video_links": (resources.embed_youtube_video_links, resources.edit_embed_youtube_video_links),
    "normalize_mdx": (converters.normalize_mdx, converters.edit_normalize_mdx),
}

_SAMPLE = """# Title

Intro _one_ and __two__ with `_code_` and [l_ink](/a_b).
* item one
*   item two
> [!tip]
> слово два
>
> ще

[!note] lazy
lazy body

> [!solution]
> answer

### Story Time
first line
second line
— А: раз
— Б: два

> **Оксана:** Привіт!
> **Іван:** Привіт, Оксано!

**Діалог 1 — Зустріч**
> **Оксана:** Раз
> **Іван:** Два

:::myth-box
claim: a
truth: b
:::
:::primary-reading {reading="x"}
text
— «Дума»
:::
<!-- bad -->їхній<!-- /bad --> <!-- /bad --> <br> <hr/> <img src="x">
[Watch](https://www.youtube.com/watch?v=dQw4w9WgXcQ) and https://youtu.be/dQw4w9WgXcQ
{% youtubeVideo "https://www.youtube.com/watch?v=dQw4w9WgXcQ" %}
- Label: https://www.youtube.com/watch?v=dQw4w9WgXcQ
> [!video]
<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>
```
code _x_
```
## Heading
text after heading


too many blanks
"""


@pytest.mark.parametrize("name", sorted(_TRANSFORMS))
def test_transform_edits_reproduce_its_output(name: str) -> None:
    plain, recorded = _TRANSFORMS[name]
    expected = plain(_SAMPLE)
    log = EditLog(_SAMPLE)
    recorded(log)
    assert log.text == expected
    edits = log.edits()
    assert apply_edits(_SAMPLE, edits) == expected
    if name != "normalize_mdx":  # the sample is made to change under each transform
        assert edits, name
    # No transform touches the intro line (or the callout body's own bytes): a unit there
    # keeps its location by position.
    m = LessonUnitMap(_SAMPLE)
    intro = _SAMPLE.index("Intro")
    m.track("intro", intro, intro + 5, "Intro")
    body = _SAMPLE.index("слово два")
    m.track("callout", body, body + 9, "слово два")
    m.carry(_SAMPLE, expected, name, edits)
    assert m.verify(expected) == {"intro": "Intro", "callout": "слово два"}


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
    assert mdx == generate_mdx(md, 1, yaml_activities=[act], meta_data=meta, level="a1", fresh=True)
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


def test_generate_mdx_duplicate_h1_removal_never_reattaches_the_unit() -> None:
    # Reviewer reproduction (r5 BLOCKER): the tracked first `# слово` is removed by
    # remove_duplicate_h1; the identical second line survives, but the unit is lost, not
    # re-attached to it, and verify fails closed as removed.
    md = "# слово\n# слово\n\nrest"
    m = LessonUnitMap(md)
    m.track(0, 0, 7, "# слово")
    meta = {"title": "T", "subtitle": "", "prev": "/a1/", "next": "/a1/", "lesson": 1, "module_slug": "s"}
    mdx = generate_mdx(md, 1, meta_data=meta, level="a1", fresh=True, unit_map=m)
    assert "# слово\n" in mdx
    with pytest.raises(UnitMapError) as exc_info:
        m.verify(mdx)
    assert exc_info.value.kind == LOST_REMOVED and exc_info.value.transform == "remove_duplicate_h1"
    assert exc_info.value.key == 0
    # The second (untracked) copy is the one on the page; a unit tracked there is found.
    m = LessonUnitMap(md)
    m.track(1, 8, 15, "# слово")
    mdx = generate_mdx(md, 1, meta_data=meta, level="a1", fresh=True, unit_map=m)
    assert m.verify(mdx) == {1: "# слово"}


def test_generate_mdx_duplicate_paragraph_in_a_removed_section() -> None:
    # The Вправи section is stripped; its paragraph is an exact copy of paragraphs before and
    # after it. Only the unit in the removed section is lost; the others keep their positions.
    md = "## A\n\nслово\n\n## Вправи\n\nслово\n\n## B\n\nслово\n"
    m = LessonUnitMap(md)
    for key, start in zip((1, 2, 3), [i for i in range(len(md)) if md.startswith("слово", i)], strict=True):
        m.track(key, start, start + 5, "слово")
    meta = {"title": "T", "subtitle": "", "prev": "/a1/", "next": "/a1/", "lesson": 1, "module_slug": "s"}
    mdx = generate_mdx(md, 1, meta_data=meta, level="a1", fresh=True, unit_map=m)
    assert "Вправи" not in mdx.split('<TabItem label="Урок — Lesson">')[1].split("</TabItem>")[0]
    with pytest.raises(UnitMapError) as exc_info:
        m.verify(mdx)
    assert exc_info.value.key == 2 and exc_info.value.kind == LOST_REMOVED
    assert exc_info.value.transform == "strip_activities_section"
    del m.units[2]
    assert m.verify(mdx) == {1: "слово", 3: "слово"}
    assert m.units[1].start < m.units[3].start


# ---------------------------------------------------------------------------
# No-op and partial replacements (r6 BLOCKER: unchanged text reported as removed)
# ---------------------------------------------------------------------------

_META = {"title": "T", "subtitle": "", "prev": "/a1/", "next": "/a1/", "lesson": 1, "module_slug": "s"}


def _track_and_generate(md: str, unit: str, *, key: str = "u"):
    m = LessonUnitMap(md)
    start = md.index(unit)
    m.track(key, start, start + len(unit), unit)
    mdx = generate_mdx(md, 1, meta_data=_META, level="a1", fresh=True, unit_map=m)
    return m, mdx


def test_edit_log_records_no_edit_for_a_replacement_equal_to_its_match() -> None:
    for repl in (lambda match: match.group(0), r"\g<0>", "abc"):
        log = EditLog("x abc y")
        log.sub(r"abc", repl)
        assert log.text == "x abc y" and log.edits() == []
    # Explicit edits and a replacement that undoes an earlier one are also no-ops.
    log = EditLog("x abc y")
    log.apply([Edit(2, 5, "abc")])
    log.replace(2, 5, "Q")
    log.replace(2, 3, "abc")
    assert log.text == "x abc y" and log.edits() == []


def test_a_real_replacement_over_a_tracked_unit_still_invalidates_it() -> None:
    log = EditLog("x abc y")
    log.sub("abc", lambda match: "abd")
    m = LessonUnitMap("x abc y")
    m.track("u", 2, 5, "abc")
    m.carry_log(log, "swap")
    with pytest.raises(UnitMapError) as exc_info:
        m.verify("x abd y")
    assert exc_info.value.kind == LOST_REWRITTEN and exc_info.value.transform == "swap"
    # Deleting the whole unit is still a removal.
    log = EditLog("x abc y")
    log.sub("abc", lambda match: "")
    m = LessonUnitMap("x abc y")
    m.track("u", 2, 5, "abc")
    m.carry_log(log, "drop")
    with pytest.raises(UnitMapError) as exc_info:
        m.verify("x  y")
    assert exc_info.value.kind == LOST_REMOVED


def test_a_replacement_that_changes_only_a_suffix_keeps_the_prefix_unit_located() -> None:
    log = EditLog("x abcdef y")
    log.sub("abcdef", lambda match: "abcXYZ")
    m = LessonUnitMap("x abcdef y")
    m.track("prefix", 2, 5, "abc")
    m.track("suffix", 5, 8, "def")
    m.carry_log(log, "tail")
    assert (m.units["prefix"].start, m.units["prefix"].end) == (2, 5)
    assert m.units["suffix"].lost_kind == LOST_REMOVED
    del m.units["suffix"]
    assert m.verify("x abcXYZ y") == {"prefix": "abc"}


def test_generate_mdx_keeps_a_youtube_link_in_a_table_cell_mapped() -> None:
    # Reviewer reproduction (r6 BLOCKER a): embed_youtube_video_links leaves table links
    # alone, so the link stays on the page and the unit must verify.
    link = "[Video](https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
    md = f"# T\n\n| Назва | Посилання |\n| --- | --- |\n| слово | {link} |\n\nend"
    m, mdx = _track_and_generate(md, link)
    assert link in mdx
    assert m.verify(mdx) == {"u": link}


def test_generate_mdx_keeps_an_unresolved_slug_link_mapped() -> None:
    # Reviewer reproduction (r6 BLOCKER b): the unknown slug is returned unchanged.
    marker = "[slug:this-slug-does-not-exist]"
    md = f"# T\n\nдив. {marker} тут\n\nend"
    m, mdx = _track_and_generate(md, marker)
    assert marker in mdx
    assert m.verify(mdx) == {"u": marker}


def test_generate_mdx_still_rewrites_an_embedded_youtube_link_unit() -> None:
    link = "[Video](https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
    md = f"# T\n\n{link}\n\nend"
    m, mdx = _track_and_generate(md, link)
    assert "<YouTubeVideo" in mdx
    with pytest.raises(UnitMapError):
        m.verify(mdx)
