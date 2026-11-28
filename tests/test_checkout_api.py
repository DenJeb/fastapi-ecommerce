def create_category(client, headers):
    response = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": "Books", "slug": "books"},
    )
    assert response.status_code == 201
    return response.json()


def create_product(client, headers, category_id):
    response = client.post(
        "/api/v1/admin/products",
        headers=headers,
        json={
            "category_id": category_id,
            "name": "Book",
            "slug": "book",
            "status": "ACTIVE",
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


def set_stock(client, headers, variant_id, quantity):
    response = client.post(
        f"/api/v1/admin/variants/{variant_id}/inventory-adjustments",
        headers=headers,
        json={"quantity_delta": quantity, "reason": "Initial stock"},
    )
    assert response.status_code == 200


def add_to_cart(client, headers, variant_id, quantity=1):
    response = client.post(
        "/api/v1/cart/items",
        headers=headers,
        json={"variant_id": variant_id, "quantity": quantity},
    )
    assert response.status_code == 200
    return response.json()


def create_order(client, headers, key=None):
    request_headers = dict(headers)
    if key is not None:
        request_headers["Idempotency-Key"] = key
    return client.post(
        "/api/v1/checkout/orders",
        headers=request_headers,
    )


def test_checkout_preview_computes_totals(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])
    set_stock(client, admin_headers, variant["id"], 5)
    add_to_cart(client, user_headers, variant["id"], 2)

    response = client.post(
        "/api/v1/checkout/preview",
        headers=user_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["variant_id"] == variant["id"]
    assert item["sku"] == "SKU-1"
    assert item["available"] == 5
    assert item["unit_price"] == "10.00"
    assert item["line_total"] == "20.00"
    assert body["subtotal"] == "20.00"
    assert body["discount_total"] == "0.00"
    assert body["total_amount"] == "20.00"
    assert body["currency"] == "CNY"


def test_checkout_preview_rejects_empty_cart(client, user_headers):
    response = client.post(
        "/api/v1/checkout/preview",
        headers=user_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CART_EMPTY"


def test_checkout_preview_requires_authentication(client):
    response = client.post("/api/v1/checkout/preview")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_checkout_preview_rejects_insufficient_stock(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])
    set_stock(client, admin_headers, variant["id"], 1)
    add_to_cart(client, user_headers, variant["id"], 2)

    response = client.post(
        "/api/v1/checkout/preview",
        headers=user_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_create_order_reserves_stock_and_clears_cart(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])
    set_stock(client, admin_headers, variant["id"], 5)
    add_to_cart(client, user_headers, variant["id"], 2)

    response = create_order(client, user_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["order_no"].startswith("ORD-")
    assert body["status"] == "PENDING_PAYMENT"
    assert body["subtotal"] == "20.00"
    assert body["total_amount"] == "20.00"
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["product_name"] == "Book"
    assert item["sku"] == "SKU-1"
    assert item["variant_name"] == "Default"
    assert item["unit_price"] == "10.00"
    assert item["quantity"] == 2
    assert item["line_total"] == "20.00"

    response = client.get(
        "/api/v1/admin/inventory",
        headers=admin_headers,
    )
    inventory = response.json()["items"][0]
    assert inventory["on_hand"] == 5
    assert inventory["reserved"] == 2
    assert inventory["available"] == 3

    response = client.get("/api/v1/cart", headers=user_headers)
    assert response.json()["items"] == []


def test_create_order_rolls_back_on_insufficient_stock(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])
    set_stock(client, admin_headers, variant["id"], 1)
    add_to_cart(client, user_headers, variant["id"], 2)

    response = create_order(client, user_headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"

    response = client.get("/api/v1/cart", headers=user_headers)
    assert len(response.json()["items"]) == 1

    response = client.get(
        "/api/v1/admin/inventory",
        headers=admin_headers,
    )
    inventory = response.json()["items"][0]
    assert inventory["reserved"] == 0


def test_create_order_is_idempotent(
    client, admin_headers, user_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])
    set_stock(client, admin_headers, variant["id"], 5)
    add_to_cart(client, user_headers, variant["id"], 2)

    first = create_order(client, user_headers, key="order-key-1")
    assert first.status_code == 201
    first_body = first.json()

    second = create_order(client, user_headers, key="order-key-1")
    assert second.status_code == 200
    second_body = second.json()

    assert second_body["id"] == first_body["id"]
    assert second_body["order_no"] == first_body["order_no"]

    response = client.get(
        "/api/v1/admin/inventory",
        headers=admin_headers,
    )
    inventory = response.json()["items"][0]
    assert inventory["reserved"] == 2

    response = client.get("/api/v1/cart", headers=user_headers)
    assert response.json()["items"] == []


def test_create_order_requires_authentication(client):
    response = client.post("/api/v1/checkout/orders")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"