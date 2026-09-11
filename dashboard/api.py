"""
Interactive Data Dashboard - Backend API.

FastAPI-based dashboard backend with real-time metrics, filtering, and export.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import csv
import io
import json
import random
import uuid


app = FastAPI(title="Interactive Data Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────── Data Generation ─────────────────────────────────


def generate_metrics(
    from_time: datetime,
    to_time: datetime,
    granularity: str = "1m",
    agent: Optional[str] = None,
    vertical: Optional[str] = None,
) -> list[dict]:
    """Generate sample metrics data."""
    metrics = []
    current = from_time
    delta = timedelta(minutes=1) if granularity == "1m" else timedelta(minutes=5)

    while current <= to_time:
        point = {
            "timestamp": current.isoformat() + "Z",
            "tasks_completed": random.randint(10, 100),
            "tasks_failed": random.randint(0, 5),
            "avg_latency_ms": random.randint(50, 500),
            "token_usage": random.randint(1000, 50000),
            "active_agents": random.randint(1, 10),
            "safety_gates_passed": random.randint(50, 100),
            "safety_gates_denied": random.randint(0, 3),
        }
        if agent:
            point["agent"] = agent
        if vertical:
            point["vertical"] = vertical
        metrics.append(point)
        current += delta

    return metrics


# ──────────────────── REST Endpoints ──────────────────────────────────


@app.get("/api/v1/dashboard/metrics")
async def get_metrics(
    from_time: Optional[str] = Query(None),
    to_time: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    vertical: Optional[str] = Query(None),
    granularity: str = Query("1m"),
):
    """Get dashboard metrics with optional filters."""
    to = datetime.fromisoformat(to_time.replace("Z", "+00:00")) if to_time else datetime.utcnow()
    frm = datetime.fromisoformat(from_time.replace("Z", "+00:00")) if from_time else to - timedelta(hours=24)

    metrics = generate_metrics(frm, to, granularity, agent, vertical)

    return {
        "metrics": metrics,
        "total": len(metrics),
        "granularity": granularity,
        "filters": {
            "from": frm.isoformat() + "Z",
            "to": to.isoformat() + "Z",
            "agent": agent,
            "vertical": vertical,
        },
    }


@app.get("/api/v1/dashboard/kpis")
async def get_kpis():
    """Get KPI summary cards."""
    return {
        "kpis": [
            {"title": "Tasks Completed", "value": 12543, "change": 12.5, "icon": "check", "color": "green"},
            {"title": "Avg Latency", "value": "145ms", "change": -8.2, "icon": "clock", "color": "blue"},
            {"title": "Active Agents", "value": 8, "change": 0, "icon": "users", "color": "violet"},
            {"title": "Safety Score", "value": "99.7%", "change": 0.1, "icon": "shield", "color": "emerald"},
            {"title": "Token Usage", "value": "2.4M", "change": 5.3, "icon": "cpu", "color": "orange"},
            {"title": "Uptime", "value": "99.9%", "change": 0, "icon": "server", "color": "cyan"},
        ]
    }


@app.get("/api/v1/dashboard/export/csv")
async def export_csv(
    from_time: Optional[str] = Query(None),
    to_time: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    vertical: Optional[str] = Query(None),
):
    """Export metrics as CSV."""
    to = datetime.fromisoformat(to_time.replace("Z", "+00:00")) if to_time else datetime.utcnow()
    frm = datetime.fromisoformat(from_time.replace("Z", "+00:00")) if from_time else to - timedelta(hours=24)

    metrics = generate_metrics(frm, to, "1m", agent, vertical)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=metrics[0].keys() if metrics else [])
    writer.writeheader()
    writer.writerows(metrics)

    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dashboard_metrics.csv"},
    )


@app.get("/api/v1/dashboard/export/json")
async def export_json(
    from_time: Optional[str] = Query(None),
    to_time: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    vertical: Optional[str] = Query(None),
):
    """Export metrics as JSON."""
    to = datetime.fromisoformat(to_time.replace("Z", "+00:00")) if to_time else datetime.utcnow()
    frm = datetime.fromisoformat(from_time.replace("Z", "+00:00")) if from_time else to - timedelta(hours=24)

    metrics = generate_metrics(frm, to, "1m", agent, vertical)

    output = io.StringIO()
    json.dump(metrics, output, indent=2)
    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=dashboard_metrics.json"},
    )


# ──────────────────── WebSocket ───────────────────────────────────────


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket for real-time dashboard updates."""
    await manager.connect(websocket)

    try:
        while True:
            # Send metrics every 5 seconds
            metrics = generate_metrics(
                datetime.utcnow() - timedelta(minutes=1),
                datetime.utcnow(),
                "1m",
            )
            await websocket.send_json({
                "type": "metrics_update",
                "data": metrics[-1] if metrics else {},
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ──────────────────── Health Check ────────────────────────────────────


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
