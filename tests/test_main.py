from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

client = TestClient(app)

def test_root_returns_running_status():
    response = client.get("/")
    assert response.status_code == 200

def test_fetch_descriptors_rejects_empty_list():
    response = client.post("/fetch-descriptors", json={"compound_names": []})
    assert response.status_code == 422

@patch("main.fetch_cid_by_name", new_callable=AsyncMock)
def test_fetch_descriptors_handles_not_found_compound(mock_fetch_cid):
    mock_fetch_cid.return_value = None
    response = client.post("/fetch-descriptors", json={"compound_names": ["FakeCompound"]})
    assert response.status_code == 200
    body = response.json()
    assert body["total_resolved"] == 0
