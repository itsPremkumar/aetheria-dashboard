"""
Tests for Interactive Data Dashboard.
Test count: 16
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'src'))

from dashboard.api import app
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


# ──────────────────── Health Tests ────────────────────────────────────


class TestHealth:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
