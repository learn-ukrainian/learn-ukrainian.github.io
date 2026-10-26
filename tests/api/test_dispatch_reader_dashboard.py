"""Exercise the dashboard's actual script against mixed task records."""

import json
import re
import subprocess
from pathlib import Path


def test_dashboard_renders_versions_and_preserves_quoted_run_identity():
    """A quoted nonce must not split an HTML handler or lose run identity."""
    page = Path("dashboards/delegate.html").read_text()
    script = re.search(r"<script>(.*?)</script>", page, re.S)[1]
    probe = r"""
const vm = require('node:vm');
const elements = {};
global.document = {createElement: () => ({
  textContent: '', get innerHTML() {
    return this.textContent.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  }
}), getElementById: id => elements[id] ||= {
  innerHTML: '', textContent: '', style: {}, classList: {add() {}}
}};
const tasks = [
  {task_id: 'legacy', status: 'done', duration_s: 3},
  {task_id: 'v2', schema_version: 2, status: 'crashed', run_nonce: "run'quoted",
   finished_at: '2026-10-26T12:00:00Z', push_state: 'unpushed', worktree_dirty_on_exit: true},
  {task_id: 'active', status: 'spawning', run_nonce: "active'quoted"},
  {schema_version: 99, unknown_field: true}
];
const requests = [];
global.fetch = async url => {
  requests.push(url);
  return {ok: true, text: async () => JSON.stringify(url.includes('?limit=') ? {tasks} : {task: tasks[1]})};
};
vm.runInThisContext(SCRIPT);
setImmediate(async () => {
  const completed = elements['completed-content'].innerHTML;
  const active = elements['active-content'].innerHTML;
  const handlers = [...(completed + active).matchAll(/onclick='([^']*)'/g)].map(m => m[1]);
  const calls = [];
  for (const handler of handlers) {
    const decoded = handler.replaceAll('&#39;', "'").replaceAll('&quot;', '"').replaceAll('&amp;', '&');
    vm.runInNewContext(decoded, {openDetail: (...args) => calls.push(args)});
  }
  await openDetail('v2', "run'quoted");
  console.log(JSON.stringify({completed, calls, requests, view: observerTaskView(tasks[1])}));
});
""".replace("SCRIPT", json.dumps(script))
    result = subprocess.run(["node", "-e", probe], check=True, capture_output=True, text=True, timeout=15)
    rendered = json.loads(result.stdout)
    assert "legacy" in rendered["completed"] and "crashed" in rendered["completed"]
    assert rendered["calls"] == [["legacy", None], ["v2", "run'quoted"], ["active", "active'quoted"]]
    assert rendered["requests"][-1] == "/api/delegate/tasks/v2?run_nonce=run'quoted"
    assert rendered["view"]["delivery"] == {"push_state": "unpushed", "worktree_dirty_on_exit": True}
