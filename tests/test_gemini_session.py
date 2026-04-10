"""Tests for ``scripts/build/gemini_session.py`` and ``session_analysis.py``.

Covers AC1–AC4 of issue #1174:
- Parser reads session files and extracts prompt + response
- Checklist compliance report generated
- Prompt size breakdown per phase
- Tested on a real a2-bridge-shaped session fixture
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Ensure scripts/ is importable without adjusting PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build.gemini_session import (
    extract_prompt_and_response,
    find_latest_session,
    find_session_near_time,
    list_sessions,
    parse_session,
)
from build.session_analysis import (
    _INJECT_PLACEHOLDER_FIRST_PARTS,
    _dict_to_yaml,
    analyze_prompt_sections,
    build_report,
    check_directive_coverage,
    extract_directives,
    write_report_yaml,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_session(
    tmp_path: Path,
    *,
    session_id: str = "test-session-id",
    start_time: str = "2026-04-10T21:23:18.297Z",
    messages: list[dict] | None = None,
) -> Path:
    """Write a session JSON file shaped like Gemini CLI's real output."""
    if messages is None:
        messages = [
            {
                "id": "m1",
                "timestamp": start_time,
                "type": "user",
                "content": [{"text": "# A2 bridge prompt\n\nWrite ONE section."}],
            },
            {
                "id": "m2",
                "timestamp": "2026-04-10T21:24:00.000Z",
                "type": "gemini",
                "content": [{"text": "## Пригадуємо відмінки\n\nSome content."}],
            },
        ]
    data = {
        "sessionId": session_id,
        "projectHash": "test-hash",
        "startTime": start_time,
        "lastUpdated": "2026-04-10T21:24:00.000Z",
        "messages": messages,
        "kind": "chat",
    }
    path = tmp_path / f"session-{start_time.replace(':', '-')}-abc.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_parse_session_extracts_messages(tmp_path):
    path = _make_session(tmp_path)
    session = parse_session(path)
    assert session.session_id == "test-session-id"
    assert session.start_time == datetime(
        2026, 4, 10, 21, 23, 18, 297000, tzinfo=UTC
    )
    assert len(session.messages) == 2
    assert session.messages[0].type == "user"
    assert "Write ONE section" in session.messages[0].text
    assert session.messages[1].type == "gemini"
    assert "Пригадуємо відмінки" in session.messages[1].text


def test_parse_session_handles_prompt_only(tmp_path):
    """Real Gemini sessions sometimes only contain the user prompt (if the
    call crashed before a response landed). Parser must not explode."""
    path = _make_session(
        tmp_path,
        messages=[
            {
                "id": "m1",
                "timestamp": "2026-04-10T21:23:18.297Z",
                "type": "user",
                "content": [{"text": "just a prompt"}],
            }
        ],
    )
    session = parse_session(path)
    assert len(session.messages) == 1
    prompt, response = extract_prompt_and_response(session)
    assert prompt == "just a prompt"
    assert response == ""


def test_parse_session_handles_multi_part_content(tmp_path):
    """Content may be a list of multiple text parts — we concatenate them."""
    path = _make_session(
        tmp_path,
        messages=[
            {
                "id": "m1",
                "timestamp": "2026-04-10T21:23:18.297Z",
                "type": "user",
                "content": [{"text": "part one "}, {"text": "part two"}],
            }
        ],
    )
    session = parse_session(path)
    assert session.messages[0].text == "part one part two"


def test_parse_session_tolerates_malformed_json(tmp_path):
    path = tmp_path / "session-broken.json"
    path.write_text("this is not json", encoding="utf-8")
    session = parse_session(path)
    assert session.messages == []
    assert session.start_time is None


