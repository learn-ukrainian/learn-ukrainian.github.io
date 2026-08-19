"""Linux-native systemd templates must supervise listeners, not oneshot services.sh."""

from __future__ import annotations

from pathlib import Path

PACKAGING = Path(__file__).resolve().parents[2] / "packaging" / "systemd"
UNITS = (
    "learn-ukrainian-api.service",
    "learn-ukrainian-sources.service",
    "learn-ukrainian-work.service",
    "learn-ukrainian-astro.service",
)


def test_systemd_templates_are_type_simple() -> None:
    for name in UNITS:
        text = (PACKAGING / name).read_text(encoding="utf-8")
        assert "Type=simple" in text
        assert "Type=oneshot" not in text
        assert "RemainAfterExit" not in text
        assert "services.sh start" not in text
        if name != "learn-ukrainian-work.service":
            assert "127.0.0.1" in text


def test_api_supervisor_is_gated_for_linux() -> None:
    text = Path(__file__).resolve().parents[2].joinpath("services.sh").read_text(
        encoding="utf-8"
    )
    assert "_api_supervisor_available" in text
    assert "SVC_API_SUPERVISOR_BIN" in text
    assert "command -v launchctl >/dev/null 2>&1" in text
    assert text.count("_api_supervisor_available") >= 3


def test_systemd_templates_have_no_host_facts() -> None:
    forbidden = ("atlas-runner", "hramatka", "46.", "HostName")
    for path in PACKAGING.iterdir():
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} leaked {token!r}"
