def create_category(client, headers, name="Books", slug="books"):
    response = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": name, "slug": slug},
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


def create_variant(client, headers, product_id, sku="SKU-1"):
    response = client.post(
        f"/api/v1/admin/products/{product_id}/variants",
        headers=headers,
        json={"sku": sku, "name": "Default", "price": "10.00"},
    )
    assert response.status_code == 201
    return response.json()


def adjust(client, headers, variant_id, quantity_delta, reason="Adjustment"):
    return client.post(
        f"/api/v1/admin/variants/{variant_id}/inventory-adjustments",
        headers=headers,
        json={"quantity_delta": quantity_delta, "reason": reason},
    )


def test_adjust_inventory_and_list(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    response = adjust(client, admin_headers, variant["id"], 5, "Initial stock")

    assert response.status_code == 200
    body = response.json()
    assert body["on_hand"] == 5
    assert body["reserved"] == 0
    assert body["available"] == 5

    response = client.get("/api/v1/admin/inventory", headers=admin_headers)

    assert response.status_code == 200
    inventory_body = response.json()
    assert inventory_body["total"] == 1
    item = inventory_body["items"][0]
    assert item["variant_id"] == variant["id"]
    assert item["available"] == 5

    response = client.get(
        f"/api/v1/admin/inventory-movements?variant_id={variant['id']}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    movement_body = response.json()
    assert movement_body["total"] == 1
    movement = movement_body["items"][0]
    assert movement["movement_type"] == "ADJUST_IN"
    assert movement["quantity_delta"] == 5
    assert movement["on_hand_after"] == 5


def test_adjust_inventory_rejects_zero_quantity(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    response = adjust(client, admin_headers, variant["id"], 0)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_adjust_inventory_rejects_missing_variant(client, admin_headers):
    response = adjust(client, admin_headers, 999999, 5)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_adjust_inventory_requires_authentication(client):
    response = client.post(
        "/api/v1/admin/variants/1/inventory-adjustments",
        json={"quantity_delta": 5, "reason": "Initial stock"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_adjust_inventory_rejects_negative_on_hand(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    assert adjust(client, admin_headers, variant["id"], 2).status_code == 200

    response = adjust(client, admin_headers, variant["id"], -3)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVENTORY_NEGATIVE"


def test_list_inventory_movements_filters_and_paginates(
    client, admin_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    assert adjust(client, admin_headers, variant["id"], 5).status_code == 200
    assert adjust(client, admin_headers, variant["id"], -2).status_code == 200

    response = client.get(
        f"/api/v1/admin/inventory-movements"
        f"?variant_id={variant['id']}&page=1&page_size=1",
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["movement_type"] == "ADJUST_OUT"
    assert body["items"][0]["quantity_delta"] == -2

    response = client.get(
        f"/api/v1/admin/inventory-movements"
        f"?variant_id={variant['id']}&page=2&page_size=1",
        headers=admin_headers,
    )
    body = response.json()
    assert body["items"][0]["movement_type"] == "ADJUST_IN"