def test_extract_prompt_and_response_returns_first_of_each(tmp_path):
    path = _make_session(
        tmp_path,
        messages=[
            {
                "id": "m1",
                "timestamp": "2026-04-10T21:23:18.297Z",
                "type": "user",
                "content": [{"text": "first user"}],
            },
            {
                "id": "m2",
                "timestamp": "2026-04-10T21:23:19.000Z",
                "type": "gemini",
                "content": [{"text": "first model"}],
            },
            {
                "id": "m3",
                "timestamp": "2026-04-10T21:23:20.000Z",
                "type": "user",
                "content": [{"text": "second user"}],
            },
        ],
    )
    session = parse_session(path)
    prompt, response = extract_prompt_and_response(session)
    assert prompt == "first user"
    assert response == "first model"


# ---------------------------------------------------------------------------
# Session lookup helpers
# ---------------------------------------------------------------------------

def test_list_sessions_empty_when_dir_missing(monkeypatch, tmp_path):
    """Gracefully handle environments where Gemini CLI was never run."""
    monkeypatch.setattr(
        "build.gemini_session.GEMINI_CHATS_ROOT", tmp_path / "nonexistent"
    )
    assert list_sessions("learn-ukrainian") == []
    assert find_latest_session("learn-ukrainian") is None


def test_find_latest_session_returns_newest(monkeypatch, tmp_path):
    chats_dir = tmp_path / "fake-gemini" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "build.gemini_session.GEMINI_CHATS_ROOT", tmp_path / "fake-gemini"
    )

    # Create two sessions with different mtimes
    older = _make_session(
        chats_dir, start_time="2026-04-09T10-00-00.000Z", session_id="older"
    )
    newer = _make_session(
        chats_dir, start_time="2026-04-10T10-00-00.000Z", session_id="newer"
    )
    import os
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    latest = find_latest_session("learn-ukrainian")
    assert latest == newer


def test_find_session_near_time_matches_closest(monkeypatch, tmp_path):
    chats_dir = tmp_path / "fake-gemini" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "build.gemini_session.GEMINI_CHATS_ROOT", tmp_path / "fake-gemini"
    )

    _make_session(
        chats_dir, start_time="2026-04-10T21:20:00.000Z", session_id="s1"
    )
    closest = _make_session(
        chats_dir, start_time="2026-04-10T21:23:18.000Z", session_id="closest"
    )
    _make_session(
        chats_dir, start_time="2026-04-10T21:40:00.000Z", session_id="s3"
    )

    target = datetime(2026, 4, 10, 21, 23, 20, tzinfo=UTC)
    matched = find_session_near_time(target, max_drift_s=60.0)
    assert matched == closest


def test_find_session_near_time_rejects_outside_window(
    monkeypatch, tmp_path
):
    chats_dir = tmp_path / "fake-gemini" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "build.gemini_session.GEMINI_CHATS_ROOT", tmp_path / "fake-gemini"
    )
    _make_session(
        chats_dir, start_time="2026-04-10T12:00:00.000Z", session_id="far"
    )

    target = datetime(2026, 4, 10, 21, 23, 20, tzinfo=UTC)
    # Session is hours away; with a 5-minute window, no match.
    assert find_session_near_time(target, max_drift_s=300.0) is None


def test_find_session_near_time_skips_naive_targets(
    monkeypatch, tmp_path
):
    chats_dir = tmp_path / "fake-gemini" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "build.gemini_session.GEMINI_CHATS_ROOT", tmp_path / "fake-gemini"
    )
    _make_session(chats_dir)
    # Passing a naive datetime must not crash (would otherwise TypeError
    # on subtraction with an aware datetime).
    naive = datetime(2026, 4, 10, 21, 23, 18)
    assert find_session_near_time(naive) is None


# ---------------------------------------------------------------------------
# Prompt section analysis
# ---------------------------------------------------------------------------

