def register_payload(**overrifes):
    payload = {
        "email": "user@example.com",
        "username": "user_1",
        "password": "password123",
    }
    payload.update(overrifes)
    return payload


def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["username"] == "user_1"
    assert body["is_active"] is True
    assert [role["name"] for role in body["roles"]] == ["user"]
    assert "password_hash" not in body


def test_register_rejects_duplicate_email(client):
    client.post("/api/v1/auth/register", json=register_payload())

    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(username="another_user"),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_register_rejects_duplicate_username(client):
    client.post("/api/v1/auth/register", json=register_payload())

    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(email="another@example.com"),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "USERNAME_ALREADY_EXISTS"


def test_login_returns_access_token(client):
    client.post("/api/v1/auth/register", json=register_payload())

    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "user@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0


def test_login_accepts_username(client):
    client.post("/api/v1/auth/register", json=register_payload())

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "user_1", "password": "password123"},
    )

    assert response.status_code == 200


def test_login_rejects_wrong_password(client):
    client.post("/api/v1/auth/register", json=register_payload())

    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "user@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert response.headers["WWW-Authenticate"] == "Bearer"