def create_category(client, headers):
    response = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": "Books", "slug": "books"},
    )
    assert response.status_code == 201
    return response.json()


def create_product(client, headers, category_id, status="ACTIVE"):
    response = client.post(
        "/api/v1/admin/products",
        headers=headers,
        json={
            "category_id": category_id,
            "name": "Book",
            "slug": "book",
            "status": status,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_variant(client, headers, product_id):
    response = client.post(
        f"/api/v1/admin/products/{product_id}/variants",
        headers=headers,
        json={"sku": "SKU-1", "name": "Default", "price": "10.00"},
    )
    assert response.status_code == 201
    return response.json()


def add_item(client, headers, variant_id, quantity=1):
    return client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"variant_id": variant_id, "quantity": quantity},
    )


def test_get_cart_requires_authentication(client):
    response = client.get("/api/v1/cart")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_get_cart_creates_empty_cart(client, user_headers):
    response = client.get("/api/v1/cart", headers=user_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["subtotal"] == "0.00"
    assert body["total_quantity"] == 0


def test_add_item_returns_totals(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    response = add_item(client, user_headers, variant["id"], 2)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["variant_id"] == variant["id"]
    assert item["sku"] == "SKU-1"
    assert item["unit_price"] == "10.00"
    assert item["quantity"] == 2
    assert item["line_total"] == "20.00"
    assert body["subtotal"] == "20.00"
    assert body["total_quantity"] == 2


def test_add_same_variant_merges_quantity(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    assert add_item(client, user_headers, variant["id"], 1).status_code == 200

    response = add_item(client, user_headers, variant["id"], 2)

    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 3
    assert body["subtotal"] == "30.00"


def test_add_item_rejects_unavailable_variant(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(
        client, admin_headers, category["id"], status="DRAFT"
    )
    variant = create_variant(client, admin_headers, product["id"])

    response = add_item(client, user_headers, variant["id"], 1)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_update_cart_item_quantity(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])
    cart = add_item(client, user_headers, variant["id"], 2).json()
    item_id = cart["items"][0]["id"]

    response = client.patch(
        f"/api/v1/cart/items/{item_id}",
        headers=user_headers,
        json={"quantity": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["quantity"] == 5
    assert body["items"][0]["line_total"] == "50.00"
    assert body["subtotal"] == "50.00"


def test_update_cart_item_rejects_zero(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])
    cart = add_item(client, user_headers, variant["id"], 2).json()
    item_id = cart["items"][0]["id"]

    response = client.patch(
        f"/api/v1/cart/items/{item_id}",
        headers=user_headers,
        json={"quantity": 0},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_remove_cart_item(client, admin_headers, user_headers):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])
    cart = add_item(client, user_headers, variant["id"], 2).json()
    item_id = cart["items"][0]["id"]

    response = client.delete(
        f"/api/v1/cart/items/{item_id}",
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["subtotal"] == "0.00"


def test_cart_is_isolated_between_users(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    cart = add_item(client, user_headers, variant["id"], 2).json()
    item_id = cart["items"][0]["id"]

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "username": "other_user",
            "password": "password123",
        },
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={
            "identifier": "other@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    other_headers = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

    response = client.get("/api/v1/cart", headers=other_headers)
    assert response.json()["items"] == []

    response = client.patch(
        f"/api/v1/cart/items/{item_id}",
        headers=other_headers,
        json={"quantity": 1},
    )
    assert response.status_code == 404

    response = client.delete(
        f"/api/v1/cart/items/{item_id}",
        headers=other_headers,
    )
    assert response.status_code == 404