def test_analyze_prompt_sections_detects_major_blocks():
    prompt = (
        "# Section-by-Section Generation — Section 1/4\n"
        "Preamble text here.\n\n"
        "## Section Skeleton (follow this exactly)\n"
        "- P1 (~120 words): [topic one]\n"
        "- P2 (~100 words): [topic two]\n\n"
        "## Full Plan (for reference)\n"
        "plan body goes here with several lines\n" * 20
        + "\n## Knowledge Packet\n"
        + "wiki content here\n" * 50
        + "\n## Output\n"
        "Write the section.\n"
    )
    sections = analyze_prompt_sections(prompt)
    names = [s.name for s in sections]
    assert "header" in names
    assert "skeleton" in names
    assert "plan" in names
    assert "wiki" in names
    assert "output_spec" in names
    # Every section should be non-empty
    assert all(s.length > 0 for s in sections)
    # Fractions should sum to approximately 1.0
    assert abs(sum(s.fraction for s in sections) - 1.0) < 0.01


def test_analyze_prompt_sections_flags_oversized_wiki():
    # Wiki packet dominates the prompt — should be flagged as > 40%.
    prompt = (
        "# Section-by-Section Generation\nbrief header\n"
        "## Full Plan\nshort plan\n"
        "## Knowledge Packet\n" + ("wiki content line\n" * 1000)
        + "## Output\nwrite it"
    )
    report = build_report(
        prompt, response="ok", phase="write", session_path="test",
    )
    assert "wiki" in report.large_sections


def test_analyze_prompt_sections_empty():
    assert analyze_prompt_sections("") == []


def test_analyze_prompt_sections_unknown_prompt():
    """If no markers match, the whole thing is one 'unknown' blob."""
    result = analyze_prompt_sections("just some text with no markers")
    assert len(result) == 1
    assert result[0].name == "unknown"
    assert result[0].fraction == 1.0


# ---------------------------------------------------------------------------
# Directive extraction + coverage
# ---------------------------------------------------------------------------

def test_extract_directives_checklist_items():
    prompt = (
        "Requirements:\n"
        "- [ ] Include дж/дз affricates\n"
        "- [x] Cover case alternations\n"
        "* [ ] Mention euphonic rules\n"
    )
    directives = extract_directives(prompt)
    checklist = [d for d in directives if d.kind == "checklist"]
    assert len(checklist) == 3
    assert any("дж/дз" in d.text for d in checklist)
    assert any("euphonic" in d.text for d in checklist)


def test_extract_directives_must_sentences():
    prompt = (
        "Each section MUST contain at least one callout. "
        "The module as a whole MUST have 3+ callouts. "
        "Activities are REQUIRED for every section."
    )
    must = [d for d in extract_directives(prompt) if d.kind == "must"]
    assert len(must) >= 2
    assert all("MUST" in d.text or "REQUIRED" in d.text for d in must)


def test_extract_directives_skeleton_paragraphs():
    prompt = (
        "## Section Skeleton\n"
        "- P1 (~120 words): [Dialogue: arrival at Kyiv school]\n"
        "- P2 (~80 words): [Conceptual overview of declension]\n"
    )
    paras = [
        d for d in extract_directives(prompt) if d.kind == "skeleton_para"
    ]
    assert len(paras) == 2
    assert "P1 (120w)" in paras[0].text
    assert "Dialogue" in paras[0].text


def test_extract_directives_inject_activity_filters_placeholders():
    prompt = (
        "<!-- INJECT_ACTIVITY: type, topic hint, count items -->\n"  # placeholder
        "<!-- INJECT_ACTIVITY: fill-in, Case Drill, 8 items -->\n"  # real
    )
    activities = [
        d for d in extract_directives(prompt) if d.kind == "inject_activity"
    ]
    assert len(activities) == 1
    assert "fill-in" in activities[0].text


def test_check_directive_coverage_skeleton_para_keyword_match():
    directives = extract_directives(
        "- P1 (~120 words): [Dialogue: arrival at Kyiv school, Nominative, Accusative]"
    )
    response = (
        "## Introduction\nThe dialogue shows a student arriving in Kyiv, "
        "introducing themselves using Nominative case and describing what "
        "they study with Accusative."
    )
    checked = check_directive_coverage(directives, response)
    assert checked[0].covered is True
    assert "keywords" in checked[0].coverage_note


