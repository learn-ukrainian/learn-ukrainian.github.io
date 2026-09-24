"""A complete temporary curriculum tree for the plan-review input tests (#8397 E3c-2).

Built on the plan-validate fixture world (tests/curriculum/test_plan_validate.py):
plan, pack + lock, word store + lock, prior plan, arc, grammar registry, scope
sidecar. On top of it this adds what the plan-review manifest also hashes — the
decisions record and the base-layer request the planned learner state joins —
gives the plan a stale evidence_ref.sha256 (a provisional pack), and turns the
tree into a git repository whose origin/main is HEAD, so the append-only
registry check has a merge base. The pack-verify function is replaced by a fake
(the real one needs the sources database); its own tests use a fake Sources.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from scripts.curriculum.validate.validate import main as validate_main
from tests.curriculum.test_plan_validate import LEVEL, SLUG, World, build_base, write_world

STALE_SHA = "ab12" * 16
GIT_IDENTITY = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.com", "-c", "commit.gpgsign=false"]


@dataclass(frozen=True)
class Env:
    root: Path
    world: World

    @property
    def plan_path(self) -> Path:
        return self.world.plan_path

    @property
    def pack_path(self) -> Path:
        return self.world.pack_path

    @property
    def words_path(self) -> Path:
        return self.world.words_path

    @property
    def plans_dir(self) -> Path:
        return self.plan_path.parent

    @property
    def evidence_dir(self) -> Path:
        return self.pack_path.parent

    @property
    def state_dir(self) -> Path:
        return self.evidence_dir / "_state" / SLUG

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()


def git(root: Path, *args: str) -> None:
    done = subprocess.run(["git", *GIT_IDENTITY, *args], cwd=root, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr


def build_env(root: Path, *, git_repo: bool = True) -> Env:
    plan, pack, words = build_base()
    words["words"][7]["pos"] = "noun"  # W-008 is the base layer of the planned learner state
    world = write_world(root, plan, pack, words)
    plan_doc = yaml.safe_load(world.plan_path.read_bytes())
    plan_doc["evidence_ref"]["sha256"] = STALE_SHA  # the provisional pack is not promoted yet
    world.plan_path.write_bytes(yaml.safe_dump(plan_doc, allow_unicode=True, sort_keys=False).encode("utf-8"))
    plans_dir, evidence_dir = world.plan_path.parent, world.pack_path.parent
    (plans_dir / "_decisions.yaml").write_text("decisions: []\n", encoding="utf-8")
    (evidence_dir / "_base.request.yaml").write_text(
        yaml.safe_dump({"words": [{"lemma": "lemma-eight", "pos": "noun"}]}), encoding="utf-8"
    )
    if git_repo:
        git(root, "init", "-q", "-b", "main")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "baseline")
        git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    return Env(root=root, world=world)


def validate_provisional(env: Env, *extra: str) -> int:
    return validate_main([LEVEL, SLUG, "--plan", str(env.plan_path), "--provisional-pack", "--write-report", *extra])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
