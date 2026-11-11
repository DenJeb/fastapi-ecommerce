import fastapi.testclient

import app.main

client = fastapi.testclient.TestClient(app.main.application)


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


def test_app_exception_handler():
    response = client.get("/test-error")

    assert response.status_code == 404
    assert response.json() == {
        "code": "RESOURCE_NOT_FOUND",
        "message": "Product does not exist.",
        "details": None,
    }


def test_http_exception_handler():
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "code": "HTTP_ERROR",
        "message": "Not Found",
        "details": None,
    }