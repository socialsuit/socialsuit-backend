import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_thumbnail():
    response = client.get("/generate-thumbnail", params={"query": "nature"})
    assert response.status_code == 200
