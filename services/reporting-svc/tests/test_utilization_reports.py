"""
Tests for utilization reports endpoint.
Mocks HTTP calls to assets-svc.
"""

import pytest
import respx
import httpx
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestUtilizationReport:
    """Test the /reports/utilization endpoint."""

    @respx.mock
    def test_utilization_with_mixed_statuses(self, client):
        """Test utilization report with various asset statuses."""
        mock_stats = {
            "available": 50,
            "assigned": 30,
            "retired": 15,
            "lost": 5
        }
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 100  # Sum of all statuses
        assert data["in_use"] == 30  # Only assigned
        assert data["utilization_pct"] == 30.0  # 30/100 * 100
        assert data["by_status"] == mock_stats

    @respx.mock
    def test_utilization_all_assigned(self, client):
        """Test utilization report when all assets are assigned."""
        mock_stats = {
            "assigned": 100
        }
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 100
        assert data["in_use"] == 100
        assert data["utilization_pct"] == 100.0

    @respx.mock
    def test_utilization_all_available(self, client):
        """Test utilization report when all assets are available."""
        mock_stats = {
            "available": 75
        }
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 75
        assert data["in_use"] == 0  # No assigned
        assert data["utilization_pct"] == 0.0

    @respx.mock
    def test_utilization_no_assets(self, client):
        """Test utilization report when no assets exist (zero total)."""
        mock_stats = {}
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert data["in_use"] == 0
        assert data["utilization_pct"] == 0.0  # Should not divide by zero
        assert data["by_status"] == {}

    @respx.mock
    def test_utilization_no_assigned_status(self, client):
        """Test utilization when there are assets but none assigned."""
        mock_stats = {
            "available": 20,
            "retired": 5
        }
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 25
        assert data["in_use"] == 0
        assert data["utilization_pct"] == 0.0

    @respx.mock
    def test_utilization_rounding(self, client):
        """Test utilization percentage rounding."""
        mock_stats = {
            "available": 67,
            "assigned": 33
        }
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 100
        assert data["in_use"] == 33
        # 33/100 * 100 = 33.0, rounded to 1 decimal
        assert data["utilization_pct"] == 33.0

    @respx.mock
    def test_utilization_fractional_percentage(self, client):
        """Test utilization with fractional percentage."""
        mock_stats = {
            "available": 47,
            "assigned": 53
        }
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 100
        assert data["in_use"] == 53
        assert data["utilization_pct"] == 53.0

    @respx.mock
    def test_utilization_small_numbers(self, client):
        """Test utilization with small asset counts."""
        mock_stats = {
            "available": 2,
            "assigned": 1
        }
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 3
        assert data["in_use"] == 1
        # 1/3 * 100 = 33.333... rounded to 33.3
        assert data["utilization_pct"] == 33.3

    @respx.mock
    def test_utilization_assets_svc_error(self, client):
        """Test utilization report when assets-svc is unavailable."""
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(500, json={"error": "Internal error"})
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 502
        assert "assets-svc unavailable" in response.json()["detail"]

    @respx.mock
    def test_utilization_assets_svc_timeout(self, client):
        """Test utilization report when assets-svc times out."""
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 502
        assert "assets-svc unavailable" in response.json()["detail"]

    @respx.mock
    def test_utilization_multiple_statuses(self, client):
        """Test utilization with many different statuses."""
        mock_stats = {
            "available": 100,
            "assigned": 75,
            "retired": 25,
            "lost": 10,
            "maintenance": 5
        }
        
        respx.get("http://assets-svc:8080/assets/stats/by-status").mock(
            return_value=httpx.Response(200, json=mock_stats)
        )
        
        response = client.get("/reports/utilization")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 215
        assert data["in_use"] == 75
        assert data["utilization_pct"] == 34.9  # 75/215 * 100 = 34.88... -> 34.9
        assert len(data["by_status"]) == 5
