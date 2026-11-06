"""The configured-entry-point loader confines product ``scripts.*`` modules to one product root (C-4764).

Each test builds the extracted layout in-process: a product checkout under ``tmp_path`` with its
own ``scripts`` package and the product marker, not on ``sys.path``, while the machinery's cached
``scripts`` entry is hidden for the test (the machinery package is renamed once extracted). Product
code under test appends to a run log, so a refusal can be proven to come before any product code ran.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
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


def test_a_package_that_repoints_its_search_path_is_refused_before_its_child_runs(product, tmp_path):
    """The package's own code moves its search path to another checkout: that checkout's module never runs."""
    foreign = tmp_path / "other" / "scripts" / "pkg"
    foreign.mkdir(parents=True)
    (foreign / "leaf.py").write_text(product.recording("foreign-leaf"), encoding="utf-8")
    product.write("pkg/__init__.py", product.recording("pkg", f"__path__.insert(0, {str(foreign)!r})\n"))
    product.write("pkg/leaf.py", product.recording("leaf"))
    product.names.append("scripts.pkg.leaf")

    with pytest.raises(ConfiguredModuleError, match=r"scripts\.pkg searches outside"):
        load_configured_module("scripts.pkg.leaf")

    assert product.ran() == ["scripts", "pkg"]
    assert "scripts.pkg.leaf" not in sys.modules


def test_a_foreign_cached_part_below_a_missing_package_is_refused_before_anything_runs(product, tmp_path, monkeypatch):
    """Every cached part is checked on its own first, even below a package that does not exist."""
    name = "scripts.lu_confined_missing.leaf"
    foreign = ModuleType(name)
    foreign.__file__ = str(tmp_path / "other" / "scripts" / "lu_confined_missing" / "leaf.py")
    monkeypatch.setitem(sys.modules, name, foreign)

    with pytest.raises(ConfiguredModuleError, match="not a file in this checkout"):
        load_configured_module(name)

    assert sys.modules[name] is foreign
    assert "scripts" not in sys.modules
    assert product.ran() == []


def test_a_cached_module_is_used_without_rerunning_its_missing_ancestors(product):
    """As an ordinary import: a cached module, or a cached parent of the module, is used as it is."""
    product.write(
        "pkg/__init__.py", product.recording("pkg", "import sys\nassert 'scripts.pkg.sub' not in sys.modules\n")
    )
    product.write("pkg/sub/__init__.py", product.recording("sub"))
    product.write("pkg/sub/leaf.py", product.recording("leaf", "VALUE = 17\n"))
    product.write("pkg/sub/other.py", product.recording("other", "VALUE = 18\n"))
    product.names.extend(["scripts.pkg.sub.leaf", "scripts.pkg.sub.other"])
    leaf = load_configured_module("scripts.pkg.sub.leaf")
    sys.modules.pop("scripts.pkg")

    assert load_configured_module("scripts.pkg.sub.leaf") is leaf
    assert load_configured_module("scripts.pkg.sub.other").VALUE == 18

    assert product.ran() == ["scripts", "pkg", "sub", "leaf", "other"]
    assert "scripts.pkg" not in sys.modules


def test_an_uninspectable_ordinary_namespace_path_refuses_without_cache_mutation(product, tmp_path, monkeypatch):
    """A dynamic namespace path with a missing ancestor must give a typed refusal, not a raw KeyError."""
    product.write("pkg/__init__.py", product.recording("pkg"))
    name = product.leaf(product.recording("leaf", "VALUE = 17\n"), package="pkg.ns")
    monkeypatch.syspath_prepend(str(product.root))
    leaf = importlib.import_module(name)
    namespace = sys.modules["scripts.pkg.ns"]
    top = sys.modules["scripts"]
    parent = sys.modules.pop("scripts.pkg")
    assert importlib.import_module(name) is leaf
    foreign = Product(tmp_path / "foreign", product.runs)
    foreign.write("__init__.py", foreign.recording("foreign-scripts"))
    foreign.write("pkg/__init__.py", foreign.recording("foreign-pkg"))
    foreign.write("pkg/ns/__init__.py", foreign.recording("foreign-ns"))
    foreign.write(f"pkg/ns/{name.rpartition('.')[2]}.py", foreign.recording("foreign-leaf"))
    monkeypatch.syspath_prepend(str(foreign.root))

    with pytest.raises(ConfiguredModuleError, match=r"missing ancestor.*scripts\.pkg") as caught:
        load_configured_module(name)

    assert caught.value.name == name
    assert isinstance(caught.value.__cause__, KeyError)
    assert caught.value.__cause__.args == ("scripts.pkg",)
    assert sys.modules[name] is leaf
    assert sys.modules["scripts.pkg.ns"] is namespace
    assert sys.modules["scripts"] is top and top.pkg is parent
    assert "scripts.pkg" not in sys.modules
    assert product.ran() == ["scripts", "pkg", "leaf"]


def test_a_load_waiting_on_an_ordinary_import_does_not_deadlock(product, monkeypatch):
    """A product module, imported the ordinary way in one thread, calls the loader while another thread waits for it."""
    load_configured_module(product.leaf("VALUE = 1\n"))
    events = ModuleType(f"lu_confined_events_{uuid.uuid4().hex}")
    events.started = threading.Event()
    events.resume = threading.Event()
    events.load = load_configured_module
    monkeypatch.setitem(sys.modules, events.__name__, events)
    other = product.leaf("VALUE = 2\n")
    blocked = product.leaf(
        f"import sys\nevents = sys.modules[{events.__name__!r}]\nevents.started.set()\n"
        f"events.resume.wait(10)\nOTHER = events.load({other!r})\n"
    )
    results: dict[str, ModuleType] = {}
    errors: list[BaseException] = []

    def run(label: str, load) -> None:
        try:
            results[label] = load(blocked)
        except BaseException as exc:
            errors.append(exc)

    ordinary = threading.Thread(target=run, args=("ordinary", importlib.import_module), daemon=True)
    ordinary.start()
    assert events.started.wait(10)
    configured = threading.Thread(target=run, args=("configured", load_configured_module), daemon=True)
    configured.start()
    # The configured load now waits for the module the ordinary import is still running.
    configured.join(timeout=0.5)
    assert configured.is_alive()
    events.resume.set()
    ordinary.join(timeout=10)
    configured.join(timeout=10)

    assert not ordinary.is_alive() and not configured.is_alive()
    assert errors == []
    assert results["ordinary"] is results["configured"]
    assert results["configured"].OTHER.VALUE == 2


@pytest.mark.parametrize("package_target", [False, True], ids=["module", "package"])
def test_failed_cached_import_retry_never_executes_a_foreign_checkout(product, tmp_path, monkeypatch, package_target):
    """F5: all external cache/path changes precede entry; only ordinary failure cleanup occurs during the call."""
    events = ModuleType(f"lu_confined_events_{uuid.uuid4().hex}")
    events.started = threading.Event()
    events.resume = threading.Event()
    entered = threading.Event()
    monkeypatch.setitem(sys.modules, events.__name__, events)
    package = f"lu_confined_retry_{uuid.uuid4().hex}"
    name = f"scripts.{package}.leaf"
    product.write(f"{package}/__init__.py", product.recording("pkg"))
    relative = f"{package}/leaf/__init__.py" if package_target else f"{package}/leaf.py"
    product.write(
        relative,
        product.recording(
            "trusted-leaf",
            f"import sys\nevents = sys.modules[{events.__name__!r}]\nevents.started.set()\n"
            "assert events.resume.wait(10)\nraise RuntimeError('ordinary import failed')\n",
        ),
    )
    foreign = Product(tmp_path / "foreign", product.runs)
    foreign.write("__init__.py", foreign.recording("foreign-scripts"))
    foreign.write(f"{package}/__init__.py", foreign.recording("foreign-pkg"))
    foreign.write(relative, foreign.recording("foreign-leaf"))
    monkeypatch.syspath_prepend(str(product.root))
    original_import = product_entry._import

    def observed_import(prefix, scripts_dir):
        if prefix == name:
            entered.set()
        return original_import(prefix, scripts_dir)

    monkeypatch.setattr(product_entry, "_import", observed_import)
    errors: dict[str, BaseException] = {}

    def run(label, load):
        try:
            load(name)
        except BaseException as exc:
            errors[label] = exc

    ordinary = threading.Thread(target=run, args=("ordinary", importlib.import_module), daemon=True)
    configured = threading.Thread(target=run, args=("configured", load_configured_module), daemon=True)
    ordinary.start()
    try:
        assert events.started.wait(10)
        assert sys.modules[name].__spec__._initializing
        sys.modules.pop("scripts")
        sys.modules.pop(f"scripts.{package}")
        monkeypatch.syspath_prepend(str(foreign.root))
        configured.start()
        assert entered.wait(10)
    finally:
        events.resume.set()
        ordinary.join(timeout=10)
        if configured.ident is not None:
            configured.join(timeout=10)

    assert not ordinary.is_alive() and not configured.is_alive()
    assert isinstance(errors.get("ordinary"), RuntimeError)
    assert not [label for label in product.ran() if label.startswith("foreign-")]
    assert not [
        prefix for prefix in ("scripts", f"scripts.{package}", name)
        if prefix in sys.modules and Path(sys.modules[prefix].__file__).is_relative_to(foreign.root)
    ]
    assert isinstance(errors.get("configured"), RuntimeError)


def test_concurrent_first_scripts_import_keeps_ordinary_initializing_state_and_does_not_deadlock(product, monkeypatch):
    """C1: first scripts initialization can nest a configured load while another configured call waits."""
    events = ModuleType(f"lu_confined_events_{uuid.uuid4().hex}")
    events.started = threading.Event()
    events.resume = threading.Event()
    events.load = load_configured_module
    monkeypatch.setitem(sys.modules, events.__name__, events)
    inner = product.leaf(product.recording("inner", "VALUE = 19\n"))
    outer = product.leaf(product.recording("outer", "VALUE = 20\n"))
    product.write(
        "__init__.py",
        product.recording(
            "scripts",
            f"import sys, importlib\nevents = sys.modules[{events.__name__!r}]\n"
            "INITIALIZING = __spec__._initializing\nSELF = importlib.import_module(__name__)\n"
            f"events.started.set()\nassert events.resume.wait(10)\nINNER = events.load({inner!r})\n",
        ),
    )
    monkeypatch.syspath_prepend(str(product.root))
    results = {}
    errors = []

    def run(label, load, name):
        try:
            results[label] = load(name)
        except BaseException as exc:
            errors.append(exc)

    configured = threading.Thread(target=run, args=("configured", load_configured_module, outer), daemon=True)
    ordinary = threading.Thread(target=run, args=("ordinary", importlib.import_module, "scripts"), daemon=True)
    before = list(sys.meta_path)
    configured.start()
    try:
        assert events.started.wait(10)
        initializing = sys.modules["scripts"]
        assert initializing.__spec__._initializing
        assert initializing.INITIALIZING and initializing.SELF is initializing
        ordinary.start()
        ordinary.join(timeout=0.2)
        assert ordinary.is_alive() and "ordinary" not in results, (results, errors)
    finally:
        events.resume.set()
        configured.join(timeout=10)
        if ordinary.ident is not None:
            ordinary.join(timeout=10)
    assert not ordinary.is_alive() and not configured.is_alive()
    assert errors == []
    assert results["ordinary"] is initializing
    assert not initializing.__spec__._initializing
    assert initializing.INNER.VALUE == 19 and results["configured"].VALUE == 20
    assert product.ran() == ["scripts", "inner", "outer"]
    assert sys.meta_path == before


@pytest.mark.parametrize("inner_fails", [False, True], ids=["inner-success", "inner-failure"])
@pytest.mark.parametrize("outer_fails", [False, True], ids=["outer-success", "outer-failure"])
def test_nested_scopes_restore_the_outer_guard_and_clean_up_exceptions(product, tmp_path, monkeypatch, inner_fails, outer_fails):
    """C3: nested success and BaseException restore exactly the active outer registration."""
    before = list(sys.meta_path)
    inner = product.leaf("raise SystemExit(8)\n" if inner_fails else "VALUE = 21\n")
    foreign = Product(tmp_path / "foreign", product.runs)
    foreign.write("__init__.py", foreign.recording("foreign-scripts"))
    foreign_name = foreign.leaf(foreign.recording("foreign-leaf"))
    events = ModuleType(f"lu_confined_events_{uuid.uuid4().hex}")
    snapshots = []

    def nest():
        outer_scope = list(sys.meta_path)
        assert outer_scope != before
        if inner_fails:
            with pytest.raises(SystemExit):
                load_configured_module(inner)
            assert inner not in sys.modules
        else:
            assert load_configured_module(inner).VALUE == 21
        assert sys.meta_path == outer_scope
        cached = {key: value for key, value in sys.modules.items() if key == "scripts" or key.startswith("scripts.")}
        bindings = dict(vars(sys.modules["scripts"]))
        with pytest.raises(ConfiguredModuleError, match="not a file in this checkout"):
            load_configured_module(foreign_name, product_root=foreign.root)
        assert all(sys.modules[key] is value for key, value in cached.items())
        assert {key for key in sys.modules if key == "scripts" or key.startswith("scripts.")} == set(cached)
        assert vars(sys.modules["scripts"]) == bindings
        assert sys.meta_path == outer_scope
        snapshots.append(outer_scope)

    events.nest = nest
    monkeypatch.setitem(sys.modules, events.__name__, events)
    outer = product.leaf(
        f"import sys\nsys.modules[{events.__name__!r}].nest()\n"
        + ("raise SystemExit(9)\n" if outer_fails else "VALUE = 22\n")
    )
    if outer_fails:
        with pytest.raises(SystemExit):
            load_configured_module(outer)
        assert outer not in sys.modules
    else:
        assert load_configured_module(outer).VALUE == 22
    assert len(snapshots) == 1
    assert sys.meta_path == before
    assert not [label for label in product.ran() if label.startswith("foreign-")]


def test_overlapping_thread_scopes_guard_only_their_own_names_and_remove_only_their_own_finder(product, tmp_path, monkeypatch):
    """C3: a scope ignores another thread and unrelated names, including while the other scope exits."""
    load_configured_module(product.leaf("VALUE = 1\n"))
    first = product.leaf("VALUE = 31\n")
    second = product.leaf("raise SystemExit(4)\n")
    ambient = f"lu_confined_ambient_{uuid.uuid4().hex}"
    (tmp_path / f"{ambient}.py").write_text(product.recording("ambient", "VALUE = 32\n"), encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    observed = []

    class AmbientFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname in (first, second):
                observed.append((threading.current_thread().name, fullname))
                return importlib.machinery.ModuleSpec(fullname, None, origin="ambient-sentinel")
            return None

    ambient_finder = AmbientFinder()
    monkeypatch.setattr(sys, "meta_path", [ambient_finder, *sys.meta_path])
    before = list(sys.meta_path)
    entered = {name: threading.Event() for name in (first, second)}
    release = {name: threading.Event() for name in (first, second)}
    original_import = product_entry._import
    probes = {}
    results = {}
    errors = {}

    def observed_import(prefix, scripts_dir):
        if prefix in entered:
            entered[prefix].set()
            assert release[prefix].wait(10)
            other = second if prefix == first else first
            probes[prefix] = importlib.util.find_spec(other).origin
            assert importlib.import_module(ambient).VALUE == 32
        return original_import(prefix, scripts_dir)

    monkeypatch.setattr(product_entry, "_import", observed_import)

    def run(name):
        try:
            results[name] = load_configured_module(name)
        except BaseException as exc:
            errors[name] = exc

    threads = {name: threading.Thread(target=run, args=(name,), name=name, daemon=True) for name in (first, second)}
    try:
        for thread in threads.values():
            thread.start()
        assert all(event.wait(10) for event in entered.values())
        active = list(sys.meta_path)
        assert len(active) == len(before) + 2
        assert importlib.util.find_spec(first).origin == "ambient-sentinel"
        assert importlib.util.find_spec(second).origin == "ambient-sentinel"
        release[first].set()
        threads[first].join(timeout=10)
        assert not threads[first].is_alive()
        assert len(sys.meta_path) == len(before) + 1
        assert results[first].VALUE == 31
        # The first scope's exit must not remove the second scope's guard.
        release[second].set()
        threads[second].join(timeout=10)
    finally:
        for event in release.values():
            event.set()
        for thread in threads.values():
            if thread.ident is not None:
                thread.join(timeout=10)
        sys.modules.pop(ambient, None)
    assert all(not thread.is_alive() for thread in threads.values())
    assert isinstance(errors.get(second), SystemExit) and first not in errors
    assert probes[first] == "ambient-sentinel"
    # first is now cached, so the other thread observes its trusted ordinary cached spec.
    assert Path(probes[second]).is_relative_to(product.root)
    assert (first, first) not in observed and (second, second) not in observed
    assert second not in sys.modules
    assert product.ran() == ["scripts", "ambient"]
    assert sys.meta_path == before


@pytest.mark.parametrize("missing", ["lu_confined_missing.leaf", "pkg.lu_confined_missing"])
def test_guarded_missing_names_raise_without_delegating_to_an_ambient_finder(product, monkeypatch, missing):
    """C3: an absent guarded ancestor or target must fail closed, even with an ambient finder ready."""
    product.write("pkg/__init__.py")
    consulted = []

    class AmbientFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname == "scripts" or fullname.startswith("scripts."):
                consulted.append(fullname)
                raise AssertionError("guarded resolution fell through")
            return None

    monkeypatch.setattr(sys, "meta_path", [AmbientFinder(), *sys.meta_path])
    before = list(sys.meta_path)
    with pytest.raises(ModuleNotFoundError):
        load_configured_module(f"scripts.{missing}")
    assert consulted == []
    assert sys.meta_path == before


def test_last_scope_cleanup_does_not_skip_an_unrelated_imports_ambient_finder(product, tmp_path, monkeypatch):
    """C3: cleanup must not shift the finder list under an unrelated ordinary import already traversing it."""
    load_configured_module(product.leaf("VALUE = 1\n"))
    target = product.leaf("VALUE = 41\n")
    unrelated = f"lu_confined_unrelated_{uuid.uuid4().hex}"
    source = tmp_path / "not-on-the-import-path" / "ambient.py"
    source.parent.mkdir()
    source.write_text(product.recording("ambient", "VALUE = 42\n"), encoding="utf-8")
    reached_guard = threading.Event()
    resume_ordinary = threading.Event()
    entered = threading.Event()
    resume_configured = threading.Event()

    class AmbientFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname == unrelated:
                return importlib.util.spec_from_file_location(fullname, source)
            return None

    monkeypatch.setattr(sys, "meta_path", [AmbientFinder(), *sys.meta_path])
    before = list(sys.meta_path)
    original_find = product_entry._ProductFinder.find_spec
    original_import = product_entry._import

    def observed_find(self, fullname, path=None, target=None):
        if fullname == unrelated:
            reached_guard.set()
            assert resume_ordinary.wait(10)
        return original_find(self, fullname, path, target)

    def observed_import(prefix, scripts_dir):
        module = original_import(prefix, scripts_dir)
        if prefix == target:
            entered.set()
            assert resume_configured.wait(10)
        return module

    monkeypatch.setattr(product_entry._ProductFinder, "find_spec", observed_find)
    monkeypatch.setattr(product_entry, "_import", observed_import)
    results = {}
    errors = {}

    def run(label, load, name):
        try:
            results[label] = load(name)
        except BaseException as exc:
            errors[label] = exc

    configured = threading.Thread(target=run, args=("configured", load_configured_module, target), daemon=True)
    ordinary = threading.Thread(target=run, args=("ordinary", importlib.import_module, unrelated), daemon=True)
    configured.start()
    try:
        assert entered.wait(10)
        ordinary.start()
        assert reached_guard.wait(10)
        resume_configured.set()
        configured.join(timeout=10)
        assert not configured.is_alive()
        assert results["configured"].VALUE == 41
        assert sys.meta_path == before
    finally:
        resume_configured.set()
        resume_ordinary.set()
        configured.join(timeout=10)
        if ordinary.ident is not None:
            ordinary.join(timeout=10)
        sys.modules.pop(unrelated, None)
    assert not ordinary.is_alive()
    assert errors == {}
    assert results["ordinary"].VALUE == 42
    assert product.ran() == ["scripts", "ambient"]
    assert sys.meta_path == before


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


def test_a_failed_top_level_execution_leaves_nothing_cached(product, monkeypatch):
    events = ModuleType(f"lu_confined_events_{uuid.uuid4().hex}")
    monkeypatch.setitem(sys.modules, events.__name__, events)
    product.write(
        "__init__.py",
        product.recording(
            "scripts",
            f"import sys\nevents = sys.modules[{events.__name__!r}]\n"
            "events.module = sys.modules[__name__]\nevents.initializing = __spec__._initializing\n"
            "raise SystemExit(3)\n",
        ),
    )
    name = product.leaf("VALUE = 2\n")
    before = list(sys.meta_path)
    with pytest.raises(SystemExit):
        load_configured_module(name)
    assert "scripts" not in sys.modules
    assert events.initializing and not events.module.__spec__._initializing
    assert sys.meta_path == before
    product.write("__init__.py", product.recording("scripts"))
    assert load_configured_module(name).VALUE == 2


def test_a_failed_leaf_import_is_neither_cached_nor_bound(product):
    name = product.leaf(product.recording("leaf", "raise SystemExit(7)\n"))
    leaf = name.rpartition(".")[2]
    before = list(sys.meta_path)
    with pytest.raises(SystemExit):
        load_configured_module(name)
    assert name not in sys.modules
    assert leaf not in vars(sys.modules["scripts"])
    assert sys.meta_path == before
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
