from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_screen_library_flags_lipinski_pass():
    response = client.post("/screen-library", json={
        "compounds": [{"name": "Aspirin", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}]
    })
    assert response.status_code == 200
    body = response.json()
    assert body["results"][0]["passes_lipinski"] is True

def test_screen_library_rejects_invalid_smiles():
    response = client.post("/screen-library", json={
        "compounds": [{"name": "Bad", "smiles": "not_a_real_smiles!!!"}]
    })
    assert response.status_code == 200
    assert response.json()["results"][0]["valid_smiles"] is False