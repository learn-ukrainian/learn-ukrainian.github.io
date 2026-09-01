"""Run the launcher handoff-identity fixtures under the required pytest gate.

``scripts/audit/test_handoff_identity.sh`` exercises
``scripts/lib/handoff_identity.sh`` — the derivation that ``start-claude.sh``
uses to turn a Claude Code ``--agent`` selection into the right
``SESSION_HANDOFF_AGENT`` cold-start slot (e.g. ``infra-orchestrator`` →
``claude-infra``). This thin wrapper makes that mapping load-bearing in the
required ``Test (pytest)`` job, so the infra/folk cold-start collision cannot
silently regress.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_TEST = _REPO_ROOT / "scripts" / "audit" / "test_handoff_identity.sh"
_HANDOFF_IDENTITY = _REPO_ROOT / "scripts" / "lib" / "handoff_identity.sh"
_ISSUE_STREAMS = _REPO_ROOT / "scripts" / "config" / "issue_streams.yaml"
_LAUNCH_PATH_MINTS = (
    _HANDOFF_IDENTITY,
    _REPO_ROOT / "scripts" / "lib" / "launcher_core.sh",
    _REPO_ROOT / "scripts" / "session_canary" / "grok_lane.py",
)


def _infra_harness_stream_id() -> str:
    """Anchor on the live infra-harness epic so succession cannot stale this suite."""
    epics = yaml.safe_load(_ISSUE_STREAMS.read_text(encoding="utf-8"))["streams"]["infra-harness"][
        "epics"
    ]
    assert epics, "infra-harness must list at least one epic in issue_streams.yaml"
    return f"epic:{int(epics[0])}"


INFRA_STREAM_ID = _infra_harness_stream_id()


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_handoff_identity_fixtures() -> None:
    assert _HOOK_TEST.is_file(), f"missing identity test: {_HOOK_TEST}"
    result = subprocess.run(
        ["bash", str(_HOOK_TEST)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"identity fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - handoff identity fixtures passed" in result.stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("resolver", "expected"),
    [
        ("handoff_identity_for_epic", "claude-devops"),
        ("handoff_identity_for_gemini_epic", "gemini-devops"),
        ("handoff_identity_for_codex_epic", "codex-devops"),
        ("handoff_identity_for_cursor_epic", "cursor-devops"),
    ],
)
def test_devops_resolves_to_dedicated_provider_slot(resolver: str, expected: str) -> None:
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; "$2" devops', "bash", str(_HANDOFF_IDENTITY), resolver],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("resolver", "expected"),
    [
        ("handoff_identity_for_epic", "claude"),
        ("handoff_identity_for_gemini_epic", "gemini"),
        ("handoff_identity_for_codex_epic", "codex"),
        ("handoff_identity_for_cursor_epic", "cursor"),
        ("handoff_identity_for_grok_epic", "grok"),
        ("handoff_identity_for_kimi_epic", "kimi"),
    ],
)
def test_monitor_empty_roster_resolves_to_provider_identity(resolver: str, expected: str) -> None:
    """monitor.slots is [] in area_assignments.yaml: no per-lane roster slot is
    minted, so the launcher must export the bare provider identity — a valid
    inbox --for choice — instead of a phantom `{provider}-monitor` (#7597)."""
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; "$2" monitor', "bash", str(_HANDOFF_IDENTITY), resolver],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("resolver", "expected"),
    [
        ("handoff_identity_for_epic", "claude"),
        ("handoff_identity_for_gemini_epic", "gemini"),
        ("handoff_identity_for_codex_epic", "codex"),
        ("handoff_identity_for_cursor_epic", "cursor"),
        ("handoff_identity_for_grok_epic", "grok"),
        ("handoff_identity_for_kimi_epic", "kimi"),
    ],
)
def test_open_model_data_empty_roster_resolves_to_provider_identity(resolver: str, expected: str) -> None:
    """open-model-data.slots is [] in area_assignments.yaml: the launcher must
    not mint the phantom `grok-open-model-data` slot that inbox --for rejects
    (#7597)."""
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; "$2" open-model-data', "bash", str(_HANDOFF_IDENTITY), resolver],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("selector", "expected"),
    [
        ("infra", f"infra\t{INFRA_STREAM_ID}\n"),
        ("harness", f"infra\t{INFRA_STREAM_ID}\n"),
        ("infra.fleet-comms", f"infra\t{INFRA_STREAM_ID}\n"),
        ("devops", "devops\tepic:5703\n"),
        ("infra.devops", "devops\tepic:5703\n"),
        ("atlas", "atlas\tepic:4387\n"),
        ("practice", "atlas\tepic:4387\n"),
        ("practice-hub", "atlas\tepic:4387\n"),
        ("atlas.practice", "atlas\tepic:4387\n"),
        ("hramatka", "hramatka\tepic:4542\n"),
        ("hramatka.lessons", "hramatka\tepic:4542\n"),
        ("folk", "folk\tepic:2836\n"),
        ("seminars-folk", "folk\tepic:2836\n"),
        ("bio", "bio\tepic:4431\n"),
        ("seminars-bio", "bio\tepic:4431\n"),
        ("corpus", "corpus\tepic:4706\n"),
        ("corpus-channels", "corpus\tepic:4706\n"),
        ("monitor", "monitor\tepic:7177\n"),
        ("infra.monitor", "monitor\tepic:7177\n"),
    ],
)
def test_legacy_selector_outputs_remain_byte_identical(selector: str, expected: str) -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; launcher_selector_resolve "$2"',
            "bash",
            str(_HANDOFF_IDENTITY),
            selector,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("selector", "lane", "stream", "claude_slot", "gemini_slot", "grok_slot", "codex_slot"),
    [
        ("infra.fleet-comms", "infra", INFRA_STREAM_ID, "claude-infra", "gemini-infra", "grok-infra", "codex-infra"),
        ("infra.devops", "devops", "epic:5703", "claude-devops", "gemini-devops", "grok-devops", "codex-devops"),
        ("devops", "devops", "epic:5703", "claude-devops", "gemini-devops", "grok-devops", "codex-devops"),
        # Empty-roster areas (slots: []) mint the bare provider identity (#7597).
        ("infra.monitor", "monitor", "epic:7177", "claude", "gemini", "grok", "codex"),
        ("monitor", "monitor", "epic:7177", "claude", "gemini", "grok", "codex"),
        ("atlas.practice", "atlas", "epic:4387", "claude-atlas", "gemini-atlas", "grok-atlas", "codex-atlas"),
        ("practice-hub", "atlas", "epic:4387", "claude-atlas", "gemini-atlas", "grok-atlas", "codex-atlas"),
        ("hramatka.lessons", "hramatka", "epic:4542", "claude-hramatka", "gemini-hramatka", "grok-hramatka", "codex-hramatka"),
        ("corpus", "corpus", "epic:4706", "claude-corpus", "gemini-corpus", "grok-corpus", "codex-corpus"),
        ("corpus-channels", "corpus", "epic:4706", "claude-corpus", "gemini-corpus", "grok-corpus", "codex-corpus"),
    ],
)
def test_dot_notation_selector_resolves_stream_and_provider_handoff(
    selector: str,
    lane: str,
    stream: str,
    claude_slot: str,
    gemini_slot: str,
    grok_slot: str,
    codex_slot: str,
) -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; printf "%s|%s|%s|%s|%s|%s" "$(launcher_selector_lane "$2")" "$(launcher_selector_stream "$2")" "$(handoff_identity_for_epic "$2")" "$(handoff_identity_for_gemini_epic "$2")" "$(handoff_identity_for_grok_epic "$2")" "$(handoff_identity_for_codex_epic "$2")"',
            "bash",
            str(_HANDOFF_IDENTITY),
            selector,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{lane}|{stream}|{claude_slot}|{gemini_slot}|{grok_slot}|{codex_slot}"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize("arguments", [["--epic", "atlas.epic"], ["--epic=atlas.epic"]])
