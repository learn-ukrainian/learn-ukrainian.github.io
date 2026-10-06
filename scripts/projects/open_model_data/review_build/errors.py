"""Diagnostics deliberately carry no text, paths or human locators."""

import re


class BuildError(Exception):
    def __init__(self, code: str, *, record_id: str = "", component: str = "", row_key: str = ""):
        self.code = code
        self.record_id = record_id
        self.component = component
        self.row_key = row_key
        # Hash arbitrary row keys: even a database primary key can contain a headword.
        super().__init__(code)

    def diagnostic(self) -> dict[str, str]:
        from .contract import digest

        return {
            "error": self.code if re.fullmatch(r"[a-z_]+", self.code) else "build_failure",
            "record_id": self.record_id if re.fullmatch(r"[0-9a-f]{64}", self.record_id) else "",
            "component": self.component if re.fullmatch(r"C[1-79]", self.component) else "",
            "row_key": digest(self.row_key.encode()) if self.row_key else "",
        }


def require(condition: bool, code: str) -> None:
    if not condition:
        raise BuildError(code)
