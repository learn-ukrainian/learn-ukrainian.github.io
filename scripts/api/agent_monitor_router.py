"""Host-local Agent Capacity & Process Monitor API for learn-ukrainian.

Prevents multi-agent workload overload, OOM crashes, and CPU contention across fleet models.
Enforces capacity invariant: host_reserved (1250 MB) + active_reservations + requested_ram <= safe_allocatable_memory.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
import uuid
from typing import Any

import psutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .config import BATCH_STATE_DIR

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent-monitor"])

DB_PATH = BATCH_STATE_DIR / "agent_monitor.sqlite3"
HOST_RESERVED_RAM_MB = 1250  # Reserved for OS and core services
MAX_SAFE_RAM_PERCENT = 75.0  # Max allocatable RAM percentage


class PreflightRequest(BaseModel):
    agent_id: str = Field(..., description="Agent identity, e.g. gemini/2156-eval")
    task_name: str = Field(..., description="Name of workload, e.g. dialect_scraping")
    required_ram_mb: int = Field(512, ge=64, le=3072, description="Requested RAM in MB")


class LeaseRegisterRequest(BaseModel):
    agent_id: str = Field(..., description="Agent identity, e.g. gemini/2156-eval")
    task_name: str = Field(..., description="Name of workload, e.g. dialect_scraping")
    pid: int = Field(..., description="Process ID")
    process_create_time: float = Field(..., description="Process creation timestamp")
    reserved_ram_mb: int = Field(512, ge=64, le=3072, description="Requested RAM in MB")


class HeartbeatRequest(BaseModel):
    lease_token: str
    pid: int


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_leases (
            lease_token TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            task_name TEXT NOT NULL,
            pid INTEGER NOT NULL,
            process_create_time REAL NOT NULL,
            reserved_ram_mb INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at REAL NOT NULL,
            last_heartbeat REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def _calculate_severity(used_percent: float) -> str:
    if used_percent >= 85.0:
        return "critical"
    elif used_percent >= MAX_SAFE_RAM_PERCENT:
        return "warning"
    return "healthy"


@router.get("/status")
def get_monitor_status() -> dict[str, Any]:
    mem = psutil.virtual_memory()
    load = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)

    conn = _get_db()
    cur = conn.cursor()
    now = time.time()

    # Prune expired leases (>300s without heartbeat)
    cur.execute(
        "UPDATE agent_leases SET status='EXPIRED' WHERE status='APPROVED' AND last_heartbeat < ?",
        (now - 300,),
    )
    conn.commit()

    cur.execute(
        "SELECT lease_token, agent_id, task_name, pid, process_create_time, reserved_ram_mb, last_heartbeat FROM agent_leases WHERE status='APPROVED'"
    )
    rows = cur.fetchall()
    active_leases = []
    expired_tokens = []

    for row in rows:
        lease_tok, agent_id, task_name, pid, proc_create_time, reserved_ram_mb, last_hb = row
        try:
            proc = psutil.Process(pid)
            if abs(proc.create_time() - proc_create_time) > 5.0:
                expired_tokens.append(lease_tok)
                continue
        except psutil.NoSuchProcess:
            expired_tokens.append(lease_tok)
            continue
        except psutil.AccessDenied:
            pass

        active_leases.append(
            {
                "agent_id": agent_id,
                "task_name": task_name,
                "pid": pid,
                "reserved_ram_mb": reserved_ram_mb,
                "last_heartbeat": last_hb,
            }
        )

    if expired_tokens:
        cur.executemany("UPDATE agent_leases SET status='EXPIRED' WHERE lease_token=?", [(t,) for t in expired_tokens])
        conn.commit()
    conn.close()

    total_reserved_mb = sum(l["reserved_ram_mb"] for l in active_leases)
    severity = _calculate_severity(mem.percent)

    return {
        "host": "local_fleet",
        "timestamp": now,
        "severity": severity,
        "load_1m_5m_15m": list(load),
        "ram": {
            "total_mb": int(mem.total / (1024 * 1024)),
            "available_mb": int(mem.available / (1024 * 1024)),
            "used_percent": mem.percent,
        },
        "capacity_reservations": {
            "active_leases_count": len(active_leases),
            "total_reserved_ram_mb": total_reserved_mb,
            "host_reserved_ram_mb": HOST_RESERVED_RAM_MB,
        },
        "active_leases": active_leases,
    }


@router.post("/preflight")
def preflight_check(req: PreflightRequest) -> dict[str, Any]:
    mem = psutil.virtual_memory()
    total_ram_mb = int(mem.total / (1024 * 1024))
    available_ram_mb = int(mem.available / (1024 * 1024))

    conn = _get_db()
    cur = conn.cursor()
    now = time.time()

    cur.execute(
        "SELECT COALESCE(SUM(reserved_ram_mb), 0) FROM agent_leases WHERE status='APPROVED' AND last_heartbeat >= ?",
        (now - 300,),
    )
    active_reserved_mb = cur.fetchone()[0]
    conn.close()

    safe_capacity_mb = int(total_ram_mb * (MAX_SAFE_RAM_PERCENT / 100.0)) - HOST_RESERVED_RAM_MB

    if (active_reserved_mb + req.required_ram_mb) > safe_capacity_mb or available_ram_mb < (req.required_ram_mb + 256):
        return {
            "verdict": "REJECTED",
            "reason": "Host memory capacity limit reached.",
            "available_ram_mb": available_ram_mb,
            "active_reserved_mb": active_reserved_mb,
            "requested_ram_mb": req.required_ram_mb,
            "retry_after_seconds": 60,
        }

    return {
        "verdict": "APPROVED",
        "available_ram_mb": available_ram_mb,
        "active_reserved_mb": active_reserved_mb,
        "requested_ram_mb": req.required_ram_mb,
    }


@router.post("/register")
def register_agent_lease(req: LeaseRegisterRequest) -> dict[str, Any]:
    try:
        proc = psutil.Process(req.pid)
        if abs(proc.create_time() - req.process_create_time) > 5.0:
            raise HTTPException(status_code=400, detail="Process creation time mismatch")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        raise HTTPException(status_code=400, detail="Process ID does not exist on host") from None

    mem = psutil.virtual_memory()
    total_ram_mb = int(mem.total / (1024 * 1024))
    available_ram_mb = int(mem.available / (1024 * 1024))

    conn = _get_db()
    conn.execute("BEGIN IMMEDIATE")
    cur = conn.cursor()
    now = time.time()

    # Idempotency check: return existing lease if already registered
    cur.execute(
        "SELECT lease_token, reserved_ram_mb FROM agent_leases WHERE agent_id=? AND task_name=? AND pid=? AND process_create_time=? AND status='APPROVED' AND last_heartbeat >= ?",
        (req.agent_id, req.task_name, req.pid, req.process_create_time, now - 300.0),
    )
    existing = cur.fetchone()
    if existing:
        conn.commit()
        conn.close()
        return {
            "verdict": "APPROVED",
            "lease_token": existing[0],
            "agent_id": req.agent_id,
            "task_name": req.task_name,
            "pid": req.pid,
            "reserved_ram_mb": existing[1],
            "heartbeat_interval_seconds": 30,
            "lease_timeout_seconds": 300,
            "idempotent_reattach": True,
        }

    cur.execute(
        "SELECT COALESCE(SUM(reserved_ram_mb), 0) FROM agent_leases WHERE status='APPROVED' AND last_heartbeat >= ?",
        (now - 300,),
    )
    active_reserved_mb = cur.fetchone()[0]

    safe_capacity_mb = int(total_ram_mb * (MAX_SAFE_RAM_PERCENT / 100.0)) - HOST_RESERVED_RAM_MB

    if (active_reserved_mb + req.reserved_ram_mb) > safe_capacity_mb or available_ram_mb < (req.reserved_ram_mb + 256):
        conn.rollback()
        conn.close()
        return {
            "verdict": "REJECTED",
            "reason": "Host memory capacity limit reached. Insufficient allocatable RAM.",
            "available_ram_mb": available_ram_mb,
            "active_reserved_mb": active_reserved_mb,
            "requested_ram_mb": req.reserved_ram_mb,
            "retry_after_seconds": 60,
        }

    lease_token = f"lease_{uuid.uuid4().hex[:12]}"
    cur.execute(
        "INSERT INTO agent_leases VALUES (?, ?, ?, ?, ?, ?, 'APPROVED', ?, ?)",
        (
            lease_token,
            req.agent_id,
            req.task_name,
            req.pid,
            req.process_create_time,
            req.reserved_ram_mb,
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "verdict": "APPROVED",
        "lease_token": lease_token,
        "agent_id": req.agent_id,
        "task_name": req.task_name,
        "pid": req.pid,
        "reserved_ram_mb": req.reserved_ram_mb,
        "heartbeat_interval_seconds": 30,
        "lease_timeout_seconds": 300,
    }


@router.post("/heartbeat")
def heartbeat_agent_lease(req: HeartbeatRequest) -> dict[str, Any]:
    conn = _get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT process_create_time FROM agent_leases WHERE lease_token=? AND pid=? AND status='APPROVED'",
        (req.lease_token, req.pid),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Active lease token not found or process mismatch",
        )

    stored_create_time = row[0]
    try:
        proc = psutil.Process(req.pid)
        if abs(proc.create_time() - stored_create_time) > 5.0:
            conn.close()
            raise HTTPException(status_code=400, detail="Process creation time mismatch on heartbeat")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        conn.close()
        raise HTTPException(status_code=400, detail="Process ID does not exist on host") from None

    now = time.time()
    cur.execute(
        "UPDATE agent_leases SET last_heartbeat=? WHERE lease_token=? AND pid=? AND status='APPROVED'",
        (now, req.lease_token, req.pid),
    )
    conn.commit()
    conn.close()

    return {"status": "OK", "lease_token": req.lease_token, "timestamp": now}


@router.post("/release")
def release_agent_lease(lease_token: str) -> dict[str, Any]:
    conn = _get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE agent_leases SET status='RELEASED' WHERE lease_token=? AND status='APPROVED'",
        (lease_token,),
    )
    released = cur.rowcount
    conn.commit()
    conn.close()

    if released == 0:
        raise HTTPException(status_code=404, detail="Active lease token not found")

    return {"status": "RELEASED", "lease_token": lease_token}