def test_legacy_epic_suffix_normalizes_before_selector_resolution(arguments: list[str]) -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; epic="$(handoff_epic_from_argv "${@:2}")"; printf "%s|%s" "$epic" "$(launcher_selector_lane "$epic")"',
            "bash",
            str(_HANDOFF_IDENTITY),
            *arguments,
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "atlas|atlas"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_unknown_selector_fails_closed() -> None:
    result = subprocess.run(
        ["bash", "-c", 'source "$1"; launcher_selector_resolve unknown', "bash", str(_HANDOFF_IDENTITY)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 1
    assert result.stdout == ""


def test_devops_epic_is_registered_separately_from_infra() -> None:
    registry = yaml.safe_load(_ISSUE_STREAMS.read_text(encoding="utf-8"))["streams"]

    assert registry["infra-harness"]["epics"]
    assert 5703 in registry["devops"]["epics"]  # allow-hardcoded-epic: devops stream anchor
    assert set(registry["infra-harness"]["epics"]).isdisjoint(registry["devops"]["epics"])
    assert f"epic:{int(registry['infra-harness']['epics'][0])}" == INFRA_STREAM_ID


def test_monitor_epic_is_registered_separately_from_infra() -> None:
    registry = yaml.safe_load(_ISSUE_STREAMS.read_text(encoding="utf-8"))["streams"]

    assert registry["infra-harness"]["epics"]
    assert 7177 in registry["monitor"]["epics"]  # allow-hardcoded-epic: monitor stream anchor
    assert set(registry["infra-harness"]["epics"]).isdisjoint(registry["monitor"]["epics"])
    assert set(registry["devops"]["epics"]).isdisjoint(registry["monitor"]["epics"])


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    "launcher",
    [
        "start-gemini-driver.sh",
        "start-grok-driver.sh",
        "start-claude-driver.sh",
        "start-codex-driver.sh",
        "start-cursor-driver.sh",
    ],
)
def test_launcher_help_documents_allowlisted_dot_notation(launcher: str) -> None:
    result = subprocess.run(
        ["bash", str(_REPO_ROOT / launcher), "--help"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Valid lane selectors:" in result.stdout
    assert "infra.fleet-comms" in result.stdout
    assert "atlas.practice" in result.stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize(
    ("launcher", "arguments", "expected_code"),
    [
        ("start-gemini-driver.sh", ["unknown"], 2),
        ("start-grok-driver.sh", ["unknown"], 2),
        ("start-claude-driver.sh", ["unknown"], 2),
        ("start-codex-driver.sh", ["unknown"], 2),
        ("start-cursor-driver.sh", ["unknown"], 2),
    ],
)
def test_launcher_unknown_selector_fails_closed(launcher: str, arguments: list[str], expected_code: int) -> None:
    result = subprocess.run(
        ["bash", str(_REPO_ROOT / launcher), *arguments],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == expected_code
    assert "unknown lane selector 'unknown'" in result.stderr
    assert "Valid lane selectors:" in result.stderr


def test_infra_launcher_stream_matches_registry_anchor() -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; launcher_selector_stream infra',
            "bash",
            str(_HANDOFF_IDENTITY),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == INFRA_STREAM_ID


def test_infra_stream_follows_registry_mutation(tmp_path: Path) -> None:
    """A registry change must flow through the launcher with zero script edits."""
    fresh_epic = 888001
    fixture = tmp_path / "issue_streams.yaml"
    fixture.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "streams": {
                    "infra-harness": {
                        "title": "Infra fixture",
                        "epics": [fresh_epic],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["HANDOFF_ISSUE_STREAMS_YAML"] = str(fixture)
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; printf "%s|%s|%s" "$(launcher_selector_stream infra)" "$(launcher_selector_stream harness)" "$(launcher_selector_stream infra.fleet-comms)"',
            "bash",
            str(_HANDOFF_IDENTITY),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    expected = f"epic:{fresh_epic}"
    assert result.stdout == f"{expected}|{expected}|{expected}"
    assert expected != INFRA_STREAM_ID


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_new_registry_stream_resolves_without_shell_edit(tmp_path: Path) -> None:
    """A new stream key and its infra.<key> form need only a registry row."""
    fresh_key = "future-ops"
    fresh_epic = 888001
    fixture = tmp_path / "issue_streams.yaml"
    fixture.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "streams": {
                    fresh_key: {
                        "title": "Future operations fixture",
                        "epics": [fresh_epic, 888003],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["HANDOFF_ISSUE_STREAMS_YAML"] = str(fixture)

    for selector in (fresh_key, f"infra.{fresh_key}"):
        result = subprocess.run(
            [
                "bash",
                "-c",
                'source "$1"; launcher_selector_resolve "$2"',
                "bash",
                str(_HANDOFF_IDENTITY),
                selector,
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == f"{fresh_key}\tepic:{fresh_epic}\n"

    help_result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; launcher_selector_help',
            "bash",
            str(_HANDOFF_IDENTITY),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert help_result.returncode == 0, help_result.stderr
    assert f"{fresh_key} | infra.{fresh_key}" in help_result.stdout


def test_launch_path_does_not_literal_mint_infra_epic() -> None:
    """Reintroducing a literal epic:4707 mint on the launch path must fail."""
    for path in _LAUNCH_PATH_MINTS:
        text = path.read_text(encoding="utf-8")
        assert "epic:4707" not in text, f"{path} reminted epic:4707"
        assert "4707" not in text, f"{path} still hard-codes 4707"


def test_fresh_infra_stream_capsule_is_registered(tmp_path: Path) -> None:
    """A successor infra epic gets registered dual-write + non-empty handoff paths."""
    from agents_extensions.shared.session_streams.db import SessionStreamDatabase
    from agents_extensions.shared.session_streams.model import LeaseHolder
    from agents_extensions.shared.session_streams.receipts import register_manifest_inventory
    from agents_extensions.shared.session_streams.store import SessionStreamStore
    from scripts.session_supervisor import LaunchRole, SessionSupervisor

    fresh_epic = 888001
    stream_id = f"epic:{fresh_epic}"
    repo = tmp_path / "repo"
    cfg = repo / "scripts" / "config"
    cfg.mkdir(parents=True)
    (cfg / "issue_streams.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "streams": {
                    "infra-harness": {
                        "title": "Infra fixture",
                        "epics": [fresh_epic],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    registration = register_manifest_inventory(store, repo)
    assert stream_id in registration.registered_stream_ids
    assert registration.modes[stream_id] == "inventory"

    supervisor = SessionSupervisor(store, repo_root=repo)
    lease = supervisor.open_driver(
        role=LaunchRole.DRIVER,
        stream_id=stream_id,
        holder=LeaseHolder(
            agent="probe",
            harness="probe",
            instance_id="fresh-infra-capsule",
            process_id=os.getpid(),
        ),
        lineage_id="lineage-fresh-infra",
        ttl_seconds=60,
    )
    capsule = supervisor.build_capsule(
        role=LaunchRole.DRIVER, stream_id=stream_id, lease=lease
    ).as_dict()
    assert capsule["identity"]["stream_id"] == stream_id
    assert capsule["dual_write"]["mode"] == "inventory"
    assert capsule["dual_write"]["handoff_paths"]
    assert any("harness-epic" in path for path in capsule["dual_write"]["handoff_paths"])
    supervisor.close_driver(role=LaunchRole.DRIVER, lease=lease)
