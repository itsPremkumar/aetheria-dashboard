"""
Interactive Data Dashboard - Backend API.

FastAPI-based dashboard backend with real-time metrics, filtering, and export.
Serves both the REST API and the interactive dashboard frontend.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import asyncio
import csv
import io
import json
import os
import random
import uuid


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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


def generate_time_series(
    hours: int = 24,
    vertical: Optional[str] = None,
) -> list[dict]:
    """Generate time series data for charts."""
    now = datetime.utcnow()
    start = now - timedelta(hours=hours)
    return generate_metrics(start, now, "5m", vertical=vertical)


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


@app.get("/api/v1/dashboard/timeseries")
async def get_timeseries(
    hours: int = Query(24, ge=1, le=168),
    vertical: Optional[str] = Query(None),
):
    """Get time series data for charts."""
    data = generate_time_series(hours, vertical)
    return {
        "data": data,
        "count": len(data),
        "hours": hours,
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


# ──────────────────── Dashboard Frontend ──────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Data Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --bg-primary: #0f0f1a;
            --bg-secondary: #1a1a2e;
            --bg-card: #16213e;
            --text-primary: #e0e0e0;
            --text-secondary: #a0a0b0;
            --accent-blue: #4a9eff;
            --accent-green: #27ae60;
            --accent-orange: #f39c12;
            --accent-red: #e74c3c;
            --accent-purple: #9b59b6;
            --accent-cyan: #00bcd4;
            --border-color: #2a2a4a;
            --shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }

        .dashboard {
            max-width: 1440px;
            margin: 0 auto;
            padding: 1.5rem;
        }

        /* Header */
        .dashboard-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .dashboard-title {
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .live-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 0.8rem;
            background: var(--bg-card);
            border-radius: 20px;
            border: 1px solid var(--border-color);
            font-size: 0.85rem;
        }

        .live-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        .connection-status {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        /* Filter Panel */
        .filter-panel {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-color);
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: flex-end;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            flex: 1;
            min-width: 150px;
        }

        .filter-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-secondary);
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .filter-input, .filter-select {
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 0.9rem;
            transition: border-color 0.2s;
        }

        .filter-input:focus, .filter-select:focus {
            outline: none;
            border-color: var(--accent-blue);
        }

        .btn {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: none;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-primary {
            background: var(--accent-blue);
            color: white;
        }

        .btn-primary:hover {
            background: #3a8eef;
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-secondary:hover {
            border-color: var(--accent-blue);
        }

        /* KPI Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .kpi-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow);
            transition: transform 0.2s;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
        }

        .kpi-title {
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }

        .kpi-value {
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .kpi-change {
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }

        .kpi-change.positive { color: var(--accent-green); }
        .kpi-change.negative { color: var(--accent-red); }
        .kpi-change.neutral { color: var(--text-secondary); }

        /* Charts Grid */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .chart-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow);
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .chart-title {
            font-size: 1rem;
            font-weight: 600;
        }

        .chart-container {
            position: relative;
            height: 280px;
        }

        /* Export Panel */
        .export-panel {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid var(--border-color);
            margin-bottom: 1.5rem;
        }

        .export-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }

        .export-buttons {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
        }

        .btn-export {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: var(--bg-secondary);
            color: var(--text-primary);
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-export:hover {
            border-color: var(--accent-blue);
            background: rgba(74, 158, 255, 0.1);
        }

        /* Data Table */
        .data-table-card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow);
            margin-bottom: 1.5rem;
            overflow-x: auto;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }

        .data-table th {
            text-align: left;
            padding: 0.75rem 0.5rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }

        .data-table td {
            padding: 0.6rem 0.5rem;
            border-bottom: 1px solid rgba(42, 42, 74, 0.5);
        }

        .data-table tr:hover td {
            background: rgba(74, 158, 255, 0.05);
        }

        /* Footer */
        .dashboard-footer {
            text-align: center;
            padding: 1.5rem 0;
            color: var(--text-secondary);
            font-size: 0.85rem;
            border-top: 1px solid var(--border-color);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .dashboard { padding: 1rem; }
            .dashboard-title { font-size: 1.4rem; }
            .charts-grid { grid-template-columns: 1fr; }
            .chart-container { height: 220px; }
            .kpi-grid { grid-template-columns: repeat(2, 1fr); }
            .filter-panel { flex-direction: column; }
            .filter-group { min-width: 100%; }
        }

        @media (max-width: 480px) {
            .kpi-grid { grid-template-columns: 1fr; }
            .kpi-value { font-size: 1.4rem; }
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- Header -->
        <header class="dashboard-header">
            <h1 class="dashboard-title">Interactive Data Dashboard</h1>
            <div class="header-right">
                <div class="live-indicator">
                    <span class="live-dot"></span>
                    <span>LIVE</span>
                </div>
                <span class="connection-status" id="connectionStatus">Connecting...</span>
            </div>
        </header>

        <!-- Filters -->
        <div class="filter-panel">
            <div class="filter-group">
                <label class="filter-label">Time Range</label>
                <select class="filter-select" id="timeRange">
                    <option value="1">Last 1 Hour</option>
                    <option value="6">Last 6 Hours</option>
                    <option value="24" selected>Last 24 Hours</option>
                    <option value="72">Last 3 Days</option>
                    <option value="168">Last 7 Days</option>
                </select>
            </div>
            <div class="filter-group">
                <label class="filter-label">Agent</label>
                <select class="filter-select" id="agentFilter">
                    <option value="">All Agents</option>
                    <option value="agent_1">Agent 1</option>
                    <option value="agent_2">Agent 2</option>
                    <option value="agent_3">Agent 3</option>
                </select>
            </div>
            <div class="filter-group">
                <label class="filter-label">Vertical</label>
                <select class="filter-select" id="verticalFilter">
                    <option value="">All Verticals</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="legal">Legal</option>
                    <option value="finance">Finance</option>
                    <option value="education">Education</option>
                    <option value="agriculture">Agriculture</option>
                </select>
            </div>
            <div class="filter-group">
                <label class="filter-label">From</label>
                <input type="datetime-local" class="filter-input" id="fromDate">
            </div>
            <div class="filter-group">
                <label class="filter-label">To</label>
                <input type="datetime-local" class="filter-input" id="toDate">
            </div>
            <button class="btn btn-primary" id="applyFilters">Apply</button>
            <button class="btn btn-secondary" id="resetFilters">Reset</button>
        </div>

        <!-- KPI Cards -->
        <div class="kpi-grid" id="kpiGrid">
            <!-- Filled dynamically -->
        </div>

        <!-- Export Panel -->
        <div class="export-panel">
            <div class="export-title">Export Data</div>
            <div class="export-buttons">
                <button class="btn-export" data-format="csv">CSV</button>
                <button class="btn-export" data-format="json">JSON</button>
                <button class="btn-export" data-format="png">PNG (Chart)</button>
            </div>
        </div>

        <!-- Charts -->
        <div class="charts-grid">
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">Tasks Completed Over Time</span>
                </div>
                <div class="chart-container">
                    <canvas id="tasksChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">Average Latency (ms)</span>
                </div>
                <div class="chart-container">
                    <canvas id="latencyChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">Token Usage</span>
                </div>
                <div class="chart-container">
                    <canvas id="tokenChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <div class="chart-header">
                    <span class="chart-title">Safety Gates (Passed vs Denied)</span>
                </div>
                <div class="chart-container">
                    <canvas id="safetyChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Data Table -->
        <div class="data-table-card">
            <div class="chart-header">
                <span class="chart-title">Recent Metrics Data</span>
            </div>
            <table class="data-table" id="dataTable">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Tasks Completed</th>
                        <th>Tasks Failed</th>
                        <th>Avg Latency (ms)</th>
                        <th>Token Usage</th>
                        <th>Active Agents</th>
                        <th>Safety Passed</th>
                        <th>Safety Denied</th>
                    </tr>
                </thead>
                <tbody id="dataTableBody">
                </tbody>
            </table>
        </div>

        <footer class="dashboard-footer">
            <p>Interactive Data Dashboard &mdash; Built with FastAPI, Chart.js, WebSocket</p>
        </footer>
    </div>

    <script>
        // ──────────────────── State ─────────────────────────────────
        const state = {
            charts: {},
            data: [],
            kpis: [],
            ws: null,
            filters: {
                hours: 24,
                agent: '',
                vertical: '',
                from: null,
                to: null
            }
        };

        const COLORS = {
            blue: '#4a9eff',
            green: '#27ae60',
            orange: '#f39c12',
            red: '#e74c3c',
            purple: '#9b59b6',
            cyan: '#00bcd4',
            grid: 'rgba(255,255,255,0.05)',
            text: '#a0a0b0'
        };

        // ──────────────────── Chart Defaults ─────────────────────────
        Chart.defaults.color = COLORS.text;
        Chart.defaults.borderColor = COLORS.grid;
        Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

        // ──────────────────── API Helpers ────────────────────────────
        async function fetchJSON(url) {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        }

        function buildQueryParams() {
            const params = new URLSearchParams();
            if (state.filters.hours) params.set('hours', state.filters.hours);
            if (state.filters.agent) params.set('agent', state.filters.agent);
            if (state.filters.vertical) params.set('vertical', state.filters.vertical);
            if (state.filters.from) params.set('from_time', new Date(state.filters.from).toISOString());
            if (state.filters.to) params.set('to_time', new Date(state.filters.to).toISOString());
            return params.toString();
        }

        // ──────────────────── KPI Cards ──────────────────────────────
        function renderKPIs(kpis) {
            const grid = document.getElementById('kpiGrid');
            grid.innerHTML = kpis.map(kpi => {
                const changeClass = kpi.change > 0 ? 'positive' : kpi.change < 0 ? 'negative' : 'neutral';
                const arrow = kpi.change > 0 ? '↑' : kpi.change < 0 ? '↓' : '→';
                const changeText = kpi.change !== 0 ? `${arrow} ${Math.abs(kpi.change)}%` : 'No change';
                return `
                    <div class="kpi-card">
                        <div class="kpi-title">${kpi.title}</div>
                        <div class="kpi-value" style="color: ${COLORS[kpi.color] || COLORS.blue}">${kpi.value}</div>
                        <div class="kpi-change ${changeClass}">${changeText}</div>
                    </div>
                `;
            }).join('');
        }

        // ──────────────────── Charts ─────────────────────────────────
        function initCharts() {
            const commonOptions = {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 600 },
                plugins: {
                    legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16 } },
                    tooltip: {
                        backgroundColor: '#1a1a2e',
                        borderColor: '#2a2a4a',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 8,
                    }
                },
                scales: {
                    x: { grid: { color: COLORS.grid }, ticks: { maxTicksLimit: 8 } },
                    y: { grid: { color: COLORS.grid }, beginAtZero: true }
                }
            };

            // Tasks Chart (Bar)
            state.charts.tasks = new Chart(document.getElementById('tasksChart'), {
                type: 'bar',
                data: { labels: [], datasets: [{
                    label: 'Tasks Completed',
                    data: [],
                    backgroundColor: COLORS.blue,
                    borderRadius: 4,
                }] },
                options: { ...commonOptions, scales: { ...commonOptions.scales } }
            });

            // Latency Chart (Line)
            state.charts.latency = new Chart(document.getElementById('latencyChart'), {
                type: 'line',
                data: { labels: [], datasets: [{
                    label: 'Avg Latency (ms)',
                    data: [],
                    borderColor: COLORS.orange,
                    backgroundColor: 'rgba(243, 156, 18, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 6,
                }] },
                options: commonOptions
            });

            // Token Chart (Area/Line)
            state.charts.token = new Chart(document.getElementById('tokenChart'), {
                type: 'line',
                data: { labels: [], datasets: [{
                    label: 'Token Usage',
                    data: [],
                    borderColor: COLORS.purple,
                    backgroundColor: 'rgba(155, 89, 182, 0.15)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 6,
                }] },
                options: commonOptions
            });

            // Safety Chart (Stacked Bar)
            state.charts.safety = new Chart(document.getElementById('safetyChart'), {
                type: 'bar',
                data: { labels: [], datasets: [
                    { label: 'Passed', data: [], backgroundColor: COLORS.green, borderRadius: 4 },
                    { label: 'Denied', data: [], backgroundColor: COLORS.red, borderRadius: 4 },
                ]},
                options: { ...commonOptions, scales: { ...commonOptions.scales, x: { ...commonOptions.scales.x, stacked: true }, y: { ...commonOptions.scales.y, stacked: true } } }
            });
        }

        function formatTime(ts) {
            const d = new Date(ts);
            return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        }

        function updateCharts(data) {
            const labels = data.map(d => formatTime(d.timestamp));
            const tasksCompleted = data.map(d => d.tasks_completed);
            const avgLatency = data.map(d => d.avg_latency_ms);
            const tokenUsage = data.map(d => d.token_usage);
            const safetyPassed = data.map(d => d.safety_gates_passed);
            const safetyDenied = data.map(d => d.safety_gates_denied);

            // Update each chart
            state.charts.tasks.data.labels = labels;
            state.charts.tasks.data.datasets[0].data = tasksCompleted;
            state.charts.tasks.update();

            state.charts.latency.data.labels = labels;
            state.charts.latency.data.datasets[0].data = avgLatency;
            state.charts.latency.update();

            state.charts.token.data.labels = labels;
            state.charts.token.data.datasets[0].data = tokenUsage;
            state.charts.token.update();

            state.charts.safety.data.labels = labels;
            state.charts.safety.data.datasets[0].data = safetyPassed;
            state.charts.safety.data.datasets[1].data = safetyDenied;
            state.charts.safety.update();
        }

        // ──────────────────── Data Table ──────────────────────────────
        function updateDataTable(data) {
            const tbody = document.getElementById('dataTableBody');
            const recent = data.slice(-15).reverse();
            tbody.innerHTML = recent.map(d => `
                <tr>
                    <td>${new Date(d.timestamp).toLocaleString()}</td>
                    <td>${d.tasks_completed}</td>
                    <td>${d.tasks_failed}</td>
                    <td>${d.avg_latency_ms}</td>
                    <td>${d.token_usage.toLocaleString()}</td>
                    <td>${d.active_agents}</td>
                    <td>${d.safety_gates_passed}</td>
                    <td>${d.safety_gates_denied}</td>
                </tr>
            `).join('');
        }

        // ──────────────────── Data Loading ────────────────────────────
        async function loadData() {
            try {
                const [tsData, kpiData] = await Promise.all([
                    fetchJSON(`/api/v1/dashboard/timeseries?${buildQueryParams()}`),
                    fetchJSON('/api/v1/dashboard/kpis'),
                ]);

                state.data = tsData.data;
                state.kpis = kpiData.kpis;

                renderKPIs(state.kpis);
                updateCharts(state.data);
                updateDataTable(state.data);
            } catch (err) {
                console.error('Failed to load data:', err);
            }
        }

        // ──────────────────── WebSocket ───────────────────────────────
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;

            state.ws = new WebSocket(wsUrl);

            state.ws.onopen = () => {
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').style.color = COLORS.green;
            };

            state.ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                if (msg.type === 'metrics_update' && msg.data) {
                    // Append real-time data point
                    state.data.push(msg.data);
                    if (state.data.length > 200) state.data.shift();
                    updateCharts(state.data);
                    updateDataTable(state.data);
                }
            };

            state.ws.onclose = () => {
                document.getElementById('connectionStatus').textContent = 'Disconnected';
                document.getElementById('connectionStatus').style.color = COLORS.red;
                // Reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            };

            state.ws.onerror = () => {
                document.getElementById('connectionStatus').textContent = 'Error';
                document.getElementById('connectionStatus').style.color = COLORS.red;
            };
        }

        // ──────────────────── Filters ─────────────────────────────────
        function applyFilters() {
            state.filters.hours = document.getElementById('timeRange').value;
            state.filters.agent = document.getElementById('agentFilter').value;
            state.filters.vertical = document.getElementById('verticalFilter').value;
            state.filters.from = document.getElementById('fromDate').value;
            state.filters.to = document.getElementById('toDate').value;
            loadData();
        }

        function resetFilters() {
            document.getElementById('timeRange').value = '24';
            document.getElementById('agentFilter').value = '';
            document.getElementById('verticalFilter').value = '';
            document.getElementById('fromDate').value = '';
            document.getElementById('toDate').value = '';
            state.filters = { hours: 24, agent: '', vertical: '', from: null, to: null };
            loadData();
        }

        // ──────────────────── Export ──────────────────────────────────
        function setupExport() {
            document.querySelectorAll('.btn-export').forEach(btn => {
                btn.addEventListener('click', () => {
                    const format = btn.dataset.format;
                    if (format === 'png') {
                        exportChartPNG();
                    } else {
                        exportData(format);
                    }
                });
            });
        }

        function exportData(format) {
            const qs = buildQueryParams();
            const url = `/api/v1/dashboard/export/${format}?${qs}`;
            const a = document.createElement('a');
            a.href = url;
            a.download = `dashboard_metrics.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

        function exportChartPNG() {
            // Export the first chart as PNG
            const canvas = document.getElementById('tasksChart');
            const url = canvas.toDataURL('image/png');
            const a = document.createElement('a');
            a.href = url;
            a.download = 'dashboard_chart.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }

        // ──────────────────── Initialization ──────────────────────────
        document.addEventListener('DOMContentLoaded', () => {
            initCharts();
            loadData();
            connectWebSocket();
            setupExport();

            document.getElementById('applyFilters').addEventListener('click', applyFilters);
            document.getElementById('resetFilters').addEventListener('click', resetFilters);
        });
    </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve the interactive dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve the interactive dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)
