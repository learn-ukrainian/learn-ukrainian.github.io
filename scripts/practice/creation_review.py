"""Offline Practice Hub creation-review admission (no provider calls).

Identity bytes are UTF-8 canonical JSON [kind, prompt, answer, calque-or-lemma]
(ensure_ascii=False, separators=(',', ':')); no Unicode/stress normalization.
Receipt frame_sha binds canonical JSON {identity: [...], source: {...}}.
Heritage source contains the frame and pair metadata except the frames list;
cloze source is the normalized factory candidate, including provenance.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_LEDGER = Path(__file__).resolve().parents[2] / 'data/lexicon/practice-creation-review.json'
_SHA = re.compile(r'[0-9a-f]{64}')


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def frame_identity(kind: str, prompt: str, answer: str, contrast: str) -> str:
    return _sha([kind, prompt, answer, contrast])


def frame_sha(kind: str, prompt: str, answer: str, contrast: str, source: dict) -> str:
    return _sha({'identity': [kind, prompt, answer, contrast], 'source': source})


def heritage_source(pair: dict, frame: dict) -> dict:
    return {'pair': {key: value for key, value in pair.items() if key != 'frames'}, 'frame': frame}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate ledger key')
        result[key] = value
    return result


@dataclass
class CreationReview:
    grandfathered: frozenset[str] = frozenset()
    receipts: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_path(cls, path: Path = DEFAULT_LEDGER) -> CreationReview:
        try:
            payload = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_object)
            if not isinstance(payload, dict) or payload.get('schema_version') != 1:
                raise ValueError('invalid ledger schema')
            baseline = payload.get('grandfathered')
            receipts = payload.get('receipts')
            if (not isinstance(baseline, list)
                    or any(not isinstance(key, str) or not _SHA.fullmatch(key) for key in baseline)
                    or not isinstance(receipts, dict)):
                raise ValueError('invalid ledger entries')
            return cls(frozenset(baseline), receipts)
        except (OSError, ValueError) as exc:
            print(f'WARN: creation-review ledger unavailable ({type(exc).__name__}); fail-closed', file=sys.stderr)
            return cls()

    def allows(self, kind: str, prompt: str, answer: str, contrast: str, source: dict) -> bool:
        identity = frame_identity(kind, prompt, answer, contrast)
        if identity in self.grandfathered:
            return True
        receipt = self.receipts.get(identity)
        if isinstance(receipt, dict):
            reviewed_at = receipt.get('reviewed_at')
            try:
                timestamp = datetime.fromisoformat(reviewed_at.replace('Z', '+00:00')) if isinstance(reviewed_at, str) else None
            except ValueError:
                timestamp = None
            model = receipt.get('resolved_model')
            if (receipt.get('agent') == 'agy'
                    and isinstance(model, str) and re.fullmatch(r'gemini-[A-Za-z0-9][A-Za-z0-9._-]*', model)
                    and receipt.get('verdict') == 'pass'
                    and timestamp is not None and timestamp.utcoffset() is not None
                    and receipt.get('frame_sha') == frame_sha(kind, prompt, answer, contrast, source)):
                return True
        print(f'WARN: creation-review {kind} {identity} dropped: missing or invalid AGY PASS receipt', file=sys.stderr)
        return False
