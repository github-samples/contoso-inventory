"""
Tests for warranty expiring reports endpoint.
Mocks HTTP calls to assets-svc.
"""

import pytest
import respx
import httpx
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestWarrantyExpiringReport:
    """Test the /reports/warranty-expiring endpoint."""

    @respx.mock
    def test_warranty_expiring_with_assets(self, client):
        """Test warranty report with assets expiring within threshold."""
        # Mock the assets-svc response
        today = date.today()
        within_threshold = (today + timedelta(days=90)).isoformat()
        outside_threshold = (today + timedelta(days=200)).isoformat()
        expired = (today - timedelta(days=10)).isoformat()
        
        mock_assets = [
            {
                "id": 1,
                "assetTag": "EXPIRING-001",
                "assetType": "Laptop",
                "manufacturer": "Dell",
                "model": "XPS 15",
                "warrantyExpiry": within_threshold,
                "status": "available"
            },
            {
                "id": 2,
                "assetTag": "OK-002",
                "assetType": "Monitor",
                "manufacturer": "Samsung",
                "model": "S27",
                "warrantyExpiry": outside_threshold,
                "status": "available"
            },
            {
                "id": 3,
                "assetTag": "EXPIRED-003",
                "assetType": "Keyboard",
                "manufacturer": "Logitech",
                "model": "K120",
                "warrantyExpiry": expired,
                "status": "retired"
            }
        ]
        
        respx.get("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(200, json=mock_assets)
        )
        
        # Make request
        response = client.get("/reports/warranty-expiring?within_days=180")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 2  # Should include within threshold and expired
        assert data["within_days"] == 180
        assert len(data["items"]) == 2
        
        # Verify items are sorted by expiry date (earliest first)
        assert data["items"][0]["assetTag"] == "EXPIRED-003"
        assert data["items"][1]["assetTag"] == "EXPIRING-001"
        
        # Verify label formatting
        assert "EXPIRED" in data["items"][0]["label"]
        assert "EXPIRING-001" in data["items"][1]["label"]

    @respx.mock
    def test_warranty_expiring_no_matches(self, client):
        """Test warranty report when no assets are expiring."""
        today = date.today()
        far_future = (today + timedelta(days=500)).isoformat()
        
        mock_assets = [
            {
                "id": 1,
                "assetTag": "DISTANT-001",
                "assetType": "Laptop",
                "manufacturer": "Dell",
                "model": "XPS",
                "warrantyExpiry": far_future,
                "status": "available"
            }
        ]
        
        respx.get("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(200, json=mock_assets)
        )
        
        response = client.get("/reports/warranty-expiring?within_days=180")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 0
        assert data["items"] == []

    @respx.mock
    def test_warranty_expiring_empty_assets(self, client):
        """Test warranty report when no assets exist."""
        respx.get("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(200, json=[])
        )
        
        response = client.get("/reports/warranty-expiring")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 0
        assert data["items"] == []

    @respx.mock
    def test_warranty_expiring_no_warranty_date(self, client):
        """Test warranty report skips assets without warranty expiry."""
        mock_assets = [
            {
                "id": 1,
                "assetTag": "NO-WARRANTY-001",
                "assetType": "Keycard",
                "manufacturer": "Generic",
                "model": "Card",
                "warrantyExpiry": None,
                "status": "available"
            },
            {
                "id": 2,
                "assetTag": "NO-WARRANTY-002",
                "assetType": "Badge",
                "manufacturer": "Generic",
                "model": "Badge",
                "status": "available"
                # Missing warrantyExpiry key entirely
            }
        ]
        
        respx.get("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(200, json=mock_assets)
        )
        
        response = client.get("/reports/warranty-expiring")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 0
        assert data["items"] == []

    @respx.mock
    def test_warranty_expiring_invalid_date_format(self, client):
        """Test warranty report skips assets with invalid date format."""
        mock_assets = [
            {
                "id": 1,
                "assetTag": "INVALID-001",
                "assetType": "Laptop",
                "manufacturer": "Dell",
                "model": "XPS",
                "warrantyExpiry": "not-a-date",
                "status": "available"
            }
        ]
        
        respx.get("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(200, json=mock_assets)
        )
        
        response = client.get("/reports/warranty-expiring")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 0
        assert data["items"] == []

    @respx.mock
    def test_warranty_expiring_custom_threshold(self, client):
        """Test warranty report with custom threshold."""
        today = date.today()
        within_30 = (today + timedelta(days=20)).isoformat()
        within_90 = (today + timedelta(days=60)).isoformat()
        
        mock_assets = [
            {
                "id": 1,
                "assetTag": "SOON-001",
                "assetType": "Laptop",
                "manufacturer": "Dell",
                "model": "XPS",
                "warrantyExpiry": within_30,
                "status": "available"
            },
            {
                "id": 2,
                "assetTag": "LATER-002",
                "assetType": "Monitor",
                "manufacturer": "Samsung",
                "model": "S27",
                "warrantyExpiry": within_90,
                "status": "available"
            }
        ]
        
        respx.get("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(200, json=mock_assets)
        )
        
        # With 30 day threshold, should only get first asset
        response = client.get("/reports/warranty-expiring?within_days=30")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["within_days"] == 30
        assert data["count"] == 1
        assert data["items"][0]["assetTag"] == "SOON-001"

    @respx.mock
    def test_warranty_expiring_assets_svc_error(self, client):
        """Test warranty report when assets-svc is unavailable."""
        respx.get("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(500, json={"error": "Internal error"})
        )
        
        response = client.get("/reports/warranty-expiring")
        
        assert response.status_code == 502
        assert "assets-svc unavailable" in response.json()["detail"]

    @respx.mock
    def test_warranty_expiring_assets_svc_timeout(self, client):
        """Test warranty report when assets-svc times out."""
        respx.get("http://assets-svc:8080/assets").mock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        
        response = client.get("/reports/warranty-expiring")
        
        assert response.status_code == 502
        assert "assets-svc unavailable" in response.json()["detail"]
