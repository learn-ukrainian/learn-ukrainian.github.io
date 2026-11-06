"""The configured-entry-point loader confines product ``scripts.*`` modules to one product root (C-4764).

Each test builds the extracted layout in-process: a product checkout under ``tmp_path`` with its
own ``scripts`` package and the product marker, not on ``sys.path``, while the machinery's cached
``scripts`` entry is hidden for the test (the machinery package is renamed once extracted). Product
code under test appends to a run log, so a refusal can be proven to come before any product code ran.
"""

from __future__ import annotations

import importlib
import sys
import threading
import uuid
from pathlib import Path
from types import ModuleType

import pytest

from scripts.common import repo_root
from scripts.ops import product_entry
from scripts.ops.product_entry import ConfiguredModuleError, load_configured_module


class Product:
    """A product checkout outside ``sys.path`` and the names loaded from it."""

    def __init__(self, root: Path, runs: Path) -> None:
        self.root = root
        self.runs = runs
        self.names: list[str] = []

    def write(self, relative: str, source: str = "") -> Path:
        path = self.root / "scripts" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        importlib.invalidate_caches()
        return path

    def recording(self, label: str, body: str = "") -> str:
        """Module source that appends ``label`` to the run log when it executes."""
        return f"with open({str(self.runs)!r}, 'a') as _log:\n    _log.write({label + chr(10)!r})\n{body}"

    def leaf(self, source: str, *, package: str = "") -> str:
        """Write a uniquely named module (in ``package``, a dotted product package) and return its name."""
        leaf = f"lu_confined_{uuid.uuid4().hex}"
        directory = package.replace(".", "/")
        self.write(f"{directory}/{leaf}.py" if directory else f"{leaf}.py", source)
        name = ".".join(part for part in ("scripts", package, leaf) if part)
        self.names.append(name)
        return name

    def ran(self) -> list[str]:
        return self.runs.read_text(encoding="utf-8").splitlines() if self.runs.exists() else []


