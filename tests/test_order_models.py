import app.db.session
import app.models


def test_order_tables_are_registered():
    table_names = set(app.db.session.Base.metadata.tables)
    assert {"orders", "order_items", "order_events"} <= table_names