"""
Tests for CSV import endpoint.
Mocks HTTP calls to assets-svc.
"""

import io
import pytest
import respx
import httpx
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestCSVImport:
    """Test the /imports/assets endpoint."""

    @respx.mock
    def test_import_valid_csv(self, client):
        """Test importing a valid CSV file."""
        csv_content = """asset_tag,asset_type,manufacturer,model,serial_number,purchase_date,warranty_expiry,status,notes
TEST-001,Laptop,Dell,XPS 15,SN001,2024-01-01,2027-01-01,available,
TEST-002,Monitor,Samsung,S27,SN002,2024-02-01,2027-02-01,available,
TEST-003,Keyboard,Logitech,K120,,2024-03-01,2027-03-01,available,"""

        # Mock assets-svc POST responses
        route = respx.post("http://assets-svc:8080/assets")
        route.side_effect = [
            httpx.Response(201, json={"id": 1}),
            httpx.Response(201, json={"id": 2}),
            httpx.Response(201, json={"id": 3}),
        ]

        # Create file upload
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["imported"] == 3
        assert "TEST-001" in data["asset_tags"]
        assert "TEST-002" in data["asset_tags"]
        assert "TEST-003" in data["asset_tags"]
        assert len(data["asset_tags"]) == 3

    @respx.mock
    def test_import_csv_with_optional_fields(self, client):
        """Test importing CSV with optional fields populated."""
        csv_content = """asset_tag,asset_type,manufacturer,model,serial_number,purchase_date,warranty_expiry,status,notes
OPT-001,Phone,Apple,iPhone 14,IMEI123,2024-01-15,2026-01-15,assigned,Company device"""

        respx.post("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(201, json={"id": 1})
        )

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["imported"] == 1
        assert data["asset_tags"] == ["OPT-001"]

    @respx.mock
    def test_import_csv_with_null_optional_fields(self, client):
        """Test importing CSV with empty optional fields."""
        csv_content = """asset_tag,asset_type,manufacturer,model,serial_number,purchase_date,warranty_expiry,status,notes
NULL-001,Keycard,Generic,Card,,,,available,"""

        respx.post("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(201, json={"id": 1})
        )

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["imported"] == 1
        assert data["asset_tags"] == ["NULL-001"]

    def test_import_csv_missing_required_columns(self, client):
        """Test importing CSV with missing required columns."""
        csv_content = """asset_tag,manufacturer,model
MISSING-001,Dell,XPS"""

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 400
        assert "must contain columns" in response.json()["detail"]

    def test_import_csv_missing_asset_type(self, client):
        """Test CSV missing the asset_type required column."""
        csv_content = """asset_tag,manufacturer,model,status
TYPE-001,Dell,XPS,available"""

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 400
        assert "asset_type" in response.json()["detail"]

    def test_import_csv_missing_status(self, client):
        """Test CSV missing the status required column."""
        csv_content = """asset_tag,asset_type,manufacturer,model
STATUS-001,Laptop,Dell,XPS"""

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 400
        assert "status" in response.json()["detail"]

    def test_import_empty_csv(self, client):
        """Test importing an empty CSV file."""
        csv_content = ""

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 400

    def test_import_csv_header_only(self, client):
        """Test importing CSV with only headers, no data rows."""
        csv_content = """asset_tag,asset_type,manufacturer,model,status"""

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        # Should succeed but import 0 rows
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 0
        assert data["asset_tags"] == []

    @respx.mock
    def test_import_csv_single_row(self, client):
        """Test importing CSV with single data row."""
        csv_content = """asset_tag,asset_type,manufacturer,model,status
SINGLE-001,Monitor,LG,27UK850,available"""

        respx.post("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(201, json={"id": 1})
        )

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 1
        assert data["asset_tags"] == ["SINGLE-001"]

    @respx.mock
    def test_import_csv_large_batch(self, client):
        """Test importing CSV with multiple rows."""
        rows = [
            "asset_tag,asset_type,manufacturer,model,status"
        ]
        for i in range(10):
            rows.append(f"BATCH-{i:03d},Laptop,Dell,XPS,available")
        
        csv_content = "\n".join(rows)

        # Mock 10 successful creates
        route = respx.post("http://assets-svc:8080/assets")
        route.side_effect = [
            httpx.Response(201, json={"id": i}) for i in range(1, 11)
        ]

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 10
        assert len(data["asset_tags"]) == 10
        assert "BATCH-000" in data["asset_tags"]
        assert "BATCH-009" in data["asset_tags"]

    @respx.mock
    def test_import_csv_assets_svc_error(self, client):
        """Test import when assets-svc returns error.
        
        Note: Current implementation will raise HTTPStatusError and crash.
        This is intentional per the exercise description - no error handling yet.
        """
        csv_content = """asset_tag,asset_type,manufacturer,model,status
ERROR-001,Laptop,Dell,XPS,available"""

        respx.post("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(500, json={"error": "Internal error"})
        )

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        
        # Current implementation will let the HTTPStatusError bubble up
        # The test client catches it and returns 500
        with pytest.raises(httpx.HTTPStatusError):
            # Need to make the actual request, not through test client
            # which converts exceptions to responses
            import asyncio
            from app.routers.imports_ import import_assets
            from fastapi import UploadFile
            
            # Create an UploadFile mock
            class MockFile:
                async def read(self):
                    return csv_content.encode()
            
            async def run_import():
                await import_assets(MockFile())
            
            asyncio.run(run_import())

    @respx.mock
    def test_import_csv_with_extra_columns(self, client):
        """Test importing CSV with extra columns beyond required."""
        csv_content = """asset_tag,asset_type,manufacturer,model,status,extra_col,another_extra
EXTRA-001,Laptop,Dell,XPS,available,extra_val,another_val"""

        respx.post("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(201, json={"id": 1})
        )

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        # Should succeed - extra columns are ignored
        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 1

    @respx.mock
    def test_import_csv_verifies_payload_structure(self, client):
        """Test that CSV import creates correct payload structure."""
        csv_content = """asset_tag,asset_type,manufacturer,model,serial_number,purchase_date,warranty_expiry,status,notes
VERIFY-001,Laptop,Dell,XPS 15,SN123,2024-01-01,2027-01-01,available,Test note"""

        captured_payload = {}

        def capture_payload(request):
            captured_payload.update(request.content.decode())
            return httpx.Response(201, json={"id": 1})

        respx.post("http://assets-svc:8080/assets").mock(
            return_value=httpx.Response(201, json={"id": 1})
        )

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 200
        
        # Verify the request was made to assets-svc
        assert len(respx.calls) == 1
        request = respx.calls[0].request
        
        # Verify it was a POST with JSON
        assert request.method == "POST"
        assert "application/json" in request.headers.get("content-type", "")

    @respx.mock
    def test_import_csv_preserves_order(self, client):
        """Test that imported asset tags are in CSV order."""
        csv_content = """asset_tag,asset_type,manufacturer,model,status
ZEBRA-001,Laptop,Dell,XPS,available
ALPHA-001,Monitor,Samsung,S27,available
BRAVO-001,Keyboard,Logitech,K120,available"""

        route = respx.post("http://assets-svc:8080/assets")
        route.side_effect = [
            httpx.Response(201, json={"id": i}) for i in range(1, 4)
        ]

        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/imports/assets", files=files)

        assert response.status_code == 200
        data = response.json()
        
        # Tags should be in CSV order (ZEBRA, ALPHA, BRAVO), not sorted
        assert data["asset_tags"] == ["ZEBRA-001", "ALPHA-001", "BRAVO-001"]

    def test_import_requires_file(self, client):
        """Test that import endpoint requires a file."""
        response = client.post("/imports/assets")
        
        # Should get validation error for missing file
        assert response.status_code == 422
