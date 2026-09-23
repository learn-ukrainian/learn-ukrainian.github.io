from __future__ import annotations

import ast
import gzip
import hashlib
import io
import json
import os
import stat
from pathlib import Path

import pytest

from scripts.lexicon import manifest_io

STALE_POINTER_HINT = "Re-downloading cannot fix a stale pointer."


@pytest.fixture(autouse=True)
def _isolate_manifest_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(manifest_io.MANIFEST_CACHE_ENV, str(tmp_path / "manifest-cache"))


def _json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_pointer(
    pointer_path: Path,
    *,
    json_bytes: bytes,
    gz_bytes: bytes,
    gz_sha256: str | None = None,
) -> None:
    pointer_path.write_text(
        json.dumps(
            {
                "asset_url": "https://example.test/lexicon-manifest.json.gz",
                "release_tag": "atlas-manifest",
                "gz_sha256": gz_sha256 or _sha256(gz_bytes),
                "json_sha256": _sha256(json_bytes),
                "gz_bytes": len(gz_bytes),
                "json_bytes": len(json_bytes),
                "note": "test pointer",
            }
        ),
        encoding="utf-8",
    )


def _pin_defaults(monkeypatch: pytest.MonkeyPatch, manifest_path: Path, pointer_path: Path) -> None:
    monkeypatch.setattr(manifest_io, "DEFAULT_MANIFEST", manifest_path)
    monkeypatch.setattr(manifest_io, "DEFAULT_POINTER", pointer_path)


def _request_url(request: object) -> str:
    return getattr(request, "full_url", str(request))


def test_load_manifest_returns_matching_local_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"entries": [{"lemma": "дім"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    manifest_path.write_bytes(json_bytes)
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)

    def fail_urlopen(*args, **kwargs):
        raise AssertionError("matching local manifest should not fetch")

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fail_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload


def test_load_manifest_fetches_decompresses_and_writes_when_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "слово"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)

    def fake_urlopen(request: object, timeout: int):
        assert _request_url(request) == "https://example.test/lexicon-manifest.json.gz"
        assert timeout == 60
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    assert manifest_path.read_bytes() == json_bytes


def test_load_manifest_refuses_to_clobber_richer_local_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-05T17:13:27+00:00",
    }
    local_payload = {
        "entries": [{"lemma": "слово"}, {"lemma": "вікно"}],
        "generated_at": "2026-07-06T17:13:27+00:00",
    }
    json_bytes = _json_bytes(release_payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    local_bytes = _json_bytes(local_payload)
    manifest_path.write_bytes(local_bytes)
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    with pytest.raises(ValueError, match="refusing to hydrate") as excinfo:
        manifest_io.load_manifest(path=manifest_path)

    assert "2 entries" in str(excinfo.value)
    assert "1 entries" in str(excinfo.value)
    assert "2026-07-06T17:13:27+00:00" in str(excinfo.value)
    assert "2026-07-05T17:13:27+00:00" in str(excinfo.value)
    assert "ATLAS_MANIFEST_FORCE_HYDRATE=1" in str(excinfo.value)
    assert manifest_path.read_bytes() == local_bytes


def test_load_manifest_hydrates_stale_poorer_local_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_payload = {
        "entries": [{"lemma": "слово"}, {"lemma": "вікно"}],
        "generated_at": "2026-07-06T17:13:27+00:00",
    }
    local_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-05T17:13:27+00:00",
    }
    json_bytes = _json_bytes(release_payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    manifest_path.write_bytes(_json_bytes(local_payload))
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    assert manifest_io.load_manifest(path=manifest_path) == release_payload
    assert manifest_path.read_bytes() == json_bytes


def test_load_manifest_force_hydrates_richer_local_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-05T17:13:27+00:00",
    }
    local_payload = {
        "entries": [{"lemma": "слово"}, {"lemma": "вікно"}],
        "generated_at": "2026-07-06T17:13:27+00:00",
    }
    json_bytes = _json_bytes(release_payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    manifest_path.write_bytes(_json_bytes(local_payload))
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setenv("ATLAS_MANIFEST_FORCE_HYDRATE", "1")
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    assert manifest_io.load_manifest(path=manifest_path) == release_payload
    assert manifest_path.read_bytes() == json_bytes


def test_load_manifest_refuses_newer_local_manifest_with_equal_entry_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-05T17:13:27+00:00",
    }
    local_payload = {
        "entries": [{"lemma": "слово"}],
        "generated_at": "2026-07-06T17:13:27+00:00",
    }
    json_bytes = _json_bytes(release_payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    local_bytes = _json_bytes(local_payload)
    manifest_path.write_bytes(local_bytes)
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    with pytest.raises(ValueError, match="refusing to hydrate"):
        manifest_io.load_manifest(path=manifest_path)

    assert manifest_path.read_bytes() == local_bytes


def test_load_manifest_raises_on_gz_sha256_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "хиба"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes, gz_sha256="0" * 64)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)

    def fake_urlopen(request: object, timeout: int):
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="gz sha256 mismatch") as excinfo:
        manifest_io.load_manifest(path=manifest_path)

    assert "gh release download atlas-manifest" in str(excinfo.value)
    assert STALE_POINTER_HINT in str(excinfo.value)
    assert not manifest_path.exists()


