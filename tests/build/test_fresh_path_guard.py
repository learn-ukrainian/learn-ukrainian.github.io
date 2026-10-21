from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import manifest, regeneration
from scripts.build.fresh.path_guard import public_diagnostic


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