def test_check_directive_coverage_flags_missing_activity_marker():
    directives = extract_directives(
        "<!-- INJECT_ACTIVITY: quiz, Case Identification Drill, 8 items -->"
    )
    response = "The response contains no activity marker at all."
    checked = check_directive_coverage(directives, response)
    assert checked[0].covered is False
    assert "marker missing" in checked[0].coverage_note


def test_check_directive_coverage_preserves_activity_marker():
    directives = extract_directives(
        "<!-- INJECT_ACTIVITY: quiz, Case Drill, 8 items -->"
    )
    response = (
        "Some content.\n<!-- INJECT_ACTIVITY: quiz, Case Drill, 8 items -->"
    )
    checked = check_directive_coverage(directives, response)
    assert checked[0].covered is True


def test_check_directive_coverage_empty_response():
    directives = [extract_directives("- [ ] Cover cases")[0]]
    checked = check_directive_coverage(directives, "")
    assert checked[0].covered is False
    assert checked[0].coverage_note == "empty response"


def test_check_directive_coverage_missing_keywords_fails():
    """A skeleton para whose topic is absent from the response should fail."""
    directives = extract_directives(
        "- P1 (~120 words): [Trypillian civilization pottery archaeology]"
    )
    response = "This section is about vocabulary and grammar."
    checked = check_directive_coverage(directives, response)
    # None of the topic keywords appear in the response → not covered
    assert checked[0].covered is False


# ---------------------------------------------------------------------------
# Report building + YAML emission
# ---------------------------------------------------------------------------

def test_build_report_end_to_end(tmp_path):
    prompt = (
        "# Section-by-Section Generation — Section 1/4\n"
        "## Section Skeleton (follow this exactly)\n"
        "- P1 (~100 words): [Nominative case review]\n"
        "- P2 (~100 words): [Accusative case review]\n"
        "<!-- INJECT_ACTIVITY: quiz, Case Drill, 8 items -->\n"
        "## Full Plan\n"
        + "plan content\n" * 30
        + "## Knowledge Packet\n"
        + "wiki\n" * 200
        + "## Output\nWrite it."
    )
    response = (
        "## Cases\nThe Nominative case marks the subject. "
        "The Accusative case marks the object.\n"
        "<!-- INJECT_ACTIVITY: quiz, Case Drill, 8 items -->"
    )
    report = build_report(
        prompt, response, phase="write-chunk-01", session_path="/tmp/x.json",
    )
    d = report.to_dict()
    assert d["phase"] == "write-chunk-01"
    assert d["prompt_chars"] == len(prompt)
    assert d["response_chars"] == len(response)
    assert d["directives_total"] >= 3  # 2 skeleton + 1 inject_activity
    assert d["directives_covered"] >= 2  # both skeleton paras covered
    # Wiki should dominate this synthetic prompt
    section_names = [s["name"] for s in d["sections"]]
    assert "wiki" in section_names
    # Write the YAML and verify it round-trips
    out = tmp_path / "session-analysis.yaml"
    write_report_yaml(report, out)
    assert out.exists()
    import yaml
    loaded = yaml.safe_load(out.read_text())
    assert loaded["phase"] == "write-chunk-01"
    assert loaded["prompt_chars"] == len(prompt)


def test_build_report_handles_empty_prompt_and_response():
    report = build_report("", "", phase="x", session_path="x")
    assert report.prompt_chars == 0
    assert report.response_chars == 0
    assert report.sections == []
    assert report.directives_total == 0


# ---------------------------------------------------------------------------
# YAML emitter internals
# ---------------------------------------------------------------------------

def test_dict_to_yaml_roundtrips_via_pyyaml():
    """Our minimal emitter must produce valid YAML that PyYAML can read."""
    import yaml
    obj = {
        "phase": "write",
        "prompt_chars": 123,
        "fraction": 0.42,
        "items": ["first", "second", "with: colon"],
        "nested": {"a": 1, "b": "two"},
        "empty_list": [],
        "empty_dict": {},
        "flag": True,
        "nothing": None,
    }
    text = _dict_to_yaml(obj)
    roundtripped = yaml.safe_load(text)
    assert roundtripped == obj


