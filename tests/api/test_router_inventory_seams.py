"""The seam figures in the router inventory must match the live `isolated_fixture` (#9630).

`docs/design/count_opsec_fixture_seams.py` runs the real fixture body against a recording
`MonkeyPatch`. The document's seam table, category totals, per-router *Seams* values and
summary row are compared with that output, so a stale or edited figure fails here.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "docs" / "design" / "count_opsec_fixture_seams.py"
INVENTORY = REPO_ROOT / "docs" / "design" / "monitor-api-router-inventory.md"

APP_STATE_OWNER = "starlette.datastructures.State"

CATEGORY_LABELS = {
    "router": "Router modules (the Seams column below)",
    "helper": "Shared API helpers (`scripts.api.*` modules that are not routers)",
    "repository": "Other repository modules (`scripts.*` outside `scripts.api`, `wiki.*`)",
    "app_state": "Application state (`app.state`)",
    "backstop": "Global backstops (`subprocess`, `socket`, `sqlite3`)",
}


def _load_script() -> Any:
    spec = importlib.util.spec_from_file_location("count_opsec_fixture_seams", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# --- parsing the document -------------------------------------------------------------


def _section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def _fixture_section(text: str) -> str:
    return _section(text, "### OPSEC fixture seams", "### Per-step module tally")


def _doc_seam_rows(text: str) -> list[dict[str, Any]]:
    rows = []
    for match in re.finditer(r"^\| `([^`]+)` \| (setattr|env) \| (\d+) \|$", _fixture_section(text), re.MULTILINE):
        owner, name = match.group(1).rsplit(".", 1)
        rows.append({"kind": match.group(2), "owner": owner, "name": name, "invocations": int(match.group(3))})
    return rows


def _doc_totals(text: str) -> dict[str, int]:
    return {
        label.replace("**", "").strip(): int(value.replace("**", ""))
        for label, value in re.findall(r"^\| ([^|]+?) \| (\*{0,2}\d+\*{0,2}) \|$", _fixture_section(text), re.MULTILINE)
    }


def _doc_router_rows(text: str) -> dict[str, int]:
    """Per-router row stem -> its *Seams* cell (the second-to-last column)."""
    section = _section(text, "## Per-router inventory", "## Summary accounting")
    rows = {}
    for line in section.splitlines():
        match = re.match(r"^\| `([a-z_.]+)\.py`(?: \(`[a-z_]+`\))? \| (.+) \|$", line)
        if match:
            rows[match.group(1)] = int(match.group(2).split(" | ")[-2])
    return rows


# --- deriving the expected figures from live records ----------------------------------


def _category(seam: dict[str, Any], router_stems: set[str]) -> str:
    owner = seam["owner"]
    if owner.split(".")[0] in sys.stdlib_module_names:
        return "backstop"
    if owner.startswith("scripts.api."):
        return "router" if owner.removeprefix("scripts.api.") in router_stems else "helper"
    if owner.startswith(("scripts.", "wiki.")):
        return "repository"
    if owner == APP_STATE_OWNER:
        return "app_state"
    return f"unclassified: {owner}"


def check_seam_doc(text: str, live: list[dict[str, Any]]) -> list[str]:
    """Every disagreement between the inventory text and the live fixture records."""
    problems: list[str] = []
    router_rows = _doc_router_rows(text)
    attrs = [seam for seam in live if seam["kind"] == "setattr"]

    doc_rows = _doc_seam_rows(text)
    if doc_rows != live:
        doc_keys = {(r["kind"], r["owner"], r["name"]): r["invocations"] for r in doc_rows}
        live_keys = {(r["kind"], r["owner"], r["name"]): r["invocations"] for r in live}
        problems.append(
            f"seam table differs from the live fixture: missing {sorted(set(live_keys) - set(doc_keys))}, "
            f"stale {sorted(set(doc_keys) - set(live_keys))}, "
            f"invocation changes {sorted(k for k in doc_keys.keys() & live_keys.keys() if doc_keys[k] != live_keys[k])}"
        )

    categories = Counter(_category(seam, set(router_rows)) for seam in attrs)
    totals = _doc_totals(text)
    for key, label in CATEGORY_LABELS.items():
        if totals.get(label) != categories.get(key, 0):
            problems.append(f"{label!r}: document {totals.get(label)}, live {categories.get(key, 0)}")
    for category in categories:
        if category not in CATEGORY_LABELS:
            problems.append(f"seam category the document cannot state: {category}")
    expected_totals = {
        "Unique `setattr` targets": len(attrs),
        "`setattr` invocations": sum(seam["invocations"] for seam in attrs),
        "Environment variables set": sum(1 for seam in live if seam["kind"] == "env"),
    }
    for label, value in expected_totals.items():
        if totals.get(label) != value:
            problems.append(f"{label!r}: document {totals.get(label)}, live {value}")
    if f"### OPSEC fixture seams — **{len(attrs)}** unique `setattr` targets" not in text:
        problems.append(f"section heading does not state {len(attrs)} unique setattr targets")
    summary = f"| OPSEC fixture `setattr` targets (unique; see *OPSEC fixture seams*) | {len(attrs)} |"
    if summary not in text:
        problems.append(f"summary accounting row does not state {len(attrs)}")

    per_owner = Counter(seam["owner"] for seam in attrs)
    for stem, value in router_rows.items():
        live_value = per_owner.get(f"scripts.api.{stem}", 0)
        if value != live_value:
            problems.append(f"router row {stem}: Seams {value}, live {live_value}")
    return problems


# --- tests ----------------------------------------------------------------------------


@pytest.fixture(scope="module")
def live_seams() -> list[dict[str, Any]]:
    """The seams from a fresh interpreter, as the document's counting rules require."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    assert result.returncode == 0, result.stderr[-2000:]
    return json.loads(result.stdout)


