"""Codex driver regression coverage, including the lease-free governor guard."""

from tests.test_launcher_contract import run_launcher


def test_sustained_driver_probes_then_claims_lease_then_binds_drive_epic() -> None:
    result = run_launcher("start-codex-driver.sh", "--epic", "devops")
    assert result.returncode == 0, result.stderr
    assert "would probe" in result.stdout
    assert result.stdout.index("would probe") < result.stdout.index("would claim lease")
    assert result.stdout.index("would claim lease") < result.stdout.index("would mint and bootstrap")
    assert result.stdout.index("would mint and bootstrap") < result.stdout.index("would bind drive-epic")


def test_governor_pins_sol_and_is_mutation_guarded_against_lease_claim() -> None:
    result = run_launcher(
        "start-codex-driver.sh",
        "--governor",
        "AUTO",
        env={"SESSION_EPIC": "foreign-lease-must-not-survive"},
    )
    assert result.returncode == 0, result.stderr
    assert "--model gpt-5.6-sol" in result.stdout
    # This is intentionally observable: removing the core's `unset SESSION_EPIC`
    # changes this line and fails the test.
    assert "governor SESSION_EPIC=<unset>" in result.stdout
    assert "foreign-lease-must-not-survive" not in result.stdout
    assert "would claim lease" not in result.stdout


def test_governor_rejects_unknown_selector_before_transport_probe() -> None:
    result = run_launcher("start-codex-driver.sh", "--governor", "not-a-selector")
    assert result.returncode == 2
    assert "unknown lane selector" in result.stderr


def test_governor_requires_a_selector_and_accepts_a_known_lane() -> None:
    missing = run_launcher("start-codex-driver.sh", "--governor")
    known = run_launcher("start-codex-driver.sh", "--governor", "devops")
    assert missing.returncode == 2
    assert "requires a value" in missing.stderr
    assert known.returncode == 0, known.stderr
    assert "would claim lease" not in known.stdout


def test_sustained_codex_driver_revalidates_certification() -> None:
    rejected = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-unknown")
    sol = run_launcher("start-codex-driver.sh", "--epic", "devops", "--model", "gpt-5.6-sol")
    assert rejected.returncode == 4
    assert sol.returncode == 0, sol.stderr
    assert "--model gpt-5.6-sol" in sol.stdout
