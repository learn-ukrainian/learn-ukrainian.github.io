import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent.parent
METRICS_DB = PROJECT_ROOT / ".mcp/metrics.db"

class MetricsManager:
    def __init__(self, db_path=METRICS_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Batch operations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT,
                level TEXT,
                module_num INTEGER,
                slug TEXT,
                status TEXT,
                duration_s REAL,
                timestamp TEXT,
                metadata TEXT
            )
        """)

        # LLM usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT,
                model TEXT,
                task_id TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                estimated_cost REAL,
                duration_s REAL,
                timestamp TEXT,
                status TEXT
            )
        """)

        conn.commit()
        conn.close()

    def log_batch_operation(self, op_type, level, module_num, slug, status, duration, metadata=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO batch_operations (operation_type, level, module_num, slug, status, duration_s, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (op_type, level, module_num, slug, status, duration, datetime.now(timezone.utc).isoformat(), json.dumps(metadata or {})))
        conn.commit()
        conn.close()

    @staticmethod
    def estimate_tokens(text):
        """Estimate token count from text (rough heuristic: 4 chars per token)."""
        if not text:
            return 0
        return len(text) // 4

    def log_llm_usage(self, agent, model, task_id, prompt_tokens, completion_tokens, duration, status="success", metadata=None):
        # Basic cost estimation
        cost = self._estimate_cost(model, prompt_tokens, completion_tokens)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO llm_usage (agent, model, task_id, prompt_tokens, completion_tokens, total_tokens, estimated_cost, duration_s, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (agent, model, task_id, prompt_tokens, completion_tokens, prompt_tokens + completion_tokens, cost, duration, datetime.now(timezone.utc).isoformat(), status))
        conn.commit()
        conn.close()

    def _estimate_cost(self, model, prompt_tokens, completion_tokens):
        # Rates per 1M tokens
        rates = {
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
            "gemini-3-flash-preview": {"input": 0.075, "output": 0.30}, # Placeholder
            "gemini-3-pro-preview": {"input": 3.50, "output": 10.50}, # Placeholder
            "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
            "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
            "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        }

        # Default to sonnet rates if unknown
        rate = rates.get(model, {"input": 3.00, "output": 15.00})

        cost = (prompt_tokens / 1_000_000 * rate["input"]) + (completion_tokens / 1_000_000 * rate["output"])
        return round(cost, 6)

    def get_recent_batch_operations(self, limit=50):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM batch_operations ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def check_alerts(self, error_threshold=0.2, cost_threshold=10.0):
        """Check for alerting conditions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        alerts = []

        # Check error rate in last 20 batch operations
        cursor.execute("""
            SELECT status FROM batch_operations
            ORDER BY timestamp DESC LIMIT 20
        """)
        recent_statuses = [row[0] for row in cursor.fetchall()]
        if recent_statuses:
            error_count = sum(1 for s in recent_statuses if s in ("ERROR", "TIMEOUT", "FAIL_AFTER_RETRIES"))
            error_rate = error_count / len(recent_statuses)
            if error_rate >= error_threshold:
                alerts.append(f"High error rate in recent batch operations: {error_rate:.0%}")

        # Check total cost
        cursor.execute("SELECT SUM(estimated_cost) FROM llm_usage")
        total_cost = cursor.fetchone()[0] or 0.0
        if total_cost >= cost_threshold:
            alerts.append(f"Total LLM cost has reached threshold: ${total_cost:.2f} >= ${cost_threshold:.2f}")

        conn.close()
        return alerts

    def get_llm_metrics_summary(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                model,
                COUNT(*) as call_count,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(duration_s) as avg_duration
            FROM llm_usage
            GROUP BY model
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
