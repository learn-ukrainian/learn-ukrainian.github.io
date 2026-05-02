import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ai_agent_bridge._env import build_agent_env, is_secret_env_key


def test_is_secret_env_key_matches_common_secret_names():
    assert is_secret_env_key("GITHUB_TOKEN") is True
    assert is_secret_env_key("OPENAI_API_KEY") is True
    assert is_secret_env_key("AWS_ACCESS_KEY_ID") is True
    assert is_secret_env_key("GOOGLE_APPLICATION_CREDENTIALS") is True
    assert is_secret_env_key("DB_PASSWORD") is True


def test_build_agent_env_strips_secret_values_and_keeps_runtime_context(tmp_path):
    source = {
        "HOME": "/Users/example",
        "PATH": "/usr/bin",
        "SHELL": "/bin/bash",
        "GITHUB_TOKEN": "ghp_secret",
        "OPENAI_API_KEY": "sk-secret",
        "GOOGLE_API_KEY": "google-secret",
        "CUSTOM_SECRET": "secret",
        "AB_REPO_ROOT": "/repo",
        "GEMINI_AUTH_MODE": "subscription",
        "UNRELATED": "drop-me",
    }

    env = build_agent_env(source, repo_root=tmp_path)

    assert env["HOME"] == "/Users/example"
    assert env["SHELL"] == "/bin/bash"
    assert env["AB_REPO_ROOT"] == "/repo"
    assert env["GEMINI_AUTH_MODE"] == "subscription"
    assert env["PATH"].startswith(str(Path(tmp_path) / ".venv" / "bin"))
    assert env["PYTHONUNBUFFERED"] == "1"

    assert "GITHUB_TOKEN" not in env
    assert "OPENAI_API_KEY" not in env
    assert "GOOGLE_API_KEY" not in env
    assert "CUSTOM_SECRET" not in env
    assert "UNRELATED" not in env
