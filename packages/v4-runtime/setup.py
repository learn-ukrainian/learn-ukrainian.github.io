"""Setuptools build hook: public assets and provenance are wheel resources."""

from build_assets import collect_assets, write_manifest
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildRuntime(build_py):
    def run(self):
        super().run()
        from pathlib import Path

        destination = Path(self.build_lib) / "learn_ukrainian_v4_runtime"
        collect_assets(destination)
        write_manifest(destination)


setup(cmdclass={"build_py": BuildRuntime})
