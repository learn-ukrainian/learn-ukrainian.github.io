"""Product catalogue schema patterns agree across Python and ECMA-262 engines."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


SCHEMA = json.loads((REPO / 'docs/knowledge/catalogue.schema.json').read_text(encoding='utf-8'))


BOM = chr(0xFEFF)


NEL = chr(0x85)
LS, PS = chr(0x2028), chr(0x2029)


def schema_patterns(node=SCHEMA, where='#'):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'pattern':
                yield where, value
            else:
                yield from schema_patterns(value, f'{where}/{key}')
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from schema_patterns(value, f'{where}/{index}')


def test_patterns_use_no_engine_dependent_constructs():
    found = list(schema_patterns())
    assert len(found) >= 10
    for where, pattern in found:
        # Remove escaped characters and bracket classes, then nothing engine-dependent may remain.
        bare = re.sub(r'\[(?:\\.|[^\]\\])*\]', '', re.sub(r'\\u[0-9a-f]{4}', '', pattern))
        assert not re.search(r'\\[sSwWdDbBAZz]', pattern), where
        assert '$' not in pattern, where
        assert '.' not in re.sub(r'\\.', '', bare), where  # an unescaped dot outside a class


def corpus():
    base = ['abc', 'docs/a.md', 'data/a.db', 'data/a/', 'id:ab', 'ab', 'docs/a/**', 'a b', 'Ґанок']
    odd = ['\n', '\r', NEL, LS, PS, BOM, chr(0xA0), chr(0x3000), chr(0x1F600), ' ', '\t', '.', '/', '..']
    out = list(base)
    for s in base:
        for c in odd:
            out += [s + c, c + s, s[:1] + c + s[1:]]
    out += [c * 3 for c in odd] + [BOM + BOM + BOM, LS + PS + ' ', NEL * 3, 'docs/../a.md', 'data/x/../y.db']
    return out


def test_python_and_ecma_engines_agree_on_every_schema_pattern():
    node = shutil.which('node')
    if node is None:
        if os.environ.get('CI'):
            pytest.fail('node is required in CI to compare the ECMA-262 engine')
        pytest.skip('node is not installed; CI runs this comparison')
    patterns = [p for _, p in schema_patterns()]
    strings = corpus()
    script = ('const d=JSON.parse(require("fs").readFileSync(0,"utf8"));'
              'console.log(JSON.stringify(d.p.map(p=>{const r=new RegExp(p,"u");return d.s.map(s=>r.test(s));})));')
    payload = json.dumps({'p': patterns, 's': strings})
    ecma = json.loads(subprocess.run([node, '-e', script], input=payload, capture_output=True, text=True,
                                     check=True, timeout=60).stdout)
    script_plain = script.replace('new RegExp(p,"u")', 'new RegExp(p)')
    ecma_plain = json.loads(subprocess.run([node, '-e', script_plain], input=payload, capture_output=True,
                                           text=True, check=True, timeout=60).stdout)
    for p, js, js_plain in zip(patterns, ecma, ecma_plain, strict=True):
        py = [re.search(p, s) is not None for s in strings]
        assert py == js, [(s, a, b) for s, a, b in zip(strings, py, js, strict=True) if a != b][:5]
        assert py == js_plain, [(s, a, b) for s, a, b in zip(strings, py, js_plain, strict=True) if a != b][:5]