def test_dict_to_yaml_quotes_dangerous_strings():
    import yaml
    # Strings containing YAML-significant characters must be quoted.
    obj = {
        "with_colon": "foo: bar",
        "with_newline": "line1\nline2",
        "with_dash": "- leading dash",
        "with_digit": "1abc",
    }
    text = _dict_to_yaml(obj)
    loaded = yaml.safe_load(text)
    assert loaded == obj


def test_injection_placeholder_set_shape():
    """Belt-and-braces: the placeholder set is lowercase-only to match
    the case-folding logic in extract_directives."""
    assert all(s == s.lower() for s in _INJECT_PLACEHOLDER_FIRST_PARTS)
    assert "type" in _INJECT_PLACEHOLDER_FIRST_PARTS


# ---------------------------------------------------------------------------
# Real-session integration (only runs if Gemini CLI data exists locally)
# ---------------------------------------------------------------------------

def _real_a2_bridge_session() -> Path | None:
    candidate = Path.home() / ".gemini" / "tmp" / "learn-ukrainian" / "chats"
    if not candidate.is_dir():
        return None
    # Find any session that contains "a2-bridge" or "Section-by-Section"
    # in its first user message. Cheap heuristic — we just need one real
    # example to prove the parser works on live data.
    for path in sorted(candidate.glob("session-*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:50]:
        try:
            session = parse_session(path)
        except OSError:
            continue
        if not session.messages:
            continue
        first = session.messages[0].text
        if "Section-by-Section" in first or "a2-bridge" in first.lower():
            return path
    return None


def test_real_a2_bridge_session_parses_if_available():
    """If a real a2-bridge session exists locally (developer machine),
    verify the parser extracts sane data. Skipped in CI."""
    path = _real_a2_bridge_session()
    if path is None:
        import pytest
        pytest.skip("No real Gemini session available in this environment")
    session = parse_session(path)
    assert session.session_id
    assert session.start_time is not None
    assert len(session.messages) >= 1
    prompt, _ = extract_prompt_and_response(session)
    assert "Section-by-Section" in prompt or "Module" in prompt
    report = build_report(
        prompt, _, phase="write", session_path=path,
    )
    # Sanity: some sections should be detected in a real writer prompt
    assert len(report.sections) > 0


# ---------------------------------------------------------------------------
# Drift calculations
# ---------------------------------------------------------------------------

def test_find_session_near_time_uses_closest_when_multiple_match(
    monkeypatch, tmp_path
):
    chats_dir = tmp_path / "fake-gemini" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "build.gemini_session.GEMINI_CHATS_ROOT", tmp_path / "fake-gemini"
    )
    target = datetime(2026, 4, 10, 21, 23, 30, tzinfo=UTC)
    # Two sessions inside the 120s window — 10s away and 50s away
    _make_session(
        chats_dir, start_time="2026-04-10T21:22:40.000Z", session_id="50s"
    )
    close = _make_session(
        chats_dir, start_time="2026-04-10T21:23:20.000Z", session_id="10s"
    )
    matched = find_session_near_time(target, max_drift_s=120.0)
    assert matched == close


def test_find_session_near_time_window_is_inclusive(
    monkeypatch, tmp_path
):
    chats_dir = tmp_path / "fake-gemini" / "learn-ukrainian" / "chats"
    chats_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "build.gemini_session.GEMINI_CHATS_ROOT", tmp_path / "fake-gemini"
    )
    target = datetime(2026, 4, 10, 21, 23, 30, tzinfo=UTC)
    exactly_edge = target - timedelta(seconds=300)
    path = _make_session(
        chats_dir,
        start_time=exactly_edge.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        session_id="edge",
    )
    assert find_session_near_time(target, max_drift_s=300.0) == path
