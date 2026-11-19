import fastapi.testclient
import sqlalchemy.exc

import app.db.dependencies
import app.main

client = fastapi.testclient.TestClient(app.main.application)


class _FailingSession:
    async def execute(self, *args, **kwargs):
        raise sqlalchemy.exc.SQLAlchemyError("database is down")

def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Saleor FastAPI Backend!",
    }
    assert response.headers["X-Request-ID"]


def test_health_check():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "OK",
        "database": "OK",
    }


def test_health_check_database_failure():
    app.main.application.dependency_overrides[
        app.db.dependencies.get_db_session
    ] = lambda: _FailingSession()

    try:
        response = client.get("/api/v1/health")
    finally:
        app.main.application.dependency_overrides.clear()

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "HTTP_ERROR"
    assert body["error"]["request_id"] == response.headers["X-Request-ID"]



def test_http_exception_handler():
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["error"] == {
        "code": "HTTP_ERROR",
        "message": "Not Found",
        "details": None,
        "request_id": response.headers["X-Request-ID"],
    }