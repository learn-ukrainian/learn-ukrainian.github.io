"""C-2481 expiry bypasses archive proof rules but respects keep-lists and links."""

import json
import os
import time

import pytest

from scripts.hygiene import preserved_retention as retention


def test_backstop_deletes_entries_older_than_24h_and_keeps_keep_listed_ones(tmp_path, monkeypatch):
    batch = tmp_path / "batch_state"
    root = batch / "preserved"
    root.mkdir(parents=True)
    old = time.time() - 25 * 3600
    for name in ("held", "pinned", "kept", "recent-child"):
        entry = root / name
        entry.mkdir()
        (entry / "payload").write_bytes(b"residue")
        os.utime(entry / "payload", (old, old))
        os.utime(entry, (old, old))
    (root / "recent-child/payload").touch()
    (root / "old-file").write_bytes(b"old")
    os.utime(root / "old-file", (old, old))
    keep = batch / "preserved-keep.txt"
    keep.write_text("kept\n")
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "live").write_text("untouched")
    (root / "external").symlink_to(victim, target_is_directory=True)
    (root / "held/link").symlink_to(victim, target_is_directory=True)
    os.utime(root / "held/link", (old, old), follow_symlinks=False)
    os.utime(root / "held", (old, old))
    monkeypatch.setattr(retention, "eligible", lambda *a: pytest.fail("backstop must bypass proof rules"))
    args = ["--batch-root", str(batch), "--expire-older-than-hours", "24"]
    assert retention.main(args) == 0
    assert (root / "held").exists() and (root / "pinned").exists()
    assert retention.main([*args, "--apply"]) == 0
    assert sorted(p.name for p in root.iterdir()) == ["external", "kept", "recent-child"]
    assert (victim / "live").read_text() == "untouched"
    rows = [json.loads(line) for path in (batch / "reports").glob("*.jsonl") for line in path.read_text().splitlines()]
    assert {row["name"] for row in rows if row["result"] == "deleted"} == {"held", "pinned", "old-file"}


@pytest.mark.parametrize("hours", ["0", "-1", "nan", "inf"])
def test_backstop_rejects_invalid_expiry_age(hours):
    with pytest.raises(SystemExit) as error:
        retention.main(["--expire-older-than-hours", hours])
    assert error.value.code == 2
