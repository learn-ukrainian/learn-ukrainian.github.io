import pytest

from scripts.ai_agent_bridge._cli import _build_parser, _dispatch_command


def test_serve_rejects_non_localhost_without_flag():
    parser = _build_parser()
    args = parser.parse_args(["serve", "--openai", "--host", "0.0.0.0"])

    with pytest.raises(SystemExit) as exc:
        _dispatch_command(args)

    assert "refusing to bind to non-localhost" in str(exc.value)

def test_serve_allows_localhost_without_flag(monkeypatch):
    # Mock uvicorn.run to avoid actually starting a server
    import uvicorn
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: None)

    parser = _build_parser()
    args = parser.parse_args(["serve", "--openai", "--host", "127.0.0.1"])

    # Should not raise SystemExit
    _dispatch_command(args)

def test_serve_allows_non_localhost_with_flag(monkeypatch):
    # Mock uvicorn.run to avoid actually starting a server
    import uvicorn
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: None)

    parser = _build_parser()
    args = parser.parse_args(["serve", "--openai", "--host", "0.0.0.0", "--allow-remote"])

    # Should not raise SystemExit
    _dispatch_command(args)

def test_serve_requires_openai():
    parser = _build_parser()
    # If we don't pass --openai, it should still fail as per existing logic
    args = parser.parse_args(["serve"])

    with pytest.raises(SystemExit) as exc:
        _dispatch_command(args)

    assert "serve currently requires --openai" in str(exc.value)
