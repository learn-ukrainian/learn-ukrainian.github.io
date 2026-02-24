from fastapi.testclient import TestClient
from scripts.api.main import app
import json

client = TestClient(app)
response = client.get("/api/dashboard/overview")
data = response.json()
for t in data["tracks"]:
    if t["id"] in ["b1", "b2", "b2-hist", "a1", "a2"]:
        print(f"Track: {t['id']}")
        print(f"  API Stats: {t['stats']}")
        
        # Check actual filesystem counts
        from pathlib import Path
        track_dir = Path("curriculum/l2-uk-en") / t["id"]
        docs_dir = Path("docusaurus/docs") / t["id"]
        
        mdx_count = len(list(docs_dir.glob("*.mdx"))) - 1 # exclude index.mdx
        audit_count = len(list((track_dir / "audit").glob("*-audit.md"))) if (track_dir / "audit").exists() else 0
        review_count = len(list((track_dir / "review").glob("*-review.md"))) if (track_dir / "review").exists() else 0
        status_count = len(list((track_dir / "status").glob("*.json"))) if (track_dir / "status").exists() else 0
        
        print(f"  Filesystem: {mdx_count} MDX, {audit_count} Audits, {review_count} Reviews, {status_count} Status JSONs")
        print()
