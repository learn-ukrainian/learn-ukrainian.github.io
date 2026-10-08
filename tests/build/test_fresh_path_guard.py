import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import manifest, regeneration
from scripts.build.fresh.path_guard import checked_path, load_a1_reference, public_diagnostic


@pytest.fixture
def reference_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
         "commit", "-q", "--allow-empty", "-m", "fixture"], check=True, capture_output=True, timeout=30,
    )
    return tmp_path


def _reference(root, data=b"Reference\r\n"):
    path = root / "curriculum/l2-uk-en/a1-v1/sample/module.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(data)
    return path


def test_a1_reference_exact_bytes_and_optional_absence(reference_repo):
    assert load_a1_reference(reference_repo, "a1", "sample") is None
    path = _reference(reference_repo)
    assert load_a1_reference(reference_repo, "a1", "sample") == (path.relative_to(reference_repo).as_posix(), b"Reference\r\n")
    with pytest.raises(ValueError, match="path_forbidden"):
        checked_path(reference_repo, path.relative_to(reference_repo), "curriculum/l2-uk-en/a1-v1")


@pytest.mark.parametrize("component", ["curriculum", "l2-uk-en", "a1-v1", "sample", "module.md"])
@pytest.mark.parametrize("broken", [False, True])
def test_a1_reference_refuses_every_symlink(reference_repo, component, broken):
    path = _reference(reference_repo)
    target = next(p for p in (path, *path.parents) if p.name == component)
    moved = reference_repo / "moved"
    target.rename(moved)
    target.symlink_to(reference_repo / "absent" if broken else moved)
    with pytest.raises(ValueError, match="a1_reference_"):
        load_a1_reference(reference_repo, "a1", "sample")


@pytest.mark.parametrize("data,reason", [(b"", "empty"), (b"\xff", "invalid_utf8")])
def test_a1_reference_refuses_invalid_bytes(reference_repo, data, reason):
    _reference(reference_repo, data)
    with pytest.raises(ValueError, match=reason):
        load_a1_reference(reference_repo, "a1", "sample")


@pytest.mark.parametrize("kind", ["directory", "unreadable", "fifo"])
def test_a1_reference_requires_readable_regular_leaf(reference_repo, kind):
    import os

    path = _reference(reference_repo)
    if kind == "unreadable":
        path.chmod(0)
    else:
        path.unlink()
        if kind == "directory":
            path.mkdir()
        else:
            os.mkfifo(path)
    with pytest.raises(ValueError, match="regular_file"):
        load_a1_reference(reference_repo, "a1", "sample")


def test_a1_reference_tracked_missing_is_not_optional(reference_repo):
    path = _reference(reference_repo)
    subprocess.run(["git", "-C", str(reference_repo), "add", "."], check=True, timeout=30)
    path.unlink()
    with pytest.raises(ValueError, match="tracked_missing"):
        load_a1_reference(reference_repo, "a1", "sample")


def test_a1_reference_unknown_git_is_not_absence(tmp_path):
    with pytest.raises(ValueError, match="git_unknown"):
        load_a1_reference(tmp_path, "a1", "sample")


@pytest.mark.parametrize("slug", ["../sample", "/sample", "sample/other", "Sample", "sample\n"])
def test_a1_reference_refuses_traversal(reference_repo, slug):
    with pytest.raises(ValueError, match="invalid_slug"):
        load_a1_reference(reference_repo, "a1", slug)


def test_a1_reference_non_a1_never_touches_filesystem(tmp_path, monkeypatch):
    from scripts.build.fresh import path_guard

    monkeypatch.setitem(path_guard.PREVIOUS_EDITIONS, "a2", "a2-v1")
    monkeypatch.setattr(path_guard.os, "open", lambda *a, **kw: pytest.fail("non-A1 read"))
    assert load_a1_reference(tmp_path, "a2", "sample") is None


@pytest.mark.parametrize("root", [Path("/home/test/project"), Path("/tmp/project with spaces")])
def test_public_diagnostic_keeps_only_repository_relative_paths(root):
    message = f"failed: '{root}/curriculum/receipt.yaml', root={root}; external /home/other/receipt.yaml"
    result = public_diagnostic(message, root)
    assert result == "failed: './curriculum/receipt.yaml', root=.; external <external-path>"
    assert str(root) not in result and "/home/" not in result
    assert public_diagnostic(f"sibling {root}-other/file.yaml", root).startswith("sibling <external-path>")


def test_public_diagnostic_preserves_relative_paths_and_reason_codes():
    message = "receipt_span_alignment_failed: curriculum/receipt.yaml unit ('urok', 's1')"
    assert public_diagnostic(message, Path("/tmp/project")) == message


@pytest.mark.parametrize("scheme", ["https", "http", "HTTPS", "HTTP"])
@pytest.mark.parametrize("url_path", ["receipt.yaml?check=12#reason", "part;param/file", "part(one)/file", "part,two/file"])
def test_public_diagnostic_preserves_urls_while_sanitizing_paths(scheme, url_path):
    url = f"{scheme}://example.test/tmp/project/{url_path}"
    message = f"See '{url}'; missing /home/other/receipt.yaml and /tmp/project/receipt.yaml"
    assert public_diagnostic(message, Path("/tmp/project")) == (
        f"See '{url}'; missing <external-path> and ./receipt.yaml"
    )


@pytest.mark.parametrize("scheme", ["file", "FILE", "ftp", "custom+v1", "httpx"])
@pytest.mark.parametrize("location", ["/home/other/tasks/output.txt", "example.test/home/other/output.txt"])
def test_public_diagnostic_redacts_non_http_url_paths(scheme, location):
    message = f"saved to: {scheme}://{location}"
    assert public_diagnostic(message, Path("/tmp/project")) == f"saved to: {scheme}:<external-path>"


@pytest.mark.parametrize("layer", ["writer", "engine", "harness"])
def test_record_failure_sanitizes_reason_at_persistence_boundary(tmp_path, layer):
    path = tmp_path / "lesson-1.regeneration.yaml"
    reason = f"missing {regeneration.SCHEMA.parents[1]}/schemas/receipt.yaml; /home/other/task.result"
    failure = {"check": 1, "layer": layer, "reason": reason}
    doc = regeneration.record_failure(path, "sample", 1, failure, {})
    if layer == "harness":
        path = path.with_name("lesson-1.writer-harness.yaml")
        doc = regeneration.load_harness(path, "sample", 1)
        rows = doc["failures"]
    else:
        rows = doc["attempts"]
    expected = "missing ./schemas/receipt.yaml; <external-path>"
    assert rows[0]["reason"] == expected
    assert yaml.safe_load(path.read_text())["failures" if layer == "harness" else "attempts"][0]["reason"] == expected
    assert failure["reason"] == reason


def test_write_manifest_error_sanitizes_reason_at_persistence_boundary(tmp_path):
    reason = f"missing {manifest.SCHEMA.parents[1]}/schemas/receipt.yaml; /home/other/task.result"
    doc = manifest.write_manifest_error(tmp_path, 1, reason, "schemas/receipt.yaml", "2026-01-01T00:00:00Z")
    expected = "missing ./schemas/receipt.yaml; <external-path>"
    assert doc["reason"] == expected
    assert yaml.safe_load((tmp_path / "lesson-1.manifest-error.yaml").read_text())["reason"] == expected