def test_inventory_seam_figures_match_the_live_fixture(live_seams: list[dict[str, Any]]) -> None:
    assert check_seam_doc(INVENTORY.read_text(encoding="utf-8"), live_seams) == []


def test_live_records_include_the_known_fixture_seams(live_seams: list[dict[str, Any]]) -> None:
    """A recorder that silently captured nothing would make the comparison vacuous."""
    targets = {(seam["owner"], seam["name"]) for seam in live_seams if seam["kind"] == "setattr"}
    assert {
        ("subprocess", "run"),
        ("subprocess", "Popen"),
        ("socket", "create_connection"),
        ("sqlite3", "connect"),
    } <= targets
    assert ("scripts.api.issues_router", "_run_gh") in targets
    assert ("os.environ", "LU_MONITOR_HOST_ID") in {(s["owner"], s["name"]) for s in live_seams if s["kind"] == "env"}
    # The repeated explicit and loop patch of one target is a single seam with two invocations.
    assert (
        next(s for s in live_seams if (s["owner"], s["name"]) == ("scripts.api.main", "build_repository_authority"))[
            "invocations"
        ]
        == 2
    )


def test_changing_one_router_seam_value_fails_the_check(live_seams: list[dict[str, Any]]) -> None:
    text = INVENTORY.read_text(encoding="utf-8")
    edited = re.sub(r"(\| `state_router\.py` \|.*\| )2( \| 2 \|)$", r"\g<1>3\g<2>", text, count=1, flags=re.MULTILINE)
    assert edited != text
    problems = check_seam_doc(edited, live_seams)
    assert problems == ["router row state_router: Seams 3, live 2"]


def test_changing_a_zero_seam_value_fails_the_check(live_seams: list[dict[str, Any]]) -> None:
    text = INVENTORY.read_text(encoding="utf-8")
    edited = re.sub(
        r"(\| `rollover_router\.py` \|.*\| )0( \| 1 \|)$", r"\g<1>1\g<2>", text, count=1, flags=re.MULTILINE
    )
    assert edited != text
    assert check_seam_doc(edited, live_seams) == ["router row rollover_router: Seams 1, live 0"]


def test_a_stale_or_missing_table_row_fails_the_check(live_seams: list[dict[str, Any]]) -> None:
    text = INVENTORY.read_text(encoding="utf-8")
    without_row = re.sub(r"^\| `subprocess\.run` \| setattr \| 1 \|\n", "", text, count=1, flags=re.MULTILINE)
    assert without_row != text
    assert any("missing [('setattr', 'subprocess', 'run')]" in p for p in check_seam_doc(without_row, live_seams))

    extra = text.replace(
        "| `subprocess.run` | setattr | 1 |",
        "| `subprocess.run` | setattr | 1 |\n| `scripts.api.gone_router._x` | setattr | 1 |",
        1,
    )
    assert any("scripts.api.gone_router" in p for p in check_seam_doc(extra, live_seams))


