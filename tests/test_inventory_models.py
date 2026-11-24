import app.db.session
import app.models


def test_inventory_tables_are_registered():
    table_names = set(app.db.session.Base.metadata.tables)
    assert {"inventories", "inventory_movements"} <= table_names