def test_load_manifest_retries_gz_sha256_mismatch_with_cache_bust(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "повтор"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    stale_gz_bytes = gzip.compress(_json_bytes({"entries": [{"lemma": "старий"}]}))
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    urls: list[str] = []

    def fake_urlopen(request: object, timeout: int):
        assert timeout == 60
        urls.append(_request_url(request))
        return io.BytesIO(stale_gz_bytes if len(urls) == 1 else gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    assert manifest_path.read_bytes() == json_bytes
    assert urls == [
        "https://example.test/lexicon-manifest.json.gz",
        (
            "https://example.test/lexicon-manifest.json.gz"
            f"?atlas_manifest_sha256={_sha256(gz_bytes)}&atlas_manifest_attempt=1"
        ),
    ]


def test_load_manifest_retries_transient_download_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "мережа"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    urls: list[str] = []

    def fake_urlopen(request: object, timeout: int):
        assert timeout == 60
        urls.append(_request_url(request))
        if len(urls) == 1:
            raise manifest_io.urllib.error.URLError("temporary release edge failure")
        return io.BytesIO(gz_bytes)

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    assert manifest_path.read_bytes() == json_bytes
    assert urls[1] == (
        "https://example.test/lexicon-manifest.json.gz"
        f"?atlas_manifest_sha256={_sha256(gz_bytes)}&atlas_manifest_attempt=1"
    )


def test_load_manifest_reports_final_download_error_after_prior_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "збій"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    stale_gz_bytes = gzip.compress(_json_bytes({"entries": [{"lemma": "старий"}]}))
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    urls: list[str] = []

    def fake_urlopen(request: object, timeout: int):
        assert timeout == 60
        urls.append(_request_url(request))
        if len(urls) == 1:
            return io.BytesIO(stale_gz_bytes)
        raise manifest_io.http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fake_urlopen)

    with pytest.raises(ValueError, match="failed to download Atlas manifest") as excinfo:
        manifest_io.load_manifest(path=manifest_path)

    assert "IncompleteRead" in str(excinfo.value)
    assert "gz sha256 mismatch" not in str(excinfo.value)
    assert not manifest_path.exists()


def test_hydrate_hardlinks_readonly_cache_and_atomic_write_replaces_link(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "кеш"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    assert manifest_io.load_manifest(path=manifest_path) == payload

    cache_path = Path(os.environ[manifest_io.MANIFEST_CACHE_ENV]) / f"{_sha256(gz_bytes)}.json"
    assert cache_path.is_file()
    assert stat.S_IMODE(cache_path.stat().st_mode) == 0o444
    assert cache_path.read_bytes() == json_bytes
    assert manifest_path.stat().st_ino == cache_path.stat().st_ino
    assert manifest_path.read_bytes() == json_bytes

    replacement = {"entries": [{"lemma": "заміна"}]}
    manifest_io.write_manifest(manifest_path, replacement)
    assert cache_path.read_bytes() == json_bytes
    assert manifest_path.stat().st_ino != cache_path.stat().st_ino
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == replacement


def test_hydrate_reuses_verified_cache_without_download(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "повторний"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "site" / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    cache_path = Path(os.environ[manifest_io.MANIFEST_CACHE_ENV]) / f"{_sha256(gz_bytes)}.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_bytes(json_bytes)
    os.chmod(cache_path, 0o444)

    def fail_urlopen(*_args, **_kwargs):
        raise AssertionError("verified cache should not fetch")

    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", fail_urlopen)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    assert manifest_path.stat().st_ino == cache_path.stat().st_ino


def test_hydrate_copies_when_hardlink_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"entries": [{"lemma": "копія"}], "enrichment_generated": True}
    json_bytes = _json_bytes(payload)
    gz_bytes = gzip.compress(json_bytes)
    manifest_path = tmp_path / "lexicon-manifest.json"
    pointer_path = tmp_path / "lexicon-manifest.pointer.json"
    _write_pointer(pointer_path, json_bytes=json_bytes, gz_bytes=gz_bytes)
    _pin_defaults(monkeypatch, manifest_path, pointer_path)
    monkeypatch.setattr(manifest_io.urllib.request, "urlopen", lambda *_args, **_kwargs: io.BytesIO(gz_bytes))

    def fail_link(src: str | Path, dst: str | Path) -> None:
        raise OSError(18, "Invalid cross-device link")

    monkeypatch.setattr(manifest_io.os, "link", fail_link)

    assert manifest_io.load_manifest(path=manifest_path) == payload
    cache_path = Path(os.environ[manifest_io.MANIFEST_CACHE_ENV]) / f"{_sha256(gz_bytes)}.json"
    assert manifest_path.read_bytes() == json_bytes
    assert manifest_path.stat().st_ino != cache_path.stat().st_ino
    assert stat.S_IMODE(manifest_path.stat().st_mode) == 0o444
    assert stat.S_IMODE(cache_path.stat().st_mode) == 0o444


_MANIFEST_FILENAME = "lexicon-manifest.json"


def _manifest_filename(text: str) -> bool:
    name = text.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    return name == _MANIFEST_FILENAME


def _div_parts(node: ast.AST) -> list[str]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _div_parts(node.left) + _div_parts(node.right)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    return []


def _is_write_mode(text: str) -> bool:
    return bool(text) and (text[0] in "wax" or "+" in text)


def _expr_is_manifest(node: ast.AST, names: set[str], returns_manifest: set[str]) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _manifest_filename(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        parts = _div_parts(node)
        return bool(parts) and _manifest_filename(parts[-1])
    if isinstance(node, ast.Name):
        return node.id in names
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in returns_manifest
    if isinstance(node, ast.IfExp):
        return _expr_is_manifest(node.body, names, returns_manifest) or _expr_is_manifest(
            node.orelse, names, returns_manifest
        )
    return False


def _bind_manifest_names(
    stmt: ast.Assign | ast.AnnAssign,
    bound: set[str],
    visible: set[str],
    returns_manifest: set[str],
) -> bool:
    value = stmt.value
    if value is None or not _expr_is_manifest(value, visible | bound, returns_manifest):
        return False
    targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
    added = False
    for target in targets:
        if isinstance(target, ast.Name) and target.id not in bound:
            bound.add(target.id)
            added = True
    return added


def _call_writes_manifest(node: ast.Call, names: set[str], returns_manifest: set[str]) -> bool:
    func = node.func
    if isinstance(func, ast.Name) and func.id == "open":
        path_arg = node.args[0] if node.args else None
        mode = node.args[1] if len(node.args) > 1 else None
        for keyword in node.keywords:
            if keyword.arg == "mode":
                mode = keyword.value
        return bool(
            path_arg is not None
            and _expr_is_manifest(path_arg, names, returns_manifest)
            and isinstance(mode, ast.Constant)
            and isinstance(mode.value, str)
            and _is_write_mode(mode.value)
        )
    if isinstance(func, ast.Attribute) and func.attr in {"write_text", "write_bytes", "open"}:
        mode = node.args[0] if func.attr == "open" and node.args else None
        writing = func.attr in {"write_text", "write_bytes"} or (
            isinstance(mode, ast.Constant) and isinstance(mode.value, str) and _is_write_mode(mode.value)
        )
        return writing and _expr_is_manifest(func.value, names, returns_manifest)
    return False


def _inplace_lines(tree: ast.AST) -> list[int]:
    functions = {
        stmt.name: stmt
        for stmt in tree.body
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    module_names: set[str] = set()
    returns_manifest: set[str] = set()
    local_names: dict[str, set[str]] = {name: set() for name in functions}
    changed = True
    while changed:
        changed = False
        for stmt in tree.body:
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                changed = (
                    _bind_manifest_names(stmt, module_names, module_names, returns_manifest) or changed
                )
        for name, fn in functions.items():
            locals_ = local_names[name]
            for inner in ast.walk(fn):
                if isinstance(inner, (ast.Assign, ast.AnnAssign)) and inner is not fn:
                    changed = (
                        _bind_manifest_names(inner, locals_, module_names, returns_manifest) or changed
                    )
            if name in returns_manifest:
                continue
            for inner in ast.walk(fn):
                if (
                    isinstance(inner, ast.Return)
                    and inner.value is not None
                    and _expr_is_manifest(inner.value, module_names | locals_, returns_manifest)
                ):
                    returns_manifest.add(name)
                    changed = True
                    break
    offenders: list[int] = []

    def _walk(node: ast.AST, names: set[str]) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _walk_scope(node, names | local_names.get(node.name, set()))
            return
        if isinstance(node, ast.Call) and _call_writes_manifest(node, names, returns_manifest):
            offenders.append(node.lineno)
        for child in ast.iter_child_nodes(node):
            _walk(child, names)

    def _walk_scope(fn: ast.FunctionDef | ast.AsyncFunctionDef, names: set[str]) -> None:
        for child in ast.iter_child_nodes(fn):
            _walk(child, names)

    _walk(tree, module_names)
    return offenders


def _inplace_manifest_writers(root: Path) -> list[str]:
    found: list[str] = []
    for path in sorted(root.glob("scripts/lexicon/*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        rel = path.relative_to(root).as_posix()
        found.extend(f"{rel}:{line}" for line in _inplace_lines(tree))
    return found


def test_lexicon_scripts_do_not_open_manifest_inplace() -> None:
    sample = ast.parse(
        "def write(path):\n"
        "    path = root / 'site' / 'src' / 'data' / 'lexicon-manifest.json'\n"
        "    open(path, 'w')\n"
        "    write_manifest(path, {})\n"
    )
    assert _inplace_lines(sample) == [3]
    root = Path(__file__).resolve().parents[1]
    assert _inplace_manifest_writers(root) == []
