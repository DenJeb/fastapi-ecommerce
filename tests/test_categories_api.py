def create_category(
    client,
    headers,
    name,
    slug,
    parent_id=None,
    is_active=True,
):
    response = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={
            "name": name,
            "slug": slug,
            "parent_id": parent_id,
            "is_active": is_active,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_list_categories_returns_only_active(client, admin_headers):
    create_category(client, admin_headers, "Books", "books")
    create_category(
        client,
        admin_headers,
        "Hidden",
        "hidden",
        is_active=False,
    )

    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == ["books"]


def test_create_category_requires_authentication(client):
    response = client.post(
        "/api/v1/admin/categories",
        json={"name": "Books", "slug": "books"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_create_category(client, admin_headers):
    body = create_category(client, admin_headers, "Books", "books")

    assert body["name"] == "Books"
    assert body["slug"] == "books"
    assert body["parent_id"] is None
    assert body["is_active"] is True


def test_create_category_rejects_duplicate_slug(client, admin_headers):
    create_category(client, admin_headers, "Books", "books")

    response = client.post(
        "/api/v1/admin/categories",
        headers=admin_headers,
        json={"name": "Other", "slug": "books"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CATEGORY_SLUG_EXISTS"


def test_create_category_rejects_missing_parent(client, admin_headers):
    response = client.post(
        "/api/v1/admin/categories",
        headers=admin_headers,
        json={"name": "Books", "slug": "books", "parent_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_update_category(client, admin_headers):
    parent = create_category(client, admin_headers, "Books", "books")
    child = create_category(client, admin_headers, "Fiction", "fiction")

    response = client.patch(
        f"/api/v1/admin/categories/{child['id']}",
        headers=admin_headers,
        json={"name": "Fiction Books", "parent_id": parent["id"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Fiction Books"
    assert body["parent_id"] == parent["id"]


def test_update_category_rejects_cycle(client, admin_headers):
    parent = create_category(client, admin_headers, "Books", "books")
    child = create_category(
        client,
        admin_headers,
        "Fiction",
        "fiction",
        parent_id=parent["id"],
    )

    response = client.patch(
        f"/api/v1/admin/categories/{parent['id']}",
        headers=admin_headers,
        json={"parent_id": child["id"]},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CATEGORY_CYCLE"


def test_update_category_can_move_to_root(client, admin_headers):
    parent = create_category(client, admin_headers, "Books", "books")
    child = create_category(
        client,
        admin_headers,
        "Fiction",
        "fiction",
        parent_id=parent["id"],
    )

    response = client.patch(
        f"/api/v1/admin/categories/{child['id']}",
        headers=admin_headers,
        json={"parent_id": None},
    )

    assert response.status_code == 200
    assert response.json()["parent_id"] is None