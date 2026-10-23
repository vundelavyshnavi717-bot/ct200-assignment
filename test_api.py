from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db
init_db()
client=TestClient(app)

def test_healthless_smoke():
    assert client.app is app
