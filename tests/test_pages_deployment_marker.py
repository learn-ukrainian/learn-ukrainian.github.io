"""Hidden-output audit for the Pages deployment marker (#11194).

The upload action publishes hidden paths only with ``include-hidden-files``;
these tests prove the audit lets through exactly the exact-SHA marker and fails
closed on every other hidden path or malformed marker.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.deploy.verify_pages_deployment_marker import (
    MarkerAuditError,
    audit,
    find_hidden_paths,
    main,
    marker_name,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy-pages.yml"
SHA = "8fec22bb97493523f45d2349957d7da47053487b"
OTHER_SHA = "df201f34537acecf20921c3cc5c383cdd2790b4d"


def _site(tmp_path: Path, *, marker: bool = True) -> Path:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>x</title>", encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    (dist / "lexicon-v2" / "a").mkdir(parents=True)
    (dist / "lexicon-v2" / "a" / "index.html").write_text("<p>a</p>", encoding="utf-8")
    if marker:
        (dist / ".well-known").mkdir()
        (dist / ".well-known" / marker_name(SHA)).write_bytes(f"{SHA}\n".encode("ascii"))
    return dist


def _refused(dist: Path, match: str, sha: str | None = SHA) -> None:
    with pytest.raises(MarkerAuditError, match=match):
        audit(dist, sha)


def test_valid_marker_with_visible_assets_is_the_only_hidden_output(tmp_path: Path) -> None:
    """Baseline: the exact marker passes, ordinary visible assets are untouched."""
    dist = _site(tmp_path)
    assert audit(dist, SHA) == dist / ".well-known" / marker_name(SHA)
    assert find_hidden_paths(dist) == []


def test_workflow_emit_step_output_passes_the_audit(tmp_path: Path) -> None:
    """Contract drift: the verifier must accept exactly what the workflow's emit step writes."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    emit = next(s for s in workflow["jobs"]["deploy"]["steps"] if s.get("name") == "Emit immutable deployment marker")
    site = tmp_path / "site"
    (site / "dist").mkdir(parents=True)
    bash = shutil.which("bash")
    assert bash is not None
    subprocess.run(
        [bash, "-euo", "pipefail", "-c", emit["run"]],
        cwd=site,
        env={"PATH": os.environ.get("PATH", ""), "GITHUB_SHA": SHA},
        check=True,
        timeout=30,
    )
    assert audit(site / "dist", SHA).read_bytes() == f"{SHA}\n".encode("ascii")


def test_absent_marker_is_refused(tmp_path: Path) -> None:
    """Missing-marker defect: no .well-known at all, or an empty one."""
    dist = _site(tmp_path, marker=False)
    _refused(dist, r"\.well-known/ is missing")
    (dist / ".well-known").mkdir()
    _refused(dist, r"is missing")


@pytest.mark.parametrize(
    "bad_sha",
    [None, "", SHA.upper(), SHA[:39], SHA + "0", "g" * 40, f" {SHA}", f"{SHA}\n"],
)
def test_missing_or_malformed_sha_is_refused(tmp_path: Path, bad_sha: str | None) -> None:
    """Malformed-input defect: only a full lowercase 40-hex SHA is a deployment identity."""
    _refused(_site(tmp_path), r"SHA", sha=bad_sha)


