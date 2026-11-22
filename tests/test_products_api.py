def create_category(client, headers, name="Books", slug="books"):
    response = client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": name, "slug": slug},
    )
    assert response.status_code == 201
    return response.json()


def create_product(
    client,
    headers,
    category_id,
    name="Example Product",
    slug="example-product",
    status="DRAFT",
):
    response = client.post(
        "/api/v1/admin/products",
        headers=headers,
        json={
            "category_id": category_id,
            "name": name,
            "slug": slug,
            "description": "Example description",
            "status": status,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_variant(
    client,
    headers,
    product_id,
    sku="SKU-1",
    name="Default",
    price="99.50",
    is_active=True,
):
    response = client.post(
        f"/api/v1/admin/products/{product_id}/variants",
        headers=headers,
        json={
            "sku": sku,
            "name": name,
            "price": price,
            "is_active": is_active,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_list_products_returns_only_active_and_paginates(
    client, admin_headers
):
    category = create_category(client, admin_headers)
    create_product(
        client, admin_headers, category["id"],
        slug="active-one", status="ACTIVE",
    )
    create_product(
        client, admin_headers, category["id"],
        slug="active-two", status="ACTIVE",
    )
    create_product(
        client, admin_headers, category["id"],
        slug="draft-one", status="DRAFT",
    )

    response = client.get("/api/v1/products?page=1&page_size=1")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert [item["slug"] for item in body["items"]] == ["active-one"]

    response = client.get("/api/v1/products?page=2&page_size=1")
    body = response.json()
    assert [item["slug"] for item in body["items"]] == ["active-two"]


def test_list_products_filters_by_category(client, admin_headers):
    books = create_category(client, admin_headers, "Books", "books")
    music = create_category(client, admin_headers, "Music", "music")
    create_product(
        client, admin_headers, books["id"],
        slug="book", status="ACTIVE",
    )
    create_product(
        client, admin_headers, music["id"],
        slug="album", status="ACTIVE",
    )

    response = client.get(
        f"/api/v1/products?category_id={books['id']}"
    )

    body = response.json()
    assert body["total"] == 1
    assert [item["slug"] for item in body["items"]] == ["book"]


def test_get_product_hides_inactive_variants(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(
        client, admin_headers, category["id"], status="ACTIVE"
    )
    create_variant(
        client, admin_headers, product["id"],
        sku="SKU-ACTIVE", is_active=True,
    )
    create_variant(
        client, admin_headers, product["id"],
        sku="SKU-INACTIVE", is_active=False,
    )

    response = client.get(f"/api/v1/products/{product['id']}")

    assert response.status_code == 200
    body = response.json()
    assert [item["sku"] for item in body["variants"]] == ["SKU-ACTIVE"]
    assert body["variants"][0]["price"] == "99.50"


def test_get_draft_product_returns_404(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(
        client, admin_headers, category["id"], status="DRAFT"
    )

    response = client.get(f"/api/v1/products/{product['id']}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_product_requires_authentication(client):
    response = client.post(
        "/api/v1/admin/products",
        json={
            "category_id": 1,
            "name": "Example",
            "slug": "example",
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_create_product_defaults_to_draft_and_rejects_duplicate_slug(
    client, admin_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])

    assert product["status"] == "DRAFT"

    response = client.post(
        "/api/v1/admin/products",
        headers=admin_headers,
        json={
            "category_id": category["id"],
            "name": "Other",
            "slug": "example-product",
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PRODUCT_SLUG_EXISTS"


def test_create_product_rejects_missing_category(client, admin_headers):
    response = client.post(
        "/api/v1/admin/products",
        headers=admin_headers,
        json={
            "category_id": 999999,
            "name": "Example",
            "slug": "example",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_variant_and_rejects_duplicate_sku(
    client, admin_headers
):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    assert variant["price"] == "99.50"

    response = client.post(
        f"/api/v1/admin/products/{product['id']}/variants",
        headers=admin_headers,
        json={"sku": "SKU-1", "name": "Other", "price": "10.00"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "VARIANT_SKU_EXISTS"


def test_update_product_status_to_active(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(
        client, admin_headers, category["id"], status="DRAFT"
    )

    response = client.patch(
        f"/api/v1/admin/products/{product['id']}",
        headers=admin_headers,
        json={"status": "ACTIVE"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"

    response = client.get(f"/api/v1/products/{product['id']}")
    assert response.status_code == 200


def test_update_variant_price(client, admin_headers):
    category = create_category(client, admin_headers)
    product = create_product(client, admin_headers, category["id"])
    variant = create_variant(client, admin_headers, product["id"])

    response = client.patch(
        f"/api/v1/admin/variants/{variant['id']}",
        headers=admin_headers,
        json={"price": "79.90"},
    )

    assert response.status_code == 200
    assert response.json()["price"] == "79.90"