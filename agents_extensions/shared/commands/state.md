Get project context in ONE call:
Run: { echo "=== STATE ==="; curl -s http://localhost:8765/api/state/summary 2>/dev/null || echo "Monitor API unavailable"; echo -e "\n=== ISSUES ==="; gh issue list --state open --limit 10 --json number,title 2>/dev/null || echo "GH unavailable"; }
