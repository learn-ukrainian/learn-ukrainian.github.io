"""Native Codex launcher behavior after the driver split."""

from tests.test_launcher_contract import run_launcher


def test_codex_interactive_rejects_epic() -> None:
    result = run_launcher("start-codex.sh", "--epic", "devops")
    assert result.returncode == 2


def test_codex_native_harness_is_default_and_forwards_arguments_after_separator() -> None:
    result = run_launcher("start-codex.sh", "--", "--ask-for-approval", "never")
    assert result.returncode == 0, result.stderr
    assert "would exec codex" in result.stdout
    assert "--ask-for-approval never" in result.stdout


def test_codex_rejects_unknown_harness_and_unsupported_launcher_flags() -> None:
    harness = run_launcher("start-codex.sh", "--harness", "native")
    unknown = run_launcher("start-codex.sh", "--not-a-real-flag")
    assert harness.returncode == unknown.returncode == 2
    assert "codex|claude-code" in harness.stderr
    assert "run --help" in unknown.stderr


def test_codex_hermes_opt_in_uses_provider_label_separately_from_model(tmp_path) -> None:
    from tests.test_launcher_contract import hermes_stub_env

    result = run_launcher("start-codex.sh", "--harness", "hermes", env=hermes_stub_env(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "would exec hermes chat --cli --provider openai-codex --model gpt-6-astra" in result.stdout
    assert "--reasoning low" in result.stdout
    assert "would claim lease" not in result.stdout
    assert "would probe" not in result.stdout


def test_codex_hermes_rejects_provider_label_as_model() -> None:
    result = run_launcher("start-codex.sh", "--harness", "hermes", "--model", "openai-codex")
    assert result.returncode == 2
    assert "only gpt-6-astra is approved" in result.stderr


def test_codex_hermes_cannot_start_astra_driver_or_governor() -> None:
    for selector in ("--epic", "--governor"):
        result = run_launcher("start-codex-driver.sh", "--harness", "hermes", selector, "devops")
        assert result.returncode == 4, result.stderr
        assert "interactive only" in result.stderr
        assert "would claim lease" not in result.stdout
        assert "would probe" not in result.stdout
