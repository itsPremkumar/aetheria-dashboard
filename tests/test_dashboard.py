"""
Tests for Interactive Data Dashboard.
Test count: 14
"""
import importlib.util
import os
import sys

# Direct import via importlib to avoid pytest path issues
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "dashboard.api",
    os.path.join(workspace_root, "dashboard", "api.py"),
)
assert _spec is not None, "Cannot find dashboard/api.py"
dashboard_api = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dashboard_api)
app = dashboard_api.app

from fastapi.testclient import TestClient

client = TestClient(app)


# ──────────────────── Metrics Tests ───────────────────────────────────


class TestMetrics:
    def test_get_metrics(self):
        response = client.get("/api/v1/dashboard/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "total" in data

    def test_get_metrics_with_filters(self):
        response = client.get("/api/v1/dashboard/metrics?agent=agent_1&vertical=finance")
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["agent"] == "agent_1"
        assert data["filters"]["vertical"] == "finance"

    def test_get_metrics_with_date_range(self):
        response = client.get("/api/v1/dashboard/metrics?from_time=2024-01-01T00:00:00Z&to_time=2024-01-02T00:00:00Z")
        assert response.status_code == 200

    def test_get_kpis(self):
        response = client.get("/api/v1/dashboard/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data
        assert len(data["kpis"]) >= 1

    def test_get_timeseries(self):
        response = client.get("/api/v1/dashboard/timeseries?hours=1")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data

    def test_get_timeseries_with_vertical(self):
        response = client.get("/api/v1/dashboard/timeseries?hours=1&vertical=healthcare")
        assert response.status_code == 200


# ──────────────────── Export Tests ────────────────────────────────────


class TestExport:
    def test_export_csv(self):
        response = client.get("/api/v1/dashboard/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_json(self):
        response = client.get("/api/v1/dashboard/export/json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_export_csv_with_filters(self):
        response = client.get("/api/v1/dashboard/export/csv?vertical=finance")
        assert response.status_code == 200

    def test_export_json_with_filters(self):
        response = client.get("/api/v1/dashboard/export/json?agent=agent_1")
        assert response.status_code == 200


# ──────────────────── Dashboard Page Tests ─────────────────────────────


class TestDashboardPage:
    def test_dashboard_home(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Interactive Data Dashboard" in response.text

    def test_dashboard_page(self):
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


# ──────────────────── WebSocket Tests ─────────────────────────────────


class TestWebSocket:
    def test_websocket_connection(self):
        with client.websocket_connect("/ws/dashboard") as ws:
            import json
            data = ws.receive_json()
            assert data["type"] == "metrics_update"
            assert "data" in data
            assert "timestamp" in data


# ──────────────────── Health Tests ────────────────────────────────────


class TestHealth:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