@pytest.fixture
def product(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "product"
    marker = root / repo_root.PRODUCT_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("levels: {}\n", encoding="utf-8")
    checkout = Product(root, tmp_path / "runs.log")
    checkout.write("__init__.py", checkout.recording("scripts"))
    monkeypatch.setenv(repo_root.PRODUCT_ROOT_ENV, str(root))
    # The extracted layout: no machinery package named scripts is cached.
    monkeypatch.delitem(sys.modules, "scripts")
    assert str(root) not in sys.path
    before = set(sys.modules)
    yield checkout
    # Drop every scripts entry the test added; monkeypatch then restores the machinery package.
    for name in set(sys.modules) - before:
        if name == "scripts" or name.startswith("scripts."):
            sys.modules.pop(name, None)


def test_loads_from_the_configured_root_not_from_sys_path(product, tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    (elsewhere / "scripts").mkdir(parents=True)
    (elsewhere / "scripts" / "__init__.py").write_text(product.recording("elsewhere"), encoding="utf-8")
    monkeypatch.syspath_prepend(str(elsewhere))
    name = product.leaf(product.recording("leaf", "import json\nVALUE = json.loads('41')\n"))

    module = load_configured_module(name, product_root=product.root)

    assert module.VALUE == 41
    assert Path(module.__file__).resolve().is_relative_to(product.root.resolve() / "scripts")
    package = sys.modules["scripts"]
    assert Path(package.__file__).resolve() == (product.root / "scripts" / "__init__.py").resolve()
    assert getattr(package, name.rpartition(".")[2]) is module
    assert load_configured_module(name) is module
    assert product.ran() == ["scripts", "leaf"]


def test_loads_a_module_in_product_subpackages(product):
    product.write("pkg/__init__.py", product.recording("pkg"))
    product.write("pkg/space/.keep")
    name = product.leaf(product.recording("leaf", "VALUE = 1\n"), package="pkg.space")

    module = load_configured_module(name)

    assert module.VALUE == 1
    assert sys.modules["scripts.pkg"].space is sys.modules["scripts.pkg.space"]
    assert product.ran() == ["scripts", "pkg", "leaf"]


def test_an_unusable_configured_root_refuses_without_falling_back(product, tmp_path, monkeypatch):
    name = product.leaf(product.recording("leaf"))
    monkeypatch.setenv(repo_root.PRODUCT_ROOT_ENV, str(tmp_path / "no-marker"))
    with pytest.raises(ConfiguredModuleError, match="no product checkout"):
        load_configured_module(name)
    with pytest.raises(ConfiguredModuleError, match="absolute"):
        load_configured_module(name, product_root=Path("relative"))
    assert product.ran() == []
    assert "scripts" not in sys.modules


def test_a_foreign_cached_top_level_package_is_refused_and_kept(product, tmp_path, monkeypatch):
    name = product.leaf(product.recording("leaf"))
    foreign = ModuleType("scripts")
    foreign.__file__ = str(tmp_path / "other" / "scripts" / "__init__.py")
    foreign.__path__ = [str(tmp_path / "other" / "scripts")]
    monkeypatch.setitem(sys.modules, "scripts", foreign)

    with pytest.raises(ConfiguredModuleError, match="scripts is not a file in this checkout"):
        load_configured_module(name)

    assert sys.modules["scripts"] is foreign
    assert product.ran() == []


def test_a_cached_package_searching_another_checkout_is_refused(product, tmp_path, monkeypatch):
    load_configured_module(product.leaf("VALUE = 1\n"))
    package = sys.modules["scripts"]
    monkeypatch.setattr(package, "__path__", [*package.__path__, str(tmp_path / "other" / "scripts")])
    name = product.leaf(product.recording("second"))

    with pytest.raises(ConfiguredModuleError, match="searches outside"):
        load_configured_module(name)

    assert product.ran() == ["scripts"]


def test_a_foreign_cached_parent_package_is_refused_before_the_leaf_runs(product, tmp_path, monkeypatch):
    product.write("pkg/__init__.py")
    name = product.leaf(product.recording("leaf"), package="pkg")
    load_configured_module(product.leaf("VALUE = 1\n"))
    foreign = ModuleType("scripts.pkg")
    foreign.__file__ = str(tmp_path / "other" / "scripts" / "pkg" / "__init__.py")
    foreign.__path__ = [str(tmp_path / "other" / "scripts" / "pkg")]
    monkeypatch.setitem(sys.modules, "scripts.pkg", foreign)

    with pytest.raises(ConfiguredModuleError, match=r"scripts\.pkg is not a file in this checkout"):
        load_configured_module(name)

    assert sys.modules["scripts.pkg"] is foreign
    assert "leaf" not in product.ran()


def test_a_foreign_cached_leaf_is_refused_and_kept(product, tmp_path, monkeypatch):
    name = product.leaf(product.recording("leaf"))
    foreign = ModuleType(name)
    foreign.__file__ = str(tmp_path / "other" / "scripts" / "leaf.py")
    monkeypatch.setitem(sys.modules, name, foreign)

    with pytest.raises(ConfiguredModuleError, match="not a file in this checkout"):
        load_configured_module(name)

    assert sys.modules[name] is foreign
    assert product.ran() == []


def test_a_module_symlinked_out_of_the_root_is_refused_before_it_runs(product, tmp_path):
    outside = tmp_path / "outside.py"
    outside.write_text(product.recording("outside"), encoding="utf-8")
    name = product.leaf("")
    link = product.root / "scripts" / f"{name.rpartition('.')[2]}.py"
    link.unlink()
    link.symlink_to(outside)
    importlib.invalidate_caches()

    with pytest.raises(ConfiguredModuleError, match="not a file in this checkout"):
        load_configured_module(name)

    assert product.ran() == []
    assert name not in sys.modules


def test_a_package_symlinked_out_of_the_root_is_refused_before_it_runs(product, tmp_path):
    outside = tmp_path / "outside-pkg"
    outside.mkdir()
    (outside / "__init__.py").write_text(product.recording("outside-pkg"), encoding="utf-8")
    (outside / "leaf.py").write_text(product.recording("outside-leaf"), encoding="utf-8")
    package = f"lu_confined_{uuid.uuid4().hex}"
    (product.root / "scripts" / package).symlink_to(outside, target_is_directory=True)
    importlib.invalidate_caches()
    name = f"scripts.{package}.leaf"
    product.names.append(name)

    with pytest.raises(ConfiguredModuleError, match="not a file in this checkout"):
        load_configured_module(name)

    assert product.ran() == []


def test_a_namespace_package_is_refused_as_the_module(product):
    package = f"lu_confined_{uuid.uuid4().hex}"
    product.write(f"{package}/child/.keep")
    with pytest.raises(ConfiguredModuleError, match="None"):
        load_configured_module(f"scripts.{package}.child")
    assert product.ran() == []


def test_a_missing_module_raises_module_not_found_with_its_name(product):
    """As an ordinary import: the checked packages before the missing part are imported first."""
    with pytest.raises(ModuleNotFoundError) as caught:
        load_configured_module("scripts.lu_confined_absent.child")
    assert caught.value.name == "scripts.lu_confined_absent"
    product.write("pkg/__init__.py", product.recording("pkg"))
    with pytest.raises(ModuleNotFoundError) as caught:
        load_configured_module("scripts.pkg.lu_confined_absent")
    assert caught.value.name == "scripts.pkg.lu_confined_absent"
    assert "scripts.pkg" in sys.modules
    assert product.ran() == ["scripts", "pkg"]


def test_a_failed_top_level_execution_leaves_nothing_cached(product):
    product.write("__init__.py", product.recording("scripts", "raise SystemExit(3)\n"))
    name = product.leaf("VALUE = 2\n")
    with pytest.raises(SystemExit):
        load_configured_module(name)
    assert "scripts" not in sys.modules
    product.write("__init__.py", product.recording("scripts"))
    assert load_configured_module(name).VALUE == 2


def test_a_failed_leaf_import_is_neither_cached_nor_bound(product):
    name = product.leaf(product.recording("leaf", "raise SystemExit(7)\n"))
    leaf = name.rpartition(".")[2]
    with pytest.raises(SystemExit):
        load_configured_module(name)
    assert name not in sys.modules
    assert leaf not in vars(sys.modules["scripts"])
    product.write(f"{leaf}.py", "VALUE = 3\n")
    assert load_configured_module(name).VALUE == 3


def test_concurrent_loads_run_the_product_code_once(product):
    name = product.leaf(product.recording("leaf", "import time\ntime.sleep(0.2)\nREADY = True\n"))
    barrier = threading.Barrier(8)
    results: list[ModuleType] = []
    errors: list[BaseException] = []

    def load() -> None:
        barrier.wait()
        try:
            results.append(load_configured_module(name))
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=load) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert errors == []
    assert len(results) == 8 and all(module is results[0] and module.READY for module in results)
    assert product.ran() == ["scripts", "leaf"]


def test_this_checkout_still_loads_its_own_modules():
    """In the product checkout the machinery's own ``scripts`` package is the product's."""
    assert repo_root.product_root().resolve() == Path(product_entry.__file__).resolve().parents[2]
    module = load_configured_module("scripts.lib.readonly_sqlite")
    assert module is sys.modules["scripts.lib.readonly_sqlite"]
    assert Path(module.__file__).resolve().is_relative_to(repo_root.product_root().resolve() / "scripts")


def test_the_cached_checkout_package_searching_another_root_is_refused(tmp_path, monkeypatch):
    """The mixed setup: this checkout's cached ``scripts`` package, its search path reaching another root.

    Selecting the other root refuses the cached package itself; selecting this checkout refuses
    the foreign search path. Neither runs the other root's module or caches it.
    """
    import scripts

    other = tmp_path / "other"
    (other / "scripts").mkdir(parents=True)
    runs = tmp_path / "runs.log"
    leaf = f"lu_confined_{uuid.uuid4().hex}"
    (other / "scripts" / f"{leaf}.py").write_text(f"open({str(runs)!r}, 'a').write('ran')\n", encoding="utf-8")
    importlib.invalidate_caches()
    monkeypatch.setattr(scripts, "__path__", [*scripts.__path__, str(other / "scripts")])
    this_checkout = Path(product_entry.__file__).resolve().parents[2]

    with pytest.raises(ConfiguredModuleError, match="scripts is not a file in this checkout"):
        load_configured_module(f"scripts.{leaf}", product_root=other)
    with pytest.raises(ConfiguredModuleError, match="scripts searches outside"):
        load_configured_module(f"scripts.{leaf}", product_root=this_checkout)

    assert not runs.exists()
    assert f"scripts.{leaf}" not in sys.modules