def test_cli_requires_sha_and_reports_refusal(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI fails closed without --sha and returns 1 with an annotation on refusal."""
    dist = _site(tmp_path)
    with pytest.raises(SystemExit) as exc:
        main([str(dist)])
    assert exc.value.code == 2

    assert main([str(dist), "--sha", ""]) == 1
    assert "::error title=Pages marker audit refused::" in capsys.readouterr().err

    assert main([str(dist), "--sha", SHA]) == 0
    assert f".well-known/{marker_name(SHA)} is the only hidden output" in capsys.readouterr().out


def test_marker_for_a_different_sha_is_refused(tmp_path: Path) -> None:
    """Stale-revision defect: a marker naming another commit must not pass for this one."""
    _refused(_site(tmp_path), r"unexpected entries", sha=OTHER_SHA)


@pytest.mark.parametrize(
    "body",
    [
        SHA.encode("ascii"),
        f"{SHA}\n\n".encode("ascii"),
        f"{SHA}\r\n".encode("ascii"),
        f"{OTHER_SHA}\n".encode("ascii"),
        b"",
    ],
    ids=["missing-newline", "extra-newline", "crlf", "wrong-sha", "empty"],
)
def test_wrong_marker_bytes_are_refused(tmp_path: Path, body: bytes) -> None:
    """Body-contract defect: the body is exactly the SHA plus one LF."""
    dist = _site(tmp_path)
    (dist / ".well-known" / marker_name(SHA)).write_bytes(body)
    _refused(dist, r"body is not exactly")


@pytest.mark.parametrize("hidden", [".env", ".DS_Store", ".git/config", ".github/workflows/x.yml", ".nojekyll"])
def test_extra_top_level_hidden_path_is_refused(tmp_path: Path, hidden: str) -> None:
    """Leak defect: enabling hidden-file upload must not publish any other root dotfile."""
    dist = _site(tmp_path)
    (dist / hidden).parent.mkdir(parents=True, exist_ok=True)
    (dist / hidden).write_text("secret", encoding="utf-8")
    _refused(dist, "unexpected hidden paths would be published: " + re.escape(hidden.split("/")[0]))


@pytest.mark.parametrize(
    "hidden",
    ["assets/.DS_Store", "lexicon-v2/a/.cache/blob", "lexicon-v2/.well-known/marker.txt", "atlas/.git/HEAD"],
)
def test_unexpected_nested_hidden_path_is_refused(tmp_path: Path, hidden: str) -> None:
    """Leak defect: hidden paths at any depth, including a nested .well-known, are refused."""
    dist = _site(tmp_path)
    (dist / hidden).parent.mkdir(parents=True, exist_ok=True)
    (dist / hidden).write_text("x", encoding="utf-8")
    first_hidden = next(i for i, part in enumerate(hidden.split("/")) if part.startswith("."))
    expected = "/".join(hidden.split("/")[: first_hidden + 1])
    with pytest.raises(MarkerAuditError) as exc:
        audit(dist, SHA)
    assert expected in str(exc.value)


def test_hidden_path_behind_visible_directory_symlink_is_refused(tmp_path: Path) -> None:
    """Dereference defect: tar --dereference follows visible dir symlinks, so the scan must too."""
    dist = _site(tmp_path)
    outside = tmp_path / "outside"
    (outside / ".secrets").mkdir(parents=True)
    (outside / ".secrets" / "token").write_text("x", encoding="utf-8")
    (dist / "linked").symlink_to(outside, target_is_directory=True)
    _refused(dist, r"linked/\.secrets")


def test_directory_symlink_cycle_terminates(tmp_path: Path) -> None:
    """Loop defect: a self-referencing symlink must not hang the scan."""
    dist = _site(tmp_path)
    (dist / "assets" / "loop").symlink_to(dist / "assets", target_is_directory=True)
    assert find_hidden_paths(dist) == []


@pytest.mark.parametrize("extra", ["security.txt", ".hidden", marker_name(OTHER_SHA)])
def test_unexpected_well_known_child_is_refused(tmp_path: Path, extra: str) -> None:
    """Allowlist defect: .well-known holds the single marker and nothing else."""
    dist = _site(tmp_path)
    (dist / ".well-known" / extra).write_text("x", encoding="utf-8")
    _refused(dist, r"\.well-known/ has unexpected entries")


def test_unexpected_well_known_subdirectory_is_refused(tmp_path: Path) -> None:
    dist = _site(tmp_path)
    (dist / ".well-known" / "acme-challenge").mkdir()
    _refused(dist, r"unexpected entries: \.well-known/acme-challenge")


def test_symlinked_well_known_is_refused(tmp_path: Path) -> None:
    """Indirection defect: a symlinked .well-known could publish any target directory."""
    dist = _site(tmp_path, marker=False)
    real = tmp_path / "elsewhere"
    real.mkdir()
    (real / marker_name(SHA)).write_bytes(f"{SHA}\n".encode("ascii"))
    (dist / ".well-known").symlink_to(real, target_is_directory=True)
    _refused(dist, r"\.well-known is a symlink")


def test_symlinked_marker_is_refused(tmp_path: Path) -> None:
    """Indirection defect: the marker must be the regular file itself, even with correct target bytes."""
    dist = _site(tmp_path)
    marker = dist / ".well-known" / marker_name(SHA)
    target = tmp_path / "target.txt"
    target.write_bytes(f"{SHA}\n".encode("ascii"))
    marker.unlink()
    marker.symlink_to(target)
    _refused(dist, r"is a symlink")


def test_well_known_that_is_a_file_is_refused(tmp_path: Path) -> None:
    dist = _site(tmp_path, marker=False)
    (dist / ".well-known").write_text(SHA, encoding="utf-8")
    _refused(dist, r"\.well-known is not a directory")


def test_nonregular_marker_is_refused(tmp_path: Path) -> None:
    """Type defect: a directory or FIFO in the marker's place is not a regular file."""
    dist = _site(tmp_path)
    marker = dist / ".well-known" / marker_name(SHA)
    marker.unlink()
    marker.mkdir()
    _refused(dist, r"is not a regular file")

    marker.rmdir()
    os.mkfifo(marker)
    _refused(dist, r"is not a regular file")


def _change_well_known(dist: Path, scratch: Path, change: str) -> None:
    well_known = dist / ".well-known"
    marker = well_known / marker_name(SHA)
    if change == "extra-child":
        (well_known / ".private").write_text("x", encoding="utf-8")
    elif change == "marker-body":
        marker.write_bytes(b"wrong deployment\n")
    elif change == "marker-symlink":
        (scratch / "payload.txt").write_text("x", encoding="utf-8")
        marker.unlink()
        marker.symlink_to(scratch / "payload.txt")
    elif change == "well-known-symlink":
        well_known.rename(scratch / "moved")
        (scratch / "moved" / ".private").write_text("x", encoding="utf-8")
        well_known.symlink_to(scratch / "moved", target_is_directory=True)
    elif change == "marker-replaced-same-bytes":
        (scratch / "copy.txt").write_bytes(f"{SHA}\n".encode("ascii"))
        os.replace(scratch / "copy.txt", marker)
    else:  # well-known-replaced-same-content
        shutil.copytree(well_known, scratch / "copy")
        shutil.rmtree(well_known)
        os.rename(scratch / "copy", well_known)


@pytest.mark.parametrize(
    ("change", "match"),
    [
        ("extra-child", r"unexpected entries: \.well-known/\.private"),
        ("marker-body", r"body is not exactly"),
        ("marker-symlink", r"is a symlink"),
        ("well-known-symlink", r"\.well-known is a symlink"),
        ("marker-replaced-same-bytes", r"replaced during the audit"),
        ("well-known-replaced-same-content", r"replaced during the audit"),
    ],
)
def test_marker_subtree_changed_during_the_scan_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str, match: str
) -> None:
    """Check-then-scan race defect: the scan skips .well-known, so a change after its check must still fail.

    The change is made when the scan first lists the artifact root, after the
    marker check has passed. The last two cases keep a valid shape but swap the
    inodes, so the decision must be bound to the approved files, not their names.
    """
    dist = _site(tmp_path)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    real_scandir = os.scandir
    changed = []

    def scandir_then_change(path: Path) -> object:
        if not changed and Path(path) == dist:
            changed.append(change)
            _change_well_known(dist, scratch, change)
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", scandir_then_change)
    _refused(dist, match)
    assert changed == [change]


def test_missing_or_symlinked_dist_is_refused(tmp_path: Path) -> None:
    _refused(tmp_path / "absent", r"does not exist")
    dist = _site(tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(dist, target_is_directory=True)
    _refused(alias, r"not a real directory")
