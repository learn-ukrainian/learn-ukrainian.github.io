"""Execute the accounting reader UI functions without a provider or browser."""

import json
import subprocess
from pathlib import Path

import pytest

DASHBOARDS = Path(__file__).resolve().parents[1] / "dashboards"


@pytest.mark.parametrize("page,start,end", [
    ("runtime.html", "function renderRecent(", "const ROUTING_PAGE_SIZE"),
    ("fleet.html", "function renderActivity(", "function renderMessages("),
    ("delegate.html", "function observerTaskView(", "function isToday("),
])
@pytest.mark.parametrize("selector", ["requested<selector", None])
def test_accounting_reader_labels_and_fields(page, start, end, selector):
    html = (DASHBOARDS / page).read_text()
    code = html[html.index(start):html.index(end, html.index(start))]
    script = r'''
const target = {innerHTML: ''};
const document = {getElementById: () => target};
const escapeHtml = x => String(x).replaceAll('<', '&lt;');
const formatTs = x => x, formatTime = x => x, formatDuration = x => x, short = x => x || 'unknown';
const table = (headers, rows) => JSON.stringify({headers, rows});
const row = {model: 'accounting-only', requested_selector: 'requested<selector', observed_model: 'observed-only', identity_state: 'observed', observed_model_source: 'provider-init'};
'''
    script += f"\nrow.requested_selector = {json.dumps(selector)};\n"
    if page == "delegate.html":
        script += code + "\nprocess.stdout.write(JSON.stringify(observerTaskView(row)));"
    else:
        call = "renderRecent([row])" if page == "runtime.html" else "renderActivity({records: [row]})"
        script += code + f"\n{call}; process.stdout.write(target.innerHTML);"
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    output = result.stdout
    if page == "delegate.html":
        view = json.loads(output)
        assert view["accounting_model"] == "accounting-only"
        assert view["requested_selector"] == selector
        assert view["observed_model"] == "observed-only"
        assert view["identity_state"] == "observed"
        assert view["observed_model_source"] == "provider-init"
    else:
        for value in ["Accounting model", "Requested selector", "Observed model", "Identity state",
                      "accounting-only", "observed-only", "observed"]:
            assert value in output
        expected_selector = "requested&lt;selector" if selector else ("not specified" if page == "runtime.html" else "unknown")
        assert expected_selector in output
