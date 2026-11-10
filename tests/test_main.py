import fastapi.testclient

from app import main


client = fastapi.testclient.TestClient(main.app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Saleor FastAPI Backend!",
    }


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "OK",
    }