def test_a_changed_invocation_total_or_category_fails_the_check(live_seams: list[dict[str, Any]]) -> None:
    text = INVENTORY.read_text(encoding="utf-8")
    edited = text.replace("| `setattr` invocations | 23 |", "| `setattr` invocations | 24 |", 1)
    assert edited != text
    assert check_seam_doc(edited, live_seams) == ["'`setattr` invocations': document 24, live 23"]

    edited = text.replace(
        "| Other repository modules (`scripts.*` outside `scripts.api`, `wiki.*`) | 10 |",
        "| Other repository modules (`scripts.*` outside `scripts.api`, `wiki.*`) | 9 |",
        1,
    )
    assert edited != text
    assert len(check_seam_doc(edited, live_seams)) == 1


def test_a_new_seam_on_an_unlisted_target_is_reported_as_missing(live_seams: list[dict[str, Any]]) -> None:
    grown = [
        *live_seams,
        {"kind": "setattr", "owner": "scripts.api.state_router", "name": "brand_new", "invocations": 1},
    ]
    problems = check_seam_doc(INVENTORY.read_text(encoding="utf-8"), grown)
    assert any("brand_new" in p for p in problems)
    assert "router row state_router: Seams 2, live 3" in problems


def test_an_unclassifiable_owner_is_reported(live_seams: list[dict[str, Any]]) -> None:
    grown = [*live_seams, {"kind": "setattr", "owner": "somewhere.else", "name": "x", "invocations": 1}]
    assert any(
        "unclassified: somewhere.else" in p for p in check_seam_doc(INVENTORY.read_text(encoding="utf-8"), grown)
    )


# --- the recorder ---------------------------------------------------------------------


def test_recorder_records_attribute_and_environment_seams_and_restores_them(monkeypatch: pytest.MonkeyPatch) -> None:
    script = _load_script()
    target = type(sys)("fake_seam_module")
    target.value = 1
    recorder = script.RecordingMonkeyPatch()
    monkeypatch.delenv("COUNT_SEAMS_PROBE", raising=False)

    recorder.setattr(target, "value", 2)
    recorder.setattr(target, "value", 3)
    recorder.setenv("COUNT_SEAMS_PROBE", "x")
    assert target.value == 3 and os.environ["COUNT_SEAMS_PROBE"] == "x"
    recorder.undo()

    assert target.value == 1 and "COUNT_SEAMS_PROBE" not in os.environ
    assert script.summarize(recorder.calls) == [
        {"kind": "env", "owner": "os.environ", "name": "COUNT_SEAMS_PROBE", "invocations": 1},
        {"kind": "setattr", "owner": "fake_seam_module", "name": "value", "invocations": 2},
    ]


def test_recorder_names_an_instance_target_by_its_class() -> None:
    script = _load_script()

    class Holder:
        field = 0

    recorder = script.RecordingMonkeyPatch()
    holder = Holder()
    recorder.setattr(holder, "field", 1)
    recorder.undo()
    assert recorder.calls == [("setattr", f"{Holder.__module__}.{Holder.__qualname__}", "field")]


def test_recorder_refuses_seam_kinds_it_does_not_record(tmp_path: Path) -> None:
    script = _load_script()
    recorder = script.RecordingMonkeyPatch()
    with pytest.raises(TypeError, match="dotted-string"):
        recorder.setattr("os.getcwd", lambda: "x")
    with pytest.raises(TypeError, match="setitem"):
        recorder.setitem({}, "k", "v")
    with pytest.raises(TypeError, match="delitem"):
        recorder.delitem({}, "k")
    with pytest.raises(TypeError, match="chdir"):
        recorder.chdir(tmp_path)
    with pytest.raises(TypeError, match="syspath_prepend"):
        recorder.syspath_prepend(str(tmp_path))
    recorder.undo()
    assert recorder.calls == []
