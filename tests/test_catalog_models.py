import app.db.session
import app.models


def test_catalog_tables_are_registered():
    table_names = set(app.db.session.Base.metadata.tables)
    assert {"categories", "products", "product_variants"} <= table_names


def test_product_variant_price_uses_decimal():
    variants = app.db.session.Base.metadata.tables["product_variants"]
    price_type = variants.columns["price"].type

    assert price_type.__class__.__name__ == "Numeric"
    assert price_type.precision == 12
    assert price_type.scale == 2