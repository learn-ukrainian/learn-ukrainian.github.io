#!/usr/bin/env python3
import json
import logging
import os
import time
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger("checkpoint")

class CheckpointManager:
    """Manages batch operation state and checkpoints."""

    def __init__(self, batch_id: str, checkpoint_dir: str = ".checkpoints"):
        self.batch_id = batch_id
        self.checkpoint_dir = Path(checkpoint_dir)
        self.state_file = self.checkpoint_dir / f"{batch_id}.state.json"
        self.lock_file = self.checkpoint_dir / f"{batch_id}.lock"
        self.state = {
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "modules": {},  # module_id -> {status, attempts, last_error, metadata}
        }
        self._ensure_dir()

    def _ensure_dir(self):
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def acquire_lock(self):
        """Simple lock file mechanism."""
        if self.lock_file.exists():
            # Check if lock is stale (> 1 hour)
            if time.time() - self.lock_file.stat().st_mtime > 3600:
                logger.warning(f"Removing stale lock file: {self.lock_file}")
                self.lock_file.unlink()
            else:
                raise RuntimeError(f"Batch {self.batch_id} is already running (locked).")

        self.lock_file.write_text(str(os.getpid()))

    def release_lock(self):
        if self.lock_file.exists():
            self.lock_file.unlink()

    def load(self) -> bool:
        """Load state from file. Returns True if successful."""
        if self.state_file.exists():
            try:
                self.state = json.loads(self.state_file.read_text())
                return True
            except Exception as e:
                logger.error(f"Failed to load checkpoint {self.state_file}: {e}")
        return False

    def save(self):
        """Save state atomically."""
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        temp_file = self.state_file.with_suffix(".tmp")
        try:
            temp_file.write_text(json.dumps(self.state, indent=2))
            temp_file.replace(self.state_file)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def update_module(self, module_id: str, status: str, **kwargs):
        """Update status of a single module."""
        if module_id not in self.state["modules"]:
            self.state["modules"][module_id] = {"attempts": 0}

        self.state["modules"][module_id].update({
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **kwargs
        })
        if status == "failed":
            self.state["modules"][module_id]["attempts"] = self.state["modules"][module_id].get("attempts", 0) + 1

        self.save()

    def is_completed(self, module_id: str) -> bool:
        return self.state["modules"].get(module_id, {}).get("status") == "completed"

    def get_attempts(self, module_id: str) -> int:
        return self.state["modules"].get(module_id, {}).get("attempts", 0)

    def get_summary(self) -> dict:
        modules = self.state["modules"].values()
        return {
            "total": len(modules),
            "completed": sum(1 for m in modules if m["status"] == "completed"),
            "failed": sum(1 for m in modules if m["status"] == "failed"),
            "pending": sum(1 for m in modules if m["status"] == "pending"),
            "skipped": sum(1 for m in modules if m["status"] == "skipped"),
        }
